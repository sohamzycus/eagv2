"""
COVE (Constraint Validation Engine) Logic.

Implements validation rules and constraints for workflow steps.
COVE ensures compliance and determinism in agent behavior.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Optional


class COVESeverity(Enum):
    """Severity levels for COVE rules."""

    CRITICAL = auto()  # Must pass - blocks execution
    WARNING = auto()  # Should pass - logs warning
    INFO = auto()  # Informational only


class COVECategory(Enum):
    """Categories of COVE rules."""

    INPUT_VALIDATION = auto()
    OUTPUT_VALIDATION = auto()
    STEP_ORDERING = auto()
    VALUE_CONSTRAINT = auto()
    BUSINESS_RULE = auto()
    COMPLIANCE = auto()
    UI_BEHAVIOR = auto()


@dataclass
class COVEViolation:
    """A violation of a COVE rule."""

    rule_id: str
    rule_name: str
    severity: COVESeverity
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    suggested_action: Optional[str] = None


@dataclass
class COVEResult:
    """Result of COVE validation."""

    passed: bool
    violations: list[COVEViolation] = field(default_factory=list)
    warnings: list[COVEViolation] = field(default_factory=list)
    info: list[COVEViolation] = field(default_factory=list)

    def add_violation(self, violation: COVEViolation) -> None:
        """Add a violation based on severity."""
        if violation.severity == COVESeverity.CRITICAL:
            self.violations.append(violation)
            self.passed = False
        elif violation.severity == COVESeverity.WARNING:
            self.warnings.append(violation)
        else:
            self.info.append(violation)

    @classmethod
    def success(cls) -> "COVEResult":
        """Create successful result."""
        return cls(passed=True)

    @classmethod
    def failure(cls, violation: COVEViolation) -> "COVEResult":
        """Create failure result with single violation."""
        result = cls(passed=False)
        result.add_violation(violation)
        return result


class COVERule(ABC):
    """
    Abstract base class for COVE validation rules.

    Follows Strategy pattern - each rule is a separate strategy.
    """

    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        severity: COVESeverity = COVESeverity.CRITICAL,
        category: COVECategory = COVECategory.BUSINESS_RULE,
    ):
        self._rule_id = rule_id
        self._name = name
        self._description = description
        self._severity = severity
        self._category = category

    @property
    def rule_id(self) -> str:
        """Get rule ID."""
        return self._rule_id

    @property
    def name(self) -> str:
        """Get rule name."""
        return self._name

    @property
    def severity(self) -> COVESeverity:
        """Get rule severity."""
        return self._severity

    @property
    def category(self) -> COVECategory:
        """Get rule category."""
        return self._category

    @abstractmethod
    def validate(self, context: dict[str, Any]) -> COVEResult:
        """Validate the rule against context."""
        pass

    def to_prompt_text(self) -> str:
        """Generate prompt text for this rule."""
        severity_marker = "🔴" if self._severity == COVESeverity.CRITICAL else "🟡"
        return f"{severity_marker} **{self._rule_id}**: {self._description}"


class FunctionalCOVERule(COVERule):
    """
    COVE rule implemented with a validation function.

    Allows dynamic rule creation without subclassing.
    """

    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        validator: Callable[[dict[str, Any]], bool],
        error_message: str,
        severity: COVESeverity = COVESeverity.CRITICAL,
        category: COVECategory = COVECategory.BUSINESS_RULE,
    ):
        super().__init__(rule_id, name, description, severity, category)
        self._validator = validator
        self._error_message = error_message

    def validate(self, context: dict[str, Any]) -> COVEResult:
        """Validate using provided function."""
        try:
            if self._validator(context):
                return COVEResult.success()
            else:
                return COVEResult.failure(
                    COVEViolation(
                        rule_id=self._rule_id,
                        rule_name=self._name,
                        severity=self._severity,
                        message=self._error_message,
                        context=context,
                    )
                )
        except Exception as e:
            return COVEResult.failure(
                COVEViolation(
                    rule_id=self._rule_id,
                    rule_name=self._name,
                    severity=COVESeverity.CRITICAL,
                    message=f"Rule validation error: {str(e)}",
                    context=context,
                )
            )


class COVEValidator:
    """
    Validates a set of COVE rules.

    Aggregates rules and provides unified validation interface.
    """

    def __init__(self):
        self._rules: dict[str, COVERule] = {}
        self._rules_by_category: dict[COVECategory, list[COVERule]] = {}

    def add_rule(self, rule: COVERule) -> "COVEValidator":
        """Add a rule to the validator."""
        self._rules[rule.rule_id] = rule

        if rule.category not in self._rules_by_category:
            self._rules_by_category[rule.category] = []
        self._rules_by_category[rule.category].append(rule)

        return self

    def validate_all(self, context: dict[str, Any]) -> COVEResult:
        """Validate all rules against context."""
        result = COVEResult.success()

        for rule in self._rules.values():
            rule_result = rule.validate(context)
            for violation in rule_result.violations:
                result.add_violation(violation)
            for warning in rule_result.warnings:
                result.add_violation(warning)
            for info in rule_result.info:
                result.add_violation(info)

        return result

    def validate_category(
        self,
        category: COVECategory,
        context: dict[str, Any],
    ) -> COVEResult:
        """Validate only rules in a specific category."""
        result = COVEResult.success()
        rules = self._rules_by_category.get(category, [])

        for rule in rules:
            rule_result = rule.validate(context)
            for violation in rule_result.violations:
                result.add_violation(violation)
            for warning in rule_result.warnings:
                result.add_violation(warning)

        return result

    def get_all_rules(self) -> list[COVERule]:
        """Get all registered rules."""
        return list(self._rules.values())

    def to_prompt_section(self) -> str:
        """Generate prompt section for all COVE rules."""
        lines = ["## COVE Validation Rules", ""]

        for category in COVECategory:
            rules = self._rules_by_category.get(category, [])
            if rules:
                lines.append(f"### {category.name.replace('_', ' ').title()}")
                lines.append("")
                for rule in rules:
                    lines.append(rule.to_prompt_text())
                lines.append("")

        return "\n".join(lines)


class StandardCOVERules:
    """
    Factory for standard COVE rules.

    These rules implement the Buy Agent v5.0 guardrails.
    """

    @staticmethod
    def no_step_skipping() -> COVERule:
        """Rule: Steps cannot be skipped."""
        return FunctionalCOVERule(
            rule_id="COVE_01",
            name="No Step Skipping",
            description="Steps must be executed in order. No step may be skipped.",
            validator=lambda ctx: ctx.get("step_order_valid", True),
            error_message="Attempted to skip a required step",
            severity=COVESeverity.CRITICAL,
            category=COVECategory.STEP_ORDERING,
        )

    @staticmethod
    def no_assumptions() -> COVERule:
        """Rule: No assumptions without data."""
        return FunctionalCOVERule(
            rule_id="COVE_02",
            name="No Assumptions",
            description="Never assume information not explicitly provided by user or tools.",
            validator=lambda ctx: not ctx.get("has_assumptions", False),
            error_message="Made assumption without explicit data",
            severity=COVESeverity.CRITICAL,
            category=COVECategory.BUSINESS_RULE,
        )

    @staticmethod
    def tool_first() -> COVERule:
        """Rule: Always use tools before responding."""
        return FunctionalCOVERule(
            rule_id="COVE_03",
            name="Tool-First Execution",
            description="Always query relevant tools before providing information to user.",
            validator=lambda ctx: ctx.get("tool_called", False) or ctx.get("no_tool_needed", False),
            error_message="Responded without using required tool",
            severity=COVESeverity.CRITICAL,
            category=COVECategory.BUSINESS_RULE,
        )

    @staticmethod
    def ui_silence() -> COVERule:
        """Rule: Hide internal reasoning from user."""
        return FunctionalCOVERule(
            rule_id="COVE_04",
            name="UI Silence",
            description="Never expose STEP names, COVE rules, or internal reasoning to user.",
            validator=lambda ctx: not ctx.get("reasoning_exposed", False),
            error_message="Internal reasoning exposed to user",
            severity=COVESeverity.CRITICAL,
            category=COVECategory.UI_BEHAVIOR,
        )

    @staticmethod
    def message_prefix() -> COVERule:
        """Rule: Messages must follow prefix rules."""
        return FunctionalCOVERule(
            rule_id="COVE_05",
            name="Message Prefix Enforcement",
            description="All user-facing messages must follow the defined prefix pattern.",
            validator=lambda ctx: ctx.get("prefix_valid", True),
            error_message="Message prefix validation failed",
            severity=COVESeverity.WARNING,
            category=COVECategory.UI_BEHAVIOR,
        )

    @staticmethod
    def supplier_validation() -> COVERule:
        """Rule: Validate supplier before proceeding."""
        return FunctionalCOVERule(
            rule_id="COVE_06",
            name="Supplier Validation",
            description="Supplier status must be validated before any transaction.",
            validator=lambda ctx: ctx.get("supplier_validated", False) or not ctx.get("needs_supplier", False),
            error_message="Proceeding without supplier validation",
            severity=COVESeverity.CRITICAL,
            category=COVECategory.COMPLIANCE,
        )

    @staticmethod
    def value_check() -> COVERule:
        """Rule: Values must be within thresholds."""
        return FunctionalCOVERule(
            rule_id="COVE_07",
            name="Value Threshold Check",
            description="Request values must be routed according to defined thresholds.",
            validator=lambda ctx: ctx.get("routing_applied", False) or not ctx.get("needs_routing", False),
            error_message="Value routing not applied",
            severity=COVESeverity.CRITICAL,
            category=COVECategory.VALUE_CONSTRAINT,
        )

    @staticmethod
    def currency_conversion() -> COVERule:
        """Rule: Multi-currency must be converted."""
        return FunctionalCOVERule(
            rule_id="COVE_08",
            name="Currency Conversion",
            description="All amounts must be shown in base currency with original amount.",
            validator=lambda ctx: ctx.get("currency_converted", True),
            error_message="Currency conversion not applied",
            severity=COVESeverity.WARNING,
            category=COVECategory.VALUE_CONSTRAINT,
        )

    @staticmethod
    def get_standard_rules() -> list[COVERule]:
        """Get all standard COVE rules."""
        return [
            StandardCOVERules.no_step_skipping(),
            StandardCOVERules.no_assumptions(),
            StandardCOVERules.tool_first(),
            StandardCOVERules.ui_silence(),
            StandardCOVERules.message_prefix(),
            StandardCOVERules.supplier_validation(),
            StandardCOVERules.value_check(),
            StandardCOVERules.currency_conversion(),
        ]

    @staticmethod
    def create_validator() -> COVEValidator:
        """Create a validator with all standard rules."""
        validator = COVEValidator()
        for rule in StandardCOVERules.get_standard_rules():
            validator.add_rule(rule)
        return validator

