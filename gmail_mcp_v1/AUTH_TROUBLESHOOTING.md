# Gmail MCP Authentication Troubleshooting Guide

## Essential Files for Authentication Issues

### 🔧 **oauth_openid_fix.py** (MAIN SOLUTION)
- **Purpose**: The working OAuth solution that includes `openid` scope
- **Use when**: Getting scope mismatch errors or need fresh authentication
- **Fixed**: "Scope has changed" errors by including `openid` scope explicitly

### 🔧 **fix_credentials.py**
- **Purpose**: Fixes redirect_uri issues in credentials.json
- **Use when**: Getting "Missing required parameter: redirect_uri" errors
- **Adds**: Proper redirect URIs to credentials.json

### 🔧 **refresh_token.py**
- **Purpose**: Refreshes expired OAuth tokens
- **Use when**: Getting 401 authentication errors after token expires
- **Maintains**: Existing authentication without full re-auth

### 📧 **test_gmail_direct.py**
- **Purpose**: Test Gmail functionality without LLM (bypasses quota issues)
- **Use when**: Want to verify Gmail works independently of Gemini API

## Common Authentication Problems & Solutions

### Problem 1: "Missing required parameter: redirect_uri"
**Solution**: Run `python fix_credentials.py` then `python oauth_openid_fix.py`

### Problem 2: "Scope has changed" errors
**Solution**: 
1. Go to https://myaccount.google.com/permissions
2. Remove Gmail MCP app permissions
3. Run `python oauth_openid_fix.py`

### Problem 3: "401 Invalid Credentials" 
**Solution**: Run `python refresh_token.py` or `python oauth_openid_fix.py`

### Problem 4: Gemini API quota exhausted
**Solution**: Run `python test_gmail_direct.py` to test Gmail without LLM

## File Structure
```
gmail_mcp_v1/
├── oauth_openid_fix.py      # ✅ WORKING AUTH SOLUTION
├── fix_credentials.py       # ✅ Fix redirect_uri issues
├── refresh_token.py         # ✅ Refresh expired tokens
├── test_gmail_direct.py     # ✅ Test Gmail without LLM
├── multi_step_research_gmail.py  # ✅ Main application
├── credentials.json         # ✅ OAuth client config (keep safe)
├── token.json              # ✅ Active auth token (auto-generated)
└── .env                    # ✅ API keys (keep safe)
```

## Quick Recovery Commands
```bash
# Full re-authentication (most common fix)
python oauth_openid_fix.py

# Fix credentials file issues
python fix_credentials.py

# Test Gmail works without LLM
python test_gmail_direct.py

# Main application
python multi_step_research_gmail.py
```
