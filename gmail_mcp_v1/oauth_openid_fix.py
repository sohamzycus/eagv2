#!/usr/bin/env python3
"""
OAuth Fix - Include openid scope to match Google's automatic addition
"""
import os
import json
import webbrowser
from google_auth_oauthlib.flow import InstalledAppFlow

def oauth_with_openid():
    """OAuth that includes openid scope to prevent mismatches"""
    print("🔐 OAuth with OpenID Scope Fix")
    print("="*40)
    
    # Clean slate
    for file in ['token.json']:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️ Removed {file}")
    
    # Include openid scope that Google automatically adds
    SCOPES = [
        'openid',  # Add this to match Google's automatic inclusion
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly'
    ]
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        
        auth_url, _ = flow.authorization_url(
            prompt='consent',
            access_type='offline'
        )
        
        print("🌐 OAuth URL with OpenID scope included:")
        print(f"   {auth_url}")
        print()
        print("📋 This should work now - scopes match what Google expects!")
        
        webbrowser.open(auth_url)
        
        print("\n📝 Steps:")
        print("   1. Browser opened - sign in")
        print("   2. Grant permissions")
        print("   3. Copy authorization code")
        print("   4. Paste below")
        
        code = input("\n📝 Authorization code: ").strip()
        
        if not code:
            print("❌ No code provided")
            return False
        
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        with open('token.json', 'w') as f:
            f.write(creds.to_json())
        
        print(f"\n🎉 SUCCESS! token.json created with matching scopes")
        print(f"📧 Token: {creds.token[:20]}...")
        
        # Test the token quickly
        print("\n🧪 Testing token...")
        import requests
        headers = {'Authorization': f'Bearer {creds.token}'}
        response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers=headers,
            verify=False
        )
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ Token works! Authenticated as: {user_info.get('email', 'Unknown')}")
        else:
            print(f"⚠️ Token test failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        return False

if __name__ == "__main__":
    success = oauth_with_openid()
    
    if success:
        print("\n🚀 Authentication complete with correct scopes!")
        print("▶️  Now run: python multi_step_research_gmail.py")
        print("📧 Test: 'Research AI trends and email to your@email.com'")
    else:
        print("❌ Still failed - check error above")
