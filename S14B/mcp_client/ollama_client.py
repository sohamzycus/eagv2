"""
Ollama Client - Interfaces with local Ollama LLM for computer task decisions
"""

import json
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FDOMElement:
    """Represents a single fDOM element"""
    node_id: str
    state_id: str
    name: str
    description: str
    element_type: str
    enabled: bool
    interactive: bool
    bbox: List[int]
    
    @classmethod
    def from_fdom_node(cls, state_id: str, node_id: str, node_data: Dict) -> "FDOMElement":
        return cls(
            node_id=f"{state_id}::{node_id}",
            state_id=state_id,
            name=node_data.get("g_icon_name", "unknown"),
            description=node_data.get("g_brief", ""),
            element_type=node_data.get("g_type", "icon"),
            enabled=node_data.get("g_enabled", True),
            interactive=node_data.get("g_interactive", True),
            bbox=node_data.get("bbox", [0, 0, 0, 0])
        )


@dataclass
class ComputerAction:
    """Represents a computer action to be performed"""
    action_type: str  # click, type, scroll, navigate
    target_element: Optional[str] = None
    target_state: Optional[str] = None
    text_input: Optional[str] = None
    reasoning: str = ""
    confidence: float = 0.0


class OllamaClient:
    """
    Client for interfacing with local Ollama instance
    Uses the fDOM structure to make informed decisions about GUI interactions
    """
    
    DEFAULT_MODEL = "llama3.2:latest"
    DEFAULT_HOST = "http://localhost:11434"
    
    def __init__(self, model: str = None, host: str = None):
        self.model = model or self.DEFAULT_MODEL
        self.host = host or self.DEFAULT_HOST
        self.conversation_history: List[Dict] = []
        self.action_history: List[ComputerAction] = []
        
    def _call_ollama(self, prompt: str, system_prompt: str = None) -> str:
        """Make a call to local Ollama instance"""
        
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add conversation history for context
        messages.extend(self.conversation_history[-10:])  # Last 10 messages for context
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 1024
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            
            assistant_message = result.get("message", {}).get("content", "")
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
            
        except requests.exceptions.RequestException as e:
            return f"Error calling Ollama: {str(e)}"
    
    def check_ollama_status(self) -> Dict[str, Any]:
        """Check if Ollama is running and available"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get("models", [])
            return {
                "status": "online",
                "models": [m.get("name") for m in models],
                "selected_model": self.model
            }
        except Exception as e:
            return {
                "status": "offline",
                "error": str(e),
                "selected_model": self.model
            }
    
    def analyze_fdom_state(self, fdom_data: Dict, current_state: str) -> Dict:
        """Analyze the current fDOM state and provide insights"""
        
        state_data = fdom_data.get("states", {}).get(current_state, {})
        nodes = state_data.get("nodes", {})
        
        # Extract available elements
        elements = []
        for node_id, node_data in nodes.items():
            if node_data.get("g_icon_name", "").lower() != "unanalyzed":
                elem = FDOMElement.from_fdom_node(current_state, node_id, node_data)
                if elem.enabled and elem.interactive:
                    elements.append(asdict(elem))
        
        # Get navigation edges from this state
        edges = [e for e in fdom_data.get("edges", []) if e.get("from") == current_state]
        
        system_prompt = """You are an expert GUI automation assistant. You analyze application interfaces and help users accomplish tasks.
        
When given the current state of an application (elements available, navigation options), you:
1. Summarize what you see in the current state
2. Identify key actionable elements
3. Suggest possible next steps based on the goal

Always be precise about element identifiers when suggesting actions."""

        prompt = f"""Analyze this GUI state:

**Current State:** {current_state}
**State Breadcrumb:** {state_data.get('breadcrumb', 'root')}

**Available Interactive Elements:**
{json.dumps(elements[:20], indent=2)}

**Navigation Options (known transitions from this state):**
{json.dumps(edges, indent=2)}

Provide a brief analysis of:
1. What application/feature this appears to be
2. Key interactive elements available
3. Possible user workflows from here"""

        analysis = self._call_ollama(prompt, system_prompt)
        
        return {
            "current_state": current_state,
            "element_count": len(elements),
            "navigation_options": len(edges),
            "analysis": analysis,
            "elements": elements
        }
    
    def plan_task(self, task_description: str, fdom_data: Dict, current_state: str, max_steps: int = 5) -> List[ComputerAction]:
        """
        Plan a sequence of actions to accomplish a task
        Returns up to max_steps actions
        """
        
        state_data = fdom_data.get("states", {}).get(current_state, {})
        nodes = state_data.get("nodes", {})
        
        # Build element list
        elements = []
        for node_id, node_data in nodes.items():
            name = node_data.get("g_icon_name", "unknown")
            if name.lower() != "unanalyzed" and node_data.get("g_enabled", True) and node_data.get("g_interactive", True):
                elements.append({
                    "id": f"{current_state}::{node_id}",
                    "name": name,
                    "description": node_data.get("g_brief", ""),
                    "type": node_data.get("g_type", "icon")
                })
        
        # Get all states for context
        all_states = list(fdom_data.get("states", {}).keys())
        edges = fdom_data.get("edges", [])
        
        system_prompt = """You are an expert GUI automation planner. Given a task and available UI elements, you create step-by-step action plans.

Your response MUST be valid JSON with this exact structure:
{
    "task_analysis": "Brief analysis of the task",
    "steps": [
        {
            "step_number": 1,
            "action_type": "click|type|scroll|navigate",
            "target_element": "state::node_id or null",
            "target_state": "state name if navigate, else null",
            "text_input": "text to type if action_type is type, else null",
            "reasoning": "Why this step is needed",
            "confidence": 0.0-1.0
        }
    ]
}

IMPORTANT:
- Only use element IDs that exist in the provided list
- For "click" actions, target_element is required
- For "type" actions, both target_element and text_input are required
- For "navigate" actions, target_state is required
- Keep steps to {max_steps} or fewer"""

        prompt = f"""Create a {max_steps}-step plan to accomplish this task:

**TASK:** {task_description}

**Current State:** {current_state}
**All Known States:** {all_states}

**Available Elements in Current State:**
{json.dumps(elements, indent=2)}

**Navigation Graph (edges):**
{json.dumps(edges[:20], indent=2)}

Respond with ONLY valid JSON following the specified format."""

        response = self._call_ollama(prompt, system_prompt)
        
        # Parse the response
        try:
            # Try to extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                plan_data = json.loads(json_str)
            else:
                plan_data = {"steps": []}
        except json.JSONDecodeError:
            plan_data = {"steps": []}
        
        # Convert to ComputerAction objects
        actions = []
        for step in plan_data.get("steps", [])[:max_steps]:
            action = ComputerAction(
                action_type=step.get("action_type", "click"),
                target_element=step.get("target_element"),
                target_state=step.get("target_state"),
                text_input=step.get("text_input"),
                reasoning=step.get("reasoning", ""),
                confidence=step.get("confidence", 0.5)
            )
            actions.append(action)
            self.action_history.append(action)
        
        return actions
    
    def decide_next_exploration_action(self, fdom_data: Dict, current_state: str, 
                                       explored_nodes: set, pending_nodes: set) -> Optional[ComputerAction]:
        """
        Decide the next best element to explore during automated exploration
        """
        
        state_data = fdom_data.get("states", {}).get(current_state, {})
        nodes = state_data.get("nodes", {})
        
        # Find unexplored elements in current state
        unexplored = []
        for node_id, node_data in nodes.items():
            full_id = f"{current_state}::{node_id}"
            name = node_data.get("g_icon_name", "unknown")
            
            if (full_id in pending_nodes and 
                name.lower() != "unanalyzed" and 
                node_data.get("g_enabled", True) and 
                node_data.get("g_interactive", True)):
                unexplored.append({
                    "id": full_id,
                    "name": name,
                    "description": node_data.get("g_brief", ""),
                    "type": node_data.get("g_type", "icon")
                })
        
        if not unexplored:
            return None
        
        system_prompt = """You are an intelligent GUI exploration agent. Your goal is to systematically explore an application by clicking on elements to discover new functionality.

Choose the MOST INTERESTING unexplored element to click next. Consider:
- Elements that might open new menus/dialogs (File, Edit, Settings)
- Elements that reveal hidden functionality
- Elements that haven't been explored yet

Respond with ONLY valid JSON:
{
    "chosen_element": "the full element ID",
    "reasoning": "why this element is interesting to explore"
}"""

        prompt = f"""Choose the next element to explore:

**Current State:** {current_state}
**Already Explored:** {len(explored_nodes)} elements
**Pending Exploration:** {len(pending_nodes)} elements

**Unexplored Elements in Current State (choose one):**
{json.dumps(unexplored[:15], indent=2)}

Which element should we click next?"""

        response = self._call_ollama(prompt, system_prompt)
        
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                choice = json.loads(response[json_start:json_end])
                chosen_id = choice.get("chosen_element", "")
                reasoning = choice.get("reasoning", "")
                
                # Validate the choice
                if any(e["id"] == chosen_id for e in unexplored):
                    return ComputerAction(
                        action_type="click",
                        target_element=chosen_id,
                        reasoning=reasoning,
                        confidence=0.8
                    )
        except json.JSONDecodeError:
            pass
        
        # Fallback: return first unexplored element
        if unexplored:
            return ComputerAction(
                action_type="click",
                target_element=unexplored[0]["id"],
                reasoning="Default selection - first available element",
                confidence=0.5
            )
        
        return None
    
    def clear_history(self):
        """Clear conversation and action history"""
        self.conversation_history = []
        self.action_history = []


# Test function
def test_ollama_client():
    """Test the Ollama client"""
    print("🧪 Testing Ollama Client...")
    
    client = OllamaClient()
    
    # Check status
    status = client.check_ollama_status()
    print(f"\n📡 Ollama Status: {status}")
    
    if status["status"] == "online":
        print(f"✅ Ollama is running with models: {status['models']}")
        
        # Test a simple call
        response = client._call_ollama("What is 2+2? Reply with just the number.")
        print(f"\n🤖 Test response: {response}")
    else:
        print(f"❌ Ollama is offline: {status.get('error')}")
        print("💡 Start Ollama with: ollama serve")


if __name__ == "__main__":
    test_ollama_client()

