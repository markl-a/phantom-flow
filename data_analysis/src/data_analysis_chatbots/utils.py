"""Backward compatibility module.

All utilities have been moved to utils/__init__.py for better organization.
This module provides backward compatibility by re-exporting all utilities.

DEPRECATED: Import from data_analysis_chatbots.utils instead.
"""

# Re-export all utilities from utils package for backward compatibility
from .utils import *  # noqa: F401, F403

# Explicitly list exports for better IDE support
__all__ = [
    # Performance monitoring
    "timer",
    "memory_profiler",
    "retry",
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
