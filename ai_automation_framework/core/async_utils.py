"""Async utility functions and helpers for the AI Automation Framework."""

import asyncio
import functools
import random
import time
from asyncio import Semaphore, Lock
from contextlib import asynccontextmanager
from typing import TypeVar, Callable, Any, Optional, Coroutine, List, Awaitable
from ai_automation_framework.core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def run_sync(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run async code in a synchronous context.

    This function creates an event loop if one doesn't exist and runs
    the given coroutine to completion.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine

    Example:
        >>> async def fetch_data():
        ...     return "data"
        >>> result = run_sync(fetch_data())
        >>> print(result)
        'data'
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we can't use run_until_complete
            # Create a new loop in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists, create one
        return asyncio.run(coro)


async def run_async(func: Callable[..., T], *args, **kwargs) -> T:
    """
    Run synchronous code in an async context without blocking.

    This function runs a synchronous function in a thread pool executor,
    allowing async code to call blocking functions without blocking the event loop.

    Args:
        func: The synchronous function to run
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        The result of the function

    Example:
        >>> def blocking_operation(x):
        ...     time.sleep(1)
        ...     return x * 2
        >>> result = await run_async(blocking_operation, 5)
        >>> print(result)
        10
    """
    loop = asyncio.get_event_loop()
    partial_func = functools.partial(func, *args, **kwargs)
    return await loop.run_in_executor(None, partial_func)


async def async_sleep_with_jitter(
    base_delay: float,
    jitter_factor: float = 0.1,
    max_jitter: Optional[float] = None
) -> None:
    """
    Async sleep with random jitter to prevent thundering herd problems.

    This function adds random jitter to sleep delays, which helps distribute load
    and prevent multiple clients from synchronizing their retry attempts or periodic
    tasks, avoiding thundering herd scenarios.

    Args:
        base_delay: Base delay in seconds
        jitter_factor: Factor to multiply base_delay for jitter range (default 0.1 = 10%)
        max_jitter: Maximum jitter in seconds (overrides jitter_factor if specified)

    Returns:
        None

    Example:
        >>> # Sleep for approximately 5 seconds with ±10% jitter
        >>> await async_sleep_with_jitter(5.0)
        >>>
        >>> # Sleep for approximately 10 seconds with ±2 second maximum jitter
        >>> await async_sleep_with_jitter(10.0, max_jitter=2.0)
        >>>
        >>> # Sleep for approximately 1 second with ±30% jitter
        >>> await async_sleep_with_jitter(1.0, jitter_factor=0.3)

    Note:
        The actual sleep time will be: base_delay + random(-jitter, +jitter)
        where jitter = min(base_delay * jitter_factor, max_jitter or infinity)
    """
    if max_jitter is not None:
        jitter = max_jitter
    else:
        jitter = base_delay * jitter_factor

    # Random jitter between -jitter and +jitter
    actual_jitter = random.uniform(-jitter, jitter)
    actual_delay = max(0, base_delay + actual_jitter)  # Ensure non-negative

    await asyncio.sleep(actual_delay)


async def gather_with_concurrency(
    n: int,
    *tasks: Awaitable[T],
    return_exceptions: bool = False
) -> List[T]:
    """
    Run multiple async tasks with a concurrency limit.

    This function is similar to asyncio.gather() but limits the number
    of tasks that can run concurrently.

    Args:
        n: Maximum number of concurrent tasks
        *tasks: The tasks to run
        return_exceptions: If True, exceptions are returned instead of raised

    Returns:
        List of results from all tasks

    Example:
        >>> async def fetch(i):
        ...     await asyncio.sleep(0.1)
        ...     return i * 2
        >>> tasks = [fetch(i) for i in range(10)]
        >>> results = await gather_with_concurrency(3, *tasks)
        >>> print(results)
        [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
    """
    semaphore = Semaphore(n)

    async def _with_semaphore(task: Awaitable[T]) -> T:
        async with semaphore:
            return await task

    return await asyncio.gather(
        *(_with_semaphore(task) for task in tasks),
        return_exceptions=return_exceptions
    )


@asynccontextmanager
async def async_timeout(seconds: float):
    """
    Async context manager for timeout operations.

    This provides a cleaner interface for asyncio.wait_for with timeout.
    Raises asyncio.TimeoutError if the operation takes longer than specified.

    Args:
        seconds: Timeout in seconds

    Yields:
        None

    Raises:
        asyncio.TimeoutError: If operation exceeds timeout

    Example:
        >>> async def slow_operation():
        ...     await asyncio.sleep(5)
        >>> async with async_timeout(1.0):
        ...     await slow_operation()  # Will raise TimeoutError
    """
    loop = asyncio.get_event_loop()
    deadline = loop.time() + seconds

    # Store the current task
    task = asyncio.current_task()

    def _timeout_callback():
        if task:
            task.cancel()

    # Schedule the timeout
    timeout_handle = loop.call_at(deadline, _timeout_callback)

    try:
        yield
    except asyncio.CancelledError:
        raise asyncio.TimeoutError(f"Operation timed out after {seconds} seconds")
    finally:
        timeout_handle.cancel()


def retry_async(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying async functions with exponential backoff.

    This decorator will retry the decorated function if it raises one of the
    specified exceptions, with exponential backoff between attempts.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated function

    Example:
        >>> @retry_async(max_attempts=3, base_delay=0.5)
        ... async def unreliable_operation():
        ...     if random.random() < 0.5:
        ...         raise ValueError("Random failure")
        ...     return "success"
        >>> result = await unreliable_operation()
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts - 1:
                        # Last attempt failed, raise the exception
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)

                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_attempts}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )

                    await asyncio.sleep(delay)

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected state in retry_async")

        return wrapper
    return decorator


class AsyncLock:
    """
    Wrapper for asyncio.Lock with cleaner interface and logging.

    This class provides a more user-friendly interface for async locking
    with optional timeout support and automatic logging.

    Example:
        >>> lock = AsyncLock(name="resource_lock")
        >>> async with lock:
        ...     # Critical section
        ...     await process_resource()

        >>> # Or with timeout
        >>> async with lock.acquire_timeout(5.0):
        ...     await process_resource()
    """

    def __init__(self, name: Optional[str] = None, log_acquires: bool = False):
        """
        Initialize the async lock.

        Args:
            name: Optional name for the lock (used in logging)
            log_acquires: If True, log when lock is acquired/released
        """
        self._lock = Lock()
        self.name = name or "AsyncLock"
        self.log_acquires = log_acquires
        self._logger = get_logger(f"AsyncLock.{self.name}")

    async def __aenter__(self):
        """Async context manager entry."""
        if self.log_acquires:
            self._logger.debug(f"Acquiring lock {self.name}")

        await self._lock.acquire()

        if self.log_acquires:
            self._logger.debug(f"Lock {self.name} acquired")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self._lock.release()

        if self.log_acquires:
            self._logger.debug(f"Lock {self.name} released")

    @asynccontextmanager
    async def acquire_timeout(self, timeout: float):
        """
        Acquire lock with timeout.

        Args:
            timeout: Timeout in seconds

        Yields:
            self

        Raises:
            asyncio.TimeoutError: If lock cannot be acquired within timeout

        Example:
            >>> lock = AsyncLock()
            >>> async with lock.acquire_timeout(5.0):
            ...     await critical_operation()
        """
        try:
            async with async_timeout(timeout):
                async with self:
                    yield self
        except asyncio.TimeoutError:
            self._logger.error(f"Failed to acquire lock {self.name} within {timeout}s")
            raise

    def locked(self) -> bool:
        """
        Check if lock is currently held.

        Returns:
            True if lock is held, False otherwise
        """
        return self._lock.locked()

    async def acquire(self):
        """Acquire the lock."""
        if self.log_acquires:
            self._logger.debug(f"Acquiring lock {self.name}")

        await self._lock.acquire()

        if self.log_acquires:
            self._logger.debug(f"Lock {self.name} acquired")

    def release(self):
        """Release the lock."""
        self._lock.release()

        if self.log_acquires:
            self._logger.debug(f"Lock {self.name} released")


__all__ = [
    "run_sync",
    "run_async",
    "async_sleep_with_jitter",
    "gather_with_concurrency",
    "async_timeout",
    "retry_async",
    "AsyncLock",
]
