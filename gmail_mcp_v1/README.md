# 📧 Gmail MCP v1 - AI-Powered Email Assistant

## What This Does
This is an AI-powered system that uses **Google Gemini 2.0 Flash** to control Gmail automatically. The AI agent can:
- 📧 Send emails via Gmail API
- 📝 Compose email drafts  
- 📋 List recent emails
- 🔍 Check Gmail account status
- 🎯 Execute complex email tasks from natural language

## ⚡ Quick Start

### Prerequisites
1. **Python 3.7+** installed
2. **Gmail account** with API access
3. **Google Cloud Project** with Gmail API enabled

### Option 1: Simple Run (Recommended)
```bash
python setup_and_run.py
```

### Option 2: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
export GOOGLE_API_KEY="GEMINI_API_KEY"

# Run components separately
python mcp_server.py &
python agent.py --question "Send an email to test@example.com"
```

## 🔧 Gmail API Setup

### Step 1: Google Cloud Console Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Gmail API**
4. Create **OAuth 2.0 credentials**
5. Download the credentials file

### Step 2: Configure Credentials
Choose one of these methods:

**Method A: Credentials File**
1. Download `credentials.json` from Google Cloud Console
2. Place it in the `gmail_mcp_v1/` folder

**Method B: Environment Variables**
```bash
export GOOGLE_CLIENT_ID="your_client_id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your_client_secret"
```

**Method C: Use Template**
1. Copy `credentials_template.json` to `credentials.json`
2. Fill in your actual client ID and secret

## 🎮 How It Works

1. **Gmail MCP Server** starts on `http://127.0.0.1:5001`
2. **AI Agent** connects to Gemini 2.0 Flash
3. **Agent** plans Gmail operations using available tools:
   - `get_gmail_info()` - Get account info
   - `send_email()` - Send emails
   - `compose_email()` - Create drafts
   - `list_recent_emails()` - List emails
4. **Gmail API** executes operations
5. **Results** saved to `gmail_session.json`

## 📝 Example Tasks You Can Try

### Send Emails
- "Send an email to john@example.com with subject 'Meeting Tomorrow' and message 'Hi John, don't forget our meeting at 2 PM tomorrow.'"
- "Email sarah@company.com about the project update"

### Compose Drafts
- "Compose a draft email to team@company.com about the weekly report"
- "Create a draft for my boss about vacation request"

### Check Emails
- "List my recent emails"
- "Show me the last 10 emails in my inbox"
- "Check my Gmail account status"

## 🔍 Available Tools

### get_gmail_info()
Gets Gmail account information and authentication status.

**Response:**
```json
{
  "status": "ok",
  "gmail_info": {
    "user_email": "your@email.com",
    "messages_total": 1234,
    "threads_total": 567,
    "authenticated": true
  }
}
```

### send_email(params)
Sends an email via Gmail API.

**Parameters:**
- `to` (required): Recipient email address
- `subject` (required): Email subject
- `body` (required): Email body content  
- `cc` (optional): CC recipients
- `bcc` (optional): BCC recipients

**Example:**
```json
{
  "to": "recipient@example.com",
  "subject": "Hello from AI",
  "body": "This is a test email from an AI agent!",
  "cc": "manager@company.com"
}
```

### compose_email(params) 
Creates an email draft in Gmail.

**Parameters:**
- `to` (required): Recipient email address
- `subject` (required): Email subject
- `body` (required): Email body content

### list_recent_emails(params)
Lists recent emails from Gmail.

**Parameters:**
- `max_results` (optional): Number of emails to return (default: 10, max: 50)

## 📊 Output Files

- `gmail_session.json` - Complete execution log with LLM requests/responses
- `gmail_agent.log` - System operation logs
- `token.json` - OAuth tokens (auto-generated after first auth)

## 🔒 Security & Privacy

- Uses OAuth 2.0 for secure Gmail access
- API key for Gemini is included (for demo purposes)
- Email content is processed by Gemini AI
- Tokens stored locally in `token.json`
- No email content is permanently stored

## 🔍 Troubleshooting

### Gmail Authentication Issues
```
❌ Gmail authentication failed
```
**Solution:** 
1. Check `credentials.json` is valid
2. Ensure Gmail API is enabled
3. Verify OAuth consent screen is configured
4. Delete `token.json` and re-authenticate

### Missing Dependencies
```
❌ Gmail dependencies not available
```
**Solution:**
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Permission Denied
```
❌ insufficient authentication scopes
```
**Solution:**
1. Delete `token.json`
2. Re-run the application
3. Grant all requested permissions

### Rate Limiting
```
❌ Quota exceeded
```
**Solution:**
- Gmail API has daily limits
- Wait and try again later
- Consider upgrading your Google Cloud quotas

## 🏗️ Architecture

```
User Input → AI Agent (Gemini) → Gmail MCP Server → Gmail API → Email Sent
                ↓
         gmail_session.json (logs all interactions)
```

## 📋 Project Structure

```
gmail_mcp_v1/
├── mcp_server.py          # Gmail MCP server with API integration
├── agent.py               # AI agent with Gemini 2.0 Flash
├── prompt_manager.py      # Email-focused system prompts
├── utils.py               # Logging and timing utilities
├── setup_and_run.py       # Main setup and execution script
├── requirements.txt       # Python dependencies
├── credentials_template.json # OAuth credentials template
├── README.md              # This file
└── [generated files]
    ├── gmail_session.json # Execution logs
    ├── gmail_agent.log    # System logs
    └── token.json         # OAuth tokens (auto-generated)
```

## 🚀 Ready to Send Emails!

Just run `python setup_and_run.py` and watch AI control your Gmail automatically! 📧✨

## ⚠️ Important Notes

- This is a demo system with hardcoded API keys
- For production use, secure your API keys properly
- Review all emails before sending in production
- Respect email recipients and anti-spam policies
- Gmail API quotas apply - use responsibly
