"""mcp_server.py - Flask MCP server with Gmail API integration"""
import time, logging, argparse, json, os
from flask import Flask, request, jsonify
from utils import setup_logging, log_and_time
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
    creds = None
    # Token file stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use credentials.json if available, otherwise use environment variables
            if os.path.exists('credentials.json'):
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            else:
                # Fallback: create credentials from environment variables
                client_config = {
                    "web": {
                        "client_id": os.environ.get('GOOGLE_CLIENT_ID', ''),
                        "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET', ''),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost:8080/callback"]
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            
            creds = flow.run_local_server(port=8080)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

def _get_gmail_service():
    """Get authenticated Gmail service"""
    if STATE['gmail_service'] is None:
        try:
            creds = _authenticate_gmail()
            STATE['credentials'] = creds
            STATE['gmail_service'] = build('gmail', 'v1', credentials=creds)
            
            # Get user email
            user_service = build('oauth2', 'v2', credentials=creds)
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
    """Get Gmail account information"""
    if not GMAIL_AVAILABLE:
        return jsonify({'status':'error','error':'Gmail dependencies not available','details':str(_IMPORT_ERR)}), 500
    
    try:
        service = _get_gmail_service()
        if not service:
            return jsonify({'status':'error','error':'Gmail authentication failed'}), 500
        
        # Get profile information
        profile = service.users().getProfile(userId='me').execute()
        
        info = {
            'user_email': STATE['user_email'],
            'messages_total': profile.get('messagesTotal', 0),
            'threads_total': profile.get('threadsTotal', 0),
            'history_id': profile.get('historyId', ''),
            'authenticated': True
        }
        
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
        service = _get_gmail_service()
        if not service:
            return jsonify({'status':'error','error':'Gmail authentication failed'}), 500
        
        # Create message
        message = MIMEMultipart()
        message['to'] = to_email
        message['subject'] = subject
        message['from'] = STATE['user_email']
        
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
        
        # Add body
        message.attach(MIMEText(body, 'plain'))
        
        # Convert to base64
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Send email
        send_result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        logger.info(f'Email sent successfully to {to_email}. Message ID: {send_result.get("id")}')
        
        return jsonify({
            'status': 'ok',
            'message_id': send_result.get('id'),
            'to': to_email,
            'subject': subject,
            'from': STATE['user_email'],
            'thread_id': send_result.get('threadId')
        })
        
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
