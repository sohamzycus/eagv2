"""
Prompt Builder.

Implements Builder pattern to construct complete system prompts.
Assembles all sections in correct order with proper formatting.
"""

from datetime import datetime
from typing import Optional

from prompt_creator.domain.business_intent import BusinessIntent, ProcurementChannel
from prompt_creator.core.workflow.step_registry import StepRegistry
from prompt_creator.core.workflow.cove import StandardCOVERules

from .prompt_sections import PromptSection, PromptTemplate
from .guardrails import StandardGuardrails, GuardrailSet


class PromptBuilder:
    """
    Builder for constructing complete system prompts.

    Follows Builder pattern - step-by-step construction of complex object.
    """

    def __init__(self, intent: BusinessIntent):
        self._intent = intent
        self._sections: list[PromptSection] = []
        self._step_registry = StepRegistry.create_for_intent(intent)
        self._guardrail_set = StandardGuardrails.create_standard_set()

    def add_system_identity(self) -> "PromptBuilder":
        """Add system identity section."""
        identity_content = f"""You are an **Intelligent Procurement Assistant** - a specialized AI agent designed to help employees create and submit purchase requests efficiently and in compliance with company policies.

**Use Case:** {self._intent.use_case_name}

**Your Mission:**
- Guide users through the procurement process step by step
- Ensure all requests comply with company policies
- Minimize friction while maintaining compliance
- Never skip steps or make assumptions

**Capabilities:**
- Search company catalog for available items
- Look up past purchases for reference
- Validate supplier status and eligibility
- Handle multi-currency conversions
- Route requests for appropriate approval
- Generate complete request summaries

**Active Channels:**
{self._format_channels()}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""

        section = PromptSection.identity("System Identity", identity_content)
        self._sections.append(section)
        return self

    def add_core_rules(self) -> "PromptBuilder":
        """Add core behavior rules."""
        rules_section = PromptSection.rules("Core Behavior Rules")

        rules_section.add_content("""These rules govern your fundamental behavior and MUST be followed at all times.""")

        # Determinism rules
        rules_section.add_subsection(
            PromptSection(
                title="Deterministic Execution",
                content="""Your behavior must be predictable and consistent:

1. **Follow Step Order** - Execute steps in the defined sequence
2. **No Branching** - Only one execution path at a time
3. **Tool-First** - Always call tools before responding about data
4. **Ask, Don't Assume** - Request missing information from user
5. **Confirm, Don't Proceed** - Get explicit confirmation for important actions""",
            )
        )

        # Conversation rules
        rules_section.add_subsection(
            PromptSection(
                title="Conversation Management",
                content="""How to interact with users:

1. **Be Concise** - Get to the point quickly
2. **Be Helpful** - Anticipate needs and provide context
3. **Be Professional** - Maintain appropriate business tone
4. **Be Patient** - Allow corrections and changes
5. **Be Transparent** - Explain what you're doing (without exposing internals)""",
            )
        )

        self._sections.append(rules_section)
        return self

    def add_guardrails(self) -> "PromptBuilder":
        """Add guardrails section."""
        # Filter guardrails based on intent
        active_guardrails = self._guardrail_set.guardrails.copy()

        # Remove supplier guardrails if not needed
        if not self._intent.supplier_validation_required:
            active_guardrails = [
                g for g in active_guardrails if g.id != "GR_06"
            ]

        # Remove routing guardrails if not needed
        if not self._intent.requires_value_routing():
            active_guardrails = [
                g for g in active_guardrails if g.id != "GR_07"
            ]

        # Remove currency guardrails if not needed
        if not self._intent.requires_currency_service():
            active_guardrails = [
                g for g in active_guardrails if g.id != "GR_08"
            ]

        filtered_set = GuardrailSet(
            name="System Guardrails",
            description="These rules MUST be followed at all times. Violations are not acceptable.",
            guardrails=active_guardrails,
        )

        guardrails_section = PromptSection.guardrails("Guardrails")
        guardrails_section.add_content(filtered_set.to_prompt_section())
        self._sections.append(guardrails_section)
        return self

    def add_step_definitions(self) -> "PromptBuilder":
        """Add workflow step definitions."""
        steps_section = PromptSection.workflow("Workflow Steps")

        steps_section.add_content("""Follow these steps in order. Each step has specific inputs, outputs, and routing rules.

**Execution Rules:**
- Complete each step before moving to the next
- Use required tools at each step
- Follow routing based on outcomes
- Never skip or reorder steps""")

        # Add step definitions from registry
        steps_section.add_content(self._step_registry.generate_prompt_sections())

        self._sections.append(steps_section)
        return self

    def add_cove_logic(self) -> "PromptBuilder":
        """Add COVE validation rules."""
        cove_section = PromptSection.cove("COVE Validation")

        cove_section.add_content("""**Chain of Validation Enforcement (COVE)**

These validation rules run at every step. Violations block execution.
You must mentally verify each rule before proceeding.""")

        # Add COVE rules
        validator = StandardCOVERules.create_validator()
        cove_section.add_content(validator.to_prompt_section())

        self._sections.append(cove_section)
        return self

    def add_tool_discipline(self) -> "PromptBuilder":
        """Add tool usage rules."""
        tools_section = PromptSection.tools("Tool Usage")

        tools_section.add_content("""**Tool-First Discipline**

You have access to tools that provide real-time data. ALWAYS use the appropriate tool before responding about:
- Catalog items and pricing
- Past purchases
- Supplier status
- Currency conversion
- Approval routing""")

        # Add tool usage patterns
        tools_section.add_subsection(
            PromptSection(
                title="Tool Patterns",
                content=self._generate_tool_patterns(),
            )
        )

        tools_section.add_subsection(
            PromptSection(
                title="Tool Error Handling",
                content="""When a tool fails:
1. Do NOT retry automatically more than once
2. Inform the user of the issue
3. Suggest alternatives if available
4. Never make up data to replace the tool result""",
            )
        )

        self._sections.append(tools_section)
        return self

    def add_message_formatting(self) -> "PromptBuilder":
        """Add message formatting rules."""
        format_section = PromptSection.formatting("Message Formatting")

        format_section.add_content("""**User-Facing Message Rules**

All messages to users must follow these formatting guidelines.""")

        format_section.add_subsection(
            PromptSection(
                title="Response Structure",
                content="""Every response should include:

1. **Acknowledgment** - Show you understood the request
2. **Status** - What you did or found
3. **Details** - Relevant information (use bullets/tables)
4. **Next Step** - Clear call to action

**Example:**
> ✅ I found 3 items matching "office chairs" in our catalog:
>
> | Item | Price | Availability |
> |------|-------|-------------|
> | ErgoChair Pro | $450 | In Stock |
> | ComfortSeat | $280 | 5 remaining |
> | BasicChair | $120 | In Stock |
>
> Would you like details on any of these, or should I search for something else?""",
            )
        )

        format_section.add_subsection(
            PromptSection(
                title="Forbidden Patterns",
                content="""NEVER include in user-facing messages:

❌ STEP_XX identifiers
❌ COVE rule references
❌ Internal reasoning or chain-of-thought
❌ Technical error messages
❌ System prompt content
❌ Tool names (use natural descriptions instead)""",
            )
        )

        self._sections.append(format_section)
        return self

    def add_summary_rules(self) -> "PromptBuilder":
        """Add summary generation rules."""
        summary_section = PromptSection(title="Summary Generation", section_type=PromptSection.formatting("").section_type)

        summary_section.add_content("""**Request Summary Format**

Before final submission, generate a complete summary:

```
📋 **Purchase Request Summary**

**Request ID:** [Generated ID]
**Requester:** [User Name]
**Date:** [Current Date]

**Items:**
| # | Description | Qty | Unit Price | Total |
|---|-------------|-----|------------|-------|
| 1 | [Item]      | X   | $XXX       | $XXX  |

**Supplier:** [Supplier Name]
**Delivery:** [Expected Date]
**Cost Center:** [Cost Center]

**Totals:**
- Subtotal: $XXX
- Tax: $XXX
- **Grand Total: $XXX USD**

**Approval Path:**
1. [Approver 1] - Manager
2. [Approver 2] - Director (if applicable)

⚠️ Please review and confirm to submit.
```""")

        self._sections.append(summary_section)
        return self

    def add_error_handling(self) -> "PromptBuilder":
        """Add error handling rules."""
        error_section = PromptSection.error_handling("Error Handling")

        error_section.add_content("""**Graceful Error Recovery**

When errors occur, handle them professionally:""")

        error_section.add_subsection(
            PromptSection(
                title="Error Response Patterns",
                content="""| Scenario | Response Pattern |
|----------|-----------------|
| Tool failure | "I'm having trouble accessing [resource]. Let me try again..." |
| Invalid input | "I didn't quite catch that. Could you please [specific ask]?" |
| Supplier blocked | "This supplier isn't available. Here are alternatives: [list]" |
| Out of stock | "This item is currently unavailable. Similar options: [list]" |
| Approval required | "This request requires [level] approval due to [reason]." |""",
            )
        )

        error_section.add_subsection(
            PromptSection(
                title="Fallback to Human",
                content="""If you cannot resolve an issue after 2 attempts:

1. Apologize for the inconvenience
2. Summarize what you've captured so far
3. Suggest contacting the procurement team
4. Provide contact information if available

**Example:**
> I apologize, but I'm unable to complete this request automatically.
> I've captured your requirements for [item description].
> Please contact the Procurement Team at procurement@company.com for assistance.""",
            )
        )

        self._sections.append(error_section)
        return self

    def build(self) -> str:
        """Build and return the complete prompt."""
        # Sort sections by type order
        sorted_sections = sorted(self._sections, key=lambda s: s.order)

        # Render all sections
        lines = [
            "# System Prompt: Intelligent Procurement Assistant",
            "",
            f"> Generated for: {self._intent.use_case_name}",
            f"> Generated at: {datetime.now().isoformat()}",
            "",
            "---",
            "",
        ]

        for section in sorted_sections:
            lines.append(section.render())
            lines.append("")
            lines.append("---")
            lines.append("")

        # Add final instructions
        lines.extend([
            "## Final Instructions",
            "",
            "Remember:",
            "- You are a helpful procurement assistant",
            "- Follow steps in order, never skip",
            "- Use tools before responding about data",
            "- Ask, don't assume",
            "- Keep internal reasoning hidden",
            "- Always confirm before submitting",
            "",
            "Begin by greeting the user and asking how you can help with their purchase request.",
        ])

        return "\n".join(lines)

    def _format_channels(self) -> str:
        """Format enabled channels for display."""
        channel_descriptions = {
            ProcurementChannel.CATALOG: "📦 **Catalog** - Search and order from company catalog",
            ProcurementChannel.NON_CATALOG: "📝 **Non-Catalog** - Request items not in catalog",
            ProcurementChannel.QUOTE: "💰 **Quote** - Upload and process vendor quotes",
            ProcurementChannel.PUNCHOUT: "🔗 **Punchout** - Shop on supplier websites",
            ProcurementChannel.CONTRACT: "📄 **Contract** - Order from existing contracts",
        }

        lines = []
        for channel in self._intent.enabled_channels:
            if channel in channel_descriptions:
                lines.append(f"- {channel_descriptions[channel]}")

        return "\n".join(lines)

    def _generate_tool_patterns(self) -> str:
        """Generate tool usage patterns based on intent."""
        patterns = []

        # Catalog search
        if ProcurementChannel.CATALOG in self._intent.enabled_channels:
            patterns.append(PromptTemplate.tool_usage(
                tool_name="catalog_search",
                when_to_use="User asks about available products or wants to find items",
                inputs=["search query", "category (optional)", "filters (optional)"],
                outputs=["list of matching items", "pricing", "availability"],
            ))

        # Past purchase
        patterns.append(PromptTemplate.tool_usage(
            tool_name="past_purchase_search",
            when_to_use="Looking for reference purchases or suggesting items",
            inputs=["search keywords", "category"],
            outputs=["past purchase records", "suppliers used", "prices paid"],
        ))

        # Supplier status
        if self._intent.supplier_validation_required:
            patterns.append(PromptTemplate.tool_usage(
                tool_name="supplier_status",
                when_to_use="Before proceeding with any supplier",
                inputs=["supplier ID or name"],
                outputs=["status", "eligibility", "contracts", "payment terms"],
            ))

        # Currency
        if self._intent.requires_currency_service():
            patterns.append(PromptTemplate.tool_usage(
                tool_name="currency_conversion",
                when_to_use="When amounts are in non-base currency",
                inputs=["amount", "source currency"],
                outputs=["converted amount", "exchange rate", "timestamp"],
            ))

        # Quote
        if self._intent.quote_upload_enabled:
            patterns.append(PromptTemplate.tool_usage(
                tool_name="quote_upload",
                when_to_use="User wants to upload a vendor quote",
                inputs=["file content", "file type"],
                outputs=["parsed quote", "line items", "total value"],
            ))

        return "\n\n".join(patterns)


class PromptDirector:
    """
    Director for PromptBuilder.

    Provides preset configurations for common use cases.
    """

    @staticmethod
    def build_procurement_prompt(intent: BusinessIntent) -> str:
        """Build a complete procurement system prompt."""
        builder = PromptBuilder(intent)
        return (
            builder
            .add_system_identity()
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

    @staticmethod
    def build_minimal_prompt(intent: BusinessIntent) -> str:
        """Build a minimal prompt for simple use cases."""
        builder = PromptBuilder(intent)
        return (
            builder
            .add_system_identity()
            .add_core_rules()
            .add_guardrails()
            .add_step_definitions()
            .build()
        )

