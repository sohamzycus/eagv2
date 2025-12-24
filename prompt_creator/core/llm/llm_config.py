"""
LLM Configuration.

Single source of truth for LLM settings.
Supports multiple providers and model families.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
import os


class LLMProvider(Enum):
    """Supported LLM providers."""

    AZURE_OPENAI = "azure_openai"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"  # For testing


class ModelFamily(Enum):
    """
    Model families for prompt adaptation.

    Different models require different prompt phrasing for optimal results.
    """

    GPT_4O = "gpt-4o"
    GPT_4_1 = "gpt-4.1"  # Future
    GPT_5_1 = "gpt-5.1"  # Future
    GPT_5_2 = "gpt-5.2"  # Future
    CLAUDE_SONNET = "claude-sonnet"
    CLAUDE_OPUS = "claude-opus"


@dataclass(frozen=True)
class LLMConfig:
    """
    Immutable LLM configuration.

    This is the SINGLE SOURCE OF TRUTH for LLM settings.
    Change provider/model here - no code changes elsewhere needed.
    """

    provider: LLMProvider
    model: str
    model_family: ModelFamily
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout_seconds: int = 120

    # Azure-specific settings
    azure_endpoint: Optional[str] = None
    azure_deployment: Optional[str] = None
    azure_api_version: str = "2024-02-01"

    # Rate limiting
    max_retries: int = 3
    retry_delay_seconds: float = 1.0

    # Feature flags
    enable_structured_output: bool = True
    enable_streaming: bool = False

    # Prompt adaptation settings
    use_system_message: bool = True  # Some models handle system differently
    chain_of_thought_style: str = "hidden"  # hidden, visible, xml_tags

    def __post_init__(self):
        """Validate configuration."""
        if self.provider == LLMProvider.AZURE_OPENAI:
            if not self.azure_endpoint:
                raise ValueError("Azure endpoint required for Azure OpenAI")
            if not self.azure_deployment:
                raise ValueError("Azure deployment required for Azure OpenAI")

    @classmethod
    def azure_gpt4o(
        cls,
        endpoint: str,
        deployment: str,
        api_version: str = "2024-02-15-preview",
        temperature: float = 0.0,
    ) -> "LLMConfig":
        """Factory for Azure OpenAI GPT-4o configuration."""
        return cls(
            provider=LLMProvider.AZURE_OPENAI,
            model="gpt-4o",
            model_family=ModelFamily.GPT_4O,
            temperature=temperature,
            azure_endpoint=endpoint,
            azure_deployment=deployment,
            azure_api_version=api_version,
        )

    @classmethod
    def zycus_gpt4o(cls, api_key: str = None, temperature: float = 0.0) -> "LLMConfig":
        """
        Factory for Zycus Azure OpenAI GPT-4o configuration.
        
        Pre-configured for Zycus PTU endpoint.
        """
        return cls(
            provider=LLMProvider.AZURE_OPENAI,
            model="gpt-4o",
            model_family=ModelFamily.GPT_4O,
            temperature=temperature,
            azure_endpoint="https://zycus-ptu.azure-api.net/ptu-intakemanagement",
            azure_deployment="gpt4o-130524",
            azure_api_version="2024-02-15-preview",
        )

    @classmethod
    def openai_gpt4o(cls, temperature: float = 0.0) -> "LLMConfig":
        """Factory for OpenAI GPT-4o configuration."""
        return cls(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            model_family=ModelFamily.GPT_4O,
            temperature=temperature,
        )

    @classmethod
    def claude_sonnet(cls, temperature: float = 0.0) -> "LLMConfig":
        """Factory for Claude Sonnet configuration."""
        return cls(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-sonnet-20240229",
            model_family=ModelFamily.CLAUDE_SONNET,
            temperature=temperature,
            use_system_message=True,
            chain_of_thought_style="xml_tags",
        )

    @classmethod
    def claude_opus(cls, temperature: float = 0.0) -> "LLMConfig":
        """Factory for Claude Opus configuration."""
        return cls(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-opus-20240229",
            model_family=ModelFamily.CLAUDE_OPUS,
            temperature=temperature,
            use_system_message=True,
            chain_of_thought_style="xml_tags",
        )

    @classmethod
    def mock(cls) -> "LLMConfig":
        """Factory for mock/testing configuration."""
        return cls(
            provider=LLMProvider.MOCK,
            model="mock-model",
            model_family=ModelFamily.GPT_4O,
            temperature=0.0,
        )

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """
        Create configuration from environment variables.

        Environment variables:
            LLM_PROVIDER: azure_openai, openai, anthropic
            LLM_MODEL: gpt-4o, claude-3-sonnet, etc.
            AZURE_OPENAI_ENDPOINT: Azure endpoint URL
            AZURE_OPENAI_DEPLOYMENT: Azure deployment name
            AZURE_OPENAI_API_VERSION: API version (optional)
            LLM_TEMPERATURE: Sampling temperature (optional)
        """
        provider_str = os.getenv("LLM_PROVIDER", "azure_openai").lower()
        provider = LLMProvider(provider_str)

        model = os.getenv("LLM_MODEL", "gpt-4o")
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))

        # Determine model family
        model_family = cls._detect_model_family(model)

        if provider == LLMProvider.AZURE_OPENAI:
            return cls(
                provider=provider,
                model=model,
                model_family=model_family,
                temperature=temperature,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            )
        elif provider == LLMProvider.OPENAI:
            return cls(
                provider=provider,
                model=model,
                model_family=model_family,
                temperature=temperature,
            )
        elif provider == LLMProvider.ANTHROPIC:
            return cls(
                provider=provider,
                model=model,
                model_family=model_family,
                temperature=temperature,
                use_system_message=True,
                chain_of_thought_style="xml_tags",
            )
        else:
            return cls.mock()

    @staticmethod
    def _detect_model_family(model: str) -> ModelFamily:
        """Detect model family from model name."""
        model_lower = model.lower()

        if "gpt-4o" in model_lower:
            return ModelFamily.GPT_4O
        elif "gpt-4.1" in model_lower:
            return ModelFamily.GPT_4_1
        elif "gpt-5.1" in model_lower:
            return ModelFamily.GPT_5_1
        elif "gpt-5.2" in model_lower:
            return ModelFamily.GPT_5_2
        elif "opus" in model_lower:
            return ModelFamily.CLAUDE_OPUS
        elif "sonnet" in model_lower or "claude" in model_lower:
            return ModelFamily.CLAUDE_SONNET
        else:
            return ModelFamily.GPT_4O  # Default


@dataclass
class PromptAdaptationConfig:
    """
    Configuration for adapting prompts to different model families.

    Each model family may require different prompt phrasing techniques.
    """

    model_family: ModelFamily

    # Phrasing preferences
    use_imperative: bool = True  # "Do X" vs "You should X"
    use_markdown: bool = True  # Use markdown formatting
    use_xml_tags: bool = False  # Use XML-style tags for structure

    # Chain-of-thought settings
    cot_instruction: str = "Think step by step"
    hide_cot: bool = True  # Hide reasoning from user

    # Guardrail phrasing
    prohibition_prefix: str = "NEVER"
    requirement_prefix: str = "ALWAYS"

    # Structural preferences
    max_section_depth: int = 3
    use_numbered_lists: bool = True
    use_emoji: bool = True

    @classmethod
    def for_model_family(cls, family: ModelFamily) -> "PromptAdaptationConfig":
        """Get adaptation config for a model family."""
        configs = {
            ModelFamily.GPT_4O: cls(
                model_family=family,
                use_imperative=True,
                use_markdown=True,
                use_xml_tags=False,
                cot_instruction="Think through this step by step, but keep your reasoning internal.",
                hide_cot=True,
            ),
            ModelFamily.GPT_4_1: cls(
                model_family=family,
                use_imperative=True,
                use_markdown=True,
                use_xml_tags=False,
                cot_instruction="Reason carefully before responding.",
                hide_cot=True,
            ),
            ModelFamily.GPT_5_1: cls(
                model_family=family,
                use_imperative=True,
                use_markdown=True,
                use_xml_tags=False,
                cot_instruction="Apply systematic reasoning.",
                hide_cot=True,
            ),
            ModelFamily.GPT_5_2: cls(
                model_family=family,
                use_imperative=True,
                use_markdown=True,
                use_xml_tags=False,
                cot_instruction="Use structured reasoning.",
                hide_cot=True,
            ),
            ModelFamily.CLAUDE_SONNET: cls(
                model_family=family,
                use_imperative=False,  # Claude prefers softer phrasing
                use_markdown=True,
                use_xml_tags=True,  # Claude works well with XML
                cot_instruction="<thinking>Think through this carefully before responding.</thinking>",
                hide_cot=True,
                prohibition_prefix="You must never",
                requirement_prefix="You must always",
            ),
            ModelFamily.CLAUDE_OPUS: cls(
                model_family=family,
                use_imperative=False,
                use_markdown=True,
                use_xml_tags=True,
                cot_instruction="<thinking>Reason through this systematically.</thinking>",
                hide_cot=True,
                prohibition_prefix="You must never",
                requirement_prefix="You must always",
            ),
        }

        return configs.get(family, configs[ModelFamily.GPT_4O])

