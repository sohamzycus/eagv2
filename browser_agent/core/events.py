"""
Event system implementing the Observer Pattern.

Provides a decoupled way to log, monitor, and react to agent actions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .interfaces import Observer


class EventType(Enum):
    """Types of events that can occur during agent execution."""
    
    # Navigation events
    NAVIGATION_START = auto()
    NAVIGATION_COMPLETE = auto()
    NAVIGATION_ERROR = auto()
    
    # Form events
    FORM_DETECTED = auto()
    FIELD_EXTRACTED = auto()
    FIELD_FILLED = auto()
    FORM_SUBMITTED = auto()
    FORM_SUBMISSION_ERROR = auto()
    
    # LLM events
    LLM_PROMPT_SENT = auto()
    LLM_RESPONSE_RECEIVED = auto()
    LLM_ERROR = auto()
    
    # Browser events
    BROWSER_LAUNCHED = auto()
    BROWSER_CLOSED = auto()
    SCREENSHOT_CAPTURED = auto()
    
    # Agent events
    AGENT_STARTED = auto()
    AGENT_COMPLETED = auto()
    AGENT_ERROR = auto()
    ACTION_EXECUTED = auto()


@dataclass
class Event:
    """Represents an event in the system."""
    
    event_type: EventType
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for logging."""
        return {
            "type": self.event_type.name,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }


class EventDispatcher:
    """
    Central hub for event dispatching (Observer Pattern).
    
    Manages observers and dispatches events to all registered observers.
    Implements Singleton pattern to ensure single dispatcher instance.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._observers: List["Observer"] = []
            cls._instance._event_history: List[Event] = []
        return cls._instance
    
    def attach(self, observer: "Observer") -> None:
        """Attach an observer to receive events."""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer: "Observer") -> None:
        """Detach an observer from receiving events."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def dispatch(self, event: Event) -> None:
        """Dispatch an event to all attached observers."""
        self._event_history.append(event)
        for observer in self._observers:
            try:
                observer.update(event)
            except Exception as e:
                # Log error but don't break the dispatch chain
                print(f"Error in observer {observer.get_name()}: {e}")
    
    def get_history(self) -> List[Event]:
        """Get the event history."""
        return self._event_history.copy()
    
    def clear_history(self) -> None:
        """Clear the event history."""
        self._event_history.clear()
    
    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None



