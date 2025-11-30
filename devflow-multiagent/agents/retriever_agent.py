"""
Retriever Agent - Context & Information Gathering

This agent fetches relevant context for the query including:
- Git history and commits
- Code files and snippets
- Documentation
- Previous similar queries from memory
"""

import os
import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from .base_agent import BaseAgent, AgentContext


@dataclass
class RetrievedItem:
    """A single retrieved piece of context."""
    source: str  # "git", "file", "memory", "docs"
    content: str
    relevance_score: float
    metadata: Dict[str, Any]


class RetrieverAgent(BaseAgent):
    """
    Gathers relevant context for query processing.
    Uses multiple retrieval strategies based on intent.
    """
    
    def __init__(self, workspace_path: Optional[str] = None):
        super().__init__("retriever", "🔍 Retriever")
        self.workspace = Path(workspace_path or os.getcwd())
    
    def get_capabilities(self) -> List[str]:
        return [
            "git_history_retrieval",
            "file_content_retrieval",
            "memory_search",
            "documentation_lookup",
            "context_ranking"
        ]
    
    async def process(self, context: AgentContext) -> Dict[str, Any]:
        """
        Retrieve relevant context based on perception understanding.
        """
        self.start_processing()
        
        try:
            understanding = context.current_understanding
            intent = understanding.get("intent", "general_help")
            entities = understanding.get("entities", {})
            temporal = understanding.get("temporal", {})
            
            retrieved_items: List[RetrievedItem] = []
            
            # Strategy: Route to appropriate retrieval methods
            if intent in ["standup_summary", "pr_description"]:
                git_items = await self._retrieve_git_context(
                    temporal, entities
                )
                retrieved_items.extend(git_items)
            
            if intent in ["code_review", "tech_debt", "documentation"]:
                file_items = await self._retrieve_file_context(entities)
                retrieved_items.extend(file_items)
            
            if intent == "dependency_check":
                dep_items = await self._retrieve_dependency_context()
                retrieved_items.extend(dep_items)
            
            # Always check memory for similar past queries
            memory_items = await self._retrieve_from_memory(
                context.original_query
            )
            retrieved_items.extend(memory_items)
            
            # Rank and filter results
            ranked_items = self._rank_results(retrieved_items)
            
            # Update shared context
            context.retrieved_context = [
                {
                    "source": item.source,
                    "content": item.content[:500],  # Truncate for context
                    "score": item.relevance_score,
                    "metadata": item.metadata
                }
                for item in ranked_items[:10]  # Top 10 items
            ]
            
            self.finish_processing(success=True)
            
            return {
                "success": True,
                "items_retrieved": len(ranked_items),
                "top_sources": list(set(i.source for i in ranked_items[:5])),
                "summary": self._create_summary(ranked_items)
            }
            
        except Exception as e:
            self.finish_processing(success=False)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _retrieve_git_context(
        self, 
        temporal: Dict, 
        entities: Dict
    ) -> List[RetrievedItem]:
        """Retrieve git commit history."""
        items = []
        
        try:
            # Determine time range
            since_date = self._get_since_date(temporal.get("reference"))
            
            # Try to get git commits
            commits = await self._run_git_command([
                "git", "log", 
                f"--since={since_date}",
                "--pretty=format:%h|%s|%an|%ad",
                "--date=short",
                "-n", "20"
            ])
            
            if commits:
                for line in commits.split("\n"):
                    if "|" in line:
                        parts = line.split("|")
                        if len(parts) >= 4:
                            items.append(RetrievedItem(
                                source="git",
                                content=f"[{parts[0]}] {parts[1]}",
                                relevance_score=0.8,
                                metadata={
                                    "hash": parts[0],
                                    "message": parts[1],
                                    "author": parts[2],
                                    "date": parts[3]
                                }
                            ))
            
            # Get changed files
            changed_files = await self._run_git_command([
                "git", "diff", "--name-only", f"--since={since_date}"
            ])
            
            if changed_files:
                items.append(RetrievedItem(
                    source="git",
                    content=f"Changed files:\n{changed_files}",
                    relevance_score=0.7,
                    metadata={"type": "changed_files"}
                ))
                
        except Exception:
            # Git not available or not a git repo
            items.append(RetrievedItem(
                source="git",
                content="[Git context unavailable - not a git repository]",
                relevance_score=0.1,
                metadata={"error": True}
            ))
        
        return items
    
    async def _retrieve_file_context(
        self, 
        entities: Dict
    ) -> List[RetrievedItem]:
        """Retrieve file contents based on entities."""
        items = []
        
        file_paths = entities.get("file_path", [])
        
        for file_path in file_paths[:5]:  # Limit to 5 files
            full_path = self.workspace / file_path
            
            if full_path.exists() and full_path.is_file():
                try:
                    content = full_path.read_text()
                    items.append(RetrievedItem(
                        source="file",
                        content=content[:2000],  # First 2000 chars
                        relevance_score=0.9,
                        metadata={
                            "path": str(file_path),
                            "size": len(content),
                            "type": full_path.suffix
                        }
                    ))
                except Exception:
                    pass
        
        return items
    
    async def _retrieve_dependency_context(self) -> List[RetrievedItem]:
        """Retrieve dependency information."""
        items = []
        
        # Check for common dependency files
        dep_files = [
            "requirements.txt",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "Gemfile"
        ]
        
        for dep_file in dep_files:
            full_path = self.workspace / dep_file
            if full_path.exists():
                try:
                    content = full_path.read_text()
                    items.append(RetrievedItem(
                        source="dependency",
                        content=content,
                        relevance_score=0.95,
                        metadata={
                            "file": dep_file,
                            "type": "dependency_manifest"
                        }
                    ))
                except Exception:
                    pass
        
        return items
    
    async def _retrieve_from_memory(self, query: str) -> List[RetrievedItem]:
        """Search memory for similar past queries."""
        # Placeholder - would connect to actual memory store
        return []
    
    def _rank_results(
        self, 
        items: List[RetrievedItem]
    ) -> List[RetrievedItem]:
        """Rank retrieved items by relevance."""
        return sorted(items, key=lambda x: x.relevance_score, reverse=True)
    
    def _get_since_date(self, temporal_ref: Optional[str]) -> str:
        """Convert temporal reference to date string."""
        now = datetime.now()
        
        mapping = {
            "yesterday": now - timedelta(days=1),
            "today": now,
            "last_week": now - timedelta(weeks=1),
            "this_week": now - timedelta(days=now.weekday()),
            "last_month": now - timedelta(days=30)
        }
        
        target = mapping.get(temporal_ref, now - timedelta(days=1))
        return target.strftime("%Y-%m-%d")
    
    async def _run_git_command(self, cmd: List[str]) -> str:
        """Run a git command and return output."""
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.workspace),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return stdout.decode().strip()
    
    def _create_summary(self, items: List[RetrievedItem]) -> str:
        """Create summary of retrieved context."""
        by_source = {}
        for item in items:
            by_source[item.source] = by_source.get(item.source, 0) + 1
        
        parts = [f"📦 Retrieved {len(items)} items:"]
        for source, count in by_source.items():
            parts.append(f"  • {source}: {count} items")
        
        return "\n".join(parts)

