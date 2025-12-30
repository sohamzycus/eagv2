"""
Reasoning Store.

Persistence layer for reasoning data.
Supports JSONL, SQLite, and in-memory storage.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .reasoning_node import ReasoningNode, ReasoningChain


class ReasoningStore(ABC):
    """
    Abstract base class for reasoning storage.

    Defines interface for persisting reasoning data.
    """

    @abstractmethod
    def log(
        self,
        session_id: str,
        agent_name: str,
        step: str,
        input_data: Any,
        decision: str,
        output: Any,
        next_step: Optional[str] = None,
    ) -> str:
        """
        Log a reasoning step.

        Returns the node ID.
        """
        pass

    @abstractmethod
    def get_chain(self, session_id: str) -> Optional[ReasoningChain]:
        """Get the complete reasoning chain for a session."""
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[ReasoningNode]:
        """Get a specific reasoning node."""
        pass

    @abstractmethod
    def list_sessions(self, limit: int = 100) -> list[str]:
        """List recent session IDs."""
        pass


class InMemoryReasoningStore(ReasoningStore):
    """
    In-memory reasoning store.

    Useful for testing and development.
    """

    def __init__(self):
        self._chains: dict[str, ReasoningChain] = {}
        self._nodes: dict[str, ReasoningNode] = {}

    def log(
        self,
        session_id: str,
        agent_name: str,
        step: str,
        input_data: Any,
        decision: str,
        output: Any,
        next_step: Optional[str] = None,
    ) -> str:
        """Log a reasoning step."""
        # Get or create chain
        if session_id not in self._chains:
            self._chains[session_id] = ReasoningChain(session_id=session_id)

        chain = self._chains[session_id]

        # Create node
        node = ReasoningNode(
            session_id=session_id,
            agent_name=agent_name,
            step_id=step,
            input_data=input_data,
            decision=decision,
            output_data=output,
            next_step=next_step,
        )

        # Add to chain and index
        chain.add_node(node)
        self._nodes[node.node_id] = node

        return node.node_id

    def get_chain(self, session_id: str) -> Optional[ReasoningChain]:
        """Get reasoning chain."""
        return self._chains.get(session_id)

    def get_node(self, node_id: str) -> Optional[ReasoningNode]:
        """Get reasoning node."""
        return self._nodes.get(node_id)

    def list_sessions(self, limit: int = 100) -> list[str]:
        """List sessions."""
        sessions = sorted(
            self._chains.keys(),
            key=lambda s: self._chains[s].started_at,
            reverse=True,
        )
        return sessions[:limit]

    def clear(self) -> None:
        """Clear all data."""
        self._chains.clear()
        self._nodes.clear()


class JSONLReasoningStore(ReasoningStore):
    """
    JSONL-based reasoning store.

    Persists reasoning data to JSONL files.
    One file per session for efficient streaming.
    """

    def __init__(self, storage_dir: str = "./reasoning_data"):
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, ReasoningChain] = {}

    def log(
        self,
        session_id: str,
        agent_name: str,
        step: str,
        input_data: Any,
        decision: str,
        output: Any,
        next_step: Optional[str] = None,
    ) -> str:
        """Log a reasoning step to JSONL file."""
        # Get or create chain
        if session_id not in self._cache:
            existing_chain = self._load_chain(session_id)
            self._cache[session_id] = existing_chain or ReasoningChain(session_id=session_id)

        chain = self._cache[session_id]

        # Create node
        node = ReasoningNode(
            session_id=session_id,
            agent_name=agent_name,
            step_id=step,
            input_data=input_data,
            decision=decision,
            output_data=output,
            next_step=next_step,
        )

        # Add to chain
        chain.add_node(node)

        # Append to file
        self._append_node(session_id, node)

        return node.node_id

    def get_chain(self, session_id: str) -> Optional[ReasoningChain]:
        """Get reasoning chain, loading from file if needed."""
        if session_id in self._cache:
            return self._cache[session_id]
        return self._load_chain(session_id)

    def get_node(self, node_id: str) -> Optional[ReasoningNode]:
        """Get a specific node by ID."""
        # Search through all cached chains
        for chain in self._cache.values():
            node = chain.get_node(node_id)
            if node:
                return node

        # Search through files
        for session_file in self._storage_dir.glob("*.jsonl"):
            chain = self._load_chain(session_file.stem)
            if chain:
                node = chain.get_node(node_id)
                if node:
                    return node

        return None

    def list_sessions(self, limit: int = 100) -> list[str]:
        """List sessions from storage."""
        sessions = []
        for session_file in self._storage_dir.glob("*.jsonl"):
            sessions.append(session_file.stem)

        # Sort by modification time
        sessions.sort(
            key=lambda s: (self._storage_dir / f"{s}.jsonl").stat().st_mtime,
            reverse=True,
        )

        return sessions[:limit]

    def _get_session_file(self, session_id: str) -> Path:
        """Get path to session file."""
        return self._storage_dir / f"{session_id}.jsonl"

    def _append_node(self, session_id: str, node: ReasoningNode) -> None:
        """Append node to session file."""
        file_path = self._get_session_file(session_id)
        with open(file_path, "a") as f:
            f.write(json.dumps(node.to_dict()) + "\n")

    def _load_chain(self, session_id: str) -> Optional[ReasoningChain]:
        """Load chain from file."""
        file_path = self._get_session_file(session_id)
        if not file_path.exists():
            return None

        chain = ReasoningChain(session_id=session_id)
        with open(file_path, "r") as f:
            for line in f:
                if line.strip():
                    node_data = json.loads(line)
                    node = ReasoningNode.from_dict(node_data)
                    chain.nodes.append(node)

        if chain.nodes:
            chain.started_at = chain.nodes[0].timestamp
            if chain.nodes[-1].next_step is None and chain.nodes[-1].next_agent is None:
                chain.completed_at = chain.nodes[-1].timestamp
                chain.status = "completed"

        self._cache[session_id] = chain
        return chain

    def export_session(self, session_id: str, format: str = "json") -> str:
        """Export session data."""
        chain = self.get_chain(session_id)
        if not chain:
            return "{}"

        if format == "json":
            return json.dumps(chain.to_dict(), indent=2)
        else:
            # Return raw JSONL
            file_path = self._get_session_file(session_id)
            if file_path.exists():
                return file_path.read_text()
            return ""


@dataclass
class ReasoningQuery:
    """
    Query for filtering reasoning data.

    Used for analysis and debugging.
    """

    session_ids: list[str] = None
    agent_names: list[str] = None
    step_ids: list[str] = None
    has_error: Optional[bool] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100

    def matches(self, node: ReasoningNode) -> bool:
        """Check if node matches query."""
        if self.session_ids and node.session_id not in self.session_ids:
            return False
        if self.agent_names and node.agent_name not in self.agent_names:
            return False
        if self.step_ids and node.step_id not in self.step_ids:
            return False
        if self.has_error is not None:
            if self.has_error and not node.error:
                return False
            if not self.has_error and node.error:
                return False
        if self.start_time and node.timestamp < self.start_time:
            return False
        if self.end_time and node.timestamp > self.end_time:
            return False
        return True


class ReasoningAnalyzer:
    """
    Analyzer for reasoning data.

    Provides insights and metrics from reasoning chains.
    """

    def __init__(self, store: ReasoningStore):
        self._store = store

    def get_session_stats(self, session_id: str) -> dict[str, Any]:
        """Get statistics for a session."""
        chain = self._store.get_chain(session_id)
        if not chain:
            return {}

        return {
            "session_id": session_id,
            "total_steps": len(chain.nodes),
            "unique_agents": len(set(n.agent_name for n in chain.nodes)),
            "unique_steps": len(set(n.step_id for n in chain.nodes if n.step_id)),
            "total_duration_ms": chain.get_duration_ms(),
            "avg_step_duration_ms": chain.get_duration_ms() / len(chain.nodes) if chain.nodes else 0,
            "error_count": len(chain.get_errors()),
            "status": chain.status,
        }

    def get_agent_performance(self, session_id: str) -> dict[str, dict[str, Any]]:
        """Get performance metrics by agent."""
        chain = self._store.get_chain(session_id)
        if not chain:
            return {}

        agents = {}
        for node in chain.nodes:
            if node.agent_name not in agents:
                agents[node.agent_name] = {
                    "call_count": 0,
                    "total_duration_ms": 0,
                    "error_count": 0,
                }
            agents[node.agent_name]["call_count"] += 1
            agents[node.agent_name]["total_duration_ms"] += node.duration_ms
            if node.error:
                agents[node.agent_name]["error_count"] += 1

        # Calculate averages
        for agent in agents.values():
            if agent["call_count"] > 0:
                agent["avg_duration_ms"] = agent["total_duration_ms"] / agent["call_count"]

        return agents

    def find_bottlenecks(self, session_id: str, threshold_ms: int = 1000) -> list[ReasoningNode]:
        """Find steps that took longer than threshold."""
        chain = self._store.get_chain(session_id)
        if not chain:
            return []

        return [n for n in chain.nodes if n.duration_ms > threshold_ms]



