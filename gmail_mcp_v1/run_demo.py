# run_demo.py - start server thread and run Gmail agent
import threading, time, logging
from utils import setup_logging
setup_logging()
logger = logging.getLogger('run_demo')

def start_server():
    import mcp_server
    mcp_server.main()

def start_agent():
    import agent, time
    time.sleep(1.5)
    agent.run_agent(
        'Send an email to demo@example.com with subject "AI Test Email" and message "Hello! This is a test email sent by an AI agent using Gmail API."', 
        'http://127.0.0.1:5001', 
        'gmail_session.json'
    )

if __name__ == '__main__':
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    start_agent()
    logger.info('Demo finished. Check gmail_session.json and gmail_agent.log')
