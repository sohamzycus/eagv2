"""
Step Registry.

Factory for creating workflow steps based on business intent.
Maps intent to appropriate step configurations.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from prompt_creator.domain.business_intent import (
    BusinessIntent,
    ProcurementChannel,
)

from .step import Step, ConcreteStep, StepContext, StepResult, StepStatus


@dataclass
class StepDefinition:
    """
    Definition of a workflow step.

    Used by the registry to create Step instances.
    """

    step_id: str
    name: str
    description: str
    required_inputs: list[str] = field(default_factory=list)
    optional_inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    routing: dict[str, str] = field(default_factory=dict)
    tool_required: Optional[str] = None
    enabled: bool = True

    def to_prompt_section(self) -> str:
        """Generate prompt section for this step."""
        lines = [
            f"### {self.step_id}: {self.name}",
            "",
            f"**Purpose:** {self.description}",
            "",
        ]

        if self.required_inputs:
            lines.append("**Required Inputs:**")
            for inp in self.required_inputs:
                lines.append(f"- {inp}")
            lines.append("")

        if self.outputs:
            lines.append("**Outputs:**")
            for out in self.outputs:
                lines.append(f"- {out}")
            lines.append("")

        if self.conditions:
            lines.append("**Conditions:**")
            for cond in self.conditions:
                lines.append(f"- {cond}")
            lines.append("")

        if self.tool_required:
            lines.append(f"**Required Tool:** `{self.tool_required}`")
            lines.append("")

        if self.routing:
            lines.append("**Routing:**")
            for condition, next_step in self.routing.items():
                lines.append(f"- IF {condition} → {next_step}")
            lines.append("")

        return "\n".join(lines)


class StepRegistry:
    """
    Registry for creating and managing workflow steps.

    Follows Factory pattern - creates steps based on intent.
    """

    def __init__(self):
        self._definitions: dict[str, StepDefinition] = {}
        self._steps: dict[str, Step] = {}

    def register_definition(self, definition: StepDefinition) -> "StepRegistry":
        """Register a step definition."""
        self._definitions[definition.step_id] = definition
        return self

    def get_definition(self, step_id: str) -> Optional[StepDefinition]:
        """Get a step definition by ID."""
        return self._definitions.get(step_id)

    def get_all_definitions(self) -> list[StepDefinition]:
        """Get all registered definitions."""
        return list(self._definitions.values())

    def create_step(self, definition: StepDefinition) -> Step:
        """Create a Step instance from definition."""

        def executor(context: StepContext) -> StepResult:
            # Default executor - actual implementation would call tools
            return StepResult.success(
                output={"step_id": definition.step_id, "status": "simulated"},
                next_step_id=list(definition.routing.values())[0] if definition.routing else None,
                reasoning=f"Executed {definition.name}",
            )

        step = ConcreteStep(
            step_id=definition.step_id,
            name=definition.name,
            description=definition.description,
            executor=executor,
            required_inputs=definition.required_inputs,
            optional_inputs=definition.optional_inputs,
        )

        # Add routing conditions
        for condition, next_step in definition.routing.items():
            step.add_condition(condition, next_step)

        self._steps[definition.step_id] = step
        return step

    def create_all_steps(self) -> list[Step]:
        """Create all steps from registered definitions."""
        return [
            self.create_step(defn)
            for defn in self._definitions.values()
            if defn.enabled
        ]

    @classmethod
    def create_for_intent(cls, intent: BusinessIntent) -> "StepRegistry":
        """
        Create a registry with steps appropriate for the given intent.

        This is the main factory method that maps business intent to steps.
        """
        registry = cls()

        # Always add core steps
        registry._add_core_steps()

        # Add channel-specific steps
        if ProcurementChannel.CATALOG in intent.enabled_channels:
            registry._add_catalog_steps()

        if intent.quote_upload_enabled:
            registry._add_quote_steps()

        # Add conditional steps
        if intent.supplier_validation_required:
            registry._add_supplier_steps()

        if intent.requires_value_routing():
            registry._add_routing_steps(intent)

        if intent.requires_currency_service():
            registry._add_currency_steps(intent)

        # Always add completion steps
        registry._add_completion_steps()

        return registry

    def _add_core_steps(self) -> None:
        """Add core workflow steps."""
        self.register_definition(
            StepDefinition(
                step_id="STEP_01",
                name="REQUEST_INTAKE",
                description="Capture initial purchase request from user",
                required_inputs=["user_message"],
                outputs=["request_type", "initial_requirements", "keywords"],
                conditions=[
                    "User must provide purchase intent",
                    "Extract item description and quantity if provided",
                ],
                routing={"request_captured": "STEP_02"},
            )
        )

        self.register_definition(
            StepDefinition(
                step_id="STEP_02",
                name="REQUEST_CLASSIFICATION",
                description="Classify request type and determine workflow path",
                required_inputs=["initial_requirements"],
                outputs=["request_category", "workflow_path", "is_goods", "is_services"],
                conditions=[
                    "Must classify as: goods, services, or both",
                    "Must determine: catalog, non-catalog, or quote path",
                    "Must identify urgency level",
                ],
                routing={
                    "catalog_item": "STEP_03",
                    "non_catalog": "STEP_04",
                    "quote_required": "STEP_05",
                },
            )
        )

        self.register_definition(
            StepDefinition(
                step_id="STEP_04",
                name="PAST_PURCHASE_SEARCH",
                description="Search for similar past purchases for reference",
                required_inputs=["keywords", "request_category"],
                outputs=["past_purchases", "suggested_suppliers", "reference_prices"],
                conditions=[
                    "Must search historical purchase data",
                    "Return top 3 relevant past purchases",
                    "Include supplier and pricing information",
                ],
                tool_required="past_purchase_search",
                routing={"history_found": "STEP_06", "no_history": "STEP_06"},
            )
        )

    def _add_catalog_steps(self) -> None:
        """Add catalog-related steps."""
        self.register_definition(
            StepDefinition(
                step_id="STEP_03",
                name="CATALOG_SEARCH",
                description="Search company catalog for requested items",
                required_inputs=["keywords", "request_category"],
                outputs=["catalog_results", "match_confidence", "pricing"],
                conditions=[
                    "Must use catalog_search tool",
                    "Present top 5 matching items",
                    "Show pricing and availability",
                    "Calculate match confidence",
                ],
                tool_required="catalog_search",
                routing={
                    "item_found": "STEP_06",
                    "no_match": "STEP_04",
                    "punchout_available": "STEP_03B",
                },
            )
        )

        self.register_definition(
            StepDefinition(
                step_id="STEP_03B",
                name="PUNCHOUT_DISCOVERY",
                description="Discover and initiate punchout sessions",
                required_inputs=["supplier_id", "user_id"],
                outputs=["punchout_url", "session_id"],
                conditions=[
                    "Verify supplier supports punchout",
                    "Create secure session",
                    "Provide return URL for cart capture",
                ],
                tool_required="punchout_session",
                routing={"session_created": "STEP_06"},
            )
        )

    def _add_quote_steps(self) -> None:
        """Add quote handling steps."""
        self.register_definition(
            StepDefinition(
                step_id="STEP_05",
                name="QUOTE_UPLOAD",
                description="Handle quote upload and parsing",
                required_inputs=["quote_file"],
                outputs=["parsed_quote", "line_items", "total_value", "supplier"],
                conditions=[
                    "Accept PDF, XLSX, CSV, DOCX formats",
                    "Extract supplier information",
                    "Parse line items with quantities and prices",
                    "Calculate total value",
                    "Validate quote validity date",
                ],
                tool_required="quote_upload",
                routing={
                    "quote_valid": "STEP_06",
                    "quote_invalid": "STEP_05_ERROR",
                    "multiple_quotes": "STEP_05B",
                },
            )
        )

        self.register_definition(
            StepDefinition(
                step_id="STEP_05B",
                name="QUOTE_COMPARISON",
                description="Compare multiple quotes for best value",
                required_inputs=["quote_ids"],
                outputs=["comparison_result", "recommended_quote", "analysis"],
                conditions=[
                    "Compare pricing across quotes",
                    "Consider delivery timelines",
                    "Evaluate supplier ratings",
                    "Provide recommendation with reasoning",
                ],
                tool_required="quote_compare",
                routing={"quote_selected": "STEP_06"},
            )
        )

    def _add_supplier_steps(self) -> None:
        """Add supplier validation steps."""
        self.register_definition(
            StepDefinition(
                step_id="STEP_07",
                name="SUPPLIER_VALIDATION",
                description="Validate supplier status and eligibility",
                required_inputs=["supplier_id"],
                outputs=["supplier_status", "is_eligible", "contracts", "payment_terms"],
                conditions=[
                    "Check supplier active status",
                    "Verify not blocked or suspended",
                    "Check for existing contracts",
                    "Retrieve payment terms",
                ],
                tool_required="supplier_status",
                routing={
                    "supplier_valid": "STEP_08",
                    "supplier_blocked": "STEP_07_BLOCKED",
                    "supplier_inactive": "STEP_07_ALTERNATE",
                },
            )
        )

        self.register_definition(
            StepDefinition(
                step_id="STEP_07_ALTERNATE",
                name="ALTERNATE_SUPPLIER",
                description="Find alternative suppliers when primary is unavailable",
                required_inputs=["request_category", "original_supplier_id"],
                outputs=["alternative_suppliers", "recommendations"],
                conditions=[
                    "Search for suppliers in same category",
                    "Prioritize suppliers with contracts",
                    "Show ratings and past performance",
                ],
                tool_required="supplier_search",
                routing={"alternate_found": "STEP_07", "no_alternates": "STEP_07_ERROR"},
            )
        )

    def _add_routing_steps(self, intent: BusinessIntent) -> None:
        """Add value-based routing steps."""
        thresholds = intent.value_thresholds
        self.register_definition(
            StepDefinition(
                step_id="STEP_09",
                name="VALUE_ROUTING",
                description="Route request based on total value",
                required_inputs=["total_value", "currency"],
                outputs=["routing_tier", "approval_path", "required_approvers"],
                conditions=[
                    f"Low value: < {thresholds.low_threshold} {thresholds.currency}",
                    f"Medium value: {thresholds.low_threshold}-{thresholds.medium_threshold} {thresholds.currency}",
                    f"High value: {thresholds.medium_threshold}-{thresholds.high_threshold} {thresholds.currency}",
                    f"Critical value: > {thresholds.high_threshold} {thresholds.currency}",
                ],
                tool_required="value_routing",
                routing={
                    "low_value": "STEP_10",
                    "medium_value": "STEP_10",
                    "high_value": "STEP_10",
                    "critical_value": "STEP_10",
                },
            )
        )

    def _add_currency_steps(self, intent: BusinessIntent) -> None:
        """Add currency conversion steps."""
        self.register_definition(
            StepDefinition(
                step_id="STEP_08",
                name="CURRENCY_CONVERSION",
                description="Handle multi-currency conversion",
                required_inputs=["amount", "source_currency"],
                outputs=["converted_amount", "exchange_rate", "conversion_timestamp"],
                conditions=[
                    f"Convert to base currency: {intent.currency_config.base_currency}",
                    "Show both original and converted amounts",
                    "Include exchange rate and timestamp",
                    f"Supported currencies: {', '.join(intent.currency_config.supported_currencies)}",
                ],
                tool_required="currency_conversion",
                routing={"converted": "STEP_09"},
            )
        )

    def _add_completion_steps(self) -> None:
        """Add workflow completion steps."""
        self.register_definition(
            StepDefinition(
                step_id="STEP_06",
                name="ITEM_CONFIGURATION",
                description="Configure purchase item details",
                required_inputs=["selected_item"],
                outputs=["configured_item", "quantity", "delivery_date", "cost_center"],
                conditions=[
                    "Capture quantity and unit of measure",
                    "Capture desired delivery date",
                    "Capture cost center / GL code",
                    "Validate against item constraints",
                ],
                routing={"configured": "STEP_07"},
            )
        )

        self.register_definition(
            StepDefinition(
                step_id="STEP_10",
                name="APPROVAL_ROUTING",
                description="Determine and initiate approval workflow",
                required_inputs=["routing_tier", "requester_id", "amount"],
                outputs=["workflow_id", "approvers", "estimated_time"],
                conditions=[
                    "Determine approver(s) based on routing tier",
                    "Check delegation rules",
                    "Calculate estimated approval time",
                ],
                tool_required="approval_workflow",
                routing={"routed": "STEP_11"},
            )
        )

        self.register_definition(
            StepDefinition(
                step_id="STEP_11",
                name="REQUEST_SUMMARY",
                description="Generate complete request summary",
                required_inputs=[
                    "configured_item",
                    "supplier",
                    "total_value",
                    "approval_path",
                ],
                outputs=["summary", "request_id"],
                conditions=[
                    "Include all captured details",
                    "Show itemized breakdown",
                    "Display approval workflow",
                    "Generate unique request ID",
                    "Format for user review",
                ],
                routing={"summarized": "STEP_12"},
            )
        )

        self.register_definition(
            StepDefinition(
                step_id="STEP_12",
                name="CONFIRMATION",
                description="Get user confirmation and submit request",
                required_inputs=["summary", "user_confirmation"],
                outputs=["submission_status", "tracking_number", "next_steps"],
                conditions=[
                    "Present summary for user review",
                    "Require explicit confirmation",
                    "Submit only after YES confirmation",
                    "Provide tracking information",
                ],
                tool_required="request_submit",
                routing={
                    "confirmed": "COMPLETE",
                    "edit_requested": "STEP_06",
                    "cancelled": "CANCELLED",
                },
            )
        )

    def generate_prompt_sections(self) -> str:
        """Generate all step sections for prompt."""
        lines = ["## Workflow Steps", ""]

        for definition in sorted(
            self._definitions.values(),
            key=lambda d: d.step_id,
        ):
            if definition.enabled:
                lines.append(definition.to_prompt_section())

        return "\n".join(lines)

