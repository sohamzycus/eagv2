"""
Reasoning Node.

Represents a single step in the agent's reasoning chain.
Provides full traceability and replay capability.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4


@dataclass
class ReasoningNode:
    """
    A single node in the reasoning chain.

    Captures complete context for one reasoning step.
    """

    # Identification
    node_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str = ""
    parent_id: Optional[str] = None

    # Agent info
    agent_name: str = ""
    step_id: str = ""

    # Input/Output
    input_data: Any = None
    output_data: Any = None

    # Decision
    decision: str = ""
    reasoning: str = ""
    confidence: float = 1.0

    # Flow control
    next_step: Optional[str] = None
    next_agent: Optional[str] = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: int = 0
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "node_id": self.node_id,
            "session_id": self.session_id,
            "parent_id": self.parent_id,
            "agent_name": self.agent_name,
            "step_id": self.step_id,
            "input_data": self._serialize_data(self.input_data),
            "output_data": self._serialize_data(self.output_data),
            "decision": self.decision,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "next_step": self.next_step,
            "next_agent": self.next_agent,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "error": self.error,
            "metadata": self.metadata,
        }

    def _serialize_data(self, data: Any) -> Any:
        """Serialize data for storage."""
        if data is None:
            return None
        if isinstance(data, (str, int, float, bool)):
            return data
        if isinstance(data, (list, tuple)):
            return [self._serialize_data(item) for item in data]
        if isinstance(data, dict):
            return {k: self._serialize_data(v) for k, v in data.items()}
        if hasattr(data, "to_dict"):
            return data.to_dict()
        if hasattr(data, "__dict__"):
            return {k: self._serialize_data(v) for k, v in data.__dict__.items()}
        return str(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReasoningNode":
        """Create from dictionary."""
        return cls(
            node_id=data.get("node_id", str(uuid4())),
            session_id=data.get("session_id", ""),
            parent_id=data.get("parent_id"),
            agent_name=data.get("agent_name", ""),
            step_id=data.get("step_id", ""),
            input_data=data.get("input_data"),
            output_data=data.get("output_data"),
            decision=data.get("decision", ""),
            reasoning=data.get("reasoning", ""),
            confidence=data.get("confidence", 1.0),
            next_step=data.get("next_step"),
            next_agent=data.get("next_agent"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            duration_ms=data.get("duration_ms", 0),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )

    def to_display(self) -> dict[str, Any]:
        """Convert to display-friendly format for UI."""
        return {
            "step": self.step_id,
            "agent": self.agent_name,
            "decision": self.decision,
            "reasoning": self.reasoning,
            "next": self.next_step or self.next_agent or "END",
            "time": self.timestamp.strftime("%H:%M:%S"),
            "duration": f"{self.duration_ms}ms",
            "error": self.error,
        }


@dataclass
class ReasoningChain:
    """
    A chain of reasoning nodes forming complete session trace.

    Provides methods for traversal and analysis.
    """

    session_id: str
    nodes: list[ReasoningNode] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: str = "in_progress"
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: ReasoningNode) -> None:
        """Add a node to the chain."""
        node.session_id = self.session_id
        if self.nodes:
            node.parent_id = self.nodes[-1].node_id
        self.nodes.append(node)

    def get_node(self, node_id: str) -> Optional[ReasoningNode]:
        """Get node by ID."""
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def get_nodes_by_agent(self, agent_name: str) -> list[ReasoningNode]:
        """Get all nodes from a specific agent."""
        return [n for n in self.nodes if n.agent_name == agent_name]

    def get_nodes_by_step(self, step_id: str) -> list[ReasoningNode]:
        """Get all nodes for a specific step."""
        return [n for n in self.nodes if n.step_id == step_id]

    def get_errors(self) -> list[ReasoningNode]:
        """Get all nodes with errors."""
        return [n for n in self.nodes if n.error]

    def complete(self, status: str = "completed") -> None:
        """Mark chain as complete."""
        self.completed_at = datetime.now()
        self.status = status

    def get_duration_ms(self) -> int:
        """Get total duration in milliseconds."""
        if not self.nodes:
            return 0
        return sum(n.duration_ms for n in self.nodes)

    def get_summary(self) -> dict[str, Any]:
        """Get chain summary."""
        return {
            "session_id": self.session_id,
            "status": self.status,
            "total_nodes": len(self.nodes),
            "agents_involved": list(set(n.agent_name for n in self.nodes)),
            "steps_executed": list(set(n.step_id for n in self.nodes if n.step_id)),
            "errors": len(self.get_errors()),
            "total_duration_ms": self.get_duration_ms(),
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def to_timeline(self) -> list[dict[str, Any]]:
        """Convert to timeline format for UI display."""
        return [node.to_display() for node in self.nodes]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReasoningChain":
        """Create from dictionary."""
        chain = cls(
            session_id=data["session_id"],
            started_at=datetime.fromisoformat(data["started_at"]),
            status=data.get("status", "unknown"),
            metadata=data.get("metadata", {}),
        )
        if data.get("completed_at"):
            chain.completed_at = datetime.fromisoformat(data["completed_at"])
        for node_data in data.get("nodes", []):
            chain.nodes.append(ReasoningNode.from_dict(node_data))
        return chain

    def replay(self) -> list[dict[str, Any]]:
        """
        Generate replay data for debugging.

        Returns step-by-step trace of reasoning.
        """
        replay = []
        for i, node in enumerate(self.nodes):
            replay.append({
                "sequence": i + 1,
                "timestamp": node.timestamp.isoformat(),
                "agent": node.agent_name,
                "step": node.step_id,
                "input": node.input_data,
                "decision": node.decision,
                "output": node.output_data,
                "next": node.next_step or node.next_agent,
                "error": node.error,
            })
        return replay

