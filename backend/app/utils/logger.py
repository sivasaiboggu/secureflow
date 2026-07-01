import logging
import sys
import json
from datetime import datetime
from app.config.settings import settings

class JSONFormatter(logging.Formatter):
    """Formats log records as JSON objects for centralized logging (ELK)"""
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def setup_logging():
    """Initializes standard or JSON logging based on configuration settings"""
    root_logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = sys.stdout
    if settings.LOG_FORMAT.lower() == "json":
        log_handler = logging.StreamHandler(handler)
        log_handler.setFormatter(JSONFormatter())
    else:
        log_handler = logging.StreamHandler(handler)
        log_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s (%(filename)s:%(lineno)d): %(message)s'
        )
        log_handler.setFormatter(log_formatter)
        
    root_logger.addHandler(log_handler)
    
    # Set logging level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Suppress verbose third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
