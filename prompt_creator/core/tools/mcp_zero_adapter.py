"""
MCP-Zero Adapter.

Adapts workflow steps and business intent to MCP-Zero tool specifications.
Implements Adapter pattern.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import json

from prompt_creator.domain.business_intent import BusinessIntent, ProcurementChannel
from .tool_contract import ToolContract, ToolContractBuilder, ToolType, ParameterType


@dataclass
class MCPZeroRegistry:
    """
    Registry of MCP-Zero tool specifications.

    Manages tool contracts and provides serialization.
    """

    name: str
    version: str = "1.0.0"
    tools: list[ToolContract] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def add_tool(self, tool: ToolContract) -> "MCPZeroRegistry":
        """Add a tool to the registry."""
        self.tools.append(tool)
        return self

    def get_tool(self, name: str) -> Optional[ToolContract]:
        """Get tool by name."""
        for tool in self.tools:
            if tool.tool_name == name:
                return tool
        return None

    def get_tools_by_type(self, tool_type: ToolType) -> list[ToolContract]:
        """Get tools by type."""
        return [t for t in self.tools if t.tool_type == tool_type]

    def to_json(self, indent: int = 2) -> str:
        """Serialize registry to JSON."""
        data = {
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "tools": [tool.to_mcp_zero_spec() for tool in self.tools],
            "metadata": self.metadata,
        }
        return json.dumps(data, indent=indent)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "tools": [tool.to_mcp_zero_spec() for tool in self.tools],
            "metadata": self.metadata,
        }

    @classmethod
    def from_json(cls, json_str: str) -> "MCPZeroRegistry":
        """Deserialize from JSON."""
        data = json.loads(json_str)
        registry = cls(
            name=data["name"],
            version=data.get("version", "1.0.0"),
            metadata=data.get("metadata", {}),
        )
        for tool_data in data.get("tools", []):
            registry.add_tool(ToolContract.from_dict(tool_data))
        return registry


class MCPZeroAdapter:
    """
    Adapter for generating MCP-Zero tool specifications from business intent.

    Implements Adapter pattern - adapts business domain to MCP-Zero format.
    """

    def __init__(self, intent: BusinessIntent):
        self._intent = intent

    def generate_registry(self) -> MCPZeroRegistry:
        """Generate complete MCP-Zero registry from intent."""
        registry = MCPZeroRegistry(
            name=f"{self._intent.use_case_name}_tools",
            version="1.0.0",
            metadata={
                "use_case": self._intent.use_case_name,
                "generated_for": self._intent.description,
            },
        )

        # Add core tools
        for tool in self._generate_core_tools():
            registry.add_tool(tool)

        # Add channel-specific tools
        if ProcurementChannel.CATALOG in self._intent.enabled_channels:
            for tool in self._generate_catalog_tools():
                registry.add_tool(tool)

        # Add quote tools
        if self._intent.quote_upload_enabled:
            for tool in self._generate_quote_tools():
                registry.add_tool(tool)

        # Add supplier tools
        if self._intent.supplier_validation_required:
            for tool in self._generate_supplier_tools():
                registry.add_tool(tool)

        # Add currency tools
        if self._intent.requires_currency_service():
            for tool in self._generate_currency_tools():
                registry.add_tool(tool)

        # Add routing tools
        if self._intent.requires_value_routing():
            for tool in self._generate_routing_tools():
                registry.add_tool(tool)

        # Add approval tools
        for tool in self._generate_approval_tools():
            registry.add_tool(tool)

        return registry

    def _generate_core_tools(self) -> list[ToolContract]:
        """Generate core tools required for any workflow."""
        tools = []

        # Past purchase search
        tools.append(
            ToolContractBuilder("past_purchase_search")
            .description("Search historical purchase data for similar requests")
            .tool_type(ToolType.INTERNAL)
            .endpoint("/api/purchases/search", "POST")
            .string_param("query", "Search query keywords")
            .string_param("category", "Item category filter", required=False)
            .number_param("limit", "Maximum results to return", required=False, default=5)
            .output({
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "purchase_id": {"type": "string"},
                        "description": {"type": "string"},
                        "supplier": {"type": "string"},
                        "amount": {"type": "number"},
                        "currency": {"type": "string"},
                        "date": {"type": "string", "format": "date"},
                    },
                },
            })
            .build()
        )

        # Request submission
        tools.append(
            ToolContractBuilder("request_submit")
            .description("Submit the completed purchase request")
            .tool_type(ToolType.INTERNAL)
            .endpoint("/api/requests", "POST")
            .param("request_data", ParameterType.OBJECT, "Complete request payload")
            .string_param("requester_id", "ID of the requester")
            .string_param("notes", "Additional notes", required=False)
            .output({
                "type": "object",
                "properties": {
                    "request_id": {"type": "string"},
                    "status": {"type": "string"},
                    "tracking_url": {"type": "string"},
                    "estimated_completion": {"type": "string"},
                },
            })
            .build()
        )

        return tools

    def _generate_catalog_tools(self) -> list[ToolContract]:
        """Generate catalog-related tools."""
        tools = []

        # Catalog search
        tools.append(
            ToolContractBuilder("catalog_search")
            .description("Search company product catalog")
            .tool_type(ToolType.INTERNAL)
            .endpoint("/api/catalog/search", "GET")
            .string_param("query", "Search terms")
            .string_param("category", "Product category", required=False)
            .number_param("min_price", "Minimum price filter", required=False)
            .number_param("max_price", "Maximum price filter", required=False)
            .bool_param("in_stock_only", "Filter to in-stock items only", default=False)
            .cache(300)  # Cache for 5 minutes
            .output({
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "price": {"type": "number"},
                        "currency": {"type": "string"},
                        "stock_status": {"type": "string"},
                        "supplier_id": {"type": "string"},
                        "supplier_name": {"type": "string"},
                        "image_url": {"type": "string"},
                    },
                },
            })
            .build()
        )

        # Catalog item details
        tools.append(
            ToolContractBuilder("catalog_item_details")
            .description("Get detailed information about a catalog item")
            .tool_type(ToolType.INTERNAL)
            .endpoint("/api/catalog/items/{item_id}", "GET")
            .string_param("item_id", "Catalog item ID")
            .cache(600)  # Cache for 10 minutes
            .output({
                "type": "object",
                "properties": {
                    "item_id": {"type": "string"},
                    "name": {"type": "string"},
                    "full_description": {"type": "string"},
                    "specifications": {"type": "object"},
                    "pricing_tiers": {"type": "array"},
                    "lead_time_days": {"type": "integer"},
                    "minimum_order_qty": {"type": "integer"},
                    "supplier": {"type": "object"},
                },
            })
            .build()
        )

        # Punchout session
        if ProcurementChannel.PUNCHOUT in self._intent.enabled_channels:
            tools.append(
                ToolContractBuilder("punchout_session")
                .description("Create a punchout session to supplier website")
                .tool_type(ToolType.EXTERNAL)
                .endpoint("/api/punchout/sessions", "POST")
                .string_param("supplier_id", "Supplier ID")
                .string_param("user_id", "User ID")
                .string_param("return_url", "URL to return to after shopping", required=False)
                .output({
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "redirect_url": {"type": "string"},
                        "expires_at": {"type": "string", "format": "date-time"},
                    },
                })
                .build()
            )

        return tools

    def _generate_quote_tools(self) -> list[ToolContract]:
        """Generate quote handling tools."""
        tools = []

        # Quote upload
        tools.append(
            ToolContractBuilder("quote_upload")
            .description("Upload and parse a vendor quote document")
            .tool_type(ToolType.INTERNAL)
            .endpoint("/api/quotes/upload", "POST")
            .string_param("file_content", "Base64 encoded file content")
            .string_param("file_type", "File type (pdf, xlsx, csv, docx)")
            .string_param("supplier_hint", "Hint for supplier identification", required=False)
            .timeout(60000)  # 60 second timeout for parsing
            .output({
                "type": "object",
                "properties": {
                    "quote_id": {"type": "string"},
                    "supplier": {"type": "string"},
                    "valid_until": {"type": "string", "format": "date"},
                    "line_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "line_number": {"type": "integer"},
                                "description": {"type": "string"},
                                "quantity": {"type": "number"},
                                "unit_price": {"type": "number"},
                                "total": {"type": "number"},
                            },
                        },
                    },
                    "subtotal": {"type": "number"},
                    "tax": {"type": "number"},
                    "total_value": {"type": "number"},
                    "currency": {"type": "string"},
                },
            })
            .build()
        )

        # Quote compare
        if self._intent.multi_supplier_quotes:
            tools.append(
                ToolContractBuilder("quote_compare")
                .description("Compare multiple quotes for the same request")
                .tool_type(ToolType.INTERNAL)
                .endpoint("/api/quotes/compare", "POST")
                .param("quote_ids", ParameterType.ARRAY, "List of quote IDs to compare")
                .output({
                    "type": "object",
                    "properties": {
                        "comparison_id": {"type": "string"},
                        "recommended_quote_id": {"type": "string"},
                        "recommendation_reason": {"type": "string"},
                        "comparison": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "quote_id": {"type": "string"},
                                    "supplier": {"type": "string"},
                                    "total": {"type": "number"},
                                    "delivery_days": {"type": "integer"},
                                    "score": {"type": "number"},
                                },
                            },
                        },
                    },
                })
                .build()
            )

        return tools

    def _generate_supplier_tools(self) -> list[ToolContract]:
        """Generate supplier validation tools."""
        tools = []

        # Supplier status
        tools.append(
            ToolContractBuilder("supplier_status")
            .description("Check supplier status and eligibility")
            .tool_type(ToolType.INTERNAL)
            .endpoint("/api/suppliers/{supplier_id}/status", "GET")
            .string_param("supplier_id", "Supplier ID")
            .string_param("supplier_name", "Supplier name (for lookup)", required=False)
            .cache(1800)  # Cache for 30 minutes
            .output({
                "type": "object",
                "properties": {
                    "supplier_id": {"type": "string"},
                    "name": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive", "blocked", "pending"],
                    },
                    "is_eligible": {"type": "boolean"},
                    "block_reason": {"type": "string"},
                    "contracts": {"type": "array"},
                    "payment_terms": {"type": "string"},
                    "rating": {"type": "number"},
                },
            })
            .build()
        )

        # Supplier search
        if self._intent.alternate_supplier_suggestion:
            tools.append(
                ToolContractBuilder("supplier_search")
                .description("Search for alternative suppliers")
                .tool_type(ToolType.INTERNAL)
                .endpoint("/api/suppliers/search", "GET")
                .string_param("category", "Product/service category")
                .string_param("product_type", "Specific product type", required=False)
                .string_param("region", "Geographic region", required=False)
                .bool_param("contracted_only", "Only show contracted suppliers", default=False)
                .cache(3600)  # Cache for 1 hour
                .output({
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "supplier_id": {"type": "string"},
                            "name": {"type": "string"},
                            "rating": {"type": "number"},
                            "contract_status": {"type": "string"},
                            "categories": {"type": "array"},
                        },
                    },
                })
                .build()
            )

        return tools

    def _generate_currency_tools(self) -> list[ToolContract]:
        """Generate currency conversion tools."""
        tools = []
        config = self._intent.currency_config

        # Currency conversion
        tools.append(
            ToolContractBuilder("currency_conversion")
            .description("Convert amounts between currencies")
            .tool_type(ToolType.EXTERNAL)
            .endpoint("/api/currency/convert", "GET")
            .auth_required(False)
            .number_param("amount", "Amount to convert")
            .string_param("from_currency", "Source currency code (e.g., EUR)")
            .string_param("to_currency", "Target currency code", required=False, default=config.base_currency)
            .cache(3600)  # Cache rates for 1 hour
            .output({
                "type": "object",
                "properties": {
                    "original_amount": {"type": "number"},
                    "original_currency": {"type": "string"},
                    "converted_amount": {"type": "number"},
                    "target_currency": {"type": "string"},
                    "exchange_rate": {"type": "number"},
                    "rate_timestamp": {"type": "string", "format": "date-time"},
                },
            })
            .build()
        )

        # Exchange rates
        tools.append(
            ToolContractBuilder("currency_rates")
            .description("Get current exchange rates")
            .tool_type(ToolType.EXTERNAL)
            .endpoint("/api/currency/rates", "GET")
            .auth_required(False)
            .string_param("base_currency", "Base currency", required=False, default=config.base_currency)
            .cache(3600)
            .output({
                "type": "object",
                "properties": {
                    "base": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "rates": {"type": "object"},
                },
            })
            .build()
        )

        return tools

    def _generate_routing_tools(self) -> list[ToolContract]:
        """Generate value-based routing tools."""
        tools = []
        thresholds = self._intent.value_thresholds

        tools.append(
            ToolContractBuilder("value_routing")
            .description("Determine approval routing based on request value")
            .tool_type(ToolType.INTERNAL)
            .endpoint("/api/routing/determine", "POST")
            .number_param("total_value", "Total request value")
            .string_param("currency", "Currency of the value")
            .string_param("category", "Request category", required=False)
            .string_param("requester_id", "ID of the requester", required=False)
            .output({
                "type": "object",
                "properties": {
                    "routing_tier": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                    },
                    "threshold_applied": {"type": "number"},
                    "required_approvers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "approver_id": {"type": "string"},
                                "name": {"type": "string"},
                                "role": {"type": "string"},
                                "level": {"type": "integer"},
                            },
                        },
                    },
                    "approval_workflow_id": {"type": "string"},
                    "estimated_approval_time": {"type": "string"},
                },
                "metadata": {
                    "thresholds": {
                        "low": thresholds.low_threshold,
                        "medium": thresholds.medium_threshold,
                        "high": thresholds.high_threshold,
                        "currency": thresholds.currency,
                    },
                },
            })
            .build()
        )

        return tools

    def _generate_approval_tools(self) -> list[ToolContract]:
        """Generate approval workflow tools."""
        tools = []

        # Get approval workflow
        tools.append(
            ToolContractBuilder("approval_workflow")
            .description("Get approval workflow for a request")
            .tool_type(ToolType.INTERNAL)
            .endpoint("/api/approvals/workflow", "POST")
            .string_param("requester_id", "ID of the requester")
            .number_param("amount", "Request amount")
            .string_param("category", "Request category", required=False)
            .string_param("cost_center", "Cost center", required=False)
            .output({
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string"},
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "step": {"type": "integer"},
                                "approver_id": {"type": "string"},
                                "approver_name": {"type": "string"},
                                "role": {"type": "string"},
                                "status": {"type": "string"},
                            },
                        },
                    },
                    "current_step": {"type": "integer"},
                    "status": {"type": "string"},
                },
            })
            .build()
        )

        # Submit for approval
        tools.append(
            ToolContractBuilder("approval_submit")
            .description("Submit request for approval")
            .tool_type(ToolType.INTERNAL)
            .endpoint("/api/approvals/submit", "POST")
            .string_param("request_id", "Request ID")
            .string_param("workflow_id", "Workflow ID")
            .string_param("notes", "Notes for approvers", required=False)
            .output({
                "type": "object",
                "properties": {
                    "submission_id": {"type": "string"},
                    "status": {"type": "string"},
                    "next_approver": {"type": "string"},
                    "estimated_completion": {"type": "string"},
                },
            })
            .build()
        )

        return tools

