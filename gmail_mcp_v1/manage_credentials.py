#!/usr/bin/env python3
"""
Gmail MCP Credential Manager
Safely manages credential files outside the repository
"""
import os
import shutil
import json

def setup_credentials():
    """Setup credentials from secure location"""
    secure_dir = "../gmail_credentials_secure"
    repo_dir = "."
    
    print("🔐 Gmail MCP Credential Manager")
    print("="*40)
    
    if not os.path.exists(secure_dir):
        print(f"❌ Secure directory not found: {secure_dir}")
        print("💡 Run authentication setup first")
        return False
    
    # Files to link/copy
    credential_files = [
        "credentials.json",
        "token.json", 
        "gmail_session.json",
        "llm_gmail_session.json"
    ]
    
    print("🔗 Setting up credential file access...")
    
    for file in credential_files:
        secure_path = os.path.join(secure_dir, file)
        repo_path = os.path.join(repo_dir, file)
        
        if os.path.exists(secure_path):
            # Remove existing file/link
            if os.path.exists(repo_path):
                os.remove(repo_path)
            
            # On Windows, create a hard link or copy
            try:
                # Try hard link first (more efficient)
                os.link(secure_path, repo_path)
                print(f"  ✅ Hard linked {file}")
            except OSError:
                # Fallback to copy
                shutil.copy2(secure_path, repo_path)
                print(f"  ✅ Copied {file}")
        else:
            print(f"  ⚠️  {file} not found in secure location")
    
    print(f"\n📁 Secure location: {os.path.abspath(secure_dir)}")
    print("🔐 Credentials accessible in repository (but not tracked by git)")
    
    return True

def cleanup_credentials():
    """Remove credential files from repository"""
    credential_files = [
        "credentials.json",
        "token.json",
        "gmail_session.json", 
        "llm_gmail_session.json"
    ]
    
    print("🧹 Cleaning up credential files from repository...")
    
    for file in credential_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"  ✅ Removed {file}")
    
    print("✅ Repository cleaned of credential files")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_credentials()
    else:
        success = setup_credentials()
        
        if success:
            print("\n🚀 Ready to use Gmail MCP!")
            print("▶️  python multi_step_research_gmail.py")
            print("▶️  python test_gmail_direct.py")
        else:
            print("\n❌ Setup failed - check secure directory")
