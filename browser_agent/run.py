#!/usr/bin/env python3
"""
Quick-start script for the Browser Agent.

This script fills the assignment Google Form using a local LLM.

Usage:
    python run.py --github-url "YOUR_GITHUB_URL" --youtube-url "YOUR_YOUTUBE_URL"
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agent import BrowserAgent
from utils.config import Config


# The Google Form URL from the assignment
FORM_URL = "https://forms.gle/6Nc6QaaJyDvePxLv7"


async def run_agent(github_url: str, youtube_url: str, model: str = "llama3.2"):
    """Run the browser agent to fill the form."""
    
    print("\n" + "="*70)
    print("🤖 Browser Agent - Assignment Form Filler")
    print("="*70)
    print(f"📝 Form URL: {FORM_URL}")
    print(f"🧠 Model: {model}")
    print(f"📎 GitHub URL: {github_url}")
    print(f"📺 YouTube URL: {youtube_url}")
    print("="*70 + "\n")
    
    # Create configuration
    config = Config()
    config.llm.model = model
    config.agent.strategy = "hybrid"
    config.agent.github_url = github_url
    config.agent.youtube_url = youtube_url
    config.browser.headless = False  # Show browser for demo
    config.browser.slow_mo = 150     # Slow down for visibility
    
    # Create and run agent
    agent = BrowserAgent(config)
    
    # Add context for form filling
    context = {
        "assignment": "EAG v2 Browser Agent Assignment",
        "github_url": github_url,
        "youtube_url": youtube_url,
    }
    
    success = await agent.fill_form(FORM_URL, context=context, auto_submit=True)
    
    if success:
        print("\n" + "="*70)
        print("🎉 SUCCESS! Form has been filled and submitted!")
        print("="*70)
        print("\n📸 Screenshots saved in 'screenshots/' directory")
        print("📋 Logs saved to 'agent_log.json'")
        print("\nYou can now check the form submission confirmation.")
    else:
        print("\n" + "="*70)
        print("❌ FAILED! Check the logs for details.")
        print("="*70)
    
    return success


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Browser Agent - Fill the Assignment Google Form",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Using llama3.2 (default)
    python run.py --github-url "https://github.com/user/repo" --youtube-url "https://youtube.com/..."

    # Using phi4
    python run.py --model phi4 --github-url "..." --youtube-url "..."

    # Using mistral
    python run.py --model mistral --github-url "..." --youtube-url "..."
        """
    )
    
    parser.add_argument(
        "--github-url", "-g",
        required=True,
        help="GitHub URL for the browser agent code"
    )
    parser.add_argument(
        "--youtube-url", "-y", 
        required=True,
        help="YouTube URL showing the agent in action"
    )
    parser.add_argument(
        "--model", "-m",
        default="llama3.2",
        help="Ollama model to use (default: llama3.2)"
    )
    parser.add_argument(
        "--no-submit",
        action="store_true",
        help="Fill form but don't submit"
    )
    
    args = parser.parse_args()
    
    # Validate URLs
    if not args.github_url.startswith("http"):
        print("❌ Error: GitHub URL must start with http:// or https://")
        sys.exit(1)
    
    if not args.youtube_url.startswith("http"):
        print("❌ Error: YouTube URL must start with http:// or https://")
        sys.exit(1)
    
    # Run the agent
    success = asyncio.run(run_agent(
        github_url=args.github_url,
        youtube_url=args.youtube_url,
        model=args.model
    ))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

