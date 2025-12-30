"""
Browser automation module using Playwright.

Implements Template Method Pattern for browser actions.
"""

from .controller import BrowserController
from .actions import (
    NavigateAction,
    ClickAction,
    TypeAction,
    SelectAction,
    ExtractFormAction,
    ScreenshotAction,
)

__all__ = [
    "BrowserController",
    "NavigateAction",
    "ClickAction", 
    "TypeAction",
    "SelectAction",
    "ExtractFormAction",
    "ScreenshotAction",
]





