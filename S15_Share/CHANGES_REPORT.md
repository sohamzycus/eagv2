# S15_Share Code Changes Report

## Summary of Changes Made

This document summarizes all code changes made to enable the S15_Share agentic system to:
1. Use Ollama local models (phi4) instead of Gemini
2. Generate detailed project plans for complex tasks
3. Support 4 test tasks (Gmail signup, web search, document processing, planning)

---

## 1. Configuration Changes

### `config/profiles.yaml`
**Change:** Updated LLM configuration to use Ollama phi4 model

```yaml
# Before
llm:
  text_generation: gemini

# After  
llm:
  text_generation: phi4  # Using Ollama local model
```

### `config/mcp_server_config.yaml`
**Change:** Updated MCP server paths for macOS

```yaml
# Before (Windows paths)
cwd: I:\TSAI\2025\EAG 2\Course Content\Code\Session 14\S15_Manual-1\S15_Manual\mcp_servers

# After (macOS paths)
cwd: /Users/soham.niyogi/Soham/codebase/eagv2/S15_Share/mcp_servers
```

---

## 2. Prompt Changes

### `prompts/perception_prompt.txt`
**Changes:**
1. Added planning request detection in routing logic
2. Added detailed instructions for planning requests
3. Added example for planning/project breakdown requests

**Key Addition - Planning Detection:**
```
### Route to `"summarize"` when:
...
- **PLANNING REQUESTS**: User asks for a plan, project breakdown, task list, or roadmap
  - Keywords: "create a plan", "plan for", "break down", "organize", "project plan", "task list", "roadmap", "steps to", "how to approach"
  - For planning requests, route IMMEDIATELY to summarize with detailed planning instructions
```

**Key Addition - Planning Instructions:**
```
### **🎯 PLANNING REQUEST INSTRUCTIONS**
When the user asks for a plan, project breakdown, or task organization, use this format:

"Create a COMPREHENSIVE PROJECT PLAN for: [user's request]. 

Structure the plan with:
1. **Phases** - Major stages (Research, Design, Development, Testing, Delivery)
2. **Tasks** - Specific work items with checkboxes [ ]
3. **Subtasks** - Granular steps where needed
..."
```

### `prompts/summarizer_prompt.txt`
**Change:** Added Example 5 for Project Planning Requests with detailed physics animation project plan example

### `prompts/planning_prompt.txt` (NEW FILE)
**Created:** Comprehensive planning prompt template for generating detailed task breakdowns

---

## 3. MCP Server Changes

### `mcp_servers/mcp_server_3.py`
**Change:** Added Ollama fallback for summarization when GEMINI_API_KEY is not available

```python
# Added Ollama fallback function
async def ollama_summarize(text: str, prompt: str) -> str:
    """Use Ollama for summarization when Gemini is not available"""
    ...

# Modified get_client() to handle missing API key gracefully
def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            _client = genai.Client(api_key=api_key)
        else:
            _client = None  # Will use Ollama fallback
    return _client
```

---

## 4. Test Files Created

### `test_planning_prompt.py`
Test script to verify planning prompt generates detailed task breakdowns using Ollama phi4

---

## 5. Environment Setup

### Python Version
- Changed from Python 3.14 to Python 3.12 (required for onnxruntime compatibility)

### Commands to Set Up:
```bash
cd /Users/soham.niyogi/Soham/codebase/eagv2/S15_Share
rm -rf .venv
uv venv --python python3.12
uv sync
playwright install chromium
```

---

## 6. Test Results

### All 4 Tasks Routing Test:
```
✅ Task 1 (Gmail Signup) → browserAgent (PASS)
   Entities: ['Gmail', 'John Doe', 'Sign up', 'johndoe2024test']
   Confidence: 0.90

✅ Task 2 (Web Search) → decision (PASS)
   Entities: ['Tesla', 'stock news', 'summary']
   Confidence: 0.85

✅ Task 3 (Document Processing) → decision (PASS)
   Entities: ['DLF', 'company financials']
   Confidence: 0.50

✅ Task 4 (Planning Request) → summarize (PASS)
   Entities: ['middle school physics teacher', 'conservation of momentum', 'demonstration animations', 'HTML presentation']
   Confidence: 0.95
```

### Planning Prompt Test with phi4:
```
✅ Generated plan with:
   - 36-55 tasks/subtasks
   - 6-7 phases
   - 3000+ characters

Phases generated:
- Research Phase
- Design Phase
- Development Phase
- Presentation Structure
- Testing and Finalization
- Delivery
```

---

## 7. Four Test Tasks

### Task 1: Gmail Signup (Browser Automation)
- **Type:** browserAgent
- **Description:** Sign up for Gmail with specific user details
- **Tools Used:** Browser automation tools (click, fill, navigate)

### Task 2: Web Search (Decision)
- **Type:** decision
- **Description:** Search for Tesla stock news and summarize
- **Tools Used:** web_search_urls, webpage_url_to_raw_text, webpage_url_to_llm_summary

### Task 3: Document Processing (Decision)
- **Type:** decision
- **Description:** Convert PDF to text and extract financial figures
- **Tools Used:** convert_pdf_to_markdown, search_stored_documents_rag

### Task 4: Planning Request (Summarize)
- **Type:** summarize (direct)
- **Description:** Create detailed project plan for physics animations
- **Tools Used:** None (LLM generates plan directly)

---

## 8. Final Planning Prompt

The enhanced planning prompt ensures detailed task breakdowns by:

1. **Detecting planning keywords** in the perception module
2. **Routing directly to summarizer** with detailed instructions
3. **Using structured format** with phases, tasks, and subtasks
4. **Including all necessary steps** - research, design, development, testing, delivery

### Example Output for Physics Animation Project:

```markdown
# Conservation of Momentum Animations Project

## Research Phase
- [ ] Research basic conservation of momentum concepts
- [ ] Identify key principles to demonstrate
- [ ] Find appropriate examples for middle school level
- [ ] Gather reference materials and equations

## Design Phase
- [ ] Design animation 1: Basic collision demonstration
- [ ] Design animation 2: Elastic collisions
- [ ] Design animation 3: Inelastic collisions
- [ ] Design animation 4: Explosions (conservation in reverse)
- [ ] Design animation 5: Real-world applications

## Development Phase
- [ ] Set up JavaScript animation framework
- [ ] Create animation 1: Basic collision demonstration
- [ ] Create animation 2: Elastic collisions
- [ ] Create animation 3: Inelastic collisions
- [ ] Create animation 4: Explosions
- [ ] Create animation 5: Real-world applications
- [ ] Add interactive elements (speed controls, reset buttons)

## Presentation Structure
- [ ] Create HTML structure for presentation
- [ ] Design simple, clean CSS for presentation
- [ ] Add navigation between animations
- [ ] Add explanatory text for each animation
- [ ] Add formulas and equations where appropriate

## Testing and Finalization
- [ ] Test all animations for accuracy
- [ ] Test presentation in browser
- [ ] Optimize for classroom display
- [ ] Prepare final package for delivery

## Delivery
- [ ] Deploy presentation
- [ ] Provide final URL to user
- [ ] Document any usage instructions
```

---

## 9. Video Recording Instructions

To record the 4 flows:

1. **Run the demo script**:
   ```bash
   cd /Users/soham.niyogi/Soham/codebase/eagv2/S15_Share
   ./run_demo_video.sh
   ```

2. **Or run individual tasks**:
   ```bash
   source .venv/bin/activate
   python demo_4_tasks.py 1  # Gmail Signup
   python demo_4_tasks.py 2  # Web Search
   python demo_4_tasks.py 3  # Document Processing
   python demo_4_tasks.py 4  # Planning Request
   ```

3. **For full agent interaction** (requires browser server):
   ```bash
   # Terminal 1: Start browser server on port 8100 (if needed)
   # Terminal 2: Run agent
   uv run main.py
   ```

4. **Test prompts**:
   - Task 1: "Sign me up on Gmail with name John Doe"
   - Task 2: "Search for Tesla stock news and summarize"
   - Task 3: "Search stored documents for DLF financials"
   - Task 4: "Create a detailed plan for physics momentum animations for middle school"

---

## 10. Final Planning Prompt (for reference)

The enhanced planning prompt in `prompts/planning_prompt.txt` includes:

1. **Clear structure requirements** - Phases, Tasks, Subtasks with checkboxes
2. **Phase categories** for different project types (Technical, Creative, Research)
3. **Detailed examples** showing expected output format
4. **Planning principles** - Be exhaustive, specific, organized, practical
5. **Critical rules** - Never skip phases, include dependencies, consider edge cases

This prompt ensures that when a user asks for a project plan, the system generates:
- 30-55+ tasks/subtasks
- 5-7 logical phases
- Specific, actionable items with checkboxes
- Proper dependency ordering
- Complete coverage from research to delivery

