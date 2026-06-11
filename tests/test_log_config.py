import logging
import json
import sys
from log_config import JSONFormatter, setup_logging
import pytest
from datetime import datetime

def test_json_formatter():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=10,
        msg="Test error message",
        args=(),
        exc_info=None
    )
    
    formatted_output = formatter.format(record)
    log_data = json.loads(formatted_output)
    
    assert log_data["level"] == "ERROR"
    assert log_data["logger"] == "test_logger"
    assert log_data["message"] == "Test error message"
    assert "timestamp" in log_data
    assert "exc_info" not in log_data

def test_json_formatter_with_exc_info():
    formatter = JSONFormatter()
    try:
        1 / 0
    except ZeroDivisionError:
        exc_info = sys.exc_info()
        
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=10,
        msg="Division by zero error",
        args=(),
        exc_info=exc_info
    )
    
    formatted_output = formatter.format(record)
    log_data = json.loads(formatted_output)
    
    assert log_data["message"] == "Division by zero error"
    assert "exc_info" in log_data
    assert "ZeroDivisionError" in log_data["exc_info"]

def test_setup_logging():
    # Store old handlers to restore later if needed
    logger = logging.getLogger()
    old_handlers = logger.handlers[:]
    
    setup_logging(level=logging.DEBUG)
    
    assert logger.level == logging.DEBUG
    # Make sure we added our handler, but don't count on it being the only one 
    # since pytest adds its own log capture handlers
    has_our_handler = False
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and isinstance(handler.formatter, JSONFormatter):
            has_our_handler = True
            break
            
    assert has_our_handler
    
    # Restore original state
    logger.handlers = old_handlers
