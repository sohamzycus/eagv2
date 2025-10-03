# 🔧 Gmail API Setup Guide - Step by Step

## Overview
To use the Gmail MCP system, you need to enable Gmail API in Google Cloud Console and download OAuth credentials. This guide walks you through the entire process.

## 📋 Prerequisites
- Google account (Gmail account)
- Web browser
- 10-15 minutes of time

---

## Step 1: Access Google Cloud Console

1. **Open your web browser** and go to: https://console.cloud.google.com/
2. **Sign in** with your Google account (the same account whose Gmail you want to control)
3. You'll see the Google Cloud Console dashboard

---

## Step 2: Create or Select a Project

### Option A: Create New Project (Recommended for first-time users)
1. **Click the project dropdown** at the top of the page (next to "Google Cloud")
2. **Click "NEW PROJECT"** button
3. **Enter project details:**
   - Project name: `Gmail MCP Demo` (or any name you prefer)
   - Organization: Leave as default or "No organization"
   - Location: Leave as default
4. **Click "CREATE"** button
5. **Wait** for project creation (30-60 seconds)
6. **Select your new project** from the dropdown

### Option B: Use Existing Project
1. **Click the project dropdown** at the top
2. **Select an existing project** you want to use

---

## Step 3: Enable Gmail API

1. **Navigate to APIs & Services:**
   - Click the hamburger menu (☰) in the top-left
   - Click "APIs & Services" 
   - Click "Library"

2. **Search for Gmail API:**
   - In the search box, type: `Gmail API`
   - Click on "Gmail API" from the results

3. **Enable the API:**
   - Click the blue "ENABLE" button
   - Wait for activation (10-30 seconds)
   - You'll see "API enabled" confirmation

---

## Step 4: Configure OAuth Consent Screen

1. **Go to OAuth consent screen:**
   - In the left sidebar, click "OAuth consent screen"

2. **Choose User Type:**
   - Select "External" (unless you have a Google Workspace account)
   - Click "CREATE"

3. **Fill in App Information:**
   - **App name:** `Gmail MCP Demo`
   - **User support email:** Your email address
   - **Developer contact email:** Your email address
   - Leave other fields as default
   - Click "SAVE AND CONTINUE"

4. **Scopes (Step 2):**
   - Click "SAVE AND CONTINUE" (we'll add scopes programmatically)

5. **Test users (Step 3):**
   - Click "ADD USERS"
   - Add your own email address
   - Click "ADD"
   - Click "SAVE AND CONTINUE"

6. **Summary (Step 4):**
   - Review the information
   - Click "BACK TO DASHBOARD"

---

## Step 5: Create OAuth 2.0 Credentials

1. **Go to Credentials:**
   - In the left sidebar, click "Credentials"

2. **Create Credentials:**
   - Click "CREATE CREDENTIALS" at the top
   - Select "OAuth client ID"

3. **Configure OAuth client:**
   - **Application type:** Select "Desktop application"
   - **Name:** `Gmail MCP Client`
   - Click "CREATE"

4. **Download Credentials:**
   - A popup will appear showing your client ID and secret
   - **Click "DOWNLOAD JSON"** button
   - Save the file as `credentials.json`
   - **Important:** Remember where you save this file!

---

## Step 6: Place Credentials File

1. **Locate your downloaded file:**
   - It's usually in your Downloads folder
   - Named something like `client_secret_123456789.json`

2. **Rename and move the file:**
   - Rename it to exactly: `credentials.json`
   - Move it to your `gmail_mcp_v1/` folder
   - The final path should be: `gmail_mcp_v1/credentials.json`

---

## 🎉 Verification

Your `gmail_mcp_v1/` folder should now contain:
```
gmail_mcp_v1/
├── credentials.json          ← Your downloaded file (NEW!)
├── mcp_server.py
├── agent.py
├── setup_and_run.py
└── ... (other files)
```

---

## 🚀 Test Your Setup

1. **Run the Gmail MCP system:**
   ```bash
   cd gmail_mcp_v1
   python setup_and_run.py
   ```

2. **First-time authentication:**
   - Your browser will open automatically
   - Sign in with your Google account
   - Click "Allow" to grant permissions:
     - ✅ Send email on your behalf
     - ✅ View your email messages
     - ✅ Manage drafts

3. **Success indicators:**
   - Console shows: `✅ Gmail service authenticated for: your@email.com`
   - A `token.json` file is created automatically
   - The system is ready to send emails!

---

## 🔍 Troubleshooting

### Error: "credentials.json not found"
- **Solution:** Make sure the file is named exactly `credentials.json` (not `credentials.json.txt`)
- **Check location:** File must be directly in the `gmail_mcp_v1/` folder

### Error: "Gmail API not enabled"
- **Solution:** Go back to Google Cloud Console → APIs & Services → Library
- **Search:** "Gmail API" and make sure it shows "API enabled"

### Error: "OAuth consent screen not configured"  
- **Solution:** Complete Step 4 above, especially adding yourself as a test user

### Error: "Access denied" or "insufficient scopes"
- **Solution:** 
  1. Delete the `token.json` file
  2. Run the setup again
  3. Grant all requested permissions

---

## 🔒 Security Notes

- **Keep credentials.json secure** - it contains your OAuth client secret
- **Don't share credentials.json** - it's specific to your project
- **Token.json** is auto-generated and contains your access tokens
- **For production use:** Use environment variables instead of credential files

---

## 📞 Need Help?

If you encounter issues:
1. **Check the logs:** Look at `gmail_agent.log` for detailed error messages
2. **Verify project:** Make sure you're using the correct Google Cloud project
3. **Double-check steps:** Ensure Gmail API is enabled and OAuth is configured
4. **Test with simple command:** Try "Check my Gmail account status" first

---

## 🎯 What's Next?

Once setup is complete, you can:
- Send emails via AI commands
- List your recent emails  
- Compose drafts automatically
- Integrate with other systems

**Ready to send your first AI email!** 🚀📧
