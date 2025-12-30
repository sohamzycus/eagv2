"""
Core abstractions and interfaces for the Browser Agent.

Design Patterns Used:
- Abstract Factory: LLM provider creation
- Strategy: Form filling strategies  
- Observer: Event logging and monitoring
- Template Method: Browser action sequences
"""

from .interfaces import (
    LLMProvider,
    BrowserAction,
    FormFillerStrategy,
    Observer,
    ActionResult,
)
from .events import Event, EventType, EventDispatcher

__all__ = [
    "LLMProvider",
    "BrowserAction", 
    "FormFillerStrategy",
    "Observer",
    "ActionResult",
    "Event",
    "EventType",
    "EventDispatcher",
]





