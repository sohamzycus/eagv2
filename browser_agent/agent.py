"""
Browser Agent - Main orchestrator for automated form filling.

This agent uses local LLMs (via Ollama) to intelligently fill web forms.

Design Patterns Used:
- Abstract Factory: LLM provider creation
- Strategy: Form filling strategies
- Observer: Event logging and monitoring
- Template Method: Browser actions
- Factory: Browser and agent component creation

Usage:
    agent = BrowserAgent(config)
    await agent.fill_form("https://forms.gle/...")
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.interfaces import LLMProvider, FormFillerStrategy
from core.events import Event, EventType, EventDispatcher
from browser.controller import BrowserController
from llm.providers import LLMProviderFactory, OllamaProvider
from llm.prompt_manager import PromptManager
from form_filler.google_forms import GoogleFormsFiller
from strategies.llm_strategy import LLMGuidedStrategy
from strategies.rule_strategy import RuleBasedStrategy
from strategies.hybrid_strategy import HybridStrategy
from utils.observers import ConsoleLogger, FileLogger
from utils.config import Config


class BrowserAgent:
    """
    Main Browser Agent class.
    
    Orchestrates browser automation, LLM interaction, and form filling
    to automatically complete web forms.
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_env()
        self.dispatcher = EventDispatcher()
        
        # Setup observers
        self._setup_observers()
        
        # Initialize components (lazy loaded)
        self._llm_provider: Optional[LLMProvider] = None
        self._strategy: Optional[FormFillerStrategy] = None
        self._browser: Optional[BrowserController] = None
        self._prompt_manager: Optional[PromptManager] = None
    
    def _setup_observers(self) -> None:
        """Setup event observers."""
        # Console logger for real-time output
        self.console_logger = ConsoleLogger(verbose=self.config.agent.verbose)
        self.dispatcher.attach(self.console_logger)
        
        # File logger for persistence
        self.file_logger = FileLogger(log_file=self.config.agent.log_file)
        self.dispatcher.attach(self.file_logger)
    
    @property
    def llm_provider(self) -> LLMProvider:
        """Lazy-load LLM provider."""
        if self._llm_provider is None:
            self._llm_provider = LLMProviderFactory.create_provider(
                self.config.llm.provider,
                model=self.config.llm.model,
                base_url=self.config.llm.base_url,
                temperature=self.config.llm.temperature,
                timeout=self.config.llm.timeout
            )
        return self._llm_provider
    
    @property
    def strategy(self) -> FormFillerStrategy:
        """Lazy-load form filling strategy."""
        if self._strategy is None:
            user_context = self.config.get_user_context()
            
            if self.config.agent.strategy == "llm":
                self._strategy = LLMGuidedStrategy(
                    self.llm_provider,
                    user_context=user_context
                )
            elif self.config.agent.strategy == "rule":
                self._strategy = RuleBasedStrategy(user_data=user_context)
            else:  # hybrid (default)
                self._strategy = HybridStrategy(
                    self.llm_provider,
                    user_data=user_context
                )
        return self._strategy
    
    async def check_llm_available(self) -> bool:
        """Check if the LLM is available."""
        try:
            return await self.llm_provider.is_available()
        except Exception as e:
            self.dispatcher.dispatch(Event(
                event_type=EventType.LLM_ERROR,
                message=f"LLM not available: {str(e)}",
                data={"error": str(e)}
            ))
            return False
    
    async def fill_form(
        self, 
        url: str,
        context: Optional[Dict[str, Any]] = None,
        auto_submit: bool = True
    ) -> bool:
        """
        Fill a form at the given URL.
        
        Args:
            url: The URL of the form to fill
            context: Additional context for form filling
            auto_submit: Whether to submit the form after filling
            
        Returns:
            True if form was successfully filled (and submitted if requested)
        """
        context = context or {}
        context.update(self.config.get_user_context())
        
        self.dispatcher.dispatch(Event(
            event_type=EventType.AGENT_STARTED,
            message=f"Starting form fill: {url}",
            data={"url": url, "auto_submit": auto_submit}
        ))
        
        # Check LLM availability
        if self.config.agent.strategy in ["llm", "hybrid"]:
            llm_available = await self.check_llm_available()
            if not llm_available:
                print(f"\n⚠️  Warning: LLM ({self.config.llm.model}) not available.")
                print("Make sure Ollama is running: ollama serve")
                print(f"And the model is installed: ollama pull {self.config.llm.model}\n")
                
                if self.config.agent.strategy == "llm":
                    return False
                
                # Fall back to rule-based for hybrid
                print("Falling back to rule-based strategy...\n")
                self._strategy = RuleBasedStrategy(
                    user_data=self.config.get_user_context()
                )
        
        async with BrowserController(
            headless=self.config.browser.headless,
            slow_mo=self.config.browser.slow_mo,
            screenshots_dir=self.config.browser.screenshots_dir,
            viewport={
                "width": self.config.browser.viewport_width,
                "height": self.config.browser.viewport_height
            }
        ) as browser:
            
            # Navigate to URL
            result = await browser.navigate(url)
            if not result.is_success:
                self.dispatcher.dispatch(Event(
                    event_type=EventType.AGENT_ERROR,
                    message=f"Failed to navigate: {result.message}"
                ))
                return False
            
            # Take initial screenshot
            await browser.screenshot("01_initial")
            
            # Create Google Forms filler
            filler = GoogleFormsFiller(self.strategy)
            
            # Detect if it's a Google Form
            is_google_form = await filler.detect_form(browser.page)
            if not is_google_form:
                self.dispatcher.dispatch(Event(
                    event_type=EventType.AGENT_ERROR,
                    message="Not a Google Form or form not detected"
                ))
                return False
            
            # Extract questions
            questions = await filler.extract_questions(browser.page)
            if not questions:
                self.dispatcher.dispatch(Event(
                    event_type=EventType.AGENT_ERROR,
                    message="No questions found in form"
                ))
                return False
            
            print(f"\n📋 Found {len(questions)} questions:\n")
            for q in questions:
                req = " (required)" if q.required else ""
                opts = f" [{len(q.options)} options]" if q.options else ""
                print(f"  • {q.title}{req}{opts}")
            print()
            
            # Take screenshot after extraction
            await browser.screenshot("02_questions_extracted")
            
            # Fill all questions
            results = await filler.fill_all(browser.page, context)
            
            # Check results
            success_count = sum(1 for r in results if r.is_success)
            print(f"\n✅ Filled {success_count}/{len(results)} questions\n")
            
            # Take screenshot after filling
            await browser.screenshot("03_form_filled")
            
            # Submit if requested
            if auto_submit:
                print("📤 Submitting form...")
                submit_result = await filler.submit(browser.page)
                
                if submit_result.is_success:
                    print("✅ Form submitted successfully!\n")
                    await asyncio.sleep(2)
                    await browser.screenshot("04_submitted")
                else:
                    print(f"❌ Submit failed: {submit_result.message}\n")
                    await browser.screenshot("04_submit_error")
                    
                    self.dispatcher.dispatch(Event(
                        event_type=EventType.AGENT_COMPLETED,
                        message="Form filled but submission may have failed",
                        data={"success_count": success_count, "submitted": False}
                    ))
                    return False
            
            self.dispatcher.dispatch(Event(
                event_type=EventType.AGENT_COMPLETED,
                message="Form filling completed",
                data={"success_count": success_count, "submitted": auto_submit}
            ))
            
            return True
    
    async def run(self, url: str, **kwargs) -> bool:
        """Alias for fill_form for convenience."""
        return await self.fill_form(url, **kwargs)


async def main():
    """Main entry point for the browser agent."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Browser Agent - Automated Form Filler using Local LLM"
    )
    parser.add_argument(
        "url",
        help="URL of the form to fill"
    )
    parser.add_argument(
        "--model", "-m",
        default="llama3.2",
        help="LLM model to use (default: llama3.2)"
    )
    parser.add_argument(
        "--strategy", "-s",
        choices=["llm", "rule", "hybrid"],
        default="hybrid",
        help="Form filling strategy (default: hybrid)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--no-submit",
        action="store_true",
        help="Don't submit the form after filling"
    )
    parser.add_argument(
        "--name",
        default="Soham Niyogi",
        help="Name to use for form fields"
    )
    parser.add_argument(
        "--email",
        default="sohamniyogi9@gmail.com",
        help="Email to use for form fields"
    )
    parser.add_argument(
        "--github-url",
        default="",
        help="GitHub URL for form fields"
    )
    parser.add_argument(
        "--youtube-url",
        default="",
        help="YouTube URL for form fields"
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to YAML configuration file"
    )
    
    args = parser.parse_args()
    
    # Build configuration
    if args.config:
        config = Config.from_yaml(args.config)
    else:
        config = Config()
    
    # Override with command line arguments
    config.llm.model = args.model
    config.agent.strategy = args.strategy
    config.browser.headless = args.headless
    config.agent.user_name = args.name
    config.agent.user_email = args.email
    config.agent.github_url = args.github_url
    config.agent.youtube_url = args.youtube_url
    
    # Print banner
    print("\n" + "="*60)
    print("🤖 Browser Agent - Automated Form Filler")
    print("="*60)
    print(f"Model: {config.llm.model}")
    print(f"Strategy: {config.agent.strategy}")
    print(f"URL: {args.url}")
    print("="*60 + "\n")
    
    # Create and run agent
    agent = BrowserAgent(config)
    success = await agent.fill_form(
        args.url,
        auto_submit=not args.no_submit
    )
    
    if success:
        print("\n🎉 Task completed successfully!")
    else:
        print("\n❌ Task failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())





