"""
Form Filling Strategies - Strategy Pattern Implementation.

Provides different approaches for determining form field values:
- LLMGuidedStrategy: Uses local LLM to intelligently fill forms
- RuleBasedStrategy: Uses predefined rules and mappings
- HybridStrategy: Combines both approaches
"""

from .llm_strategy import LLMGuidedStrategy
from .rule_strategy import RuleBasedStrategy
from .hybrid_strategy import HybridStrategy

__all__ = [
    "LLMGuidedStrategy",
    "RuleBasedStrategy",
    "HybridStrategy",
]



