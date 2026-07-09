# app/logger.py
import logging
import sys
from datetime import datetime
import os

# Crear carpeta de logs si no existe
os.makedirs("logs", exist_ok=True)

def setup_logger():
    logger = logging.getLogger("agencia_api")
    logger.setLevel(logging.INFO)
    
    # Formato para archivo
    file_handler = logging.FileHandler("logs/app.log")
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Formato para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s - %(message)s'
    ))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()