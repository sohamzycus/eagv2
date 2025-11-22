# Hybrid Decision-Making Agent Architecture

## 🧠 System Overview

This is a **Perception-Decision-Action (PDA)** based AI agent framework that solves complex multi-step tasks using external tools through Model Context Protocol (MCP) servers.

## 📊 Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                          USER INPUT                                   │
│                     "Find ASCII sum of INDIA"                         │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     AGENT CONTEXT                                     │
│  ┌──────────────────────────────────────────────────────────┐        │
│  │ Session Manager │ Memory Manager │ Agent Profile          │        │
│  │ - Session ID    │ - History      │ - Strategy             │        │
│  │ - Step Tracking │ - Tool Results │ - Max Steps            │        │
│  │ - Task Progress │ - Success Tags │ - Planning Mode        │        │
│  └──────────────────────────────────────────────────────────┘        │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      AGENT LOOP (Main Control)                        │
│  ┌──────────────────────────────────────────────────────────┐        │
│  │  For each step (max 3 steps):                            │        │
│  │    For each lifeline (max 3 retries):                    │        │
│  │      1. Perception                                        │        │
│  │      2. Planning (Decision)                               │        │
│  │      3. Execution (Action)                                │        │
│  │      4. Result Validation                                 │        │
│  └──────────────────────────────────────────────────────────┘        │
└─────────┬────────────────────┬────────────────────┬──────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   PERCEPTION     │  │    DECISION      │  │     ACTION       │
│   (Modules)      │  │   (Strategy)     │  │   (Sandbox)      │
│                  │  │                  │  │                  │
│ ┌──────────────┐ │  │ ┌──────────────┐ │  │ ┌──────────────┐ │
│ │ Extract      │ │  │ │ Load Prompt  │ │  │ │ Python       │ │
│ │ Intent       │ │  │ │ (Conservative│ │  │ │ Sandbox      │ │
│ │ Entities     │ │  │ │  /Exploratory│ │  │ │ Execution    │ │
│ │ Tool Hints   │ │  │ │   Mode)      │ │  │ │              │ │
│ │              │ │  │ │              │ │  │ │ Real MCP     │ │
│ │ Select       │ │  │ │ Generate     │ │  │ │ Tool Calls   │ │
│ │ Relevant     │ │  │ │ solve()      │ │  │ │              │ │
│ │ MCP Servers  │ │  │ │ Function     │ │  │ │ Result       │ │
│ │              │ │  │ │              │ │  │ │ Parsing      │ │
│ └──────────────┘ │  │ └──────────────┘ │  │ └──────────────┘ │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                     │
         │                     │                     │
         └─────────────────────┴─────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      MULTI-MCP DISPATCHER                             │
│  ┌──────────────────────────────────────────────────────────┐        │
│  │  Tool Discovery & Routing:                               │        │
│  │  - Server 1 (Math): add, subtract, power, fibonacci...   │        │
│  │  - Server 2 (Documents): search_docs, extract_pdf...     │        │
│  │  - Server 3 (Web): search, fetch_url...                  │        │
│  │  - Server 4 (Memory): get_history, search_conversations  │        │
│  └──────────────────────────────────────────────────────────┘        │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      RESULT HANDLING                                  │
│  ┌──────────────────────────────────────────────────────────┐        │
│  │  if result.startswith("FINAL_ANSWER:"):                  │        │
│  │      → Return to user and exit                            │        │
│  │  elif result.startswith("FURTHER_PROCESSING_REQUIRED:"):  │        │
│  │      → Feed back as input to next step                    │        │
│  │  else:                                                     │        │
│  │      → Retry with lifeline or proceed to next step        │        │
│  └──────────────────────────────────────────────────────────┘        │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        MEMORY PERSISTENCE                             │
│  ┌──────────────────────────────────────────────────────────┐        │
│  │  memory/YYYY/MM/DD/session-{timestamp}-{uuid}.json       │        │
│  │  - Tool calls                                             │        │
│  │  - Tool results                                           │        │
│  │  - Success/failure tags                                   │        │
│  │  - Final answers                                          │        │
│  └──────────────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────────┘
```

## 🔄 Detailed Component Breakdown

### 1. **Agent Context** (`core/context.py`)
- **Purpose**: Manages session state and configuration
- **Components**:
  - `AgentProfile`: Loads agent configuration from `config/profiles.yaml`
  - `StrategyProfile`: Defines planning mode (conservative/exploratory), max steps, lifelines
  - `MemoryManager`: Handles session memory storage and retrieval
  - `session_id`: Unique identifier for each conversation session
  - `task_progress`: Tracks subtask execution status

### 2. **Agent Loop** (`core/loop.py`)
- **Purpose**: Main execution loop orchestrating the PDA cycle
- **Flow**:
  ```
  For step in [1, 2, 3]:  # max_steps = 3
      For lifeline in [0, 1, 2, 3]:  # max_lifelines_per_step = 3
          → Perception (understand query)
          → Decision (generate plan)
          → Action (execute plan)
          → Validate result
          if success: break
      if FINAL_ANSWER: return
      if FURTHER_PROCESSING_REQUIRED: continue with updated input
  ```
- **Key Features**:
  - Step-based retry mechanism with lifelines
  - Automatic input refinement for multi-step tasks
  - Sandbox execution of generated Python code

### 3. **Perception Module** (`modules/perception.py`)
- **Purpose**: Understand user intent and select relevant tools
- **Input**: User query + MCP server descriptions
- **Output**: `PerceptionResult` containing:
  - `intent`: What the user wants to achieve
  - `entities`: Important keywords/concepts
  - `tool_hint`: Suggested tool name (optional)
  - `selected_servers`: List of relevant MCP server IDs
- **LLM Call**: Uses Gemini/Ollama to analyze query and output structured JSON

### 4. **Decision Module** (`modules/decision.py`)
- **Purpose**: Generate executable Python plan using available tools
- **Strategy Selection** (`core/strategy.py`):
  - **Conservative Mode**: Plans ONE tool call at a time
  - **Exploratory Mode**: 
    - Parallel: Multiple independent tool calls
    - Sequential: Chained dependent tool calls
- **Output**: Complete Python `solve()` function with:
  - Tool usage docstrings
  - Proper input formatting
  - Result parsing logic
  - Return statement with `FINAL_ANSWER:` or `FURTHER_PROCESSING_REQUIRED:`

### 5. **Action Module** (`modules/action.py`)
- **Purpose**: Execute generated plan in sandboxed environment
- **Sandbox Features**:
  - Creates isolated Python module scope
  - Injects real MCP dispatcher
  - Limits max tool calls per plan (default: 5)
  - Safe execution with error handling
- **Result Processing**:
  - Extracts JSON results from tool responses
  - Formats output for user or next step
  - Handles exceptions gracefully

### 6. **Multi-MCP Dispatcher** (`core/session.py`)
- **Purpose**: Manage connections to multiple MCP servers
- **Stateless Design**: 
  - Discovers tools once during initialization
  - Creates fresh session per tool call
  - Maps tool names to server configurations
- **Tool Discovery**:
  - Scans all configured MCP servers
  - Builds `tool_map`: `{tool_name: {config, tool}}`
  - Builds `server_tools`: `{server_id: [tools]}`

### 7. **Memory Manager** (`modules/memory.py`)
- **Purpose**: Persist conversation history and tool usage
- **Storage Structure**:
  ```
  memory/
    2025/
      01/
        15/
          session-1736950800-a3f9e2.json
  ```
- **Memory Items**:
  - `run_metadata`: Session start/end
  - `tool_call`: Tool invocation record
  - `tool_output`: Tool result + success flag
  - `final_answer`: User-facing response
- **Features**:
  - Incremental save after each action
  - Success/failure tracking
  - Tag-based categorization

### 8. **Model Manager** (`modules/model_manager.py`)
- **Purpose**: Abstraction layer for LLM providers
- **Supported Models**:
  - Gemini (via Google GenAI SDK)
  - Ollama (local models via REST API)
- **Configuration**: Loaded from `config/models.json` and `profiles.yaml`

### 9. **MCP Servers** (`mcp_server_*.py`)
- **Server 1 (Math)**: Arithmetic, trigonometry, factorial, Fibonacci, string-to-ASCII conversion
- **Server 2 (Documents)**: PDF extraction, web scraping, FAISS-based document search
- **Server 3 (Web)**: DuckDuckGo search, HTML fetching
- **Server 4 (Memory)**: Historical conversation search (to be implemented)

## 🎯 Execution Flow Example

**Query**: "Find the ASCII values of characters in INDIA and then return sum of exponentials of those values."

### Step 1: Perception
```json
{
  "intent": "Convert string to ASCII then calculate exponential sum",
  "entities": ["INDIA", "ASCII", "exponential", "sum"],
  "tool_hint": "strings_to_chars_to_int",
  "selected_servers": ["math"]
}
```

### Step 2: Decision
```python
async def solve():
    # FUNCTION_CALL: 1
    input = {"input": {"string": "INDIA"}}
    result = await mcp.call_tool('strings_to_chars_to_int', input)
    numbers = json.loads(result.content[0].text)["result"]
    
    # FUNCTION_CALL: 2
    input = {"input": {"numbers": numbers}}
    result = await mcp.call_tool('int_list_to_exponential_sum', input)
    final = json.loads(result.content[0].text)["result"]
    
    return f"FINAL_ANSWER: {final}"
```

### Step 3: Action
- Executes `solve()` in sandbox
- Calls `strings_to_chars_to_int` → gets `[73, 78, 68, 73, 65]`
- Calls `int_list_to_exponential_sum` → calculates `e^73 + e^78 + e^68 + e^73 + e^65`
- Returns `FINAL_ANSWER: 4.2e33`

### Step 4: Result
- Agent detects `FINAL_ANSWER:` prefix
- Extracts and displays answer to user
- Saves session to memory
- Exits successfully

## 🔧 Configuration Files

### `config/profiles.yaml`
- Agent identity (name, description)
- Strategy settings (planning_mode, max_steps, lifelines)
- Memory configuration
- LLM provider selection
- MCP server definitions with capabilities

### `config/models.json`
- Model definitions (Gemini, Ollama, Phi4, Qwen, etc.)
- API endpoints and parameters
- Model-specific configurations

### `prompts/*.txt`
- `perception_prompt.txt`: Guides intent extraction and server selection
- `decision_prompt_conservative.txt`: Single tool call planning
- `decision_prompt_exploratory_*.txt`: Multi-tool planning strategies

## 🧩 Key Design Patterns

1. **Stateless MCP Connections**: Fresh session per tool call for reliability
2. **Lifeline System**: Automatic retry with limited attempts
3. **Sandbox Execution**: Isolated Python environment for generated code
4. **Hierarchical Memory**: Date-based storage for easy navigation
5. **Pluggable Strategies**: Conservative vs Exploratory planning modes
6. **FURTHER_PROCESSING_REQUIRED**: Mechanism for multi-step reasoning
7. **Tool Discovery**: Dynamic mapping from multiple MCP servers

## 🚀 Advantages

- **Modular**: Clean separation of Perception, Decision, Action
- **Extensible**: Easy to add new MCP servers and tools
- **Fault-Tolerant**: Lifeline-based retry mechanism
- **Observable**: Comprehensive logging and memory tracking
- **Flexible**: Configurable strategies and model providers
- **Multi-Step Capable**: Handles complex tasks requiring multiple tools

## 🐛 Known Limitations

1. Fixed path separators in `profiles.yaml` (Windows-specific)
2. No historical conversation indexing yet
3. Limited heuristic validation on inputs/outputs
4. Conservative prompt is verbose (729 words)
5. Memory retrieval not integrated into perception stage

