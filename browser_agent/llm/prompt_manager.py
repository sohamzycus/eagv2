"""
Prompt Manager for structured prompt handling.

Loads and manages prompts from template files.
"""

import os
from pathlib import Path
from typing import Dict, Optional


class PromptManager:
    """
    Manages prompt templates for the agent.
    
    Supports variable substitution in templates.
    """
    
    def __init__(self, prompts_dir: Optional[str] = None):
        if prompts_dir:
            self.prompts_dir = Path(prompts_dir)
        else:
            # Default to prompts directory relative to this file
            self.prompts_dir = Path(__file__).parent.parent / "prompts"
        
        self._cache: Dict[str, str] = {}
    
    def load_prompt(self, name: str) -> str:
        """Load a prompt template by name."""
        if name in self._cache:
            return self._cache[name]
        
        prompt_file = self.prompts_dir / f"{name}.txt"
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_file}")
        
        content = prompt_file.read_text()
        self._cache[name] = content
        return content
    
    def format_prompt(self, name: str, **variables) -> str:
        """Load and format a prompt template with variables."""
        template = self.load_prompt(name)
        try:
            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing variable in prompt template: {e}")
    
    def get_system_prompt(self) -> str:
        """Get the main system prompt for the agent."""
        return self.load_prompt("system")
    
    def get_form_analysis_prompt(self, form_html: str, form_fields: str) -> str:
        """Get prompt for analyzing form structure."""
        return self.format_prompt(
            "form_analysis",
            form_html=form_html,
            form_fields=form_fields
        )
    
    def get_field_value_prompt(
        self, 
        field_label: str,
        field_type: str, 
        options: str,
        context: str
    ) -> str:
        """Get prompt for determining field values."""
        return self.format_prompt(
            "field_value",
            field_label=field_label,
            field_type=field_type,
            options=options,
            context=context
        )
    
    def clear_cache(self) -> None:
        """Clear the prompt cache."""
        self._cache.clear()


