"""mcp_server.py - Flask MCP server with Gmail API integration"""
import time, logging, argparse, json, os
from flask import Flask, request, jsonify
from utils import setup_logging, log_and_time

# GLOBAL SSL FIX for Windows - Apply immediately
import ssl
import urllib3

try:
    # Disable SSL warnings globally
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Set environment variables to disable SSL verification
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    os.environ['CURL_CA_BUNDLE'] = ''
    
    # Create unverified SSL context and make it the default
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    ssl._create_default_https_context = lambda: ssl_context
    print("🔧 Global SSL verification disabled for Windows compatibility")
except Exception as e:
    print(f"⚠️ Could not disable SSL globally: {e}")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system environment variables

setup_logging()
logger = logging.getLogger('gmail_mcp_server')

try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    import ssl
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import base64
    GMAIL_AVAILABLE = True
except Exception as e:
    GMAIL_AVAILABLE = False
    _IMPORT_ERR = e

app = Flask(__name__)
STATE = {'gmail_service': None, 'user_email': None, 'credentials': None}

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 
          'https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/userinfo.email']

def _authenticate_gmail():
    """Authenticate with Gmail API using OAuth2"""
    logger.info("Starting Gmail authentication process...")
    creds = None
    # Token file stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        logger.info("Found existing token.json, loading credentials...")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials...")
                try:
                    creds.refresh(Request())
                    logger.info("Credentials refreshed successfully")
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    # Delete invalid token and start fresh
                    if os.path.exists('token.json'):
                        os.remove('token.json')
                    creds = None
        
        if not creds or not creds.valid:
            logger.info("Starting OAuth2 flow...")
            # Use credentials.json if available, otherwise use environment variables
            if os.path.exists('credentials.json'):
                logger.info("Using credentials.json for OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            else:
                logger.info("Using environment variables for OAuth flow")
                # Fallback: create credentials from environment variables
                client_config = {
                    "installed": {
                        "client_id": os.environ.get('GOOGLE_CLIENT_ID', ''),
                        "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET', ''),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost:8080/", "http://localhost:8081/", "http://localhost:8082/", "urn:ietf:wg:oauth:2.0:oob"]
                    }
                }
                if not client_config["installed"]["client_id"]:
                    raise Exception("No credentials.json found and no GOOGLE_CLIENT_ID environment variable set")
                
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            
            logger.info("Opening browser for OAuth consent...")
            logger.info("Please complete authentication in your browser...")
            logger.info("After authorization, you may see a 'page not found' - this is normal!")
            try:
                # Use standard OAuth ports that are pre-configured in Google Cloud Console
                oauth_ports = [8080, 8081, 8082]
                creds = None
                
                for port in oauth_ports:
                    try:
                        logger.info(f"Trying OAuth on port {port}...")
                        creds = flow.run_local_server(
                            port=port,
                            timeout_seconds=300,  # 5 minute timeout
                            open_browser=True,
                            success_message='Authentication successful! You can close this window and return to your application.'
                        )
                        logger.info(f"OAuth flow completed successfully on port {port}")
                        break
                    except OSError as e:
                        if "Address already in use" in str(e) or "10048" in str(e):
                            logger.warning(f"Port {port} in use, trying next port...")
                            continue
                        else:
                            raise e
                
                if not creds:
                    raise Exception("All OAuth ports (8080-8082) are in use")
            except Exception as e:
                logger.error(f"OAuth flow failed: {e}")
                logger.info("If you see '404 path not found' in browser, that's normal - check if authentication completed in console")
                raise Exception(f"Gmail authentication failed: {e}")
        
        # Save the credentials for the next run
        try:
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            logger.info("Saved authentication tokens to token.json")
        except Exception as e:
            logger.warning(f"Could not save token.json: {e}")
    
    logger.info("Gmail authentication completed successfully")
    return creds

def _get_gmail_service():
    """Get authenticated Gmail service"""
    if STATE['gmail_service'] is None:
        try:
            creds = _authenticate_gmail()
            STATE['credentials'] = creds
            
            # AGGRESSIVE SSL FIX for Windows - Force disable SSL verification
            logger.info("🔧 Applying aggressive SSL fix for Windows...")
            
            try:
                # Method 1: Complete SSL bypass with httplib2
                import httplib2
                import urllib3
                import ssl
                import os
                
                # Disable all SSL warnings
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                # Set environment variable to disable SSL verification
                os.environ['PYTHONHTTPSVERIFY'] = '0'
                
                # Create httplib2 Http object with SSL verification completely disabled
                http = httplib2.Http(
                    disable_ssl_certificate_validation=True,
                    ca_certs=None
                )
                
                STATE['gmail_service'] = build('gmail', 'v1', credentials=creds, http=http)
                user_service = build('oauth2', 'v2', credentials=creds, http=http)
                logger.info("✅ Gmail service created with COMPLETE SSL bypass")
                
            except Exception as ssl_error:
                logger.warning(f"httplib2 SSL bypass failed: {ssl_error}")
                
                try:
                    # Method 2: Monkey patch SSL context globally
                    import ssl
                    import urllib3
                    
                    # Disable SSL warnings
                    urllib3.disable_warnings()
                    
                    # Create unverified SSL context and make it default
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    
                    # Monkey patch the default SSL context
                    ssl._create_default_https_context = lambda: ssl_context
                    
                    STATE['gmail_service'] = build('gmail', 'v1', credentials=creds)
                    user_service = build('oauth2', 'v2', credentials=creds)
                    logger.info("✅ Gmail service created with monkey-patched SSL context")
                    
                except Exception as e:
                    logger.error(f"Monkey patch SSL fix failed: {e}")
                    
                    try:
                        # Method 3: Use requests with session and SSL disabled
                        import requests
                        from googleapiclient.http import HttpRequest
                        from googleapiclient.discovery import build
                        
                        # Create a session with SSL verification disabled
                        session = requests.Session()
                        session.verify = False
                        
                        # Disable SSL warnings for requests
                        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                        
                        # Try to build service with default method but SSL globally disabled
                        STATE['gmail_service'] = build('gmail', 'v1', credentials=creds)
                        user_service = build('oauth2', 'v2', credentials=creds)
                        logger.info("⚠️ Gmail service created with global SSL disabled")
                        
                    except Exception as final_error:
                        logger.error(f"ALL SSL fix methods failed: {final_error}")
                        raise Exception(f"Cannot create Gmail service due to SSL issues: {final_error}")
            
            # Get user email
            user_info = user_service.userinfo().get().execute()
            STATE['user_email'] = user_info.get('email')
            
            logger.info(f'Gmail service authenticated for: {STATE["user_email"]}')
        except Exception as e:
            logger.error(f'Gmail authentication failed: {e}')
            return None
    
    return STATE['gmail_service']

@app.route('/tool/get_gmail_info', methods=['POST'])
@log_and_time
def http_get_gmail_info():
    """Get Gmail account information using direct API"""
    if not GMAIL_AVAILABLE:
        return jsonify({'status':'error','error':'Gmail dependencies not available','details':str(_IMPORT_ERR)}), 500
    
    try:
        # Load credentials directly
        creds = _authenticate_gmail()
        if not creds:
            return jsonify({'status':'error','error':'Gmail authentication failed'}), 500
        
        # Use direct API calls with SSL disabled
        import requests
        headers = {'Authorization': f'Bearer {creds.token}'}
        
        # Get user info
        user_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers=headers,
            verify=False,
            timeout=30
        )
        
        if user_response.status_code != 200:
            return jsonify({'status':'error','error':f'Failed to get user info: {user_response.status_code}'}), 500
        
        user_info = user_response.json()
        user_email = user_info.get('email', 'unknown')
        
        # Get Gmail profile
        profile_response = requests.get(
            'https://gmail.googleapis.com/gmail/v1/users/me/profile',
            headers=headers,
            verify=False,
            timeout=30
        )
        
        if profile_response.status_code == 200:
            profile = profile_response.json()
            messages_total = profile.get('messagesTotal', 0)
            threads_total = profile.get('threadsTotal', 0)
            history_id = profile.get('historyId', '')
        else:
            messages_total = 0
            threads_total = 0
            history_id = ''
        
        info = {
            'user_email': user_email,
            'messages_total': messages_total,
            'threads_total': threads_total,
            'history_id': history_id,
            'authenticated': True
        }
        
        logger.info(f'✅ Gmail info retrieved for: {user_email}')
        return jsonify({'status':'ok', 'gmail_info': info})
        
    except Exception as e:
        logger.exception('get_gmail_info failed')
        return jsonify({'status':'error','error': str(e)}), 500

@app.route('/tool/send_email', methods=['POST'])
@log_and_time
def http_send_email():
    """Send an email via Gmail API"""
    if not GMAIL_AVAILABLE:
        return jsonify({'status':'error','error':'Gmail dependencies not available'}), 500
    
    data = request.get_json(force=True) or {}
    to_email = data.get('to', '')
    subject = data.get('subject', 'Email from AI Agent')
    body = data.get('body', '')
    cc = data.get('cc', '')
    bcc = data.get('bcc', '')
    
    if not to_email:
        return jsonify({'status':'error','error':'Recipient email address required'}), 400
    
    try:
        # Load credentials directly
        creds = _authenticate_gmail()
        if not creds:
            return jsonify({'status':'error','error':'Gmail authentication failed'}), 500
        
        # Get user email first
        import requests
        headers = {'Authorization': f'Bearer {creds.token}'}
        
        user_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers=headers,
            verify=False,
            timeout=30
        )
        
        if user_response.status_code == 200:
            user_email = user_response.json().get('email', 'unknown')
        else:
            user_email = 'unknown'
        
        # Create message using direct approach
        from email.mime.text import MIMEText
        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject
        message['from'] = user_email
        
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
        
        # Convert to base64
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Send email using direct API call
        send_data = {'raw': raw_message}
        
        send_response = requests.post(
            'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
            headers={
                'Authorization': f'Bearer {creds.token}',
                'Content-Type': 'application/json'
            },
            json=send_data,
            verify=False,
            timeout=60
        )
        
        if send_response.status_code == 200:
            send_result = send_response.json()
            logger.info(f'✅ Email sent successfully to {to_email}. Message ID: {send_result.get("id")}')
            
            return jsonify({
                'status': 'ok',
                'message_id': send_result.get('id'),
                'to': to_email,
                'subject': subject,
                'from': user_email,
                'thread_id': send_result.get('threadId')
            })
        else:
            error_msg = f'Failed to send email: HTTP {send_response.status_code} - {send_response.text}'
            logger.error(error_msg)
            return jsonify({'status':'error','error': error_msg}), 500
        
    except Exception as e:
        logger.exception('send_email failed')
        return jsonify({'status':'error','error': str(e)}), 500

@app.route('/tool/compose_email', methods=['POST'])
@log_and_time
def http_compose_email():
    """Compose and save an email draft"""
    if not GMAIL_AVAILABLE:
        return jsonify({'status':'error','error':'Gmail dependencies not available'}), 500
    
    data = request.get_json(force=True) or {}
    to_email = data.get('to', '')
    subject = data.get('subject', 'Draft from AI Agent')
    body = data.get('body', '')
    
    try:
        service = _get_gmail_service()
        if not service:
            return jsonify({'status':'error','error':'Gmail authentication failed'}), 500
        
        # Create message
        message = MIMEMultipart()
        message['to'] = to_email
        message['subject'] = subject
        message['from'] = STATE['user_email']
        message.attach(MIMEText(body, 'plain'))
        
        # Convert to base64
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Create draft
        draft_result = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw_message}}
        ).execute()
        
        logger.info(f'Draft created successfully. Draft ID: {draft_result.get("id")}')
        
        return jsonify({
            'status': 'ok',
            'draft_id': draft_result.get('id'),
            'message_id': draft_result.get('message', {}).get('id'),
            'to': to_email,
            'subject': subject
        })
        
    except Exception as e:
        logger.exception('compose_email failed')
        return jsonify({'status':'error','error': str(e)}), 500

@app.route('/tool/list_recent_emails', methods=['POST'])
@log_and_time
def http_list_recent_emails():
    """List recent emails"""
    if not GMAIL_AVAILABLE:
        return jsonify({'status':'error','error':'Gmail dependencies not available'}), 500
    
    data = request.get_json(force=True) or {}
    max_results = min(int(data.get('max_results', 10)), 50)  # Limit to 50
    
    try:
        service = _get_gmail_service()
        if not service:
            return jsonify({'status':'error','error':'Gmail authentication failed'}), 500
        
        # Get list of messages
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        email_list = []
        
        for msg in messages[:max_results]:
            # Get message details
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = message.get('payload', {}).get('headers', [])
            email_info = {'id': msg['id']}
            
            for header in headers:
                name = header.get('name', '').lower()
                if name == 'from':
                    email_info['from'] = header.get('value', '')
                elif name == 'subject':
                    email_info['subject'] = header.get('value', '')
                elif name == 'date':
                    email_info['date'] = header.get('value', '')
            
            email_list.append(email_info)
        
        return jsonify({
            'status': 'ok',
            'emails': email_list,
            'count': len(email_list)
        })
        
    except Exception as e:
        logger.exception('list_recent_emails failed')
        return jsonify({'status':'error','error': str(e)}), 500

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=5001)  # Different port from Paint version
    args = parser.parse_args()
    
    logger.info('Starting Gmail MCP server on %s:%d', args.host, args.port)
    
    if not GMAIL_AVAILABLE:
        logger.error('Gmail dependencies not available: %s', _IMPORT_ERR)
        logger.error('Please install: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client')
    
    app.run(host=args.host, port=args.port, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
