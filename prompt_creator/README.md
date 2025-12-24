# Prompt Creator

**A Prompt-as-a-Product System for AI Procurement Assistants**

Generate production-ready system prompts equivalent to "Buy Agent v5.0" from minimal business user input, with full reasoning visibility, MCP-Zero tooling, and SOLID-compliant architecture.

## 🔑 LLM Support

The system uses **Azure OpenAI GPT-4o** as the primary execution model, with support for:

| Model | Status | Notes |
|-------|--------|-------|
| Azure OpenAI GPT-4o | ✅ Fully Supported | Primary model |
| OpenAI GPT-4o | ✅ Fully Supported | Fallback |
| GPT-4.1 | 🔜 Planned | Future support |
| GPT-5.1 / 5.2 | 🔜 Planned | Future support |
| Claude Sonnet/Opus | 🔜 Planned | Prompt adaptation ready |

### Quick Start with Azure OpenAI

```bash
# Set environment variables
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o"
export AZURE_OPENAI_API_KEY="your-api-key"

# Run the system
python main.py
```

### Quick Start with OpenAI

```bash
export OPENAI_API_KEY="sk-your-api-key"
python main.py
```

## 🎯 Overview

The Prompt Creator solves the gap between business users and agentic AI:

- **Business users** describe their needs in plain language
- **System generates** enterprise-grade prompts with:
  - Step ordering (STEP_01 → STEP_20)
  - COVE validation logic
  - Guardrails and constraints
  - MCP-Zero tool specifications
- **Full traceability** via reasoning persistence

## 🏗 Architecture

```
┌───────────────────────────────────────────┐
│ Business User (Natural Language)           │
└───────────────────────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│ Gradio UI (Conversation + Reasoning View) │
└───────────────────────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│ Intake Orchestrator Agent (Meta-Agent)    │
│ - Controls flow                           │
│ - Enforces guardrails                     │
└───────────────────────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│ Clarification Agent                       │
│ - Asks minimal follow-ups                 │
│ - Maps intent → workflow patterns         │
└───────────────────────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│ Prompt Composer Agent                     │
│ - Generates system prompts                │
│ - Injects steps, COVEs, guardrails         │
└───────────────────────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│ Tool Synthesizer Agent                    │
│ - Creates MCP-Zero tool specs             │
│ - Maps steps → tools                      │
└───────────────────────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│ Persistence + Reasoning Store             │
│ (JSONL / SQLite / In-Memory)              │
└───────────────────────────────────────────┘
```

## 📦 Project Structure

```
prompt_creator/
│
├── core/
│   ├── llm/                        # LLM ABSTRACTION LAYER
│   │   ├── llm_client.py           # Abstract LLM interface (DIP)
│   │   ├── llm_config.py           # Configuration & model families
│   │   ├── llm_factory.py          # Factory for LLM creation
│   │   ├── azure_openai_client.py  # Azure OpenAI implementation
│   │   └── llm_logger.py           # LLM call logging
│   │
│   ├── agents/
│   │   ├── base_agent.py           # Abstract agent with LLM injection
│   │   ├── agent_factory.py        # Factory with LLM dependency injection
│   │   ├── intake_orchestrator.py  # Meta-agent for flow control
│   │   ├── clarification_agent.py  # LLM-powered requirements gathering
│   │   ├── prompt_composer_agent.py # LLM-powered prompt generation
│   │   └── tool_synthesizer_agent.py # LLM-powered tool synthesis
│   │
│   ├── workflow/
│   │   ├── step.py                 # Step definitions
│   │   ├── cove.py                 # COVE validation rules
│   │   ├── workflow_engine.py      # Workflow execution
│   │   └── step_registry.py        # Step factory
│   │
│   ├── prompt/
│   │   ├── prompt_builder.py       # Builder pattern for prompts
│   │   ├── prompt_sections.py      # Composite pattern for sections
│   │   └── guardrails.py           # Guardrail definitions
│   │
│   ├── tools/
│   │   ├── tool_contract.py        # MCP-Zero contracts
│   │   └── mcp_zero_adapter.py     # Adapter for tool generation
│   │
│   └── reasoning/
│       ├── reasoning_node.py       # Reasoning trace nodes
│       ├── reasoning_store.py      # Persistence layer
│       └── audit_logger.py         # Compliance logging
│
├── domain/
│   ├── business_intent.py          # BusinessIntent model
│   └── clarification_model.py      # Clarification Q&A models
│
├── ui/
│   ├── gradio_app.py               # Gradio UI with live LLM
│   └── views.py                    # View components
│
├── main.py                         # Entry point with LLM wiring
├── requirements.txt
└── README.md
```

## 🔌 LLM Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AGENT LAYER                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │Clarification│  │  Prompt     │  │    Tool     │     │
│  │   Agent     │  │  Composer   │  │ Synthesizer │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │             │
│         └────────────────┼────────────────┘             │
│                          │                              │
│                          ▼                              │
│              ┌───────────────────────┐                  │
│              │   LLMClient (DIP)     │  ← Abstract      │
│              └───────────┬───────────┘                  │
└──────────────────────────┼──────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────┐
│              LLM ABSTRACTION LAYER                      │
│                          │                              │
│              ┌───────────▼───────────┐                  │
│              │     LLM Factory       │                  │
│              └───────────┬───────────┘                  │
│                          │                              │
│    ┌─────────────────────┼─────────────────────┐        │
│    │                     │                     │        │
│    ▼                     ▼                     ▼        │
│ ┌──────────┐       ┌──────────┐         ┌──────────┐   │
│ │  Azure   │       │  OpenAI  │         │  Claude  │   │
│ │ GPT-4o   │       │  GPT-4o  │         │  Sonnet  │   │
│ └──────────┘       └──────────┘         └──────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Key Principles:**
- Agents NEVER import OpenAI/Azure directly
- All LLM calls go through `LLMClient` abstraction
- Switching models = changing config, not code
- Every LLM call is logged for governance

## 🚀 Quick Start

### Installation

```bash
cd prompt_creator
pip install -r requirements.txt
```

### Run the UI

```bash
python main.py
```

Then open http://localhost:7860 in your browser.

### Run Demo Mode

```bash
python main.py --demo
```

This generates a sample prompt without user interaction.

### Run CLI Mode

```bash
python main.py --cli
```

Interactive command-line interface.

## 🎨 Design Patterns Used

### Behavioral Patterns

- **Strategy** → Workflow variants (catalog / quote / non-catalog)
- **Chain of Responsibility** → STEP execution
- **Template Method** → Agent execution skeleton

### Structural Patterns

- **Facade** → Prompt generation API
- **Adapter** → MCP-Zero tools
- **Composite** → Prompt sections

### Creational Patterns

- **Factory** → Agent creation
- **Builder** → System prompt assembly
- **Singleton** → Agent factory

## 📋 SOLID Compliance

| Principle | Implementation |
|-----------|---------------|
| **Single Responsibility** | Each agent has one job |
| **Open/Closed** | Extend via new agents, not modification |
| **Liskov Substitution** | Agents are interchangeable via interface |
| **Interface Segregation** | Minimal agent interface |
| **Dependency Inversion** | Agents depend on abstractions |

## 🔧 Key Features

### Business User Experience

- Plain language input
- Maximum 5 clarifying questions
- No technical jargon exposed
- Progress visibility

### Generated Outputs

- **System Prompt**: 10,000+ character production-ready prompt
- **MCP-Zero Tools**: Complete tool specifications in JSON
- **Reasoning Trace**: Full decision log for debugging

### Agent Capabilities

| Agent | Capabilities |
|-------|-------------|
| Intake Orchestrator | routing, governance, state_control |
| Clarification Agent | clarification |
| Prompt Composer | prompt_generation |
| Tool Synthesizer | tool_synthesis |

## 📊 Example Output

### Input (Business User)
```
I want an AI that helps employees raise purchase requests
and routes them correctly
```

### Clarifying Questions (Max 5)
1. Do users buy goods, services, or both?
2. Should the system support quote uploads?
3. Is value-based routing needed?

### Generated Prompt (Preview)
```markdown
# System Prompt: Intelligent Procurement Assistant

## System Identity
You are an **Intelligent Procurement Assistant**...

## Core Behavior Rules
### Deterministic Execution
1. **Follow Step Order** - Execute steps in the defined sequence
2. **No Branching** - Only one execution path at a time
...

## Workflow Steps
### STEP_01: REQUEST_INTAKE
**Purpose:** Capture initial purchase request from user
**Required Inputs:** user_message
**Routing:** IF request_captured → STEP_02
...

## COVE Validation
🔴 **COVE_01**: Steps must be executed in order. No step may be skipped.
🔴 **COVE_02**: Never assume information not explicitly provided.
...
```

### Generated Tools (MCP-Zero)
```json
{
  "name": "Employee Procurement Assistant_tools",
  "version": "1.0.0",
  "tools": [
    {
      "tool_name": "catalog_search",
      "description": "Search company product catalog",
      "type": "internal",
      "input_schema": {...},
      "mcp_zero": {
        "endpoint": "/api/catalog/search",
        "method": "GET",
        "auth_required": true
      }
    },
    ...
  ]
}
```

## 🔍 Reasoning Visibility

Every agent decision is logged:

```json
{
  "session_id": "uuid",
  "actor": "clarification_agent",
  "input": "I want a procurement bot",
  "output": "BusinessIntent created",
  "decision": "Proceed to Prompt Composer",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

View in:
- **Gradio UI**: Reasoning tab
- **JSONL files**: `./reasoning_data/`
- **Audit logs**: `./audit_logs/`

## 🛠 Extending the System

### Add a New Agent

```python
from prompt_creator.core.agents.base_agent import Agent, AgentCapability

class MyCustomAgent(Agent):
    def __init__(self):
        super().__init__(
            name="my_custom_agent",
            capabilities=[AgentCapability.CUSTOM],
        )

    def can_handle(self, context: AgentContext) -> bool:
        return context.current_step == "MY_STEP"

    def execute(self, context: AgentContext) -> AgentResponse:
        # Your logic here
        return AgentResponse.success_response(...)
```

### Add New COVE Rules

```python
from prompt_creator.core.workflow.cove import FunctionalCOVERule, COVESeverity

my_rule = FunctionalCOVERule(
    rule_id="COVE_CUSTOM",
    name="My Custom Rule",
    description="...",
    validator=lambda ctx: ctx.get("my_condition", False),
    error_message="Validation failed",
    severity=COVESeverity.CRITICAL,
)
```

### Add New Steps

```python
from prompt_creator.core.workflow.step_registry import StepDefinition

my_step = StepDefinition(
    step_id="STEP_CUSTOM",
    name="MY_CUSTOM_STEP",
    description="...",
    required_inputs=["input1", "input2"],
    outputs=["output1"],
    routing={"condition": "NEXT_STEP"},
)
```

## 📝 License

MIT License

## 🤝 Contributing

1. Follow SOLID principles
2. Add tests for new features
3. Update documentation
4. Run `black` and `mypy` before submitting

---

Built with ❤️ for enterprise AI adoption

