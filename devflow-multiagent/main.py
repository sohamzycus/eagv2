#!/usr/bin/env python3
"""
DevFlow - Multi-Agent Developer Productivity System

A novel multi-agent architecture for accelerating developer workflows.

Usage:
    python main.py

Author: Soham Niyogi
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ==================== ANSI Colors ====================

class Colors:
    """ANSI color codes for terminal output."""
    # Base colors
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright foreground
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"


def print_header():
    """Print DevFlow header."""
    header = f"""
{Colors.BRIGHT_CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║    ██████╗ ███████╗██╗   ██╗███████╗██╗      ██████╗ ██╗    ██╗               ║
║    ██╔══██╗██╔════╝██║   ██║██╔════╝██║     ██╔═══██╗██║    ██║               ║
║    ██║  ██║█████╗  ██║   ██║█████╗  ██║     ██║   ██║██║ █╗ ██║               ║
║    ██║  ██║██╔══╝  ╚██╗ ██╔╝██╔══╝  ██║     ██║   ██║██║███╗██║               ║
║    ██████╔╝███████╗ ╚████╔╝ ██║     ███████╗╚██████╔╝╚███╔███╔╝               ║
║    ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝                ║
║                                                                               ║
║              {Colors.BRIGHT_YELLOW}🚀 Multi-Agent Developer Productivity System 🚀{Colors.BRIGHT_CYAN}               ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}"""
    print(header)


def print_stage(stage: str, message: str, icon: str = "▶"):
    """Print a pipeline stage."""
    print(f"\n{Colors.BRIGHT_BLUE}{Colors.BOLD}{icon} {stage}{Colors.RESET} {Colors.DIM}│{Colors.RESET} {message}")


def print_agent_action(agent: str, action: str, color: str = Colors.CYAN):
    """Print agent action."""
    print(f"  {color}├─ {agent}:{Colors.RESET} {action}")


def print_success(message: str):
    """Print success message."""
    print(f"\n{Colors.BRIGHT_GREEN}{Colors.BOLD}✅ SUCCESS{Colors.RESET} {message}")


def print_error(message: str):
    """Print error message."""
    print(f"\n{Colors.BRIGHT_RED}{Colors.BOLD}❌ ERROR{Colors.RESET} {message}")


def print_response(response: str):
    """Print formatted response."""
    print(f"\n{Colors.BRIGHT_WHITE}{Colors.BOLD}{'─' * 80}{Colors.RESET}")
    print(f"{Colors.BRIGHT_GREEN}📋 Response:{Colors.RESET}")
    print(f"{Colors.WHITE}{response}{Colors.RESET}")
    print(f"{Colors.BRIGHT_WHITE}{Colors.BOLD}{'─' * 80}{Colors.RESET}")


def print_metrics(metrics: dict):
    """Print execution metrics."""
    print(f"\n{Colors.DIM}{'─' * 40}")
    print(f"⏱️  Execution: {metrics.get('execution_time_ms', 0)}ms")
    print(f"📊 Confidence: {metrics.get('confidence', 0):.0%}")
    print(f"🔄 Pipeline stages: {metrics.get('stages', 0)}")
    print(f"{'─' * 40}{Colors.RESET}")


def print_help():
    """Print help message."""
    help_text = f"""
{Colors.BRIGHT_YELLOW}{Colors.BOLD}📖 Available Commands:{Colors.RESET}

{Colors.CYAN}Developer Queries:{Colors.RESET}
  • "What did I work on yesterday?"    → {Colors.DIM}Standup summary{Colors.RESET}
  • "Generate PR description"          → {Colors.DIM}PR template{Colors.RESET}
  • "Review code in src/api.py"        → {Colors.DIM}Code review{Colors.RESET}
  • "Find tech debt in the project"    → {Colors.DIM}Tech debt analysis{Colors.RESET}
  • "Check my dependencies"            → {Colors.DIM}Security check{Colors.RESET}
  • "Document src/utils.py"            → {Colors.DIM}Documentation{Colors.RESET}

{Colors.CYAN}System Commands:{Colors.RESET}
  • help      → Show this message
  • metrics   → Show agent metrics
  • clear     → Clear screen
  • exit      → Exit DevFlow

{Colors.DIM}Tip: Just type your question naturally!{Colors.RESET}
"""
    print(help_text)


class DevFlowCLI:
    """
    Command-line interface for DevFlow.
    
    Provides an interactive, colorful experience for
    developer productivity workflows.
    """
    
    def __init__(self):
        self.orchestrator = None
        self.running = True
        self.query_count = 0
    
    async def initialize(self):
        """Initialize the orchestrator."""
        print_stage("INIT", "Initializing DevFlow agents...", "⚡")
        
        from coordinator import Orchestrator
        
        self.orchestrator = Orchestrator()
        
        print_agent_action("Perception", "Ready", Colors.GREEN)
        print_agent_action("Retriever", "Ready", Colors.GREEN)
        print_agent_action("Critic", "Ready", Colors.GREEN)
        print_agent_action("Memory", "Ready", Colors.GREEN)
        print_agent_action("Decision", "Ready", Colors.GREEN)
        
        print_success("All agents initialized!")
    
    async def process_query(self, query: str) -> Optional[dict]:
        """Process a user query through the pipeline."""
        self.query_count += 1
        
        print_stage("PERCEPTION", "Understanding query...", "🧠")
        print_agent_action("Perception", "Classifying intent", Colors.CYAN)
        
        print_stage("RETRIEVAL", "Gathering context...", "🔍")
        print_agent_action("Retriever", "Fetching relevant data", Colors.CYAN)
        print_agent_action("Memory", "Checking history", Colors.CYAN)
        
        print_stage("PLANNING", "Creating execution plan...", "📋")
        print_agent_action("Planner", "Generating steps", Colors.CYAN)
        
        print_stage("EXECUTION", "Running plan...", "⚙️")
        
        # Actually run the orchestrator
        result = await self.orchestrator.process_query(query)
        
        if result.get("success"):
            print_stage("CRITIQUE", "Validating output...", "🔎")
            print_agent_action("Critic", "Quality check passed", Colors.GREEN)
            
            print_stage("DECISION", "Generating response...", "🎯")
            print_agent_action("Decision", "Synthesizing final output", Colors.GREEN)
        
        return result
    
    async def run(self):
        """Main CLI loop."""
        print_header()
        
        await self.initialize()
        
        print(f"\n{Colors.BRIGHT_YELLOW}Type 'help' for available commands or just ask a question!{Colors.RESET}\n")
        
        while self.running:
            try:
                # Prompt
                prompt = f"{Colors.BRIGHT_MAGENTA}🧑 DevFlow ▸{Colors.RESET} "
                query = input(prompt).strip()
                
                if not query:
                    continue
                
                # Handle system commands
                if query.lower() == "exit":
                    print(f"\n{Colors.BRIGHT_CYAN}👋 Thanks for using DevFlow! Happy coding!{Colors.RESET}\n")
                    self.running = False
                    break
                
                elif query.lower() == "help":
                    print_help()
                    continue
                
                elif query.lower() == "clear":
                    os.system("clear" if os.name != "nt" else "cls")
                    print_header()
                    continue
                
                elif query.lower() == "metrics":
                    metrics = self.orchestrator.get_agent_metrics()
                    print(f"\n{Colors.BRIGHT_CYAN}📊 Agent Metrics:{Colors.RESET}")
                    for agent, data in metrics.items():
                        print(f"  {Colors.CYAN}{agent}:{Colors.RESET}")
                        for key, value in data.items():
                            print(f"    • {key}: {value}")
                    continue
                
                # Process developer query
                start_time = datetime.now()
                
                result = await self.process_query(query)
                
                elapsed = (datetime.now() - start_time).total_seconds() * 1000
                
                if result.get("success"):
                    print_response(result.get("response", "No response generated"))
                    
                    # Show followups
                    followups = result.get("followups", [])
                    if followups:
                        print(f"\n{Colors.BRIGHT_YELLOW}💡 Suggested follow-ups:{Colors.RESET}")
                        for f in followups:
                            print(f"   • {Colors.DIM}{f}{Colors.RESET}")
                    
                    print_metrics({
                        "execution_time_ms": int(elapsed),
                        "confidence": result.get("confidence", 0),
                        "stages": len(result.get("pipeline", {}).get("history", []))
                    })
                else:
                    print_error(result.get("error", "Unknown error"))
                
            except KeyboardInterrupt:
                print(f"\n\n{Colors.BRIGHT_CYAN}👋 Interrupted. Goodbye!{Colors.RESET}\n")
                break
            except Exception as e:
                print_error(str(e))


async def main():
    """Entry point."""
    cli = DevFlowCLI()
    await cli.run()


if __name__ == "__main__":
    asyncio.run(main())

