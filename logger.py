import logging
import os
from datetime import datetime

def setup_logger():
    logger = logging.getLogger("Spotify Agent")
    logger.setLevel(logging.DEBUG)
    
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # File handler
    fh = logging.FileHandler(f"logs/{datetime.now().strftime('%Y-%m-%d')}.log")
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    
    # Format
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    # Aff handlers
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger