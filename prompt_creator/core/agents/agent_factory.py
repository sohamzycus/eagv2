"""
Agent Factory.

Implements Factory Pattern for agent creation with LLM injection.
Follows Dependency Inversion - factory depends on abstractions.
"""

from enum import Enum, auto
from typing import TYPE_CHECKING, Optional

from .base_agent import Agent, ReasoningStore

if TYPE_CHECKING:
    from prompt_creator.core.llm.llm_client import LLMClient
    from .clarification_agent import ClarificationAgent
    from .intake_orchestrator import IntakeOrchestrator
    from .prompt_composer_agent import PromptComposerAgent, PromptAdapterAgent
    from .tool_synthesizer_agent import ToolSynthesizerAgent


class AgentType(Enum):
    """Types of agents available in the system."""

    INTAKE_ORCHESTRATOR = auto()
    CLARIFICATION = auto()
    PROMPT_COMPOSER = auto()
    PROMPT_ADAPTER = auto()
    TOOL_SYNTHESIZER = auto()


class AgentFactory:
    """
    Factory for creating agents with LLM injection.

    Implements Factory Pattern with dependency injection.
    All agents receive LLM client through the factory - never create their own.
    """

    _instance: Optional["AgentFactory"] = None
    _agents: dict[AgentType, Agent] = {}
    _llm_client: Optional["LLMClient"] = None
    _reasoning_store: Optional[ReasoningStore] = None

    def __new__(cls) -> "AgentFactory":
        """Singleton pattern for factory."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._agents = {}
            cls._llm_client = None
            cls._reasoning_store = None
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset factory state (useful for testing)."""
        cls._instance = None
        cls._agents = {}
        cls._llm_client = None
        cls._reasoning_store = None

    @classmethod
    def configure(
        cls,
        llm_client: Optional["LLMClient"] = None,
        reasoning_store: Optional[ReasoningStore] = None,
    ) -> "AgentFactory":
        """
        Configure the factory with LLM and reasoning store.

        This is called once at startup to inject dependencies.
        """
        instance = cls()
        cls._llm_client = llm_client
        cls._reasoning_store = reasoning_store
        return instance

    def create(
        self,
        agent_type: AgentType,
        llm_client: Optional["LLMClient"] = None,
        reasoning_store: Optional[ReasoningStore] = None,
    ) -> Agent:
        """
        Create an agent of the specified type.

        LLM client is injected from:
        1. Explicit parameter
        2. Factory configuration
        3. None (agent will work without LLM if possible)
        """
        # Use provided or factory-configured dependencies
        llm = llm_client or self._llm_client
        store = reasoning_store or self._reasoning_store

        # Return cached instance if exists with same LLM
        cache_key = (agent_type, id(llm))
        if agent_type in self._agents:
            existing = self._agents[agent_type]
            if hasattr(existing, '_llm') and existing._llm is llm:
                return existing

        # Create new instance
        agent = self._create_agent(agent_type, llm, store)
        self._agents[agent_type] = agent
        return agent

    def _create_agent(
        self,
        agent_type: AgentType,
        llm_client: Optional["LLMClient"],
        reasoning_store: Optional[ReasoningStore],
    ) -> Agent:
        """Internal method to create agent instances."""
        # Lazy imports to avoid circular dependencies
        from .clarification_agent import ClarificationAgent
        from .intake_orchestrator import IntakeOrchestrator
        from .prompt_composer_agent import PromptComposerAgent, PromptAdapterAgent
        from .tool_synthesizer_agent import ToolSynthesizerAgent

        creators = {
            AgentType.INTAKE_ORCHESTRATOR: lambda: IntakeOrchestrator(
                llm_client=llm_client,
                reasoning_store=reasoning_store,
            ),
            AgentType.CLARIFICATION: lambda: ClarificationAgent(
                llm_client=llm_client,
                reasoning_store=reasoning_store,
            ),
            AgentType.PROMPT_COMPOSER: lambda: PromptComposerAgent(
                llm_client=llm_client,
                reasoning_store=reasoning_store,
            ),
            AgentType.PROMPT_ADAPTER: lambda: PromptAdapterAgent(
                llm_client=llm_client,
                reasoning_store=reasoning_store,
            ),
            AgentType.TOOL_SYNTHESIZER: lambda: ToolSynthesizerAgent(
                llm_client=llm_client,
                reasoning_store=reasoning_store,
            ),
        }

        if agent_type not in creators:
            raise ValueError(f"Unknown agent type: {agent_type}")

        return creators[agent_type]()

    def get_all_agents(self) -> dict[AgentType, Agent]:
        """Get all created agents."""
        return self._agents.copy()

    def create_all(
        self,
        llm_client: Optional["LLMClient"] = None,
        reasoning_store: Optional[ReasoningStore] = None,
    ) -> dict[AgentType, Agent]:
        """Create all agent types with shared LLM client."""
        for agent_type in AgentType:
            self.create(
                agent_type,
                llm_client=llm_client,
                reasoning_store=reasoning_store,
            )
        return self._agents.copy()

    @property
    def has_llm(self) -> bool:
        """Check if factory has LLM configured."""
        return self._llm_client is not None

    @property
    def llm_info(self) -> dict:
        """Get LLM configuration info."""
        if not self._llm_client:
            return {"configured": False}
        return {
            "configured": True,
            "provider": self._llm_client.provider_name,
            "model": self._llm_client.model_name,
        }


class AgentRegistry:
    """
    Registry for managing agent instances.

    Provides lookup and lifecycle management for agents.
    """

    def __init__(self):
        self._agents: dict[str, Agent] = {}
        self._factory = AgentFactory()

    def register(self, agent: Agent) -> None:
        """Register an agent instance."""
        self._agents[agent.name] = agent

    def get(self, name: str) -> Optional[Agent]:
        """Get agent by name."""
        return self._agents.get(name)

    def get_or_create(
        self,
        agent_type: AgentType,
        llm_client: Optional["LLMClient"] = None,
    ) -> Agent:
        """Get existing agent or create new one."""
        agent = self._factory.create(agent_type, llm_client=llm_client)
        self.register(agent)
        return agent

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    def clear(self) -> None:
        """Clear all registered agents."""
        self._agents.clear()
