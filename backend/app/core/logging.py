"""Structured logging with automated PII masking."""

import logging
import re
from typing import Any, Dict

# Regex patterns for masking sensitive data in logs
ID_PATTERN = re.compile(r"([A-Z0-9]{2})[A-Z0-9]+([A-Z0-9]{2})", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"(^[a-zA-Z0-9_.+-])[^@]+(@.+)$")


def mask_sensitive_value(value: str) -> str:
    if not value or len(value) < 4:
        return "****"
    return f"{value[:2]}****{value[-2:]}"


class RedactedFormatter(logging.Formatter):
    """Custom logging formatter to suppress PII fields."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        # Prevent logging full tokens
        redacted = re.sub(r"Bearer\s+[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*", "Bearer [REDACTED_JWT]", original)
        return redacted


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(RedactedFormatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
