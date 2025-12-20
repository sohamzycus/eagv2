"""
Hybrid Form Filling Strategy.

Combines Rule-Based and LLM-Guided strategies for optimal form filling.
Uses rules when confident, falls back to LLM for complex fields.
"""

from typing import Any, Dict

from core.interfaces import FormFillerStrategy, FormField, LLMProvider
from .llm_strategy import LLMGuidedStrategy
from .rule_strategy import RuleBasedStrategy


class HybridStrategy(FormFillerStrategy):
    """
    Combines rule-based and LLM-guided strategies.
    
    Strategy:
    1. Try rule-based first for known patterns
    2. Fall back to LLM for complex or unknown fields
    3. Validate with LLM if needed
    """
    
    def __init__(
        self, 
        llm_provider: LLMProvider,
        user_data: Dict[str, str] = None,
        use_llm_for_options: bool = True
    ):
        self.rule_strategy = RuleBasedStrategy(user_data=user_data)
        self.llm_strategy = LLMGuidedStrategy(
            llm_provider, 
            user_context=user_data or {}
        )
        self.use_llm_for_options = use_llm_for_options
        
        # Patterns that should use rules (high confidence)
        self.rule_patterns = [
            "name", "email", "phone", "address", 
            "github", "url", "link"
        ]
    
    async def determine_field_value(
        self, 
        field: FormField, 
        context: Dict[str, Any]
    ) -> str:
        """Determine value using hybrid approach."""
        label_lower = field.label.lower()
        
        # Decision logic: when to use rules vs LLM
        use_rules = any(pattern in label_lower for pattern in self.rule_patterns)
        has_options = bool(field.options)
        
        if has_options and self.use_llm_for_options:
            # Use LLM for multiple choice to make intelligent selections
            return await self.llm_strategy.determine_field_value(field, context)
        elif use_rules and not has_options:
            # Use rules for known patterns
            value = await self.rule_strategy.determine_field_value(field, context)
            
            # Validate with LLM if needed
            is_valid = await self.rule_strategy.validate_response(field, value)
            if not is_valid:
                return await self.llm_strategy.determine_field_value(field, context)
            
            return value
        else:
            # Default to LLM for unknown or complex fields
            return await self.llm_strategy.determine_field_value(field, context)
    
    async def validate_response(
        self, 
        field: FormField, 
        value: str
    ) -> bool:
        """Validate using rule-based validation first, then LLM if needed."""
        # Quick rule-based validation
        is_valid = await self.rule_strategy.validate_response(field, value)
        
        if is_valid:
            return True
        
        # LLM validation for edge cases
        return await self.llm_strategy.validate_response(field, value)

