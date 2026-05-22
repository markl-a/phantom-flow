"""
Base Adapter for Workflow Integrations

This module provides abstract base classes for workflow integration adapters,
ensuring a consistent interface across different workflow automation platforms.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Protocol
from contextlib import contextmanager


logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class WorkflowExecution:
    """
    Workflow execution result/status.

    Attributes:
        execution_id: Unique execution identifier
        workflow_id: Workflow identifier
        status: Execution status
        start_time: When execution started
        end_time: When execution completed
        input_data: Input data provided to workflow
        output_data: Output data from workflow
        error: Error message if failed
        metadata: Additional execution metadata
    """
    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_complete(self) -> bool:
        """Check if execution is complete."""
        return self.status in {
            ExecutionStatus.SUCCESS,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMEOUT
        }

    @property
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.SUCCESS


@dataclass
class WorkflowInfo:
    """
    Workflow information.

    Attributes:
        workflow_id: Unique workflow identifier
        name: Workflow name
        description: Workflow description
        is_active: Whether workflow is active
        tags: Workflow tags/labels
        metadata: Additional workflow metadata
    """
    workflow_id: str
    name: str
    description: Optional[str] = None
    is_active: bool = True
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseWorkflowAdapter(ABC):
    """
    Base class for workflow automation adapters.

    This abstract base class defines the interface that all workflow
    integration adapters should implement, ensuring consistency across
    different platforms (n8n, Airflow, Zapier, Make, etc.).

    All adapters should inherit from this class and implement the
    required abstract methods.

    Attributes:
        name: Adapter name
        base_url: Base URL of the workflow platform
        connected: Whether adapter is connected
    """

    def __init__(
        self,
        name: str,
        base_url: Optional[str] = None,
        auto_connect: bool = True,
        **kwargs
    ):
        """
        Initialize workflow adapter.

        Args:
            name: Adapter name
            base_url: Base URL of the workflow platform
            auto_connect: Whether to auto-connect on initialization
            **kwargs: Additional adapter-specific configuration
        """
        self.name = name
        self.base_url = base_url
        self._connected = False
        self._config = kwargs
        self.logger = logging.getLogger(f"{__name__}.{name}")

        if auto_connect and base_url:
            try:
                self.connect()
            except Exception as e:
                self.logger.warning(f"Auto-connect failed: {e}")

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the workflow platform.

        Returns:
            True if connection successful, False otherwise

        Example:
            >>> adapter = MyWorkflowAdapter(base_url="https://example.com")
            >>> if adapter.connect():
            ...     print("Connected successfully")
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the workflow platform.

        Returns:
            True if disconnection successful

        Example:
            >>> adapter.disconnect()
        """
        pass

    @abstractmethod
    def trigger_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        wait_for_completion: bool = False,
        timeout: Optional[int] = None
    ) -> WorkflowExecution:
        """
        Trigger a workflow execution.

        Args:
            workflow_id: Workflow identifier to trigger
            input_data: Input data for the workflow
            wait_for_completion: Whether to wait for workflow to complete
            timeout: Timeout in seconds (if wait_for_completion=True)

        Returns:
            WorkflowExecution object with execution details

        Raises:
            ConnectionError: If not connected to platform
            ValueError: If workflow_id is invalid
            TimeoutError: If execution times out

        Example:
            >>> execution = adapter.trigger_workflow(
            ...     "workflow-123",
            ...     input_data={"key": "value"},
            ...     wait_for_completion=True,
            ...     timeout=300
            ... )
            >>> print(f"Status: {execution.status}")
        """
        pass

    @abstractmethod
    def get_execution_status(self, execution_id: str) -> WorkflowExecution:
        """
        Get status of a workflow execution.

        Args:
            execution_id: Execution identifier

        Returns:
            WorkflowExecution object with current status

        Raises:
            ConnectionError: If not connected to platform
            ValueError: If execution_id is invalid

        Example:
            >>> execution = adapter.get_execution_status("exec-456")
            >>> if execution.is_complete:
            ...     print(f"Completed with status: {execution.status}")
        """
        pass

    @abstractmethod
    def list_workflows(
        self,
        active_only: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[WorkflowInfo]:
        """
        List available workflows.

        Args:
            active_only: Only return active workflows
            tags: Filter by tags

        Returns:
            List of WorkflowInfo objects

        Example:
            >>> workflows = adapter.list_workflows(active_only=True)
            >>> for wf in workflows:
            ...     print(f"{wf.name}: {wf.workflow_id}")
        """
        pass

    @abstractmethod
    def get_workflow_info(self, workflow_id: str) -> WorkflowInfo:
        """
        Get information about a specific workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            WorkflowInfo object

        Raises:
            ValueError: If workflow not found
        """
        pass

    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a running workflow execution.

        Optional method - not all platforms support cancellation.

        Args:
            execution_id: Execution identifier

        Returns:
            True if cancellation successful

        Raises:
            NotImplementedError: If platform doesn't support cancellation
        """
        raise NotImplementedError(
            f"{self.name} does not support execution cancellation"
        )

    def get_execution_logs(self, execution_id: str) -> List[str]:
        """
        Get logs for a workflow execution.

        Optional method - not all platforms support logs.

        Args:
            execution_id: Execution identifier

        Returns:
            List of log lines

        Raises:
            NotImplementedError: If platform doesn't support logs
        """
        raise NotImplementedError(
            f"{self.name} does not support execution logs"
        )

    @property
    def is_connected(self) -> bool:
        """Check if adapter is connected."""
        return self._connected

    def validate_connection(self) -> bool:
        """
        Validate that connection is still active.

        Returns:
            True if connection is valid
        """
        return self.is_connected

    @contextmanager
    def connection(self):
        """
        Context manager for connection handling.

        Example:
            >>> with adapter.connection():
            ...     execution = adapter.trigger_workflow("workflow-123")
        """
        try:
            if not self.is_connected:
                self.connect()
            yield self
        finally:
            if self.is_connected:
                self.disconnect()

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}("
            f"name={self.name}, "
            f"base_url={self.base_url}, "
            f"connected={self.is_connected})"
        )


class BaseWebhookAdapter(BaseWorkflowAdapter):
    """
    Base adapter for webhook-based workflow platforms.

    This adapter is for platforms that primarily use webhooks
    for triggering workflows (like n8n, Make.com, Zapier).
    """

    @abstractmethod
    def trigger_webhook(
        self,
        webhook_url: str,
        data: Dict[str, Any],
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Trigger a webhook.

        Args:
            webhook_url: Full webhook URL
            data: Data to send to webhook
            method: HTTP method (GET, POST, etc.)
            headers: Additional HTTP headers

        Returns:
            Response data

        Example:
            >>> response = adapter.trigger_webhook(
            ...     "https://example.com/webhook/abc123",
            ...     {"key": "value"}
            ... )
        """
        pass


class BaseAPIAdapter(BaseWorkflowAdapter):
    """
    Base adapter for API-based workflow platforms.

    This adapter is for platforms with full REST APIs
    (like Airflow, Prefect, Temporal).
    """

    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with the platform API.

        Args:
            credentials: Authentication credentials

        Returns:
            True if authentication successful
        """
        pass

    @abstractmethod
    def refresh_token(self) -> bool:
        """
        Refresh authentication token.

        Returns:
            True if refresh successful
        """
        pass


class AdapterRegistry:
    """
    Registry for workflow adapters.

    Similar to LLMClientFactory, this registry allows dynamic
    registration and creation of workflow adapters.
    """

    _adapters: Dict[str, type] = {}
    _lock = None

    @classmethod
    def _get_lock(cls):
        """Get or create the threading lock."""
        if cls._lock is None:
            import threading
            cls._lock = threading.RLock()
        return cls._lock

    @classmethod
    def register(cls, name: str, adapter_class: type) -> None:
        """
        Register a workflow adapter.

        Args:
            name: Adapter name (e.g., "n8n", "airflow")
            adapter_class: Adapter class
        """
        if not issubclass(adapter_class, BaseWorkflowAdapter):
            raise TypeError(
                f"Adapter must inherit from BaseWorkflowAdapter, "
                f"got {adapter_class}"
            )

        with cls._get_lock():
            cls._adapters[name.lower()] = adapter_class
            logger.info(f"Registered workflow adapter: {name}")

    @classmethod
    def create(cls, name: str, **kwargs) -> BaseWorkflowAdapter:
        """
        Create a workflow adapter.

        Args:
            name: Adapter name
            **kwargs: Adapter configuration

        Returns:
            Instantiated adapter
        """
        normalized_name = name.lower()

        with cls._get_lock():
            if normalized_name not in cls._adapters:
                available = ", ".join(cls._adapters.keys())
                raise ValueError(
                    f"Unknown adapter '{normalized_name}'. "
                    f"Available: {available or 'none'}"
                )

            adapter_class = cls._adapters[normalized_name]

        return adapter_class(name=name, **kwargs)

    @classmethod
    def list_adapters(cls) -> List[str]:
        """Get list of registered adapters."""
        with cls._get_lock():
            return sorted(cls._adapters.keys())
