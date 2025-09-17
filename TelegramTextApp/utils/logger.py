import logging
import os
import sys
from pathlib import Path
from .. import config

def setup(name=""):
    DEBUG = config.DEBUG
    log_path = config.LOG_PATH

    logger = logging.getLogger(name)
    logger.handlers.clear()
    
    log_level = logging.DEBUG if DEBUG else logging.INFO
    logger.setLevel(log_level)
    
    if name:
        formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    else:
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    
    if not DEBUG:
        if not name:
            filename = "application.log"
        else:
            filename = f"{name}.log"
        
        if log_path:
            os.makedirs(log_path, exist_ok=True)
            log_file = os.path.join(log_path, filename)
        else:
            log_file = filename
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        logger.debug("Режим отладки активирован. Логи выводятся в консоль")
    
    return logger