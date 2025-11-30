"""
Critic Agent - Output Validation & Quality Control

This agent evaluates execution results and determines:
- Is the output correct and complete?
- Does it answer the original query?
- Should the plan be rewritten?
"""

from typing import Any, Dict, List
from dataclasses import dataclass
from enum import Enum

from .base_agent import BaseAgent, AgentContext


class CritiqueVerdict(Enum):
    """Possible critique outcomes."""
    APPROVED = "approved"  # Output is good, proceed
    NEEDS_IMPROVEMENT = "needs_improvement"  # Minor fixes needed
    REPLAN = "replan"  # Major issues, need new plan
    REJECTED = "rejected"  # Cannot proceed, inform user


@dataclass
class CritiqueResult:
    """Structured critique output."""
    verdict: CritiqueVerdict
    confidence: float
    issues: List[str]
    suggestions: List[str]
    quality_scores: Dict[str, float]


class CriticAgent(BaseAgent):
    """
    Validates execution outputs against quality criteria.
    Acts as gatekeeper before final response.
    """
    
    def __init__(self, strictness: str = "medium"):
        super().__init__("critic", "🔎 Critic")
        
        # Strictness affects thresholds
        self.thresholds = {
            "low": {"completeness": 0.5, "accuracy": 0.5, "relevance": 0.5},
            "medium": {"completeness": 0.7, "accuracy": 0.7, "relevance": 0.6},
            "high": {"completeness": 0.85, "accuracy": 0.85, "relevance": 0.75}
        }[strictness]
        
        self.critique_history: List[CritiqueResult] = []
    
    def get_capabilities(self) -> List[str]:
        return [
            "output_validation",
            "quality_scoring",
            "issue_detection",
            "improvement_suggestions",
            "replan_decision"
        ]
    
    async def process(self, context: AgentContext) -> Dict[str, Any]:
        """
        Critique the current execution results.
        """
        self.start_processing()
        
        try:
            # Get execution history
            executions = context.execution_history
            if not executions:
                self.finish_processing(success=True)
                return {
                    "success": True,
                    "verdict": CritiqueVerdict.APPROVED.value,
                    "message": "No executions to critique"
                }
            
            # Get latest execution
            latest = executions[-1]
            
            # Evaluate quality dimensions
            quality_scores = await self._evaluate_quality(
                context.original_query,
                context.current_understanding,
                latest
            )
            
            # Detect issues
            issues = self._detect_issues(latest, quality_scores)
            
            # Generate suggestions
            suggestions = self._generate_suggestions(issues)
            
            # Determine verdict
            verdict = self._determine_verdict(quality_scores, issues)
            confidence = self._calculate_confidence(quality_scores)
            
            critique = CritiqueResult(
                verdict=verdict,
                confidence=confidence,
                issues=issues,
                suggestions=suggestions,
                quality_scores=quality_scores
            )
            
            # Record critique
            self.critique_history.append(critique)
            context.critiques.append({
                "verdict": verdict.value,
                "confidence": confidence,
                "issues": issues,
                "scores": quality_scores
            })
            
            self.finish_processing(success=True)
            
            return {
                "success": True,
                "verdict": verdict.value,
                "confidence": confidence,
                "issues": issues,
                "suggestions": suggestions,
                "quality_scores": quality_scores,
                "should_replan": verdict == CritiqueVerdict.REPLAN,
                "summary": self._create_summary(critique)
            }
            
        except Exception as e:
            self.finish_processing(success=False)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _evaluate_quality(
        self,
        query: str,
        understanding: Dict,
        execution: Dict
    ) -> Dict[str, float]:
        """Evaluate output against quality dimensions."""
        
        result = execution.get("result", "")
        success = execution.get("success", False)
        
        scores = {}
        
        # Completeness: Does output address all parts of query?
        scores["completeness"] = self._score_completeness(
            query, understanding, result
        )
        
        # Accuracy: Is the output correct format and structure?
        scores["accuracy"] = self._score_accuracy(
            understanding, result, success
        )
        
        # Relevance: Does output match the intent?
        scores["relevance"] = self._score_relevance(
            understanding, result
        )
        
        # Actionability: Can user act on this output?
        scores["actionability"] = self._score_actionability(result)
        
        return scores
    
    def _score_completeness(
        self, 
        query: str, 
        understanding: Dict, 
        result: str
    ) -> float:
        """Score how complete the result is."""
        if not result:
            return 0.0
        
        # Check if key entities are addressed
        actions = understanding.get("actions", [])
        addressed = sum(1 for a in actions if a.lower() in result.lower())
        action_coverage = addressed / max(1, len(actions))
        
        # Check result length (reasonable output)
        length_score = min(1.0, len(result) / 100)
        
        return (action_coverage * 0.6 + length_score * 0.4)
    
    def _score_accuracy(
        self, 
        understanding: Dict, 
        result: str,
        success: bool
    ) -> float:
        """Score result accuracy."""
        if not success:
            return 0.3
        
        if not result:
            return 0.0
        
        # Check for error indicators
        error_indicators = ["error", "failed", "exception", "traceback"]
        has_errors = any(e in result.lower() for e in error_indicators)
        
        if has_errors:
            return 0.4
        
        return 0.85
    
    def _score_relevance(self, understanding: Dict, result: str) -> float:
        """Score how relevant output is to intent."""
        intent = understanding.get("intent", "")
        
        # Intent-specific keywords that should appear
        intent_keywords = {
            "standup_summary": ["commit", "work", "done", "progress"],
            "pr_description": ["changes", "description", "pull"],
            "code_review": ["review", "issue", "suggest", "improve"],
            "tech_debt": ["debt", "refactor", "complexity", "improve"],
            "dependency_check": ["dependency", "version", "security"],
            "documentation": ["doc", "description", "usage"]
        }
        
        keywords = intent_keywords.get(intent, [])
        if not keywords:
            return 0.5
        
        matched = sum(1 for k in keywords if k in result.lower())
        return min(1.0, matched / len(keywords) + 0.3)
    
    def _score_actionability(self, result: str) -> float:
        """Score how actionable the output is."""
        if not result:
            return 0.0
        
        # Look for actionable patterns
        actionable_patterns = [
            "TODO:", "FIXME:", "should", "recommend",
            "consider", "next step", "action item"
        ]
        
        has_actionable = any(p in result for p in actionable_patterns)
        
        # Check for structured output (lists, sections)
        has_structure = any(c in result for c in ["-", "*", "1.", "•", "##"])
        
        base_score = 0.5
        if has_actionable:
            base_score += 0.25
        if has_structure:
            base_score += 0.25
        
        return base_score
    
    def _detect_issues(
        self, 
        execution: Dict, 
        scores: Dict[str, float]
    ) -> List[str]:
        """Detect specific issues in output."""
        issues = []
        
        if not execution.get("success"):
            issues.append("Execution failed")
        
        for metric, score in scores.items():
            threshold = self.thresholds.get(metric, 0.7)
            if score < threshold:
                issues.append(
                    f"{metric.capitalize()} below threshold: "
                    f"{score:.0%} < {threshold:.0%}"
                )
        
        result = execution.get("result", "")
        if len(result) < 50:
            issues.append("Output too short")
        
        return issues
    
    def _generate_suggestions(self, issues: List[str]) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        for issue in issues:
            if "completeness" in issue.lower():
                suggestions.append(
                    "Add more detail to address all parts of the query"
                )
            elif "accuracy" in issue.lower():
                suggestions.append(
                    "Verify output format and correct any errors"
                )
            elif "relevance" in issue.lower():
                suggestions.append(
                    "Focus output more closely on the original intent"
                )
            elif "too short" in issue.lower():
                suggestions.append(
                    "Expand output with more detailed information"
                )
        
        return suggestions
    
    def _determine_verdict(
        self, 
        scores: Dict[str, float], 
        issues: List[str]
    ) -> CritiqueVerdict:
        """Determine final verdict based on scores and issues."""
        
        avg_score = sum(scores.values()) / max(1, len(scores))
        
        if avg_score >= 0.8 and len(issues) == 0:
            return CritiqueVerdict.APPROVED
        elif avg_score >= 0.6 or len(issues) <= 2:
            return CritiqueVerdict.NEEDS_IMPROVEMENT
        elif avg_score >= 0.4:
            return CritiqueVerdict.REPLAN
        else:
            return CritiqueVerdict.REJECTED
    
    def _calculate_confidence(self, scores: Dict[str, float]) -> float:
        """Calculate critique confidence."""
        if not scores:
            return 0.5
        return sum(scores.values()) / len(scores)
    
    def _create_summary(self, critique: CritiqueResult) -> str:
        """Create human-readable critique summary."""
        emoji_map = {
            CritiqueVerdict.APPROVED: "✅",
            CritiqueVerdict.NEEDS_IMPROVEMENT: "⚠️",
            CritiqueVerdict.REPLAN: "🔄",
            CritiqueVerdict.REJECTED: "❌"
        }
        
        lines = [
            f"{emoji_map[critique.verdict]} Verdict: {critique.verdict.value}"
        ]
        
        if critique.issues:
            lines.append(f"Issues: {len(critique.issues)}")
        
        lines.append(f"Confidence: {critique.confidence:.0%}")
        
        return " | ".join(lines)

