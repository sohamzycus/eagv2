# fDOM MCP Client - Ollama Computer Control Agent

A Model Context Protocol (MCP) client that converts fDOM GUI state machine output into actionable computer control tasks using local Ollama LLM.

## 🌟 Features

- **🤖 Ollama Integration**: Uses local Ollama LLM for intelligent task planning
- **📊 5-Step Task Execution**: Execute computer tasks in exactly 5 steps
- **🔄 50-Iteration Exploration**: Systematic UI exploration with configurable iterations
- **🗺️ MAP Visualization**: Interactive HTML state graph visualization
- **🔌 MCP Protocol**: Full MCP server implementation for tool integration

## 📁 Project Structure

```
mcp_client/
├── __init__.py           # Package initialization
├── ollama_client.py      # Ollama LLM client for task planning
├── mcp_server.py         # MCP server implementation
├── fdom_map.py           # MAP visualization generator
├── task_executor.py      # Task and exploration executors
├── demo.py               # Demo script and CLI
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Ollama**: Install and run Ollama locally
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Start Ollama
   ollama serve
   
   # Pull a model (e.g., llama3.2)
   ollama pull llama3.2
   ```

2. **Python dependencies**:
   ```bash
   pip install requests
   ```

### Usage

#### 1. Check Prerequisites
```bash
python -m mcp_client.demo --check
```

#### 2. List Available Apps
```bash
python -m mcp_client.demo --list-apps
```

#### 3. Run a 5-Step Task
```bash
# Execute a specific task
python -m mcp_client.demo --app notepad --task "Open file menu and create new document"

# Dry run (plan only)
python -m mcp_client.demo --app notepad --task "Open file menu" --dry-run
```

#### 4. Run 50-Iteration Exploration
```bash
# Full 50 iterations with Ollama guidance
python -m mcp_client.demo --app notepad --explore --iterations 50

# Without Ollama (simple sequential)
python -m mcp_client.demo --app notepad --explore --iterations 50 --no-ollama
```

#### 5. Generate MAP Visualization
```bash
python -m mcp_client.demo --app notepad --generate-map
# Opens fdom_map.html in browser
```

#### 6. Interactive Mode
```bash
python -m mcp_client.demo --app notepad --interactive
```

## 📊 MCP Tools Available

| Tool | Description |
|------|-------------|
| `get_current_state` | Get current UI state and elements |
| `list_states` | List all known UI states |
| `get_elements` | Get interactive elements in a state |
| `find_element` | Search for element by name |
| `get_navigation_options` | Get available state transitions |
| `navigate_to_state` | Navigate to a specific state |
| `click_element` | Click on an element |
| `get_exploration_progress` | Get exploration statistics |

## 🧠 How It Works

### Task Execution Flow

1. **Load fDOM**: Load the UI state machine from JSON
2. **Plan with Ollama**: Send current state + task to LLM
3. **Get Action Steps**: LLM returns structured action plan
4. **Execute Steps**: Click elements, navigate states
5. **Track Results**: Log all actions and state changes

### Exploration Flow

1. **Initialize**: Load pending/explored node sets
2. **Select Target**: Use Ollama to pick interesting element
3. **Execute Click**: Simulate click via MCP
4. **Handle Transition**: Update state if changed
5. **Repeat**: Continue for N iterations

## 📈 Output Files

Results are saved to `S14B/outputs/`:

- `task_result_YYYYMMDD_HHMMSS.json` - Task execution results
- `exploration_APP_YYYYMMDD_HHMMSS.json` - Exploration results

## 🗺️ MAP Visualization

The MAP generates an interactive HTML visualization showing:

- **Nodes**: UI states as circles
- **Edges**: Navigation transitions with trigger labels
- **Statistics**: Element counts, exploration progress
- **Controls**: Zoom, pan, click to highlight

Open `apps/<app>/fdom_map.html` in a browser.

## 🔧 API Usage

```python
import asyncio
from mcp_client.ollama_client import OllamaClient
from mcp_client.task_executor import TaskExecutor, ExplorationExecutor

# Check Ollama
client = OllamaClient()
print(client.check_ollama_status())

# Execute a task
async def run_task():
    executor = TaskExecutor("notepad")
    result = await executor.execute_task(
        "Open file menu and save document",
        max_steps=5
    )
    print(result.to_dict())

asyncio.run(run_task())

# Run exploration
async def explore():
    executor = ExplorationExecutor("notepad")
    summary = await executor.run_exploration(max_iterations=50)
    print(summary)

asyncio.run(explore())
```

## 🔗 GitHub

This project is part of the Seraphine Agentic Pipeline (S14B).

Repository: [Your GitHub URL Here]

## 📜 License

MIT License

## 🙏 Acknowledgments

- Ollama team for the local LLM runtime
- Model Context Protocol specification
- Seraphine GUI detection pipeline

