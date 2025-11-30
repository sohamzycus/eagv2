"""
Coordinator/Orchestrator - Central Control for Multi-Agent System

This is the brain of DevFlow. It:
- Routes queries through the agent pipeline
- Manages agent communication
- Handles plan execution and rewriting
- Coordinates between all specialized agents

Architecture matches the diagram:
    Coordinator
        │
    ┌───┴───┬───────┬────────┐
    ▼       ▼       ▼        ▼
Perception Retriever Critic Memory
        │       │       │
        └───┬───┘       │
            ▼           │
       Plan/Step◄───────┘
            │
            ▼
        Executor
            │
            ▼
      Decision Agent
"""

import uuid
import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from agents import (
    AgentContext,
    PerceptionAgent,
    RetrieverAgent,
    CriticAgent,
    MemoryAgent,
    DecisionAgent,
    CritiqueVerdict
)


class PipelineStage(Enum):
    """Stages in the processing pipeline."""
    PERCEPTION = "perception"
    RETRIEVAL = "retrieval"
    MEMORY = "memory"
    PLANNING = "planning"
    EXECUTION = "execution"
    CRITIQUE = "critique"
    REPLAN = "replan"
    DECISION = "decision"
    COMPLETE = "complete"


@dataclass
class PipelineState:
    """Current state of the pipeline."""
    stage: PipelineStage
    query_id: str
    start_time: datetime
    stage_history: List[Dict] = field(default_factory=list)
    replan_count: int = 0
    max_replans: int = 2
    
    def advance_to(self, stage: PipelineStage, result: Dict = None):
        """Move to next stage, recording history."""
        self.stage_history.append({
            "from": self.stage.value,
            "to": stage.value,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        self.stage = stage


@dataclass
class Plan:
    """Execution plan generated from perception."""
    plan_id: str
    steps: List[Dict]  # {"action": str, "params": Dict, "expected": str}
    current_step: int = 0
    completed_steps: List[Dict] = field(default_factory=list)
    
    @property
    def is_complete(self) -> bool:
        return self.current_step >= len(self.steps)
    
    @property
    def next_step(self) -> Optional[Dict]:
        if self.is_complete:
            return None
        return self.steps[self.current_step]


class Orchestrator:
    """
    Central coordinator for the multi-agent system.
    
    Implements the coordination pattern from the architecture:
    1. Perception → Understand query
    2. Retriever → Gather context (parallel with Memory)
    3. Memory → Recall similar past queries
    4. Plan/Step → Create execution plan
    5. Executor → Execute steps
    6. Critic → Validate output
    7. Replan (if needed) → Modify plan
    8. Decision → Generate final response
    """
    
    def __init__(self, workspace_path: str = None):
        # Initialize all agents
        self.perception = PerceptionAgent()
        self.retriever = RetrieverAgent(workspace_path)
        self.critic = CriticAgent(strictness="medium")
        self.memory = MemoryAgent()
        self.decision = DecisionAgent()
        
        self.agents = {
            "perception": self.perception,
            "retriever": self.retriever,
            "critic": self.critic,
            "memory": self.memory,
            "decision": self.decision
        }
        
        self.current_plan: Optional[Plan] = None
        self.pipeline_state: Optional[PipelineState] = None
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main entry point - process a query through the full pipeline.
        
        Returns structured result with response and metadata.
        """
        # Initialize pipeline
        query_id = str(uuid.uuid4())[:8]
        context = AgentContext(
            query_id=query_id,
            original_query=query
        )
        
        self.pipeline_state = PipelineState(
            stage=PipelineStage.PERCEPTION,
            query_id=query_id,
            start_time=datetime.now()
        )
        
        try:
            # Stage 1: Perception - Understand the query
            perception_result = await self._run_perception(context)
            
            if not perception_result["success"]:
                return self._error_response(
                    "Failed to understand query", 
                    perception_result
                )
            
            # Stage 2 & 3: Parallel - Retrieval and Memory
            retrieval_result, memory_result = await asyncio.gather(
                self._run_retrieval(context),
                self._run_memory(context)
            )
            
            # Stage 4: Planning - Create execution plan
            self.current_plan = self._create_plan(context)
            
            # Stage 5 & 6: Execution Loop with Critic
            final_result = await self._execute_with_critique(context)
            
            # Stage 7: Decision - Generate final response
            decision_result = await self._run_decision(context)
            
            # Store successful interaction in memory
            if decision_result.get("success"):
                self.memory.store_interaction(
                    query=query,
                    intent=context.current_understanding.get("intent", "unknown"),
                    response=decision_result.get("response", ""),
                    quality_score=decision_result.get("confidence", 0.5)
                )
                self.memory.save_session()
            
            return {
                "success": True,
                "query_id": query_id,
                "response": decision_result.get("response", ""),
                "response_type": decision_result.get("response_type", "final"),
                "confidence": decision_result.get("confidence", 0.0),
                "followups": decision_result.get("followups", []),
                "pipeline": self._get_pipeline_summary(),
                "execution_time_ms": self._get_execution_time()
            }
            
        except Exception as e:
            return self._error_response(str(e), {"exception": True})
    
    async def _run_perception(self, context: AgentContext) -> Dict:
        """Run perception stage."""
        self.pipeline_state.advance_to(PipelineStage.PERCEPTION)
        result = await self.perception.process(context)
        self.pipeline_state.advance_to(PipelineStage.RETRIEVAL, result)
        return result
    
    async def _run_retrieval(self, context: AgentContext) -> Dict:
        """Run retrieval stage."""
        result = await self.retriever.process(context)
        return result
    
    async def _run_memory(self, context: AgentContext) -> Dict:
        """Run memory stage."""
        self.pipeline_state.advance_to(PipelineStage.MEMORY)
        result = await self.memory.process(context)
        return result
    
    def _create_plan(self, context: AgentContext) -> Plan:
        """Create execution plan based on intent."""
        self.pipeline_state.advance_to(PipelineStage.PLANNING)
        
        intent = context.current_understanding.get("intent", "general_help")
        entities = context.current_understanding.get("entities", {})
        
        # Intent-specific plan templates
        plan_templates = {
            "standup_summary": [
                {"action": "fetch_git_commits", "params": {"days": 1}},
                {"action": "summarize_commits", "params": {}},
                {"action": "format_standup", "params": {}}
            ],
            "pr_description": [
                {"action": "get_branch_changes", "params": {}},
                {"action": "analyze_changes", "params": {}},
                {"action": "generate_description", "params": {}}
            ],
            "code_review": [
                {"action": "load_files", "params": {"paths": entities.get("file_path", [])}},
                {"action": "analyze_code", "params": {}},
                {"action": "generate_feedback", "params": {}}
            ],
            "tech_debt": [
                {"action": "scan_codebase", "params": {}},
                {"action": "calculate_metrics", "params": {}},
                {"action": "prioritize_debt", "params": {}}
            ],
            "dependency_check": [
                {"action": "find_manifests", "params": {}},
                {"action": "check_vulnerabilities", "params": {}},
                {"action": "suggest_updates", "params": {}}
            ],
            "documentation": [
                {"action": "parse_code", "params": {}},
                {"action": "extract_signatures", "params": {}},
                {"action": "generate_docs", "params": {}}
            ]
        }
        
        steps = plan_templates.get(intent, [
            {"action": "analyze_query", "params": {}},
            {"action": "generate_response", "params": {}}
        ])
        
        return Plan(
            plan_id=f"plan_{context.query_id}",
            steps=steps
        )
    
    async def _execute_with_critique(self, context: AgentContext) -> Dict:
        """Execute plan steps with critic validation."""
        self.pipeline_state.advance_to(PipelineStage.EXECUTION)
        
        max_iterations = 5
        iteration = 0
        
        while not self.current_plan.is_complete and iteration < max_iterations:
            step = self.current_plan.next_step
            
            # Execute current step
            step_result = await self._execute_step(step, context)
            context.add_execution(
                step=step["action"],
                result=step_result,
                success=True
            )
            
            # Advance plan
            self.current_plan.completed_steps.append({
                "step": step,
                "result": step_result
            })
            self.current_plan.current_step += 1
            
            iteration += 1
        
        # Run critic on final result
        self.pipeline_state.advance_to(PipelineStage.CRITIQUE)
        critique_result = await self.critic.process(context)
        
        # Check if replan is needed
        if critique_result.get("should_replan"):
            if self.pipeline_state.replan_count < self.pipeline_state.max_replans:
                self.pipeline_state.replan_count += 1
                self.pipeline_state.advance_to(PipelineStage.REPLAN)
                
                # Create new plan
                self.current_plan = self._replan(context, critique_result)
                
                # Re-execute (recursive)
                return await self._execute_with_critique(context)
        
        return critique_result
    
    async def _execute_step(self, step: Dict, context: AgentContext) -> Any:
        """Execute a single plan step."""
        action = step.get("action", "")
        params = step.get("params", {})
        
        # Simplified execution - returns context-based result
        # In full implementation, this would dispatch to actual tools
        return {
            "action": action,
            "status": "completed",
            "data": context.retrieved_context[:3]  # Use retrieved context
        }
    
    def _replan(self, context: AgentContext, critique: Dict) -> Plan:
        """Create new plan based on critique feedback."""
        suggestions = critique.get("suggestions", [])
        
        # Add improvement steps based on suggestions
        improvement_steps = []
        for suggestion in suggestions:
            if "detail" in suggestion.lower():
                improvement_steps.append({
                    "action": "expand_detail", 
                    "params": {}
                })
            elif "format" in suggestion.lower():
                improvement_steps.append({
                    "action": "reformat_output",
                    "params": {}
                })
        
        # Combine with existing completed steps
        new_steps = [
            *[s["step"] for s in self.current_plan.completed_steps],
            *improvement_steps,
            {"action": "finalize", "params": {}}
        ]
        
        return Plan(
            plan_id=f"replan_{context.query_id}_{self.pipeline_state.replan_count}",
            steps=new_steps
        )
    
    async def _run_decision(self, context: AgentContext) -> Dict:
        """Run decision stage."""
        self.pipeline_state.advance_to(PipelineStage.DECISION)
        result = await self.decision.process(context)
        self.pipeline_state.advance_to(PipelineStage.COMPLETE, result)
        return result
    
    def _error_response(self, message: str, details: Dict) -> Dict:
        """Generate error response."""
        return {
            "success": False,
            "error": message,
            "details": details,
            "pipeline": self._get_pipeline_summary() if self.pipeline_state else {}
        }
    
    def _get_pipeline_summary(self) -> Dict:
        """Get summary of pipeline execution."""
        if not self.pipeline_state:
            return {}
        
        return {
            "query_id": self.pipeline_state.query_id,
            "final_stage": self.pipeline_state.stage.value,
            "stages_traversed": len(self.pipeline_state.stage_history),
            "replans": self.pipeline_state.replan_count,
            "history": [
                {"stage": h["from"], "to": h["to"]} 
                for h in self.pipeline_state.stage_history
            ]
        }
    
    def _get_execution_time(self) -> int:
        """Get total execution time in milliseconds."""
        if not self.pipeline_state:
            return 0
        
        elapsed = datetime.now() - self.pipeline_state.start_time
        return int(elapsed.total_seconds() * 1000)
    
    def get_agent_metrics(self) -> Dict[str, Dict]:
        """Get metrics from all agents."""
        return {
            name: agent.get_metrics_summary()
            for name, agent in self.agents.items()
        }

