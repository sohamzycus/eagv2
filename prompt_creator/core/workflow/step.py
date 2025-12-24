"""
Step Definition and Execution.

Implements Chain of Responsibility pattern for step flow.
Each step knows how to execute and route to next step.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Optional


class StepStatus(Enum):
    """Status of a workflow step."""

    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    SKIPPED = auto()
    FAILED = auto()
    BLOCKED = auto()


@dataclass
class StepResult:
    """Result of executing a step."""

    status: StepStatus
    output: Any = None
    next_step_id: Optional[str] = None
    reasoning: str = ""
    error: Optional[str] = None
    duration_ms: int = 0

    @classmethod
    def success(
        cls,
        output: Any,
        next_step_id: str,
        reasoning: str = "",
        duration_ms: int = 0,
    ) -> "StepResult":
        """Create successful result."""
        return cls(
            status=StepStatus.COMPLETED,
            output=output,
            next_step_id=next_step_id,
            reasoning=reasoning,
            duration_ms=duration_ms,
        )

    @classmethod
    def failure(cls, error: str, reasoning: str = "") -> "StepResult":
        """Create failure result."""
        return cls(
            status=StepStatus.FAILED,
            error=error,
            reasoning=reasoning,
        )

    @classmethod
    def blocked(cls, reason: str) -> "StepResult":
        """Create blocked result."""
        return cls(
            status=StepStatus.BLOCKED,
            reasoning=reason,
        )


@dataclass
class StepContext:
    """Context passed to step execution."""

    session_id: str
    step_id: str
    inputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    previous_outputs: dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)


class Step(ABC):
    """
    Abstract base class for workflow steps.

    Implements Template Method pattern - defines execution skeleton.
    """

    def __init__(
        self,
        step_id: str,
        name: str,
        description: str,
        required_inputs: list[str] = None,
        optional_inputs: list[str] = None,
    ):
        self._step_id = step_id
        self._name = name
        self._description = description
        self._required_inputs = required_inputs or []
        self._optional_inputs = optional_inputs or []
        self._next_step: Optional["Step"] = None
        self._condition_handlers: dict[str, str] = {}

    @property
    def step_id(self) -> str:
        """Get step ID."""
        return self._step_id

    @property
    def name(self) -> str:
        """Get step name."""
        return self._name

    @property
    def description(self) -> str:
        """Get step description."""
        return self._description

    def set_next(self, step: "Step") -> "Step":
        """Set next step in chain (Chain of Responsibility)."""
        self._next_step = step
        return step

    def add_condition(self, condition: str, next_step_id: str) -> "Step":
        """Add conditional routing."""
        self._condition_handlers[condition] = next_step_id
        return self

    def validate_inputs(self, context: StepContext) -> tuple[bool, list[str]]:
        """Validate that required inputs are present."""
        missing = []
        for req in self._required_inputs:
            if req not in context.inputs and req not in context.previous_outputs:
                missing.append(req)
        return len(missing) == 0, missing

    def execute(self, context: StepContext) -> StepResult:
        """
        Template method for step execution.

        1. Validate inputs
        2. Execute step logic
        3. Determine next step
        """
        # Validate
        is_valid, missing = self.validate_inputs(context)
        if not is_valid:
            return StepResult.failure(
                error=f"Missing required inputs: {missing}",
                reasoning=f"Step {self._step_id} blocked due to missing inputs",
            )

        # Execute
        start_time = datetime.now()
        try:
            result = self._execute(context)
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            result.duration_ms = duration
            return result
        except Exception as e:
            return StepResult.failure(
                error=str(e),
                reasoning=f"Step {self._step_id} failed with exception",
            )

    @abstractmethod
    def _execute(self, context: StepContext) -> StepResult:
        """Implement step-specific logic."""
        pass

    def to_prompt_section(self) -> str:
        """Generate prompt section for this step."""
        lines = [
            f"### {self._step_id}: {self._name}",
            "",
            f"**Purpose:** {self._description}",
            "",
        ]

        if self._required_inputs:
            lines.append("**Required Inputs:**")
            for inp in self._required_inputs:
                lines.append(f"- {inp}")
            lines.append("")

        if self._condition_handlers:
            lines.append("**Routing:**")
            for condition, next_id in self._condition_handlers.items():
                lines.append(f"- IF {condition} → {next_id}")

        return "\n".join(lines)


class ConcreteStep(Step):
    """
    Concrete step implementation using callbacks.

    Allows dynamic step creation without subclassing.
    """

    def __init__(
        self,
        step_id: str,
        name: str,
        description: str,
        executor: Callable[[StepContext], StepResult],
        required_inputs: list[str] = None,
        optional_inputs: list[str] = None,
    ):
        super().__init__(step_id, name, description, required_inputs, optional_inputs)
        self._executor = executor

    def _execute(self, context: StepContext) -> StepResult:
        """Execute using provided callback."""
        return self._executor(context)


class StepChain:
    """
    Manages a chain of steps.

    Implements Chain of Responsibility - steps process in order.
    """

    def __init__(self):
        self._steps: dict[str, Step] = {}
        self._first_step: Optional[Step] = None
        self._current_step: Optional[Step] = None

    def add_step(self, step: Step) -> "StepChain":
        """Add a step to the chain."""
        self._steps[step.step_id] = step

        if self._first_step is None:
            self._first_step = step
        elif self._current_step:
            self._current_step.set_next(step)

        self._current_step = step
        return self

    def get_step(self, step_id: str) -> Optional[Step]:
        """Get step by ID."""
        return self._steps.get(step_id)

    def execute_from(
        self,
        step_id: str,
        context: StepContext,
    ) -> list[StepResult]:
        """Execute chain starting from specified step."""
        results = []
        current = self.get_step(step_id)

        while current:
            context.step_id = current.step_id
            result = current.execute(context)
            results.append(result)

            if result.status != StepStatus.COMPLETED:
                break

            # Get next step
            if result.next_step_id:
                current = self.get_step(result.next_step_id)
            else:
                current = current._next_step

            # Update context with previous output
            if result.output:
                context.previous_outputs[current.step_id if current else "final"] = (
                    result.output
                )

        return results

    def get_all_steps(self) -> list[Step]:
        """Get all steps in order."""
        return list(self._steps.values())

