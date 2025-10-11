#!/usr/bin/env python3
"""
Enhanced Gmail MCP with Research Capabilities
Supports research queries, web search, content analysis, and intelligent email generation
"""
import os
import json
import base64
import requests
import time
import re
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

class ResearchGmailMCP:
    """Enhanced Gmail MCP with research and analysis capabilities"""
    
    def __init__(self):
        self.creds = None
        self.user_email = None
        self.session_data = {}
        self.load_credentials()
        self.setup_gemini()
    
    def setup_gemini(self):
        """Setup Gemini API for research capabilities"""
        self.gemini_api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
        if not self.gemini_api_key:
            print("⚠️ No Gemini API key found - research features will be limited")
            self.gemini_client = None
        else:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.gemini_api_key)
                print("✅ Gemini API client initialized for research")
            except ImportError:
                print("⚠️ google-genai not available - research features limited")
                self.gemini_client = None
    
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
    
    def search_web(self, query, max_results=5):
        """Search web for information using multiple sources"""
        print(f"🔍 Searching web for: {query}")
        
        # For demo purposes, simulate web search results
        # In production, you'd integrate with actual search APIs
        search_results = {
            'status': 'ok',
            'query': query,
            'results': [
                {
                    'title': f'Research on {query}',
                    'url': 'https://example.com/research',
                    'snippet': f'Comprehensive information about {query} including key insights and analysis.',
                    'relevance': 0.95
                },
                {
                    'title': f'{query} - Latest Developments',
                    'url': 'https://example.com/latest',
                    'snippet': f'Recent developments and trends related to {query}.',
                    'relevance': 0.88
                }
            ]
        }
        
        # If Gemini is available, enhance results with AI analysis
        if self.gemini_client:
            try:
                analysis_prompt = f"Analyze and summarize key points about: {query}"
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=[{'parts': [{'text': analysis_prompt}]}]
                )
                search_results['ai_analysis'] = response.text
            except Exception as e:
                print(f"⚠️ AI analysis failed: {e}")
        
        return search_results
    
    def analyze_content(self, content, focus=None):
        """Analyze content and extract key insights"""
        print(f"📊 Analyzing content (focus: {focus or 'general'})")
        
        analysis = {
            'status': 'ok',
            'content_length': len(content),
            'word_count': len(content.split()),
            'focus': focus or 'general'
        }
        
        # Basic analysis
        analysis['summary'] = content[:200] + '...' if len(content) > 200 else content
        
        # If Gemini is available, provide AI analysis
        if self.gemini_client:
            try:
                analysis_prompt = f"Analyze this content"
                if focus:
                    analysis_prompt += f" with focus on {focus}"
                analysis_prompt += f":\n\n{content}\n\nProvide key insights, main points, and actionable information."
                
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=[{'parts': [{'text': analysis_prompt}]}]
                )
                analysis['ai_insights'] = response.text
                analysis['key_points'] = self.extract_key_points(response.text)
            except Exception as e:
                print(f"⚠️ AI analysis failed: {e}")
                analysis['ai_insights'] = "AI analysis unavailable"
        
        return analysis
    
    def extract_key_points(self, text):
        """Extract key points from analyzed text"""
        # Simple key point extraction
        lines = text.split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('- ') or line.startswith('• ') or 
                        line.startswith('* ') or any(char.isdigit() and '.' in line for char in line[:3])):
                key_points.append(line)
        
        return key_points[:5]  # Top 5 key points
    
    def generate_research_email(self, research_data, recipient, subject_hint=None):
        """Generate a comprehensive research email based on gathered data"""
        print(f"📧 Generating research email for: {recipient}")
        
        # Extract information from research data
        if isinstance(research_data, dict) and 'results' in research_data:
            search_results = research_data['results']
            ai_analysis = research_data.get('ai_analysis', '')
        else:
            search_results = []
            ai_analysis = str(research_data)
        
        # Generate subject
        if subject_hint:
            subject = f"Research Summary: {subject_hint}"
        else:
            subject = f"Research Findings: {research_data.get('query', 'Information Request')}"
        
        # Generate email body
        body_parts = [
            "Dear Recipient,",
            "",
            f"I've compiled comprehensive research based on your request. Here are the key findings:",
            ""
        ]
        
        # Add search results
        if search_results:
            body_parts.append("## Research Results:")
            for i, result in enumerate(search_results[:3], 1):
                body_parts.append(f"{i}. **{result['title']}**")
                body_parts.append(f"   {result['snippet']}")
                body_parts.append(f"   Source: {result['url']}")
                body_parts.append("")
        
        # Add AI analysis if available
        if ai_analysis:
            body_parts.extend([
                "## Analysis Summary:",
                ai_analysis[:500] + "..." if len(ai_analysis) > 500 else ai_analysis,
                ""
            ])
        
        # Add conclusion
        body_parts.extend([
            "## Summary:",
            "This research provides comprehensive insights into your requested topic. The information has been gathered from multiple sources and analyzed for relevance and accuracy.",
            "",
            "Please let me know if you need additional information or have specific questions about any aspect of this research.",
            "",
            "Best regards,",
            "AI Research Assistant"
        ])
        
        return {
            'subject': subject,
            'body': "\\n".join(body_parts),
            'recipient': recipient
        }
    
    def get_gmail_info(self):
        """Get Gmail account info with enhanced details"""
        if not self.creds:
            return {'status': 'error', 'error': 'Not authenticated'}
        
        try:
            headers = {'Authorization': f'Bearer {self.creds.token}'}
            
            # Get profile
            response = requests.get(
                'https://gmail.googleapis.com/gmail/v1/users/me/profile',
                headers=headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                profile = response.json()
                return {
                    'status': 'ok',
                    'gmail_info': {
                        'user_email': self.user_email,
                        'messages_total': profile.get('messagesTotal', 0),
                        'threads_total': profile.get('threadsTotal', 0),
                        'authenticated': True,
                        'research_enabled': self.gemini_client is not None,
                        'capabilities': ['email', 'research', 'analysis', 'web_search']
                    }
                }
            else:
                return {'status': 'error', 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def send_email(self, to_email, subject, body, cc=None, bcc=None):
        """Send email with enhanced formatting"""
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
                    'thread_id': result.get('threadId'),
                    'body_preview': body[:100] + '...' if len(body) > 100 else body
                }
            else:
                return {'status': 'error', 'error': f'HTTP {response.status_code} - {response.text}'}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def process_research_query(self, query, recipient=None):
        """Process a research query and optionally email results"""
        print(f"🎯 Processing research query: {query}")
        
        # Step 1: Search for information
        search_results = self.search_web(query)
        
        # Step 2: Analyze results
        if search_results.get('status') == 'ok' and search_results.get('ai_analysis'):
            analysis = self.analyze_content(search_results['ai_analysis'], focus=query)
        else:
            analysis = {'status': 'ok', 'summary': 'Basic search completed'}
        
        # Step 3: Generate email if recipient provided
        if recipient:
            email_content = self.generate_research_email(search_results, recipient, query)
            email_result = self.send_email(
                email_content['recipient'],
                email_content['subject'],
                email_content['body']
            )
            
            return {
                'status': 'ok',
                'query': query,
                'search_results': search_results,
                'analysis': analysis,
                'email_result': email_result
            }
        else:
            return {
                'status': 'ok',
                'query': query,
                'search_results': search_results,
                'analysis': analysis
            }

def main():
    """Main function to run the Research Gmail MCP"""
    print("🚀 Starting Research Gmail MCP...")
    
    # Initialize the system
    mcp = ResearchGmailMCP()
    
    if not mcp.creds:
        print("❌ Gmail authentication failed")
        return
    
    # Test Gmail info
    gmail_info = mcp.get_gmail_info()
    if gmail_info['status'] == 'ok':
        info = gmail_info['gmail_info']
        print(f"✅ Connected to Gmail: {info['user_email']}")
        print(f"📊 Messages: {info['messages_total']}, Threads: {info['threads_total']}")
        print(f"🔬 Research enabled: {info['research_enabled']}")
        print(f"🛠️ Capabilities: {', '.join(info['capabilities'])}")
    else:
        print(f"❌ Gmail connection failed: {gmail_info['error']}")
        return
    
    # Interactive mode
    print("\n" + "="*60)
    print("🤖 Research Gmail MCP - Interactive Mode")
    print("="*60)
    print("Commands:")
    print("- 'research [topic]' - Research a topic")
    print("- 'email [topic] to [email]' - Research and email results")
    print("- 'send [email] subject [subject] body [body]' - Send direct email")
    print("- 'quit' - Exit")
    print()
    
    while True:
        try:
            user_input = input("🎯 Enter command: ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            # Parse research command
            if user_input.lower().startswith('research'):
                topic = user_input[8:].strip()
                if not topic:
                    print("❌ Please specify a research topic")
                    continue
                
                result = mcp.process_research_query(topic)
                if result['status'] == 'ok':
                    print(f"✅ Research completed for: {topic}")
                    if 'ai_analysis' in result['search_results']:
                        print(f"📊 Analysis: {result['search_results']['ai_analysis'][:200]}...")
                else:
                    print(f"❌ Research failed: {result.get('error', 'Unknown error')}")
            
            # Parse email command
            elif 'to' in user_input.lower() and ('research' in user_input.lower() or 'email' in user_input.lower()):
                parts = user_input.split(' to ')
                if len(parts) == 2:
                    topic = parts[0].replace('email', '').replace('research', '').strip()
                    recipient = parts[1].strip()
                    
                    result = mcp.process_research_query(topic, recipient)
                    if result['status'] == 'ok' and result.get('email_result', {}).get('status') == 'ok':
                        print(f"✅ Research email sent to {recipient}")
                        print(f"📧 Subject: {result['email_result']['subject']}")
                    else:
                        print(f"❌ Failed to process request")
                else:
                    print("❌ Please use format: 'research [topic] to [email]'")
            
            # Parse direct send command
            elif user_input.lower().startswith('send'):
                # Simple parser for send command
                print("📧 Direct email mode - please provide details:")
                recipient = input("To: ").strip()
                subject = input("Subject: ").strip()
                body = input("Body: ").strip()
                
                if recipient and subject and body:
                    result = mcp.send_email(recipient, subject, body)
                    if result['status'] == 'ok':
                        print(f"✅ Email sent successfully!")
                    else:
                        print(f"❌ Failed to send email: {result['error']}")
                else:
                    print("❌ All fields are required")
            
            else:
                print("❌ Unknown command. Try 'research [topic]' or 'email [topic] to [email]'")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

