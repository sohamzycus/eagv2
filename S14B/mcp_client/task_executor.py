"""
Task Executor - Executes computer tasks in N steps using fDOM + Ollama
Provides the main execution loop for automated GUI tasks
"""

import json
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from enum import Enum

from .ollama_client import OllamaClient, ComputerAction, FDOMElement
from .mcp_server import MCPServer, FDOMContext


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class TaskStep:
    """Represents a single step in a task"""
    step_number: int
    action: ComputerAction
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


@dataclass
class TaskExecution:
    """Represents a complete task execution"""
    task_id: str
    task_description: str
    steps: List[TaskStep]
    max_steps: int
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    initial_state: str = "root"
    final_state: str = "root"
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "task_description": self.task_description,
            "steps": [
                {
                    "step_number": s.step_number,
                    "action_type": s.action.action_type,
                    "target": s.action.target_element or s.action.target_state,
                    "reasoning": s.action.reasoning,
                    "status": s.status.value,
                    "result": s.result,
                    "error": s.error
                }
                for s in self.steps
            ],
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "initial_state": self.initial_state,
            "final_state": self.final_state
        }


class TaskExecutor:
    """
    Executes computer tasks using fDOM state machine and Ollama planning
    Supports configurable step counts and execution strategies
    """
    
    def __init__(self, 
                 app_name: str,
                 ollama_model: str = "llama3.2:latest",
                 step_delay: float = 1.0,
                 on_step_complete: Callable = None):
        
        self.app_name = app_name
        self.step_delay = step_delay
        self.on_step_complete = on_step_complete
        
        # Initialize components
        self.context = FDOMContext(app_name)
        self.mcp_server = MCPServer(self.context)
        self.ollama = OllamaClient(model=ollama_model)
        
        # Execution state
        self.current_execution: Optional[TaskExecution] = None
        self.execution_history: List[TaskExecution] = []
        self.is_paused = False
        
    def check_ollama(self) -> Dict:
        """Check if Ollama is available"""
        return self.ollama.check_ollama_status()
    
    async def execute_task(self, 
                           task_description: str, 
                           max_steps: int = 5,
                           dry_run: bool = False) -> TaskExecution:
        """
        Execute a computer task in up to max_steps steps
        
        Args:
            task_description: Natural language description of the task
            max_steps: Maximum number of steps (default 5)
            dry_run: If True, plan but don't execute
            
        Returns:
            TaskExecution with results
        """
        
        # Create execution record
        execution = TaskExecution(
            task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            task_description=task_description,
            steps=[],
            max_steps=max_steps,
            status=TaskStatus.RUNNING,
            start_time=datetime.now(),
            initial_state=self.context.current_state
        )
        self.current_execution = execution
        
        print(f"\n{'='*60}")
        print(f"🎯 TASK: {task_description}")
        print(f"📊 Max Steps: {max_steps}")
        print(f"📍 Starting State: {self.context.current_state}")
        print(f"{'='*60}\n")
        
        try:
            # Plan the task using Ollama
            print("🧠 Planning task with Ollama...")
            planned_actions = self.ollama.plan_task(
                task_description,
                self.context.fdom_data,
                self.context.current_state,
                max_steps=max_steps
            )
            
            if not planned_actions:
                print("⚠️ No actions planned. Using fallback exploration.")
                # Fallback: try to find relevant elements
                planned_actions = await self._create_fallback_plan(task_description, max_steps)
            
            print(f"📋 Planned {len(planned_actions)} steps\n")
            
            # Execute each step
            for i, action in enumerate(planned_actions):
                if self.is_paused:
                    execution.status = TaskStatus.PAUSED
                    break
                
                step = TaskStep(
                    step_number=i + 1,
                    action=action,
                    status=TaskStatus.RUNNING,
                    start_time=datetime.now()
                )
                execution.steps.append(step)
                
                print(f"🔹 Step {step.step_number}/{max_steps}: {action.action_type}")
                print(f"   Target: {action.target_element or action.target_state or 'N/A'}")
                print(f"   Reasoning: {action.reasoning[:100]}...")
                
                if not dry_run:
                    # Execute the action
                    result = await self._execute_action(action)
                    step.result = result
                    
                    if result.get("success"):
                        step.status = TaskStatus.COMPLETED
                        print(f"   ✅ Success: {result.get('message', 'Done')}")
                    else:
                        step.status = TaskStatus.FAILED
                        step.error = result.get("error", "Unknown error")
                        print(f"   ❌ Failed: {step.error}")
                else:
                    step.status = TaskStatus.COMPLETED
                    step.result = {"dry_run": True}
                    print(f"   📝 [DRY RUN] Would execute")
                
                step.end_time = datetime.now()
                
                # Callback
                if self.on_step_complete:
                    self.on_step_complete(step)
                
                # Delay between steps
                if i < len(planned_actions) - 1:
                    await asyncio.sleep(self.step_delay)
            
            # Finalize execution
            execution.end_time = datetime.now()
            execution.final_state = self.context.current_state
            
            failed_steps = sum(1 for s in execution.steps if s.status == TaskStatus.FAILED)
            if failed_steps == 0:
                execution.status = TaskStatus.COMPLETED
            elif failed_steps == len(execution.steps):
                execution.status = TaskStatus.FAILED
            else:
                execution.status = TaskStatus.COMPLETED  # Partial success
            
            print(f"\n{'='*60}")
            print(f"✨ Task {'COMPLETED' if execution.status == TaskStatus.COMPLETED else 'FINISHED'}")
            print(f"📊 Steps: {len(execution.steps)}/{max_steps}")
            print(f"✅ Successful: {len(execution.steps) - failed_steps}")
            print(f"❌ Failed: {failed_steps}")
            print(f"📍 Final State: {execution.final_state}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.end_time = datetime.now()
            print(f"❌ Task execution failed: {e}")
        
        self.execution_history.append(execution)
        self.current_execution = None
        
        return execution
    
    async def _execute_action(self, action: ComputerAction) -> Dict:
        """Execute a single action using MCP server"""
        
        if action.action_type == "click":
            if not action.target_element:
                return {"success": False, "error": "No target element specified"}
            
            result = await self.mcp_server.handle_tool_call(
                "click_element",
                {"element_id": action.target_element}
            )
            
            if result.get("state_changed"):
                self.context.set_current_state(result.get("new_state", self.context.current_state))
            
            return {
                "success": "error" not in result,
                "message": f"Clicked {result.get('element_clicked', 'unknown')}",
                "state_changed": result.get("state_changed", False),
                "new_state": result.get("new_state")
            }
        
        elif action.action_type == "navigate":
            if not action.target_state:
                return {"success": False, "error": "No target state specified"}
            
            result = await self.mcp_server.handle_tool_call(
                "navigate_to_state",
                {"state_id": action.target_state}
            )
            
            return {
                "success": result.get("success", False),
                "message": f"Navigated to {action.target_state}",
                "new_state": action.target_state
            }
        
        elif action.action_type == "type":
            # Note: Typing not fully implemented in simulation
            return {
                "success": True,
                "message": f"Would type: {action.text_input}",
                "simulated": True
            }
        
        elif action.action_type == "scroll":
            return {
                "success": True,
                "message": "Scroll action simulated",
                "simulated": True
            }
        
        return {"success": False, "error": f"Unknown action type: {action.action_type}"}
    
    async def _create_fallback_plan(self, task_description: str, max_steps: int) -> List[ComputerAction]:
        """Create a fallback plan when Ollama doesn't return valid actions"""
        
        # Get current elements
        elements = self.context.get_elements_in_state()
        interactive_elements = [
            e for e in elements 
            if e.get("interactive") and e.get("enabled") and e.get("name", "").lower() != "unanalyzed"
        ]
        
        # Simple keyword matching
        keywords = task_description.lower().split()
        
        actions = []
        for elem in interactive_elements[:max_steps]:
            elem_name = elem.get("name", "").lower()
            
            # Check if element matches any keyword
            if any(kw in elem_name for kw in keywords) or len(actions) < 2:
                action = ComputerAction(
                    action_type="click",
                    target_element=elem["id"],
                    reasoning=f"Clicking '{elem.get('name')}' - matches task keywords",
                    confidence=0.3
                )
                actions.append(action)
        
        return actions
    
    def pause(self):
        """Pause current execution"""
        self.is_paused = True
    
    def resume(self):
        """Resume execution"""
        self.is_paused = False
    
    def get_execution_summary(self) -> Dict:
        """Get summary of all executions"""
        return {
            "total_executions": len(self.execution_history),
            "completed": sum(1 for e in self.execution_history if e.status == TaskStatus.COMPLETED),
            "failed": sum(1 for e in self.execution_history if e.status == TaskStatus.FAILED),
            "total_steps_executed": sum(len(e.steps) for e in self.execution_history),
            "executions": [e.to_dict() for e in self.execution_history[-10:]]  # Last 10
        }


class ExplorationExecutor:
    """
    Executes systematic exploration of an application
    Supports configurable iteration counts (e.g., 50 iterations)
    """
    
    def __init__(self,
                 app_name: str,
                 ollama_model: str = "llama3.2:latest",
                 iteration_delay: float = 2.0,
                 on_iteration_complete: Callable = None):
        
        self.app_name = app_name
        self.iteration_delay = iteration_delay
        self.on_iteration_complete = on_iteration_complete
        
        # Initialize components
        self.context = FDOMContext(app_name)
        self.mcp_server = MCPServer(self.context)
        self.ollama = OllamaClient(model=ollama_model)
        
        # Exploration state
        self.explored_nodes: set = set()
        self.pending_nodes: set = set()
        self.iteration_results: List[Dict] = []
        self.is_running = False
        
        # Load initial pending nodes
        self._load_pending_nodes()
    
    def _load_pending_nodes(self):
        """Load pending nodes from fDOM"""
        states = self.context.fdom_data.get("states", {})
        
        for state_id, state_data in states.items():
            nodes = state_data.get("nodes", {})
            for node_id, node_data in nodes.items():
                full_id = f"{state_id}::{node_id}"
                
                if (node_data.get("status") == "pending" and
                    node_data.get("g_icon_name", "").lower() != "unanalyzed" and
                    node_data.get("g_enabled", True) and
                    node_data.get("g_interactive", True)):
                    self.pending_nodes.add(full_id)
                elif node_data.get("status") == "explored":
                    self.explored_nodes.add(full_id)
    
    async def run_exploration(self, 
                               max_iterations: int = 50,
                               use_ollama_guidance: bool = True) -> Dict:
        """
        Run automated exploration for specified iterations
        
        Args:
            max_iterations: Maximum number of exploration iterations (default 50)
            use_ollama_guidance: Whether to use Ollama to guide exploration
            
        Returns:
            Summary of exploration results
        """
        
        self.is_running = True
        start_time = datetime.now()
        
        print(f"\n{'='*70}")
        print(f"🔍 AUTOMATED EXPLORATION")
        print(f"{'='*70}")
        print(f"📱 App: {self.app_name}")
        print(f"🔄 Iterations: {max_iterations}")
        print(f"🧠 Ollama Guidance: {'Enabled' if use_ollama_guidance else 'Disabled'}")
        print(f"📊 Pending Nodes: {len(self.pending_nodes)}")
        print(f"✅ Already Explored: {len(self.explored_nodes)}")
        print(f"{'='*70}\n")
        
        iterations_completed = 0
        successful_explorations = 0
        state_changes = 0
        errors = 0
        
        try:
            for iteration in range(1, max_iterations + 1):
                if not self.is_running:
                    print(f"\n⏹️ Exploration stopped by user")
                    break
                
                if not self.pending_nodes:
                    print(f"\n✅ All nodes explored! Stopping early.")
                    break
                
                print(f"\n--- Iteration {iteration}/{max_iterations} ---")
                print(f"📊 Pending: {len(self.pending_nodes)} | Explored: {len(self.explored_nodes)}")
                
                # Select next node to explore
                if use_ollama_guidance:
                    action = self.ollama.decide_next_exploration_action(
                        self.context.fdom_data,
                        self.context.current_state,
                        self.explored_nodes,
                        self.pending_nodes
                    )
                    
                    if action and action.target_element:
                        target_node = action.target_element
                        reasoning = action.reasoning
                    else:
                        # Fallback to first pending
                        target_node = next(iter(self.pending_nodes))
                        reasoning = "Fallback selection"
                else:
                    # Simple sequential selection
                    target_node = next(iter(self.pending_nodes))
                    reasoning = "Sequential selection"
                
                print(f"🎯 Target: {target_node}")
                print(f"💭 Reason: {reasoning[:80]}...")
                
                # Execute click
                result = await self.mcp_server.handle_tool_call(
                    "click_element",
                    {"element_id": target_node}
                )
                
                iteration_result = {
                    "iteration": iteration,
                    "target_node": target_node,
                    "reasoning": reasoning,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
                
                if result.get("success") or "error" not in result:
                    successful_explorations += 1
                    
                    # Mark as explored
                    self.pending_nodes.discard(target_node)
                    self.explored_nodes.add(target_node)
                    
                    if result.get("state_changed"):
                        state_changes += 1
                        new_state = result.get("new_state")
                        print(f"✅ State changed → {new_state}")
                        self.context.set_current_state(new_state)
                        
                        # Load new pending nodes from new state
                        self._load_pending_from_state(new_state)
                    else:
                        print(f"✅ Clicked: {result.get('element_clicked', 'unknown')}")
                else:
                    errors += 1
                    print(f"❌ Error: {result.get('error', 'Unknown')}")
                    # Remove from pending anyway to avoid infinite loops
                    self.pending_nodes.discard(target_node)
                
                self.iteration_results.append(iteration_result)
                iterations_completed += 1
                
                # Callback
                if self.on_iteration_complete:
                    self.on_iteration_complete(iteration_result)
                
                # Delay
                await asyncio.sleep(self.iteration_delay)
        
        except Exception as e:
            print(f"\n❌ Exploration error: {e}")
            errors += 1
        
        finally:
            self.is_running = False
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            "app_name": self.app_name,
            "iterations_completed": iterations_completed,
            "max_iterations": max_iterations,
            "successful_explorations": successful_explorations,
            "state_changes": state_changes,
            "errors": errors,
            "pending_remaining": len(self.pending_nodes),
            "total_explored": len(self.explored_nodes),
            "duration_seconds": duration,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "iterations_per_minute": (iterations_completed / duration * 60) if duration > 0 else 0
        }
        
        print(f"\n{'='*70}")
        print(f"📊 EXPLORATION SUMMARY")
        print(f"{'='*70}")
        print(f"🔄 Iterations: {iterations_completed}/{max_iterations}")
        print(f"✅ Successful: {successful_explorations}")
        print(f"🔀 State Changes: {state_changes}")
        print(f"❌ Errors: {errors}")
        print(f"📊 Remaining: {len(self.pending_nodes)} pending nodes")
        print(f"⏱️ Duration: {duration:.1f}s ({summary['iterations_per_minute']:.1f} iter/min)")
        print(f"{'='*70}\n")
        
        return summary
    
    def _load_pending_from_state(self, state_id: str):
        """Load pending nodes from a specific state"""
        state_data = self.context.fdom_data.get("states", {}).get(state_id, {})
        nodes = state_data.get("nodes", {})
        
        for node_id, node_data in nodes.items():
            full_id = f"{state_id}::{node_id}"
            
            if (full_id not in self.explored_nodes and
                node_data.get("g_icon_name", "").lower() != "unanalyzed" and
                node_data.get("g_enabled", True) and
                node_data.get("g_interactive", True)):
                self.pending_nodes.add(full_id)
    
    def stop(self):
        """Stop the exploration"""
        self.is_running = False
    
    def get_results(self) -> List[Dict]:
        """Get all iteration results"""
        return self.iteration_results


# Convenience functions
async def execute_5_step_task(app_name: str, task: str, dry_run: bool = False) -> Dict:
    """Execute a task in exactly 5 steps"""
    executor = TaskExecutor(app_name)
    result = await executor.execute_task(task, max_steps=5, dry_run=dry_run)
    return result.to_dict()


async def run_50_iteration_exploration(app_name: str, use_ollama: bool = True) -> Dict:
    """Run exploration for 50 iterations"""
    executor = ExplorationExecutor(app_name)
    return await executor.run_exploration(max_iterations=50, use_ollama_guidance=use_ollama)


# Test
if __name__ == "__main__":
    async def main():
        print("🧪 Testing Task Executor...")
        
        # Test 5-step task
        print("\n1. Testing 5-step task execution (dry run):")
        result = await execute_5_step_task(
            "notepad",
            "Open File menu and create a new document",
            dry_run=True
        )
        print(f"Result: {json.dumps(result, indent=2)[:500]}...")
        
        # Test exploration (limited for testing)
        print("\n2. Testing exploration (5 iterations):")
        executor = ExplorationExecutor("notepad")
        summary = await executor.run_exploration(max_iterations=5, use_ollama_guidance=False)
        print(f"Summary: {json.dumps(summary, indent=2)}")
    
    asyncio.run(main())

