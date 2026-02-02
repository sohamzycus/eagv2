# S20 Fixes Change Sheet for S15_NewArch

**Date:** January 31, 2026  
**Version:** S15_NewArch → S20 Compliant  
**Author:** Auto-generated via AI Assistant

---

## Executive Summary

This document details all critical fixes applied to S15_NewArch to make it production-ready. These fixes address bugs that caused crashes, infinite loops, empty outputs, and poor UX.

---

## Change Log

### 1. CRITICAL: Stringified List Bug Fix

| Attribute | Details |
|-----------|---------|
| **File** | `memory/context.py` (NEW FILE) |
| **Method Added** | `_ensure_parsed_value(value)` |
| **Bug Description** | LLMs return lists as strings like `"['url1', 'url2']"`. Iterating over this gives characters `[`, `'`, `u`, `r`, `l`... causing crashes or hallucinations. |
| **Solution** | Recursively parse strings using `ast.literal_eval` to convert to actual Python objects. |
| **Lines Added** | ~50 lines |

**Before (Bug):**
```python
for item in inputs['urls']:  # Iterates chars: "[", "'", "u", "r", "l"...
```

**After (Fix):**
```python
inputs['urls'] = self._ensure_parsed_value(inputs['urls'])
# Now iterates: ['url1', 'url2', 'url3']
```

---

### 2. CRITICAL: Blind Formatter Bug Fix

| Attribute | Details |
|-----------|---------|
| **File** | `core/loop.py` |
| **Method Modified** | `_execute_step()` → `build_agent_input()` |
| **Bug Description** | FormatterAgent couldn't access session variables (`research_summary`, `code_analysis`). Final reports had empty placeholders. |
| **Solution** | Explicitly inject `all_globals_schema` for FormatterAgent. |
| **Lines Changed** | ~15 lines |

**Code Added:**
```python
if agent_type == "FormatterAgent":
    all_globals = context.plan_graph.graph['globals_schema'].copy()
    return {
        ...
        "all_globals_schema": all_globals,  # ✅ Now included
        ...
    }
```

---

### 3. UX: Bootstrap Graph (Infinite Spinner Fix)

| Attribute | Details |
|-----------|---------|
| **File** | `core/loop.py` |
| **Method Added** | `_create_bootstrap_context()` |
| **Bug Description** | UI appeared frozen for 10-30 seconds during planning phase. Users thought app crashed. |
| **Solution** | Create a "Planning" node immediately so UI shows status instantly. |
| **Lines Added** | ~30 lines |

**New Method:**
```python
def _create_bootstrap_context(self, query: str, file_manifest: dict):
    bootstrap_graph = {
        "nodes": [{"id": "PLANNING", "agent": "PlannerAgent", ...}],
        "edges": [{"source": "ROOT", "target": "PLANNING"}]
    }
    context = ExecutionContextManager(bootstrap_graph, ...)
    context.mark_running("PLANNING")  # UI sees activity immediately
    return context
```

---

### 4. LOGIC: Infinite Loop Warning Fix

| Attribute | Details |
|-----------|---------|
| **File** | `core/loop.py` |
| **Method Modified** | `_execute_step()` |
| **Bug Description** | Agents browse "just one more link" forever, hit 15-turn limit with no output. |
| **Solution** | Inject warning at `turn >= max_turns - 2` forcing agent to stop and summarize. |
| **Lines Changed** | ~20 lines |

**Warning Injected:**
```
🛑 CRITICAL WARNING: You are on turn 14/15.
⚠️ STOP BROWSING. STOP SEARCHING.
✅ You MUST provide your FINAL OUTPUT now.
❌ Do NOT call any more tools.
```

---

### 5. MEMORY: Rich Clarification Context

| Attribute | Details |
|-----------|---------|
| **File** | `memory/context.py` |
| **Method Added** | `save_clarification(agent_question, user_response)` |
| **Bug Description** | Only "Yes" was saved. Next agent didn't know what "Yes" referred to. |
| **Solution** | Save full context: "Agent asked: Should I deploy? User said: Yes" |
| **Lines Added** | ~25 lines |

---

### 6. ROBUSTNESS: 3-Strategy Extraction

| Attribute | Details |
|-----------|---------|
| **File** | `memory/context.py` |
| **Method Added** | `extract_output_value(output, key)` |
| **Bug Description** | Pipeline broke when agent put answer in wrong JSON field. |
| **Solution** | Try 3 strategies: (1) Direct key, (2) Nested in `output`/`result`, (3) In `final_answer` |
| **Lines Added** | ~40 lines |

---

### 7. MCP: Config-Based Loading

| Attribute | Details |
|-----------|---------|
| **File** | `mcp_servers/multi_mcp.py` (REWRITTEN) |
| **Config File** | `config/mcp_config.json` (NEW) |
| **Changes** | Hardcoded dict → JSON config file |
| **Features Added** | Git URL support, file caching, increased timeout (20s), retry logic |
| **Lines Changed** | ~200 lines (full rewrite) |

**New Config Format:**
```json
{
  "servers": {
    "browser": {"command": "uv", "args": [...], "timeout": 20, "enabled": true},
    "rag": {"command": "uv", "args": [...], "timeout": 30, "enabled": true},
    "sandbox": {"command": "uv", "args": [...], "timeout": 60, "enabled": true}
  }
}
```

---

### 8. MCP: RAG Server Parallel Processing

| Attribute | Details |
|-----------|---------|
| **File** | `mcp_servers/server_rag.py` |
| **Changes** | Sequential → Parallel with ThreadPoolExecutor |
| **Features Added** | `pdf_lock` for thread safety, `MAX_WORKERS=2` |
| **Lines Changed** | ~100 lines |

**Key Additions:**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

pdf_lock = threading.Lock()
MAX_WORKERS = 2

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    future_to_file = {executor.submit(_process_single_file, ...): file}
```

---

### 9. MCP: Bulk Search Tool Restored

| Attribute | Details |
|-----------|---------|
| **File** | `mcp_servers/server_browser.py` |
| **Tool Added** | `search_web_with_text_content(query, num_results)` |
| **Bug Description** | Agents wasted 10+ turns clicking URLs one by one. |
| **Solution** | Single tool that searches AND extracts text from all results. |
| **Lines Added** | ~80 lines |

---

### 10. PROMPTS: Headless Environment Constraints

| Attribute | Details |
|-----------|---------|
| **Files** | `prompts/coder.md`, `prompts/planner.md` |
| **Changes** | Added headless server constraints |

**coder.md additions:**
```markdown
🛑 STRICT ENVIRONMENT CONSTRAINTS (S20 HEADLESS HARDENING)

❌ NEVER USE:
- plt.show() → Use plt.savefig('output.png')
- cv2.imshow() → Use cv2.imwrite('output.png', img)
- webbrowser.open() → FORBIDDEN
- tkinter, pygame, PyQt → FORBIDDEN
```

**planner.md additions:**
```markdown
🛑 S20 ENVIRONMENT AWARENESS

This system runs in a HEADLESS SERVER environment.
- NO DESKTOP BROWSER - Use BrowserAgent with MCP tools
- NO GUI DISPLAY - Save to files instead
```

---

### 11. Config Paths Updated

| File | Change |
|------|--------|
| `config/agent_config.yaml` | `16_NetworkX/` → `S15_NewArch/` |
| `app.py` | Updated comments and titles |
| `mcp_servers/server_sandbox.py` | Updated path comments |
| `test_path_fix.py` | Updated expected path |

---

## New Files Created

| File | Purpose |
|------|---------|
| `memory/__init__.py` | Module initialization |
| `memory/context.py` | ExecutionContextManager with all fixes |
| `config/mcp_config.json` | MCP server configuration |
| `core/graph_adapter.py` | Frontend visualization adapter |
| `core/explorer_utils.py` | File tree utilities |
| `test_s20_fixes.py` | Verification test suite |
| `CHANGELOG_S20_FIXES.md` | This document |

---

## Files Modified

| File | Lines Changed |
|------|---------------|
| `core/loop.py` | ~80 lines added/modified |
| `mcp_servers/multi_mcp.py` | ~200 lines (full rewrite) |
| `mcp_servers/server_rag.py` | ~100 lines modified |
| `mcp_servers/server_browser.py` | ~80 lines added |
| `prompts/coder.md` | ~30 lines added |
| `prompts/planner.md` | ~25 lines added |
| `config/agent_config.yaml` | 10 path updates |

---

## Verification

All fixes verified via `test_s20_fixes.py`:

```
============================================================
S20 FIXES VERIFICATION TEST
============================================================
✅ FIX #1: Stringified List Bug (_ensure_parsed_value)
✅ FIX #2: Formatter globals injection (all_globals_schema)
✅ FIX #3: Bootstrap Graph (immediate context)
✅ FIX #4: Final Turn Warning
✅ FIX #5: Rich Clarification Context
✅ FIX #6: 3-Strategy Extraction
✅ FIX #7: Config-based MCP loading
✅ FIX #8: ThreadPoolExecutor in RAG
✅ FIX #9: search_web_with_text_content tool
✅ FIX #10: Headless prompts
✅ FIX #11: Config paths (S15_NewArch)

RESULTS: 11 passed, 0 failed
🎉 ALL S20 FIXES VERIFIED SUCCESSFULLY!
```

---

## How to Run

```bash
cd S15_NewArch

# Install dependencies
pip install networkx faiss-cpu numpy pandas mcp rich gradio playwright trafilatura

# Install playwright browsers
playwright install chromium

# Run CLI mode
python app.py

# Run with Gradio UI
python app.py --ui
```

---

## Test Queries

1. **Web Search Query:**
   ```
   What's the latest revenue of Dhurandhar Movie
   ```

2. **RAG Query (Local Documents):**
   ```
   Search stored documents about cricket
   ```
