"""
LLM Client Interface.

Abstract base class for all LLM implementations.
Follows Dependency Inversion Principle - agents depend on this abstraction.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageRole(Enum):
    """Standard message roles across all LLM providers."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


@dataclass
class LLMMessage:
    """
    A message in the LLM conversation.

    Provider-agnostic representation that gets adapted per model.
    """

    role: MessageRole
    content: str
    name: Optional[str] = None  # For function/tool messages
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        """Convert to simple dict format."""
        result = {"role": self.role.value, "content": self.content}
        if self.name:
            result["name"] = self.name
        return result

    @classmethod
    def system(cls, content: str) -> "LLMMessage":
        """Create a system message."""
        return cls(role=MessageRole.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "LLMMessage":
        """Create a user message."""
        return cls(role=MessageRole.USER, content=content)

    @classmethod
    def assistant(cls, content: str) -> "LLMMessage":
        """Create an assistant message."""
        return cls(role=MessageRole.ASSISTANT, content=content)


@dataclass
class LLMResponse:
    """
    Response from an LLM call.

    Contains the generated content plus metadata for logging/debugging.
    """

    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = ""
    latency_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_cost_estimate(self) -> float:
        """Estimate cost based on token usage (rough approximation)."""
        # Approximate costs per 1K tokens (varies by model)
        input_cost = self.prompt_tokens * 0.00001
        output_cost = self.completion_tokens * 0.00003
        return input_cost + output_cost


class LLMClient(ABC):
    """
    Abstract base class for LLM clients.

    All model-specific implementations must inherit from this.
    Agents ONLY interact with this interface - never with concrete implementations.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name (e.g., 'azure_openai', 'openai', 'anthropic')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the model name (e.g., 'gpt-4o', 'claude-3-sonnet')."""
        pass

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            system_prompt: The system prompt defining agent behavior
            messages: List of conversation messages
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate
            stop_sequences: Sequences that stop generation

        Returns:
            LLMResponse containing the generated content and metadata
        """
        pass

    @abstractmethod
    def generate_with_structured_output(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        output_schema: Dict[str, Any],
        temperature: float = 0.0,
    ) -> LLMResponse:
        """
        Generate a response with structured JSON output.

        Args:
            system_prompt: The system prompt
            messages: Conversation messages
            output_schema: JSON schema for the expected output
            temperature: Sampling temperature

        Returns:
            LLMResponse with JSON-parseable content
        """
        pass

    def generate_simple(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> str:
        """
        Simplified generation for single-turn interactions.

        Convenience method that wraps generate().
        """
        response = self.generate(
            system_prompt=system_prompt,
            messages=[LLMMessage.user(user_message)],
            temperature=temperature,
        )
        return response.content

    def is_available(self) -> bool:
        """
        Check if the LLM client is available and configured.

        Override in implementations to add health checks.
        """
        return True

