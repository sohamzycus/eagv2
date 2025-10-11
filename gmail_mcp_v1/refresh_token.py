#!/usr/bin/env python3
"""
Gmail Token Refresh Utility
Quick script to refresh expired Gmail OAuth tokens
"""
import os
import json
from google.oauth2.credentials import Credentials

def refresh_gmail_token():
    """Refresh Gmail OAuth token"""
    print("🔄 Gmail Token Refresh Utility")
    print("="*40)
    
    if not os.path.exists('token.json'):
        print("❌ token.json not found")
        print("💡 Run setup_and_run.py to authenticate first")
        return False
    
    try:
        # Load existing credentials
        creds = Credentials.from_authorized_user_file('token.json', [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/userinfo.email'
        ])
        
        print(f"📋 Current token status:")
        print(f"   Valid: {creds.valid}")
        print(f"   Expired: {creds.expired}")
        print(f"   Has refresh token: {bool(creds.refresh_token)}")
        
        if creds.expired and creds.refresh_token:
            print("\n🔄 Refreshing expired token...")
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            
            # Save refreshed credentials
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            
            print("✅ Token refreshed successfully!")
            print(f"   New expiry: {creds.expiry}")
            return True
            
        elif not creds.refresh_token:
            print("❌ No refresh token available")
            print("💡 You need to re-authenticate. Run setup_and_run.py")
            return False
            
        else:
            print("✅ Token is still valid")
            return True
            
    except Exception as e:
        print(f"❌ Failed to refresh token: {e}")
        print("💡 Try running setup_and_run.py to re-authenticate")
        return False

if __name__ == "__main__":
    success = refresh_gmail_token()
    
    if success:
        print("\n🎯 You can now use the Gmail MCP system!")
        print("   Run: python multi_step_research_gmail.py")
    else:
        print("\n🔧 Authentication needed:")
        print("   Run: python setup_and_run.py")


