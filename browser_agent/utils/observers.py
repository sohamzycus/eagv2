"""
Observer implementations for logging and monitoring.

Implements Observer Pattern for event-driven logging.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.interfaces import Observer
from core.events import Event, EventType


class ConsoleLogger(Observer):
    """
    Logs events to console with colored output.
    """
    
    # ANSI color codes
    COLORS = {
        "reset": "\033[0m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
    }
    
    EVENT_COLORS = {
        EventType.NAVIGATION_START: "blue",
        EventType.NAVIGATION_COMPLETE: "green",
        EventType.NAVIGATION_ERROR: "red",
        EventType.FORM_DETECTED: "cyan",
        EventType.FIELD_EXTRACTED: "cyan",
        EventType.FIELD_FILLED: "green",
        EventType.FORM_SUBMITTED: "green",
        EventType.FORM_SUBMISSION_ERROR: "red",
        EventType.LLM_PROMPT_SENT: "magenta",
        EventType.LLM_RESPONSE_RECEIVED: "magenta",
        EventType.LLM_ERROR: "red",
        EventType.BROWSER_LAUNCHED: "blue",
        EventType.BROWSER_CLOSED: "blue",
        EventType.SCREENSHOT_CAPTURED: "yellow",
        EventType.AGENT_STARTED: "green",
        EventType.AGENT_COMPLETED: "green",
        EventType.AGENT_ERROR: "red",
        EventType.ACTION_EXECUTED: "cyan",
    }
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
    
    def get_name(self) -> str:
        return "ConsoleLogger"
    
    def update(self, event: Event) -> None:
        """Log event to console."""
        color = self.EVENT_COLORS.get(event.event_type, "reset")
        color_code = self.COLORS[color]
        reset = self.COLORS["reset"]
        
        timestamp = event.timestamp.strftime("%H:%M:%S")
        type_name = event.event_type.name
        
        print(f"{color_code}[{timestamp}] {type_name}: {event.message}{reset}")
        
        if self.verbose and event.data:
            for key, value in event.data.items():
                print(f"  {key}: {value}")


class FileLogger(Observer):
    """
    Logs events to a JSON file for later analysis.
    """
    
    def __init__(self, log_file: str = "agent_log.json"):
        self.log_file = Path(log_file)
        self.events = []
        
        # Create or clear log file
        self.log_file.write_text("[]")
    
    def get_name(self) -> str:
        return "FileLogger"
    
    def update(self, event: Event) -> None:
        """Log event to file."""
        self.events.append(event.to_dict())
        
        # Write all events to file
        with open(self.log_file, 'w') as f:
            json.dump(self.events, f, indent=2, default=str)
    
    def get_events(self) -> list:
        """Get all logged events."""
        return self.events.copy()
    
    def clear(self) -> None:
        """Clear the log."""
        self.events = []
        self.log_file.write_text("[]")


class ScreenshotObserver(Observer):
    """
    Captures screenshots on specific events.
    """
    
    def __init__(self, screenshots_dir: str = "screenshots", page=None):
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.page = page
        self.screenshot_count = 0
        
        # Events that trigger screenshots
        self.trigger_events = {
            EventType.NAVIGATION_COMPLETE,
            EventType.FORM_DETECTED,
            EventType.FORM_SUBMITTED,
            EventType.AGENT_ERROR,
        }
    
    def get_name(self) -> str:
        return "ScreenshotObserver"
    
    def set_page(self, page) -> None:
        """Set the page to capture screenshots from."""
        self.page = page
    
    def update(self, event: Event) -> None:
        """Capture screenshot on relevant events."""
        if event.event_type in self.trigger_events and self.page:
            self.screenshot_count += 1
            filename = f"{self.screenshot_count:03d}_{event.event_type.name}.png"
            path = self.screenshots_dir / filename
            
            # Note: This is synchronous, should be run in event loop
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule screenshot capture
                    asyncio.create_task(self._capture(str(path)))
            except:
                pass
    
    async def _capture(self, path: str) -> None:
        """Capture screenshot asynchronously."""
        if self.page:
            try:
                await self.page.screenshot(path=path, full_page=True)
            except:
                pass


