"""
Database module for storing prompts, history, and agent trails.
Uses SQLite for simplicity - can be swapped for PostgreSQL in production.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class PromptRecord:
    """A saved prompt record."""
    id: str
    name: str
    description: str
    prompt_text: str
    tools_json: str
    domain: str
    created_at: str
    updated_at: str
    version: int = 1
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AgentTrail:
    """A single step in the agent's reasoning trail."""
    id: str
    session_id: str
    step_number: int
    agent_name: str
    action: str
    input_text: str
    output_text: str
    thinking: str
    timestamp: str
    duration_ms: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SessionHistory:
    """A conversation session."""
    id: str
    user_input: str
    generated_prompt_id: Optional[str]
    status: str
    created_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class Database:
    """SQLite database for prompt storage and history."""
    
    def __init__(self, db_path: str = "prompt_creator.db"):
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def _get_conn(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database tables."""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    prompt_text TEXT NOT NULL,
                    tools_json TEXT,
                    domain TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version INTEGER DEFAULT 1
                );
                
                CREATE TABLE IF NOT EXISTS agent_trails (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    step_number INTEGER NOT NULL,
                    agent_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    input_text TEXT,
                    output_text TEXT,
                    thinking TEXT,
                    timestamp TEXT NOT NULL,
                    duration_ms INTEGER DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_input TEXT,
                    generated_prompt_id TEXT,
                    status TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (generated_prompt_id) REFERENCES prompts(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_trails_session ON agent_trails(session_id);
                CREATE INDEX IF NOT EXISTS idx_prompts_domain ON prompts(domain);
            """)
    
    # Prompt operations
    def save_prompt(self, record: PromptRecord) -> str:
        """Save a prompt record."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO prompts 
                (id, name, description, prompt_text, tools_json, domain, created_at, updated_at, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id, record.name, record.description, record.prompt_text,
                record.tools_json, record.domain, record.created_at, record.updated_at, record.version
            ))
        return record.id
    
    def get_prompt(self, prompt_id: str) -> Optional[PromptRecord]:
        """Get a prompt by ID."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,)).fetchone()
            if row:
                return PromptRecord(**dict(row))
        return None
    
    def list_prompts(self, domain: Optional[str] = None, limit: int = 50) -> List[PromptRecord]:
        """List saved prompts."""
        with self._get_conn() as conn:
            if domain:
                rows = conn.execute(
                    "SELECT * FROM prompts WHERE domain = ? ORDER BY updated_at DESC LIMIT ?",
                    (domain, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM prompts ORDER BY updated_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [PromptRecord(**dict(row)) for row in rows]
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        return True
    
    # Agent trail operations
    def save_trail(self, trail: AgentTrail) -> str:
        """Save an agent trail step."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO agent_trails 
                (id, session_id, step_number, agent_name, action, input_text, output_text, thinking, timestamp, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trail.id, trail.session_id, trail.step_number, trail.agent_name,
                trail.action, trail.input_text, trail.output_text, trail.thinking,
                trail.timestamp, trail.duration_ms
            ))
        return trail.id
    
    def get_session_trails(self, session_id: str) -> List[AgentTrail]:
        """Get all trails for a session."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM agent_trails WHERE session_id = ? ORDER BY step_number",
                (session_id,)
            ).fetchall()
            return [AgentTrail(**dict(row)) for row in rows]
    
    # Session operations
    def save_session(self, session: SessionHistory) -> str:
        """Save a session."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sessions (id, user_input, generated_prompt_id, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (session.id, session.user_input, session.generated_prompt_id, session.status, session.created_at))
        return session.id
    
    def get_recent_sessions(self, limit: int = 20) -> List[SessionHistory]:
        """Get recent sessions."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [SessionHistory(**dict(row)) for row in rows]


# Global database instance
_db: Optional[Database] = None


def get_db(db_path: str = "prompt_creator.db") -> Database:
    """Get or create database instance."""
    global _db
    if _db is None:
        _db = Database(db_path)
    return _db


