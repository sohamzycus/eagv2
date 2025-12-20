"""
Ollama Client for BirdSense.

Provides interface to local LLM models via Ollama for:
- Species reasoning and verification
- Description matching
- Natural language queries about birds
"""

import httpx
import json
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass
import asyncio


@dataclass
class OllamaConfig:
    """Configuration for Ollama client."""
    base_url: str = "http://localhost:11434"
    model: str = "phi3:mini"  # Lightweight model for edge deployment
    temperature: float = 0.3
    max_tokens: int = 512
    timeout: int = 30
    stream: bool = False


class OllamaClient:
    """
    Async client for Ollama API.
    
    Supports:
    - Text generation
    - Streaming responses
    - Model listing and management
    """
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=httpx.Timeout(self.config.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout)
            )
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Generate text completion.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Sampling temperature (default from config)
            max_tokens: Max tokens to generate
            model: Model to use (default from config)
            
        Returns:
            Generated text response
        """
        payload = {
            "model": model or self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except httpx.HTTPError as e:
            raise ConnectionError(f"Failed to connect to Ollama: {e}")
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream text generation.
        
        Yields:
            Chunks of generated text
        """
        payload = {
            "model": model or self.config.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        async with self.client.stream("POST", "/api/generate", json=payload) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
                    if data.get("done", False):
                        break
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None
    ) -> str:
        """
        Chat completion with message history.
        
        Args:
            messages: List of {"role": "user/assistant/system", "content": "..."}
            model: Model to use
            
        Returns:
            Assistant response
        """
        payload = {
            "model": model or self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }
        
        try:
            response = await self.client.post("/api/chat", json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            raise ConnectionError(f"Failed to connect to Ollama: {e}")
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            return response.json().get("models", [])
        except httpx.HTTPError as e:
            raise ConnectionError(f"Failed to list models: {e}")
    
    async def is_model_available(self, model: Optional[str] = None) -> bool:
        """Check if specified model is available."""
        model = model or self.config.model
        try:
            models = await self.list_models()
            return any(m.get("name", "").startswith(model.split(":")[0]) for m in models)
        except Exception:
            return False
    
    async def health_check(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False


class SyncOllamaClient:
    """
    Synchronous wrapper for OllamaClient.
    
    Convenience class for non-async code paths.
    """
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self._async_client = OllamaClient(config)
    
    def _run(self, coro):
        """Run async coroutine synchronously."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, use nest_asyncio pattern
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(coro)
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop exists
            return asyncio.run(coro)
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> str:
        """Generate text completion synchronously."""
        return self._run(
            self._async_client.generate(
                prompt, system_prompt, temperature, max_tokens, model
            )
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None
    ) -> str:
        """Chat completion synchronously."""
        return self._run(self._async_client.chat(messages, model))
    
    def health_check(self) -> bool:
        """Check Ollama health synchronously."""
        return self._run(self._async_client.health_check())
    
    def is_model_available(self, model: Optional[str] = None) -> bool:
        """Check model availability synchronously."""
        return self._run(self._async_client.is_model_available(model))

