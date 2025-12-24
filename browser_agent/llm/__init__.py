"""
LLM Provider Module - Abstract Factory Pattern Implementation.

Supports local models via Ollama (llama, phi4, mistral, etc.)
"""

from .providers import OllamaProvider, LLMProviderFactory
from .prompt_manager import PromptManager

__all__ = [
    "OllamaProvider",
    "LLMProviderFactory", 
    "PromptManager",
]


