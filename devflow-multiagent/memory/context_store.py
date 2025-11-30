"""
Context Store - Session and Memory Persistence

Provides:
- Session state management
- Query-response history
- Similarity-based recall
- Persistence to disk
"""

import json
import hashlib
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class ConversationTurn:
    """A single query-response pair."""
    turn_id: str
    query: str
    intent: str
    response: str
    quality_score: float
    timestamp: str
    execution_time_ms: int = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class Session:
    """A conversation session."""
    session_id: str
    start_time: str
    turns: List[ConversationTurn] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    end_time: Optional[str] = None
    
    @property
    def turn_count(self) -> int:
        return len(self.turns)
    
    @property
    def is_active(self) -> bool:
        return self.end_time is None


class ContextStore:
    """
    Manages session context and historical interactions.
    
    Features:
    - Session lifecycle management
    - Turn-by-turn conversation tracking
    - Similarity-based query recall
    - Disk persistence
    """
    
    def __init__(self, storage_dir: str = "sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        self.active_session: Optional[Session] = None
        self.session_history: List[Session] = []
        
        # Load history
        self._load_history()
    
    def start_session(self) -> Session:
        """Start a new conversation session."""
        session_id = hashlib.md5(
            datetime.now().isoformat().encode()
        ).hexdigest()[:12]
        
        self.active_session = Session(
            session_id=session_id,
            start_time=datetime.now().isoformat()
        )
        
        return self.active_session
    
    def end_session(self):
        """End the current session and persist."""
        if self.active_session:
            self.active_session.end_time = datetime.now().isoformat()
            self.session_history.append(self.active_session)
            self._save_session(self.active_session)
            self.active_session = None
    
    def add_turn(
        self,
        query: str,
        intent: str,
        response: str,
        quality_score: float,
        execution_time_ms: int = 0,
        metadata: Dict = None
    ) -> ConversationTurn:
        """Add a conversation turn to active session."""
        if not self.active_session:
            self.start_session()
        
        turn_id = f"{self.active_session.session_id}_{self.active_session.turn_count + 1:03d}"
        
        turn = ConversationTurn(
            turn_id=turn_id,
            query=query,
            intent=intent,
            response=response,
            quality_score=quality_score,
            timestamp=datetime.now().isoformat(),
            execution_time_ms=execution_time_ms,
            metadata=metadata or {}
        )
        
        self.active_session.turns.append(turn)
        
        # Auto-save after each turn
        self._save_session(self.active_session)
        
        return turn
    
    def get_session_context(self) -> Dict:
        """Get current session context for agents."""
        if not self.active_session:
            return {}
        
        return {
            "session_id": self.active_session.session_id,
            "turn_count": self.active_session.turn_count,
            "recent_queries": [
                t.query for t in self.active_session.turns[-5:]
            ],
            "context": self.active_session.context
        }
    
    def update_context(self, key: str, value: Any):
        """Update session context."""
        if self.active_session:
            self.active_session.context[key] = value
    
    def find_similar_queries(
        self, 
        query: str, 
        limit: int = 5
    ) -> List[Dict]:
        """
        Find similar past queries using Jaccard similarity.
        
        Args:
            query: Query to find matches for
            limit: Max results to return
        
        Returns:
            List of similar turns with similarity scores
        """
        query_words = set(query.lower().split())
        results = []
        
        # Search all sessions
        for session in self.session_history:
            for turn in session.turns:
                turn_words = set(turn.query.lower().split())
                
                # Jaccard similarity
                intersection = len(query_words & turn_words)
                union = len(query_words | turn_words)
                
                if union > 0:
                    similarity = intersection / union
                    
                    if similarity > 0.3:  # Threshold
                        results.append({
                            "turn_id": turn.turn_id,
                            "query": turn.query,
                            "intent": turn.intent,
                            "response_preview": turn.response[:200],
                            "similarity": similarity,
                            "quality": turn.quality_score,
                            "session_id": session.session_id
                        })
        
        # Also search current session
        if self.active_session:
            for turn in self.active_session.turns[:-1]:  # Exclude current
                turn_words = set(turn.query.lower().split())
                intersection = len(query_words & turn_words)
                union = len(query_words | turn_words)
                
                if union > 0:
                    similarity = intersection / union
                    if similarity > 0.3:
                        results.append({
                            "turn_id": turn.turn_id,
                            "query": turn.query,
                            "intent": turn.intent,
                            "response_preview": turn.response[:200],
                            "similarity": similarity,
                            "quality": turn.quality_score,
                            "session_id": self.active_session.session_id
                        })
        
        # Sort by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results[:limit]
    
    def get_intent_statistics(self) -> Dict[str, int]:
        """Get statistics on intent usage."""
        stats = {}
        
        for session in self.session_history:
            for turn in session.turns:
                stats[turn.intent] = stats.get(turn.intent, 0) + 1
        
        if self.active_session:
            for turn in self.active_session.turns:
                stats[turn.intent] = stats.get(turn.intent, 0) + 1
        
        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
    
    def _save_session(self, session: Session):
        """Save session to disk."""
        file_path = self.storage_dir / f"session_{session.session_id}.json"
        
        try:
            data = asdict(session)
            file_path.write_text(json.dumps(data, indent=2))
        except Exception:
            pass
    
    def _load_history(self):
        """Load session history from disk."""
        for file_path in self.storage_dir.glob("session_*.json"):
            try:
                data = json.loads(file_path.read_text())
                
                # Reconstruct session
                turns = [
                    ConversationTurn(**t) for t in data.get("turns", [])
                ]
                
                session = Session(
                    session_id=data["session_id"],
                    start_time=data["start_time"],
                    turns=turns,
                    context=data.get("context", {}),
                    end_time=data.get("end_time")
                )
                
                if session.end_time:  # Only add completed sessions
                    self.session_history.append(session)
                    
            except Exception:
                pass
    
    def get_summary(self) -> Dict:
        """Get storage summary."""
        total_turns = sum(s.turn_count for s in self.session_history)
        if self.active_session:
            total_turns += self.active_session.turn_count
        
        return {
            "sessions": len(self.session_history),
            "active": self.active_session is not None,
            "total_turns": total_turns,
            "storage_dir": str(self.storage_dir)
        }

