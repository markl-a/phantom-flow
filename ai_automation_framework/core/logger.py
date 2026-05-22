"""Logging utilities for the AI Automation Framework."""

import sys
import os
import json
import time
import uuid
import re
from pathlib import Path
from typing import Optional, Any, Dict, Callable
from contextvars import ContextVar
from contextlib import contextmanager
from functools import wraps
from loguru import logger
from ai_automation_framework.core.config import get_config


# Context variable for correlation ID tracking
_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


class SensitiveDataFilter:
    """
    Filter to mask sensitive data in log messages.

    This filter protects against accidental logging of:
    - API keys and tokens
    - Passwords and secrets
    - Credit card numbers
    - Email addresses (optional)
    - IP addresses (optional)
    - JWT tokens
    - Bearer tokens
    """

    # Regex patterns for sensitive data detection
    PATTERNS = {
        # API Keys and Tokens (common patterns)
        'api_key': [
            r'api[_-]?key[\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            r'apikey[\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            r'key[\s:=]+["\']?([a-zA-Z0-9_\-]{32,})["\']?',
        ],
        # Passwords
        'password': [
            r'password[\s:=]+["\']?([^\s"\']{8,})["\']?',
            r'passwd[\s:=]+["\']?([^\s"\']{8,})["\']?',
            r'pwd[\s:=]+["\']?([^\s"\']{8,})["\']?',
        ],
        # Secrets and tokens
        'secret': [
            r'secret[\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            r'token[\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            r'auth[\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        ],
        # Bearer tokens
        'bearer': [
            r'Bearer\s+([a-zA-Z0-9_\-\.]+)',
            r'bearer[\s:=]+["\']?([a-zA-Z0-9_\-\.]+)["\']?',
        ],
        # JWT tokens (rough pattern)
        'jwt': [
            r'eyJ[a-zA-Z0-9_\-]*\.eyJ[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*',
        ],
        # AWS keys
        'aws_key': [
            r'AKIA[0-9A-Z]{16}',  # AWS Access Key ID
            r'aws_secret_access_key[\s:=]+["\']?([a-zA-Z0-9/+=]{40})["\']?',
        ],
        # Credit card numbers (basic pattern)
        'credit_card': [
            r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b',
        ],
        # Email addresses (optional - may mask legitimate non-sensitive emails)
        'email': [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        ],
        # Generic secrets in environment variable format
        'env_secret': [
            r'[A-Z_]+_(KEY|SECRET|TOKEN|PASSWORD)[\s:=]+["\']?([^\s"\']+)["\']?',
        ],
    }

    # Replacement text for masked data
    MASK_TEXT = {
        'api_key': '***API_KEY***',
        'password': '***PASSWORD***',
        'secret': '***SECRET***',
        'bearer': 'Bearer ***TOKEN***',
        'jwt': '***JWT_TOKEN***',
        'aws_key': '***AWS_KEY***',
        'credit_card': '****-****-****-****',
        'email': '***EMAIL***',
        'env_secret': '***SECRET***',
    }

    def __init__(self, mask_emails: bool = False, custom_patterns: Dict[str, str] = None):
        """
        Initialize the sensitive data filter.

        Args:
            mask_emails: Whether to mask email addresses (default: False)
            custom_patterns: Additional patterns to mask {name: regex_pattern}
        """
        self.mask_emails = mask_emails
        self.custom_patterns = custom_patterns or {}

        # Compile regex patterns for performance
        self.compiled_patterns = {}
        for category, patterns in self.PATTERNS.items():
            # Skip email masking if not enabled
            if category == 'email' and not mask_emails:
                continue

            self.compiled_patterns[category] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

        # Add custom patterns
        for name, pattern in self.custom_patterns.items():
            self.compiled_patterns[f'custom_{name}'] = [
                re.compile(pattern, re.IGNORECASE)
            ]

    def filter(self, message: str) -> str:
        """
        Filter and mask sensitive data in a log message.

        Args:
            message: Original log message

        Returns:
            Filtered message with sensitive data masked
        """
        if not message:
            return message

        filtered_message = message

        # Apply each pattern category
        for category, patterns in self.compiled_patterns.items():
            mask_text = self.MASK_TEXT.get(category, '***REDACTED***')

            for pattern in patterns:
                # Replace sensitive data with mask
                filtered_message = pattern.sub(mask_text, filtered_message)

        return filtered_message

    def filter_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter sensitive data in a dictionary (recursive).

        Args:
            data: Dictionary potentially containing sensitive data

        Returns:
            Filtered dictionary with sensitive values masked
        """
        if not isinstance(data, dict):
            return data

        filtered = {}
        sensitive_keys = {
            'password', 'passwd', 'pwd', 'secret', 'token', 'api_key',
            'apikey', 'key', 'auth', 'authorization', 'bearer', 'credentials'
        }

        for key, value in data.items():
            # Check if key indicates sensitive data
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                filtered[key] = '***REDACTED***'
            elif isinstance(value, dict):
                # Recursively filter nested dictionaries
                filtered[key] = self.filter_dict(value)
            elif isinstance(value, str):
                # Filter string values
                filtered[key] = self.filter(value)
            elif isinstance(value, list):
                # Filter list items
                filtered[key] = [
                    self.filter(item) if isinstance(item, str)
                    else self.filter_dict(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                filtered[key] = value

        return filtered


# Global sensitive data filter instance
_sensitive_filter = SensitiveDataFilter(mask_emails=False)


def _json_serializer(record: Dict[str, Any]) -> str:
    """
    Serialize log record to JSON format with sensitive data filtering.

    Args:
        record: Log record dictionary

    Returns:
        JSON formatted string with sensitive data masked
    """
    # Extract correlation ID if available
    correlation_id = _correlation_id.get()

    # Filter sensitive data from message
    filtered_message = _sensitive_filter.filter(record["message"])

    # Build structured log entry
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "logger": record["name"],
        "function": record["function"],
        "line": record["line"],
        "message": filtered_message,
    }

    # Add correlation ID if present
    if correlation_id:
        log_entry["correlation_id"] = correlation_id

    # Add extra fields from record (with filtering)
    if "extra" in record and record["extra"]:
        log_entry["extra"] = _sensitive_filter.filter_dict(record["extra"])

    # Add exception info if present
    if record["exception"]:
        exception_value = str(record["exception"].value) if record["exception"].value else None
        # Filter sensitive data from exception messages
        if exception_value:
            exception_value = _sensitive_filter.filter(exception_value)

        log_entry["exception"] = {
            "type": record["exception"].type.__name__ if record["exception"].type else None,
            "value": exception_value,
        }

    return json.dumps(log_entry)


def setup_logger(
    log_file: Optional[str] = None,
    log_level: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "1 week",
    use_json: bool = False,
) -> None:
    """
    Setup logger with file and console output.

    Args:
        log_file: Path to log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If None, reads from LOG_LEVEL environment variable or defaults to INFO
        rotation: When to rotate the log file
        retention: How long to keep old log files
        use_json: If True, use JSON format for logging
    """
    # Get log level from environment if not specified
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Validate log level
    valid_levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
    if log_level.upper() not in valid_levels:
        log_level = "INFO"

    # Remove default handler
    logger.remove()

    if use_json:
        # JSON format for structured logging
        def json_sink(message):
            """Custom sink for JSON logging to stderr."""
            record = message.record
            json_output = _json_serializer(record) + "\n"
            sys.stderr.write(json_output)
            sys.stderr.flush()

        logger.add(
            json_sink,
            level=log_level,
        )

        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            def json_file_sink(message):
                """Custom sink for JSON logging to file."""
                record = message.record
                json_output = _json_serializer(record) + "\n"
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(json_output)

            logger.add(
                json_file_sink,
                level=log_level,
            )
    else:
        # Human-readable format (backward compatible)
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True,
        )

        # Add file handler if log_file is provided
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level=log_level,
                rotation=rotation,
                retention=retention,
                encoding="utf-8",
            )


def get_logger(name: Optional[str] = None) -> Any:
    """
    Get a logger instance.

    Args:
        name: Name for the logger (usually __name__)

    Returns:
        Logger instance
    """
    # Initialize logger if not already done
    if not logger._core.handlers:
        config = get_config()

        # Check if JSON logging is enabled via environment
        use_json = os.getenv("LOG_FORMAT", "").upper() == "JSON"

        setup_logger(
            log_file=config.log_file,
            log_level=config.log_level,
            use_json=use_json,
        )

    if name:
        return logger.bind(name=name)
    return logger


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set correlation ID for request tracing.

    Args:
        correlation_id: Custom correlation ID. If None, generates a new UUID

    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    _correlation_id.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID.

    Returns:
        Current correlation ID or None if not set
    """
    return _correlation_id.get()


def clear_correlation_id() -> None:
    """Clear the current correlation ID."""
    _correlation_id.set(None)


def configure_sensitive_filter(
    mask_emails: bool = False,
    custom_patterns: Dict[str, str] = None
) -> None:
    """
    Configure the global sensitive data filter.

    Args:
        mask_emails: Whether to mask email addresses in logs
        custom_patterns: Additional regex patterns to mask {name: pattern}

    Example:
        >>> configure_sensitive_filter(
        ...     mask_emails=True,
        ...     custom_patterns={'ssn': r'\b\d{3}-\d{2}-\d{4}\b'}
        ... )
    """
    global _sensitive_filter
    _sensitive_filter = SensitiveDataFilter(
        mask_emails=mask_emails,
        custom_patterns=custom_patterns
    )


def get_sensitive_filter() -> SensitiveDataFilter:
    """
    Get the global sensitive data filter instance.

    Returns:
        Current SensitiveDataFilter instance
    """
    return _sensitive_filter


@contextmanager
def log_context(**kwargs):
    """
    Context manager for temporarily adding extra fields to log messages.

    Args:
        **kwargs: Extra fields to add to log context

    Example:
        with log_context(user_id="123", request_id="abc"):
            logger.info("Processing request")  # Will include user_id and request_id
    """
    # Add correlation ID to context if present
    correlation_id = get_correlation_id()
    if correlation_id:
        kwargs["correlation_id"] = correlation_id

    token = logger.contextualize(**kwargs)
    try:
        yield
    finally:
        # Context is automatically removed when exiting
        pass


def log_performance(func: Optional[Callable] = None, *, level: str = "INFO"):
    """
    Decorator to log function execution time.

    Args:
        func: Function to decorate
        level: Log level to use (default: INFO)

    Example:
        @log_performance
        def my_function():
            pass

        @log_performance(level="DEBUG")
        def another_function():
            pass
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = f.__name__
            module_name = f.__module__

            # Get correlation ID if present
            correlation_id = get_correlation_id()

            try:
                # Log function start
                extra = {
                    "function": func_name,
                    "module": module_name,
                    "phase": "start",
                }
                if correlation_id:
                    extra["correlation_id"] = correlation_id

                logger.bind(**extra).log(level, f"Starting {func_name}")

                # Execute function
                result = f(*args, **kwargs)

                # Log successful completion
                duration = time.time() - start_time
                extra["phase"] = "complete"
                extra["duration_ms"] = round(duration * 1000, 2)

                logger.bind(**extra).log(
                    level,
                    f"Completed {func_name} in {duration:.2f}s"
                )

                return result

            except Exception as e:
                # Log error with timing
                duration = time.time() - start_time
                extra = {
                    "function": func_name,
                    "module": module_name,
                    "phase": "error",
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                }
                if correlation_id:
                    extra["correlation_id"] = correlation_id

                logger.bind(**extra).error(
                    f"Failed {func_name} after {duration:.2f}s: {e}"
                )
                raise

        return wrapper

    # Handle both @log_performance and @log_performance() syntax
    if func is None:
        return decorator
    else:
        return decorator(func)


# Auto-initialize logger
get_logger()
