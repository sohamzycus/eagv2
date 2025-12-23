"""
🐦 BirdSense - LLM Provider Factory
Developed by Soham

Factory pattern for multiple LLM backends:
- Ollama (Local)
- OpenAI (Public API)
- Azure OpenAI (Enterprise)
- LiteLLM (Unified proxy)
"""

import os
import requests
import base64
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from PIL import Image

# Suppress SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    api_key: str = ""
    api_base: str = ""
    vision_model: str = "gpt-4o"
    text_model: str = "gpt-4o"
    # Azure specific
    deployment: str = ""
    api_version: str = "2024-02-15-preview"


@dataclass  
class ProviderStatus:
    """Status of an LLM provider."""
    available: bool = False
    name: str = "Unknown"
    provider_type: str = "unknown"
    vision_model: str = ""
    text_model: str = ""
    error: str = ""


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self._available = False
        self._error = ""
    
    @property
    def available(self) -> bool:
        return self._available
    
    @property
    def error(self) -> str:
        return self._error
    
    @abstractmethod
    def check_connection(self) -> bool:
        """Check if the provider is accessible."""
        pass
    
    @abstractmethod
    def call_vision(self, image: Image.Image, prompt: str) -> str:
        """Call vision model with an image."""
        pass
    
    @abstractmethod
    def call_text(self, prompt: str) -> str:
        """Call text model with a prompt."""
        pass
    
    @abstractmethod
    def get_status(self) -> ProviderStatus:
        """Get provider status."""
        pass
    
    def _prepare_image(self, image: Image.Image, max_size: int = 800) -> str:
        """Prepare image as base64 for API call."""
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            image = image.resize(
                (int(image.size[0] * ratio), int(image.size[1] * ratio)),
                Image.Resampling.LANCZOS
            )
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode()


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.api_base or "http://localhost:11434"
        self.vision_model = config.vision_model or "llava:7b"
        self.text_model = config.text_model or "phi4:latest"
    
    def check_connection(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                has_vision = any("llava" in m.lower() for m in models)
                has_text = any(any(t in m.lower() for t in ["phi", "llama", "qwen"]) for m in models)
                self._available = has_vision or has_text
                if not self._available:
                    self._error = "No compatible models found"
                return self._available
        except Exception as e:
            self._error = f"Connection failed: {str(e)[:50]}"
        self._available = False
        return False
    
    def call_vision(self, image: Image.Image, prompt: str) -> str:
        if not self._available:
            return ""
        try:
            img_b64 = self._prepare_image(image)
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.vision_model,
                    "prompt": prompt,
                    "images": [img_b64],
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 1200}
                },
                timeout=120
            )
            if resp.status_code == 200:
                return resp.json().get("response", "")
        except Exception as e:
            print(f"Ollama vision error: {e}")
        return ""
    
    def call_text(self, prompt: str) -> str:
        if not self._available:
            return ""
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.text_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 800}
                },
                timeout=60
            )
            if resp.status_code == 200:
                return resp.json().get("response", "")
        except Exception as e:
            print(f"Ollama text error: {e}")
        return ""
    
    def get_status(self) -> ProviderStatus:
        return ProviderStatus(
            available=self._available,
            name="Ollama",
            provider_type="ollama",
            vision_model=self.vision_model,
            text_model=self.text_model,
            error=self._error
        )


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.api_base = config.api_base or "https://api.openai.com"
        self.vision_model = config.vision_model or "gpt-4o"
        self.text_model = config.text_model or "gpt-4o"
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def check_connection(self) -> bool:
        if not self.api_key:
            self._error = "API key not set"
            self._available = False
            return False
        
        try:
            resp = requests.post(
                f"{self.api_base}/v1/chat/completions",
                headers=self._get_headers(),
                json={
                    "model": self.text_model,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5
                },
                timeout=15,
                verify=False
            )
            if resp.status_code == 200:
                self._available = True
                self._error = ""
                return True
            else:
                error_data = resp.json().get("error", {})
                self._error = error_data.get("message", f"HTTP {resp.status_code}")[:100]
        except Exception as e:
            self._error = str(e)[:50]
        
        self._available = False
        return False
    
    def call_vision(self, image: Image.Image, prompt: str) -> str:
        if not self._available:
            return ""
        try:
            img_b64 = self._prepare_image(image)
            resp = requests.post(
                f"{self.api_base}/v1/chat/completions",
                headers=self._get_headers(),
                json={
                    "model": self.vision_model,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                        ]
                    }],
                    "max_tokens": 1200,
                    "temperature": 0.1
                },
                timeout=120,
                verify=False
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"OpenAI vision error: {e}")
        return ""
    
    def call_text(self, prompt: str) -> str:
        if not self._available:
            return ""
        try:
            resp = requests.post(
                f"{self.api_base}/v1/chat/completions",
                headers=self._get_headers(),
                json={
                    "model": self.text_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 800,
                    "temperature": 0.2
                },
                timeout=60,
                verify=False
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"OpenAI text error: {e}")
        return ""
    
    def get_status(self) -> ProviderStatus:
        return ProviderStatus(
            available=self._available,
            name="OpenAI",
            provider_type="openai",
            vision_model=self.vision_model,
            text_model=self.text_model,
            error=self._error
        )


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI API provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.endpoint = config.api_base
        self.deployment = config.deployment
        self.api_version = config.api_version or "2024-02-15-preview"
        self.model_name = config.vision_model or "gpt-4o"
    
    def _get_url(self) -> str:
        return f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def check_connection(self) -> bool:
        if not self.api_key or not self.endpoint or not self.deployment:
            self._error = "Missing API key, endpoint, or deployment"
            self._available = False
            return False
        
        try:
            resp = requests.post(
                self._get_url(),
                headers=self._get_headers(),
                json={
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5
                },
                timeout=15,
                verify=False
            )
            if resp.status_code == 200:
                self._available = True
                self._error = ""
                return True
            else:
                self._error = f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            self._error = str(e)[:50]
        
        self._available = False
        return False
    
    def call_vision(self, image: Image.Image, prompt: str) -> str:
        if not self._available:
            return ""
        try:
            img_b64 = self._prepare_image(image)
            resp = requests.post(
                self._get_url(),
                headers=self._get_headers(),
                json={
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                        ]
                    }],
                    "max_tokens": 1200,
                    "temperature": 0.1
                },
                timeout=120,
                verify=False
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Azure vision error: {e}")
        return ""
    
    def call_text(self, prompt: str) -> str:
        if not self._available:
            return ""
        try:
            resp = requests.post(
                self._get_url(),
                headers=self._get_headers(),
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 800,
                    "temperature": 0.2
                },
                timeout=60,
                verify=False
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Azure text error: {e}")
        return ""
    
    def get_status(self) -> ProviderStatus:
        return ProviderStatus(
            available=self._available,
            name="Azure OpenAI",
            provider_type="azure",
            vision_model=self.model_name,
            text_model=self.model_name,
            error=self._error
        )


class ProviderFactory:
    """
    Factory for creating and managing LLM providers.
    Supports automatic fallback between providers.
    """
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.active_provider: Optional[str] = None
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured providers from environment."""
        # Load from environment
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        # Ollama (Local)
        ollama_config = ProviderConfig(
            api_base=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
            vision_model="llava:7b",
            text_model="phi4:latest"
        )
        self.providers["ollama"] = OllamaProvider(ollama_config)
        
        # Check if Azure is configured
        is_azure = os.environ.get("IS_AZURE", "false").lower() == "true"
        azure_deployment = os.environ.get("AZURE_DEPLOYMENT", "")
        
        # API key - check multiple sources for flexibility
        api_key = os.environ.get("LITELLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
        
        if is_azure and azure_deployment:
            # Azure OpenAI
            azure_config = ProviderConfig(
                api_key=api_key,
                api_base=os.environ.get("LITELLM_API_BASE", ""),
                deployment=azure_deployment,
                api_version=os.environ.get("AZURE_API_VERSION", "2024-02-15-preview"),
                vision_model=os.environ.get("LITELLM_VISION_MODEL", "gpt-4o"),
                text_model=os.environ.get("LITELLM_TEXT_MODEL", "gpt-4o")
            )
            self.providers["cloud"] = AzureOpenAIProvider(azure_config)
        else:
            # OpenAI / LiteLLM
            openai_config = ProviderConfig(
                api_key=api_key,
                api_base=os.environ.get("LITELLM_API_BASE", "https://api.openai.com"),
                vision_model=os.environ.get("LITELLM_VISION_MODEL", "gpt-4o"),
                text_model=os.environ.get("LITELLM_TEXT_MODEL", "gpt-4o")
            )
            self.providers["cloud"] = OpenAIProvider(openai_config)
        
        # Check availability
        self._check_all_providers()
    
    def _check_all_providers(self):
        """Check all providers and set active."""
        for name, provider in self.providers.items():
            print(f"🔍 Checking {name}...")
            if provider.check_connection():
                print(f"✅ {name} available")
            else:
                print(f"⚠️ {name} not available: {provider.error}")
        
        # Set default active provider
        if self.providers.get("ollama", None) and self.providers["ollama"].available:
            self.active_provider = "ollama"
        elif self.providers.get("cloud", None) and self.providers["cloud"].available:
            self.active_provider = "cloud"
        else:
            self.active_provider = None
    
    def set_active(self, provider_name: str) -> bool:
        """Set the active provider."""
        if provider_name == "auto":
            # Auto-select best available
            if self.providers.get("ollama") and self.providers["ollama"].available:
                self.active_provider = "ollama"
            elif self.providers.get("cloud") and self.providers["cloud"].available:
                self.active_provider = "cloud"
            else:
                self.active_provider = None
            return self.active_provider is not None
        
        if provider_name in self.providers:
            if self.providers[provider_name].available:
                self.active_provider = provider_name
                return True
        return False
    
    def get_active(self) -> Optional[LLMProvider]:
        """Get the active provider."""
        if self.active_provider and self.active_provider in self.providers:
            return self.providers[self.active_provider]
        return None
    
    def call_vision(self, image: Image.Image, prompt: str) -> str:
        """Call vision model on active provider."""
        provider = self.get_active()
        if provider:
            return provider.call_vision(image, prompt)
        return ""
    
    def call_text(self, prompt: str) -> str:
        """Call text model on active provider."""
        provider = self.get_active()
        if provider:
            return provider.call_text(prompt)
        return ""
    
    def get_status_html(self) -> str:
        """Generate HTML status display."""
        ollama = self.providers.get("ollama")
        cloud = self.providers.get("cloud")
        active = self.get_active()
        
        ollama_status = "🟢" if ollama and ollama.available else "⚪"
        cloud_status = "🟢" if cloud and cloud.available else "⚪"
        
        if active:
            status = active.get_status()
            if status.provider_type == "ollama":
                bg_color, text_color, border_color = "#ecfdf5", "#065f46", "#a7f3d0"
                status_text = "🟢 Ollama (Local)"
            else:
                bg_color, text_color, border_color = "#f3e8ff", "#6b21a8", "#d8b4fe"
                status_text = f"🟣 {status.name}"
            
            vision_model = status.vision_model.split(":")[0] if ":" in status.vision_model else status.vision_model
            text_model = status.text_model.split(":")[0] if ":" in status.text_model else status.text_model
            error_html = ""
        else:
            bg_color, text_color, border_color = "#fef3c7", "#92400e", "#fcd34d"
            status_text = "⚠️ No Provider"
            vision_model = "⚠️"
            text_model = "⚠️"
            # Show error from cloud provider
            error_msg = cloud.error if cloud else "No providers configured"
            error_html = f'<div style="width:100%;margin-top:8px;padding:8px;background:#fef2f2;border-radius:6px;font-size:0.85em;color:#991b1b;">❌ {error_msg}</div>'
        
        return f"""<div style="
            font-family: -apple-system, system-ui, sans-serif;
            padding: 10px 16px;
            background: {bg_color};
            border-radius: 10px;
            border: 1px solid {border_color};
            color: {text_color};
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        ">
            <span style="font-weight: 600; padding: 4px 10px; border-radius: 6px;">{status_text}</span>
            <span>Vision: <b>{vision_model}</b></span>
            <span>Text: <b>{text_model}</b></span>
            <span style="opacity: 0.7; font-size: 0.85em; margin-left: auto;">
                Ollama: {ollama_status} | Cloud: {cloud_status}
            </span>
            {error_html}
        </div>"""
    
    def get_model_info(self, task: str) -> Dict[str, str]:
        """Get info about the model being used for a task."""
        active = self.get_active()
        if active:
            status = active.get_status()
            if task == "vision":
                return {"name": status.vision_model, "provider": status.name}
            else:
                return {"name": status.text_model, "provider": status.name}
        return {"name": "Not Available", "provider": "None"}


# Global factory instance
provider_factory = ProviderFactory()

