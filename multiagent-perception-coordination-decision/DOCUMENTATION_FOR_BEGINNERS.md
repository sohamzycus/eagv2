# 🧠 Multi-Agent Perception-Coordination-Decision Framework
## A Beginner's Guide to Understanding Agentic AI

---

## 📚 Table of Contents

1. [What is This Project?](#what-is-this-project)
2. [Why Do We Need AI Agents?](#why-do-we-need-ai-agents)
3. [The Three Core Concepts](#the-three-core-concepts)
4. [Architecture Overview](#architecture-overview)
5. [Component Deep Dive](#component-deep-dive)
6. [How It All Works Together](#how-it-all-works-together)
7. [The Tools (MCP Servers)](#the-tools-mcp-servers)
8. [Memory System](#memory-system)
9. [Heuristics - Safety First](#heuristics---safety-first)
10. [Step-by-Step Example](#step-by-step-example)
11. [Key Files Explained](#key-files-explained)
12. [Running the System](#running-the-system)
13. [Glossary](#glossary)

---

## 🤔 What is This Project?

Imagine you have a really smart assistant that can:
- **Understand** what you're asking (even if you're vague)
- **Plan** how to solve your problem step by step
- **Use tools** like calculators, document searchers, or web browsers
- **Learn from past conversations** to do better next time
- **Know when to stop** and give you the answer

This project is exactly that - an **AI Agent** that thinks, plans, acts, and learns!

### Real-World Analogy 🏠

Think of it like a **personal assistant** who:
1. **Listens** to your request ("Find me a good Italian restaurant nearby")
2. **Understands** what you want (food, Italian, close by)
3. **Plans** how to help (search Google, check reviews, look at distance)
4. **Acts** by using tools (opens browser, searches, reads reviews)
5. **Responds** with a helpful answer ("Here are 3 great options...")

---

## 🎯 Why Do We Need AI Agents?

### The Problem with Regular AI (like ChatGPT)

Regular AI models can only:
- Answer based on what they were trained on
- Cannot browse the internet
- Cannot use calculators
- Cannot read your documents
- Cannot remember your past conversations

### What Agents Add

AI Agents can:
- ✅ **Use external tools** (calculators, search engines, document readers)
- ✅ **Remember past conversations** and learn from them
- ✅ **Break complex problems** into smaller steps
- ✅ **Recover from errors** and try different approaches
- ✅ **Know when they're done** vs. need more work

---

## 🧩 The Three Core Concepts

This framework is built on three main ideas - think of them as the **brain**, **planner**, and **hands** of the agent:

### 1. 👁️ Perception (The Eyes & Ears)

**What it does**: Understands and interprets information

**In simple terms**: 
- When you ask "What's 5 + 3?", perception understands you want a math answer
- When a tool returns data, perception evaluates if it's useful

**Key questions perception answers**:
- What is the user asking for?
- What type of answer do they need? (number, list, explanation?)
- Did the last step help us get closer to the answer?
- Are we done yet?

### 2. 🧠 Decision (The Brain & Planner)

**What it does**: Creates plans and decides what to do next

**In simple terms**:
- Breaks down "Calculate 5+3, then multiply by 2" into steps
- Decides which tool to use (calculator? document search?)
- Adjusts the plan if something goes wrong

**Key questions decision answers**:
- What steps do we need to solve this?
- Which tool should we use?
- What should we do if a step fails?

### 3. ✋ Action (The Hands)

**What it does**: Actually executes the plan by running code and calling tools

**In simple terms**:
- Takes the plan and actually does it
- Calls the calculator with "5 + 3"
- Returns the result "8"

**Key questions action answers**:
- How do I call this tool correctly?
- What result did the tool give me?
- Did the tool succeed or fail?

---

## 🏗️ Architecture Overview

Here's how the system is organized:

```
┌─────────────────────────────────────────────────────────────┐
│                        USER                                  │
│                   "What is 5 + 3?"                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    MAIN.PY                                   │
│              (Entry Point - Interactive Shell)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    AGENT LOOP                                │
│            (Orchestrates the whole process)                  │
│                                                              │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐          │
│   │ PERCEPTION│ ──▶│  DECISION │ ──▶│   ACTION  │          │
│   │  (Understand)  │  (Plan)   │    │  (Execute)│          │
│   └───────────┘    └───────────┘    └───────────┘          │
│         │                                  │                 │
│         └──────────── LOOP ◀──────────────┘                 │
│                  (Until goal achieved)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│    MEMORY   │  │   HEURISTICS │  │ MCP SERVERS │
│ (Past chats)│  │  (Safety)    │  │  (Tools)    │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## 🔍 Component Deep Dive

### 📁 Folder Structure Explained

```
multiagent-perception-coordination-decision/
│
├── main.py                    # 🚀 Start here! Interactive chat interface
│
├── agent/                     # 🤖 The Agent's Brain
│   ├── agent_loop.py          # Main orchestration loop
│   ├── agentSession.py        # Tracks conversation state
│   └── context.py             # Stores agent configuration
│
├── perception/                # 👁️ Understanding Module
│   └── perception.py          # Interprets user queries & results
│
├── decision/                  # 🧠 Planning Module
│   └── decision.py            # Creates & adjusts plans
│
├── action/                    # ✋ Execution Module
│   └── executor.py            # Runs code & calls tools safely
│
├── memory/                    # 💾 Memory System
│   ├── memory_search.py       # Searches past conversations
│   └── session_log.py         # Saves current conversation
│
├── heuristics/                # 🛡️ Safety Rules
│   └── heuristics.py          # Validates & sanitizes inputs
│
├── mcp_servers/               # 🔧 External Tools
│   ├── mcp_server_1.py        # Math tools (add, multiply, etc.)
│   ├── mcp_server_2.py        # Document tools (search PDFs, etc.)
│   ├── mcp_server_3.py        # Web tools (search internet)
│   └── multiMCP.py            # Connects to all servers
│
├── prompts/                   # 📝 LLM Instructions
│   ├── perception_prompt.txt  # How to understand queries
│   └── decision_prompt.txt    # How to create plans
│
└── config/                    # ⚙️ Settings
    ├── mcp_server_config.yaml # Which tools are available
    └── models.json            # Which AI model to use
```

---

### 🤖 The Agent Loop (agent/agent_loop.py)

This is the **heart** of the system - it coordinates everything:

```
User Query: "Calculate factorial of 5"
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                    AGENT LOOP                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Step 0: 📚 MEMORY SEARCH                               │
│  ──────────────────────                                  │
│  "Have I solved similar problems before?"                │
│  → If yes, use that knowledge to help                    │
│                                                          │
│  Step 1: 👁️ PERCEPTION                                  │
│  ──────────────────────                                  │
│  "What is the user asking for?"                          │
│  → Entities: ["factorial", "5"]                          │
│  → Result type: "number"                                 │
│  → Can I answer directly? No, need to calculate          │
│                                                          │
│  Step 2: 🧠 DECISION                                     │
│  ──────────────────────                                  │
│  "How should I solve this?"                              │
│  → Plan: "Step 0: Call factorial(5), return result"      │
│  → Code: result = factorial(5); return result            │
│                                                          │
│  Step 3: ✋ ACTION (Execute)                             │
│  ──────────────────────                                  │
│  → Run: factorial(5)                                     │
│  → Result: 120                                           │
│                                                          │
│  Step 4: 👁️ PERCEPTION (Evaluate Result)                │
│  ──────────────────────                                  │
│  "Did we achieve the goal?"                              │
│  → Yes! 120 is the factorial of 5                        │
│  → Mark: original_goal_achieved = true                   │
│                                                          │
│  Step 5: 💾 SAVE & RETURN                               │
│  ──────────────────────                                  │
│  → Save to memory for future reference                   │
│  → Return: "Factorial of 5 is 120"                       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

### 👁️ Perception Module (perception/perception.py)

The perception module uses an LLM (like Gemini) to understand:

**Input** (User Query):
```json
{
  "snapshot_type": "user_query",
  "raw_input": "What is the factorial of 5?"
}
```

**Output** (Structured Understanding):
```json
{
  "entities": ["factorial", "5"],
  "result_requirement": "A numerical value representing 5!",
  "original_goal_achieved": false,
  "reasoning": "Need to calculate factorial using a tool",
  "local_goal_achieved": true,
  "local_reasoning": "Successfully understood the query",
  "solution_summary": "Not ready yet",
  "confidence": "0.8"
}
```

**Two Modes**:

1. **User Query Mode**: "What does the user want?"
2. **Step Result Mode**: "Did the tool output help us?"

---

### 🧠 Decision Module (decision/decision.py)

The decision module creates execution plans:

**Input**:
```json
{
  "plan_mode": "initial",
  "planning_strategy": "exploratory",
  "original_query": "What is factorial of 5?",
  "perception": { ... }
}
```

**Output**:
```json
{
  "plan_text": [
    "Step 0: Calculate factorial of 5 using factorial tool",
    "Step 1: Return the result as final answer"
  ],
  "step_index": 0,
  "description": "Calculate factorial of 5",
  "type": "CODE",
  "code": "result = factorial(5)\nreturn result"
}
```

**Planning Strategies**:

| Strategy | Description | Best For |
|----------|-------------|----------|
| Conservative | One step at a time, wait for results | Accuracy-focused tasks |
| Exploratory | Multiple parallel approaches | Information gathering |

---

### ✋ Action/Executor (action/executor.py)

The executor safely runs the code generated by the decision module:

**Key Features**:
- ✅ **Sandboxed execution** - Can't harm your computer
- ✅ **Limited allowed imports** - Only safe Python modules
- ✅ **Timeout protection** - Stops infinite loops
- ✅ **Function call limit** - Max 5 tool calls per step

**How it works**:
```
Code: "result = factorial(5)\nreturn result"
         │
         ▼
┌─────────────────────────────────────┐
│         EXECUTOR                     │
├─────────────────────────────────────┤
│ 1. Parse code as AST                │
│ 2. Validate (no dangerous imports)  │
│ 3. Inject tool proxies              │
│ 4. Wrap in async function           │
│ 5. Execute with timeout             │
│ 6. Return result or error           │
└─────────────────────────────────────┘
         │
         ▼
Result: {"status": "success", "result": "120"}
```

---

## 🔧 The Tools (MCP Servers)

**MCP** = Model Context Protocol - a standard way for AI agents to use external tools.

### Available Tool Servers:

#### 1. Math Server (mcp_server_1.py)
```
Tools: add, subtract, multiply, divide, factorial, power, 
       sin, cos, tan, fibonacci_numbers, strings_to_chars_to_int,
       int_list_to_exponential_sum
```

**Example**:
```python
factorial(5)        # Returns: 120
add(10, 20)         # Returns: 30
fibonacci_numbers(5) # Returns: [0, 1, 1, 2, 3]
```

#### 2. Document Server (mcp_server_2.py)
```
Tools: search_stored_documents_rag, convert_webpage_url_into_markdown,
       extract_pdf
```

**Example**:
```python
search_stored_documents_rag("Tesla patents")
# Returns: Relevant document chunks about Tesla
```

#### 3. Web Search Server (mcp_server_3.py)
```
Tools: duckduckgo_search_results, download_raw_html_from_url
```

**Example**:
```python
duckduckgo_search_results("Python programming")
# Returns: Search results from the web
```

### How Tools Connect (multiMCP.py)

```
┌───────────────────────────────────────────────────────┐
│                    MultiMCP                            │
│           (Central Tool Coordinator)                   │
├───────────────────────────────────────────────────────┤
│                                                        │
│   "I want to call factorial(5)"                        │
│                │                                       │
│                ▼                                       │
│   ┌────────────────────────────────┐                  │
│   │  tool_map:                      │                  │
│   │  {                              │                  │
│   │    "factorial": mcp_server_1,   │                  │
│   │    "add": mcp_server_1,         │                  │
│   │    "search_rag": mcp_server_2,  │                  │
│   │    ...                          │                  │
│   │  }                              │                  │
│   └────────────────────────────────┘                  │
│                │                                       │
│                ▼                                       │
│   Route to correct server → Execute → Return result    │
│                                                        │
└───────────────────────────────────────────────────────┘
```

---

## 💾 Memory System

The agent remembers past conversations to provide better help!

### How Memory Works:

```
User: "What is factorial of 5?"
Agent: "120"

       ↓ (Saved to memory)

File: memory/session_logs/2025/05/08/abc123.json
{
  "session_id": "abc123",
  "original_query": "What is factorial of 5?",
  "solution_summary": "Factorial of 5 is 120",
  "original_goal_achieved": true
}

       ↓ (Later, new conversation)

User: "Calculate factorial of 7"
Agent: 
  1. Searches memory for "factorial"
  2. Finds: "Factorial of 5 is 120" was solved using factorial()
  3. Uses same approach: factorial(7) = 5040
```

### Memory Search (memory_search.py)

Uses **fuzzy matching** to find relevant past conversations:

```python
# User asks: "What's 5 factorial?"
# Memory has: "What is factorial of 5?"

# Fuzzy match score: 85% similar
# → "This past conversation might help!"
```

---

## 🛡️ Heuristics - Safety First

The heuristics module protects the system from harmful inputs:

### Rules Applied:

| Rule | What It Checks | Example Blocked |
|------|----------------|-----------------|
| URL Validation | Are URLs real and safe? | `http://malware.com` |
| File Path Check | Do files exist? | `/etc/passwd` |
| Sentence Length | Is input too long? | Spam attacks |
| Blacklist Words | Contains harmful terms? | "hack", "password", "exploit" |
| URL Protocol | Has https://? | Auto-adds if missing |

### Example:

```python
query = "hack into the system password"

# Heuristics processing:
# ❌ Found blacklisted words: "hack", "password"
# → Query blocked or sanitized to: "XXXX into the system XXXXXXXX"
```

---

## 🎬 Step-by-Step Example

Let's trace through a complete query:

### Query: "What are the main topics in the Tesla document?"

```
┌──────────────────────────────────────────────────────────────┐
│ STEP 0: USER INPUT                                           │
├──────────────────────────────────────────────────────────────┤
│ User: "What are the main topics in the Tesla document?"      │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ STEP 1: MEMORY SEARCH                                        │
├──────────────────────────────────────────────────────────────┤
│ 🔍 Searching past conversations for "Tesla document"...      │
│ ✅ Found: Previous query about "Tesla patents" - 78% match   │
│ → This might help: Use document search tool                  │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ STEP 2: PERCEPTION (Initial)                                 │
├──────────────────────────────────────────────────────────────┤
│ 📊 Analysis:                                                 │
│   entities: ["Tesla", "document", "topics"]                  │
│   result_requirement: "List of main topics from document"    │
│   original_goal_achieved: false (need to search first)       │
│   confidence: 0.7                                            │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ STEP 3: DECISION (Planning)                                  │
├──────────────────────────────────────────────────────────────┤
│ 📋 Plan:                                                     │
│   Step 0: Search stored documents for Tesla content          │
│   Step 1: Analyze chunks to extract main topics              │
│   Step 2: Summarize and conclude                             │
│                                                              │
│ 💻 Code for Step 0:                                          │
│   result = search_stored_documents_rag("Tesla main topics")  │
│   return result                                              │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ STEP 4: ACTION (Execution)                                   │
├──────────────────────────────────────────────────────────────┤
│ ⚡ Executing: search_stored_documents_rag("Tesla main topics")│
│                                                              │
│ 📄 Result:                                                   │
│   "Tesla Motors has open-sourced their electric vehicle      │
│    patents... The company focuses on sustainable transport,  │
│    battery technology, and autonomous driving..."            │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ STEP 5: PERCEPTION (Evaluate Result)                         │
├──────────────────────────────────────────────────────────────┤
│ 📊 Analysis of result:                                       │
│   local_goal_achieved: true (got document content)           │
│   original_goal_achieved: false (need to summarize)          │
│   reasoning: "Have content, need to extract topics"          │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ STEP 6: DECISION (Next Step)                                 │
├──────────────────────────────────────────────────────────────┤
│ 📋 Updated Plan - Move to Step 1:                            │
│                                                              │
│ 💻 Code for Step 1:                                          │
│   result = """                                               │
│   Main topics in Tesla document:                             │
│   1. Open-source patents                                     │
│   2. Sustainable transport                                   │
│   3. Battery technology                                      │
│   4. Autonomous driving                                      │
│   """                                                        │
│   return result                                              │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ STEP 7: PERCEPTION (Final Check)                             │
├──────────────────────────────────────────────────────────────┤
│ ✅ original_goal_achieved: true                              │
│ ✅ solution_summary: "Main topics: open-source patents,      │
│    sustainable transport, battery tech, autonomous driving"  │
│ ✅ confidence: 0.95                                          │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ STEP 8: SAVE & RESPOND                                       │
├──────────────────────────────────────────────────────────────┤
│ 💾 Saved to: memory/session_logs/2025/11/22/xyz789.json     │
│                                                              │
│ 🎉 Response to User:                                         │
│ "The main topics in the Tesla document are:                  │
│  1. Open-source patents                                      │
│  2. Sustainable transport                                    │
│  3. Battery technology                                       │
│  4. Autonomous driving"                                      │
└──────────────────────────────────────────────────────────────┘
```

---

## 📄 Key Files Explained

### 1. main.py - The Entry Point

```python
# What it does:
# 1. Loads MCP server configurations
# 2. Initializes the MultiMCP (tool connector)
# 3. Creates the AgentLoop
# 4. Runs an interactive chat loop

# Key code:
multi_mcp = MultiMCP(server_configs=configs)  # Connect to tools
await multi_mcp.initialize()                   # Discover all tools
loop = AgentLoop(...)                          # Create the agent
response = await loop.run(query)               # Process user query
```

### 2. agent/agentSession.py - Conversation Tracker

```python
# Tracks the entire conversation:
class AgentSession:
    session_id: str            # Unique ID for this chat
    original_query: str        # What the user asked
    perception: PerceptionSnapshot  # Understanding of query
    plan_versions: list        # All plans created
    state: dict               # Current status (goal achieved?)

# Example state:
{
  "original_goal_achieved": True,
  "final_answer": "Factorial of 5 is 120",
  "confidence": 0.95,
  "solution_summary": "Successfully calculated factorial"
}
```

### 3. prompts/perception_prompt.txt - How to Understand

This file teaches the LLM how to analyze queries. Key instructions:

```
"You are the perception module..."
- Extract important entities
- Determine what type of answer is needed
- Check if the goal is already achieved
- Provide reasoning for your conclusions
```

### 4. prompts/decision_prompt.txt - How to Plan

This file teaches the LLM how to create plans:

```
"You are the decision-making module..."
- Create 1-3 step plans
- Use available tools only
- Chain operations aggressively
- Handle errors gracefully
```

---

## 🚀 Running the System

### Prerequisites

1. **Python 3.10+** installed
2. **Gemini API Key** (or Ollama for local models)
3. **Dependencies** installed:
   ```bash
   pip install google-generativeai mcp pydantic pyyaml rapidfuzz
   ```

### Step-by-Step:

```bash
# 1. Navigate to the project
cd multiagent-perception-coordination-decision

# 2. Set your API key
export GEMINI_API_KEY="your-key-here"

# 3. Run the agent
python main.py
```

### Example Session:

```
──────────────────────────────────────────────────────
🔸  Agentic Query Assistant  🔸
Type your question and press Enter.
Type 'exit' or 'quit' to leave.
──────────────────────────────────────────────────────

🟢  You: What is 5 + 3?

Searching Recent Conversation History
🔍 Found 12 JSON file(s)...

[Perception 0] Initial ERORLL:
  {'entities': ['5', '3'], 'result_requirement': 'sum of numbers'...}

[Decision Plan Text: V1]:
  Step 0: Calculate 5 + 3 using add function
  Step 1: Return the result

[Step 0] Calculate 5 + 3
[EXECUTING CODE]
result = add(5, 3)
return result

[Perception of Step 0 Result]:
  {'original_goal_achieved': True, 'solution_summary': '8'}

🔵 Agent: The sum of 5 + 3 is 8.
```

---

## 📖 Glossary

| Term | Definition |
|------|------------|
| **Agent** | An AI system that can perceive, plan, act, and learn |
| **MCP** | Model Context Protocol - standard for AI-tool communication |
| **Perception** | The understanding/interpretation phase |
| **Decision** | The planning phase |
| **Action** | The execution phase |
| **Session** | One complete conversation with the agent |
| **Tool** | External capability (calculator, search, etc.) |
| **ERORLL** | Entity-Requirement-Outcome-Reasoning-Local-Logic format |
| **Heuristics** | Safety rules that validate inputs |
| **Memory** | Past conversations stored for learning |
| **Sandbox** | Safe execution environment for code |
| **LLM** | Large Language Model (like Gemini, GPT) |
| **Prompt** | Instructions given to the LLM |

---

## 🎓 Key Takeaways for Beginners

1. **Agents are smart loops**: They keep perceiving → deciding → acting until done
2. **Tools extend AI capabilities**: Agents can now calculate, search, and more
3. **Memory enables learning**: Past conversations help future performance
4. **Safety is built-in**: Heuristics protect against harmful inputs
5. **Plans can adapt**: If something fails, the agent replans
6. **Prompts are crucial**: Good instructions = good results

---

## 🔗 Next Steps

1. **Run the agent** and try some queries
2. **Read the prompts** to understand how the LLM is instructed
3. **Explore memory** to see how conversations are stored
4. **Add a new tool** to extend capabilities
5. **Modify heuristics** to add custom safety rules

---

**Happy Learning! 🚀**

*This framework demonstrates the core concepts of agentic AI - understanding, planning, executing, and learning. As you explore, you'll see how these simple ideas combine to create powerful, intelligent systems.*

