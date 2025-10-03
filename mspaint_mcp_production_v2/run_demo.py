# run_demo.py - start server thread and run agent
import threading, time, logging
from utils import setup_logging
setup_logging()
logger = logging.getLogger('run_demo')

def start_server():
    import mcp_server
    mcp_server.main()

def start_agent():
    import agent, time
    time.sleep(1.2)
    agent.run_agent('What are you doing? Learning that prompting really is the key!', 'http://127.0.0.1:5000', 'llm_session.json')

if __name__ == '__main__':
    t = threading.Thread(target=start_server, daemon=True); t.start()
    start_agent()
    logger.info('Demo finished. Check llm_session.json and mcp_agent.log')
