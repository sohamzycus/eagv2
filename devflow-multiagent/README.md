# 🚀 DevFlow Multi-Agent System

## Developer Productivity Accelerator

A **novel multi-agent architecture** powered by **phi4 LLM** (via Ollama) that automates developer workflows with **REAL analysis** of your actual codebase.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-phi4-green.svg)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Problem Statement

Developers spend **30-40% of their time** on repetitive, non-coding tasks:
- Writing standup updates
- Creating PR descriptions
- Reviewing code manually
- Tracking technical debt
- Updating documentation

**DevFlow** automates these workflows using a coordinated multi-agent system with **real LLM-powered analysis**.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 📝 **Standup Summary** | Generates standup from real git commits |
| 📄 **PR Description** | Creates PR templates from branch changes |
| 🔍 **Code Review** | AI-powered code analysis with suggestions |
| 📊 **Tech Debt** | Identifies and prioritizes technical debt |
| 🔒 **Dependency Check** | Security and version analysis |
| 📚 **Documentation** | Auto-generates docs from code |

---

## 🏗️ Architecture

```
                         ┌─────────────────┐
                         │   COORDINATOR   │
                         │   (Orchestrator)│
                         └────────┬────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  PERCEPTION   │       │   RETRIEVER     │       │     MEMORY      │
│    AGENT      │       │     AGENT       │       │     AGENT       │
└───────┬───────┘       └────────┬────────┘       └────────┬────────┘
        │                        │                         │
        └────────────┬───────────┘                         │
                     ▼                                     │
              ┌─────────────┐                              │
              │  PLAN/STEP  │◄─────────────────────────────┘
              └──────┬──────┘
                     ▼
              ┌─────────────┐         ┌─────────────┐
              │  EXECUTOR   │────────▶│   CRITIC    │
              └─────────────┘         └──────┬──────┘
                     │                       │
                     │    ┌──────────────────┤ (Replan)
                     ▼    ▼                  │
              ┌─────────────────────────────────┐
              │        DECISION AGENT           │
              │      (Powered by phi4 LLM)      │
              └─────────────────────────────────┘
```

---

## 🤖 LLM Integration

DevFlow uses **local LLM** via Ollama - no cloud APIs required!

| Model | Size | Purpose |
|-------|------|---------|
| **phi4** | 9.1 GB | Text generation, analysis |
| **nomic-embed-text** | 274 MB | Vector embeddings |

```python
from llm import generate

response = await generate(
    prompt="Summarize these git commits...",
    system="You are a developer assistant."
)
```

---

## 🚀 Quick Start

### Prerequisites

```bash
# 1. Install Ollama (if not installed)
brew install ollama

# 2. Pull required models
ollama pull phi4
ollama pull nomic-embed-text

# 3. Verify models
ollama list
```

### Run DevFlow

```bash
# Navigate to project
cd devflow-multiagent

# Option 1: Interactive CLI
python3 main.py

# Option 2: Demo (3 example queries)
python3 demo_run.py

# Option 3: Real Analysis (uses phi4 on actual repo)
python3 real_analysis.py
```

---

## 📊 Demo Output

Running `python3 real_analysis.py` produces:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║           🚀 DevFlow REAL ANALYSIS - Using phi4 Ollama Model 🚀              ║
╚══════════════════════════════════════════════════════════════════════════════╝

════════════════════════════════════════════════════════════════════════════════
  📝 REAL STANDUP SUMMARY - eagv2 Repository
════════════════════════════════════════════════════════════════════════════════

  ▶ Fetching git commits...
  ▶ 🤖 Using phi4 to generate standup summary...

────────────────────────────────────────────────────────────────────────────────
📋 Generated Standup (via phi4):

## What I Worked On
- Implemented Fibonacci sequence generation and exponential sum calculation
- Added hybrid decision-making video and updated API key security
- Developed core components of Hybrid Decision-Making Agent Framework
...

════════════════════════════════════════════════════════════════════════════════
  🔍 REAL CODE REVIEW - DevFlow Main Module
════════════════════════════════════════════════════════════════════════════════

📋 Code Review (via phi4):
### Strengths
- Modular Design: Well-organized with clear separation of concerns
- ANSI Colors: Enhances readability

### Issues
- Hardcoded Paths: Using sys.path.insert can be error-prone
...
```

---

## 📁 Project Structure

```
devflow-multiagent/
├── llm/                         # 🆕 LLM Integration
│   ├── __init__.py
│   └── ollama_client.py         # phi4 + nomic-embed-text
├── coordinator/                 # Central Orchestration
│   └── orchestrator.py
├── agents/                      # 5 Specialized Agents
│   ├── base_agent.py
│   ├── perception_agent.py      # Query understanding
│   ├── retriever_agent.py       # Real git/file retrieval
│   ├── critic_agent.py          # Quality validation
│   ├── memory_agent.py          # History management
│   └── decision_agent.py        # Response synthesis
├── execution/                   # Plan Execution
│   ├── plan_manager.py
│   └── step_executor.py
├── tools/                       # Developer Tools
│   ├── git_analyzer.py
│   └── code_reviewer.py
├── memory/                      # Session Persistence
├── prompts/                     # Agent Prompts
├── config/                      # Configuration
├── main.py                      # Interactive CLI
├── demo_run.py                  # Demo script
├── real_analysis.py             # Real analysis script
├── ARCHITECTURE.md              # Full architecture docs
└── YOUTUBE_SCRIPT.md            # Video recording guide
```

---

## 🔧 Configuration

Edit `config/settings.yaml`:

```yaml
llm:
  provider: "ollama"
  model: "phi4"
  temperature: 0.3
  max_tokens: 4096
  base_url: "http://localhost:11434"

agents:
  perception:
    confidence_threshold: 0.7
  critic:
    validation_strictness: "medium"
```

---

## 🎬 Demo Queries

```
🧑 DevFlow ▸ What did I work on yesterday?
→ Generates standup from real git commits

🧑 DevFlow ▸ Review code in main.py
→ AI-powered code review with suggestions

🧑 DevFlow ▸ Find tech debt in the project
→ Scans repo and prioritizes issues
```

---

## 📈 Code Statistics

| Metric | Value |
|--------|-------|
| Python Files | 20+ |
| Lines of Code | ~5000 |
| Agents | 5 specialized |
| External Dependencies | 0 (for LLM client) |

---

## 🎯 Design Principles

1. **Real Data** - Uses actual git history, real code files
2. **Local LLM** - No cloud APIs, runs on phi4 via Ollama
3. **Zero Dependencies** - LLM client uses only stdlib
4. **Separation of Concerns** - Each agent has single responsibility
5. **Self-Healing** - Critic-Replan loop handles failures
6. **Developer Focus** - Optimized for developer workflows

---

## 📚 Documentation

- [Architecture Guide](ARCHITECTURE.md) - Full system architecture
- [YouTube Script](YOUTUBE_SCRIPT.md) - Video recording guide

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) - Local LLM serving
- [phi4](https://huggingface.co/microsoft/phi-4) - Microsoft's compact LLM

---

## 📄 License

MIT License - Built for Developer Productivity Hackathon

---

## 👤 Author

**Soham Niyogi**

---

*Powered by phi4 Ollama Model* 🤖
