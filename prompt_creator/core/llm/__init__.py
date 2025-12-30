"""
LLM Abstraction Layer.

Provides model-agnostic interface for LLM operations.
Supports Azure OpenAI, OpenAI, and future Claude/GPT-5.x models.
"""

from .llm_client import LLMClient, LLMResponse, LLMMessage
from .llm_config import LLMConfig, LLMProvider, ModelFamily
from .llm_factory import LLMFactory
from .llm_logger import LLMCallLogger, LLMCallRecord

__all__ = [
    "LLMClient",
    "LLMResponse",
    "LLMMessage",
    "LLMConfig",
    "LLMProvider",
    "ModelFamily",
    "LLMFactory",
    "LLMCallLogger",
    "LLMCallRecord",
]



