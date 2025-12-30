"""
Agent Builder - Production-Ready with Tool Simulation & Autogen Support
Features:
1. Visual tool call rendering for business users
2. SQLite persistence for agents and chat history  
3. Simulated API/tool calls with swagger specs
4. Autogen-compatible prompt generation
"""

import gradio as gr
import json
import os
import sys
import sqlite3
import re
from datetime import datetime
from uuid import uuid4
from typing import Dict, List, Any, Optional
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================================
# DATABASE LAYER - Persistence for Agents & Conversations
# ============================================================================

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "agent_builder.db")

def init_db():
    """Initialize SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        system_prompt TEXT,
        tools_json TEXT,
        swagger_spec TEXT,
        created_at TEXT,
        updated_at TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        agent_id TEXT,
        summary TEXT,
        messages TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tool_executions (
        id TEXT PRIMARY KEY,
        agent_id TEXT,
        conversation_id TEXT,
        tool_name TEXT,
        input_params TEXT,
        output_result TEXT,
        executed_at TEXT,
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    )''')
    
    conn.commit()
    conn.close()

init_db()


class AgentStore:
    """Handles agent persistence."""
    
    @staticmethod
    def save_agent(agent_id: str, name: str, description: str, 
                   system_prompt: str, tools_json: str, swagger_spec: str) -> str:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = datetime.now().isoformat()
        
        c.execute('''INSERT OR REPLACE INTO agents 
                     (id, name, description, system_prompt, tools_json, swagger_spec, created_at, updated_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (agent_id, name, description, system_prompt, tools_json, swagger_spec, now, now))
        
        conn.commit()
        conn.close()
        return agent_id
    
    @staticmethod
    def get_agent(agent_id: str) -> Optional[Dict]:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0], 'name': row[1], 'description': row[2],
                'system_prompt': row[3], 'tools_json': row[4], 'swagger_spec': row[5],
                'created_at': row[6], 'updated_at': row[7]
            }
        return None
    
    @staticmethod
    def list_agents() -> List[Dict]:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, name, description, created_at FROM agents ORDER BY updated_at DESC LIMIT 20')
        rows = c.fetchall()
        conn.close()
        return [{'id': r[0], 'name': r[1], 'description': r[2], 'created_at': r[3]} for r in rows]
    
    @staticmethod
    def save_conversation(conv_id: str, agent_id: str, summary: str, messages: List[Dict]):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = datetime.now().isoformat()
        
        c.execute('''INSERT OR REPLACE INTO conversations 
                     (id, agent_id, summary, messages, created_at, updated_at)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (conv_id, agent_id, summary, json.dumps(messages), now, now))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_conversation(conv_id: str) -> Optional[Dict]:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM conversations WHERE id = ?', (conv_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0], 'agent_id': row[1], 'summary': row[2],
                'messages': json.loads(row[3]), 'created_at': row[4]
            }
        return None
    
    @staticmethod
    def log_tool_execution(agent_id: str, conv_id: str, tool_name: str, 
                          input_params: Dict, output_result: Dict):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        exec_id = str(uuid4())[:12]
        
        c.execute('''INSERT INTO tool_executions 
                     (id, agent_id, conversation_id, tool_name, input_params, output_result, executed_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (exec_id, agent_id, conv_id, tool_name, 
                   json.dumps(input_params), json.dumps(output_result), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()


# ============================================================================
# TOOL SIMULATOR - Creates mock APIs with dynamic responses
# ============================================================================

class ToolSimulator:
    """Simulates tool/API calls with realistic mock data."""
    
    # Mock data generators for different domains
    MOCK_DATA = {
        "catalog_items": [
            {"id": "CAT001", "name": "Dell Laptop XPS 15", "price": 1299.99, "category": "Electronics", "supplier": "Dell Direct", "in_stock": True},
            {"id": "CAT002", "name": "HP LaserJet Pro", "price": 349.00, "category": "Office Equipment", "supplier": "HP Store", "in_stock": True},
            {"id": "CAT003", "name": "Ergonomic Office Chair", "price": 450.00, "category": "Furniture", "supplier": "Herman Miller", "in_stock": False},
            {"id": "CAT004", "name": "Coffee Mug Set (6pc)", "price": 24.99, "category": "Office Supplies", "supplier": "Amazon Business", "in_stock": True},
            {"id": "CAT005", "name": "Wireless Mouse", "price": 29.99, "category": "Electronics", "supplier": "Logitech", "in_stock": True},
        ],
        "suppliers": [
            {"id": "SUP001", "name": "Dell Direct", "rating": 4.8, "contract_status": "Active", "payment_terms": "Net 30"},
            {"id": "SUP002", "name": "HP Store", "rating": 4.5, "contract_status": "Active", "payment_terms": "Net 45"},
            {"id": "SUP003", "name": "Amazon Business", "rating": 4.7, "contract_status": "Active", "payment_terms": "Net 15"},
            {"id": "SUP004", "name": "Staples", "rating": 4.2, "contract_status": "Pending Renewal", "payment_terms": "Net 30"},
        ],
        "purchase_orders": [
            {"po_number": "PO-2024-001", "status": "Delivered", "amount": 2599.98, "items": 2},
            {"po_number": "PO-2024-002", "status": "In Transit", "amount": 450.00, "items": 1},
            {"po_number": "PO-2024-003", "status": "Pending Approval", "amount": 1299.99, "items": 1},
        ],
        "users": [
            {"id": "USR001", "name": "John Smith", "department": "Engineering", "budget_remaining": 5000.00},
            {"id": "USR002", "name": "Sarah Johnson", "department": "Marketing", "budget_remaining": 3500.00},
        ]
    }
    
    @classmethod
    def execute_tool(cls, tool_name: str, parameters: Dict) -> Dict:
        """Execute a simulated tool call and return mock results."""
        
        # Normalize tool name
        tool_lower = tool_name.lower().replace(" ", "_")
        
        # Route to appropriate handler
        if "search" in tool_lower or "catalog" in tool_lower or "item" in tool_lower:
            return cls._search_catalog(parameters)
        elif "supplier" in tool_lower:
            return cls._get_suppliers(parameters)
        elif "purchase" in tool_lower or "po" in tool_lower or "order" in tool_lower:
            return cls._handle_purchase_order(parameters)
        elif "user" in tool_lower or "employee" in tool_lower:
            return cls._get_user_info(parameters)
        elif "intent" in tool_lower or "capture" in tool_lower:
            return cls._capture_intent(parameters)
        elif "create" in tool_lower or "submit" in tool_lower:
            return cls._create_request(parameters)
        elif "approve" in tool_lower:
            return cls._approve_request(parameters)
        else:
            return cls._generic_response(tool_name, parameters)
    
    @classmethod
    def _search_catalog(cls, params: Dict) -> Dict:
        query = params.get("query", params.get("search_term", params.get("item_name", ""))).lower()
        items = cls.MOCK_DATA["catalog_items"]
        
        if query:
            items = [i for i in items if query in i["name"].lower() or query in i["category"].lower()]
        
        return {
            "success": True,
            "results_count": len(items),
            "items": items[:5],
            "search_query": query,
            "timestamp": datetime.now().isoformat()
        }
    
    @classmethod
    def _get_suppliers(cls, params: Dict) -> Dict:
        category = params.get("category", "")
        suppliers = cls.MOCK_DATA["suppliers"]
        
        return {
            "success": True,
            "suppliers": suppliers,
            "active_count": sum(1 for s in suppliers if s["contract_status"] == "Active"),
            "timestamp": datetime.now().isoformat()
        }
    
    @classmethod
    def _handle_purchase_order(cls, params: Dict) -> Dict:
        action = params.get("action", "view")
        
        if action == "create":
            po_num = f"PO-2024-{random.randint(100, 999)}"
            return {
                "success": True,
                "po_number": po_num,
                "status": "Created - Pending Approval",
                "estimated_delivery": "5-7 business days",
                "message": f"Purchase Order {po_num} created successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "orders": cls.MOCK_DATA["purchase_orders"],
                "timestamp": datetime.now().isoformat()
            }
    
    @classmethod
    def _get_user_info(cls, params: Dict) -> Dict:
        user_id = params.get("user_id", "USR001")
        user = cls.MOCK_DATA["users"][0]
        
        return {
            "success": True,
            "user": user,
            "permissions": ["create_pr", "view_catalog", "submit_order"],
            "timestamp": datetime.now().isoformat()
        }
    
    @classmethod
    def _capture_intent(cls, params: Dict) -> Dict:
        user_input = params.get("user_input", params.get("message", ""))
        
        return {
            "success": True,
            "intent": {
                "action": "purchase",
                "entity_type": "item",
                "extracted_entities": {
                    "item_description": user_input,
                    "urgency": "normal",
                    "quantity": 1
                },
                "confidence": 0.92
            },
            "next_action": "search_catalog",
            "timestamp": datetime.now().isoformat()
        }
    
    @classmethod
    def _create_request(cls, params: Dict) -> Dict:
        req_id = f"REQ-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        
        return {
            "success": True,
            "request_id": req_id,
            "status": "Submitted",
            "workflow_state": "Pending Manager Approval",
            "estimated_completion": "2-3 business days",
            "timestamp": datetime.now().isoformat()
        }
    
    @classmethod
    def _approve_request(cls, params: Dict) -> Dict:
        return {
            "success": True,
            "approval_status": "Approved",
            "approved_by": "System (Auto-approval < $500)",
            "next_step": "Purchase Order Generation",
            "timestamp": datetime.now().isoformat()
        }
    
    @classmethod
    def _generic_response(cls, tool_name: str, params: Dict) -> Dict:
        return {
            "success": True,
            "tool": tool_name,
            "input_received": params,
            "message": f"Tool '{tool_name}' executed successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    @classmethod
    def generate_swagger_spec(cls, tools_json: str, agent_name: str) -> str:
        """Generate OpenAPI/Swagger spec from tools JSON."""
        try:
            tools = json.loads(tools_json)
        except:
            return "{}"
        
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": f"{agent_name} API",
                "description": f"Auto-generated API for {agent_name}",
                "version": "1.0.0"
            },
            "servers": [{"url": "http://localhost:8000/api/v1"}],
            "paths": {},
            "components": {"schemas": {}}
        }
        
        for tool in tools:
            tool_name = tool.get("name", "unknown").replace(" ", "_").lower()
            path = f"/{tool_name}"
            
            # Build request schema
            request_schema = {"type": "object", "properties": {}}
            required = []
            
            for param_name, param_def in tool.get("parameters", {}).items():
                request_schema["properties"][param_name] = {
                    "type": param_def.get("type", "string"),
                    "description": param_def.get("description", "")
                }
                if param_def.get("required", False):
                    required.append(param_name)
            
            if required:
                request_schema["required"] = required
            
            # Build response schema
            response_schema = {"type": "object", "properties": {}}
            for ret_name, ret_def in tool.get("returns", {}).items():
                response_schema["properties"][ret_name] = {
                    "type": ret_def.get("type", "string"),
                    "description": ret_def.get("description", "")
                }
            
            spec["paths"][path] = {
                "post": {
                    "summary": tool.get("description", ""),
                    "operationId": tool_name,
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": request_schema
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": response_schema
                                }
                            }
                        }
                    }
                }
            }
        
        return json.dumps(spec, indent=2)


# ============================================================================
# TOOL CALL RENDERER - Visual formatting for business users
# ============================================================================

class ToolCallRenderer:
    """Renders tool calls with visual styling for business users."""
    
    TOOL_PATTERNS = [
        r'\b(IntentCaptureTool|CatalogSearchTool|SupplierLookupTool|PurchaseOrderTool|ApprovalTool|UserInfoTool)\b',
        r'\b(search_catalog|get_suppliers|create_po|submit_request|capture_intent|check_approval)\b',
        r'(?:using|calling|executing|invoking)\s+(?:the\s+)?(\w+Tool|\w+_tool)\b',
        r'\[\[TOOL:(\w+)\]\]',
    ]
    
    @classmethod
    def render_response(cls, response: str, tools_used: List[Dict] = None) -> str:
        """Render response with visual tool call indicators."""
        
        # Replace tool mentions with styled badges
        for pattern in cls.TOOL_PATTERNS:
            response = re.sub(
                pattern,
                lambda m: cls._create_tool_badge(m.group(1) if m.lastindex else m.group(0)),
                response,
                flags=re.IGNORECASE
            )
        
        # Add tool execution blocks if tools were used
        if tools_used:
            tool_blocks = "\n\n---\n**🔧 Tool Executions:**\n"
            for tool in tools_used:
                tool_blocks += cls._create_tool_execution_block(tool)
            response += tool_blocks
        
        return response
    
    @classmethod
    def _create_tool_badge(cls, tool_name: str) -> str:
        """Create a styled badge for tool name."""
        return f'<span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2px 8px; border-radius: 4px; font-family: monospace; font-size: 0.85em; font-weight: 600;">🔧 {tool_name}</span>'
    
    @classmethod
    def _create_tool_execution_block(cls, tool: Dict) -> str:
        """Create a visual block showing tool execution."""
        name = tool.get("name", "Unknown Tool")
        inputs = tool.get("inputs", {})
        outputs = tool.get("outputs", {})
        
        block = f"""
<div style="background: #1e1e2e; border-left: 4px solid #667eea; padding: 12px; margin: 8px 0; border-radius: 4px; font-family: monospace; font-size: 0.9em;">
<div style="color: #a6e3a1; margin-bottom: 8px;">▶ <strong>{name}</strong></div>
<div style="color: #89b4fa;">Input: <code>{json.dumps(inputs, indent=2)}</code></div>
<div style="color: #f9e2af; margin-top: 8px;">Output: <code>{json.dumps(outputs, indent=2)[:200]}...</code></div>
</div>
"""
        return block


# ============================================================================
# AUTOGEN PROMPT GENERATOR
# ============================================================================

AUTOGEN_PROMPT_TEMPLATE = '''"""
Autogen-Compatible Agent: {agent_name}
Auto-generated by Agent Builder
"""

from autogen import AssistantAgent, UserProxyAgent, register_function
import json

# System Message for the Agent
SYSTEM_MESSAGE = """
{system_prompt}
"""

# Tool Definitions
TOOLS = {tools_json}

# Register tools as Autogen functions
{tool_registrations}

# Create the Assistant Agent
assistant = AssistantAgent(
    name="{agent_name_snake}",
    system_message=SYSTEM_MESSAGE,
    llm_config={{
        "config_list": [{{"model": "gpt-4", "api_key": "YOUR_API_KEY"}}],
        "temperature": 0.7,
    }},
)

# Create User Proxy (for tool execution)
user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config={{"work_dir": "workspace"}},
)

# Register tool functions with the agents
{function_registrations}

# Usage Example:
# user_proxy.initiate_chat(assistant, message="I need to buy office supplies")
'''


def generate_autogen_code(agent_name: str, system_prompt: str, tools_json: str) -> str:
    """Generate Autogen-compatible Python code."""
    
    try:
        tools = json.loads(tools_json)
    except:
        tools = []
    
    # Generate tool registrations
    tool_registrations = []
    function_registrations = []
    
    for tool in tools:
        name = tool.get("name", "unknown_tool").replace(" ", "_").lower()
        desc = tool.get("description", "")
        params = tool.get("parameters", {})
        
        # Build parameter string
        param_str = ", ".join([f'{p}: str = ""' for p in params.keys()])
        
        tool_registrations.append(f'''
def {name}({param_str}) -> dict:
    """
    {desc}
    """
    # TODO: Implement actual tool logic
    return {{"status": "success", "tool": "{name}"}}
''')
        
        function_registrations.append(f'''
register_function(
    {name},
    caller=assistant,
    executor=user_proxy,
    name="{name}",
    description="{desc}"
)
''')
    
    agent_name_snake = agent_name.replace(" ", "_").lower()
    
    return AUTOGEN_PROMPT_TEMPLATE.format(
        agent_name=agent_name,
        agent_name_snake=agent_name_snake,
        system_prompt=system_prompt.replace('"""', '\\"\\"\\"'),
        tools_json=tools_json,
        tool_registrations="\n".join(tool_registrations),
        function_registrations="\n".join(function_registrations)
    )


# ============================================================================
# ORCHESTRATOR PROMPT - Enhanced for structured tool generation
# ============================================================================

ORCHESTRATOR_PROMPT = """You are an expert AI Agent Designer for enterprise procurement systems.

## Your Role
Help users create production-ready AI agents through natural conversation. You handle the ENTIRE process:

1. **Understand** - Grasp what the user wants to build
2. **Clarify** - Ask questions ONLY when truly needed for clarity
3. **Design** - Create workflow stages and identify tools
4. **Generate** - Produce complete system prompts with tool specifications

## Conversation Guidelines

- Be conversational and natural, not robotic
- Ask clarifying questions only when genuinely needed
- When you have enough context, proceed to generation
- Show your thinking process naturally
- Be concise but thorough

## When User Describes Their Need

Understand their intent. If clear enough, say:
"I understand you want [summary]. Let me design this for you."
Then generate the prompt.

If clarification needed, ask ONE natural question at a time.

## When Ready to Generate

Output the complete system prompt using this EXACT format:

---BEGIN_GENERATED_PROMPT---

# [Agent Name]

## Identity
You are [role description]. Your primary responsibility is [main goal].

## Available Tools

When you need to perform an action, use the appropriate tool by indicating: [[TOOL:tool_name]]

### IntentCaptureTool
- **Purpose**: Captures and analyzes user intent from natural language
- **When to use**: At the start of every user interaction
- **Parameters**: 
  - user_input (string): The user's message
- **Returns**: intent object with action, entities, confidence

### CatalogSearchTool
- **Purpose**: Searches internal catalog for items
- **When to use**: When user wants to find/buy items
- **Parameters**: 
  - query (string): Search term
  - category (string, optional): Filter by category
- **Returns**: list of matching items with prices and availability

[Add more tools as needed based on the agent's requirements]

## Workflow

### Stage 1: Intent Capture
**Goal**: Understand what the user wants
**Tools**: IntentCaptureTool
**Output**: Structured intent with entities
**Next**: Route to appropriate stage based on intent

### Stage 2: [Next Stage Name]
**Goal**: [What this stage accomplishes]
**Tools**: [Tools used]
**Output**: [What this produces]
**Next**: [Transition condition]

## Rules
- Never fabricate data - always use tools to fetch real information
- Always confirm with user before submitting orders
- Show prices and totals clearly
- Handle errors gracefully with helpful messages

## Response Style
- Be helpful and professional
- Use bullet points for lists
- Format currency properly
- Keep responses concise but complete

---END_GENERATED_PROMPT---

Then output tools JSON (Autogen-compatible format):

---BEGIN_TOOLS_JSON---
[
  {{
    "name": "IntentCaptureTool",
    "description": "Captures and analyzes user intent from natural language input",
    "parameters": {{
      "user_input": {{"type": "string", "description": "The user's message to analyze", "required": true}}
    }},
    "returns": {{
      "intent": {{"type": "object", "description": "Structured intent with action and entities"}},
      "confidence": {{"type": "number", "description": "Confidence score 0-1"}}
    }}
  }},
  {{
    "name": "CatalogSearchTool",
    "description": "Searches the product catalog for items matching the query",
    "parameters": {{
      "query": {{"type": "string", "description": "Search term", "required": true}},
      "category": {{"type": "string", "description": "Optional category filter"}}
    }},
    "returns": {{
      "items": {{"type": "array", "description": "List of matching products"}},
      "total_count": {{"type": "integer", "description": "Total results found"}}
    }}
  }}
]
---END_TOOLS_JSON---

## Current Conversation
{conversation}

## Your Response
Respond naturally. If generating, use the exact markers above. Ensure tools are comprehensive and cover all workflow needs."""


TESTER_PROMPT = """You are an AI agent with the following system prompt:

{system_prompt}

IMPORTANT: When you would use a tool, indicate it clearly like this:
[[TOOL:ToolName]] with parameters: {{"param": "value"}}

Then describe what the tool would return and continue your response based on that.

The available tools are:
{tools_summary}

User message: {user_message}"""


# ============================================================================
# AGENT BUILDER - Main orchestration class
# ============================================================================

class AgentBuilder:
    """Handles agent creation with persistence and tool simulation."""
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.agent_id = str(uuid4())[:8]
        self.conversation_id = str(uuid4())[:8]
        self.conversation_history = []
        self.generated_prompt = ""
        self.generated_tools = ""
        self.swagger_spec = ""
        self.autogen_code = ""
        self.agent_name = "Untitled Agent"
        self.agent_description = ""
        self.tools_executed = []
    
    def reset(self):
        """Start fresh."""
        self.agent_id = str(uuid4())[:8]
        self.conversation_id = str(uuid4())[:8]
        self.conversation_history = []
        self.generated_prompt = ""
        self.generated_tools = ""
        self.swagger_spec = ""
        self.autogen_code = ""
        self.agent_name = "Untitled Agent"
        self.agent_description = ""
        self.tools_executed = []
    
    def load_agent(self, agent_id: str) -> bool:
        """Load an existing agent."""
        agent = AgentStore.get_agent(agent_id)
        if agent:
            self.agent_id = agent['id']
            self.agent_name = agent['name']
            self.agent_description = agent.get('description', '')
            self.generated_prompt = agent.get('system_prompt', '')
            self.generated_tools = agent.get('tools_json', '')
            self.swagger_spec = agent.get('swagger_spec', '')
            if self.generated_tools:
                self.autogen_code = generate_autogen_code(
                    self.agent_name, self.generated_prompt, self.generated_tools
                )
            return True
        return False
    
    def save(self):
        """Persist current agent."""
        if self.generated_prompt:
            AgentStore.save_agent(
                self.agent_id, self.agent_name, self.agent_description,
                self.generated_prompt, self.generated_tools, self.swagger_spec
            )
            AgentStore.save_conversation(
                self.conversation_id, self.agent_id,
                self._generate_summary(), self.conversation_history
            )
    
    def _generate_summary(self) -> str:
        """Generate a brief summary of the conversation."""
        if len(self.conversation_history) < 2:
            return "New conversation"
        return f"Agent: {self.agent_name} | Messages: {len(self.conversation_history)}"
    
    def chat(self, user_message: str) -> tuple:
        """Process chat and return (response, prompt, tools, swagger, autogen, name)."""
        if not user_message.strip():
            return "", self.generated_prompt, self.generated_tools, self.swagger_spec, self.autogen_code, self.agent_name
        
        self.conversation_history.append({"role": "user", "content": user_message})
        conversation_text = "\n".join([
            f"{m['role'].title()}: {m['content']}" for m in self.conversation_history[-20:]
        ])
        
        full_prompt = ORCHESTRATOR_PROMPT.format(conversation=conversation_text)
        
        response = self.llm.generate_simple(
            system_prompt=full_prompt,
            user_message="Based on the conversation, provide your response. If ready to generate, use the exact format specified.",
            temperature=0.7
        )
        
        # Extract generated content if present
        if "---BEGIN_GENERATED_PROMPT---" in response and "---END_GENERATED_PROMPT---" in response:
            prompt_start = response.find("---BEGIN_GENERATED_PROMPT---") + len("---BEGIN_GENERATED_PROMPT---")
            prompt_end = response.find("---END_GENERATED_PROMPT---")
            self.generated_prompt = response[prompt_start:prompt_end].strip()
            
            # Extract agent name
            for line in self.generated_prompt.split("\n"):
                if line.startswith("# "):
                    self.agent_name = line[2:].strip()
                    break
            
            # Extract tools
            if "---BEGIN_TOOLS_JSON---" in response and "---END_TOOLS_JSON---" in response:
                tools_start = response.find("---BEGIN_TOOLS_JSON---") + len("---BEGIN_TOOLS_JSON---")
                tools_end = response.find("---END_TOOLS_JSON---")
                self.generated_tools = response[tools_start:tools_end].strip()
                
                # Generate swagger and autogen code
                self.swagger_spec = ToolSimulator.generate_swagger_spec(self.generated_tools, self.agent_name)
                self.autogen_code = generate_autogen_code(self.agent_name, self.generated_prompt, self.generated_tools)
            
            # Save automatically
            self.save()
            
            display_response = response.split("---BEGIN_GENERATED_PROMPT---")[0].strip()
            if not display_response:
                display_response = f"✅ **{self.agent_name}** has been created and saved!\n\nCheck the tabs on the right for:\n- 📋 System Prompt\n- 🛠️ Tools JSON\n- 📘 Swagger Spec\n- 🐍 Autogen Code"
        else:
            display_response = response
        
        self.conversation_history.append({"role": "assistant", "content": display_response})
        
        return display_response, self.generated_prompt, self.generated_tools, self.swagger_spec, self.autogen_code, self.agent_name
    
    def test_agent(self, user_message: str) -> tuple:
        """Test the generated agent with tool simulation."""
        if not self.generated_prompt:
            return "⚠️ Create an agent first by chatting on the left.", []
        
        if not user_message.strip():
            return "", []
        
        # Build tools summary for the tester
        tools_summary = "None"
        try:
            tools = json.loads(self.generated_tools)
            tools_summary = "\n".join([f"- {t['name']}: {t['description']}" for t in tools])
        except:
            pass
        
        response = self.llm.generate_simple(
            system_prompt=TESTER_PROMPT.format(
                system_prompt=self.generated_prompt,
                tools_summary=tools_summary,
                user_message=user_message
            ),
            user_message=user_message,
            temperature=0.7
        )
        
        # Detect and simulate tool calls
        tool_calls = []
        tool_pattern = r'\[\[TOOL:(\w+)\]\](?:\s*with parameters:\s*(\{[^}]+\}))?'
        matches = re.findall(tool_pattern, response)
        
        for tool_name, params_str in matches:
            params = {}
            if params_str:
                try:
                    params = json.loads(params_str)
                except:
                    params = {"raw": params_str}
            
            # Simulate the tool
            result = ToolSimulator.execute_tool(tool_name, params)
            
            tool_calls.append({
                "name": tool_name,
                "inputs": params,
                "outputs": result
            })
            
            # Log execution
            AgentStore.log_tool_execution(
                self.agent_id, self.conversation_id,
                tool_name, params, result
            )
        
        # Render response with tool styling
        rendered_response = ToolCallRenderer.render_response(response, tool_calls)
        
        return rendered_response, tool_calls


# ============================================================================
# GRADIO APP
# ============================================================================

def create_workflow_creator_app(llm_client=None):
    """Create the Agent Builder UI."""
    
    if llm_client is None:
        with gr.Blocks() as app:
            gr.Markdown("# ❌ LLM Required\nSet AZURE_OPENAI_API_KEY")
        return app
    
    builder = AgentBuilder(llm_client)
    
    def on_chat(message, history):
        response, prompt, tools, swagger, autogen, name = builder.chat(message)
        history = history or []
        if message.strip():
            history.append({"role": "user", "content": message})
        if response.strip():
            history.append({"role": "assistant", "content": response})
        return history, "", prompt, tools, swagger, autogen, name
    
    def on_test(message, history):
        if not message.strip():
            return history, "", ""
        
        history = history or []
        history.append({"role": "user", "content": message})
        
        response, tool_calls = builder.test_agent(message)
        history.append({"role": "assistant", "content": response})
        
        # Format tool execution log
        tool_log = ""
        if tool_calls:
            tool_log = "### 🔧 Tool Executions\n\n"
            for tc in tool_calls:
                tool_log += f"**{tc['name']}**\n```json\n{json.dumps(tc['outputs'], indent=2)}\n```\n\n"
        
        return history, "", tool_log
    
    def on_reset():
        builder.reset()
        return (
            [{"role": "assistant", "content": "Hi! Describe the AI agent you want to create.\n\nExamples:\n• Purchase assistant for employees\n• Invoice processor with 3-way matching\n• Sourcing agent for RFP management"}],
            "", "", "", "", "Untitled Agent", [], ""
        )
    
    def on_load_agent(agent_id):
        if builder.load_agent(agent_id):
            return (
                [{"role": "assistant", "content": f"✅ Loaded agent: **{builder.agent_name}**\n\nYou can continue refining it or test it in the Test tab."}],
                builder.generated_prompt,
                builder.generated_tools,
                builder.swagger_spec,
                builder.autogen_code,
                builder.agent_name
            )
        return None, "", "", "", "", "Untitled Agent"
    
    def get_agent_list():
        agents = AgentStore.list_agents()
        if not agents:
            return "No saved agents yet."
        return "\n".join([f"• **{a['name']}** (`{a['id']}`)" for a in agents])
    
    # Build UI
    with gr.Blocks(title="Agent Builder") as app:
        
        gr.Markdown(
            """
            <div style="text-align: center; padding: 15px 0;">
                <h1 style="margin: 0;">⚡ Agent Builder</h1>
                <p style="opacity: 0.7;">Design AI agents with tool simulation & Autogen export</p>
            </div>
            """
        )
        
        with gr.Row():
            # LEFT: Design Chat
            with gr.Column(scale=3):
                gr.Markdown("### 💬 Design Your Agent")
                
                chat = gr.Chatbot(
                    value=[{"role": "assistant", "content": "Hi! Describe the AI agent you want to create.\n\nExamples:\n• Purchase assistant for employees\n• Invoice processor with 3-way matching\n• Sourcing agent for RFP management"}],
                    height=420
                )
                
                with gr.Row():
                    msg = gr.Textbox(placeholder="Describe your agent...", show_label=False, scale=5)
                    send = gr.Button("Send", variant="primary", scale=1)
                
                with gr.Row():
                    reset = gr.Button("🔄 New", size="sm")
                    with gr.Column(scale=3):
                        agent_id_input = gr.Textbox(placeholder="Agent ID to load...", show_label=False, scale=2)
                    load_btn = gr.Button("📂 Load", size="sm")
                
                with gr.Accordion("📁 Saved Agents", open=False):
                    saved_list = gr.Markdown(get_agent_list())
                    refresh_btn = gr.Button("🔄 Refresh List", size="sm")
            
            # RIGHT: Configuration & Output
            with gr.Column(scale=3):
                agent_name = gr.Textbox(value="Untitled Agent", label="Agent Name", interactive=False)
                
                with gr.Tabs():
                    with gr.TabItem("📋 System Prompt"):
                        prompt_box = gr.Textbox(label="", lines=14, placeholder="System prompt appears here...")
                    
                    with gr.TabItem("🛠️ Tools JSON"):
                        tools_box = gr.Textbox(label="", lines=14, placeholder="Tool definitions...")
                    
                    with gr.TabItem("📘 Swagger/OpenAPI"):
                        swagger_box = gr.Textbox(label="", lines=14, placeholder="OpenAPI spec...")
                    
                    with gr.TabItem("🐍 Autogen Code"):
                        autogen_box = gr.Textbox(label="", lines=14, placeholder="Autogen-compatible Python code...")
                    
                    with gr.TabItem("🧪 Test Agent"):
                        test_chat = gr.Chatbot(height=220)
                        with gr.Row():
                            test_msg = gr.Textbox(placeholder="Test your agent...", show_label=False, scale=4)
                            test_send = gr.Button("Test", scale=1)
                        tool_log = gr.Markdown("*Tool execution logs will appear here*")
        
        # Events
        send.click(on_chat, [msg, chat], [chat, msg, prompt_box, tools_box, swagger_box, autogen_box, agent_name])
        msg.submit(on_chat, [msg, chat], [chat, msg, prompt_box, tools_box, swagger_box, autogen_box, agent_name])
        test_send.click(on_test, [test_msg, test_chat], [test_chat, test_msg, tool_log])
        test_msg.submit(on_test, [test_msg, test_chat], [test_chat, test_msg, tool_log])
        reset.click(on_reset, outputs=[chat, prompt_box, tools_box, swagger_box, autogen_box, agent_name, test_chat, tool_log])
        load_btn.click(on_load_agent, [agent_id_input], [chat, prompt_box, tools_box, swagger_box, autogen_box, agent_name])
        refresh_btn.click(lambda: get_agent_list(), outputs=[saved_list])
    
    return app


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not api_key:
        print("❌ AZURE_OPENAI_API_KEY required")
        sys.exit(1)
    
    from core.llm.llm_factory import LLMFactory
    llm = LLMFactory.create_zycus_gpt4o(api_key=api_key)
    print("✅ Connected to GPT-4o")
    
    app = create_workflow_creator_app(llm)
    port = int(os.getenv("GRADIO_SERVER_PORT", "7863"))
    print(f"🚀 Agent Builder: http://localhost:{port}")
    app.launch(
        server_port=port, 
        server_name="0.0.0.0",
        theme=gr.themes.Soft(primary_hue="orange", neutral_hue="slate")
    )
