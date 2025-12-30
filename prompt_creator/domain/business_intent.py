"""
Business Intent Domain Model.

Represents the normalized business requirements extracted from user conversations.
Follows Single Responsibility Principle - only handles intent representation.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ProcurementChannel(Enum):
    """Supported procurement channels."""

    CATALOG = auto()
    NON_CATALOG = auto()
    QUOTE = auto()
    PUNCHOUT = auto()
    CONTRACT = auto()


class RoutingStrategy(Enum):
    """Value-based routing strategies."""

    THRESHOLD_BASED = auto()  # Route based on value thresholds
    CATEGORY_BASED = auto()  # Route based on item category
    HYBRID = auto()  # Both threshold and category
    NONE = auto()  # No special routing


class ComplianceLevel(Enum):
    """Compliance strictness levels."""

    STRICT = auto()  # Full guardrails, no exceptions
    STANDARD = auto()  # Normal compliance
    RELAXED = auto()  # Minimal constraints (dev/test only)


class ApprovalWorkflow(Enum):
    """Approval workflow types."""

    HIERARCHICAL = auto()  # Manager chain
    VALUE_BASED = auto()  # Based on amount
    CATEGORY_BASED = auto()  # Based on category
    HYBRID = auto()  # Multiple criteria


@dataclass
class CurrencyConfig:
    """Currency handling configuration."""

    base_currency: str = "USD"
    supported_currencies: list[str] = field(
        default_factory=lambda: ["USD", "EUR", "GBP", "INR"]
    )
    auto_convert: bool = True
    conversion_service_required: bool = True


@dataclass
class ValueThreshold:
    """Value threshold for routing decisions."""

    low_threshold: float = 1000.0
    medium_threshold: float = 10000.0
    high_threshold: float = 50000.0
    currency: str = "USD"


@dataclass
class BusinessIntent:
    """
    Normalized business intent extracted from user input.

    This is the core domain model that drives prompt generation.
    All agent decisions and prompt composition reference this model.
    """

    # Core identification
    use_case_name: str
    description: str

    # Procurement channels
    supports_goods: bool = True
    supports_services: bool = True
    enabled_channels: list[ProcurementChannel] = field(
        default_factory=lambda: [
            ProcurementChannel.CATALOG,
            ProcurementChannel.NON_CATALOG,
        ]
    )

    # Quote handling
    quote_upload_enabled: bool = False
    multi_supplier_quotes: bool = False
    quote_comparison_required: bool = False

    # Routing
    routing_strategy: RoutingStrategy = RoutingStrategy.THRESHOLD_BASED
    value_thresholds: ValueThreshold = field(default_factory=ValueThreshold)

    # Compliance
    compliance_level: ComplianceLevel = ComplianceLevel.STRICT
    approval_workflow: ApprovalWorkflow = ApprovalWorkflow.VALUE_BASED

    # Currency
    currency_config: CurrencyConfig = field(default_factory=CurrencyConfig)

    # Supplier handling
    supplier_validation_required: bool = True
    supplier_status_check: bool = True
    alternate_supplier_suggestion: bool = True

    # UI behavior
    ui_silence_required: bool = True  # Hide internal reasoning
    message_prefix_enforcement: bool = True
    summary_generation: bool = True

    # Conversation behavior
    max_clarification_rounds: int = 3
    fallback_to_human: bool = True

    # Additional metadata
    custom_guardrails: list[str] = field(default_factory=list)
    custom_steps: list[str] = field(default_factory=list)

    def requires_catalog_search(self) -> bool:
        """Check if catalog search step is needed."""
        return ProcurementChannel.CATALOG in self.enabled_channels

    def requires_quote_handling(self) -> bool:
        """Check if quote-related steps are needed."""
        return (
            ProcurementChannel.QUOTE in self.enabled_channels
            or self.quote_upload_enabled
        )

    def requires_value_routing(self) -> bool:
        """Check if value-based routing is needed."""
        return self.routing_strategy in [
            RoutingStrategy.THRESHOLD_BASED,
            RoutingStrategy.HYBRID,
        ]

    def requires_currency_service(self) -> bool:
        """Check if currency conversion service is needed."""
        return (
            self.currency_config.auto_convert
            and len(self.currency_config.supported_currencies) > 1
        )

    def get_enabled_channel_names(self) -> list[str]:
        """Get list of enabled channel names."""
        return [channel.name.lower() for channel in self.enabled_channels]


@dataclass
class IntentValidationResult:
    """Result of validating a BusinessIntent."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)


class BusinessIntentValidator:
    """
    Validates BusinessIntent for completeness and consistency.

    Follows Single Responsibility - only validates intents.
    """

    def validate(self, intent: BusinessIntent) -> IntentValidationResult:
        """Validate the business intent."""
        result = IntentValidationResult(is_valid=True)

        # Required fields
        if not intent.use_case_name:
            result.add_error("Use case name is required")

        if not intent.description:
            result.add_error("Description is required")

        # Channel consistency
        if not intent.enabled_channels:
            result.add_error("At least one procurement channel must be enabled")

        # Quote consistency
        if intent.multi_supplier_quotes and not intent.quote_upload_enabled:
            result.add_warning(
                "Multi-supplier quotes enabled but quote upload is disabled"
            )

        # Value routing consistency
        if intent.requires_value_routing():
            thresholds = intent.value_thresholds
            if thresholds.low_threshold >= thresholds.medium_threshold:
                result.add_error("Low threshold must be less than medium threshold")
            if thresholds.medium_threshold >= thresholds.high_threshold:
                result.add_error("Medium threshold must be less than high threshold")

        return result



