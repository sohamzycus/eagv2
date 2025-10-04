#!/usr/bin/env python3
"""
Setup and Run Script for Gmail MCP v1
Sets up the .env file and runs the demo
"""
import os
import sys
import subprocess
import threading
import time
import json

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Installing...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'python-dotenv'])
    from dotenv import load_dotenv
    load_dotenv()

# Check if API key is available from .env or environment
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')

def setup_environment():
    """Set up .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        print("⚠️  No .env file found!")
        print("Creating .env file with your API key...")
        
        env_content = """# Environment variables for Gmail MCP
GOOGLE_API_KEY=AIzaSyBomWfEWE4Usj9FVbWQs5NvNV2dMjuIiDs
GEMINI_API_KEY=AIzaSyBomWfEWE4Usj9FVbWQs5NvNV2dMjuIiDs
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with API key")
        
        # Reload environment variables
        load_dotenv()
        global GOOGLE_API_KEY
        GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    
    if GOOGLE_API_KEY:
        os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY
        os.environ['GEMINI_API_KEY'] = GOOGLE_API_KEY
        print(f"✅ Set API keys from .env file: {GOOGLE_API_KEY[:20]}...")
    else:
        print("❌ No API key found in .env file or environment variables")
        return False
    
    return True

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'flask',
        'requests', 
        'google-auth',
        'google-auth-oauthlib',
        'google-auth-httplib2',
        'google-api-python-client',
        'google-genai'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            # Handle different import names
            import_name = package.replace('-', '_')
            if package == 'google-api-python-client':
                import_name = 'googleapiclient'
            elif package == 'google-auth-oauthlib':
                import_name = 'google_auth_oauthlib'
            elif package == 'google-auth-httplib2':
                import_name = 'google_auth_httplib2'
            
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ Installed {package}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                return False
    else:
        print("✅ All required packages are installed")
    
    return True

def check_gmail_credentials():
    """Check if Gmail credentials are available"""
    if os.path.exists('credentials.json'):
        print("✅ Found credentials.json for Gmail OAuth")
        return True
    elif os.environ.get('GOOGLE_CLIENT_ID') and os.environ.get('GOOGLE_CLIENT_SECRET'):
        print("✅ Found Gmail OAuth credentials in environment variables")
        return True
    else:
        print("⚠️  No Gmail credentials found!")
        print("")
        print("To use Gmail API, you need to:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials")
        print("5. Download credentials.json and place it in this folder")
        print("")
        print("OR set environment variables:")
        print("  GOOGLE_CLIENT_ID=your_client_id")
        print("  GOOGLE_CLIENT_SECRET=your_client_secret")
        print("")
        return False

def start_server():
    """Start the Gmail MCP server"""
    try:
        import mcp_server
        print("🚀 Starting Gmail MCP Server on http://127.0.0.1:5001")
        mcp_server.main()
    except Exception as e:
        print(f"❌ Server error: {e}")

def start_agent():
    """Start the AI agent"""
    try:
        import agent
        print("🤖 Starting AI Agent...")
        time.sleep(2)  # Give server time to start
        
        # Run with a custom question
        print("")
        print("Gmail operations you can try:")
        print("- Send an email to someone@example.com with subject 'Hello' and message 'Test'")
        print("- List my recent emails")
        print("- Compose a draft email to colleague@company.com about meeting")
        print("- Check my Gmail account status")
        print("")
        question = input("Enter your email task (or press Enter for default): ").strip()
        if not question:
            question = "Send an email to test@example.com with subject 'Hello from AI' and message 'This is a test email from an AI agent!'"
        
        print(f"🎯 Agent task: {question}")
        print("⏳ Note: Gmail authentication may take 1-2 minutes on first run...")
        session = agent.run_agent(question, 'http://127.0.0.1:5001', 'gmail_session.json')
        
        print("✅ Agent execution completed!")
        print("📄 Check 'gmail_session.json' for detailed logs")
        print("📄 Check 'gmail_agent.log' for system logs")
        
        return session
        
    except Exception as e:
        print(f"❌ Agent error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main setup and execution function"""
    print("=" * 60)
    print("📧 Gmail MCP v1 - Setup & Run")
    print("=" * 60)
    
    # Setup environment
    if not setup_environment():
        print("❌ Failed to setup environment variables")
        return
    
    # Check requirements
    if not check_requirements():
        print("❌ Failed to install required packages")
        return
    
    # Check Gmail credentials
    if not check_gmail_credentials():
        print("❌ Gmail credentials not configured")
        print("The system will still run but Gmail operations will fail.")
        print("")
        proceed = input("Continue anyway? (y/N): ").strip().lower()
        if proceed != 'y':
            return
    
    print("\n" + "=" * 60)
    print("🚀 Starting Gmail MCP System...")
    print("=" * 60)
    
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start
    time.sleep(3)
    
    # Start agent
    session = start_agent()
    
    if session:
        print("\n" + "=" * 60)
        print("📊 Execution Summary:")
        print("=" * 60)
        print(f"🔧 Tools executed: {len(session.get('tool_execution', []))}")
        for i, tool_exec in enumerate(session.get('tool_execution', []), 1):
            tool_name = tool_exec.get('tool', 'unknown')
            status = tool_exec.get('response', {}).get('status', 'unknown')
            print(f"  {i}. {tool_name}: {status}")
            
            # Show email details if available
            if tool_name == 'send_email' and status == 'ok':
                resp = tool_exec.get('response', {})
                print(f"     📧 Sent to: {resp.get('to', 'unknown')}")
                print(f"     📝 Subject: {resp.get('subject', 'unknown')}")
                print(f"     🆔 Message ID: {resp.get('message_id', 'unknown')}")
        
        print(f"\n📝 Session saved to: gmail_session.json")
        print(f"📝 Logs saved to: gmail_agent.log")
    
    print("\n🎉 Demo completed! Check your Gmail for results.")
    input("Press Enter to exit...")

if __name__ == '__main__':
    main()
