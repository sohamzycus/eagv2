"""
Prompt Composer Agent.

Translates BusinessIntent into full system prompts with STEP/COVE logic.
Uses LLM for intelligent prompt generation and model-specific adaptation.
"""

import json
from typing import Optional, TYPE_CHECKING

from prompt_creator.domain.business_intent import BusinessIntent, ProcurementChannel

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


# System prompt for the Prompt Composer
COMPOSER_SYSTEM_PROMPT = """You are an expert System Prompt Architect specializing in enterprise AI agents.

Your task is to generate production-ready system prompts for procurement AI assistants.

The generated prompt MUST include:
1. **System Identity** - Clear role definition
2. **Core Rules** - Deterministic behavior rules
3. **Guardrails** - What the agent must/must not do
4. **Workflow Steps** - Ordered STEP_XX definitions
5. **COVE Rules** - Chain of Validation Enforcement
6. **Tool Discipline** - When and how to use tools
7. **Message Formatting** - How to format responses
8. **Error Handling** - How to handle failures

CRITICAL REQUIREMENTS:
- Steps must be numbered (STEP_01, STEP_02, etc.)
- Each step must have: Purpose, Inputs, Outputs, Routing
- Guardrails must use NEVER/ALWAYS language
- Internal reasoning must be hidden from users
- Tool calls must happen BEFORE responding with data

Output the complete system prompt in Markdown format."""


PROMPT_REFINEMENT_PROMPT = """You are a Prompt Quality Reviewer.

Review this system prompt and suggest improvements for:
1. Clarity of instructions
2. Completeness of guardrails
3. Step ordering logic
4. Tool usage patterns

Output your refined version of the prompt."""


class PromptComposerAgent(LLMEnabledAgent):
    """
    Agent responsible for generating system prompts.

    Uses LLM to generate prompts equivalent to Buy Agent v5.0:
    - Step ordering (STEP_01 → STEP_20)
    - Guardrails
    - Hidden chain-of-thought
    - Tool-first discipline
    """

    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        reasoning_store: Optional[ReasoningStore] = None,
    ):
        super().__init__(
            name="prompt_composer_agent",
            capabilities=[AgentCapability.PROMPT_GENERATION],
            llm_client=llm_client,
            reasoning_store=reasoning_store,
        )
        self.set_system_prompt(COMPOSER_SYSTEM_PROMPT)

    def can_handle(self, context: AgentContext) -> bool:
        """Can handle if intent exists but prompt not yet generated."""
        return context.intent is not None and context.generated_prompt is None

    def execute(self, context: AgentContext) -> AgentResponse:
        """Generate the system prompt from business intent."""
        if context.intent is None:
            return AgentResponse.failure_response(
                error="No business intent available",
                reasoning="Cannot compose prompt without intent",
            )

        intent: BusinessIntent = context.intent

        context.log_reasoning(
            agent_name=self.name,
            step="PROMPT_COMPOSITION_START",
            input_data={
                "use_case": intent.use_case_name,
                "channels": intent.get_enabled_channel_names(),
            },
            decision="Starting prompt generation",
            output=None,
            next_step="GENERATE_WITH_LLM",
        )

        # Try LLM-based generation first
        llm = self._llm or context.llm_client
        if llm:
            prompt = self._generate_with_llm(intent, context)
        else:
            # Fallback to builder pattern
            prompt = self._generate_with_builder(intent)

        context.generated_prompt = prompt

        context.log_reasoning(
            agent_name=self.name,
            step="PROMPT_COMPOSITION_COMPLETE",
            input_data={"intent": intent.use_case_name},
            decision="Prompt generated successfully",
            output={"prompt_length": len(prompt), "sections_count": prompt.count("##")},
            next_step="tool_synthesizer_agent",
        )

        return AgentResponse.success_response(
            output={"prompt": prompt},
            reasoning=f"Generated {len(prompt)} character prompt with full STEP/COVE logic",
            next_agent="intake_orchestrator",
            user_message=f"✅ System prompt generated ({len(prompt):,} characters)",
        )

    def _generate_with_llm(
        self,
        intent: BusinessIntent,
        context: AgentContext,
    ) -> str:
        """Generate prompt using LLM."""
        llm = self._llm or context.llm_client

        # Build specification for LLM
        spec = self._build_specification(intent)

        # Generate initial prompt
        initial_prompt = f"""Generate a complete system prompt for this procurement assistant:

**Specification:**
```json
{json.dumps(spec, indent=2)}
```

Requirements:
- The prompt should be 10,000+ characters
- Include at least 12 workflow steps (STEP_01 to STEP_12)
- Include at least 8 guardrails
- Include COVE validation rules
- Include tool usage patterns for each enabled capability
- Make it production-ready

Generate the complete system prompt now."""

        try:
            response = llm.generate_simple(
                system_prompt=self._system_prompt,
                user_message=initial_prompt,
                temperature=0.2,
            )

            # If response is too short, enhance it
            if len(response) < 5000:
                response = self._enhance_prompt(response, intent, llm)

            return response

        except Exception as e:
            # Fallback to builder
            return self._generate_with_builder(intent)

    def _enhance_prompt(
        self,
        initial_prompt: str,
        intent: BusinessIntent,
        llm,
    ) -> str:
        """Enhance a short prompt with more detail."""
        enhancement_request = f"""The following system prompt needs to be expanded with more detail:

{initial_prompt}

Please add:
1. More detailed step definitions with inputs/outputs
2. Specific tool usage instructions
3. Error handling patterns
4. Message formatting examples
5. Summary generation rules

The enhanced prompt should be at least 10,000 characters."""

        try:
            enhanced = llm.generate_simple(
                system_prompt=PROMPT_REFINEMENT_PROMPT,
                user_message=enhancement_request,
                temperature=0.2,
            )

            # Use enhanced if longer, otherwise combine
            if len(enhanced) > len(initial_prompt):
                return enhanced
            return initial_prompt + "\n\n" + enhanced

        except:
            return initial_prompt

    def _build_specification(self, intent: BusinessIntent) -> dict:
        """Build specification dict for LLM."""
        return {
            "use_case_name": intent.use_case_name,
            "description": intent.description,
            "procurement_type": {
                "goods": intent.supports_goods,
                "services": intent.supports_services,
            },
            "channels": intent.get_enabled_channel_names(),
            "features": {
                "quote_upload": intent.quote_upload_enabled,
                "value_routing": intent.requires_value_routing(),
                "supplier_validation": intent.supplier_validation_required,
                "currency_conversion": intent.requires_currency_service(),
                "catalog_search": intent.requires_catalog_search(),
            },
            "value_thresholds": {
                "low": intent.value_thresholds.low_threshold,
                "medium": intent.value_thresholds.medium_threshold,
                "high": intent.value_thresholds.high_threshold,
                "currency": intent.value_thresholds.currency,
            },
            "compliance": intent.compliance_level.name,
            "ui_settings": {
                "hide_reasoning": intent.ui_silence_required,
                "message_prefix": intent.message_prefix_enforcement,
                "generate_summary": intent.summary_generation,
            },
        }

    def _generate_with_builder(self, intent: BusinessIntent) -> str:
        """Fallback: Generate prompt using builder pattern."""
        from prompt_creator.core.prompt.prompt_builder import PromptBuilder

        builder = PromptBuilder(intent)
        return (
            builder.add_system_identity()
            .add_core_rules()
            .add_guardrails()
            .add_step_definitions()
            .add_cove_logic()
            .add_tool_discipline()
            .add_message_formatting()
            .add_summary_rules()
            .add_error_handling()
            .build()
        )


class PromptAdapterAgent(LLMEnabledAgent):
    """
    Agent for adapting prompts to different model families.

    Takes a canonical prompt and adapts it for specific models:
    - GPT-4o: Standard formatting
    - GPT-4.1/5.x: Enhanced structured output
    - Claude: XML tags and softer language
    """

    MODEL_ADAPTATION_PROMPTS = {
        "gpt-4o": """Adapt this prompt for GPT-4o:
- Use direct, imperative language
- Use markdown formatting
- Keep chain-of-thought hidden
- Use NEVER/ALWAYS for guardrails""",

        "gpt-4.1": """Adapt this prompt for GPT-4.1:
- Use structured output format
- Emphasize step-by-step reasoning
- Use clear decision trees
- Add explicit state transitions""",

        "gpt-5.1": """Adapt this prompt for GPT-5.1:
- Use advanced reasoning patterns
- Enable multi-step planning
- Add reflection checkpoints
- Use structured validation""",

        "gpt-5.2": """Adapt this prompt for GPT-5.2:
- Use sophisticated reasoning chains
- Enable self-correction
- Add meta-cognitive instructions
- Use hierarchical validation""",

        "claude-sonnet": """Adapt this prompt for Claude Sonnet:
- Use softer, more collaborative language
- Use XML tags for structure (<thinking>, <answer>)
- Replace NEVER with "You must not"
- Replace ALWAYS with "You must"
- Add ethical considerations""",

        "claude-opus": """Adapt this prompt for Claude Opus:
- Use thoughtful, nuanced language
- Use XML tags for structure
- Add reasoning transparency
- Include uncertainty acknowledgment
- Use collaborative framing""",
    }

    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        reasoning_store: Optional[ReasoningStore] = None,
    ):
        super().__init__(
            name="prompt_adapter_agent",
            capabilities=[AgentCapability.PROMPT_GENERATION],
            llm_client=llm_client,
            reasoning_store=reasoning_store,
        )

    def can_handle(self, context: AgentContext) -> bool:
        """Can handle if there's a prompt to adapt."""
        return context.generated_prompt is not None

    def execute(self, context: AgentContext) -> AgentResponse:
        """Adapt prompt for target model family."""
        target = context.target_model_family or "gpt-4o"

        if target not in self.MODEL_ADAPTATION_PROMPTS:
            # No adaptation needed
            return AgentResponse.success_response(
                output={"prompt": context.generated_prompt},
                reasoning=f"No adaptation needed for {target}",
            )

        llm = self._llm or context.llm_client
        if not llm:
            # Can't adapt without LLM
            return AgentResponse.success_response(
                output={"prompt": context.generated_prompt},
                reasoning="No LLM available for adaptation",
            )

        adaptation_instruction = self.MODEL_ADAPTATION_PROMPTS[target]

        adapted_prompt = llm.generate_simple(
            system_prompt=f"You are a Prompt Adaptation Specialist.\n\n{adaptation_instruction}",
            user_message=f"Adapt this prompt:\n\n{context.generated_prompt}",
            temperature=0.1,
        )

        return AgentResponse.success_response(
            output={"prompt": adapted_prompt, "target_model": target},
            reasoning=f"Adapted prompt for {target}",
        )

    def adapt_for_model(
        self,
        prompt: str,
        target_model: str,
        context: Optional[AgentContext] = None,
    ) -> str:
        """Standalone method to adapt a prompt for a specific model."""
        if target_model not in self.MODEL_ADAPTATION_PROMPTS:
            return prompt

        llm = self._llm or (context.llm_client if context else None)
        if not llm:
            return prompt

        adaptation_instruction = self.MODEL_ADAPTATION_PROMPTS[target_model]

        try:
            return llm.generate_simple(
                system_prompt=f"You are a Prompt Adaptation Specialist.\n\n{adaptation_instruction}",
                user_message=f"Adapt this prompt:\n\n{prompt}",
                temperature=0.1,
            )
        except:
            return prompt
