"""Middleware system for request/response processing pipelines.

This module provides a flexible middleware system that allows chaining of
processing steps for requests and responses. It supports both synchronous
and asynchronous operations, with built-in middleware for common tasks.
"""

import asyncio
import time
import hashlib
import json
from abc import ABC, abstractmethod
from typing import (
    Any, Callable, Dict, List, Optional, Union, Awaitable, TypeVar, Generic
)
from datetime import datetime, timedelta
from collections import defaultdict
from contextlib import contextmanager, asynccontextmanager
from functools import wraps

from ai_automation_framework.core.logger import get_logger
from ai_automation_framework.core.cache import ResponseCache


logger = get_logger(__name__)

T = TypeVar('T')


class MiddlewareContext:
    """
    Context object for passing data between middleware in the pipeline.

    The context object maintains state throughout the request/response pipeline,
    allowing middleware to share data and communicate with each other.

    Attributes:
        request: The original request object
        response: The response object (set during processing)
        metadata: Additional metadata dictionary
        short_circuit: Flag to stop pipeline execution

    Example:
        >>> context = MiddlewareContext(request="Hello")
        >>> context.set("user_id", "123")
        >>> user_id = context.get("user_id")
    """

    def __init__(self, request: Any = None, **kwargs):
        """
        Initialize middleware context.

        Args:
            request: The request object to process
            **kwargs: Additional context data
        """
        self.request = request
        self.response: Optional[Any] = None
        self.metadata: Dict[str, Any] = kwargs
        self.short_circuit: bool = False
        self._start_time: float = time.time()
        self._errors: List[Exception] = []

    def set(self, key: str, value: Any) -> None:
        """
        Set a metadata value.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata value.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            The metadata value or default
        """
        return self.metadata.get(key, default)

    def has(self, key: str) -> bool:
        """
        Check if metadata key exists.

        Args:
            key: Metadata key

        Returns:
            True if key exists, False otherwise
        """
        return key in self.metadata

    def stop(self) -> None:
        """Stop pipeline execution after current middleware."""
        self.short_circuit = True

    def add_error(self, error: Exception) -> None:
        """
        Add an error to the context.

        Args:
            error: Exception that occurred
        """
        self._errors.append(error)

    @property
    def errors(self) -> List[Exception]:
        """Get list of errors that occurred during processing."""
        return self._errors

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time since context creation in seconds."""
        return time.time() - self._start_time

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary.

        Returns:
            Dictionary representation of context
        """
        return {
            "request": self.request,
            "response": self.response,
            "metadata": self.metadata,
            "short_circuit": self.short_circuit,
            "elapsed_time": self.elapsed_time,
            "errors": [str(e) for e in self._errors]
        }


class Middleware(ABC):
    """
    Base class for middleware components.

    Middleware components can intercept and modify requests/responses
    in the processing pipeline. They implement before and after hooks
    that are called during pipeline execution.

    Example:
        >>> class MyMiddleware(Middleware):
        ...     def before(self, context):
        ...         print(f"Before: {context.request}")
        ...
        ...     def after(self, context):
        ...         print(f"After: {context.response}")
    """

    def __init__(self, name: Optional[str] = None, enabled: bool = True):
        """
        Initialize middleware.

        Args:
            name: Middleware name (defaults to class name)
            enabled: Whether middleware is enabled
        """
        self.name = name or self.__class__.__name__
        self.enabled = enabled
        self.logger = get_logger(f"Middleware.{self.name}")

    def before(self, context: MiddlewareContext) -> None:
        """
        Hook called before main processing.

        Args:
            context: The middleware context
        """
        pass

    def after(self, context: MiddlewareContext) -> None:
        """
        Hook called after main processing.

        Args:
            context: The middleware context
        """
        pass

    async def before_async(self, context: MiddlewareContext) -> None:
        """
        Async hook called before main processing.

        Args:
            context: The middleware context
        """
        # Default implementation calls sync version
        self.before(context)

    async def after_async(self, context: MiddlewareContext) -> None:
        """
        Async hook called after main processing.

        Args:
            context: The middleware context
        """
        # Default implementation calls sync version
        self.after(context)

    def should_run(self, context: MiddlewareContext) -> bool:
        """
        Determine if middleware should run based on context.

        Args:
            context: The middleware context

        Returns:
            True if middleware should run, False otherwise
        """
        return self.enabled

    def on_error(self, context: MiddlewareContext, error: Exception) -> None:
        """
        Handle errors that occur during processing.

        Args:
            context: The middleware context
            error: The exception that occurred
        """
        self.logger.error(f"Error in {self.name}: {error}")
        context.add_error(error)


class ConditionalMiddleware(Middleware):
    """
    Middleware that only runs if a condition is met.

    Example:
        >>> def check_user(ctx):
        ...     return ctx.get("user_id") is not None
        ...
        >>> middleware = ConditionalMiddleware(
        ...     condition=check_user,
        ...     delegate=LoggingMiddleware()
        ... )
    """

    def __init__(
        self,
        condition: Callable[[MiddlewareContext], bool],
        delegate: Middleware,
        name: Optional[str] = None
    ):
        """
        Initialize conditional middleware.

        Args:
            condition: Function that determines if middleware should run
            delegate: The middleware to run if condition is true
            name: Optional middleware name
        """
        super().__init__(name=name or f"Conditional({delegate.name})")
        self.condition = condition
        self.delegate = delegate

    def should_run(self, context: MiddlewareContext) -> bool:
        """Check if condition is met and middleware is enabled."""
        return self.enabled and self.condition(context)

    def before(self, context: MiddlewareContext) -> None:
        """Call delegate's before hook."""
        if self.should_run(context):
            self.delegate.before(context)

    def after(self, context: MiddlewareContext) -> None:
        """Call delegate's after hook."""
        if self.should_run(context):
            self.delegate.after(context)

    async def before_async(self, context: MiddlewareContext) -> None:
        """Call delegate's async before hook."""
        if self.should_run(context):
            await self.delegate.before_async(context)

    async def after_async(self, context: MiddlewareContext) -> None:
        """Call delegate's async after hook."""
        if self.should_run(context):
            await self.delegate.after_async(context)


class LoggingMiddleware(Middleware):
    """
    Middleware for logging request/response information.

    Logs details about each request and response, including timing information.

    Example:
        >>> middleware = LoggingMiddleware(log_request=True, log_response=True)
    """

    def __init__(
        self,
        log_request: bool = True,
        log_response: bool = True,
        log_metadata: bool = False,
        name: Optional[str] = None
    ):
        """
        Initialize logging middleware.

        Args:
            log_request: Whether to log requests
            log_response: Whether to log responses
            log_metadata: Whether to log metadata
            name: Optional middleware name
        """
        super().__init__(name=name or "Logging")
        self.log_request = log_request
        self.log_response = log_response
        self.log_metadata = log_metadata

    def before(self, context: MiddlewareContext) -> None:
        """Log request information."""
        if self.log_request:
            self.logger.info(f"Request: {context.request}")
            if self.log_metadata and context.metadata:
                self.logger.debug(f"Metadata: {context.metadata}")

    def after(self, context: MiddlewareContext) -> None:
        """Log response information."""
        if self.log_response:
            self.logger.info(
                f"Response: {context.response} "
                f"(elapsed: {context.elapsed_time:.3f}s)"
            )
            if context.errors:
                self.logger.warning(f"Errors occurred: {len(context.errors)}")


class TimingMiddleware(Middleware):
    """
    Middleware for tracking execution time.

    Measures and logs the time taken for request processing.
    Stores timing information in context metadata.

    Example:
        >>> middleware = TimingMiddleware(warn_threshold=1.0)
    """

    def __init__(
        self,
        warn_threshold: Optional[float] = None,
        store_in_context: bool = True,
        name: Optional[str] = None
    ):
        """
        Initialize timing middleware.

        Args:
            warn_threshold: Warn if processing takes longer than this (seconds)
            store_in_context: Store timing in context metadata
            name: Optional middleware name
        """
        super().__init__(name=name or "Timing")
        self.warn_threshold = warn_threshold
        self.store_in_context = store_in_context

    def before(self, context: MiddlewareContext) -> None:
        """Mark start time."""
        context.set("_timing_start", time.time())

    def after(self, context: MiddlewareContext) -> None:
        """Calculate and log elapsed time."""
        start_time = context.get("_timing_start")
        if start_time is None:
            return

        elapsed = time.time() - start_time

        if self.store_in_context:
            context.set("elapsed_time", elapsed)

        log_msg = f"Processing completed in {elapsed:.3f}s"

        if self.warn_threshold and elapsed > self.warn_threshold:
            self.logger.warning(f"{log_msg} (threshold: {self.warn_threshold}s)")
        else:
            self.logger.info(log_msg)


class RetryMiddleware(Middleware):
    """
    Middleware for automatic retry with exponential backoff.

    Retries failed operations with configurable retry logic and backoff.

    Example:
        >>> middleware = RetryMiddleware(
        ...     max_attempts=3,
        ...     base_delay=1.0,
        ...     exceptions=(ValueError, ConnectionError)
        ... )
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        exceptions: tuple = (Exception,),
        name: Optional[str] = None
    ):
        """
        Initialize retry middleware.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff calculation
            exceptions: Tuple of exception types to catch and retry
            name: Optional middleware name
        """
        super().__init__(name=name or "Retry")
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.exceptions = exceptions

    def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)
            except self.exceptions as e:
                last_exception = e

                if attempt == self.max_attempts - 1:
                    self.logger.error(
                        f"Failed after {self.max_attempts} attempts: {e}"
                    )
                    raise

                delay = min(
                    self.base_delay * (self.exponential_base ** attempt),
                    self.max_delay
                )

                self.logger.warning(
                    f"Attempt {attempt + 1}/{self.max_attempts} failed, "
                    f"retrying in {delay:.2f}s: {e}"
                )

                time.sleep(delay)

        if last_exception:
            raise last_exception

    async def execute_with_retry_async(
        self,
        func: Callable[..., Awaitable],
        *args,
        **kwargs
    ) -> Any:
        """
        Execute async function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                return await func(*args, **kwargs)
            except self.exceptions as e:
                last_exception = e

                if attempt == self.max_attempts - 1:
                    self.logger.error(
                        f"Failed after {self.max_attempts} attempts: {e}"
                    )
                    raise

                delay = min(
                    self.base_delay * (self.exponential_base ** attempt),
                    self.max_delay
                )

                self.logger.warning(
                    f"Attempt {attempt + 1}/{self.max_attempts} failed, "
                    f"retrying in {delay:.2f}s: {e}"
                )

                await asyncio.sleep(delay)

        if last_exception:
            raise last_exception


class CacheMiddleware(Middleware):
    """
    Middleware for caching responses.

    Caches responses to avoid redundant processing. Uses ResponseCache
    for persistent disk-based caching with TTL support.

    Example:
        >>> cache = ResponseCache(cache_dir="./cache", ttl_hours=24)
        >>> middleware = CacheMiddleware(
        ...     cache=cache,
        ...     key_generator=lambda ctx: str(ctx.request)
        ... )
    """

    def __init__(
        self,
        cache: Optional[ResponseCache] = None,
        key_generator: Optional[Callable[[MiddlewareContext], str]] = None,
        cache_dir: str = "./cache",
        ttl_hours: int = 24,
        name: Optional[str] = None
    ):
        """
        Initialize cache middleware.

        Args:
            cache: ResponseCache instance (creates one if not provided)
            key_generator: Function to generate cache keys from context
            cache_dir: Directory for cache storage
            ttl_hours: Cache TTL in hours
            name: Optional middleware name
        """
        super().__init__(name=name or "Cache")
        self.cache = cache or ResponseCache(
            cache_dir=cache_dir,
            ttl_hours=ttl_hours
        )
        self.key_generator = key_generator or self._default_key_generator

    def _default_key_generator(self, context: MiddlewareContext) -> str:
        """
        Generate cache key from context.

        Args:
            context: Middleware context

        Returns:
            Cache key string
        """
        # Create a deterministic key from request
        request_str = json.dumps(
            context.request,
            sort_keys=True,
            default=str
        )
        return hashlib.sha256(request_str.encode()).hexdigest()

    def before(self, context: MiddlewareContext) -> None:
        """Check cache for existing response."""
        try:
            cache_key = self.key_generator(context)
            context.set("_cache_key", cache_key)

            # Try to get from cache
            cached = self.cache.get(
                prompt=cache_key,
                model="default",
                temperature=0.0
            )

            if cached is not None:
                self.logger.info(f"Cache hit for key: {cache_key[:16]}...")
                context.response = cached
                context.set("_cache_hit", True)
                context.stop()  # Short-circuit pipeline
            else:
                self.logger.debug(f"Cache miss for key: {cache_key[:16]}...")
                context.set("_cache_hit", False)

        except Exception as e:
            self.logger.warning(f"Cache check failed: {e}")
            context.set("_cache_hit", False)

    def after(self, context: MiddlewareContext) -> None:
        """Store response in cache."""
        if context.get("_cache_hit"):
            return  # Already from cache

        try:
            cache_key = context.get("_cache_key")
            if cache_key and context.response is not None:
                self.cache.set(
                    prompt=cache_key,
                    response=context.response,
                    model="default",
                    temperature=0.0
                )
                self.logger.debug(f"Cached response for key: {cache_key[:16]}...")

        except Exception as e:
            self.logger.warning(f"Failed to cache response: {e}")


class RateLimitMiddleware(Middleware):
    """
    Middleware for rate limiting requests.

    Implements token bucket algorithm for rate limiting with configurable
    limits per time window.

    Example:
        >>> middleware = RateLimitMiddleware(
        ...     max_requests=100,
        ...     window_seconds=60
        ... )
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: float = 60.0,
        key_func: Optional[Callable[[MiddlewareContext], str]] = None,
        name: Optional[str] = None
    ):
        """
        Initialize rate limit middleware.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            key_func: Function to extract rate limit key from context
            name: Optional middleware name
        """
        super().__init__(name=name or "RateLimit")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_func = key_func or (lambda ctx: "default")

        # Track requests per key
        self._request_times: Dict[str, List[float]] = defaultdict(list)

    def _cleanup_old_requests(self, key: str, current_time: float) -> None:
        """
        Remove requests outside the current window.

        Args:
            key: Rate limit key
            current_time: Current timestamp
        """
        cutoff_time = current_time - self.window_seconds
        self._request_times[key] = [
            t for t in self._request_times[key] if t > cutoff_time
        ]

    def _is_rate_limited(self, key: str) -> bool:
        """
        Check if key is rate limited.

        Args:
            key: Rate limit key

        Returns:
            True if rate limited, False otherwise
        """
        current_time = time.time()
        self._cleanup_old_requests(key, current_time)

        request_count = len(self._request_times[key])

        if request_count >= self.max_requests:
            return True

        # Add current request
        self._request_times[key].append(current_time)
        return False

    def before(self, context: MiddlewareContext) -> None:
        """Check rate limit before processing."""
        key = self.key_func(context)

        if self._is_rate_limited(key):
            wait_time = self.window_seconds
            error_msg = (
                f"Rate limit exceeded for key '{key}'. "
                f"Max {self.max_requests} requests per {self.window_seconds}s. "
                f"Retry after {wait_time:.1f}s"
            )
            self.logger.warning(error_msg)

            context.set("rate_limited", True)
            context.set("rate_limit_key", key)
            context.set("retry_after", wait_time)
            context.stop()

            raise RuntimeError(error_msg)

        context.set("rate_limited", False)


class MiddlewareStack:
    """
    Stack for chaining multiple middleware components.

    Executes middleware in order for before hooks, then processes the handler,
    then executes middleware in reverse order for after hooks.

    Example:
        >>> stack = MiddlewareStack([
        ...     LoggingMiddleware(),
        ...     TimingMiddleware(),
        ...     CacheMiddleware()
        ... ])
        >>> result = stack.execute(handler, request="Hello")
    """

    def __init__(self, middleware: Optional[List[Middleware]] = None):
        """
        Initialize middleware stack.

        Args:
            middleware: List of middleware to add to stack
        """
        self.middleware: List[Middleware] = middleware or []
        self.logger = get_logger("MiddlewareStack")

    def add(self, middleware: Middleware) -> 'MiddlewareStack':
        """
        Add middleware to stack.

        Args:
            middleware: Middleware to add

        Returns:
            Self for chaining
        """
        self.middleware.append(middleware)
        return self

    def remove(self, middleware: Middleware) -> 'MiddlewareStack':
        """
        Remove middleware from stack.

        Args:
            middleware: Middleware to remove

        Returns:
            Self for chaining
        """
        if middleware in self.middleware:
            self.middleware.remove(middleware)
        return self

    def clear(self) -> 'MiddlewareStack':
        """
        Clear all middleware from stack.

        Returns:
            Self for chaining
        """
        self.middleware.clear()
        return self

    def _run_before_hooks(self, context: MiddlewareContext) -> bool:
        """
        Run before hooks for all middleware.

        Args:
            context: The middleware context

        Returns:
            True if short-circuited, False otherwise
        """
        for mw in self.middleware:
            if not mw.should_run(context):
                continue

            try:
                mw.before(context)

                if context.short_circuit:
                    self.logger.info(f"Pipeline short-circuited by {mw.name}")
                    return True

            except Exception as e:
                mw.on_error(context, e)
                if not isinstance(mw, RetryMiddleware):
                    raise

        return False

    def _run_after_hooks(self, context: MiddlewareContext) -> None:
        """
        Run after hooks for all middleware in reverse order.

        Args:
            context: The middleware context
        """
        for mw in reversed(self.middleware):
            if not mw.should_run(context):
                continue

            try:
                mw.after(context)
            except Exception as e:
                mw.on_error(context, e)
                # Don't raise on after hooks to ensure cleanup

    async def _run_before_hooks_async(self, context: MiddlewareContext) -> bool:
        """
        Run async before hooks for all middleware.

        Args:
            context: The middleware context

        Returns:
            True if short-circuited, False otherwise
        """
        for mw in self.middleware:
            if not mw.should_run(context):
                continue

            try:
                await mw.before_async(context)

                if context.short_circuit:
                    self.logger.info(f"Pipeline short-circuited by {mw.name}")
                    return True

            except Exception as e:
                mw.on_error(context, e)
                if not isinstance(mw, RetryMiddleware):
                    raise

        return False

    async def _run_after_hooks_async(self, context: MiddlewareContext) -> None:
        """
        Run async after hooks for all middleware in reverse order.

        Args:
            context: The middleware context
        """
        for mw in reversed(self.middleware):
            if not mw.should_run(context):
                continue

            try:
                await mw.after_async(context)
            except Exception as e:
                mw.on_error(context, e)
                # Don't raise on after hooks to ensure cleanup

    def execute(
        self,
        handler: Callable[[Any], Any],
        request: Any = None,
        **context_kwargs
    ) -> Any:
        """
        Execute handler with middleware stack (synchronous).

        Args:
            handler: Function to execute
            request: Request object
            **context_kwargs: Additional context data

        Returns:
            Handler result or cached response
        """
        context = MiddlewareContext(request=request, **context_kwargs)

        try:
            # Execute before hooks
            short_circuited = self._run_before_hooks(context)
            if short_circuited:
                return context.response

            # Execute handler if not short-circuited
            if context.response is None:
                context.response = handler(context.request)

            # Execute after hooks in reverse order
            self._run_after_hooks(context)

            return context.response

        except Exception as e:
            self.logger.error(f"Error in middleware stack: {e}")
            raise

    async def execute_async(
        self,
        handler: Callable[[Any], Awaitable[Any]],
        request: Any = None,
        **context_kwargs
    ) -> Any:
        """
        Execute async handler with middleware stack.

        Args:
            handler: Async function to execute
            request: Request object
            **context_kwargs: Additional context data

        Returns:
            Handler result or cached response
        """
        context = MiddlewareContext(request=request, **context_kwargs)

        try:
            # Execute before hooks
            short_circuited = await self._run_before_hooks_async(context)
            if short_circuited:
                return context.response

            # Execute handler if not short-circuited
            if context.response is None:
                context.response = await handler(context.request)

            # Execute after hooks in reverse order
            await self._run_after_hooks_async(context)

            return context.response

        except Exception as e:
            self.logger.error(f"Error in middleware stack: {e}")
            raise

    def __len__(self) -> int:
        """Get number of middleware in stack."""
        return len(self.middleware)

    def __iter__(self):
        """Iterate over middleware in stack."""
        return iter(self.middleware)


def middleware_decorator(
    *middleware_list: Middleware,
    use_async: bool = False
):
    """
    Decorator to apply middleware to a function.

    Args:
        *middleware_list: Middleware instances to apply
        use_async: Whether to use async execution

    Returns:
        Decorated function

    Example:
        >>> @middleware_decorator(
        ...     LoggingMiddleware(),
        ...     TimingMiddleware()
        ... )
        ... def my_handler(request):
        ...     return f"Processed: {request}"
    """
    stack = MiddlewareStack(list(middleware_list))

    def decorator(func: Callable) -> Callable:
        if use_async or asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # First arg is the request
                request = args[0] if args else None
                return await stack.execute_async(func, request)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # First arg is the request
                request = args[0] if args else None
                return stack.execute(func, request)
            return sync_wrapper

    return decorator


__all__ = [
    "MiddlewareContext",
    "Middleware",
    "ConditionalMiddleware",
    "LoggingMiddleware",
    "TimingMiddleware",
    "RetryMiddleware",
    "CacheMiddleware",
    "RateLimitMiddleware",
    "MiddlewareStack",
    "middleware_decorator",
]
