"""
Clarification Domain Models.

Models for the clarification conversation flow.
Follows Interface Segregation - separate concerns for questions and responses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional
from uuid import uuid4


class QuestionType(Enum):
    """Types of clarification questions."""

    BOOLEAN = auto()  # Yes/No questions
    SINGLE_CHOICE = auto()  # Pick one option
    MULTI_CHOICE = auto()  # Pick multiple options
    TEXT = auto()  # Free-form text
    NUMERIC = auto()  # Numeric value
    CONFIRMATION = auto()  # Confirm understanding


class QuestionPriority(Enum):
    """Priority of clarification questions."""

    CRITICAL = auto()  # Must be answered
    IMPORTANT = auto()  # Should be answered
    OPTIONAL = auto()  # Nice to have


@dataclass
class QuestionOption:
    """An option for choice-based questions."""

    value: str
    label: str
    description: Optional[str] = None
    default: bool = False


@dataclass
class ClarificationQuestion:
    """
    A single clarification question to ask the user.

    Designed for minimal friction - only ask what's necessary.
    """

    id: str
    question_text: str
    question_type: QuestionType
    priority: QuestionPriority = QuestionPriority.IMPORTANT
    options: list[QuestionOption] = field(default_factory=list)
    default_value: Optional[Any] = None
    help_text: Optional[str] = None
    intent_field: Optional[str] = None  # Maps to BusinessIntent field
    validation_regex: Optional[str] = None
    depends_on: Optional[str] = None  # Question ID this depends on

    @classmethod
    def boolean(
        cls,
        id: str,
        question: str,
        intent_field: str,
        default: bool = False,
        help_text: Optional[str] = None,
        priority: QuestionPriority = QuestionPriority.IMPORTANT,
    ) -> "ClarificationQuestion":
        """Factory method for boolean questions."""
        return cls(
            id=id,
            question_text=question,
            question_type=QuestionType.BOOLEAN,
            priority=priority,
            default_value=default,
            help_text=help_text,
            intent_field=intent_field,
        )

    @classmethod
    def single_choice(
        cls,
        id: str,
        question: str,
        options: list[QuestionOption],
        intent_field: str,
        help_text: Optional[str] = None,
        priority: QuestionPriority = QuestionPriority.IMPORTANT,
    ) -> "ClarificationQuestion":
        """Factory method for single-choice questions."""
        default = next((opt.value for opt in options if opt.default), None)
        return cls(
            id=id,
            question_text=question,
            question_type=QuestionType.SINGLE_CHOICE,
            priority=priority,
            options=options,
            default_value=default,
            help_text=help_text,
            intent_field=intent_field,
        )

    @classmethod
    def multi_choice(
        cls,
        id: str,
        question: str,
        options: list[QuestionOption],
        intent_field: str,
        help_text: Optional[str] = None,
        priority: QuestionPriority = QuestionPriority.IMPORTANT,
    ) -> "ClarificationQuestion":
        """Factory method for multi-choice questions."""
        defaults = [opt.value for opt in options if opt.default]
        return cls(
            id=id,
            question_text=question,
            question_type=QuestionType.MULTI_CHOICE,
            priority=priority,
            options=options,
            default_value=defaults,
            help_text=help_text,
            intent_field=intent_field,
        )


@dataclass
class UserResponse:
    """User's response to a clarification question."""

    question_id: str
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0  # How confident we are in parsing

    def as_bool(self) -> bool:
        """Parse response as boolean."""
        if isinstance(self.value, bool):
            return self.value
        if isinstance(self.value, str):
            return self.value.lower() in ("yes", "true", "1", "y")
        return bool(self.value)

    def as_list(self) -> list[str]:
        """Parse response as list."""
        if isinstance(self.value, list):
            return self.value
        if isinstance(self.value, str):
            return [v.strip() for v in self.value.split(",")]
        return [str(self.value)]

    def as_str(self) -> str:
        """Parse response as string."""
        if isinstance(self.value, list):
            return ", ".join(str(v) for v in self.value)
        return str(self.value)


@dataclass
class ClarificationSession:
    """
    Manages the clarification conversation flow.

    Tracks questions asked, responses received, and determines
    when enough information has been gathered.
    """

    session_id: str = field(default_factory=lambda: str(uuid4()))
    questions: list[ClarificationQuestion] = field(default_factory=list)
    responses: dict[str, UserResponse] = field(default_factory=dict)
    current_question_index: int = 0
    max_questions: int = 5  # Minimize friction
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def add_question(self, question: ClarificationQuestion) -> None:
        """Add a question to the session."""
        self.questions.append(question)

    def add_response(self, response: UserResponse) -> None:
        """Record a user response."""
        self.responses[response.question_id] = response

    def get_current_question(self) -> Optional[ClarificationQuestion]:
        """Get the next unanswered question."""
        for q in self.questions:
            if q.id not in self.responses:
                # Check dependencies
                if q.depends_on and q.depends_on not in self.responses:
                    continue
                return q
        return None

    def get_unanswered_critical(self) -> list[ClarificationQuestion]:
        """Get critical questions that haven't been answered."""
        return [
            q
            for q in self.questions
            if q.priority == QuestionPriority.CRITICAL and q.id not in self.responses
        ]

    def is_complete(self) -> bool:
        """Check if clarification is complete."""
        # All critical questions must be answered
        if self.get_unanswered_critical():
            return False
        # Either we've hit max questions or no more questions
        answered_count = len(self.responses)
        return answered_count >= self.max_questions or self.get_current_question() is None

    def complete(self) -> None:
        """Mark session as complete."""
        self.completed_at = datetime.now()

    def get_response_value(
        self, question_id: str, default: Any = None
    ) -> Any:
        """Get the value of a response by question ID."""
        response = self.responses.get(question_id)
        return response.value if response else default

    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary for persistence."""
        return {
            "session_id": self.session_id,
            "questions": [q.id for q in self.questions],
            "responses": {
                qid: {"value": r.value, "timestamp": r.timestamp.isoformat()}
                for qid, r in self.responses.items()
            },
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class StandardQuestions:
    """
    Factory for standard clarification questions.

    These are the minimal questions needed to generate a Buy Agent prompt.
    Business language only - no technical terms exposed.
    """

    @staticmethod
    def goods_or_services() -> ClarificationQuestion:
        """Question about procurement type."""
        return ClarificationQuestion.single_choice(
            id="goods_services",
            question="What type of purchases will employees make?",
            options=[
                QuestionOption("goods", "Physical goods", "Items like equipment, supplies"),
                QuestionOption("services", "Services", "Work done by vendors"),
                QuestionOption("both", "Both goods and services", default=True),
            ],
            intent_field="supports_goods,supports_services",
            help_text="This determines the workflow and approval rules",
            priority=QuestionPriority.CRITICAL,
        )

    @staticmethod
    def procurement_channels() -> ClarificationQuestion:
        """Question about available purchase channels."""
        return ClarificationQuestion.multi_choice(
            id="channels",
            question="How should employees be able to purchase items?",
            options=[
                QuestionOption("catalog", "From company catalog", default=True),
                QuestionOption("non_catalog", "Direct purchase (non-catalog)", default=True),
                QuestionOption("punchout", "Supplier website (punchout)"),
                QuestionOption("contract", "From existing contracts"),
            ],
            intent_field="enabled_channels",
            help_text="Multiple options can be selected",
            priority=QuestionPriority.CRITICAL,
        )

    @staticmethod
    def quote_support() -> ClarificationQuestion:
        """Question about quote handling."""
        return ClarificationQuestion.boolean(
            id="quote_support",
            question="Should employees be able to upload vendor quotes?",
            intent_field="quote_upload_enabled",
            default=True,
            help_text="Enables quote comparison and multi-supplier sourcing",
        )

    @staticmethod
    def value_routing() -> ClarificationQuestion:
        """Question about value-based routing."""
        return ClarificationQuestion.boolean(
            id="value_routing",
            question="Should requests be routed based on purchase value?",
            intent_field="routing_strategy",
            default=True,
            help_text="Higher value requests may require additional approval",
            priority=QuestionPriority.CRITICAL,
        )

    @staticmethod
    def supplier_validation() -> ClarificationQuestion:
        """Question about supplier validation."""
        return ClarificationQuestion.boolean(
            id="supplier_validation",
            question="Should the system verify supplier status before proceeding?",
            intent_field="supplier_validation_required",
            default=True,
            help_text="Blocks requests to inactive or blocked suppliers",
        )

    @staticmethod
    def get_standard_questions() -> list[ClarificationQuestion]:
        """Get all standard clarification questions in order."""
        return [
            StandardQuestions.goods_or_services(),
            StandardQuestions.procurement_channels(),
            StandardQuestions.quote_support(),
            StandardQuestions.value_routing(),
            StandardQuestions.supplier_validation(),
        ]

