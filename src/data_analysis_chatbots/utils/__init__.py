"""Utility functions for the Data Analysis with Chatbots project.

This module consolidates all utility functions including:
- Logging setup and configuration
- Directory and path management
- Performance monitoring decorators
- Security utilities
- Formatting utilities
- Safe mathematical operations
"""

import os
import sys
from pathlib import Path
from typing import Union, Optional

from loguru import logger

# Import performance monitoring decorators and security utilities
from .performance import (
    timer,
    memory_profiler,
    retry,
    monitor,
    memoize,
    cached_property_with_ttl,
    LRUCache
)
from .security import SensitiveDataFilter


def setup_logging(
    log_file: Optional[str] = None,
    level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "30 days"
) -> None:
    """
    Setup logging configuration.

    Args:
        log_file: Path to log file. If None, logs only to console.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rotation: When to rotate the log file
        retention: How long to keep old log files
    """
    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )

    # Add file handler if specified
    if log_file:
        ensure_dir(Path(log_file).parent)
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
            level=level,
            rotation=rotation,
            retention=retention,
            compression="zip"
        )

    logger.info(f"Logging initialized. Level: {level}")


def ensure_dir(directory: Union[str, Path]) -> Path:
    """
    Ensure that a directory exists. Create it if it doesn't.

    Args:
        directory: Path to the directory

    Returns:
        Path object of the directory
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_project_root() -> Path:
    """
    Get the root directory of the project.

    Returns:
        Path to project root
    """
    # Assuming this file is in src/data_analysis_chatbots/utils/
    return Path(__file__).parent.parent.parent.parent


def get_data_path(filename: str, data_type: str = "raw") -> Path:
    """
    Get the full path to a data file.

    Args:
        filename: Name of the data file
        data_type: Type of data ('raw', 'processed', 'outputs')

    Returns:
        Full path to the data file
    """
    project_root = get_project_root()
    data_dir = project_root / "data" / data_type
    ensure_dir(data_dir)
    return data_dir / filename


def format_currency(amount: float, currency: str = "$") -> str:
    """
    Format a number as currency.

    Args:
        amount: Amount to format
        currency: Currency symbol

    Returns:
        Formatted currency string
    """
    return f"{currency}{amount:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format a number as percentage.

    Args:
        value: Value to format (0.15 for 15%)
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.

    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value to return if division by zero

    Returns:
        Result of division or default
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ValueError):
        return default


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


__all__ = [
    # Performance monitoring
    "timer",
    "memory_profiler",
    "retry",
    "monitor",
    # Caching utilities
    "memoize",
    "cached_property_with_ttl",
    "LRUCache",
    # Security
    "SensitiveDataFilter",
    # Logging and setup
    "setup_logging",
    # Path management
    "ensure_dir",
    "get_project_root",
    "get_data_path",
    # Formatting
    "format_currency",
    "format_percentage",
    # Utilities
    "safe_divide",
    "truncate_string",
]
