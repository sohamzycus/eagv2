import time, logging, os
from functools import wraps
from typing import Callable, Any

LOG_FILE = os.path.join(os.path.dirname(__file__), 'mcp_agent.log')

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def log_and_time(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('mcp')
        start = time.time()
        logger.info('CALL %s args=%s kwargs=%s', func.__name__, args, kwargs)
        try:
            res = func(*args, **kwargs)
            elapsed = time.time() - start
            logger.info('RETURN %s elapsed=%.6f', func.__name__, elapsed)
            return res
        except Exception as e:
            elapsed = time.time() - start
            logger.exception('EXCEPTION in %s after %.6f sec: %s', func.__name__, elapsed, str(e))
            raise
    return wrapper
