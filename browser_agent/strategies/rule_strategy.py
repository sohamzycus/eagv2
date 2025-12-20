"""
Rule-Based Form Filling Strategy.

Uses predefined rules and keyword matching to determine field values.
"""

import re
from typing import Any, Dict, List, Tuple

from core.interfaces import FormFillerStrategy, FormField


class RuleBasedStrategy(FormFillerStrategy):
    """
    Strategy that uses predefined rules to determine field values.
    
    Rules are matched against field labels using keyword patterns.
    """
    
    def __init__(self, rules: Dict[str, Any] = None, user_data: Dict[str, str] = None):
        # Start with defaults, then update with provided user_data
        self.user_data = {
            "name": "Soham Niyogi",
            "email": "sohamniyogi9@gmail.com",
            "github_url": "https://github.com/sohamniyogi/browser-agent",
            "youtube_url": "https://www.youtube.com/watch?v=example",
            "default_text": "This is a sample response.",
        }
        if user_data:
            self.user_data.update(user_data)
        
        # Default rules: (pattern, value_key or callable)
        self.rules: List[Tuple[str, str]] = [
            (r"(?i)name", "name"),
            (r"(?i)email", "email"),
            (r"(?i)github|code|repository", "github_url"),
            (r"(?i)youtube|video|demo", "youtube_url"),
            (r"(?i)url|link|http", "github_url"),
        ]
        
        if rules:
            self.rules.extend(rules.items())
    
    async def determine_field_value(
        self, 
        field: FormField, 
        context: Dict[str, Any]
    ) -> str:
        """Determine value based on rule matching."""
        label = field.label
        
        # Check if there are options (radio/dropdown)
        if field.options:
            # For multiple choice, try to match context or return first option
            for option in field.options:
                if any(kw in option.lower() for kw in context.get("keywords", [])):
                    return option
            return field.options[0]
        
        # Match against rules
        for pattern, value_key in self.rules:
            if re.search(pattern, label):
                if callable(value_key):
                    return value_key(field, context)
                return self.user_data.get(value_key, self.user_data["default_text"])
        
        # Default fallback
        return self.user_data.get("default_text", "N/A")
    
    async def validate_response(
        self, 
        field: FormField, 
        value: str
    ) -> bool:
        """Validate the value against field constraints."""
        if not value and field.required:
            return False
        
        if field.options and value not in field.options:
            return False
        
        # Basic type validation
        if field.field_type == "email" and value:
            return "@" in value and "." in value
        
        if field.field_type == "url" and value:
            return value.startswith(("http://", "https://"))
        
        return True
    
    def add_rule(self, pattern: str, value: str) -> None:
        """Add a new rule to the strategy."""
        self.rules.append((pattern, value))
    
    def set_user_data(self, key: str, value: str) -> None:
        """Update user data used in rule matching."""
        self.user_data[key] = value

