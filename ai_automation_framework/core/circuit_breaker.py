"""Circuit breaker pattern implementation for resilient external service calls.

This module provides a circuit breaker implementation to prevent cascading failures
in distributed systems by stopping calls to failing services temporarily.
"""

import asyncio
import functools
import threading
import time
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    TypeVar,
    List,
    Union,
    Coroutine,
)

from ai_automation_framework.core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Failure threshold exceeded, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""

    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changed_time: float = field(default_factory=time.time)
    total_requests: int = 0
    rejected_requests: int = 0

    def reset(self) -> None:
        """Reset all statistics."""
        self.success_count = 0
        self.failure_count = 0
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.total_requests = 0
        self.rejected_requests = 0

    def reset_consecutive_counts(self) -> None:
        """Reset consecutive success/failure counts."""
        self.consecutive_failures = 0
        self.consecutive_successes = 0

    def record_success(self) -> None:
        """Record a successful call."""
        self.success_count += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        self.last_success_time = time.time()
        self.total_requests += 1

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_failure_time = time.time()
        self.total_requests += 1

    def record_rejected(self) -> None:
        """Record a rejected call (circuit open)."""
        self.rejected_requests += 1

    def get_failure_rate(self) -> float:
        """
        Calculate the failure rate.

        Returns:
            Failure rate as a float between 0 and 1
        """
        if self.total_requests == 0:
            return 0.0
        return self.failure_count / self.total_requests

    def get_stats_dict(self) -> Dict[str, Any]:
        """
        Get statistics as a dictionary.

        Returns:
            Dictionary with all statistics
        """
        return {
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "state_changed_time": self.state_changed_time,
            "total_requests": self.total_requests,
            "rejected_requests": self.rejected_requests,
            "failure_rate": self.get_failure_rate(),
        }


class CircuitBreaker:
    """
    Circuit breaker for protecting external service calls.

    The circuit breaker monitors calls to external services and automatically
    opens the circuit (stops calls) when failures exceed a threshold. After
    a recovery timeout, it enters half-open state to test if the service
    has recovered.

    States:
        - CLOSED: Normal operation, all calls pass through
        - OPEN: Too many failures, all calls fail fast
        - HALF_OPEN: Testing recovery, limited calls allowed

    Example:
        >>> breaker = CircuitBreaker(
        ...     name="api_service",
        ...     failure_threshold=5,
        ...     recovery_timeout=60.0,
        ...     expected_exception=RequestException
        ... )
        >>>
        >>> # Synchronous usage
        >>> with breaker:
        ...     response = requests.get("https://api.example.com")
        >>>
        >>> # Async usage
        >>> async with breaker:
        ...     response = await client.get("https://api.example.com")
        >>>
        >>> # Decorator usage
        >>> @breaker.decorator
        ... def call_api():
        ...     return requests.get("https://api.example.com")
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Union[type, tuple] = Exception,
        success_threshold: int = 2,
        half_open_max_calls: int = 1,
        on_open: Optional[Callable[[str], None]] = None,
        on_close: Optional[Callable[[str], None]] = None,
        on_half_open: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the circuit breaker.

        Args:
            name: Name of the circuit breaker (for logging and identification)
            failure_threshold: Number of consecutive failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery (half-open state)
            expected_exception: Exception type(s) to catch and count as failures
            success_threshold: Number of consecutive successes in half-open state before closing
            half_open_max_calls: Maximum concurrent calls allowed in half-open state
            on_open: Callback when circuit opens
            on_close: Callback when circuit closes
            on_half_open: Callback when circuit enters half-open state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        self.half_open_max_calls = half_open_max_calls

        # State management
        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()

        # Thread safety
        self._lock = threading.RLock()
        self._async_lock = asyncio.Lock()

        # Half-open state tracking
        self._half_open_calls = 0

        # Callbacks
        self._on_open = on_open
        self._on_close = on_close
        self._on_half_open = on_half_open

        # Logger
        self._logger = get_logger(f"CircuitBreaker.{name}")

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        """Get current statistics."""
        return self._stats

    def _transition_to(self, new_state: CircuitState) -> None:
        """
        Transition to a new state.

        Args:
            new_state: The state to transition to
        """
        old_state = self._state

        if old_state == new_state:
            return

        self._state = new_state
        self._stats.state_changed_time = time.time()

        self._logger.info(
            f"Circuit breaker '{self.name}' transitioned from {old_state.value} to {new_state.value}",
            extra={
                "circuit_breaker": self.name,
                "old_state": old_state.value,
                "new_state": new_state.value,
                "stats": self._stats.get_stats_dict(),
            }
        )

        # Trigger callbacks
        if new_state == CircuitState.OPEN and self._on_open:
            try:
                self._on_open(self.name)
            except Exception as e:
                self._logger.error(f"Error in on_open callback: {e}")

        elif new_state == CircuitState.CLOSED and self._on_close:
            try:
                self._on_close(self.name)
            except Exception as e:
                self._logger.error(f"Error in on_close callback: {e}")

        elif new_state == CircuitState.HALF_OPEN and self._on_half_open:
            try:
                self._on_half_open(self.name)
            except Exception as e:
                self._logger.error(f"Error in on_half_open callback: {e}")

    def _should_attempt_reset(self) -> bool:
        """
        Check if enough time has passed to attempt recovery.

        Returns:
            True if recovery should be attempted
        """
        if self._state != CircuitState.OPEN:
            return False

        if self._stats.last_failure_time is None:
            return False

        time_since_failure = time.time() - self._stats.last_failure_time
        return time_since_failure >= self.recovery_timeout

    def _check_threshold(self) -> None:
        """Check if thresholds are exceeded and transition state if needed."""
        if self._state == CircuitState.CLOSED:
            if self._stats.consecutive_failures >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)
                self._stats.reset_consecutive_counts()

        elif self._state == CircuitState.HALF_OPEN:
            if self._stats.consecutive_successes >= self.success_threshold:
                self._transition_to(CircuitState.CLOSED)
                self._stats.reset_consecutive_counts()
                self._half_open_calls = 0

            elif self._stats.consecutive_failures > 0:
                self._transition_to(CircuitState.OPEN)
                self._stats.reset_consecutive_counts()
                self._half_open_calls = 0

    def _before_call(self) -> None:
        """
        Called before each protected call.

        Raises:
            CircuitBreakerError: If circuit is open and recovery timeout not reached
        """
        with self._lock:
            # Check if we should transition from OPEN to HALF_OPEN
            if self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
                self._half_open_calls = 0

            # Reject call if circuit is open
            if self._state == CircuitState.OPEN:
                self._stats.record_rejected()
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable. Will retry after recovery timeout."
                )

            # In half-open state, limit concurrent calls
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    self._stats.record_rejected()
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is HALF_OPEN. "
                        f"Maximum test calls ({self.half_open_max_calls}) already in progress."
                    )
                self._half_open_calls += 1

    def _on_success(self) -> None:
        """Called after a successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls = max(0, self._half_open_calls - 1)

            self._stats.record_success()
            self._check_threshold()

    def _on_failure(self, exception: Exception) -> None:
        """
        Called after a failed call.

        Args:
            exception: The exception that was raised
        """
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls = max(0, self._half_open_calls - 1)

            self._stats.record_failure()

            self._logger.warning(
                f"Circuit breaker '{self.name}' recorded failure: {exception}",
                extra={
                    "circuit_breaker": self.name,
                    "state": self._state.value,
                    "consecutive_failures": self._stats.consecutive_failures,
                    "exception": str(exception),
                }
            )

            self._check_threshold()

    @contextmanager
    def __call__(self):
        """
        Context manager for synchronous calls.

        Yields:
            None

        Raises:
            CircuitBreakerError: If circuit is open
        """
        self._before_call()

        try:
            yield
            self._on_success()
        except self.expected_exception as e:
            self._on_failure(e)
            raise

    def __enter__(self):
        """Context manager entry."""
        self._before_call()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self._on_success()
        elif isinstance(exc_val, self.expected_exception):
            self._on_failure(exc_val)
        return False

    @asynccontextmanager
    async def async_call(self):
        """
        Async context manager for async calls.

        Yields:
            None

        Raises:
            CircuitBreakerError: If circuit is open
        """
        # Use async lock for state checks
        async with self._async_lock:
            self._before_call()

        try:
            yield
            async with self._async_lock:
                self._on_success()
        except self.expected_exception as e:
            async with self._async_lock:
                self._on_failure(e)
            raise

    async def __aenter__(self):
        """Async context manager entry."""
        async with self._async_lock:
            self._before_call()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        async with self._async_lock:
            if exc_type is None:
                self._on_success()
            elif isinstance(exc_val, self.expected_exception):
                self._on_failure(exc_val)
        return False

    def decorator(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator for protecting synchronous functions.

        Args:
            func: Function to protect

        Returns:
            Wrapped function

        Example:
            >>> breaker = CircuitBreaker("api")
            >>> @breaker.decorator
            ... def call_api():
            ...     return requests.get("https://api.example.com")
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            with self:
                return func(*args, **kwargs)

        return wrapper

    def async_decorator(
        self,
        func: Callable[..., Coroutine[Any, Any, T]]
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        """
        Decorator for protecting async functions.

        Args:
            func: Async function to protect

        Returns:
            Wrapped async function

        Example:
            >>> breaker = CircuitBreaker("api")
            >>> @breaker.async_decorator
            ... async def call_api():
            ...     return await client.get("https://api.example.com")
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            async with self:
                return await func(*args, **kwargs)

        return wrapper

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Call a function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open

        Example:
            >>> breaker = CircuitBreaker("api")
            >>> result = breaker.call(requests.get, "https://api.example.com")
        """
        with self:
            return func(*args, **kwargs)

    async def call_async(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args,
        **kwargs
    ) -> T:
        """
        Call an async function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open

        Example:
            >>> breaker = CircuitBreaker("api")
            >>> result = await breaker.call_async(client.get, "https://api.example.com")
        """
        async with self:
            return await func(*args, **kwargs)

    def reset(self) -> None:
        """
        Reset the circuit breaker to closed state.

        This clears all statistics and transitions to CLOSED state.
        Use with caution in production.
        """
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._stats.reset()
            self._half_open_calls = 0

            self._logger.info(
                f"Circuit breaker '{self.name}' manually reset",
                extra={"circuit_breaker": self.name}
            )

    def get_state_info(self) -> Dict[str, Any]:
        """
        Get detailed state information.

        Returns:
            Dictionary with state and statistics
        """
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "success_threshold": self.success_threshold,
                "half_open_max_calls": self.half_open_max_calls,
                "stats": self._stats.get_stats_dict(),
            }


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.

    This class provides a centralized way to create, access, and monitor
    multiple circuit breakers across an application.

    Example:
        >>> registry = CircuitBreakerRegistry()
        >>>
        >>> # Create or get circuit breaker
        >>> api_breaker = registry.get_or_create(
        ...     "api_service",
        ...     failure_threshold=5,
        ...     recovery_timeout=60.0
        ... )
        >>>
        >>> # Get all breakers
        >>> all_breakers = registry.get_all()
        >>>
        >>> # Get summary of all breakers
        >>> summary = registry.get_summary()
    """

    def __init__(self):
        """Initialize the registry."""
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
        self._logger = get_logger("CircuitBreakerRegistry")

    def register(self, breaker: CircuitBreaker) -> None:
        """
        Register a circuit breaker.

        Args:
            breaker: Circuit breaker to register

        Raises:
            ValueError: If a breaker with the same name already exists
        """
        with self._lock:
            if breaker.name in self._breakers:
                raise ValueError(
                    f"Circuit breaker '{breaker.name}' already registered"
                )

            self._breakers[breaker.name] = breaker

            self._logger.info(
                f"Registered circuit breaker '{breaker.name}'",
                extra={"circuit_breaker": breaker.name}
            )

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """
        Get a circuit breaker by name.

        Args:
            name: Name of the circuit breaker

        Returns:
            Circuit breaker or None if not found
        """
        with self._lock:
            return self._breakers.get(name)

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Union[type, tuple] = Exception,
        success_threshold: int = 2,
        half_open_max_calls: int = 1,
        on_open: Optional[Callable[[str], None]] = None,
        on_close: Optional[Callable[[str], None]] = None,
        on_half_open: Optional[Callable[[str], None]] = None,
    ) -> CircuitBreaker:
        """
        Get existing circuit breaker or create a new one.

        Args:
            name: Name of the circuit breaker
            failure_threshold: Number of consecutive failures before opening
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type(s) to catch
            success_threshold: Successes needed in half-open before closing
            half_open_max_calls: Max concurrent calls in half-open state
            on_open: Callback when circuit opens
            on_close: Callback when circuit closes
            on_half_open: Callback when circuit enters half-open

        Returns:
            Circuit breaker instance
        """
        with self._lock:
            breaker = self._breakers.get(name)

            if breaker is None:
                breaker = CircuitBreaker(
                    name=name,
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout,
                    expected_exception=expected_exception,
                    success_threshold=success_threshold,
                    half_open_max_calls=half_open_max_calls,
                    on_open=on_open,
                    on_close=on_close,
                    on_half_open=on_half_open,
                )
                self._breakers[name] = breaker

                self._logger.info(
                    f"Created circuit breaker '{name}'",
                    extra={"circuit_breaker": name}
                )

            return breaker

    def remove(self, name: str) -> bool:
        """
        Remove a circuit breaker from the registry.

        Args:
            name: Name of the circuit breaker

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if name in self._breakers:
                del self._breakers[name]

                self._logger.info(
                    f"Removed circuit breaker '{name}'",
                    extra={"circuit_breaker": name}
                )
                return True

            return False

    def get_all(self) -> Dict[str, CircuitBreaker]:
        """
        Get all registered circuit breakers.

        Returns:
            Dictionary of circuit breakers by name
        """
        with self._lock:
            return self._breakers.copy()

    def get_all_names(self) -> List[str]:
        """
        Get names of all registered circuit breakers.

        Returns:
            List of circuit breaker names
        """
        with self._lock:
            return list(self._breakers.keys())

    def get_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary of all circuit breakers.

        Returns:
            List of state info dictionaries for all breakers
        """
        with self._lock:
            return [
                breaker.get_state_info()
                for breaker in self._breakers.values()
            ]

    def reset_all(self) -> None:
        """Reset all circuit breakers to closed state."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()

            self._logger.info("Reset all circuit breakers")

    def clear(self) -> None:
        """Remove all circuit breakers from the registry."""
        with self._lock:
            self._breakers.clear()
            self._logger.info("Cleared all circuit breakers from registry")


# Global registry instance
_global_registry = CircuitBreakerRegistry()


def get_registry() -> CircuitBreakerRegistry:
    """
    Get the global circuit breaker registry.

    Returns:
        Global CircuitBreakerRegistry instance
    """
    return _global_registry


def get_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Union[type, tuple] = Exception,
    **kwargs
) -> CircuitBreaker:
    """
    Get or create a circuit breaker from the global registry.

    Args:
        name: Name of the circuit breaker
        failure_threshold: Number of consecutive failures before opening
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type(s) to catch
        **kwargs: Additional arguments for CircuitBreaker

    Returns:
        Circuit breaker instance

    Example:
        >>> breaker = get_breaker("api_service", failure_threshold=5)
        >>> with breaker:
        ...     response = requests.get("https://api.example.com")
    """
    return _global_registry.get_or_create(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exception=expected_exception,
        **kwargs
    )


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Union[type, tuple] = Exception,
    **kwargs
):
    """
    Decorator for protecting functions with a circuit breaker.

    This creates or reuses a circuit breaker from the global registry
    and wraps the function with it.

    Args:
        name: Name of the circuit breaker
        failure_threshold: Number of consecutive failures before opening
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type(s) to catch
        **kwargs: Additional arguments for CircuitBreaker

    Returns:
        Decorator function

    Example:
        >>> @circuit_breaker("api_service", failure_threshold=5)
        ... def call_api():
        ...     return requests.get("https://api.example.com")
        >>>
        >>> @circuit_breaker("async_api", failure_threshold=5)
        ... async def call_async_api():
        ...     return await client.get("https://api.example.com")
    """
    breaker = get_breaker(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exception=expected_exception,
        **kwargs
    )

    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            return breaker.async_decorator(func)
        else:
            return breaker.decorator(func)

    return decorator


__all__ = [
    "CircuitState",
    "CircuitBreakerError",
    "CircuitBreakerStats",
    "CircuitBreaker",
    "CircuitBreakerRegistry",
    "get_registry",
    "get_breaker",
    "circuit_breaker",
]
