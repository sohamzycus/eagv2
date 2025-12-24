"""
Base Agent Interface and Context.

Follows Interface Segregation Principle - defines minimal required interface.
Follows Dependency Inversion - depends on abstractions (LLMClient, ReasoningStore).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional, Protocol, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from prompt_creator.core.llm.llm_client import LLMClient


class AgentCapability(Enum):
    """Capabilities that agents can have."""

    ROUTING = auto()
    GOVERNANCE = auto()
    STATE_CONTROL = auto()
    CLARIFICATION = auto()
    PROMPT_GENERATION = auto()
    TOOL_SYNTHESIS = auto()
    PERSISTENCE = auto()


class ReasoningStore(Protocol):
    """Protocol for reasoning persistence."""

    def log(
        self,
        session_id: str,
        agent_name: str,
        step: str,
        input_data: Any,
        decision: str,
        output: Any,
        next_step: Optional[str] = None,
    ) -> None:
        """Log a reasoning step."""
        ...


class LLMClientProtocol(Protocol):
    """Protocol for LLM client - allows any LLM implementation."""

    @property
    def provider_name(self) -> str:
        ...

    @property
    def model_name(self) -> str:
        ...

    def generate_simple(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> str:
        ...


@dataclass
class AgentContext:
    """
    Shared context passed between agents.

    Immutable-ish pattern - agents should not mutate context directly,
    but return new states via AgentResponse.
    """

    session_id: str = field(default_factory=lambda: str(uuid4()))
    user_input: str = ""
    current_step: str = "INIT"
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    intent: Optional[Any] = None  # BusinessIntent when available
    generated_prompt: Optional[str] = None
    generated_tools: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    reasoning_store: Optional[ReasoningStore] = None
    llm_client: Optional[LLMClientProtocol] = None  # LLM injection
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    # Model adaptation settings
    target_model_family: str = "gpt-4o"

    def with_user_input(self, user_input: str) -> "AgentContext":
        """Create new context with user input."""
        return AgentContext(
            session_id=self.session_id,
            user_input=user_input,
            current_step=self.current_step,
            conversation_history=self.conversation_history.copy(),
            intent=self.intent,
            generated_prompt=self.generated_prompt,
            generated_tools=self.generated_tools.copy(),
            metadata=self.metadata.copy(),
            reasoning_store=self.reasoning_store,
            llm_client=self.llm_client,
            created_at=self.created_at,
            target_model_family=self.target_model_family,
        )

    def add_to_history(self, role: str, content: str) -> None:
        """Add message to conversation history."""
        self.conversation_history.append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )

    def log_reasoning(
        self,
        agent_name: str,
        step: str,
        input_data: Any,
        decision: str,
        output: Any,
        next_step: Optional[str] = None,
    ) -> None:
        """Log reasoning if store is available."""
        if self.reasoning_store:
            self.reasoning_store.log(
                session_id=self.session_id,
                agent_name=agent_name,
                step=step,
                input_data=input_data,
                decision=decision,
                output=output,
                next_step=next_step,
            )


@dataclass
class AgentResponse:
    """
    Response from an agent's execute method.

    Follows Command Pattern - encapsulates result and side effects.
    """

    success: bool
    output: Any
    next_agent: Optional[str] = None
    next_step: Optional[str] = None
    reasoning: str = ""
    requires_user_input: bool = False
    user_message: Optional[str] = None
    updated_context: Optional[AgentContext] = None
    error: Optional[str] = None
    llm_tokens_used: int = 0  # Track token usage

    @classmethod
    def success_response(
        cls,
        output: Any,
        reasoning: str,
        next_agent: Optional[str] = None,
        next_step: Optional[str] = None,
        user_message: Optional[str] = None,
        requires_user_input: bool = False,
        llm_tokens_used: int = 0,
    ) -> "AgentResponse":
        """Factory for successful response."""
        return cls(
            success=True,
            output=output,
            reasoning=reasoning,
            next_agent=next_agent,
            next_step=next_step,
            user_message=user_message,
            requires_user_input=requires_user_input,
            llm_tokens_used=llm_tokens_used,
        )

    @classmethod
    def failure_response(cls, error: str, reasoning: str) -> "AgentResponse":
        """Factory for failure response."""
        return cls(
            success=False,
            output=None,
            error=error,
            reasoning=reasoning,
        )

    @classmethod
    def needs_input_response(
        cls, message: str, reasoning: str
    ) -> "AgentResponse":
        """Factory for response requiring user input."""
        return cls(
            success=True,
            output=None,
            reasoning=reasoning,
            requires_user_input=True,
            user_message=message,
        )


class Agent(ABC):
    """
    Abstract base class for all agents.

    Follows Template Method pattern - defines algorithm skeleton.
    Follows Open/Closed Principle - extend via subclasses.
    Follows Dependency Inversion - depends on LLMClient abstraction.
    """

    def __init__(
        self,
        name: str,
        capabilities: list[AgentCapability],
        llm_client: Optional["LLMClient"] = None,
        reasoning_store: Optional[ReasoningStore] = None,
    ):
        self._name = name
        self._capabilities = capabilities
        self._llm = llm_client  # LLM injection - agents use this abstraction
        self._reasoning_store = reasoning_store

    @property
    def name(self) -> str:
        """Get agent name."""
        return self._name

    @property
    def capabilities(self) -> list[AgentCapability]:
        """Get agent capabilities."""
        return self._capabilities

    @property
    def llm(self) -> Optional["LLMClient"]:
        """Get LLM client."""
        return self._llm

    def set_llm(self, llm_client: "LLMClient") -> None:
        """Inject LLM client (for late binding)."""
        self._llm = llm_client

    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has a specific capability."""
        return capability in self._capabilities

    def has_llm(self) -> bool:
        """Check if LLM is available."""
        return self._llm is not None

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
        context: Optional[AgentContext] = None,
    ) -> str:
        """
        Generate response using LLM.

        This is a convenience method that uses the injected LLM client.
        Agents should use this instead of calling LLM directly.
        """
        # Try agent's LLM first, then context's LLM
        llm = self._llm or (context.llm_client if context else None)

        if llm is None:
            raise ValueError(f"Agent {self._name} has no LLM client configured")

        return llm.generate_simple(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
        )

    @abstractmethod
    def execute(self, context: AgentContext) -> AgentResponse:
        """
        Execute agent logic.

        This is the template method - subclasses implement specific behavior.
        """
        pass

    @abstractmethod
    def can_handle(self, context: AgentContext) -> bool:
        """
        Check if this agent can handle the current context.

        Used for Chain of Responsibility pattern.
        """
        pass

    def to_mcp_zero_spec(self) -> dict[str, Any]:
        """Generate MCP-Zero compatible agent specification."""
        return {
            "agent": self._name,
            "capabilities": [cap.name.lower() for cap in self._capabilities],
        }


class LLMEnabledAgent(Agent):
    """
    Base class for agents that use LLM for reasoning.

    Provides common LLM interaction patterns.
    """

    def __init__(
        self,
        name: str,
        capabilities: list[AgentCapability],
        llm_client: Optional["LLMClient"] = None,
        reasoning_store: Optional[ReasoningStore] = None,
    ):
        super().__init__(name, capabilities, llm_client, reasoning_store)
        self._system_prompt: str = ""

    def set_system_prompt(self, prompt: str) -> None:
        """Set the system prompt for this agent."""
        self._system_prompt = prompt

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return self._system_prompt

    def ask_llm(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        context: Optional[AgentContext] = None,
    ) -> str:
        """
        Ask the LLM a question.

        Uses agent's system prompt if not provided.
        """
        prompt = system_prompt or self._system_prompt
        return self.generate(
            system_prompt=prompt,
            user_message=user_message,
            context=context,
        )

    def reason(
        self,
        task: str,
        context: Optional[AgentContext] = None,
    ) -> str:
        """
        Use LLM for reasoning about a task.

        Adds internal reasoning instructions.
        """
        reasoning_prompt = f"""
{self._system_prompt}

TASK: {task}

Think through this step by step. Consider:
1. What is being asked?
2. What information do I have?
3. What is the best approach?
4. What should I output?
"""
        return self.generate(
            system_prompt=reasoning_prompt,
            user_message=task,
            context=context,
        )
