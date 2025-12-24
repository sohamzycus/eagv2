"""
Workflow Engine.

Orchestrates step execution and COVE validation.
Maintains workflow state and ensures deterministic execution.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional

from .step import Step, StepChain, StepContext, StepResult, StepStatus
from .cove import COVEValidator, COVEResult, StandardCOVERules


class WorkflowStatus(Enum):
    """Overall workflow status."""

    NOT_STARTED = auto()
    IN_PROGRESS = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class WorkflowState:
    """
    Complete state of a workflow execution.

    Immutable pattern - state changes create new instances.
    """

    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.NOT_STARTED
    current_step_id: Optional[str] = None
    completed_steps: list[str] = field(default_factory=list)
    step_results: dict[str, StepResult] = field(default_factory=dict)
    cove_results: dict[str, COVEResult] = field(default_factory=dict)
    context_data: dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def start(self, first_step_id: str) -> "WorkflowState":
        """Start the workflow."""
        return WorkflowState(
            workflow_id=self.workflow_id,
            status=WorkflowStatus.IN_PROGRESS,
            current_step_id=first_step_id,
            started_at=datetime.now(),
        )

    def complete_step(
        self,
        step_id: str,
        result: StepResult,
        next_step_id: Optional[str],
    ) -> "WorkflowState":
        """Record step completion."""
        new_completed = self.completed_steps + [step_id]
        new_results = {**self.step_results, step_id: result}

        return WorkflowState(
            workflow_id=self.workflow_id,
            status=WorkflowStatus.IN_PROGRESS,
            current_step_id=next_step_id,
            completed_steps=new_completed,
            step_results=new_results,
            cove_results=self.cove_results.copy(),
            context_data=self.context_data.copy(),
            started_at=self.started_at,
        )

    def add_cove_result(
        self,
        step_id: str,
        result: COVEResult,
    ) -> "WorkflowState":
        """Add COVE validation result."""
        new_cove_results = {**self.cove_results, step_id: result}
        return WorkflowState(
            workflow_id=self.workflow_id,
            status=self.status,
            current_step_id=self.current_step_id,
            completed_steps=self.completed_steps.copy(),
            step_results=self.step_results.copy(),
            cove_results=new_cove_results,
            context_data=self.context_data.copy(),
            started_at=self.started_at,
        )

    def complete(self) -> "WorkflowState":
        """Mark workflow as complete."""
        return WorkflowState(
            workflow_id=self.workflow_id,
            status=WorkflowStatus.COMPLETED,
            current_step_id=None,
            completed_steps=self.completed_steps.copy(),
            step_results=self.step_results.copy(),
            cove_results=self.cove_results.copy(),
            context_data=self.context_data.copy(),
            started_at=self.started_at,
            completed_at=datetime.now(),
        )

    def fail(self, error: str) -> "WorkflowState":
        """Mark workflow as failed."""
        return WorkflowState(
            workflow_id=self.workflow_id,
            status=WorkflowStatus.FAILED,
            current_step_id=self.current_step_id,
            completed_steps=self.completed_steps.copy(),
            step_results=self.step_results.copy(),
            cove_results=self.cove_results.copy(),
            context_data=self.context_data.copy(),
            started_at=self.started_at,
            completed_at=datetime.now(),
            error=error,
        )

    def get_progress(self) -> dict[str, Any]:
        """Get progress summary."""
        total_time = None
        if self.started_at:
            end_time = self.completed_at or datetime.now()
            total_time = (end_time - self.started_at).total_seconds()

        return {
            "workflow_id": self.workflow_id,
            "status": self.status.name,
            "steps_completed": len(self.completed_steps),
            "current_step": self.current_step_id,
            "cove_violations": sum(
                len(r.violations) for r in self.cove_results.values()
            ),
            "total_time_seconds": total_time,
            "error": self.error,
        }


class WorkflowEngine:
    """
    Engine for executing workflows with COVE validation.

    Ensures deterministic execution and validates all COVE rules.
    """

    def __init__(
        self,
        cove_validator: Optional[COVEValidator] = None,
        strict_mode: bool = True,
    ):
        self._step_chain = StepChain()
        self._cove_validator = cove_validator or StandardCOVERules.create_validator()
        self._strict_mode = strict_mode
        self._state: Optional[WorkflowState] = None

    def register_step(self, step: Step) -> "WorkflowEngine":
        """Register a step in the workflow."""
        self._step_chain.add_step(step)
        return self

    def register_steps(self, steps: list[Step]) -> "WorkflowEngine":
        """Register multiple steps."""
        for step in steps:
            self.register_step(step)
        return self

    @property
    def state(self) -> Optional[WorkflowState]:
        """Get current workflow state."""
        return self._state

    def start(self, workflow_id: str, initial_context: dict[str, Any] = None) -> WorkflowState:
        """Start a new workflow execution."""
        first_step = self._step_chain.get_all_steps()[0] if self._step_chain.get_all_steps() else None
        if not first_step:
            raise ValueError("No steps registered in workflow")

        self._state = WorkflowState(
            workflow_id=workflow_id,
            context_data=initial_context or {},
        ).start(first_step.step_id)

        return self._state

    def execute_step(self, step_id: str, inputs: dict[str, Any]) -> tuple[StepResult, COVEResult]:
        """
        Execute a single step with COVE validation.

        Returns both step result and COVE validation result.
        """
        if not self._state:
            raise ValueError("Workflow not started")

        # Validate step ordering (COVE_01)
        if self._strict_mode and step_id != self._state.current_step_id:
            # Check if this is a valid skip (some steps allow conditional skipping)
            if step_id not in self._get_valid_next_steps():
                cove_result = COVEResult.failure(
                    StandardCOVERules.no_step_skipping().validate({
                        "step_order_valid": False,
                        "expected_step": self._state.current_step_id,
                        "attempted_step": step_id,
                    }).violations[0]
                )
                return StepResult.blocked("Step skipping not allowed"), cove_result

        # Get step
        step = self._step_chain.get_step(step_id)
        if not step:
            return StepResult.failure(f"Step {step_id} not found"), COVEResult.success()

        # Create step context
        context = StepContext(
            session_id=self._state.workflow_id,
            step_id=step_id,
            inputs=inputs,
            previous_outputs={
                sid: self._state.step_results[sid].output
                for sid in self._state.completed_steps
                if self._state.step_results[sid].output
            },
            metadata=self._state.context_data,
        )

        # Execute step
        step_result = step.execute(context)

        # Validate COVE rules
        cove_context = {
            "step_id": step_id,
            "step_result": step_result,
            "inputs": inputs,
            "outputs": step_result.output,
            "tool_called": inputs.get("tool_called", False),
            "step_order_valid": True,
            **self._state.context_data,
        }
        cove_result = self._cove_validator.validate_all(cove_context)

        # Update state
        if step_result.status == StepStatus.COMPLETED:
            next_step = step_result.next_step_id or self._get_default_next_step(step_id)
            self._state = self._state.complete_step(step_id, step_result, next_step)
            self._state = self._state.add_cove_result(step_id, cove_result)

            # Check if workflow complete
            if next_step is None:
                self._state = self._state.complete()
        elif step_result.status == StepStatus.FAILED:
            if self._strict_mode:
                self._state = self._state.fail(step_result.error or "Step failed")

        return step_result, cove_result

    def execute_all(self, inputs_by_step: dict[str, dict[str, Any]] = None) -> WorkflowState:
        """Execute all steps in sequence."""
        if not self._state:
            raise ValueError("Workflow not started")

        inputs_by_step = inputs_by_step or {}

        while self._state.status == WorkflowStatus.IN_PROGRESS and self._state.current_step_id:
            step_id = self._state.current_step_id
            inputs = inputs_by_step.get(step_id, {})

            step_result, cove_result = self.execute_step(step_id, inputs)

            if step_result.status == StepStatus.FAILED:
                break
            if not cove_result.passed and self._strict_mode:
                self._state = self._state.fail(
                    f"COVE validation failed: {cove_result.violations[0].message}"
                )
                break

        return self._state

    def _get_valid_next_steps(self) -> list[str]:
        """Get list of valid next steps from current state."""
        if not self._state or not self._state.current_step_id:
            return []

        current_step = self._step_chain.get_step(self._state.current_step_id)
        if not current_step:
            return []

        # Get conditional next steps
        valid = list(current_step._condition_handlers.values())

        # Add default next step
        if current_step._next_step:
            valid.append(current_step._next_step.step_id)

        return valid

    def _get_default_next_step(self, step_id: str) -> Optional[str]:
        """Get default next step after given step."""
        step = self._step_chain.get_step(step_id)
        if step and step._next_step:
            return step._next_step.step_id
        return None

    def get_all_steps(self) -> list[Step]:
        """Get all registered steps."""
        return self._step_chain.get_all_steps()

    def to_prompt_section(self) -> str:
        """Generate prompt section describing the workflow."""
        lines = ["## Workflow Steps", ""]

        for step in self._step_chain.get_all_steps():
            lines.append(step.to_prompt_section())
            lines.append("")

        lines.append(self._cove_validator.to_prompt_section())

        return "\n".join(lines)

