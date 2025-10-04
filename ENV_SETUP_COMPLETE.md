# 🔐 .env File Setup Guide - Project-Level API Keys

## ✅ Setup Complete!

I've configured both projects to use `.env` files for secure API key management:

---

## 📁 Project Structure

### Gmail MCP v1
```
gmail_mcp_v1/
├── .env              ← Your API key (auto-created, not in version control)
├── .gitignore        ← Ignores .env file  
├── create_env.bat    ← Creates .env file (Windows)
├── create_env.ps1    ← Creates .env file (PowerShell)
├── env_template.txt  ← Template for reference
└── ... (rest of files)
```

### MSPaint MCP v2
```
mspaint_mcp_production_v2/
├── .env              ← Your API key (auto-created, not in version control)
├── .gitignore        ← Ignores .env file
├── create_env.bat    ← Creates .env file (Windows)
└── ... (rest of files)
```

---

## 🚀 How to Use

### Method 1: Automatic Creation (Easiest)
Just run the main setup script - it will create the `.env` file automatically:

```bash
# Gmail project
cd gmail_mcp_v1
python setup_and_run.py

# MSPaint project  
cd mspaint_mcp_production_v2
python setup_and_run.py
```

### Method 2: Manual Creation
```bash
# Gmail project
cd gmail_mcp_v1
create_env.bat

# MSPaint project
cd mspaint_mcp_production_v2  
create_env.bat
```

---

## 📝 .env File Content

Both projects will have this `.env` file content:
```
# Environment variables
GOOGLE_API_KEY=AIzaSyBomWfEWE4Usj9FVbWQs5NvNV2dMjuIiDs
GEMINI_API_KEY=AIzaSyBomWfEWE4Usj9FVbWQs5NvNV2dMjuIiDs
```

---

## 🔒 Security Features

### ✅ What's Protected:
- **`.env` files are in `.gitignore`** - won't be committed to version control
- **No hardcoded keys** in source files
- **Project-specific** - each project has its own `.env`
- **Easy to change** - just edit the `.env` file

### ✅ Code Changes Made:
- **Added `python-dotenv`** to requirements.txt
- **Updated agents** to load from `.env` first
- **Removed hardcoded keys** from source code
- **Added error messages** to guide users to create `.env`

---

## 🔍 Verification

After setup, verify your configuration:

```python
# This should NOT show in source code anymore
logger.info('Using fallback API key')  # ❌ Removed

# This will show instead
logger.error('No API key found. Please set GOOGLE_API_KEY in .env file')  # ✅ New
```

---

## 🎯 Benefits

1. **🔐 Secure**: API keys not in source code
2. **🔄 Flexible**: Easy to change keys per environment  
3. **👥 Team-friendly**: Each developer uses their own keys
4. **🚫 Git-safe**: `.env` files automatically ignored
5. **📁 Project-scoped**: Keys stay with each project

---

## 🎉 You're All Set!

Your API key `AIzaSyBomWfEWE4Usj9FVbWQs5NvNV2dMjuIiDs` is now securely managed through `.env` files in both projects!

- ✅ No keys visible in source code
- ✅ Version control safe  
- ✅ Easy to manage and rotate
- ✅ Professional development practices

Just run `python setup_and_run.py` in either project folder and everything will work automatically! 🚀
