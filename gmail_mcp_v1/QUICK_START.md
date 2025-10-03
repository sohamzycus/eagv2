# 🚀 Gmail MCP v1 - Quick Start Guide

## What This Does
AI-powered Gmail automation using **Google Gemini 2.0 Flash**:
- 📧 Send emails automatically
- 📝 Compose drafts
- 📋 List recent emails  
- 🎯 Natural language email commands

## ⚡ Quick Start (3 Simple Steps)

### Step 1: Install & Run
```bash
cd gmail_mcp_v1
python setup_and_run.py
```

### Step 2: Gmail Setup (First Time Only)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Gmail API
3. Create OAuth 2.0 credentials
4. Download as `credentials.json`

### Step 3: Try Commands
```
"Send email to test@example.com with subject 'Hello' and message 'Test from AI'"
"List my recent emails"
"Compose draft to colleague@company.com about meeting"
```

## 🔧 What's Pre-Configured
- ✅ **Gemini API Key**: Built-in for demo
- ✅ **Auto-install dependencies**: Google APIs, Flask, etc.
- ✅ **Gmail API integration**: OAuth 2.0 authentication
- ✅ **Full logging**: Request/response tracking

## 📋 Example Tasks

### Send Emails
- "Email john@company.com about the quarterly report"
- "Send a thank you email to client@business.com"

### Check Emails
- "Show me my last 5 emails"
- "List recent messages"

### Create Drafts
- "Draft an email to team@company.com about the project update"

## 📊 Output Files
- `gmail_session.json` - Complete execution log
- `gmail_agent.log` - System logs
- `token.json` - OAuth tokens (auto-generated)

## 🔍 Troubleshooting

**Missing credentials.json:**
- Download from Google Cloud Console
- Or set environment variables:
  ```bash
  export GOOGLE_CLIENT_ID="your_id"
  export GOOGLE_CLIENT_SECRET="your_secret"
  ```

**Permission errors:**
- Delete `token.json` and re-authenticate
- Ensure Gmail API is enabled

## 🎉 Ready to Go!
Run `python setup_and_run.py` and let AI handle your emails! 📧✨
