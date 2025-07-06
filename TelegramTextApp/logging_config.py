import logging
import sys
from pathlib import Path
import os

def setup_logging(DEBUG=False):
    logger = logging.getLogger("TelegramTextApp")
    
    logger.handlers.clear()
    
    log_level = logging.DEBUG if DEBUG == True else logging.INFO
    logger.setLevel(log_level)
    
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    
    if DEBUG == False:
        LOG_FILE = os.path.join("bot.log")
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger