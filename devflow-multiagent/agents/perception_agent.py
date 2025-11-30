"""
Perception Agent - Query Understanding & Intent Classification

This agent is the first point of contact for user queries.
It analyzes and understands what the developer wants to accomplish.
"""

import re
from typing import Any, Dict, List
from dataclasses import dataclass
from enum import Enum

from .base_agent import BaseAgent, AgentContext


class DeveloperIntent(Enum):
    """Classified developer intents."""
    STANDUP_SUMMARY = "standup_summary"
    PR_DESCRIPTION = "pr_description"
    CODE_REVIEW = "code_review"
    TECH_DEBT = "tech_debt"
    DEPENDENCY_CHECK = "dependency_check"
    DOCUMENTATION = "documentation"
    GENERAL_HELP = "general_help"
    UNKNOWN = "unknown"


@dataclass
class PerceptionResult:
    """Structured output from perception analysis."""
    intent: DeveloperIntent
    confidence: float
    entities: Dict[str, Any]  # Extracted entities (files, branches, etc.)
    temporal_context: Dict  # Time-related info (yesterday, last week)
    action_verbs: List[str]  # Main actions requested
    clarifications_needed: List[str]  # Questions to ask user


class PerceptionAgent(BaseAgent):
    """
    Understands developer queries using pattern matching
    and semantic analysis. First agent in the pipeline.
    """
    
    def __init__(self):
        super().__init__("perception", "🧠 Perception")
        
        # Intent patterns - novel keyword-based classification
        self.intent_patterns = {
            DeveloperIntent.STANDUP_SUMMARY: [
                r"standup", r"what did i (do|work on)", r"yesterday",
                r"daily summary", r"scrum update", r"my commits",
                r"progress report", r"what.*(work|done).*today"
            ],
            DeveloperIntent.PR_DESCRIPTION: [
                r"pr description", r"pull request", r"merge request",
                r"generate.*pr", r"write.*description", r"create.*pr"
            ],
            DeveloperIntent.CODE_REVIEW: [
                r"review.*code", r"code review", r"check.*code",
                r"analyze.*code", r"find.*bugs", r"improve.*code",
                r"look at.*code", r"inspect"
            ],
            DeveloperIntent.TECH_DEBT: [
                r"tech(nical)? debt", r"refactor", r"cleanup",
                r"improve quality", r"code smell", r"complexity",
                r"maintainability", r"legacy"
            ],
            DeveloperIntent.DEPENDENCY_CHECK: [
                r"dependenc", r"package", r"vulnerabilit",
                r"security.*check", r"outdated", r"update.*lib",
                r"npm audit", r"pip check"
            ],
            DeveloperIntent.DOCUMENTATION: [
                r"doc(ument)?", r"generate.*doc", r"write.*doc",
                r"readme", r"api.*doc", r"explain.*code"
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            "file_path": r'[\w/]+\.(py|js|ts|tsx|jsx|go|rs|java|rb|cpp|c|h)',
            "branch": r'(feature|bugfix|hotfix|release)/[\w-]+',
            "git_ref": r'(HEAD|main|master|develop)(\^+|\~\d+)?',
            "time_ref": r'(yesterday|today|last\s+week|this\s+week)',
            "module": r'(?:in|for|from)\s+(\w+(?:/\w+)*)\s*(?:module|package|folder)?'
        }
    
    def get_capabilities(self) -> List[str]:
        return [
            "intent_classification",
            "entity_extraction",
            "temporal_analysis",
            "query_normalization",
            "clarification_detection"
        ]
    
    async def process(self, context: AgentContext) -> Dict[str, Any]:
        """
        Analyze the user query and extract understanding.
        
        Returns structured perception with intent, entities, 
        and required clarifications.
        """
        self.start_processing()
        
        try:
            query = context.original_query.lower()
            
            # Step 1: Classify intent
            intent, confidence = self._classify_intent(query)
            
            # Step 2: Extract entities
            entities = self._extract_entities(context.original_query)
            
            # Step 3: Analyze temporal context
            temporal = self._analyze_temporal(query)
            
            # Step 4: Extract action verbs
            actions = self._extract_actions(query)
            
            # Step 5: Determine clarifications needed
            clarifications = self._determine_clarifications(
                intent, entities, query
            )
            
            # Build perception result
            perception = PerceptionResult(
                intent=intent,
                confidence=confidence,
                entities=entities,
                temporal_context=temporal,
                action_verbs=actions,
                clarifications_needed=clarifications
            )
            
            # Update shared context
            context.current_understanding = {
                "intent": intent.value,
                "confidence": confidence,
                "entities": entities,
                "temporal": temporal,
                "actions": actions,
                "needs_clarification": len(clarifications) > 0
            }
            
            self.finish_processing(success=True)
            
            return {
                "success": True,
                "perception": perception,
                "summary": self._create_summary(perception)
            }
            
        except Exception as e:
            self.finish_processing(success=False)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _classify_intent(self, query: str) -> tuple[DeveloperIntent, float]:
        """
        Classify query intent using pattern matching.
        Returns intent and confidence score.
        """
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    score += 1
            if score > 0:
                intent_scores[intent] = score / len(patterns)
        
        if not intent_scores:
            return DeveloperIntent.GENERAL_HELP, 0.3
        
        # Get highest scoring intent
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = min(0.95, intent_scores[best_intent] + 0.3)
        
        return best_intent, confidence
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract structured entities from query."""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                # Flatten tuples from complex patterns
                if isinstance(matches[0], tuple):
                    matches = [m[0] for m in matches]
                entities[entity_type] = matches
        
        return entities
    
    def _analyze_temporal(self, query: str) -> Dict:
        """Analyze time-related aspects of query."""
        temporal = {
            "reference": None,
            "range": None
        }
        
        if "yesterday" in query:
            temporal["reference"] = "yesterday"
            temporal["range"] = "day"
        elif "today" in query:
            temporal["reference"] = "today"
            temporal["range"] = "day"
        elif "last week" in query or "past week" in query:
            temporal["reference"] = "last_week"
            temporal["range"] = "week"
        elif "this week" in query:
            temporal["reference"] = "this_week"
            temporal["range"] = "week"
        elif "last month" in query:
            temporal["reference"] = "last_month"
            temporal["range"] = "month"
        
        return temporal
    
    def _extract_actions(self, query: str) -> List[str]:
        """Extract main action verbs from query."""
        action_keywords = [
            "generate", "create", "review", "check", "find",
            "analyze", "write", "summarize", "list", "show",
            "get", "fetch", "explain", "fix", "improve"
        ]
        
        found = []
        for action in action_keywords:
            if action in query:
                found.append(action)
        
        return found
    
    def _determine_clarifications(
        self, 
        intent: DeveloperIntent, 
        entities: Dict, 
        query: str
    ) -> List[str]:
        """Determine what clarifications might be needed."""
        clarifications = []
        
        # Code review needs file path
        if intent == DeveloperIntent.CODE_REVIEW:
            if "file_path" not in entities:
                clarifications.append(
                    "Which file(s) would you like me to review?"
                )
        
        # PR description needs branch
        if intent == DeveloperIntent.PR_DESCRIPTION:
            if "branch" not in entities and "git_ref" not in entities:
                clarifications.append(
                    "Which branch should I generate the PR description for?"
                )
        
        # Docs need target module
        if intent == DeveloperIntent.DOCUMENTATION:
            if "file_path" not in entities and "module" not in entities:
                clarifications.append(
                    "Which file or module should I document?"
                )
        
        return clarifications
    
    def _create_summary(self, perception: PerceptionResult) -> str:
        """Create human-readable perception summary."""
        lines = [
            f"📊 Intent: {perception.intent.value} ({perception.confidence:.0%} confidence)"
        ]
        
        if perception.entities:
            lines.append(f"📎 Entities: {perception.entities}")
        
        if perception.temporal_context.get("reference"):
            lines.append(f"⏰ Time: {perception.temporal_context['reference']}")
        
        if perception.action_verbs:
            lines.append(f"🎯 Actions: {', '.join(perception.action_verbs)}")
        
        return "\n".join(lines)

