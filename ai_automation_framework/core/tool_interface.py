"""Standardized tool interface for consistent API design."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Dict, Any, Optional, Type
from dataclasses import dataclass
import time
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class ToolResult(Generic[T]):
    """Standardized result from tool execution."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    execution_time_ms: float = 0.0

    @classmethod
    def ok(cls, data: T, execution_time_ms: float = 0.0) -> 'ToolResult[T]':
        return cls(success=True, data=data, execution_time_ms=execution_time_ms)

    @classmethod
    def fail(cls, error: str, error_type: str = None) -> 'ToolResult[T]':
        return cls(success=False, error=error, error_type=error_type)


class ToolInterface(ABC):
    """
    Abstract base class for all tools.

    All tools should implement the execute() method for consistency.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for identification."""
        pass

    @property
    def description(self) -> str:
        """Tool description."""
        return ""

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.

        All tools must implement this method.
        """
        pass

    def validate_params(self, **kwargs) -> Optional[str]:
        """
        Validate input parameters. Return error message if invalid, None if valid.
        Override in subclasses for custom validation.
        """
        return None

    def safe_execute(self, **kwargs) -> ToolResult:
        """
        Execute with validation and error handling.
        """
        # Validate first
        validation_error = self.validate_params(**kwargs)
        if validation_error:
            return ToolResult.fail(validation_error, "validation_error")

        # Execute with timing
        start = time.perf_counter()
        try:
            result = self.execute(**kwargs)
            if not isinstance(result, ToolResult):
                # Wrap legacy results
                if isinstance(result, dict):
                    if result.get('success', True):
                        return ToolResult.ok(result)
                    else:
                        return ToolResult.fail(result.get('error', 'Unknown error'))
                return ToolResult.ok(result)
            result.execution_time_ms = (time.perf_counter() - start) * 1000
            return result
        except Exception as e:
            logger.exception(f"Tool {self.name} failed")
            return ToolResult.fail(str(e), type(e).__name__)
