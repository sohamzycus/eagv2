"""
LLM Provider implementations using Abstract Factory Pattern.

Supports:
- Ollama (for local models: llama3.2, phi4, mistral, etc.)
"""

import json
import re
from typing import Any, Dict, Optional
import httpx

from core.interfaces import LLMProvider
from core.events import Event, EventType, EventDispatcher


class OllamaProvider(LLMProvider):
    """
    Concrete LLM Provider for Ollama local models.
    
    Supports models like:
    - llama3.2
    - phi4
    - mistral
    - codellama
    - qwen2.5
    """
    
    def __init__(
        self, 
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        timeout: float = 120.0
    ):
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.timeout = timeout
        self.dispatcher = EventDispatcher()
    
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a response from the local LLM."""
        self.dispatcher.dispatch(Event(
            event_type=EventType.LLM_PROMPT_SENT,
            message=f"Sending prompt to {self.model}",
            data={"model": self.model, "prompt_length": len(prompt)}
        ))
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": self.temperature
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                content = result.get("message", {}).get("content", "")
                
                self.dispatcher.dispatch(Event(
                    event_type=EventType.LLM_RESPONSE_RECEIVED,
                    message=f"Received response from {self.model}",
                    data={"response_length": len(content)}
                ))
                
                return content
                
        except Exception as e:
            self.dispatcher.dispatch(Event(
                event_type=EventType.LLM_ERROR,
                message=f"LLM error: {str(e)}",
                data={"error": str(e)}
            ))
            raise
    
    async def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Generate a JSON response from the LLM."""
        # Add JSON instruction to system prompt
        json_system = system_prompt + "\n\nYou MUST respond with valid JSON only. No markdown, no explanations."
        
        response = await self.generate(prompt, json_system)
        
        # Try to extract JSON from response
        try:
            # First, try direct parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # Try to find JSON array
            array_match = re.search(r'\[[\s\S]*\]', response)
            if array_match:
                try:
                    return {"items": json.loads(array_match.group())}
                except json.JSONDecodeError:
                    pass
        
        # Return wrapped response if JSON parsing fails
        return {"raw_response": response}
    
    def get_model_name(self) -> str:
        """Return the model name being used."""
        return self.model
    
    async def is_available(self) -> bool:
        """Check if Ollama is available and model is loaded."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [m.get("name", "").split(":")[0] for m in models]
                    return self.model.split(":")[0] in model_names
                return False
        except Exception:
            return False


class LLMProviderFactory:
    """
    Abstract Factory for creating LLM providers.
    
    Usage:
        factory = LLMProviderFactory()
        provider = factory.create_provider("ollama", model="llama3.2")
    """
    
    _providers = {
        "ollama": OllamaProvider,
    }
    
    @classmethod
    def create_provider(
        cls, 
        provider_type: str, 
        **kwargs
    ) -> LLMProvider:
        """Create an LLM provider instance."""
        if provider_type not in cls._providers:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        return cls._providers[provider_type](**kwargs)
    
    @classmethod
    def register_provider(
        cls, 
        name: str, 
        provider_class: type
    ) -> None:
        """Register a new provider type."""
        cls._providers[name] = provider_class
    
    @classmethod
    def list_providers(cls) -> list:
        """List available provider types."""
        return list(cls._providers.keys())



