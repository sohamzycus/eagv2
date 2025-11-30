# 🏗️ DevFlow Architecture

## Multi-Agent Developer Productivity System

**Powered by phi4 Ollama Model for Real LLM Analysis**

---

## 📊 System Architecture Diagram

```
                              ┌─────────────────────────────────────┐
                              │                                     │
                              │      🎯 C O O R D I N A T O R       │
                              │           (Orchestrator)            │
                              │                                     │
                              │   • Routes queries through pipeline │
                              │   • Manages agent communication     │
                              │   • Coordinates LLM calls (phi4)    │
                              │                                     │
                              └─────────────────┬───────────────────┘
                                                │
           ┌────────────────────────────────────┼────────────────────────────────────┐
           │                                    │                                    │
           ▼                                    ▼                                    ▼
┌─────────────────────────┐          ┌─────────────────────────┐          ┌─────────────────────────┐
│                         │          │                         │          │                         │
│   🧠 PERCEPTION AGENT   │          │   🔍 RETRIEVER AGENT    │          │    🧠 MEMORY AGENT      │
│                         │          │                         │          │                         │
│ • Intent classification │          │ • Git history (real)    │          │ • Session state         │
│ • Entity extraction     │          │ • File retrieval        │          │ • History recall        │
│ • Query understanding   │          │ • Context gathering     │          │ • Similar queries       │
│                         │          │                         │          │                         │
└────────────┬────────────┘          └────────────┬────────────┘          └────────────┬────────────┘
             │                                    │                                    │
             └────────────────────┬───────────────┘                                    │
                                  │                                                    │
                                  ▼                                                    │
                      ┌───────────────────────────┐                                    │
                      │                           │                                    │
                      │      📋 PLAN MANAGER      │◄───────────────────────────────────┘
                      │                           │
                      │ • Intent-based templates  │
                      │ • Step sequencing         │
                      │ • Dynamic routing         │
                      │                           │
                      └─────────────┬─────────────┘
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │                           │
                      │     ⚙️ STEP EXECUTOR      │
                      │                           │
                      │ • Tool invocation         │
                      │ • Git command execution   │
                      │ • LLM calls (phi4)        │
                      │                           │
                      └─────────────┬─────────────┘
                                    │
                                    ▼
                      ┌───────────────────────────┐           ┌─────────────────────────┐
                      │                           │           │                         │
                      │     🔎 CRITIC AGENT       │──────────▶│    🔄 PLAN REWRITE      │
                      │                           │           │                         │
                      │ • Output validation       │   Fail    │ • Modify plan           │
                      │ • Quality scoring         │◀──────────│ • Add improvement steps │
                      │ • LLM-based critique      │           │ • Retry execution       │
                      │                           │           │                         │
                      └─────────────┬─────────────┘           └─────────────────────────┘
                                    │
                                    │ Pass
                                    ▼
                      ┌───────────────────────────────────────┐
                      │                                       │
                      │          🎯 DECISION AGENT            │
                      │                                       │
                      │   • Response synthesis (phi4)         │
                      │   • Output formatting (Markdown)      │
                      │   • Follow-up suggestions             │
                      │                                       │
                      └───────────────────────────────────────┘
                                    │
                                    ▼
                            ┌─────────────┐
                            │   OUTPUT    │
                            │   TO USER   │
                            └─────────────┘
```

---

## 🤖 LLM Integration (phi4 + Ollama)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      OLLAMA LOCAL SERVER                            │
│                    http://localhost:11434                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────────────┐         ┌─────────────────────────────┐   │
│   │       phi4          │         │    nomic-embed-text         │   │
│   │   (9.1 GB model)    │         │     (274 MB model)          │   │
│   │                     │         │                             │   │
│   │  • Text generation  │         │  • Vector embeddings        │   │
│   │  • Code review      │         │  • Semantic search          │   │
│   │  • Summarization    │         │  • Similarity matching      │   │
│   │  • Analysis         │         │                             │   │
│   └─────────────────────┘         └─────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DevFlow LLM Client                             │
│                   llm/ollama_client.py                              │
├─────────────────────────────────────────────────────────────────────┤
│   • Async HTTP requests via urllib (no external deps)              │
│   • generate() - Text generation with phi4                          │
│   • embed() - Vector embeddings with nomic-embed-text               │
│   • Configurable temperature, max_tokens, timeout                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

```
User Query: "What did I work on yesterday?"
    │
    ▼
┌─────────────────┐     ┌─────────────────────────────────────────────┐
│   Perception    │────▶│              AgentContext                   │
│     Agent       │     │  • query_id, original_query                 │
│                 │     │  • current_understanding (intent, entities) │
│ Intent: standup │     │  • retrieved_context (git commits)          │
│ Conf: 0.95      │     │  • execution_history, memory_recalls        │
└─────────────────┘     └──────────────────────┬──────────────────────┘
                                               │
                  ┌────────────────────────────┴────────────────────────┐
                  │                                                     │
                  ▼                                                     ▼
      ┌───────────────────┐                               ┌───────────────────┐
      │    Retriever      │                               │     Memory        │
      │      Agent        │                               │      Agent        │
      │                   │                               │                   │
      │ • git log (real)  │                               │ • Session lookup  │
      │ • git diff (real) │                               │ • Similar queries │
      │ • File contents   │                               │                   │
      └─────────┬─────────┘                               └─────────┬─────────┘
                │                                                   │
                └─────────────────────┬─────────────────────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │    Plan Manager       │
                          │                       │
                          │ Steps:                │
                          │ 1. git_fetch_commits  │
                          │ 2. summarize_activity │
                          │ 3. format_standup     │
                          └───────────┬───────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │    Step Executor      │
                          │                       │
                          │ Execute each step     │
                          │ Call phi4 for summary │
                          └───────────┬───────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │      Critic           │
                          │                       │
                          │ Scores:               │
                          │ • Completeness: 0.9   │
                          │ • Accuracy: 0.85      │
                          │ • Relevance: 0.95     │
                          │                       │
                          │ Verdict: APPROVED ✅   │
                          └───────────┬───────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │     Decision          │
                          │                       │
                          │ Generate final        │
                          │ formatted response    │
                          │ using phi4            │
                          └───────────┬───────────┘
                                      │
                                      ▼
                              📋 Standup Summary
                              (Markdown formatted)
```

---

## 🧩 Component Details

### 1. Coordinator (Orchestrator)

The central brain that routes queries through the agent pipeline.

```python
class Orchestrator:
    """
    Central coordinator for the multi-agent system.
    
    Pipeline stages:
    1. Perception → Understand query
    2. Retrieval + Memory → Gather context (parallel)
    3. Planning → Create execution plan
    4. Execution → Run plan steps + LLM calls
    5. Critique → Validate output
    6. Decision → Generate final response with phi4
    """
```

**Key Responsibilities:**
- Route queries to appropriate agents
- Manage shared context (`AgentContext`)
- Handle pipeline state transitions
- Coordinate replan loops

---

### 2. LLM Client (Ollama)

Integration with local Ollama models for real AI-powered analysis.

```python
class OllamaClient:
    """
    Async client for Ollama API.
    
    Models:
    - phi4: Text generation (9.1 GB)
    - nomic-embed-text: Embeddings (274 MB)
    
    Features:
    - Zero external dependencies (uses urllib)
    - Async execution via thread pool
    - Configurable temperature and tokens
    """
```

**Usage:**
```python
from llm import generate, embed

# Generate text with phi4
response = await generate(
    prompt="Summarize these git commits...",
    system="You are a developer assistant."
)

# Generate embeddings
vector = await embed("What did I work on yesterday?")
```

---

### 3. Perception Agent

First agent in the pipeline - understands what the developer wants.

```python
class PerceptionAgent(BaseAgent):
    """
    Classifies intents using pattern matching:
    - standup_summary
    - pr_description
    - code_review
    - tech_debt
    - dependency_check
    - documentation
    """
```

---

### 4. Retriever Agent

Gathers REAL context from the actual repository.

```python
class RetrieverAgent(BaseAgent):
    """
    Real data sources:
    - git log (actual commits)
    - git diff (real changes)
    - File contents (real code)
    - Dependency manifests
    """
```

---

### 5. Critic Agent

Validates outputs using quality scoring.

```python
class CriticAgent(BaseAgent):
    """
    Quality dimensions:
    - Completeness (0-1)
    - Accuracy (0-1)
    - Relevance (0-1)
    - Actionability (0-1)
    
    Verdicts:
    - APPROVED → proceed
    - NEEDS_IMPROVEMENT → minor fixes
    - REPLAN → create new plan
    - REJECTED → cannot proceed
    """
```

---

### 6. Decision Agent

Synthesizes final response using phi4 LLM.

```python
class DecisionAgent(BaseAgent):
    """
    Uses phi4 for:
    - Standup summary generation
    - PR description creation
    - Code review feedback
    - Tech debt analysis
    - Documentation generation
    """
```

---

## 📁 Directory Structure

```
devflow-multiagent/
│
├── llm/                         # 🆕 LLM Integration
│   ├── __init__.py
│   └── ollama_client.py         # phi4 + nomic-embed-text
│
├── coordinator/                 # Central Orchestration
│   ├── __init__.py
│   └── orchestrator.py          # Main coordinator logic
│
├── agents/                      # Specialized Agents
│   ├── __init__.py
│   ├── base_agent.py            # Abstract base class
│   ├── perception_agent.py      # Query understanding
│   ├── retriever_agent.py       # Context retrieval (real git)
│   ├── critic_agent.py          # Output validation
│   ├── memory_agent.py          # History management
│   └── decision_agent.py        # Response generation
│
├── execution/                   # Plan Execution
│   ├── __init__.py
│   ├── plan_manager.py          # Plan creation/rewrite
│   └── step_executor.py         # Step execution
│
├── tools/                       # Developer Tools
│   ├── __init__.py
│   ├── git_analyzer.py          # Real git operations
│   └── code_reviewer.py         # Code analysis
│
├── memory/                      # Persistence
│   ├── __init__.py
│   └── context_store.py         # Session storage
│
├── mcp_bridge/                  # Tool Integration
│   ├── __init__.py
│   └── tool_dispatcher.py       # Tool dispatch
│
├── prompts/                     # Agent Prompts
│   ├── perception.txt
│   ├── planning.txt
│   ├── critic.txt
│   └── decision.txt
│
├── config/                      # Configuration
│   ├── settings.yaml            # Agent settings
│   └── tools.yaml               # Tool definitions
│
├── sessions/                    # Session Data (generated)
│
├── main.py                      # Interactive CLI
├── demo_run.py                  # Demo (3 queries)
├── real_analysis.py             # 🆕 Real repo analysis with phi4
├── requirements.txt
├── README.md
├── ARCHITECTURE.md              # This file
└── YOUTUBE_SCRIPT.md            # Video recording guide
```

---

## 🚀 Running Real Analysis

### Prerequisites
```bash
# Ensure Ollama is running with phi4
ollama list
# Should show: phi4:latest, nomic-embed-text:latest
```

### Commands

```bash
cd devflow-multiagent

# Interactive CLI
python3 main.py

# Demo (3 example queries)
python3 demo_run.py

# 🆕 Real Analysis (uses phi4 on actual repo)
python3 real_analysis.py
```

### Real Analysis Output

The `real_analysis.py` script performs:

1. **📝 Standup Summary**
   - Fetches real git commits from eagv2 repo
   - Uses phi4 to generate formatted standup

2. **🔍 Code Review**
   - Reads actual Python files
   - Uses phi4 for code analysis and suggestions

3. **📊 Tech Debt Analysis**
   - Scans real repository structure
   - Counts TODO/FIXME markers
   - Uses phi4 for actionable recommendations

---

## 🔧 Novel Design Patterns

### 1. State Machine Pattern for Agents

```python
class AgentState(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
```

### 2. Shared Context Accumulation

```python
@dataclass
class AgentContext:
    query_id: str
    original_query: str
    current_understanding: Dict      # From Perception
    retrieved_context: List          # From Retriever (real data)
    execution_history: List          # From Executor
    memory_recalls: List             # From Memory
    critiques: List                  # From Critic
```

### 3. LLM-Powered Analysis

```python
# Real git analysis with phi4
commits = await run_git_command("log", "--oneline", "-10")
analysis = await generate(
    f"Analyze these commits: {commits}",
    system="You are a developer assistant."
)
```

### 4. Self-Healing Replan Loop

```
Executor → Critic → [REPLAN] → Plan Rewrite → Executor → Critic → [APPROVED]
```

---

## 📈 Metrics & Observability

Each agent tracks its own metrics:

```python
metrics = {
    "processed": int,      # Total queries
    "succeeded": int,      # Successful
    "failed": int,         # Failed
    "avg_time_ms": float   # Average latency
}
```

Pipeline tracking:

```python
pipeline = {
    "query_id": str,
    "final_stage": str,
    "stages_traversed": int,
    "replans": int,
    "llm_calls": int       # 🆕 Track phi4 calls
}
```

---

## 🎯 Design Principles

1. **Real Data**: Uses actual git history, real code files
2. **Local LLM**: No cloud APIs, runs on phi4 via Ollama
3. **Zero Dependencies**: LLM client uses only stdlib (urllib)
4. **Separation of Concerns**: Each agent has single responsibility
5. **Extensibility**: Easy to add new agents or tools
6. **Fault Tolerance**: Replan loop handles failures gracefully
7. **Developer Focus**: Optimized for developer workflows

---

## 📚 References

- Multi-Agent Systems: Coordination patterns
- Agentic AI: Perception-Decision-Action loops
- Developer Experience: Productivity workflows
- Ollama: Local LLM serving

---

*Built for Developer Productivity Hackathon*
*Powered by phi4 Ollama Model*
