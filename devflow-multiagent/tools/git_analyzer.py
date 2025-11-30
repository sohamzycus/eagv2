"""
Git Analyzer Tool - Analyzes Git Repository History

Provides:
- Commit history retrieval
- Branch information
- File change tracking
- Diff analysis
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class GitCommit:
    """Represents a git commit."""
    hash: str
    short_hash: str
    message: str
    author: str
    author_email: str
    date: datetime
    files_changed: List[str] = None
    
    @classmethod
    def from_log_line(cls, line: str) -> Optional["GitCommit"]:
        """Parse from git log format."""
        # Format: hash|short|message|author|email|date
        parts = line.strip().split("|")
        if len(parts) >= 6:
            try:
                return cls(
                    hash=parts[0],
                    short_hash=parts[1],
                    message=parts[2],
                    author=parts[3],
                    author_email=parts[4],
                    date=datetime.fromisoformat(parts[5]) if parts[5] else datetime.now()
                )
            except Exception:
                pass
        return None


@dataclass
class FileDiff:
    """Represents changes to a file."""
    path: str
    additions: int
    deletions: int
    status: str  # A=added, M=modified, D=deleted, R=renamed


class GitAnalyzer:
    """
    Analyzes git repositories for developer productivity workflows.
    
    Features:
    - Get commits by time range
    - Analyze file changes
    - Generate summaries for standups
    - Compare branches for PRs
    """
    
    def __init__(self, repo_path: str = None):
        self.repo_path = Path(repo_path or os.getcwd())
        self._is_git_repo = None
    
    async def _run_git(self, *args) -> Optional[str]:
        """Execute a git command and return output."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", *args,
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                return stdout.decode().strip()
            return None
        except Exception:
            return None
    
    async def is_git_repository(self) -> bool:
        """Check if current path is a git repository."""
        if self._is_git_repo is None:
            result = await self._run_git("rev-parse", "--git-dir")
            self._is_git_repo = result is not None
        return self._is_git_repo
    
    async def get_current_branch(self) -> Optional[str]:
        """Get current branch name."""
        return await self._run_git("rev-parse", "--abbrev-ref", "HEAD")
    
    async def get_commits(
        self, 
        since: str = None, 
        until: str = None,
        author: str = None,
        limit: int = 20
    ) -> List[GitCommit]:
        """
        Get commits matching criteria.
        
        Args:
            since: Start date (YYYY-MM-DD or relative like "yesterday")
            until: End date
            author: Filter by author
            limit: Maximum commits to return
        """
        args = [
            "log",
            f"--pretty=format:%H|%h|%s|%an|%ae|%aI",
            f"-n{limit}"
        ]
        
        if since:
            args.append(f"--since={since}")
        if until:
            args.append(f"--until={until}")
        if author:
            args.append(f"--author={author}")
        
        output = await self._run_git(*args)
        if not output:
            return []
        
        commits = []
        for line in output.split("\n"):
            commit = GitCommit.from_log_line(line)
            if commit:
                commits.append(commit)
        
        return commits
    
    async def get_commits_since_yesterday(self) -> List[GitCommit]:
        """Convenience method for standup summaries."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return await self.get_commits(since=yesterday)
    
    async def get_files_changed(
        self, 
        since: str = None,
        ref: str = None
    ) -> List[FileDiff]:
        """
        Get list of changed files.
        
        Args:
            since: Get changes since this date
            ref: Compare against this ref (e.g., "main")
        """
        if ref:
            output = await self._run_git(
                "diff", "--numstat", ref
            )
        elif since:
            output = await self._run_git(
                "diff", "--numstat", f"--since={since}"
            )
        else:
            output = await self._run_git(
                "diff", "--numstat", "HEAD~5"
            )
        
        if not output:
            return []
        
        diffs = []
        for line in output.split("\n"):
            parts = line.split("\t")
            if len(parts) >= 3:
                try:
                    diffs.append(FileDiff(
                        path=parts[2],
                        additions=int(parts[0]) if parts[0] != "-" else 0,
                        deletions=int(parts[1]) if parts[1] != "-" else 0,
                        status="M"
                    ))
                except ValueError:
                    pass
        
        return diffs
    
    async def get_branch_comparison(
        self, 
        base: str = "main"
    ) -> Dict[str, Any]:
        """
        Compare current branch against base.
        
        Returns diff statistics for PR descriptions.
        """
        current = await self.get_current_branch()
        
        # Get commits ahead of base
        output = await self._run_git(
            "rev-list", "--count", f"{base}..{current}"
        )
        commits_ahead = int(output) if output else 0
        
        # Get commits behind base
        output = await self._run_git(
            "rev-list", "--count", f"{current}..{base}"
        )
        commits_behind = int(output) if output else 0
        
        # Get file changes
        files = await self.get_files_changed(ref=base)
        
        return {
            "current_branch": current,
            "base_branch": base,
            "commits_ahead": commits_ahead,
            "commits_behind": commits_behind,
            "files_changed": len(files),
            "total_additions": sum(f.additions for f in files),
            "total_deletions": sum(f.deletions for f in files),
            "files": [f.path for f in files]
        }
    
    async def generate_standup_data(self) -> Dict[str, Any]:
        """
        Generate data for standup summary.
        
        Returns structured data about yesterday's work.
        """
        commits = await self.get_commits_since_yesterday()
        files = await self.get_files_changed(since="yesterday")
        
        # Categorize commits
        categories = {
            "features": [],
            "fixes": [],
            "refactors": [],
            "docs": [],
            "other": []
        }
        
        for commit in commits:
            msg_lower = commit.message.lower()
            if any(k in msg_lower for k in ["feat", "add", "new", "implement"]):
                categories["features"].append(commit)
            elif any(k in msg_lower for k in ["fix", "bug", "patch", "resolve"]):
                categories["fixes"].append(commit)
            elif any(k in msg_lower for k in ["refactor", "clean", "improve"]):
                categories["refactors"].append(commit)
            elif any(k in msg_lower for k in ["doc", "readme", "comment"]):
                categories["docs"].append(commit)
            else:
                categories["other"].append(commit)
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "commits": [
                {"hash": c.short_hash, "message": c.message}
                for c in commits
            ],
            "files_changed": [f.path for f in files],
            "statistics": {
                "total_commits": len(commits),
                "features": len(categories["features"]),
                "fixes": len(categories["fixes"]),
                "additions": sum(f.additions for f in files),
                "deletions": sum(f.deletions for f in files)
            },
            "categories": {
                k: [c.message for c in v]
                for k, v in categories.items()
                if v
            }
        }
    
    async def generate_pr_data(self, base: str = "main") -> Dict[str, Any]:
        """
        Generate data for PR description.
        
        Returns structured data about branch changes.
        """
        comparison = await self.get_branch_comparison(base)
        
        # Get commits for this branch
        output = await self._run_git(
            "log",
            f"--pretty=format:%h|%s",
            f"{base}..HEAD"
        )
        
        commits = []
        if output:
            for line in output.split("\n"):
                parts = line.split("|", 1)
                if len(parts) == 2:
                    commits.append({
                        "hash": parts[0],
                        "message": parts[1]
                    })
        
        # Determine change type
        change_type = "misc"
        for commit in commits:
            msg = commit["message"].lower()
            if "feat" in msg or "add" in msg:
                change_type = "feature"
                break
            elif "fix" in msg or "bug" in msg:
                change_type = "bugfix"
                break
            elif "refactor" in msg:
                change_type = "refactor"
                break
        
        return {
            **comparison,
            "commits": commits,
            "change_type": change_type,
            "summary": f"{len(commits)} commits with {comparison['total_additions']}++ {comparison['total_deletions']}--"
        }

