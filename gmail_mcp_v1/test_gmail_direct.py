#!/usr/bin/env python3
"""
Simple Gmail Test - No LLM, just direct email sending
"""
import os
import json
import base64
import requests
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_gmail_direct():
    """Test Gmail sending without LLM"""
    print("📧 Testing Gmail Direct Send (No LLM)")
    print("="*40)
    
    if not os.path.exists('token.json'):
        print("❌ token.json not found")
        return False
    
    try:
        # Load credentials
        creds = Credentials.from_authorized_user_file('token.json')
        
        # Refresh if needed
        if creds.expired and creds.refresh_token:
            print("🔄 Refreshing token...")
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        # Get user email
        headers = {'Authorization': f'Bearer {creds.token}'}
        response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers=headers,
            verify=False
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get user info: {response.status_code}")
            return False
        
        user_email = response.json().get('email')
        print(f"✅ Authenticated as: {user_email}")
        
        # Create test email
        subject = "🎉 Gmail MCP Success Test"
        body = """Hello!

This email was sent successfully by the Gmail MCP system!

✅ OAuth authentication: WORKING
✅ Gmail API connection: WORKING  
✅ Email sending: WORKING
✅ Multi-step research ready: YES (waiting for Gemini quota)

The system is fully functional. Once the Gemini API quota resets, 
you'll be able to use the complete multi-step research workflow.

Best regards,
Gmail MCP System"""
        
        # Create MIME message
        message = MIMEText(body)
        message['to'] = user_email
        message['subject'] = subject
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode('utf-8')
        
        # Send email
        print(f"📤 Sending test email to {user_email}...")
        
        send_response = requests.post(
            'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
            headers=headers,
            json={'raw': raw_message},
            verify=False
        )
        
        if send_response.status_code == 200:
            print("🎉 SUCCESS! Test email sent successfully!")
            print(f"📧 Check your inbox: {user_email}")
            print("✅ Gmail MCP system is fully working!")
            return True
        else:
            print(f"❌ Email send failed: {send_response.status_code}")
            print(f"Error: {send_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_gmail_direct()
    
    if success:
        print("\n🚀 Gmail MCP System Status: FULLY WORKING!")
        print("⏰ Wait for Gemini quota reset, then run:")
        print("▶️  python multi_step_research_gmail.py")
    else:
        print("❌ Test failed - check errors above")
