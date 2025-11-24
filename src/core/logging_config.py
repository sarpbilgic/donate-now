import logging
import sys
import json
from typing import Any

class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def configure_logging() -> None:
    """
    Configures the root logger to output JSON to stdout.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    if root_logger.handlers:
        root_logger.handlers = []
        
    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Set lower log level for some verbose libraries if needed
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("stripe").setLevel(logging.WARNING)
