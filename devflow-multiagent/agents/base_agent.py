"""
Base Agent - Abstract Foundation for All DevFlow Agents

This module defines the core agent interface that all specialized
agents inherit from. Uses a novel state-machine pattern for
agent lifecycle management.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid


class AgentState(Enum):
    """Agent lifecycle states."""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentMessage:
    """
    Inter-agent communication message.
    Enables structured communication between agents.
    """
    sender: str
    receiver: str
    content: Any
    message_type: str  # "request", "response", "broadcast"
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 1  # 1=normal, 2=high, 3=urgent
    metadata: Dict = field(default_factory=dict)


@dataclass
class AgentContext:
    """
    Shared context passed between agents.
    Accumulates knowledge as query flows through system.
    """
    query_id: str
    original_query: str
    current_understanding: Dict = field(default_factory=dict)
    retrieved_context: List[Dict] = field(default_factory=list)
    execution_history: List[Dict] = field(default_factory=list)
    memory_recalls: List[Dict] = field(default_factory=list)
    critiques: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def add_execution(self, step: str, result: Any, success: bool):
        """Record an execution step."""
        self.execution_history.append({
            "step": step,
            "result": result,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_summary(self) -> str:
        """Get a summary of current context state."""
        return (
            f"Query: {self.original_query}\n"
            f"Understanding: {self.current_understanding}\n"
            f"Context items: {len(self.retrieved_context)}\n"
            f"Executions: {len(self.execution_history)}\n"
            f"Memory recalls: {len(self.memory_recalls)}"
        )


class BaseAgent(ABC):
    """
    Abstract base class for all DevFlow agents.
    
    Implements a novel pattern where agents:
    1. Maintain their own state
    2. Communicate via messages
    3. Can request help from other agents
    4. Track their own performance metrics
    """
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.state = AgentState.IDLE
        self.message_queue: List[AgentMessage] = []
        self.metrics = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "avg_time_ms": 0
        }
        self._start_time: Optional[datetime] = None
    
    @property
    def display_name(self) -> str:
        """Human-readable agent name for logging."""
        return f"[{self.agent_name}]"
    
    def transition_state(self, new_state: AgentState):
        """Transition to a new state with validation."""
        valid_transitions = {
            AgentState.IDLE: [AgentState.PROCESSING],
            AgentState.PROCESSING: [AgentState.WAITING, AgentState.COMPLETED, AgentState.FAILED],
            AgentState.WAITING: [AgentState.PROCESSING, AgentState.COMPLETED],
            AgentState.COMPLETED: [AgentState.IDLE],
            AgentState.FAILED: [AgentState.IDLE]
        }
        
        if new_state in valid_transitions.get(self.state, []):
            self.state = new_state
        else:
            raise ValueError(
                f"Invalid state transition: {self.state} -> {new_state}"
            )
    
    def start_processing(self):
        """Begin processing, record start time."""
        self._start_time = datetime.now()
        self.transition_state(AgentState.PROCESSING)
    
    def finish_processing(self, success: bool):
        """Complete processing, update metrics."""
        if self._start_time:
            elapsed = (datetime.now() - self._start_time).total_seconds() * 1000
            # Update running average
            total = self.metrics["processed"]
            self.metrics["avg_time_ms"] = (
                (self.metrics["avg_time_ms"] * total + elapsed) / (total + 1)
            )
        
        self.metrics["processed"] += 1
        if success:
            self.metrics["succeeded"] += 1
            self.transition_state(AgentState.COMPLETED)
        else:
            self.metrics["failed"] += 1
            self.transition_state(AgentState.FAILED)
        
        # Reset to idle
        self.state = AgentState.IDLE
    
    def receive_message(self, message: AgentMessage):
        """Add message to queue for processing."""
        self.message_queue.append(message)
    
    def create_message(
        self, 
        receiver: str, 
        content: Any, 
        message_type: str = "request"
    ) -> AgentMessage:
        """Create a new message to send to another agent."""
        return AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            content=content,
            message_type=message_type
        )
    
    @abstractmethod
    async def process(self, context: AgentContext) -> Dict[str, Any]:
        """
        Main processing method - must be implemented by subclasses.
        
        Args:
            context: Shared context with accumulated knowledge
            
        Returns:
            Dict with processing results
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides."""
        pass
    
    def get_metrics_summary(self) -> Dict:
        """Return performance metrics."""
        success_rate = (
            self.metrics["succeeded"] / max(1, self.metrics["processed"]) * 100
        )
        return {
            **self.metrics,
            "success_rate": f"{success_rate:.1f}%"
        }

