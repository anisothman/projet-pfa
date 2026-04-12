import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Dossier logs à la racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"

def setup_logger(name: str = "projet-pfa") -> logging.Logger:
    """Configure et retourne un logger"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)8s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    log_filename = LOGS_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

_LOGGER_CACHE = {}

def get_logger(name: str = "projet-pfa") -> logging.Logger:
    """Retourne un logger mis en cache"""
    if name not in _LOGGER_CACHE:
        _LOGGER_CACHE[name] = setup_logger(name)
    return _LOGGER_CACHE[name]

# Logger par défaut
logger = get_logger("projet-pfa")