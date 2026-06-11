import logging
import json
import sys
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    """
    def format(self, record: logging.LogRecord) -> str:
        """
        Formats a log record as a JSON string.
        
        Args:
            record (logging.LogRecord): The log record to format.
            
        Returns:
            str: The JSON formatted log string.
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def setup_logging(level=logging.INFO):
    """
    Sets up structured JSON logging to stderr for the root logger.
    
    Args:
        level: The logging level to set (default: logging.INFO).
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and isinstance(handler.formatter, JSONFormatter):
            return
            
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
