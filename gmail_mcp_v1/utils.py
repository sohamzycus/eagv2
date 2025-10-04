# utils.py - logging and timing utilities
import logging, time
from functools import wraps
from typing import Callable, Any

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('gmail_agent.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    # Fix Windows console encoding for emojis
    import sys
    if sys.platform == 'win32':
        try:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        except:
            pass

def log_and_time(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger = logging.getLogger(func.__module__)
        logger.info(f'CALL {func.__name__} args={args} kwargs={kwargs}')
        try:
            res = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f'RETURN {func.__name__} elapsed={elapsed:.6f}')
            return res
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f'EXCEPTION in {func.__name__} after {elapsed:.6f} sec: {e}')
            raise
    return wrapper
