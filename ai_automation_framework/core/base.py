"""Base classes for the AI Automation Framework."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, List, Union, Protocol, Literal
from types import TracebackType
try:
    from typing_extensions import TypedDict  # Prefer typing_extensions for Pydantic compatibility
except ImportError:
    from typing import TypedDict  # Fallback for environments without typing_extensions
from pydantic import BaseModel, ConfigDict, Field
from ai_automation_framework.core.logger import get_logger


# Type definitions for message and response structures
RoleType = Literal["system", "user", "assistant", "function", "tool"]
FinishReasonType = Literal["stop", "length", "function_call", "tool_calls", "content_filter"]


class FunctionCallDict(TypedDict, total=False):
    """Type definition for function call structure."""
    name: str
    arguments: str


class ToolCallDict(TypedDict, total=False):
    """Type definition for tool call structure."""
    id: str
    type: str
    function: FunctionCallDict


class UsageDict(TypedDict, total=False):
    """Type definition for token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ComponentProtocol(Protocol):
    """Protocol for component-like objects.

    Defines the interface that component-like objects should implement
    for duck typing compatibility.
    """

    name: str

    def initialize(self) -> None:
        """Initialize the component."""
        ...

    def cleanup(self) -> None:
        """Cleanup resources."""
        ...


class BaseComponent(ABC):
    """
    Base class for all framework components.

    Provides common functionality like logging, configuration, and lifecycle management.
    """

    def __init__(self, name: Optional[str] = None, **kwargs: Any) -> None:
        """
        Initialize the component.

        Args:
            name: Component name
            **kwargs: Additional configuration
        """
        self.name: str = name or self.__class__.__name__
        self.logger = get_logger(self.name)
        self.config: Dict[str, Any] = kwargs
        self._initialized: bool = False

    def initialize(self) -> None:
        """Initialize the component."""
        if not self._initialized:
            self.logger.info(f"Initializing {self.name}")
            self._initialize()
            self._initialized = True

    @abstractmethod
    def _initialize(self) -> None:
        """Component-specific initialization logic."""
        pass

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self._initialized:
            self.logger.info(f"Cleaning up {self.name}")
            self._cleanup()
            self._initialized = False

    def _cleanup(self) -> None:
        """Component-specific cleanup logic."""
        pass

    def __enter__(self) -> 'BaseComponent':
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        """Context manager exit."""
        self.cleanup()


class Message(BaseModel):
    """Represents a message in a conversation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    role: RoleType
    content: str
    name: Optional[str] = None
    function_call: Optional[Union[FunctionCallDict, Dict[str, Any]]] = None


class Response(BaseModel):
    """Represents a response from an LLM or agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    content: str
    role: RoleType = "assistant"
    model: Optional[str] = None
    usage: Optional[Union[UsageDict, Dict[str, int]]] = None
    finish_reason: Optional[FinishReasonType] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tool_calls: Optional[Union[List[ToolCallDict], List[Dict[str, Any]]]] = None
