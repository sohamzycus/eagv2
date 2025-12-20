"""
Abstract interfaces defining the contracts for all components.

Implements:
- Strategy Pattern: FormFillerStrategy
- Abstract Factory Pattern: LLMProvider  
- Template Method Pattern: BrowserAction
- Observer Pattern: Observer
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ActionStatus(Enum):
    """Status of an action execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    SKIPPED = "skipped"


@dataclass
class ActionResult:
    """Result of an action execution."""
    status: ActionStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    screenshot: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        return self.status == ActionStatus.SUCCESS


@dataclass
class FormField:
    """Represents a form field extracted from the page."""
    field_type: str  # text, radio, checkbox, dropdown, textarea
    label: str
    name: str
    required: bool = False
    options: List[str] = field(default_factory=list)
    placeholder: str = ""
    current_value: str = ""
    selector: str = ""


@dataclass
class FormData:
    """Container for form fields and metadata."""
    url: str
    title: str
    fields: List[FormField]
    submit_selector: str = ""


class LLMProvider(ABC):
    """
    Abstract Factory Pattern: Defines interface for LLM providers.
    
    Concrete implementations:
    - OllamaProvider (for llama, phi4, etc.)
    - OpenAIProvider (fallback)
    """
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Generate a JSON response from the LLM."""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name being used."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available."""
        pass


class BrowserAction(ABC):
    """
    Template Method Pattern: Defines skeleton of browser actions.
    
    Subclasses implement specific steps:
    - NavigateAction
    - ClickAction
    - TypeAction
    - ExtractAction
    """
    
    @abstractmethod
    async def execute(self, page: Any, **kwargs) -> ActionResult:
        """Execute the browser action."""
        pass
    
    @abstractmethod
    def validate(self, **kwargs) -> bool:
        """Validate action parameters before execution."""
        pass
    
    async def pre_execute(self, page: Any) -> None:
        """Hook for pre-execution setup."""
        pass
    
    async def post_execute(self, page: Any, result: ActionResult) -> None:
        """Hook for post-execution cleanup."""
        pass
    
    async def run(self, page: Any, **kwargs) -> ActionResult:
        """Template method that orchestrates the action execution."""
        if not self.validate(**kwargs):
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Validation failed for action parameters"
            )
        
        await self.pre_execute(page)
        result = await self.execute(page, **kwargs)
        await self.post_execute(page, result)
        return result


class FormFillerStrategy(ABC):
    """
    Strategy Pattern: Defines algorithm for filling form fields.
    
    Concrete strategies:
    - LLMGuidedStrategy: Uses LLM to determine field values
    - RuleBasedStrategy: Uses predefined rules
    - HybridStrategy: Combines both approaches
    """
    
    @abstractmethod
    async def determine_field_value(
        self, 
        field: FormField, 
        context: Dict[str, Any]
    ) -> str:
        """Determine what value to fill in a form field."""
        pass
    
    @abstractmethod
    async def validate_response(
        self, 
        field: FormField, 
        value: str
    ) -> bool:
        """Validate that the determined value is appropriate."""
        pass


class Observer(ABC):
    """
    Observer Pattern: Defines interface for event observers.
    
    Concrete observers:
    - ConsoleLogger
    - FileLogger
    - ScreenshotCapture
    """
    
    @abstractmethod
    def update(self, event: "Event") -> None:
        """Called when an event is dispatched."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the observer's name for identification."""
        pass

