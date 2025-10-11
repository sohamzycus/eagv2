# Gmail MCP v1 - Clean File Structure

## 🎯 **MAIN APPLICATION**
- **`multi_step_research_gmail.py`** - Complete multi-step research workflow with Gmail
- **`setup_and_run.py`** - Alternative Flask server approach

## 🔧 **AUTHENTICATION (Essential for troubleshooting)**
- **`oauth_openid_fix.py`** - ✅ **WORKING AUTH SOLUTION** (fixes scope issues)
- **`fix_credentials.py`** - Fixes redirect_uri issues in credentials.json
- **`refresh_token.py`** - Refreshes expired OAuth tokens

## 🧪 **TESTING & UTILITIES**
- **`test_gmail_direct.py`** - Test Gmail without LLM (bypasses quota issues)
- **`agent.py`** - AI agent for Flask server approach
- **`mcp_server.py`** - Flask server for HTTP-based Gmail API
- **`prompt_manager.py`** - System prompts and LLM management
- **`utils.py`** - Logging and utility functions

## 📁 **CONFIGURATION FILES**
- **`credentials.json`** - Google OAuth client configuration (keep safe!)
- **`credentials_backup.json`** - Backup of credentials
- **`token.json`** - Active OAuth token (auto-generated)
- **`.env`** - API keys (keep safe!)
- **`requirements.txt`** - Python dependencies

## 🗑️ **REMOVED (Duplicates/Failed attempts)**
- ❌ `console_oauth.py` - Failed auth attempt
- ❌ `create_token.py` - Failed auth attempt  
- ❌ `create_token_console.py` - Failed auth attempt
- ❌ `final_oauth.py` - Failed auth attempt
- ❌ `fix_auth.py` - Failed auth attempt
- ❌ `fresh_auth.py` - Failed auth attempt
- ❌ `simple_auth_gmail.py` - Failed auth attempt
- ❌ `llm_gmail_direct.py` - Older version
- ❌ `simple_research_gmail.py` - Simplified version
- ❌ `research_gmail_mcp.py` - Earlier version
- ❌ `real_research_gmail.py` - Intermediate version

## 🚀 **QUICK START**
```bash
# Main application (after Gemini quota resets)
python multi_step_research_gmail.py

# Test Gmail without LLM
python test_gmail_direct.py

# Re-authenticate if needed
python oauth_openid_fix.py
```

## 📊 **File Count**: 10 Python files (down from 18)
**Status**: ✅ Clean, essential files only
