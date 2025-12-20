#!/usr/bin/env python3
"""
Real Analysis - Analyze ANY local git repository using phi4.

Usage:
    python real_analysis.py                     # Analyze current directory
    python real_analysis.py /path/to/repo       # Analyze specific repo
    python real_analysis.py --help              # Show help

Performs real git analysis and code review using phi4 Ollama model.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Global repo path - set from command line
REPO_PATH: Path = None

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
        cwd=str(REPO_PATH),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    return stdout.decode().strip()


async def real_standup_analysis():
    """Generate real standup summary from actual git history."""
    print_header(f"📝 REAL STANDUP SUMMARY - {REPO_PATH.name}")
    
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
    print_header(f"🔍 REAL CODE REVIEW - {REPO_PATH.name}")
    
    from llm import generate
    
    # Find a Python file to review in the target repo
    py_files = list(REPO_PATH.glob("**/*.py"))[:10]
    if not py_files:
        print(f"  {C.RED}No Python files found in repository{C.RESET}")
        return "No Python files found"
    
    # Pick a substantial file (prefer files with more content)
    target_file = max(py_files, key=lambda f: f.stat().st_size if f.exists() else 0)
    print_step(f"Selected for review: {target_file.relative_to(REPO_PATH)}")
    
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
    print_header(f"📊 REAL TECH DEBT ANALYSIS - {REPO_PATH.name}")
    
    from llm import generate
    
    # Find all Python files
    print_step("Scanning repository structure...")
    
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
    repo_name = REPO_PATH.name
    print(f"""
{C.BRIGHT_CYAN}{C.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           🚀 DevFlow REAL ANALYSIS - Using phi4 Ollama Model 🚀              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.RESET}
{C.YELLOW}📁 Repository: {C.WHITE}{REPO_PATH}{C.RESET}
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

{C.CYAN}DevFlow analyzed {REPO_PATH.name} using:{C.RESET}
  • 🤖 phi4 Ollama model for LLM analysis
  • 📊 Real git history from your repo  
  • 🔍 Actual code files and structure

{C.YELLOW}All outputs above are REAL - generated from your actual codebase!{C.RESET}
{C.BRIGHT_CYAN}{C.BOLD}{'═' * 80}{C.RESET}
""")
    
    await ollama.close()


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze any local git repository using phi4 Ollama model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python real_analysis.py                        # Analyze current directory
    python real_analysis.py /path/to/my/repo       # Analyze specific repo
    python real_analysis.py ~/projects/myproject   # Use ~ for home directory
    python real_analysis.py .                      # Explicitly use current dir

Requirements:
    - Ollama must be running with phi4 model: ollama run phi4
    - Target directory must be a git repository
        """
    )
    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Path to git repository (default: current directory)"
    )
    return parser.parse_args()


def validate_repo(path: Path) -> Path:
    """Validate that path is a git repository."""
    path = path.expanduser().resolve()
    
    if not path.exists():
        print(f"{C.RED}❌ Error: Path does not exist: {path}{C.RESET}")
        sys.exit(1)
    
    if not path.is_dir():
        print(f"{C.RED}❌ Error: Path is not a directory: {path}{C.RESET}")
        sys.exit(1)
    
    git_dir = path / ".git"
    if not git_dir.exists():
        print(f"{C.RED}❌ Error: Not a git repository: {path}{C.RESET}")
        print(f"{C.YELLOW}   (No .git directory found){C.RESET}")
        sys.exit(1)
    
    return path


if __name__ == "__main__":
    args = parse_args()
    REPO_PATH = validate_repo(Path(args.repo_path))
    asyncio.run(main())

