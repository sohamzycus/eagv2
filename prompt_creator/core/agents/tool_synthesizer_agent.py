"""
Tool Synthesizer Agent.

Auto-generates MCP-Zero tool specifications from workflow steps.
Uses LLM for intelligent tool design and documentation.
"""

import json
from typing import Any, Optional, TYPE_CHECKING

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


TOOL_SYNTHESIS_PROMPT = """You are an MCP-Zero Tool Architect.

Your job is to generate tool specifications for an AI procurement assistant.

Each tool must include:
1. tool_name: snake_case identifier
2. description: Clear description of what the tool does
3. type: "internal" (company API) or "external" (third-party)
4. input_schema: JSON Schema for inputs
5. output_schema: JSON Schema for outputs
6. mcp_zero: MCP configuration (endpoint, method, auth)

Generate tools as a JSON array. Each tool should be production-ready with complete schemas."""


class ToolSynthesizerAgent(LLMEnabledAgent):
    """
    Agent responsible for generating MCP-Zero tool specifications.

    Uses LLM for:
    - Intelligent tool design
    - Schema generation
    - Documentation
    """

    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        reasoning_store: Optional[ReasoningStore] = None,
    ):
        super().__init__(
            name="tool_synthesizer_agent",
            capabilities=[AgentCapability.TOOL_SYNTHESIS],
            llm_client=llm_client,
            reasoning_store=reasoning_store,
        )
        self.set_system_prompt(TOOL_SYNTHESIS_PROMPT)

    def can_handle(self, context: AgentContext) -> bool:
        """Can handle if prompt exists but tools not yet generated."""
        return context.generated_prompt is not None and not context.generated_tools

    def execute(self, context: AgentContext) -> AgentResponse:
        """Generate MCP-Zero tool specifications from intent."""
        if context.intent is None:
            return AgentResponse.failure_response(
                error="No business intent available",
                reasoning="Cannot synthesize tools without intent",
            )

        intent: BusinessIntent = context.intent

        context.log_reasoning(
            agent_name=self.name,
            step="TOOL_SYNTHESIS_START",
            input_data={"use_case": intent.use_case_name},
            decision="Starting tool specification generation",
            output=None,
            next_step="GENERATE_TOOLS",
        )

        # Try LLM-based generation first
        llm = self._llm or context.llm_client
        if llm:
            tools = self._generate_with_llm(intent, llm)
        else:
            # Fallback to programmatic generation
            tools = self._generate_tools(intent)

        context.generated_tools = tools

        context.log_reasoning(
            agent_name=self.name,
            step="TOOL_SYNTHESIS_COMPLETE",
            input_data={"intent": intent.use_case_name},
            decision="Tool specifications generated",
            output={"tool_count": len(tools)},
            next_step="intake_orchestrator",
        )

        return AgentResponse.success_response(
            output={"tools": tools},
            reasoning=f"Generated {len(tools)} MCP-Zero tool specifications",
            next_agent="intake_orchestrator",
            user_message=f"✅ {len(tools)} tool specifications generated",
        )

    def _generate_with_llm(
        self,
        intent: BusinessIntent,
        llm,
    ) -> list[dict[str, Any]]:
        """Generate tools using LLM."""
        required_tools = self._get_required_tools(intent)

        prompt = f"""Generate MCP-Zero tool specifications for a procurement assistant.

Required tools based on configuration:
{json.dumps(required_tools, indent=2)}

For each tool, generate a complete specification with:
- tool_name (snake_case)
- description
- type ("internal" or "external")
- input_schema (JSON Schema with properties and required fields)
- output_schema (JSON Schema)
- mcp_zero (endpoint, method, auth_required, timeout_ms)

Output as a JSON array of tool specifications."""

        try:
            response = llm.generate_simple(
                system_prompt=self._system_prompt,
                user_message=prompt,
                temperature=0.0,
            )

            # Parse JSON from response
            tools = self._parse_tools_response(response)
            if tools and len(tools) > 0:
                return tools

        except Exception as e:
            pass

        # Fallback to programmatic generation
        return self._generate_tools(intent)

    def _parse_tools_response(self, response: str) -> list[dict[str, Any]]:
        """Parse tools from LLM response."""
        import re

        # Try direct parse
        try:
            return json.loads(response)
        except:
            pass

        # Try to extract JSON array from markdown
        json_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # Try to find JSON array in text
        json_match = re.search(r"(\[[\s\S]*\])", response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        return []

    def _get_required_tools(self, intent: BusinessIntent) -> list[dict]:
        """Get list of required tools based on intent."""
        tools = [
            {"name": "past_purchase_search", "purpose": "Search historical purchases"},
            {"name": "request_submit", "purpose": "Submit purchase request"},
        ]

        if ProcurementChannel.CATALOG in intent.enabled_channels:
            tools.extend([
                {"name": "catalog_search", "purpose": "Search product catalog"},
                {"name": "catalog_item_details", "purpose": "Get item details"},
            ])

        if intent.quote_upload_enabled:
            tools.extend([
                {"name": "quote_upload", "purpose": "Upload vendor quotes"},
                {"name": "quote_compare", "purpose": "Compare multiple quotes"},
            ])

        if intent.supplier_validation_required:
            tools.extend([
                {"name": "supplier_status", "purpose": "Check supplier status"},
                {"name": "supplier_search", "purpose": "Find alternative suppliers"},
            ])

        if intent.requires_currency_service():
            tools.extend([
                {"name": "currency_conversion", "purpose": "Convert currencies"},
                {"name": "currency_rates", "purpose": "Get exchange rates"},
            ])

        if intent.requires_value_routing():
            tools.append(
                {"name": "value_routing", "purpose": "Route based on value"}
            )

        tools.extend([
            {"name": "approval_workflow", "purpose": "Get approval workflow"},
            {"name": "approval_submit", "purpose": "Submit for approval"},
        ])

        return tools

    def _generate_tools(self, intent: BusinessIntent) -> list[dict[str, Any]]:
        """Fallback: Generate tools programmatically."""
        from prompt_creator.core.tools.mcp_zero_adapter import MCPZeroAdapter

        adapter = MCPZeroAdapter(intent)
        registry = adapter.generate_registry()

        return [tool.to_mcp_zero_spec() for tool in registry.tools]
