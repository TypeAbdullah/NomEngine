"""
Structured JSON Logging Module
Outputs machine-readable, structured JSON logs without sensitive data leaks.
"""
import json
import logging
import sys
import time
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include custom extra fields if provided
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            # Sanitize sensitive fields
            sanitized = {}
            for k, v in record.extra_data.items():
                if any(secret in k.lower() for secret in ["pass", "token", "secret", "auth", "key"]):
                    sanitized[k] = "[REDACTED]"
                else:
                    sanitized[k] = v
            log_obj["data"] = sanitized

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, ensure_ascii=False)


def setup_logger(name: str = "nomengine", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a structured JSON logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = setup_logger()


def log_event(event_name: str, **kwargs):
    """Helper to emit structured event logs."""
    record = logger.makeRecord(
        logger.name, logging.INFO, "", 0, f"Event: {event_name}", (), None
    )
    record.extra_data = {"event": event_name, **kwargs}
    logger.handle(record)
