# 🎯 Quick Reference Card

## 📊 **Decision Prompt Details**

### GitHub Link
```
https://github.com/[YOUR-USERNAME]/hybrid-decision-making/blob/main/prompts/decision_prompt_new.txt
```

### Word Count
**211 words** ✅ (Target: <300 words)

---

## 🚀 **Execute 3 New Queries**

### Option 1: Automated (Recommended for Video)
```bash
cd /Users/soham.niyogi/Soham/codebase/eagv2/hybrid-decision-making
python test_new_queries.py
```

### Option 2: Manual (Interactive)
```bash
cd /Users/soham.niyogi/Soham/codebase/eagv2/hybrid-decision-making
python agent.py
```

Then enter each query:
1. `What is the log value of the amount that Anmol singh paid for his DLF apartment via Capbridge?`
2. `Compare the climate change policies mentioned in the Tesla IP document with current Indian environmental regulations`
3. `Find the current population of New Delhi, calculate the square root, then multiply by the number of Cricket World Cups India has won`

---

## ⚙️ **Current Configuration**

- **Model**: Gemini (API Key configured)
- **API Key**: `AIzaSyBomWfEWE4Usj9FVbWQs5NvNV2dMjuIiDs`
- **Fallback**: Ollama (phi4, gemma3:12b, qwen2.5)
- **MCP Servers**: math, documents, websearch
- **Paths**: Updated to current directory

---

## 📝 **3 New Queries**

### Query 1: Log Calculation
**Query**: "What is the log value of the amount that Anmol singh paid for his DLF apartment via Capbridge?"  
**Expected Result**: `17.0144`  
**Tools**: search_stored_documents → math.log()

### Query 2: Policy Comparison
**Query**: "Compare the climate change policies mentioned in the Tesla IP document with current Indian environmental regulations"  
**Expected Result**: Detailed comparison text  
**Tools**: search_stored_documents (2x) → synthesis

### Query 3: Multi-Step Math
**Query**: "Find the current population of New Delhi, calculate the square root, then multiply by the number of Cricket World Cups India has won"  
**Expected Result**: `11471.52`  
**Tools**: duckduckgo_search → search_stored_documents → math.sqrt()

---

## 📦 **All Deliverables**

| # | Deliverable | File | Status |
|---|-------------|------|--------|
| 1 | Architecture | `ARCHITECTURE.md` | ✅ |
| 2 | Bug Fix | `BUG_FIX_REPORT.md` | ✅ |
| 3 | README + 3 Examples | `README.md` | ✅ |
| 4 | Heuristics | `modules/heuristics.py` | ✅ |
| 5 | Historical Store | `historical_conversations.json` | ✅ |
| 6 | New Prompt (211 words) | `prompts/decision_prompt_new.txt` | ✅ |
| 7 | Execution Guide | `EXECUTION_GUIDE.md` | ✅ |
| 8 | Test Script | `test_new_queries.py` | ✅ |

---

## 🎬 **For YouTube Video**

### Terminal Commands to Run
```bash
# Navigate to directory
cd /Users/soham.niyogi/Soham/codebase/eagv2/hybrid-decision-making

# Show word count
cat prompts/decision_prompt_new.txt | wc -w

# Run all 3 queries
python test_new_queries.py

# Show memory files
ls -R memory/
```

### What to Show
1. Architecture diagram (`ARCHITECTURE.md`)
2. Word count verification (211 words)
3. Run test script (all 3 queries)
4. Show execution logs
5. Show final answers
6. Browse memory folder
7. Show GitHub repo structure

---

## 🔧 **Switch to Ollama**

If Gemini doesn't work:

1. Edit `config/profiles.yaml`:
   ```yaml
   llm:
     text_generation: phi4  # Change from 'gemini'
   ```

2. Start Ollama:
   ```bash
   ollama serve
   ```

3. Run queries (same commands as above)

---

## ✅ **Ready to Submit**

All files are in:
```
/Users/soham.niyogi/Soham/codebase/eagv2/hybrid-decision-making/
```

**Next Steps**:
1. Run `python test_new_queries.py` to execute all 3 queries
2. Record the execution for YouTube
3. Push to GitHub
4. Update GitHub links with your username
5. Submit!

