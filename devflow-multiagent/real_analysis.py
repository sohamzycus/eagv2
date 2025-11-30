#!/usr/bin/env python3
"""
Real Analysis - Actual analysis of eagv2 repo using phi4.

Performs real git analysis and code review.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

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


def print_header(title: str):
    print(f"\n{C.BRIGHT_CYAN}{C.BOLD}{'═' * 80}")
    print(f"  {title}")
    print(f"{'═' * 80}{C.RESET}\n")


def print_step(step: str, detail: str = ""):
    print(f"  {C.CYAN}▶{C.RESET} {step} {C.DIM}{detail}{C.RESET}")


async def run_git_command(*args) -> str:
    """Run git command and return output."""
    proc = await asyncio.create_subprocess_exec(
        "git", *args,
        cwd="/Users/soham.niyogi/Soham/codebase/eagv2",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    return stdout.decode().strip()


async def real_standup_analysis():
    """Generate real standup summary from actual git history."""
    print_header("📝 REAL STANDUP SUMMARY - eagv2 Repository")
    
    from llm import generate
    
    # Get recent commits
    print_step("Fetching git commits...")
    commits = await run_git_command(
        "log", "--oneline", "-10", 
        "--pretty=format:%h | %s | %an | %ar"
    )
    
    print(f"\n{C.YELLOW}Recent Commits:{C.RESET}")
    for line in commits.split("\n"):
        print(f"  {C.DIM}{line}{C.RESET}")
    
    # Get changed files
    print_step("\nFetching changed files...")
    changed = await run_git_command(
        "diff", "--stat", "HEAD~5", "HEAD"
    )
    
    # Use phi4 to generate standup
    print_step("\n🤖 Using phi4 to generate standup summary...")
    
    prompt = f"""Based on these git commits and changes, generate a concise standup summary:

RECENT COMMITS:
{commits}

FILE CHANGES:
{changed}

Generate a professional standup update in this format:
## What I worked on
- [bullet points of work done]

## Status
- [current status]

## Next steps  
- [what's planned next]

Keep it concise and professional."""

    system = "You are a developer assistant generating standup summaries from git history."
    
    result = await generate(prompt, system)
    
    print(f"\n{C.BRIGHT_GREEN}{'─' * 80}{C.RESET}")
    print(f"{C.BRIGHT_GREEN}📋 Generated Standup (via phi4):{C.RESET}")
    print(f"{C.WHITE}{result}{C.RESET}")
    print(f"{C.BRIGHT_GREEN}{'─' * 80}{C.RESET}")
    
    return result


async def real_code_review():
    """Perform real code review on actual files."""
    print_header("🔍 REAL CODE REVIEW - DevFlow Main Module")
    
    from llm import generate
    
    # Read actual code file
    target_file = Path(__file__).parent / "main.py"
    print_step(f"Reading {target_file.name}...")
    
    code = target_file.read_text()[:3000]  # First 3000 chars
    
    # Use phi4 for code review
    print_step("🤖 Using phi4 to review code...")
    
    prompt = f"""Review this Python code and provide feedback:

```python
{code}
```

Provide a brief code review with:
1. **Strengths** - What's good about this code
2. **Issues** - Any problems or anti-patterns
3. **Suggestions** - Specific improvements

Keep response under 300 words."""

    system = "You are an expert Python code reviewer. Be concise and constructive."
    
    result = await generate(prompt, system)
    
    print(f"\n{C.BRIGHT_GREEN}{'─' * 80}{C.RESET}")
    print(f"{C.BRIGHT_GREEN}📋 Code Review (via phi4):{C.RESET}")
    print(f"{C.WHITE}{result}{C.RESET}")
    print(f"{C.BRIGHT_GREEN}{'─' * 80}{C.RESET}")
    
    return result


async def real_tech_debt_analysis():
    """Analyze real tech debt in the repository."""
    print_header("📊 REAL TECH DEBT ANALYSIS - eagv2 Repository")
    
    from llm import generate
    
    # Find all Python files
    print_step("Scanning repository structure...")
    
    repo_path = Path("/Users/soham.niyogi/Soham/codebase/eagv2")
    
    # Get directory structure
    structure = await run_git_command("ls-tree", "-r", "--name-only", "HEAD")
    py_files = [f for f in structure.split("\n") if f.endswith(".py")][:30]
    
    # Get file counts by directory
    dirs = {}
    for f in py_files:
        d = f.split("/")[0] if "/" in f else "root"
        dirs[d] = dirs.get(d, 0) + 1
    
    print(f"\n{C.YELLOW}Repository Structure:{C.RESET}")
    for d, count in sorted(dirs.items(), key=lambda x: -x[1]):
        print(f"  {C.DIM}{d}/: {count} Python files{C.RESET}")
    
    # Look for TODO/FIXME comments
    print_step("\nSearching for TODO/FIXME markers...")
    todos = await run_git_command("grep", "-n", "-E", "TODO|FIXME|HACK|XXX", "--", "*.py")
    todo_count = len(todos.split("\n")) if todos else 0
    
    # Use phi4 for analysis
    print_step("🤖 Using phi4 to analyze tech debt...")
    
    prompt = f"""Analyze this repository for technical debt:

STRUCTURE:
{dict(sorted(dirs.items(), key=lambda x: -x[1]))}

TODO/FIXME MARKERS FOUND: {todo_count}

SAMPLE FILES:
{chr(10).join(py_files[:15])}

Provide a brief tech debt analysis:
1. **Observations** - What patterns do you see?
2. **Concerns** - Potential issues
3. **Recommendations** - Priority fixes

Keep response under 250 words."""

    system = "You are a software architect analyzing codebase health."
    
    result = await generate(prompt, system)
    
    print(f"\n{C.BRIGHT_GREEN}{'─' * 80}{C.RESET}")
    print(f"{C.BRIGHT_GREEN}📋 Tech Debt Analysis (via phi4):{C.RESET}")
    print(f"{C.WHITE}{result}{C.RESET}")
    print(f"{C.BRIGHT_GREEN}{'─' * 80}{C.RESET}")
    
    return result


async def main():
    """Run all real analyses."""
    print(f"""
{C.BRIGHT_CYAN}{C.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           🚀 DevFlow REAL ANALYSIS - Using phi4 Ollama Model 🚀              ║
║                                                                              ║
║                Analyzing: eagv2 GitHub Repository                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.RESET}
""")
    
    print(f"{C.YELLOW}⚡ Connecting to Ollama (phi4 model)...{C.RESET}")
    
    from llm import get_ollama
    ollama = await get_ollama()
    
    print(f"{C.GREEN}✅ Connected to Ollama!{C.RESET}\n")
    
    # Run all 3 analyses
    await real_standup_analysis()
    await real_code_review()
    await real_tech_debt_analysis()
    
    # Summary
    print(f"""
{C.BRIGHT_CYAN}{C.BOLD}{'═' * 80}{C.RESET}
{C.BRIGHT_GREEN}{C.BOLD}✅ Real Analysis Complete!{C.RESET}

{C.CYAN}DevFlow analyzed the actual eagv2 repository using:{C.RESET}
  • 🤖 phi4 Ollama model for LLM analysis
  • 📊 Real git history from your repo  
  • 🔍 Actual code files and structure

{C.YELLOW}All outputs above are REAL - generated from your actual codebase!{C.RESET}
{C.BRIGHT_CYAN}{C.BOLD}{'═' * 80}{C.RESET}
""")
    
    await ollama.close()


if __name__ == "__main__":
    asyncio.run(main())

