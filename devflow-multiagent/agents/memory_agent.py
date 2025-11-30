"""
Memory Agent - Context & History Management

This agent manages:
- Session context and state
- Historical query/response pairs
- Long-term knowledge accumulation
- Similar past query recall
"""

import json
import hashlib
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from .base_agent import BaseAgent, AgentContext


@dataclass
class MemoryEntry:
    """A single memory entry."""
    entry_id: str
    query: str
    intent: str
    response: str
    quality_score: float
    timestamp: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class SessionState:
    """Current session state."""
    session_id: str
    start_time: str
    queries: List[str] = field(default_factory=list)
    context_stack: List[Dict] = field(default_factory=list)
    last_response: Optional[str] = None


class MemoryAgent(BaseAgent):
    """
    Manages persistent memory across sessions.
    Enables learning from past interactions.
    """
    
    def __init__(self, storage_dir: str = "sessions"):
        super().__init__("memory", "🧠 Memory")
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        self.session: Optional[SessionState] = None
        self.long_term_memory: List[MemoryEntry] = []
        
        # Load existing memory
        self._load_long_term_memory()
    
    def get_capabilities(self) -> List[str]:
        return [
            "session_management",
            "context_storage",
            "history_recall",
            "similar_query_search",
            "knowledge_persistence"
        ]
    
    async def process(self, context: AgentContext) -> Dict[str, Any]:
        """
        Process memory operations for current context.
        """
        self.start_processing()
        
        try:
            # Ensure session exists
            if not self.session:
                self._start_session(context.query_id)
            
            # Add current query to session
            self.session.queries.append(context.original_query)
            
            # Search for similar past queries
            similar = self._find_similar_queries(context.original_query)
            
            # Update context with memory recalls
            context.memory_recalls = similar
            
            # Store current context in session stack
            self.session.context_stack.append({
                "query": context.original_query,
                "understanding": context.current_understanding,
                "timestamp": datetime.now().isoformat()
            })
            
            self.finish_processing(success=True)
            
            return {
                "success": True,
                "session_id": self.session.session_id,
                "similar_queries": len(similar),
                "context_depth": len(self.session.context_stack),
                "summary": self._create_summary(similar)
            }
            
        except Exception as e:
            self.finish_processing(success=False)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _start_session(self, session_id: str):
        """Initialize a new session."""
        self.session = SessionState(
            session_id=session_id,
            start_time=datetime.now().isoformat()
        )
    
    def store_interaction(
        self,
        query: str,
        intent: str,
        response: str,
        quality_score: float,
        tags: List[str] = None
    ):
        """Store a completed interaction in long-term memory."""
        entry_id = hashlib.md5(
            f"{query}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        entry = MemoryEntry(
            entry_id=entry_id,
            query=query,
            intent=intent,
            response=response,
            quality_score=quality_score,
            timestamp=datetime.now().isoformat(),
            tags=tags or []
        )
        
        self.long_term_memory.append(entry)
        self._save_long_term_memory()
        
        # Update session
        if self.session:
            self.session.last_response = response
    
    def _find_similar_queries(self, query: str) -> List[Dict]:
        """Find similar past queries using simple text matching."""
        query_words = set(query.lower().split())
        similar = []
        
        for entry in self.long_term_memory:
            entry_words = set(entry.query.lower().split())
            
            # Calculate Jaccard similarity
            intersection = len(query_words & entry_words)
            union = len(query_words | entry_words)
            
            if union > 0:
                similarity = intersection / union
                
                if similarity > 0.3:  # Threshold
                    similar.append({
                        "entry_id": entry.entry_id,
                        "query": entry.query,
                        "intent": entry.intent,
                        "response_preview": entry.response[:200],
                        "similarity": similarity,
                        "quality": entry.quality_score
                    })
        
        # Sort by similarity
        similar.sort(key=lambda x: x["similarity"], reverse=True)
        return similar[:5]  # Top 5
    
    def get_session_context(self) -> Dict:
        """Get current session context summary."""
        if not self.session:
            return {}
        
        return {
            "session_id": self.session.session_id,
            "query_count": len(self.session.queries),
            "recent_queries": self.session.queries[-5:],
            "context_depth": len(self.session.context_stack)
        }
    
    def _load_long_term_memory(self):
        """Load memory from disk."""
        memory_file = self.storage_dir / "long_term_memory.json"
        
        if memory_file.exists():
            try:
                data = json.loads(memory_file.read_text())
                self.long_term_memory = [
                    MemoryEntry(**entry) for entry in data
                ]
            except Exception:
                self.long_term_memory = []
    
    def _save_long_term_memory(self):
        """Save memory to disk."""
        memory_file = self.storage_dir / "long_term_memory.json"
        
        try:
            data = [asdict(entry) for entry in self.long_term_memory]
            memory_file.write_text(json.dumps(data, indent=2))
        except Exception:
            pass
    
    def save_session(self):
        """Persist current session to disk."""
        if not self.session:
            return
        
        session_file = self.storage_dir / f"session_{self.session.session_id}.json"
        
        try:
            data = asdict(self.session)
            session_file.write_text(json.dumps(data, indent=2))
        except Exception:
            pass
    
    def _create_summary(self, similar: List[Dict]) -> str:
        """Create memory summary."""
        lines = ["💾 Memory Status:"]
        
        if similar:
            lines.append(f"  Found {len(similar)} similar past queries")
            if similar[0]["similarity"] > 0.5:
                lines.append(f"  Best match: {similar[0]['similarity']:.0%}")
        else:
            lines.append("  No similar past queries found")
        
        lines.append(f"  Total memories: {len(self.long_term_memory)}")
        
        return "\n".join(lines)

