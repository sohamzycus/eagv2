"""
Ollama Client - Integration with local Ollama models.

Uses phi4 for generation and nomic-embed-text for embeddings.
Uses built-in urllib (no external dependencies).
"""

import asyncio
import json
import urllib.request
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class OllamaConfig:
    """Ollama configuration."""
    base_url: str = "http://localhost:11434"
    model: str = "phi4"
    embedding_model: str = "nomic-embed-text"
    timeout: int = 120


class OllamaClient:
    """
    Async client for Ollama API.
    
    Uses urllib for compatibility (no external deps).
    """
    
    def __init__(self, config: OllamaConfig = None):
        self.config = config or OllamaConfig()
    
    def _post(self, endpoint: str, data: dict) -> dict:
        """Synchronous POST request."""
        url = f"{self.config.base_url}{endpoint}"
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {"error": str(e)}
    
    async def generate(
        self, 
        prompt: str, 
        system: str = None,
        temperature: float = 0.3,
        max_tokens: int = 2048
    ) -> str:
        """
        Generate text using phi4.
        
        Args:
            prompt: User prompt
            system: System prompt
            temperature: Creativity (0-1)
            max_tokens: Max tokens to generate
        
        Returns:
            Generated text
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        # Run sync request in thread pool to not block
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: self._post("/api/chat", payload)
        )
        
        if "error" in result:
            return f"[LLM Error: {result['error']}]"
        
        return result.get("message", {}).get("content", "")
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding using nomic-embed-text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        payload = {
            "model": self.config.embedding_model,
            "prompt": text
        }
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._post("/api/embeddings", payload)
        )
        
        if "error" in result:
            return []
        
        return result.get("embedding", [])
    
    async def close(self):
        """Close client (no-op for urllib)."""
        pass


# Global client instance
_ollama_client: Optional[OllamaClient] = None


async def get_ollama() -> OllamaClient:
    """Get global Ollama client."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


async def generate(prompt: str, system: str = None) -> str:
    """Convenience function for text generation."""
    client = await get_ollama()
    return await client.generate(prompt, system)


async def embed(text: str) -> List[float]:
    """Convenience function for embeddings."""
    client = await get_ollama()
    return await client.embed(text)
