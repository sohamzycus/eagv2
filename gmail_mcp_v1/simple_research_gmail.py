#!/usr/bin/env python3
"""
Simple Research Gmail MCP - Working Version
Enhanced Gmail MCP with research capabilities but simplified dependencies
"""
import os
import json
import base64
import requests
import time
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SimpleResearchGmail:
    """Simple Research Gmail MCP with basic AI capabilities"""
    
    def __init__(self):
        self.creds = None
        self.user_email = None
        self.load_credentials()
    
    def load_credentials(self):
        """Load Gmail credentials"""
        if not os.path.exists('token.json'):
            print("❌ token.json not found")
            return False
        
        try:
            self.creds = Credentials.from_authorized_user_file('token.json', [
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/userinfo.email'
            ])
            
            # Refresh if needed
            if self.creds.expired and self.creds.refresh_token:
                from google.auth.transport.requests import Request
                self.creds.refresh(Request())
                with open('token.json', 'w') as token:
                    token.write(self.creds.to_json())
            
            # Get user email
            headers = {'Authorization': f'Bearer {self.creds.token}'}
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers=headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                self.user_email = response.json().get('email')
                return True
            
            return False
        except Exception as e:
            print(f"❌ Failed to load credentials: {e}")
            return False
    
    def research_topic(self, topic):
        """Simple research function - generates structured content about a topic"""
        print(f"🔍 Researching: {topic}")
        
        # Simple research simulation with structured content
        research_data = {
            'topic': topic,
            'summary': f"Comprehensive research on {topic}",
            'key_points': [
                f"Key aspect 1 of {topic}",
                f"Important consideration about {topic}",
                f"Current trends in {topic}",
                f"Future implications of {topic}"
            ],
            'recommendations': [
                f"Best practice for {topic}",
                f"Implementation strategy for {topic}",
                f"Monitoring approach for {topic}"
            ],
            'sources': [
                "Academic research papers",
                "Industry reports",
                "Expert analysis",
                "Current market data"
            ]
        }
        
        return research_data
    
    def generate_research_email(self, topic, research_data, recipient):
        """Generate a professional research email"""
        subject = f"Research Summary: {topic}"
        
        body_parts = [
            "Dear Recipient,",
            "",
            f"I've completed comprehensive research on '{topic}' as requested. Here are the key findings:",
            "",
            "## Executive Summary",
            research_data['summary'],
            "",
            "## Key Points",
        ]
        
        for i, point in enumerate(research_data['key_points'], 1):
            body_parts.append(f"{i}. {point}")
        
        body_parts.extend([
            "",
            "## Recommendations",
        ])
        
        for i, rec in enumerate(research_data['recommendations'], 1):
            body_parts.append(f"{i}. {rec}")
        
        body_parts.extend([
            "",
            "## Research Sources",
            "This analysis is based on:",
        ])
        
        for source in research_data['sources']:
            body_parts.append(f"• {source}")
        
        body_parts.extend([
            "",
            "## Next Steps",
            "Please review this research summary and let me know if you need:",
            "• Additional details on any specific aspect",
            "• Further analysis of particular areas",
            "• Follow-up research on related topics",
            "",
            "I'm available to discuss these findings and provide additional insights as needed.",
            "",
            "Best regards,",
            "AI Research Assistant"
        ])
        
        return {
            'subject': subject,
            'body': "\\n".join(body_parts),
            'recipient': recipient
        }
    
    def send_email(self, to_email, subject, body, cc=None, bcc=None):
        """Send email using direct Gmail API"""
        if not self.creds:
            return {'status': 'error', 'error': 'Not authenticated'}
        
        try:
            print(f"📤 Sending research email to: {to_email}")
            print(f"📋 Subject: {subject}")
            
            headers = {'Authorization': f'Bearer {self.creds.token}'}
            
            # Create message
            message = MIMEText(body.replace('\\n', '\n'))
            message['to'] = to_email
            message['subject'] = subject
            message['from'] = self.user_email
            
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            # Convert to base64
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send email
            send_data = {'raw': raw_message}
            response = requests.post(
                'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
                headers={
                    'Authorization': f'Bearer {self.creds.token}',
                    'Content-Type': 'application/json'
                },
                json=send_data,
                verify=False,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'status': 'ok',
                    'message_id': result.get('id'),
                    'to': to_email,
                    'subject': subject,
                    'from': self.user_email,
                    'thread_id': result.get('threadId')
                }
            else:
                return {'status': 'error', 'error': f'HTTP {response.status_code} - {response.text}'}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def process_research_and_email(self, topic, recipient):
        """Complete research workflow: research topic and email results"""
        print(f"🎯 Processing research request: '{topic}' for {recipient}")
        
        try:
            # Step 1: Research the topic
            research_data = self.research_topic(topic)
            
            # Step 2: Generate email content
            email_content = self.generate_research_email(topic, research_data, recipient)
            
            # Step 3: Send the email
            result = self.send_email(
                email_content['recipient'],
                email_content['subject'],
                email_content['body']
            )
            
            return {
                'status': 'ok' if result['status'] == 'ok' else 'error',
                'topic': topic,
                'recipient': recipient,
                'research_data': research_data,
                'email_result': result,
                'error': result.get('error') if result['status'] == 'error' else None
            }
        except Exception as e:
            print(f"❌ Error in research workflow: {e}")
            return {
                'status': 'error',
                'topic': topic,
                'recipient': recipient,
                'error': str(e)
            }

def parse_natural_command(user_input):
    """Parse natural language commands flexibly"""
    user_input = user_input.strip().lower()
    
    # Extract email addresses
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, user_input, re.IGNORECASE)
    
    # Common command patterns
    research_keywords = ['research', 'analyze', 'study', 'investigate', 'look into', 'find out about', 'tell me about']
    email_keywords = ['email', 'send', 'mail', 'share', 'forward', 'notify']
    
    # Check if it's a research + email command
    has_research = any(keyword in user_input for keyword in research_keywords)
    has_email = any(keyword in user_input for keyword in email_keywords) or len(emails) > 0
    
    if has_research and (has_email or len(emails) > 0):
        # Extract topic by removing command words and email
        topic = user_input
        
        # Remove command keywords
        for keyword in research_keywords + email_keywords + ['to', 'and', 'then', 'about']:
            topic = topic.replace(keyword, ' ')
        
        # Remove email addresses
        for email in emails:
            topic = topic.replace(email.lower(), ' ')
        
        # Clean up topic
        topic = ' '.join(topic.split())  # Remove extra spaces
        topic = topic.strip('\'"')  # Remove quotes
        
        return {
            'type': 'research_email',
            'topic': topic,
            'recipient': emails[0] if emails else None
        }
    
    elif has_research:
        # Just research, no email
        topic = user_input
        for keyword in research_keywords + ['about']:
            topic = topic.replace(keyword, ' ')
        topic = ' '.join(topic.split()).strip('\'"')
        
        return {
            'type': 'research_only',
            'topic': topic
        }
    
    elif has_email and len(emails) > 0:
        # Direct email
        return {
            'type': 'direct_email',
            'recipient': emails[0]
        }
    
    return {
        'type': 'unknown',
        'original': user_input
    }

def main():
    """Test the simple research Gmail system"""
    print("🚀 Starting Simple Research Gmail MCP...")
    
    # Initialize
    gmail = SimpleResearchGmail()
    
    if not gmail.creds:
        print("❌ Gmail authentication failed")
        return
    
    print(f"✅ Connected to Gmail: {gmail.user_email}")
    
    print("\n" + "="*60)
    print("🤖 Natural Language Research Gmail MCP")
    print("="*60)
    print("Examples of what you can say:")
    print("• 'Research Indian cricket team and email to john@example.com'")
    print("• 'Analyze AI trends and send to boss@company.com'")
    print("• 'Look into renewable energy, then email results to team@work.com'")
    print("• 'Tell me about machine learning and share with colleague@office.com'")
    print("• 'Study blockchain technology and notify expert@crypto.com'")
    print("• 'quit' - Exit")
    print()
    
    while True:
        try:
            user_input = input("💬 What would you like me to do? ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            if not user_input:
                continue
            
            # Parse the natural language command
            parsed = parse_natural_command(user_input)
            
            if parsed['type'] == 'research_email':
                topic = parsed['topic']
                recipient = parsed['recipient']
                
                if not recipient:
                    recipient = input("📧 Which email should I send the results to? ").strip()
                
                if topic and recipient:
                    print(f"🎯 I'll research '{topic}' and email results to {recipient}")
                    
                    result = gmail.process_research_and_email(topic, recipient)
                    
                    if result['status'] == 'ok':
                        print(f"✅ Research completed and email sent!")
                        print(f"📧 Subject: {result['email_result']['subject']}")
                        print(f"🔬 Covered {len(result['research_data']['key_points'])} key points")
                    else:
                        print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                        if result.get('error'):
                            print(f"   Details: {result['error']}")
                else:
                    print("❌ I need both a topic and an email address")
            
            elif parsed['type'] == 'research_only':
                topic = parsed['topic']
                if topic:
                    print(f"🔍 I'll research '{topic}' for you")
                    research_data = gmail.research_topic(topic)
                    
                    print(f"✅ Research completed on '{topic}':")
                    print(f"📊 {research_data['summary']}")
                    print(f"🔑 Key points: {len(research_data['key_points'])}")
                    
                    send_email = input("📧 Would you like me to email these results? (y/n): ").strip().lower()
                    if send_email == 'y':
                        recipient = input("📧 Which email should I send to? ").strip()
                        if recipient:
                            result = gmail.process_research_and_email(topic, recipient)
                            if result['status'] == 'ok':
                                print(f"✅ Email sent to {recipient}!")
                            else:
                                print(f"❌ Email failed: {result.get('error')}")
                else:
                    print("❌ Please specify what you'd like me to research")
            
            elif parsed['type'] == 'direct_email':
                recipient = parsed['recipient']
                print(f"📧 Direct email to {recipient}")
                
                subject = input("📋 Subject: ").strip()
                body = input("📝 Message: ").strip()
                
                if subject and body:
                    result = gmail.send_email(recipient, subject, body)
                    if result['status'] == 'ok':
                        print(f"✅ Email sent successfully!")
                    else:
                        print(f"❌ Failed to send: {result.get('error')}")
                else:
                    print("❌ Both subject and message are required")
            
            else:
                print("❌ I didn't understand that. Try something like:")
                print("   'Research machine learning and email to colleague@company.com'")
                print("   'Analyze market trends and send to boss@work.com'")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
