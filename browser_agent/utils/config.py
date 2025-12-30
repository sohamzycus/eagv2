"""
Configuration management for the Browser Agent.
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str = "ollama"
    model: str = "llama3.2"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.7
    timeout: float = 120.0


@dataclass
class BrowserConfig:
    """Browser configuration."""
    headless: bool = False
    slow_mo: int = 100
    viewport_width: int = 1280
    viewport_height: int = 800
    screenshots_dir: str = "screenshots"


@dataclass
class AgentConfig:
    """Agent configuration."""
    strategy: str = "hybrid"  # llm, rule, hybrid
    user_name: str = "Soham Niyogi"
    user_email: str = "sohamniyogi9@gmail.com"
    github_url: str = ""
    youtube_url: str = ""
    verbose: bool = True
    log_file: str = "agent_log.json"


@dataclass
class Config:
    """Main configuration container."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    
    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """Load configuration from YAML file."""
        config_path = Path(path)
        if not config_path.exists():
            return cls()
        
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        
        return cls(
            llm=LLMConfig(**data.get("llm", {})),
            browser=BrowserConfig(**data.get("browser", {})),
            agent=AgentConfig(**data.get("agent", {}))
        )
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            llm=LLMConfig(
                provider=os.getenv("LLM_PROVIDER", "ollama"),
                model=os.getenv("LLM_MODEL", "llama3.2"),
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            ),
            browser=BrowserConfig(
                headless=os.getenv("BROWSER_HEADLESS", "false").lower() == "true",
                slow_mo=int(os.getenv("BROWSER_SLOW_MO", "100")),
            ),
            agent=AgentConfig(
                strategy=os.getenv("AGENT_STRATEGY", "hybrid"),
                user_name=os.getenv("USER_NAME", "Soham Niyogi"),
                user_email=os.getenv("USER_EMAIL", "sohamniyogi9@gmail.com"),
                github_url=os.getenv("GITHUB_URL", ""),
                youtube_url=os.getenv("YOUTUBE_URL", ""),
            )
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "base_url": self.llm.base_url,
                "temperature": self.llm.temperature,
            },
            "browser": {
                "headless": self.browser.headless,
                "slow_mo": self.browser.slow_mo,
                "viewport_width": self.browser.viewport_width,
                "viewport_height": self.browser.viewport_height,
            },
            "agent": {
                "strategy": self.agent.strategy,
                "user_name": self.agent.user_name,
                "user_email": self.agent.user_email,
            }
        }
    
    def get_user_context(self) -> Dict[str, str]:
        """Get user context for form filling."""
        return {
            "name": self.agent.user_name,
            "email": self.agent.user_email,
            "github_url": self.agent.github_url,
            "youtube_url": self.agent.youtube_url,
        }





