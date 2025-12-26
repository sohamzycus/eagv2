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
COMPOSER_SYSTEM_PROMPT = """You are an expert System Prompt Architect specializing in enterprise procurement AI agents.

Your task is to generate production-ready system prompts for procurement workflow assistants.

The generated prompt MUST include:
1. **System Identity** - Clear role definition for the specific procurement workflow
2. **Core Rules** - Deterministic behavior rules
3. **Guardrails** - What the agent must/must not do (NEVER/ALWAYS)
4. **Workflow Steps** - Ordered STEP_XX definitions with clear routing
5. **COVE Rules** - Chain of Validation Enforcement
6. **Available Tools** - List of tools with WHEN and HOW to use each
7. **Tool Discipline** - Rules for tool usage (ALWAYS call tool before responding)
8. **Message Formatting** - How to format responses
9. **Error Handling** - How to handle failures

CRITICAL REQUIREMENTS:
- Steps must be numbered (STEP_01, STEP_02, etc.)
- Each step must have: Purpose, Inputs, Outputs, Tool(s) to use, Routing
- Guardrails must use NEVER/ALWAYS language
- Internal reasoning must be hidden from users
- Tool calls must happen BEFORE responding with data
- Each step should reference which tool to call
- Include a "Tool Reference" section listing all available tools

TOOL INTEGRATION RULES:
- NEVER respond with data without calling the appropriate tool first
- ALWAYS validate tool responses before presenting to user
- Each step should specify which tool(s) are required
- Handle tool errors gracefully

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
        
        # Format tools for the prompt
        tools_section = self._format_tools_for_prompt(spec.get("required_tools", []))

        # Generate initial prompt
        initial_prompt = f"""Generate a complete system prompt for this procurement workflow assistant:

**Specification:**
```json
{json.dumps(spec, indent=2)}
```

**Available Tools (MUST be included in the prompt):**
{tools_section}

CRITICAL REQUIREMENTS:
1. The prompt MUST include an "Available Tools" section listing ALL tools above
2. Each workflow STEP must specify which tool(s) to call
3. Include a "Tool Discipline" section with rules like:
   - NEVER respond with data without calling the appropriate tool first
   - ALWAYS validate tool responses before presenting to user
4. Include at least 10-15 workflow steps (STEP_01 to STEP_15)
5. Include at least 8 guardrails using NEVER/ALWAYS language
6. Include COVE validation rules
7. Make it production-ready (10,000+ characters)

The generated prompt must make clear WHEN and HOW to use each tool.

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

    def _format_tools_for_prompt(self, tools: list[dict]) -> str:
        """Format tools list for inclusion in prompt generation request."""
        if not tools:
            return "No specific tools defined - generate appropriate tools based on workflow."
        
        lines = []
        for tool in tools:
            lines.append(f"- **{tool['name']}**: {tool['purpose']}")
            lines.append(f"  - When to use: {tool['when_to_use']}")
        
        return "\n".join(lines)

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
        # Determine required tools based on workflow type
        required_tools = self._get_required_tools_for_intent(intent)
        
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
            "custom_guardrails": intent.custom_guardrails,
            "custom_steps": intent.custom_steps,
            "required_tools": required_tools,
        }

    def _get_required_tools_for_intent(self, intent: BusinessIntent) -> list[dict]:
        """Determine required tools based on the workflow type."""
        tools = []
        description_lower = intent.description.lower()
        name_lower = intent.use_case_name.lower()
        
        # Invoice Processing Tools
        if any(term in description_lower or term in name_lower for term in ['invoice', 'ap ', 'accounts payable', 'billing']):
            tools.extend([
                {"name": "invoice_ocr_extract", "purpose": "Extract data from invoice documents using OCR", "when_to_use": "When user uploads an invoice or invoice image"},
                {"name": "invoice_validate", "purpose": "Validate invoice data against PO and GRN", "when_to_use": "After extraction, before processing"},
                {"name": "invoice_match", "purpose": "Perform 2-way or 3-way matching", "when_to_use": "To match invoice with PO and/or GRN"},
                {"name": "invoice_exception_check", "purpose": "Check for pricing, quantity, or tax discrepancies", "when_to_use": "During validation to identify exceptions"},
                {"name": "invoice_approve", "purpose": "Submit invoice for approval workflow", "when_to_use": "After successful validation"},
                {"name": "invoice_search", "purpose": "Search historical invoices", "when_to_use": "When user queries invoice history"},
                {"name": "payment_status", "purpose": "Check payment status for an invoice", "when_to_use": "When user asks about payment"},
            ])
        
        # Purchase Requisition Tools
        if any(term in description_lower or term in name_lower for term in ['requisition', 'pr ', 'purchase request', 'buy', 'procurement']):
            tools.extend([
                {"name": "catalog_search", "purpose": "Search product catalog", "when_to_use": "When user looks for items to purchase"},
                {"name": "catalog_item_details", "purpose": "Get detailed item information", "when_to_use": "When user selects a catalog item"},
                {"name": "budget_check", "purpose": "Verify budget availability", "when_to_use": "Before submitting requisition"},
                {"name": "approval_workflow", "purpose": "Get approval chain for requisition", "when_to_use": "To determine required approvals"},
                {"name": "requisition_submit", "purpose": "Submit purchase requisition", "when_to_use": "After all validations pass"},
                {"name": "requisition_status", "purpose": "Check requisition status", "when_to_use": "When user queries requisition progress"},
            ])
        
        # Purchase Order Tools
        if any(term in description_lower or term in name_lower for term in ['purchase order', 'po ', 'order']):
            tools.extend([
                {"name": "po_create", "purpose": "Create purchase order from requisition", "when_to_use": "After requisition approval"},
                {"name": "po_search", "purpose": "Search existing purchase orders", "when_to_use": "When user queries PO history"},
                {"name": "po_status", "purpose": "Check PO status and delivery", "when_to_use": "When user asks about order status"},
                {"name": "po_amendment", "purpose": "Modify existing purchase order", "when_to_use": "When user needs to change PO"},
            ])
        
        # Supplier Tools
        if intent.supplier_validation_required or any(term in description_lower for term in ['supplier', 'vendor']):
            tools.extend([
                {"name": "supplier_search", "purpose": "Search supplier database", "when_to_use": "When looking for suppliers"},
                {"name": "supplier_validate", "purpose": "Check supplier status and compliance", "when_to_use": "Before creating order with supplier"},
                {"name": "supplier_performance", "purpose": "Get supplier performance metrics", "when_to_use": "When evaluating suppliers"},
            ])
        
        # Quote Tools
        if intent.quote_upload_enabled or any(term in description_lower for term in ['quote', 'rfq', 'rfp', 'sourcing']):
            tools.extend([
                {"name": "quote_upload", "purpose": "Upload vendor quote document", "when_to_use": "When user submits a quote"},
                {"name": "quote_extract", "purpose": "Extract data from quote document", "when_to_use": "After quote upload"},
                {"name": "quote_compare", "purpose": "Compare multiple quotes", "when_to_use": "When user has multiple quotes"},
                {"name": "rfx_create", "purpose": "Create RFP/RFQ/RFI", "when_to_use": "When initiating sourcing event"},
            ])
        
        # Contract Tools
        if any(term in description_lower or term in name_lower for term in ['contract', 'agreement', 'renewal']):
            tools.extend([
                {"name": "contract_search", "purpose": "Search contract repository", "when_to_use": "When user looks for contracts"},
                {"name": "contract_validate", "purpose": "Check contract terms and compliance", "when_to_use": "Before using contract for procurement"},
                {"name": "contract_expiry_check", "purpose": "Check contract expiration and renewals", "when_to_use": "When validating contract validity"},
            ])
        
        # Currency Tools
        if intent.requires_currency_service():
            tools.extend([
                {"name": "currency_convert", "purpose": "Convert between currencies", "when_to_use": "When dealing with foreign currency amounts"},
                {"name": "currency_rates", "purpose": "Get current exchange rates", "when_to_use": "When user asks about exchange rates"},
            ])
        
        # Goods Receipt Tools
        if any(term in description_lower or term in name_lower for term in ['goods receipt', 'grn', 'receiving', 'delivery']):
            tools.extend([
                {"name": "grn_create", "purpose": "Create goods receipt note", "when_to_use": "When goods are received"},
                {"name": "grn_search", "purpose": "Search goods receipts", "when_to_use": "When user queries receipts"},
                {"name": "delivery_track", "purpose": "Track delivery status", "when_to_use": "When user asks about delivery"},
            ])
        
        # Always include common tools
        tools.extend([
            {"name": "user_info", "purpose": "Get current user details and permissions", "when_to_use": "At session start"},
            {"name": "audit_log", "purpose": "Log actions for audit trail", "when_to_use": "After every significant action"},
        ])
        
        # Remove duplicates
        seen = set()
        unique_tools = []
        for tool in tools:
            if tool["name"] not in seen:
                seen.add(tool["name"])
                unique_tools.append(tool)
        
        return unique_tools

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
