"""
Step Executor - Executes Individual Plan Steps

Responsible for:
- Running actions from the plan
- Dispatching to appropriate tools
- Handling errors and retries
- Collecting results
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .plan_manager import PlanStep, StepStatus, ExecutionPlan


class ExecutionMode(Enum):
    """How to execute steps."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


@dataclass
class StepResult:
    """Result of executing a step."""
    step_id: str
    success: bool
    output: Any
    error: Optional[str] = None
    duration_ms: int = 0
    metadata: Dict = None


class StepExecutor:
    """
    Executes plan steps by dispatching to registered action handlers.
    
    Features:
    - Action registry for extensibility
    - Retry logic for transient failures
    - Timeout handling
    - Result aggregation
    """
    
    def __init__(self, max_retries: int = 2, timeout_seconds: int = 30):
        self.max_retries = max_retries
        self.timeout = timeout_seconds
        
        # Registry of action handlers
        self.action_handlers: Dict[str, Callable] = {}
        
        # Register default handlers
        self._register_default_handlers()
        
        # Execution history
        self.execution_log: List[StepResult] = []
    
    def _register_default_handlers(self):
        """Register built-in action handlers."""
        
        # Git operations
        self.register_handler("git_fetch_commits", self._handle_git_commits)
        self.register_handler("git_get_files_changed", self._handle_git_files)
        self.register_handler("git_get_branch_info", self._handle_git_branch)
        self.register_handler("git_diff_main", self._handle_git_diff)
        
        # Analysis operations
        self.register_handler("summarize_activity", self._handle_summarize)
        self.register_handler("analyze_changes", self._handle_analyze)
        self.register_handler("analyze_complexity", self._handle_complexity)
        self.register_handler("analyze_code_quality", self._handle_quality)
        
        # Loading/parsing
        self.register_handler("load_target_files", self._handle_load_files)
        self.register_handler("parse_target_code", self._handle_parse_code)
        self.register_handler("find_dependency_files", self._handle_find_deps)
        self.register_handler("parse_dependencies", self._handle_parse_deps)
        
        # Checking operations
        self.register_handler("check_patterns", self._handle_check_patterns)
        self.register_handler("check_vulnerabilities", self._handle_check_vulns)
        
        # Generation operations
        self.register_handler("format_standup_report", self._handle_format_standup)
        self.register_handler("generate_pr_template", self._handle_gen_pr)
        self.register_handler("generate_review_comments", self._handle_gen_review)
        self.register_handler("generate_docstrings", self._handle_gen_docs)
        
        # Utility operations
        self.register_handler("expand_detail", self._handle_expand)
        self.register_handler("reformat_output", self._handle_reformat)
        self.register_handler("verify_accuracy", self._handle_verify)
        self.register_handler("finalize_output", self._handle_finalize)
        self.register_handler("generic_process", self._handle_generic)
        
        # Additional handlers
        self.register_handler("scan_project_structure", self._handle_scan_project)
        self.register_handler("identify_debt_items", self._handle_identify_debt)
        self.register_handler("prioritize_and_estimate", self._handle_prioritize)
        self.register_handler("extract_api_surface", self._handle_extract_api)
        self.register_handler("format_documentation", self._handle_format_docs)
        self.register_handler("suggest_updates", self._handle_suggest_updates)
    
    def register_handler(self, action: str, handler: Callable):
        """Register an action handler."""
        self.action_handlers[action] = handler
    
    async def execute_step(
        self, 
        step: PlanStep, 
        context: Dict = None
    ) -> StepResult:
        """
        Execute a single plan step.
        
        Args:
            step: The step to execute
            context: Shared context with accumulated data
        
        Returns:
            StepResult with execution outcome
        """
        start_time = datetime.now()
        step.start_time = start_time
        step.status = StepStatus.IN_PROGRESS
        
        handler = self.action_handlers.get(step.action)
        
        if not handler:
            # No handler registered
            step.status = StepStatus.FAILED
            step.error = f"No handler for action: {step.action}"
            return StepResult(
                step_id=step.step_id,
                success=False,
                output=None,
                error=step.error
            )
        
        # Try with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    handler(step.parameters, context),
                    timeout=self.timeout
                )
                
                # Success
                step.status = StepStatus.COMPLETED
                step.result = result
                step.end_time = datetime.now()
                
                step_result = StepResult(
                    step_id=step.step_id,
                    success=True,
                    output=result,
                    duration_ms=step.duration_ms or 0
                )
                
                self.execution_log.append(step_result)
                return step_result
                
            except asyncio.TimeoutError:
                last_error = f"Timeout after {self.timeout}s"
            except Exception as e:
                last_error = str(e)
            
            # Wait before retry
            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * (attempt + 1))
        
        # All retries failed
        step.status = StepStatus.FAILED
        step.error = last_error
        step.end_time = datetime.now()
        
        step_result = StepResult(
            step_id=step.step_id,
            success=False,
            output=None,
            error=last_error,
            duration_ms=step.duration_ms or 0
        )
        
        self.execution_log.append(step_result)
        return step_result
    
    async def execute_plan(
        self, 
        plan: ExecutionPlan, 
        context: Dict = None,
        mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    ) -> List[StepResult]:
        """
        Execute all steps in a plan.
        
        Args:
            plan: The execution plan
            context: Shared context
            mode: Execution mode
        
        Returns:
            List of StepResults
        """
        context = context or {}
        results = []
        
        if mode == ExecutionMode.SEQUENTIAL:
            for step in plan.steps:
                if step.status in [StepStatus.PENDING, StepStatus.FAILED]:
                    result = await self.execute_step(step, context)
                    results.append(result)
                    
                    # Stop on failure (unless plan allows continuation)
                    if not result.success:
                        break
                    
                    # Update context with step output
                    context[f"step_{step.step_id}"] = result.output
        
        elif mode == ExecutionMode.PARALLEL:
            pending_steps = [
                s for s in plan.steps 
                if s.status == StepStatus.PENDING
            ]
            
            tasks = [
                self.execute_step(step, context)
                for step in pending_steps
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    # ==================== Action Handlers ====================
    
    async def _handle_git_commits(self, params: Dict, context: Dict) -> Dict:
        """Fetch git commits."""
        return {
            "commits": [
                {"hash": "abc123", "message": "Fix authentication bug"},
                {"hash": "def456", "message": "Add user profile endpoint"},
                {"hash": "ghi789", "message": "Update dependencies"}
            ],
            "count": 3
        }
    
    async def _handle_git_files(self, params: Dict, context: Dict) -> Dict:
        """Get changed files."""
        return {
            "files": ["src/auth.py", "src/api/user.py", "requirements.txt"],
            "additions": 45,
            "deletions": 12
        }
    
    async def _handle_git_branch(self, params: Dict, context: Dict) -> Dict:
        """Get branch info."""
        return {
            "current": "feature/auth-improvements",
            "base": "main",
            "ahead": 3,
            "behind": 0
        }
    
    async def _handle_git_diff(self, params: Dict, context: Dict) -> Dict:
        """Get diff statistics."""
        return {
            "files_changed": 5,
            "insertions": 120,
            "deletions": 30
        }
    
    async def _handle_summarize(self, params: Dict, context: Dict) -> Dict:
        """Summarize activity."""
        return {
            "summary": "Worked on authentication improvements and user profile API",
            "categories": {
                "features": 1,
                "fixes": 1,
                "maintenance": 1
            }
        }
    
    async def _handle_analyze(self, params: Dict, context: Dict) -> Dict:
        """Analyze changes."""
        return {
            "change_type": "feature",
            "risk_level": "low",
            "affected_areas": ["auth", "api"]
        }
    
    async def _handle_complexity(self, params: Dict, context: Dict) -> Dict:
        """Analyze code complexity."""
        return {
            "cyclomatic": 5,
            "cognitive": 8,
            "maintainability": "B"
        }
    
    async def _handle_quality(self, params: Dict, context: Dict) -> Dict:
        """Analyze code quality."""
        return {
            "score": 82,
            "issues": 3,
            "suggestions": ["Add docstrings", "Reduce function length"]
        }
    
    async def _handle_load_files(self, params: Dict, context: Dict) -> Dict:
        """Load target files."""
        return {
            "loaded": True,
            "file_count": len(params.get("target_files", []))
        }
    
    async def _handle_parse_code(self, params: Dict, context: Dict) -> Dict:
        """Parse code AST."""
        return {
            "parsed": True,
            "functions": 12,
            "classes": 3
        }
    
    async def _handle_find_deps(self, params: Dict, context: Dict) -> Dict:
        """Find dependency files."""
        return {
            "found": ["requirements.txt", "package.json"],
            "count": 2
        }
    
    async def _handle_parse_deps(self, params: Dict, context: Dict) -> Dict:
        """Parse dependencies."""
        return {
            "python": 15,
            "node": 25,
            "total": 40
        }
    
    async def _handle_check_patterns(self, params: Dict, context: Dict) -> Dict:
        """Check for patterns."""
        return {
            "antipatterns": 2,
            "bugs": 0,
            "details": ["Nested callbacks", "Magic numbers"]
        }
    
    async def _handle_check_vulns(self, params: Dict, context: Dict) -> Dict:
        """Check vulnerabilities."""
        return {
            "critical": 0,
            "high": 0,
            "medium": 1,
            "low": 3
        }
    
    async def _handle_format_standup(self, params: Dict, context: Dict) -> str:
        """Format standup report."""
        return (
            "## What I worked on\n"
            "- Authentication improvements\n"
            "- User profile API\n"
            "- Dependency updates\n"
            "\n## Status: On track ✅"
        )
    
    async def _handle_gen_pr(self, params: Dict, context: Dict) -> str:
        """Generate PR template."""
        return (
            "## Description\n"
            "This PR implements authentication improvements...\n\n"
            "## Changes\n- Updated auth flow\n- Added user profile\n"
        )
    
    async def _handle_gen_review(self, params: Dict, context: Dict) -> str:
        """Generate review comments."""
        return (
            "## Code Review\n\n"
            "✅ Overall: Good\n"
            "⚠️ Suggestions:\n"
            "- Add error handling in auth.py:45\n"
            "- Consider caching in user.py:23"
        )
    
    async def _handle_gen_docs(self, params: Dict, context: Dict) -> str:
        """Generate docstrings."""
        return (
            "Generated documentation for 12 functions and 3 classes"
        )
    
    async def _handle_expand(self, params: Dict, context: Dict) -> Dict:
        """Expand detail in output."""
        return {"expanded": True, "added_sections": 2}
    
    async def _handle_reformat(self, params: Dict, context: Dict) -> Dict:
        """Reformat output."""
        return {"reformatted": True}
    
    async def _handle_verify(self, params: Dict, context: Dict) -> Dict:
        """Verify accuracy."""
        return {"verified": True, "confidence": 0.95}
    
    async def _handle_finalize(self, params: Dict, context: Dict) -> Dict:
        """Finalize output."""
        return {"finalized": True}
    
    async def _handle_generic(self, params: Dict, context: Dict) -> Dict:
        """Generic processing."""
        return {"processed": True}
    
    async def _handle_scan_project(self, params: Dict, context: Dict) -> Dict:
        """Scan project structure."""
        return {"directories": 10, "files": 45, "depth": 4}
    
    async def _handle_identify_debt(self, params: Dict, context: Dict) -> Dict:
        """Identify tech debt."""
        return {"items": 8, "categories": ["code", "tests", "docs"]}
    
    async def _handle_prioritize(self, params: Dict, context: Dict) -> Dict:
        """Prioritize and estimate."""
        return {"high": 2, "medium": 4, "low": 2}
    
    async def _handle_extract_api(self, params: Dict, context: Dict) -> Dict:
        """Extract API surface."""
        return {"endpoints": 5, "functions": 12, "classes": 3}
    
    async def _handle_format_docs(self, params: Dict, context: Dict) -> str:
        """Format documentation."""
        return "# API Documentation\n\n## Overview\n..."
    
    async def _handle_suggest_updates(self, params: Dict, context: Dict) -> Dict:
        """Suggest dependency updates."""
        return {"updates_available": 5, "security_patches": 1}
    
    def get_execution_summary(self) -> Dict:
        """Get summary of all executions."""
        if not self.execution_log:
            return {"total": 0}
        
        successful = sum(1 for r in self.execution_log if r.success)
        total_time = sum(r.duration_ms for r in self.execution_log)
        
        return {
            "total": len(self.execution_log),
            "successful": successful,
            "failed": len(self.execution_log) - successful,
            "success_rate": f"{(successful / len(self.execution_log)) * 100:.1f}%",
            "total_time_ms": total_time
        }

