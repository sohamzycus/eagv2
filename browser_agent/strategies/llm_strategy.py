"""
LLM-Guided Form Filling Strategy.

Uses local LLM to analyze form fields and determine appropriate values.
"""

from typing import Any, Dict
import json

from core.interfaces import FormFillerStrategy, FormField, LLMProvider
from core.events import Event, EventType, EventDispatcher


class LLMGuidedStrategy(FormFillerStrategy):
    """
    Strategy that uses LLM to determine field values.
    
    The LLM analyzes the field label, type, and context to generate
    appropriate responses for form filling.
    """
    
    def __init__(self, llm_provider: LLMProvider, user_context: Dict[str, Any] = None):
        self.llm = llm_provider
        self.user_context = user_context or {}
        self.dispatcher = EventDispatcher()
    
    async def determine_field_value(
        self, 
        field: FormField, 
        context: Dict[str, Any]
    ) -> str:
        """Use LLM to determine the appropriate value for a form field."""
        
        # Build the prompt
        system_prompt = """You are a form-filling assistant. Your job is to provide appropriate values for form fields.

IMPORTANT RULES:
1. Respond with ONLY the value to fill, nothing else
2. For multiple choice (radio/dropdown), respond with EXACTLY one of the provided options
3. For text fields, provide a reasonable, relevant response
4. Be concise and direct
5. If the field asks for a name, use: {name}
6. If the field asks for email, use: {email}
7. If the field asks for a URL, provide a valid URL format
""".format(
            name=self.user_context.get("name", "Soham Niyogi"),
            email=self.user_context.get("email", "sohamniyogi9@gmail.com")
        )
        
        # Build context string
        context_str = "\n".join([
            f"- {k}: {v}" for k, v in {**self.user_context, **context}.items()
        ])
        
        options_str = ""
        if field.options:
            options_str = f"\nAvailable options (choose EXACTLY one): {field.options}"
        
        prompt = f"""Determine the value to fill for this form field:

Field Label: {field.label}
Field Type: {field.field_type}
Required: {field.required}
Placeholder: {field.placeholder}{options_str}

Context:
{context_str}

Respond with ONLY the value to use (no explanation, no quotes, no formatting):"""
        
        try:
            response = await self.llm.generate(prompt, system_prompt)
            value = response.strip().strip('"').strip("'")
            
            # For multiple choice, ensure the value is from options
            if field.options and value not in field.options:
                # Try to find a close match
                value_lower = value.lower()
                for option in field.options:
                    if option.lower() in value_lower or value_lower in option.lower():
                        value = option
                        break
                else:
                    # Default to first option if no match
                    value = field.options[0]
            
            self.dispatcher.dispatch(Event(
                event_type=EventType.LLM_RESPONSE_RECEIVED,
                message=f"LLM determined value for '{field.label}'",
                data={"field": field.label, "value": value}
            ))
            
            return value
            
        except Exception as e:
            self.dispatcher.dispatch(Event(
                event_type=EventType.LLM_ERROR,
                message=f"LLM error for field '{field.label}': {str(e)}",
                data={"error": str(e)}
            ))
            
            # Fallback to default values
            return self._get_fallback_value(field)
    
    async def validate_response(
        self, 
        field: FormField, 
        value: str
    ) -> bool:
        """Validate that the value is appropriate for the field."""
        if not value:
            return not field.required
        
        if field.options and value not in field.options:
            return False
        
        return True
    
    def _get_fallback_value(self, field: FormField) -> str:
        """Get a fallback value when LLM fails."""
        if field.options:
            return field.options[0]
        
        label_lower = field.label.lower()
        
        if "name" in label_lower:
            return self.user_context.get("name", "Soham Niyogi")
        elif "email" in label_lower:
            return self.user_context.get("email", "sohamniyogi9@gmail.com")
        elif "url" in label_lower or "link" in label_lower:
            return self.user_context.get("github_url", "https://github.com/sohamniyogi")
        else:
            return self.user_context.get("default_text", "N/A")

