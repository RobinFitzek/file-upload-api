"""
Logging-Konfiguration für die Geodata File Upload API.
"""
import logging
import sys
import os
from typing import Optional

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """
    Konfiguriert das Logging für die Anwendung.
    
    Args:
        level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Falls nicht angegeben, wird LOG_LEVEL aus Umgebungsvariable gelesen
    
    Returns:
        Root-Logger der Anwendung
    """
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")
    
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Uvicorn-Logger weniger verbose
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # SQLAlchemy nur Warnungen
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logger = logging.getLogger("geodata-api")
    logger.info("Logging initialisiert")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Holt einen Logger für ein spezifisches Modul.
    
    Args:
        name: Name des Moduls (z.B. __name__)
    
    Returns:
        Logger-Instanz
    """
    return logging.getLogger(f"geodata-api.{name}")
