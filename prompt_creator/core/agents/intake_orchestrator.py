"""
Intake Orchestrator Agent (Meta-Agent).

Owns the conversation lifecycle and controls agent routing.
Implements Chain of Responsibility for step flow.
Uses LLM for intelligent decision-making when needed.
"""

from enum import Enum, auto
from typing import Optional, TYPE_CHECKING

from .base_agent import (
    Agent,
    AgentCapability,
    AgentContext,
    AgentResponse,
    LLMEnabledAgent,
    ReasoningStore,
)

if TYPE_CHECKING:
    from prompt_creator.core.llm.llm_client import LLMClient


class OrchestratorState(Enum):
    """States in the orchestration flow."""

    INIT = auto()
    CLARIFYING = auto()
    COMPOSING_PROMPT = auto()
    SYNTHESIZING_TOOLS = auto()
    ADAPTING_PROMPT = auto()  # New: Model-specific adaptation
    REVIEW = auto()
    COMPLETE = auto()
    ERROR = auto()


ORCHESTRATOR_SYSTEM_PROMPT = """You are a Workflow Orchestrator for a Prompt Creation System.

Your role is to:
1. Track the current state of the prompt creation process
2. Decide which agent should act next
3. Ensure steps are followed in order (never skip)
4. Enforce governance rules

States in order:
1. CLARIFYING - Gather business requirements
2. COMPOSING_PROMPT - Generate system prompt
3. SYNTHESIZING_TOOLS - Generate tool specifications
4. ADAPTING_PROMPT - Adapt for target model (optional)
5. REVIEW - Final review
6. COMPLETE - Done

You must enforce:
- No state skipping
- All required information before proceeding
- Error recovery when needed"""


class IntakeOrchestrator(LLMEnabledAgent):
    """
    Meta-agent that controls the conversation lifecycle.

    Responsibilities:
    - Flow control between agents
    - State management
    - Enforcement of step ordering (no skipping)
    - Governance and guardrails
    """

    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        reasoning_store: Optional[ReasoningStore] = None,
    ):
        super().__init__(
            name="intake_orchestrator",
            capabilities=[
                AgentCapability.ROUTING,
                AgentCapability.GOVERNANCE,
                AgentCapability.STATE_CONTROL,
            ],
            llm_client=llm_client,
            reasoning_store=reasoning_store,
        )
        self._state = OrchestratorState.INIT
        self._agent_sequence = [
            ("clarification_agent", OrchestratorState.CLARIFYING),
            ("prompt_composer_agent", OrchestratorState.COMPOSING_PROMPT),
            ("tool_synthesizer_agent", OrchestratorState.SYNTHESIZING_TOOLS),
        ]
        self._current_agent_index = 0
        self.set_system_prompt(ORCHESTRATOR_SYSTEM_PROMPT)

    @property
    def current_state(self) -> OrchestratorState:
        """Get current orchestrator state."""
        return self._state

    def reset(self) -> None:
        """Reset orchestrator to initial state."""
        self._state = OrchestratorState.INIT
        self._current_agent_index = 0

    def can_handle(self, context: AgentContext) -> bool:
        """Orchestrator can always handle - it's the entry point."""
        return True

    def execute(self, context: AgentContext) -> AgentResponse:
        """
        Execute orchestration logic.

        Determines which agent should act next based on current state.
        """
        # Log reasoning
        context.log_reasoning(
            agent_name=self.name,
            step=f"STATE_{self._state.name}",
            input_data={"user_input": context.user_input, "state": self._state.name},
            decision="Determining next agent",
            output=None,
            next_step=None,
        )

        # Handle initial state
        if self._state == OrchestratorState.INIT:
            return self._handle_init(context)

        # Handle clarifying state
        if self._state == OrchestratorState.CLARIFYING:
            return self._handle_clarifying(context)

        # Handle prompt composition
        if self._state == OrchestratorState.COMPOSING_PROMPT:
            return self._handle_composing(context)

        # Handle tool synthesis
        if self._state == OrchestratorState.SYNTHESIZING_TOOLS:
            return self._handle_synthesizing(context)

        # Handle review
        if self._state == OrchestratorState.REVIEW:
            return self._handle_review(context)

        # Handle complete
        if self._state == OrchestratorState.COMPLETE:
            return AgentResponse.success_response(
                output={"prompt": context.generated_prompt, "tools": context.generated_tools},
                reasoning="Generation complete",
                user_message="Your prompt and tools have been generated successfully!",
            )

        # Handle error
        return AgentResponse.failure_response(
            error=f"Unknown state: {self._state}",
            reasoning="Orchestrator in unknown state",
        )

    def _handle_init(self, context: AgentContext) -> AgentResponse:
        """Handle initial state - start clarification."""
        self._state = OrchestratorState.CLARIFYING

        context.log_reasoning(
            agent_name=self.name,
            step="INIT_TO_CLARIFYING",
            input_data={"user_input": context.user_input},
            decision="Starting clarification process",
            output={"next_state": "CLARIFYING"},
            next_step="clarification_agent",
        )

        return AgentResponse.success_response(
            output={"action": "start_clarification"},
            reasoning="Initial user input received, starting clarification",
            next_agent="clarification_agent",
            next_step="CLARIFICATION_START",
        )

    def _handle_clarifying(self, context: AgentContext) -> AgentResponse:
        """Handle clarification state."""
        # Check if intent is complete
        if context.intent is not None:
            self._state = OrchestratorState.COMPOSING_PROMPT

            context.log_reasoning(
                agent_name=self.name,
                step="CLARIFYING_TO_COMPOSING",
                input_data={"intent": str(context.intent)},
                decision="Intent complete, proceeding to prompt composition",
                output={"next_state": "COMPOSING_PROMPT"},
                next_step="prompt_composer_agent",
            )

            return AgentResponse.success_response(
                output={"action": "compose_prompt"},
                reasoning="Clarification complete, intent captured",
                next_agent="prompt_composer_agent",
                next_step="PROMPT_COMPOSITION_START",
            )

        # Continue clarification
        return AgentResponse.success_response(
            output={"action": "continue_clarification"},
            reasoning="Still gathering requirements",
            next_agent="clarification_agent",
            requires_user_input=True,
        )

    def _handle_composing(self, context: AgentContext) -> AgentResponse:
        """Handle prompt composition state."""
        # Check if prompt is generated
        if context.generated_prompt is not None:
            self._state = OrchestratorState.SYNTHESIZING_TOOLS

            context.log_reasoning(
                agent_name=self.name,
                step="COMPOSING_TO_SYNTHESIZING",
                input_data={"prompt_length": len(context.generated_prompt)},
                decision="Prompt generated, proceeding to tool synthesis",
                output={"next_state": "SYNTHESIZING_TOOLS"},
                next_step="tool_synthesizer_agent",
            )

            return AgentResponse.success_response(
                output={"action": "synthesize_tools"},
                reasoning="Prompt generated successfully",
                next_agent="tool_synthesizer_agent",
                next_step="TOOL_SYNTHESIS_START",
            )

        # Continue composition
        return AgentResponse.success_response(
            output={"action": "continue_composition"},
            reasoning="Generating prompt",
            next_agent="prompt_composer_agent",
        )

    def _handle_synthesizing(self, context: AgentContext) -> AgentResponse:
        """Handle tool synthesis state."""
        # Check if tools are generated
        if context.generated_tools:
            self._state = OrchestratorState.REVIEW

            context.log_reasoning(
                agent_name=self.name,
                step="SYNTHESIZING_TO_REVIEW",
                input_data={"tool_count": len(context.generated_tools)},
                decision="Tools generated, proceeding to review",
                output={"next_state": "REVIEW"},
                next_step="REVIEW",
            )

            return AgentResponse.success_response(
                output={"action": "review"},
                reasoning="Tools synthesized successfully",
                next_step="REVIEW",
                user_message="Your prompt and tools are ready for review.",
            )

        # Continue synthesis
        return AgentResponse.success_response(
            output={"action": "continue_synthesis"},
            reasoning="Generating tool specifications",
            next_agent="tool_synthesizer_agent",
        )

    def _handle_review(self, context: AgentContext) -> AgentResponse:
        """Handle review state."""
        self._state = OrchestratorState.COMPLETE

        context.log_reasoning(
            agent_name=self.name,
            step="REVIEW_TO_COMPLETE",
            input_data={},
            decision="Review complete",
            output={"next_state": "COMPLETE"},
            next_step=None,
        )

        return AgentResponse.success_response(
            output={
                "prompt": context.generated_prompt,
                "tools": context.generated_tools,
            },
            reasoning="Generation and review complete",
            user_message=self._generate_completion_message(context),
        )

    def _generate_completion_message(self, context: AgentContext) -> str:
        """Generate completion message with stats."""
        prompt_len = len(context.generated_prompt) if context.generated_prompt else 0
        tool_count = len(context.generated_tools) if context.generated_tools else 0

        llm_info = ""
        if self._llm:
            llm_info = f"\n**Model Used:** {self._llm.provider_name} / {self._llm.model_name}"

        return f"""🎉 **Generation Complete!**

Your procurement assistant prompt is ready!

**Statistics:**
- System Prompt: {prompt_len:,} characters
- MCP-Zero Tools: {tool_count} specifications
{llm_info}

**Next Steps:**
1. Review the generated prompt in the **Generated Prompt** tab
2. Check the tool specifications in the **Tools** tab
3. Download and deploy to your LLM runtime

Would you like to make any modifications?"""

    def advance_to_next_agent(self) -> Optional[str]:
        """
        Advance to next agent in sequence.

        Returns next agent name or None if complete.
        """
        if self._current_agent_index >= len(self._agent_sequence):
            self._state = OrchestratorState.COMPLETE
            return None

        agent_name, new_state = self._agent_sequence[self._current_agent_index]
        self._state = new_state
        self._current_agent_index += 1
        return agent_name

    def enforce_no_skip(self, requested_state: OrchestratorState) -> bool:
        """
        Enforce that states cannot be skipped.

        Returns True if the transition is valid.
        """
        valid_transitions = {
            OrchestratorState.INIT: [OrchestratorState.CLARIFYING],
            OrchestratorState.CLARIFYING: [OrchestratorState.COMPOSING_PROMPT],
            OrchestratorState.COMPOSING_PROMPT: [OrchestratorState.SYNTHESIZING_TOOLS],
            OrchestratorState.SYNTHESIZING_TOOLS: [OrchestratorState.ADAPTING_PROMPT, OrchestratorState.REVIEW],
            OrchestratorState.ADAPTING_PROMPT: [OrchestratorState.REVIEW],
            OrchestratorState.REVIEW: [OrchestratorState.COMPLETE],
            OrchestratorState.COMPLETE: [],
            OrchestratorState.ERROR: [],
        }

        return requested_state in valid_transitions.get(self._state, [])

    def get_progress(self) -> dict:
        """Get current progress information."""
        state_order = [
            OrchestratorState.INIT,
            OrchestratorState.CLARIFYING,
            OrchestratorState.COMPOSING_PROMPT,
            OrchestratorState.SYNTHESIZING_TOOLS,
            OrchestratorState.REVIEW,
            OrchestratorState.COMPLETE,
        ]
        current_index = state_order.index(self._state) if self._state in state_order else 0
        total = len(state_order) - 1

        return {
            "current_state": self._state.name,
            "progress_percent": min(100, int((current_index / total) * 100)),
            "steps_completed": current_index,
            "total_steps": total,
            "has_llm": self.has_llm(),
            "model": self._llm.model_name if self._llm else "None",
        }
