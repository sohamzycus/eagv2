"""
Audit Logger.

Provides compliance-ready audit logging for all system events.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


class AuditEventType(Enum):
    """Types of audit events."""

    SESSION_START = auto()
    SESSION_END = auto()
    USER_INPUT = auto()
    AGENT_ACTION = auto()
    TOOL_CALL = auto()
    TOOL_RESPONSE = auto()
    DECISION = auto()
    ERROR = auto()
    VALIDATION = auto()
    STATE_CHANGE = auto()
    PROMPT_GENERATED = auto()
    TOOLS_GENERATED = auto()


@dataclass
class AuditEvent:
    """
    A single audit event.

    Captures complete context for compliance and debugging.
    """

    event_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str = ""
    event_type: AuditEventType = AuditEventType.AGENT_ACTION
    actor: str = ""  # Agent or user who caused event
    action: str = ""
    input_data: Any = None
    output_data: Any = None
    decision: Optional[str] = None
    next_action: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: int = 0
    success: bool = True
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "event_type": self.event_type.name,
            "actor": self.actor,
            "action": self.action,
            "input": self._serialize(self.input_data),
            "output": self._serialize(self.output_data),
            "decision": self.decision,
            "next_action": self.next_action,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata,
        }

    def _serialize(self, data: Any) -> Any:
        """Serialize data for storage."""
        if data is None:
            return None
        if isinstance(data, (str, int, float, bool)):
            return data
        if isinstance(data, (list, tuple)):
            return [self._serialize(item) for item in data]
        if isinstance(data, dict):
            return {k: self._serialize(v) for k, v in data.items()}
        if hasattr(data, "to_dict"):
            return data.to_dict()
        return str(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditEvent":
        """Create from dictionary."""
        return cls(
            event_id=data.get("event_id", str(uuid4())),
            session_id=data.get("session_id", ""),
            event_type=AuditEventType[data.get("event_type", "AGENT_ACTION")],
            actor=data.get("actor", ""),
            action=data.get("action", ""),
            input_data=data.get("input"),
            output_data=data.get("output"),
            decision=data.get("decision"),
            next_action=data.get("next_action"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            duration_ms=data.get("duration_ms", 0),
            success=data.get("success", True),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )


class AuditLogger:
    """
    Audit logger for compliance and debugging.

    Logs all system events in a structured format.
    """

    def __init__(self, storage_dir: str = "./audit_logs"):
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._current_session: Optional[str] = None
        self._events: list[AuditEvent] = []

    def start_session(self, session_id: str, metadata: dict = None) -> None:
        """Start a new audit session."""
        self._current_session = session_id
        self._events = []
        self.log(
            AuditEventType.SESSION_START,
            actor="system",
            action="session_started",
            metadata=metadata or {},
        )

    def end_session(self, status: str = "completed") -> None:
        """End current audit session."""
        self.log(
            AuditEventType.SESSION_END,
            actor="system",
            action="session_ended",
            metadata={"status": status},
        )
        self._flush()
        self._current_session = None

    def log(
        self,
        event_type: AuditEventType,
        actor: str,
        action: str,
        input_data: Any = None,
        output_data: Any = None,
        decision: str = None,
        next_action: str = None,
        success: bool = True,
        error: str = None,
        metadata: dict = None,
    ) -> str:
        """Log an audit event."""
        event = AuditEvent(
            session_id=self._current_session or "",
            event_type=event_type,
            actor=actor,
            action=action,
            input_data=input_data,
            output_data=output_data,
            decision=decision,
            next_action=next_action,
            success=success,
            error=error,
            metadata=metadata or {},
        )

        self._events.append(event)
        self._write_event(event)

        return event.event_id

    def log_user_input(self, user_input: str) -> str:
        """Log user input event."""
        return self.log(
            AuditEventType.USER_INPUT,
            actor="user",
            action="message_received",
            input_data=user_input,
        )

    def log_agent_action(
        self,
        agent_name: str,
        action: str,
        input_data: Any = None,
        output_data: Any = None,
        decision: str = None,
        next_action: str = None,
    ) -> str:
        """Log agent action event."""
        return self.log(
            AuditEventType.AGENT_ACTION,
            actor=agent_name,
            action=action,
            input_data=input_data,
            output_data=output_data,
            decision=decision,
            next_action=next_action,
        )

    def log_tool_call(
        self,
        tool_name: str,
        input_data: Any,
        output_data: Any = None,
        success: bool = True,
        error: str = None,
        duration_ms: int = 0,
    ) -> str:
        """Log tool call event."""
        event = AuditEvent(
            session_id=self._current_session or "",
            event_type=AuditEventType.TOOL_CALL,
            actor=tool_name,
            action="tool_executed",
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
            success=success,
            error=error,
        )

        self._events.append(event)
        self._write_event(event)

        return event.event_id

    def log_decision(
        self,
        agent_name: str,
        decision: str,
        reasoning: str,
        next_action: str = None,
    ) -> str:
        """Log decision event."""
        return self.log(
            AuditEventType.DECISION,
            actor=agent_name,
            action="decision_made",
            decision=decision,
            next_action=next_action,
            metadata={"reasoning": reasoning},
        )

    def log_error(
        self,
        actor: str,
        error: str,
        context: dict = None,
    ) -> str:
        """Log error event."""
        return self.log(
            AuditEventType.ERROR,
            actor=actor,
            action="error_occurred",
            error=error,
            success=False,
            metadata=context or {},
        )

    def log_validation(
        self,
        validator: str,
        passed: bool,
        violations: list = None,
    ) -> str:
        """Log validation event."""
        return self.log(
            AuditEventType.VALIDATION,
            actor=validator,
            action="validation_performed",
            success=passed,
            metadata={"violations": violations or []},
        )

    def log_prompt_generated(
        self,
        prompt_length: int,
        sections: list = None,
    ) -> str:
        """Log prompt generation event."""
        return self.log(
            AuditEventType.PROMPT_GENERATED,
            actor="prompt_composer_agent",
            action="prompt_generated",
            metadata={
                "prompt_length": prompt_length,
                "sections": sections or [],
            },
        )

    def log_tools_generated(
        self,
        tool_count: int,
        tool_names: list = None,
    ) -> str:
        """Log tools generation event."""
        return self.log(
            AuditEventType.TOOLS_GENERATED,
            actor="tool_synthesizer_agent",
            action="tools_generated",
            metadata={
                "tool_count": tool_count,
                "tool_names": tool_names or [],
            },
        )

    def get_session_events(self, session_id: str = None) -> list[AuditEvent]:
        """Get all events for a session."""
        target_session = session_id or self._current_session
        return [e for e in self._events if e.session_id == target_session]

    def get_events_by_type(self, event_type: AuditEventType) -> list[AuditEvent]:
        """Get events by type."""
        return [e for e in self._events if e.event_type == event_type]

    def get_errors(self) -> list[AuditEvent]:
        """Get all error events."""
        return [e for e in self._events if not e.success or e.error]

    def export_session(self, session_id: str = None, format: str = "json") -> str:
        """Export session audit log."""
        events = self.get_session_events(session_id)

        if format == "json":
            return json.dumps([e.to_dict() for e in events], indent=2)
        else:
            # JSONL format
            lines = [json.dumps(e.to_dict()) for e in events]
            return "\n".join(lines)

    def _write_event(self, event: AuditEvent) -> None:
        """Write event to storage."""
        if not self._current_session:
            return

        file_path = self._storage_dir / f"{self._current_session}.jsonl"
        with open(file_path, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

    def _flush(self) -> None:
        """Flush events to storage."""
        # Events are written immediately, this is for any buffered operations
        pass

    def load_session(self, session_id: str) -> list[AuditEvent]:
        """Load session from storage."""
        file_path = self._storage_dir / f"{session_id}.jsonl"
        if not file_path.exists():
            return []

        events = []
        with open(file_path, "r") as f:
            for line in f:
                if line.strip():
                    events.append(AuditEvent.from_dict(json.loads(line)))

        return events

    def get_audit_summary(self, session_id: str = None) -> dict[str, Any]:
        """Get audit summary for session."""
        events = self.get_session_events(session_id)

        if not events:
            return {}

        return {
            "session_id": session_id or self._current_session,
            "total_events": len(events),
            "event_types": {
                et.name: len([e for e in events if e.event_type == et])
                for et in AuditEventType
            },
            "actors": list(set(e.actor for e in events)),
            "error_count": len(self.get_errors()),
            "start_time": events[0].timestamp.isoformat() if events else None,
            "end_time": events[-1].timestamp.isoformat() if events else None,
        }

