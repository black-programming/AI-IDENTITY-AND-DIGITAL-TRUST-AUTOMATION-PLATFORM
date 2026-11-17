"""Structured logging with automated PII masking and asynchronous correlation IDs."""

import contextvars
from datetime import datetime, timezone
import json
import logging
import re
from typing import Any, Dict, Optional

# Context variable preserving request correlation ID across async coroutine boundaries
current_request_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_request_id", default=None)

# Redaction patterns for sensitive PII and secrets
JWT_PATTERN = re.compile(r"Bearer\s+[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*", re.IGNORECASE)
PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----[\s\S]+?-----END\s+(?:RSA\s+)?PRIVATE\s+KEY-----", re.IGNORECASE)
PASSWORD_JSON_PATTERN = re.compile(r'("(?:password|secret|token|api_key|service_role_key)":\s*")[^"]+(")', re.IGNORECASE)
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")
ID_PATTERN = re.compile(r"([A-Z0-9]{2})[A-Z0-9]+([A-Z0-9]{2})", re.IGNORECASE)


def sanitize_log_message(msg: str) -> str:
    """Scrub sensitive credentials, private keys, passwords, and PII from log messages."""
    if not isinstance(msg, str):
        msg = str(msg)

    # 1. Redact JWT tokens
    msg = JWT_PATTERN.sub("Bearer [REDACTED_JWT]", msg)

    # 2. Redact Private Keys
    msg = PRIVATE_KEY_PATTERN.sub("[REDACTED_PRIVATE_KEY]", msg)

    # 3. Redact JSON password / secret fields
    msg = PASSWORD_JSON_PATTERN.sub(r"\1***REDACTED***\2", msg)

    # 4. Mask credit card numbers
    msg = CREDIT_CARD_PATTERN.sub("****-****-****-****", msg)

    return msg


def set_request_id(req_id: str) -> None:
    """Bind a correlation request ID to the current async context."""
    current_request_id.set(req_id)


def get_request_id() -> Optional[str]:
    """Retrieve the correlation request ID bound to the current async context."""
    return current_request_id.get()


class StructuredJsonFormatter(logging.Formatter):
    """Custom formatter emitting sanitized, structured JSON logs with correlation metadata."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = get_request_id() or getattr(record, "request_id", None) or "N/A"
        clean_msg = sanitize_log_message(record.getMessage())

        log_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": req_id,
            "message": clean_msg,
        }

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


class RedactedTextFormatter(logging.Formatter):
    """Human-readable text formatter for terminal output with correlation ID and secret scrubbing."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = get_request_id() or getattr(record, "request_id", None) or "-"
        clean_msg = sanitize_log_message(record.getMessage())
        time_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        return f"[{time_str}] [{record.levelname:<5}] [{record.name}] [req:{req_id}]: {clean_msg}"


def get_logger(name: str) -> logging.Logger:
    """Get or configure an application logger with redaction and request correlation."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(RedactedTextFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
