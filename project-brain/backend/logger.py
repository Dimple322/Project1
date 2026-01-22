import logging
import sys
from config import settings

LOG_LEVEL = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

# Configure root logger
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
