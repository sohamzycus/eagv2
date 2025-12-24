"""
Azure OpenAI GPT-4o Client Implementation.

This is the ONLY place where Azure OpenAI API is called.
All agents use this via the LLMClient abstraction.
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from .llm_client import LLMClient, LLMMessage, LLMResponse, MessageRole
from .llm_config import LLMConfig, LLMProvider


class AzureOpenAIClient(LLMClient):
    """
    Azure OpenAI GPT-4o client implementation.

    This class is the ONLY place where Azure OpenAI API calls are made.
    Agents never import or call Azure OpenAI directly.
    """

    def __init__(self, config: LLMConfig, api_key: str, verify_ssl: bool = True):
        """
        Initialize Azure OpenAI client.

        Args:
            config: LLM configuration
            api_key: Azure OpenAI API key
            verify_ssl: Whether to verify SSL certificates (set False for corporate APIM)
        """
        if config.provider != LLMProvider.AZURE_OPENAI:
            raise ValueError("AzureOpenAIClient requires AZURE_OPENAI provider config")

        self._config = config
        self._api_key = api_key
        self._verify_ssl = verify_ssl

        # Lazy import to avoid dependency issues
        try:
            from openai import AzureOpenAI
            import httpx

            # Create custom http client for SSL handling
            if not verify_ssl:
                import warnings
                warnings.filterwarnings('ignore', message='Unverified HTTPS request')
                http_client = httpx.Client(verify=False)
                self._client = AzureOpenAI(
                    api_key=api_key,
                    api_version=config.azure_api_version,
                    azure_endpoint=config.azure_endpoint,
                    http_client=http_client,
                )
            else:
                self._client = AzureOpenAI(
                    api_key=api_key,
                    api_version=config.azure_api_version,
                    azure_endpoint=config.azure_endpoint,
                )
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")

    @property
    def provider_name(self) -> str:
        return "azure_openai"

    @property
    def model_name(self) -> str:
        return self._config.model

    def generate(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
    ) -> LLMResponse:
        """
        Generate a response using Azure OpenAI GPT-4o.

        Args:
            system_prompt: System prompt for the model
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stop_sequences: Stop sequences

        Returns:
            LLMResponse with generated content
        """
        start_time = time.time()

        # Build messages array
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            api_messages.append(msg.to_dict())

        # Make API call
        try:
            response = self._client.chat.completions.create(
                model=self._config.azure_deployment,
                messages=api_messages,
                temperature=temperature or self._config.temperature,
                max_tokens=max_tokens or self._config.max_tokens,
                stop=stop_sequences,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=self._config.model,
                provider=self.provider_name,
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
                finish_reason=response.choices[0].finish_reason or "",
                latency_ms=latency_ms,
                request_id=response.id,
                metadata={
                    "deployment": self._config.azure_deployment,
                    "api_version": self._config.azure_api_version,
                },
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return LLMResponse(
                content=f"Error: {str(e)}",
                model=self._config.model,
                provider=self.provider_name,
                latency_ms=latency_ms,
                finish_reason="error",
                metadata={"error": str(e)},
            )

    def generate_with_structured_output(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        output_schema: Dict[str, Any],
        temperature: float = 0.0,
    ) -> LLMResponse:
        """
        Generate a response with structured JSON output.

        Uses response_format to ensure JSON output.
        """
        start_time = time.time()

        # Add schema instruction to system prompt
        schema_instruction = f"""
You must respond with valid JSON matching this schema:
```json
{json.dumps(output_schema, indent=2)}
```

Respond ONLY with the JSON object, no additional text.
"""
        enhanced_prompt = f"{system_prompt}\n\n{schema_instruction}"

        # Build messages
        api_messages = [{"role": "system", "content": enhanced_prompt}]
        for msg in messages:
            api_messages.append(msg.to_dict())

        try:
            response = self._client.chat.completions.create(
                model=self._config.azure_deployment,
                messages=api_messages,
                temperature=temperature or self._config.temperature,
                response_format={"type": "json_object"},
            )

            latency_ms = int((time.time() - start_time) * 1000)

            return LLMResponse(
                content=response.choices[0].message.content or "{}",
                model=self._config.model,
                provider=self.provider_name,
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
                finish_reason=response.choices[0].finish_reason or "",
                latency_ms=latency_ms,
                request_id=response.id,
                metadata={"structured_output": True},
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return LLMResponse(
                content="{}",
                model=self._config.model,
                provider=self.provider_name,
                latency_ms=latency_ms,
                finish_reason="error",
                metadata={"error": str(e)},
            )

    def is_available(self) -> bool:
        """Check if Azure OpenAI is available."""
        try:
            # Simple health check
            response = self._client.chat.completions.create(
                model=self._config.azure_deployment,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False


class OpenAIClient(LLMClient):
    """
    Standard OpenAI client implementation.

    Fallback when Azure OpenAI is not available.
    """

    def __init__(self, config: LLMConfig, api_key: str):
        if config.provider != LLMProvider.OPENAI:
            raise ValueError("OpenAIClient requires OPENAI provider config")

        self._config = config
        self._api_key = api_key

        try:
            from openai import OpenAI

            self._client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._config.model

    def generate(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
    ) -> LLMResponse:
        """Generate using OpenAI API."""
        start_time = time.time()

        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            api_messages.append(msg.to_dict())

        try:
            response = self._client.chat.completions.create(
                model=self._config.model,
                messages=api_messages,
                temperature=temperature or self._config.temperature,
                max_tokens=max_tokens or self._config.max_tokens,
                stop=stop_sequences,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=self._config.model,
                provider=self.provider_name,
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
                finish_reason=response.choices[0].finish_reason or "",
                latency_ms=latency_ms,
                request_id=response.id,
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return LLMResponse(
                content=f"Error: {str(e)}",
                model=self._config.model,
                provider=self.provider_name,
                latency_ms=latency_ms,
                finish_reason="error",
                metadata={"error": str(e)},
            )

    def generate_with_structured_output(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        output_schema: Dict[str, Any],
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Generate with JSON output."""
        schema_instruction = f"""
Respond with valid JSON matching this schema:
{json.dumps(output_schema, indent=2)}
"""
        enhanced_prompt = f"{system_prompt}\n\n{schema_instruction}"

        return self.generate(
            system_prompt=enhanced_prompt,
            messages=messages,
            temperature=temperature,
        )


class MockLLMClient(LLMClient):
    """
    Mock LLM client for testing.

    Returns predefined responses without making API calls.
    """

    def __init__(self, config: LLMConfig = None):
        self._config = config or LLMConfig.mock()
        self._responses: List[str] = []
        self._call_count = 0

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-model"

    def set_responses(self, responses: List[str]) -> None:
        """Set predefined responses."""
        self._responses = responses
        self._call_count = 0

    def generate(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
    ) -> LLMResponse:
        """Return mock response."""
        if self._responses and self._call_count < len(self._responses):
            content = self._responses[self._call_count]
            self._call_count += 1
        else:
            content = f"Mock response for: {messages[-1].content if messages else 'empty'}"

        return LLMResponse(
            content=content,
            model="mock-model",
            provider="mock",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            finish_reason="stop",
            latency_ms=10,
        )

    def generate_with_structured_output(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        output_schema: Dict[str, Any],
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Return mock JSON response."""
        return LLMResponse(
            content="{}",
            model="mock-model",
            provider="mock",
            finish_reason="stop",
            latency_ms=10,
        )

