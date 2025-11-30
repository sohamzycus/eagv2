#!/usr/bin/env python3
"""
Demo Run - Execute 3 example queries with colorful output.

This script demonstrates DevFlow's capabilities.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ANSI Colors
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_MAGENTA = "\033[95m"


def print_banner():
    """Print demo banner."""
    print(f"""
{C.BRIGHT_CYAN}{C.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    🚀 DevFlow Demo - 3 Example Queries 🚀                    ║
║                                                                              ║
║                Multi-Agent Developer Productivity System                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.RESET}
""")


def print_query_header(num: int, query: str, intent: str):
    """Print query header."""
    print(f"""
{C.BRIGHT_MAGENTA}{C.BOLD}{'═' * 80}{C.RESET}
{C.BRIGHT_YELLOW}{C.BOLD}📝 QUERY {num}:{C.RESET} {C.WHITE}{query}{C.RESET}
{C.CYAN}Intent: {intent}{C.RESET}
{C.BRIGHT_MAGENTA}{C.BOLD}{'═' * 80}{C.RESET}
""")


def print_pipeline_step(stage: str, agent: str, action: str, color=C.CYAN):
    """Print pipeline step."""
    print(f"  {color}▶ {stage}{C.RESET} │ {C.DIM}{agent}:{C.RESET} {action}")


def print_result(response: str, metrics: dict):
    """Print result."""
    print(f"""
{C.BRIGHT_GREEN}{C.BOLD}{'─' * 80}{C.RESET}
{C.BRIGHT_GREEN}📋 RESULT:{C.RESET}
{C.WHITE}{response}{C.RESET}
{C.BRIGHT_GREEN}{C.BOLD}{'─' * 80}{C.RESET}

{C.DIM}⏱️  Time: {metrics.get('time_ms', 0)}ms │ 📊 Confidence: {metrics.get('confidence', 0):.0%} │ 🔄 Stages: {metrics.get('stages', 0)}{C.RESET}
""")


async def run_demo():
    """Run the demo."""
    print_banner()
    
    from coordinator import Orchestrator
    
    print(f"{C.YELLOW}⚡ Initializing DevFlow agents...{C.RESET}")
    orchestrator = Orchestrator()
    print(f"{C.GREEN}✅ All agents ready!{C.RESET}\n")
    
    # Define 3 demo queries
    queries = [
        {
            "query": "What did I work on yesterday?",
            "intent": "standup_summary",
            "description": "Generate standup summary from git commits"
        },
        {
            "query": "Generate PR description for my changes",
            "intent": "pr_description", 
            "description": "Create pull request template"
        },
        {
            "query": "Find technical debt in the project",
            "intent": "tech_debt",
            "description": "Analyze codebase for tech debt"
        }
    ]
    
    for i, q in enumerate(queries, 1):
        print_query_header(i, q["query"], q["intent"])
        
        # Show pipeline steps
        print(f"{C.CYAN}Pipeline Execution:{C.RESET}")
        print_pipeline_step("PERCEPTION", "🧠 Perception", "Classifying intent...", C.BLUE)
        print_pipeline_step("RETRIEVAL", "🔍 Retriever", "Gathering context...", C.BLUE)
        print_pipeline_step("MEMORY", "💾 Memory", "Checking history...", C.BLUE)
        print_pipeline_step("PLANNING", "📋 Planner", "Creating plan...", C.YELLOW)
        print_pipeline_step("EXECUTION", "⚙️  Executor", "Running steps...", C.YELLOW)
        print_pipeline_step("CRITIQUE", "🔎 Critic", "Validating output...", C.GREEN)
        print_pipeline_step("DECISION", "🎯 Decision", "Generating response...", C.GREEN)
        
        # Actually run the query
        result = await orchestrator.process_query(q["query"])
        
        if result.get("success"):
            print_result(
                result.get("response", "No response"),
                {
                    "time_ms": result.get("execution_time_ms", 0),
                    "confidence": result.get("confidence", 0),
                    "stages": len(result.get("pipeline", {}).get("history", []))
                }
            )
            
            # Show followups
            followups = result.get("followups", [])
            if followups:
                print(f"{C.BRIGHT_YELLOW}💡 Suggested follow-ups:{C.RESET}")
                for f in followups:
                    print(f"   • {C.DIM}{f}{C.RESET}")
        else:
            print(f"{C.RED}❌ Error: {result.get('error', 'Unknown')}{C.RESET}")
        
        print()
    
    # Summary
    print(f"""
{C.BRIGHT_CYAN}{C.BOLD}{'═' * 80}{C.RESET}
{C.BRIGHT_GREEN}{C.BOLD}✅ Demo Complete!{C.RESET}

{C.CYAN}DevFlow processed 3 queries using:{C.RESET}
  • 5 specialized agents
  • Intent-based planning
  • Critic validation loop
  • Coordinated execution

{C.YELLOW}📹 This demo shows the multi-agent architecture in action!{C.RESET}
{C.BRIGHT_CYAN}{C.BOLD}{'═' * 80}{C.RESET}
""")


if __name__ == "__main__":
    asyncio.run(run_demo())

