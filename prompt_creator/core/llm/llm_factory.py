"""
LLM Factory.

Creates LLM clients based on configuration.
Single entry point for LLM instantiation.
"""

import os
from typing import Optional

from .llm_client import LLMClient
from .llm_config import LLMConfig, LLMProvider
from .azure_openai_client import AzureOpenAIClient, OpenAIClient, MockLLMClient


class LLMFactory:
    """
    Factory for creating LLM clients.

    This is the ONLY place where LLM clients are instantiated.
    Agents receive clients via dependency injection.
    """

    _instance: Optional["LLMFactory"] = None
    _client: Optional[LLMClient] = None
    _config: Optional[LLMConfig] = None

    def __new__(cls) -> "LLMFactory":
        """Singleton pattern for factory."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset factory state."""
        cls._instance = None
        cls._client = None
        cls._config = None

    @classmethod
    def create(
        cls,
        config: LLMConfig,
        api_key: Optional[str] = None,
        verify_ssl: bool = True,
    ) -> LLMClient:
        """
        Create an LLM client based on configuration.

        Args:
            config: LLM configuration
            api_key: API key (can also be read from environment)
            verify_ssl: Whether to verify SSL certificates (set False for corporate APIM)

        Returns:
            LLMClient implementation for the specified provider
        """
        # Get API key from environment if not provided
        if api_key is None:
            api_key = cls._get_api_key(config.provider)

        # Check environment for SSL verification setting
        if os.getenv("AZURE_OPENAI_VERIFY_SSL", "true").lower() == "false":
            verify_ssl = False

        # Create client based on provider
        if config.provider == LLMProvider.AZURE_OPENAI:
            return AzureOpenAIClient(config, api_key, verify_ssl=verify_ssl)

        elif config.provider == LLMProvider.OPENAI:
            return OpenAIClient(config, api_key)

        elif config.provider == LLMProvider.ANTHROPIC:
            # Future: Implement AnthropicClient
            raise NotImplementedError(
                "Anthropic client not yet implemented. "
                "Use OpenAI or Azure OpenAI for now."
            )

        elif config.provider == LLMProvider.MOCK:
            return MockLLMClient(config)

        else:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")

    @classmethod
    def create_default(cls) -> LLMClient:
        """
        Create default LLM client from environment.

        Uses LLMConfig.from_env() to read configuration.
        """
        config = LLMConfig.from_env()
        return cls.create(config)

    @classmethod
    def create_azure_gpt4o(
        cls,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> LLMClient:
        """
        Convenience method to create Azure OpenAI GPT-4o client.

        Args:
            endpoint: Azure endpoint (or from AZURE_OPENAI_ENDPOINT env)
            deployment: Deployment name (or from AZURE_OPENAI_DEPLOYMENT env)
            api_key: API key (or from AZURE_OPENAI_API_KEY env)
            api_version: API version (or from AZURE_OPENAI_API_VERSION env)
        """
        endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

        if not endpoint or not deployment:
            raise ValueError(
                "Azure OpenAI requires endpoint and deployment. "
                "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT environment variables."
            )

        config = LLMConfig.azure_gpt4o(
            endpoint=endpoint,
            deployment=deployment,
            api_version=api_version,
        )

        return cls.create(config, api_key)

    @classmethod
    def create_zycus_gpt4o(cls, api_key: Optional[str] = None, verify_ssl: bool = False) -> LLMClient:
        """
        Create Zycus Azure OpenAI GPT-4o client.
        
        Pre-configured for Zycus PTU endpoint:
        - Endpoint: https://zycus-ptu.azure-api.net/ptu-intakemanagement
        - Deployment: gpt4o-130524
        - API Version: 2024-02-15-preview
        
        Note: SSL verification is disabled by default for corporate APIM endpoints.
        
        Args:
            api_key: API key (or from AZURE_OPENAI_API_KEY env)
            verify_ssl: Whether to verify SSL (default False for Zycus APIM)
        """
        api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("API key required. Set AZURE_OPENAI_API_KEY environment variable.")
        
        config = LLMConfig.zycus_gpt4o()
        return cls.create(config, api_key, verify_ssl=verify_ssl)

    @classmethod
    def create_openai_gpt4o(cls, api_key: Optional[str] = None) -> LLMClient:
        """
        Convenience method to create OpenAI GPT-4o client.

        Args:
            api_key: API key (or from OPENAI_API_KEY env)
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable."
            )

        config = LLMConfig.openai_gpt4o()
        return cls.create(config, api_key)

    @classmethod
    def create_mock(cls) -> LLMClient:
        """Create mock client for testing."""
        return MockLLMClient()

    @staticmethod
    def _get_api_key(provider: LLMProvider) -> str:
        """Get API key from environment based on provider."""
        env_vars = {
            LLMProvider.AZURE_OPENAI: "AZURE_OPENAI_API_KEY",
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.MOCK: None,
        }

        env_var = env_vars.get(provider)
        if env_var is None:
            return ""

        api_key = os.getenv(env_var, "")
        if not api_key and provider != LLMProvider.MOCK:
            raise ValueError(
                f"API key required for {provider.value}. "
                f"Set {env_var} environment variable."
            )

        return api_key

    @classmethod
    def get_or_create(
        cls,
        config: Optional[LLMConfig] = None,
        api_key: Optional[str] = None,
    ) -> LLMClient:
        """
        Get cached client or create new one.

        Singleton pattern - reuses client if config matches.
        """
        if config is None:
            config = LLMConfig.from_env()

        # Return cached client if config matches
        if cls._client is not None and cls._config == config:
            return cls._client

        # Create and cache new client
        cls._client = cls.create(config, api_key)
        cls._config = config

        return cls._client

