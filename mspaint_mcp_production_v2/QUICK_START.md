# 🎨 MSPaint MCP Production v2 - Quick Start Guide

## What This Does
This is an AI-powered system that uses **Google Gemini 2.0 Flash** to control MS Paint automatically. The AI agent can:
- 🖼️ Open MS Paint
- 📐 Draw rectangles and shapes  
- ✍️ Add text with custom positioning
- 🎯 Execute complex drawing tasks from natural language

## ⚡ Quick Start (3 ways to run)

### Option 1: Python Script (Recommended)
```bash
python setup_and_run.py
```

### Option 2: Windows Batch File
```bash
run_with_api_key.bat
```

### Option 3: PowerShell Script
```powershell
.\run_with_api_key.ps1
```

## 🔧 What's Configured
- ✅ **Google Gemini API Key**: `GEMINI_API_KEY`
- ✅ **Auto-install dependencies**: Flask, pywinauto, google-genai, etc.
- ✅ **Windows automation**: DPI-aware Paint control
- ✅ **Logging**: Full request/response logging

## 🎮 How It Works

1. **MCP Server** starts on `http://127.0.0.1:5000`
2. **AI Agent** connects to Gemini 2.0 Flash
3. **Agent** plans Paint operations using available tools:
   - `get_monitor_info()` - Get screen info
   - `open_paint()` - Launch MS Paint
   - `draw_rectangle()` - Draw shapes
   - `add_text_in_paint()` - Add text
4. **Automation** executes via pywinauto
5. **Results** saved to `llm_session.json`

## 📝 Example Tasks You Can Try

- "Draw a rectangle and write 'Hello AI!' inside it"
- "Create a welcome message box"
- "Draw a simple diagram with text labels"
- "Make a birthday card layout"

## 📊 Output Files

- `llm_session.json` - Complete execution log with LLM requests/responses
- `mcp_agent.log` - System operation logs
- MS Paint window - Visual results

## 🔍 Troubleshooting

**If Python packages fail to install:**
```bash
pip install -r requirements.txt
```

**If MS Paint doesn't open:**
- Ensure you're on Windows
- Try running as Administrator
- Check Windows Defender isn't blocking automation

**If API calls fail:**
- Check internet connection
- Verify API key is valid
- Check `mcp_agent.log` for detailed errors

## 🏗️ Architecture

```
User Input → AI Agent (Gemini) → MCP Server → Windows Automation → MS Paint
                ↓
         llm_session.json (logs all interactions)
```

## 🚀 Ready to Run!

Just execute any of the run scripts above and watch AI control MS Paint automatically! 🎨✨
