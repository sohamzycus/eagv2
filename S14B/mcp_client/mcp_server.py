"""
MCP Server - Model Context Protocol server for fDOM GUI automation
Exposes fDOM state and actions as MCP tools
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class MCPTool:
    """Represents an MCP tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    

@dataclass
class MCPResource:
    """Represents an MCP resource"""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"


class FDOMContext:
    """
    Manages fDOM context for MCP interactions
    Provides structured access to UI state and elements
    """
    
    def __init__(self, app_name: str, base_path: str = None):
        self.app_name = app_name
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent / "apps"
        self.fdom_data: Dict = {}
        self.current_state: str = "root"
        self.load_fdom()
    
    def load_fdom(self) -> bool:
        """Load fDOM data from JSON file"""
        fdom_path = self.base_path / self.app_name / "fdom.json"
        
        if fdom_path.exists():
            try:
                with open(fdom_path, 'r', encoding='utf-8') as f:
                    self.fdom_data = json.load(f)
                return True
            except Exception as e:
                print(f"Error loading fDOM: {e}")
                return False
        return False
    
    def save_fdom(self) -> bool:
        """Save fDOM data back to JSON file"""
        fdom_path = self.base_path / self.app_name / "fdom.json"
        
        try:
            fdom_path.parent.mkdir(parents=True, exist_ok=True)
            with open(fdom_path, 'w', encoding='utf-8') as f:
                json.dump(self.fdom_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving fDOM: {e}")
            return False
    
    def get_states(self) -> List[str]:
        """Get list of all states"""
        return list(self.fdom_data.get("states", {}).keys())
    
    def get_state_info(self, state_id: str) -> Optional[Dict]:
        """Get information about a specific state"""
        return self.fdom_data.get("states", {}).get(state_id)
    
    def get_elements_in_state(self, state_id: str = None) -> List[Dict]:
        """Get all elements in a state"""
        state_id = state_id or self.current_state
        state_data = self.fdom_data.get("states", {}).get(state_id, {})
        nodes = state_data.get("nodes", {})
        
        elements = []
        for node_id, node_data in nodes.items():
            elements.append({
                "id": f"{state_id}::{node_id}",
                "node_id": node_id,
                "state_id": state_id,
                "name": node_data.get("g_icon_name", "unknown"),
                "description": node_data.get("g_brief", ""),
                "type": node_data.get("g_type", "icon"),
                "enabled": node_data.get("g_enabled", True),
                "interactive": node_data.get("g_interactive", True),
                "bbox": node_data.get("bbox", [0, 0, 0, 0]),
                "status": node_data.get("status", "unknown")
            })
        
        return elements
    
    def get_navigation_edges(self, from_state: str = None) -> List[Dict]:
        """Get navigation edges from a state"""
        from_state = from_state or self.current_state
        edges = self.fdom_data.get("edges", [])
        return [e for e in edges if e.get("from") == from_state]
    
    def get_exploration_stats(self) -> Dict:
        """Get exploration statistics"""
        return self.fdom_data.get("exploration_stats", {
            "pending_nodes": 0,
            "explored_nodes": 0,
            "non_interactive_nodes": 0,
            "total_nodes": 0
        })
    
    def set_current_state(self, state_id: str) -> bool:
        """Set the current state"""
        if state_id in self.fdom_data.get("states", {}):
            self.current_state = state_id
            return True
        return False


class MCPServer:
    """
    MCP Server implementation for fDOM GUI automation
    Provides tools for UI exploration, task planning, and execution
    """
    
    def __init__(self, fdom_context: FDOMContext = None):
        self.context = fdom_context
        self.tools = self._register_tools()
        self.resources = self._register_resources()
        self.execution_log: List[Dict] = []
    
    def _register_tools(self) -> Dict[str, MCPTool]:
        """Register available MCP tools"""
        tools = {
            "get_current_state": MCPTool(
                name="get_current_state",
                description="Get information about the current UI state including available elements",
                parameters={"type": "object", "properties": {}, "required": []}
            ),
            "list_states": MCPTool(
                name="list_states",
                description="List all known UI states in the fDOM",
                parameters={"type": "object", "properties": {}, "required": []}
            ),
            "get_elements": MCPTool(
                name="get_elements",
                description="Get all interactive elements in the current or specified state",
                parameters={
                    "type": "object",
                    "properties": {
                        "state_id": {"type": "string", "description": "State ID to get elements from (optional)"}
                    },
                    "required": []
                }
            ),
            "find_element": MCPTool(
                name="find_element",
                description="Find an element by name or partial name match",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Element name to search for"}
                    },
                    "required": ["name"]
                }
            ),
            "get_navigation_options": MCPTool(
                name="get_navigation_options",
                description="Get available navigation options from the current state",
                parameters={"type": "object", "properties": {}, "required": []}
            ),
            "navigate_to_state": MCPTool(
                name="navigate_to_state",
                description="Navigate to a specific state",
                parameters={
                    "type": "object",
                    "properties": {
                        "state_id": {"type": "string", "description": "Target state ID"}
                    },
                    "required": ["state_id"]
                }
            ),
            "click_element": MCPTool(
                name="click_element",
                description="Click on a specific element by ID",
                parameters={
                    "type": "object",
                    "properties": {
                        "element_id": {"type": "string", "description": "Full element ID (state::node_id)"}
                    },
                    "required": ["element_id"]
                }
            ),
            "get_exploration_progress": MCPTool(
                name="get_exploration_progress",
                description="Get the current exploration progress and statistics",
                parameters={"type": "object", "properties": {}, "required": []}
            )
        }
        return tools
    
    def _register_resources(self) -> Dict[str, MCPResource]:
        """Register available MCP resources"""
        resources = {
            "fdom://state": MCPResource(
                uri="fdom://state",
                name="Current fDOM State",
                description="The current UI state with all elements"
            ),
            "fdom://graph": MCPResource(
                uri="fdom://graph",
                name="State Navigation Graph",
                description="The complete state navigation graph"
            ),
            "fdom://history": MCPResource(
                uri="fdom://history",
                name="Execution History",
                description="History of executed actions"
            )
        }
        return resources
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict = None) -> Dict:
        """Handle an MCP tool call"""
        arguments = arguments or {}
        
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        # Dispatch to appropriate handler
        handlers = {
            "get_current_state": self._handle_get_current_state,
            "list_states": self._handle_list_states,
            "get_elements": self._handle_get_elements,
            "find_element": self._handle_find_element,
            "get_navigation_options": self._handle_get_navigation_options,
            "navigate_to_state": self._handle_navigate_to_state,
            "click_element": self._handle_click_element,
            "get_exploration_progress": self._handle_get_exploration_progress
        }
        
        handler = handlers.get(tool_name)
        if handler:
            result = await handler(arguments)
            
            # Log the execution
            self.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "tool": tool_name,
                "arguments": arguments,
                "result_summary": str(result)[:200]
            })
            
            return result
        
        return {"error": f"No handler for tool: {tool_name}"}
    
    async def _handle_get_current_state(self, args: Dict) -> Dict:
        """Get current state information"""
        if not self.context:
            return {"error": "No fDOM context loaded"}
        
        state_info = self.context.get_state_info(self.context.current_state)
        elements = self.context.get_elements_in_state()
        
        # Filter to interactive elements
        interactive_elements = [e for e in elements if e.get("interactive") and e.get("enabled")]
        
        return {
            "current_state": self.context.current_state,
            "breadcrumb": state_info.get("breadcrumb", "root") if state_info else "root",
            "total_elements": len(elements),
            "interactive_elements": len(interactive_elements),
            "elements": interactive_elements[:20],  # Limit for readability
            "navigation_available": len(self.context.get_navigation_edges())
        }
    
    async def _handle_list_states(self, args: Dict) -> Dict:
        """List all states"""
        if not self.context:
            return {"error": "No fDOM context loaded"}
        
        states = self.context.get_states()
        state_details = []
        
        for state_id in states:
            state_info = self.context.get_state_info(state_id)
            if state_info:
                state_details.append({
                    "id": state_id,
                    "breadcrumb": state_info.get("breadcrumb", state_id),
                    "total_elements": state_info.get("total_elements", 0),
                    "parent": state_info.get("parent"),
                    "trigger_element": state_info.get("trigger_element")
                })
        
        return {
            "total_states": len(states),
            "states": state_details
        }
    
    async def _handle_get_elements(self, args: Dict) -> Dict:
        """Get elements in a state"""
        if not self.context:
            return {"error": "No fDOM context loaded"}
        
        state_id = args.get("state_id", self.context.current_state)
        elements = self.context.get_elements_in_state(state_id)
        
        # Filter by name != unanalyzed
        filtered = [e for e in elements if e["name"].lower() != "unanalyzed"]
        
        return {
            "state_id": state_id,
            "total_elements": len(elements),
            "analyzed_elements": len(filtered),
            "elements": filtered
        }
    
    async def _handle_find_element(self, args: Dict) -> Dict:
        """Find element by name"""
        if not self.context:
            return {"error": "No fDOM context loaded"}
        
        search_name = args.get("name", "").lower()
        matches = []
        
        for state_id in self.context.get_states():
            elements = self.context.get_elements_in_state(state_id)
            for elem in elements:
                if search_name in elem["name"].lower():
                    matches.append(elem)
        
        return {
            "search_term": args.get("name"),
            "matches_found": len(matches),
            "matches": matches[:20]  # Limit results
        }
    
    async def _handle_get_navigation_options(self, args: Dict) -> Dict:
        """Get navigation options"""
        if not self.context:
            return {"error": "No fDOM context loaded"}
        
        edges = self.context.get_navigation_edges()
        
        return {
            "current_state": self.context.current_state,
            "navigation_options": len(edges),
            "edges": edges
        }
    
    async def _handle_navigate_to_state(self, args: Dict) -> Dict:
        """Navigate to a state"""
        if not self.context:
            return {"error": "No fDOM context loaded"}
        
        target_state = args.get("state_id")
        if not target_state:
            return {"error": "state_id is required"}
        
        if self.context.set_current_state(target_state):
            return {
                "success": True,
                "new_state": target_state,
                "elements_available": len(self.context.get_elements_in_state())
            }
        
        return {
            "success": False,
            "error": f"State '{target_state}' not found"
        }
    
    async def _handle_click_element(self, args: Dict) -> Dict:
        """Simulate clicking an element"""
        if not self.context:
            return {"error": "No fDOM context loaded"}
        
        element_id = args.get("element_id")
        if not element_id:
            return {"error": "element_id is required"}
        
        # Parse state::node_id format
        if "::" in element_id:
            state_id, node_id = element_id.split("::", 1)
        else:
            state_id = self.context.current_state
            node_id = element_id
        
        # Find the element
        elements = self.context.get_elements_in_state(state_id)
        target_element = None
        for elem in elements:
            if elem["node_id"] == node_id:
                target_element = elem
                break
        
        if not target_element:
            return {
                "success": False,
                "error": f"Element '{element_id}' not found"
            }
        
        # Check if click leads to new state
        edges = self.context.fdom_data.get("edges", [])
        transition = None
        for edge in edges:
            if edge.get("from") == state_id and edge.get("action", "").endswith(node_id):
                transition = edge
                break
        
        if transition:
            # Update to new state
            new_state = transition.get("to")
            self.context.set_current_state(new_state)
            return {
                "success": True,
                "element_clicked": target_element["name"],
                "state_changed": True,
                "new_state": new_state
            }
        
        return {
            "success": True,
            "element_clicked": target_element["name"],
            "state_changed": False,
            "note": "Element clicked but no state transition defined"
        }
    
    async def _handle_get_exploration_progress(self, args: Dict) -> Dict:
        """Get exploration progress"""
        if not self.context:
            return {"error": "No fDOM context loaded"}
        
        stats = self.context.get_exploration_stats()
        
        return {
            "current_state": self.context.current_state,
            "exploration_stats": stats,
            "states_discovered": len(self.context.get_states()),
            "execution_log_entries": len(self.execution_log)
        }
    
    def get_tools_list(self) -> List[Dict]:
        """Get list of available tools in MCP format"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.parameters
            }
            for tool in self.tools.values()
        ]
    
    def get_resources_list(self) -> List[Dict]:
        """Get list of available resources"""
        return [asdict(r) for r in self.resources.values()]


# Test function
async def test_mcp_server():
    """Test the MCP server"""
    print("🧪 Testing MCP Server...")
    
    # Create context for notepad
    context = FDOMContext("notepad")
    
    if not context.fdom_data:
        print("❌ Failed to load fDOM data for notepad")
        return
    
    print(f"✅ Loaded fDOM with {len(context.get_states())} states")
    
    # Create server
    server = MCPServer(context)
    
    # Test tools
    print("\n📋 Available Tools:")
    for tool in server.get_tools_list():
        print(f"  • {tool['name']}: {tool['description'][:60]}...")
    
    # Test some tool calls
    print("\n🔧 Testing Tool Calls:")
    
    result = await server.handle_tool_call("get_current_state")
    print(f"\n1. get_current_state:")
    print(f"   State: {result.get('current_state')}")
    print(f"   Interactive elements: {result.get('interactive_elements')}")
    
    result = await server.handle_tool_call("list_states")
    print(f"\n2. list_states:")
    print(f"   Total states: {result.get('total_states')}")
    
    result = await server.handle_tool_call("find_element", {"name": "File"})
    print(f"\n3. find_element('File'):")
    print(f"   Matches: {result.get('matches_found')}")
    
    print("\n✅ MCP Server is working!")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())

