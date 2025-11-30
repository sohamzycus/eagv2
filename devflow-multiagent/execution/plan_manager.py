"""
Plan Manager - Execution Plan Creation and Modification

Handles:
- Plan generation from intent
- Step sequencing
- Plan rewriting based on feedback
- Progress tracking
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class StepStatus(Enum):
    """Status of a plan step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """A single step in an execution plan."""
    step_id: str
    action: str
    parameters: Dict[str, Any]
    expected_output: str
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def duration_ms(self) -> Optional[int]:
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return None


@dataclass
class ExecutionPlan:
    """Complete execution plan with steps and metadata."""
    plan_id: str
    intent: str
    steps: List[PlanStep]
    created_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    parent_plan_id: Optional[str] = None  # For rewrites
    
    @property
    def current_step_index(self) -> int:
        """Get index of first pending step."""
        for i, step in enumerate(self.steps):
            if step.status == StepStatus.PENDING:
                return i
        return len(self.steps)
    
    @property
    def is_complete(self) -> bool:
        return all(
            s.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]
            for s in self.steps
        )
    
    @property
    def progress_percent(self) -> float:
        if not self.steps:
            return 100.0
        done = sum(
            1 for s in self.steps 
            if s.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]
        )
        return (done / len(self.steps)) * 100
    
    def get_summary(self) -> Dict:
        return {
            "plan_id": self.plan_id,
            "intent": self.intent,
            "total_steps": len(self.steps),
            "completed": sum(1 for s in self.steps if s.status == StepStatus.COMPLETED),
            "progress": f"{self.progress_percent:.0f}%",
            "version": self.version
        }


class PlanManager:
    """
    Creates and manages execution plans.
    
    Uses intent-specific templates and adapts based on
    available context and past execution results.
    """
    
    def __init__(self):
        self.plan_history: List[ExecutionPlan] = []
        self._plan_counter = 0
        
        # Templates for each intent type
        self.plan_templates = self._build_templates()
    
    def _build_templates(self) -> Dict[str, List[Dict]]:
        """Build intent-specific plan templates."""
        return {
            "standup_summary": [
                {
                    "action": "git_fetch_commits",
                    "params": {"since": "yesterday", "limit": 20},
                    "expected": "List of commit messages"
                },
                {
                    "action": "git_get_files_changed",
                    "params": {"since": "yesterday"},
                    "expected": "List of modified files"
                },
                {
                    "action": "summarize_activity",
                    "params": {},
                    "expected": "Structured summary"
                },
                {
                    "action": "format_standup_report",
                    "params": {"format": "markdown"},
                    "expected": "Formatted standup message"
                }
            ],
            
            "pr_description": [
                {
                    "action": "git_get_branch_info",
                    "params": {},
                    "expected": "Current branch details"
                },
                {
                    "action": "git_diff_main",
                    "params": {"stat": True},
                    "expected": "Diff statistics"
                },
                {
                    "action": "analyze_changes",
                    "params": {"categorize": True},
                    "expected": "Categorized changes"
                },
                {
                    "action": "generate_pr_template",
                    "params": {},
                    "expected": "PR description markdown"
                }
            ],
            
            "code_review": [
                {
                    "action": "load_target_files",
                    "params": {},
                    "expected": "File contents loaded"
                },
                {
                    "action": "analyze_complexity",
                    "params": {},
                    "expected": "Complexity metrics"
                },
                {
                    "action": "check_patterns",
                    "params": {"patterns": ["antipatterns", "bugs"]},
                    "expected": "Pattern matches"
                },
                {
                    "action": "generate_review_comments",
                    "params": {},
                    "expected": "Review feedback"
                }
            ],
            
            "tech_debt": [
                {
                    "action": "scan_project_structure",
                    "params": {},
                    "expected": "Project map"
                },
                {
                    "action": "analyze_code_quality",
                    "params": {"metrics": ["complexity", "duplication"]},
                    "expected": "Quality metrics"
                },
                {
                    "action": "identify_debt_items",
                    "params": {},
                    "expected": "Debt inventory"
                },
                {
                    "action": "prioritize_and_estimate",
                    "params": {},
                    "expected": "Prioritized debt list"
                }
            ],
            
            "dependency_check": [
                {
                    "action": "find_dependency_files",
                    "params": {},
                    "expected": "Manifest files found"
                },
                {
                    "action": "parse_dependencies",
                    "params": {},
                    "expected": "Parsed dependency list"
                },
                {
                    "action": "check_vulnerabilities",
                    "params": {"sources": ["cve", "npm", "pypi"]},
                    "expected": "Vulnerability report"
                },
                {
                    "action": "suggest_updates",
                    "params": {},
                    "expected": "Update recommendations"
                }
            ],
            
            "documentation": [
                {
                    "action": "parse_target_code",
                    "params": {},
                    "expected": "AST parsed"
                },
                {
                    "action": "extract_api_surface",
                    "params": {},
                    "expected": "Functions, classes, signatures"
                },
                {
                    "action": "generate_docstrings",
                    "params": {},
                    "expected": "Docstring content"
                },
                {
                    "action": "format_documentation",
                    "params": {"format": "markdown"},
                    "expected": "Final documentation"
                }
            ]
        }
    
    def create_plan(
        self, 
        intent: str, 
        context: Dict = None
    ) -> ExecutionPlan:
        """
        Create a new execution plan for the given intent.
        
        Args:
            intent: The classified developer intent
            context: Additional context (entities, temporal, etc.)
        
        Returns:
            ExecutionPlan ready for execution
        """
        self._plan_counter += 1
        plan_id = f"plan_{self._plan_counter:04d}"
        
        # Get template for intent
        template = self.plan_templates.get(intent, [
            {"action": "generic_process", "params": {}, "expected": "Response"}
        ])
        
        # Build steps from template
        steps = []
        for i, step_def in enumerate(template):
            step = PlanStep(
                step_id=f"{plan_id}_step_{i+1:02d}",
                action=step_def["action"],
                parameters=self._merge_params(step_def.get("params", {}), context),
                expected_output=step_def.get("expected", "")
            )
            steps.append(step)
        
        plan = ExecutionPlan(
            plan_id=plan_id,
            intent=intent,
            steps=steps
        )
        
        self.plan_history.append(plan)
        return plan
    
    def rewrite_plan(
        self, 
        original_plan: ExecutionPlan, 
        feedback: Dict
    ) -> ExecutionPlan:
        """
        Create a revised plan based on critique feedback.
        
        Args:
            original_plan: The plan that needs revision
            feedback: Critique feedback with issues and suggestions
        
        Returns:
            New ExecutionPlan with adjustments
        """
        self._plan_counter += 1
        plan_id = f"plan_{self._plan_counter:04d}"
        
        # Start with completed steps from original
        new_steps = []
        for step in original_plan.steps:
            if step.status == StepStatus.COMPLETED:
                # Clone completed step
                new_steps.append(PlanStep(
                    step_id=f"{plan_id}_step_{len(new_steps)+1:02d}",
                    action=step.action,
                    parameters=step.parameters,
                    expected_output=step.expected_output,
                    status=StepStatus.COMPLETED,
                    result=step.result
                ))
        
        # Add improvement steps based on feedback
        suggestions = feedback.get("suggestions", [])
        issues = feedback.get("issues", [])
        
        for suggestion in suggestions:
            suggestion_lower = suggestion.lower()
            
            if "detail" in suggestion_lower or "expand" in suggestion_lower:
                new_steps.append(PlanStep(
                    step_id=f"{plan_id}_step_{len(new_steps)+1:02d}",
                    action="expand_detail",
                    parameters={"focus_areas": issues},
                    expected_output="More detailed output"
                ))
            
            if "format" in suggestion_lower:
                new_steps.append(PlanStep(
                    step_id=f"{plan_id}_step_{len(new_steps)+1:02d}",
                    action="reformat_output",
                    parameters={"improve_structure": True},
                    expected_output="Better formatted output"
                ))
            
            if "verify" in suggestion_lower or "accuracy" in suggestion_lower:
                new_steps.append(PlanStep(
                    step_id=f"{plan_id}_step_{len(new_steps)+1:02d}",
                    action="verify_accuracy",
                    parameters={},
                    expected_output="Verified output"
                ))
        
        # Always add finalization step
        new_steps.append(PlanStep(
            step_id=f"{plan_id}_step_{len(new_steps)+1:02d}",
            action="finalize_output",
            parameters={},
            expected_output="Final polished output"
        ))
        
        new_plan = ExecutionPlan(
            plan_id=plan_id,
            intent=original_plan.intent,
            steps=new_steps,
            version=original_plan.version + 1,
            parent_plan_id=original_plan.plan_id
        )
        
        self.plan_history.append(new_plan)
        return new_plan
    
    def _merge_params(self, template_params: Dict, context: Dict = None) -> Dict:
        """Merge template parameters with context-specific values."""
        params = template_params.copy()
        
        if context:
            # Add file paths if specified
            if "file_path" in context.get("entities", {}):
                params["target_files"] = context["entities"]["file_path"]
            
            # Add temporal context
            if context.get("temporal", {}).get("reference"):
                params["time_reference"] = context["temporal"]["reference"]
        
        return params
    
    def get_plan_by_id(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Retrieve a plan by its ID."""
        for plan in self.plan_history:
            if plan.plan_id == plan_id:
                return plan
        return None
    
    def get_history_summary(self) -> List[Dict]:
        """Get summary of all plans."""
        return [plan.get_summary() for plan in self.plan_history]

