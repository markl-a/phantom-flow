"""Unified result types for consistent API responses."""

from dataclasses import dataclass, field
from typing import TypeVar, Generic, Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

T = TypeVar('T')

class ResultStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    PENDING = "pending"

@dataclass
class Result(Generic[T]):
    """Unified result type for all operations."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def ok(cls, data: T, **metadata) -> 'Result[T]':
        """Create successful result."""
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error: str, error_type: str = None, error_code: str = None, **metadata) -> 'Result[T]':
        """Create failed result."""
        return cls(success=False, error=error, error_type=error_type, error_code=error_code, metadata=metadata)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"success": self.success}
        if self.data is not None:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        if self.error_type:
            result["error_type"] = self.error_type
        if self.error_code:
            result["error_code"] = self.error_code
        if self.metadata:
            result["metadata"] = self.metadata
        result["timestamp"] = self.timestamp.isoformat()
        return result

@dataclass
class PaginatedResult(Generic[T]):
    """Result type for paginated data."""
    items: List[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
