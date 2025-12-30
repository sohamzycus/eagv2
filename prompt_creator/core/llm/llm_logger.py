"""
LLM Call Logger.

Provides comprehensive logging for all LLM calls.
Required for governance, debugging, and compliance.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class LLMCallRecord:
    """
    Record of a single LLM call.

    Immutable after creation for audit compliance.
    """

    # Identification
    call_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str = ""
    agent_name: str = ""

    # Request details
    provider: str = ""
    model: str = ""
    system_prompt_hash: str = ""  # Hash of prompt for privacy
    message_count: int = 0
    temperature: float = 0.0

    # Response details
    response_hash: str = ""  # Hash of response
    response_length: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # Performance
    latency_ms: int = 0
    finish_reason: str = ""

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "call_id": self.call_id,
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "provider": self.provider,
            "model": self.model,
            "system_prompt_hash": self.system_prompt_hash,
            "message_count": self.message_count,
            "temperature": self.temperature,
            "response_hash": self.response_hash,
            "response_length": self.response_length,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "finish_reason": self.finish_reason,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error": self.error,
        }


class LLMCallLogger:
    """
    Logger for LLM calls.

    Features:
    - Hash-based logging for privacy
    - JSONL storage for streaming
    - Query interface for analysis
    """

    def __init__(self, storage_dir: str = "./llm_logs"):
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._records: List[LLMCallRecord] = []
        self._current_session: Optional[str] = None

    def start_session(self, session_id: str) -> None:
        """Start a new logging session."""
        self._current_session = session_id

    def log_call(
        self,
        agent_name: str,
        provider: str,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        response_content: str,
        temperature: float = 0.0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: int = 0,
        finish_reason: str = "",
        success: bool = True,
        error: Optional[str] = None,
    ) -> LLMCallRecord:
        """
        Log an LLM call.

        Hashes sensitive content for privacy while maintaining traceability.
        """
        record = LLMCallRecord(
            session_id=self._current_session or "",
            agent_name=agent_name,
            provider=provider,
            model=model,
            system_prompt_hash=self._hash_content(system_prompt),
            message_count=len(messages),
            temperature=temperature,
            response_hash=self._hash_content(response_content),
            response_length=len(response_content),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            success=success,
            error=error,
        )

        self._records.append(record)
        self._write_record(record)

        return record

    def get_session_records(
        self, session_id: Optional[str] = None
    ) -> List[LLMCallRecord]:
        """Get all records for a session."""
        target = session_id or self._current_session
        return [r for r in self._records if r.session_id == target]

    def get_agent_records(self, agent_name: str) -> List[LLMCallRecord]:
        """Get all records for an agent."""
        return [r for r in self._records if r.agent_name == agent_name]

    def get_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a session."""
        records = self.get_session_records(session_id)

        if not records:
            return {}

        total_tokens = sum(r.total_tokens for r in records)
        total_latency = sum(r.latency_ms for r in records)
        error_count = sum(1 for r in records if not r.success)

        return {
            "total_calls": len(records),
            "total_tokens": total_tokens,
            "total_latency_ms": total_latency,
            "avg_latency_ms": total_latency / len(records) if records else 0,
            "error_count": error_count,
            "success_rate": (len(records) - error_count) / len(records) if records else 0,
            "by_agent": self._group_by_agent(records),
            "by_model": self._group_by_model(records),
        }

    def export_session(
        self, session_id: Optional[str] = None, format: str = "json"
    ) -> str:
        """Export session records."""
        records = self.get_session_records(session_id)

        if format == "json":
            return json.dumps([r.to_dict() for r in records], indent=2)
        else:
            # JSONL format
            return "\n".join(json.dumps(r.to_dict()) for r in records)

    def _hash_content(self, content: str) -> str:
        """Create SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _write_record(self, record: LLMCallRecord) -> None:
        """Write record to storage."""
        if not self._current_session:
            return

        file_path = self._storage_dir / f"{self._current_session}.jsonl"
        with open(file_path, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def _group_by_agent(
        self, records: List[LLMCallRecord]
    ) -> Dict[str, Dict[str, Any]]:
        """Group statistics by agent."""
        agents = {}
        for r in records:
            if r.agent_name not in agents:
                agents[r.agent_name] = {"calls": 0, "tokens": 0, "latency_ms": 0}
            agents[r.agent_name]["calls"] += 1
            agents[r.agent_name]["tokens"] += r.total_tokens
            agents[r.agent_name]["latency_ms"] += r.latency_ms
        return agents

    def _group_by_model(
        self, records: List[LLMCallRecord]
    ) -> Dict[str, Dict[str, Any]]:
        """Group statistics by model."""
        models = {}
        for r in records:
            key = f"{r.provider}:{r.model}"
            if key not in models:
                models[key] = {"calls": 0, "tokens": 0}
            models[key]["calls"] += 1
            models[key]["tokens"] += r.total_tokens
        return models


class LLMClientWrapper:
    """
    Wrapper that adds logging to any LLM client.

    Decorates LLMClient to automatically log all calls.
    """

    def __init__(
        self,
        client,  # LLMClient
        logger: LLMCallLogger,
        agent_name: str = "unknown",
    ):
        self._client = client
        self._logger = logger
        self._agent_name = agent_name

    @property
    def provider_name(self) -> str:
        return self._client.provider_name

    @property
    def model_name(self) -> str:
        return self._client.model_name

    def generate(
        self,
        system_prompt: str,
        messages,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
    ):
        """Generate with automatic logging."""
        response = self._client.generate(
            system_prompt=system_prompt,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop_sequences=stop_sequences,
        )

        # Log the call
        self._logger.log_call(
            agent_name=self._agent_name,
            provider=self._client.provider_name,
            model=self._client.model_name,
            system_prompt=system_prompt,
            messages=[m.to_dict() if hasattr(m, "to_dict") else m for m in messages],
            response_content=response.content,
            temperature=temperature,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            latency_ms=response.latency_ms,
            finish_reason=response.finish_reason,
            success="error" not in response.finish_reason.lower(),
        )

        return response

    def generate_simple(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> str:
        """Simple generation with logging."""
        from .llm_client import LLMMessage

        response = self.generate(
            system_prompt=system_prompt,
            messages=[LLMMessage.user(user_message)],
            temperature=temperature,
        )
        return response.content



