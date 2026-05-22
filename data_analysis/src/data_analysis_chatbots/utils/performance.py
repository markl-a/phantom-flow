"""Performance monitoring decorators and utilities.

This module provides decorators for monitoring function performance,
including execution time, memory usage, retry logic with exponential backoff,
and caching for performance optimization.
"""

import functools
import time
import hashlib
from typing import Callable, TypeVar, ParamSpec, Any, Optional, Type, Tuple, Dict
from loguru import logger
import traceback
from collections import OrderedDict
from threading import Lock

# Type variables for generic decorators
P = ParamSpec('P')
R = TypeVar('R')


def timer(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to measure and log function execution time.

    This decorator records the time taken for a function to execute
    and logs it using loguru. It preserves the original function's
    signature and metadata.

    Args:
        func: The function to be timed

    Returns:
        Wrapped function that logs execution time

    Example:
        >>> @timer
        ... def slow_function(n: int) -> int:
        ...     time.sleep(n)
        ...     return n * 2
        >>> result = slow_function(2)
        # Logs: "slow_function executed in 2.00 seconds"
    """
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time

            logger.info(
                f"{func.__name__} executed in {execution_time:.4f} seconds"
            )
            return result
        except Exception as e:
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            logger.error(
                f"{func.__name__} failed after {execution_time:.4f} seconds: {str(e)}"
            )
            raise

    return wrapper


def memory_profiler(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to measure and log memory usage of a function.

    This decorator monitors the memory consumption before and after
    function execution. It requires the 'psutil' package, but will
    gracefully degrade if it's not available.

    Args:
        func: The function to profile

    Returns:
        Wrapped function that logs memory usage

    Example:
        >>> @memory_profiler
        ... def memory_intensive_function():
        ...     data = [i for i in range(1000000)]
        ...     return sum(data)
        >>> result = memory_intensive_function()
        # Logs: "memory_intensive_function used X MB of memory"

    Note:
        Requires psutil package. Install with: pip install psutil
        If psutil is not available, the decorator will log a warning
        and execute the function without profiling.
    """
    try:
        import psutil
        import os

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Get current process
            process = psutil.Process(os.getpid())

            # Memory before execution
            mem_before = process.memory_info().rss / 1024 / 1024  # Convert to MB

            try:
                result = func(*args, **kwargs)

                # Memory after execution
                mem_after = process.memory_info().rss / 1024 / 1024  # Convert to MB
                mem_diff = mem_after - mem_before

                logger.info(
                    f"{func.__name__} memory usage: "
                    f"Before={mem_before:.2f} MB, "
                    f"After={mem_after:.2f} MB, "
                    f"Diff={mem_diff:+.2f} MB"
                )
                return result
            except Exception as e:
                mem_after = process.memory_info().rss / 1024 / 1024
                mem_diff = mem_after - mem_before
                logger.error(
                    f"{func.__name__} failed. Memory usage: "
                    f"Before={mem_before:.2f} MB, "
                    f"After={mem_after:.2f} MB, "
                    f"Diff={mem_diff:+.2f} MB, "
                    f"Error: {str(e)}"
                )
                raise

        return wrapper

    except ImportError:
        logger.warning(
            f"psutil not available. Memory profiling for {func.__name__} disabled. "
            "Install with: pip install psutil"
        )

        @functools.wraps(func)
        def wrapper_no_profile(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        return wrapper_no_profile


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to retry a function with exponential backoff.

    This decorator will retry a function if it raises specified exceptions,
    with exponentially increasing delays between attempts.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        delay: Initial delay in seconds between retries (default: 1.0)
        backoff: Multiplier for delay after each retry (default: 2.0)
        exceptions: Tuple of exception types to catch (default: (Exception,))
        on_retry: Optional callback function called on each retry.
                  Receives attempt number and exception as arguments.

    Returns:
        Decorator function

    Example:
        >>> @retry(max_attempts=3, delay=1.0, backoff=2.0)
        ... def unstable_api_call():
        ...     # Simulating an unstable API
        ...     import random
        ...     if random.random() < 0.7:
        ...         raise ConnectionError("API unavailable")
        ...     return "Success"

        >>> @retry(
        ...     max_attempts=5,
        ...     delay=0.5,
        ...     backoff=1.5,
        ...     exceptions=(ValueError, TypeError)
        ... )
        ... def data_processing():
        ...     # Process data that might fail
        ...     return process_data()

        >>> # Custom retry callback
        >>> def log_retry(attempt: int, error: Exception):
        ...     print(f"Retry {attempt}: {error}")
        >>> @retry(max_attempts=3, on_retry=log_retry)
        ... def flaky_function():
        ...     pass
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            current_delay = delay
            last_exception: Optional[Exception] = None

            for attempt in range(1, max_attempts + 1):
                try:
                    if attempt > 1:
                        logger.info(
                            f"Retry attempt {attempt}/{max_attempts} for {func.__name__}"
                        )
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts. "
                            f"Last error: {str(e)}\n{traceback.format_exc()}"
                        )
                        raise

                    # Log the retry
                    logger.warning(
                        f"{func.__name__} failed on attempt {attempt}/{max_attempts}: {str(e)}. "
                        f"Retrying in {current_delay:.2f} seconds..."
                    )

                    # Call custom retry callback if provided
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.error(
                                f"Error in retry callback: {str(callback_error)}"
                            )

                    # Wait before retrying
                    time.sleep(current_delay)
                    current_delay *= backoff

            # This should never be reached due to the raise in the loop,
            # but included for type safety
            if last_exception:
                raise last_exception
            return func(*args, **kwargs)  # type: ignore

        return wrapper

    return decorator


class LRUCache:
    """Thread-safe LRU (Least Recently Used) Cache implementation.

    This cache automatically evicts the least recently used items when
    the maximum size is reached.

    Attributes:
        maxsize: Maximum number of items to store
        ttl: Time-to-live in seconds (optional)

    Example:
        >>> cache = LRUCache(maxsize=100, ttl=300)
        >>> cache.set("key1", "value1")
        >>> value = cache.get("key1")
    """

    def __init__(self, maxsize: int = 128, ttl: Optional[float] = None):
        """Initialize the LRU cache.

        Args:
            maxsize: Maximum number of items (default: 128)
            ttl: Time-to-live in seconds (None = no expiration)
        """
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def _make_key(self, *args, **kwargs) -> str:
        """Create a hashable key from arguments."""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: The cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            # Check TTL
            if self.ttl is not None:
                if time.time() - self._timestamps.get(key, 0) > self.ttl:
                    del self._cache[key]
                    del self._timestamps[key]
                    self._misses += 1
                    return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
        """
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.maxsize:
                    # Remove oldest item
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    self._timestamps.pop(oldest_key, None)

            self._cache[key] = value
            self._timestamps[key] = time.time()

    def clear(self) -> None:
        """Clear all cached items."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {
                'size': len(self._cache),
                'maxsize': self.maxsize,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate
            }


def memoize(
    maxsize: int = 128,
    ttl: Optional[float] = None,
    key_func: Optional[Callable[..., str]] = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to cache function results with LRU eviction policy.

    This decorator caches the results of function calls based on their
    arguments. Useful for expensive computations that are called repeatedly
    with the same inputs.

    Args:
        maxsize: Maximum cache size (default: 128)
        ttl: Time-to-live in seconds (None = no expiration)
        key_func: Custom function to generate cache keys

    Returns:
        Decorated function with caching

    Example:
        >>> @memoize(maxsize=100, ttl=300)
        ... def expensive_computation(n: int) -> int:
        ...     time.sleep(1)  # Simulate expensive work
        ...     return n ** 2

        >>> result1 = expensive_computation(5)  # Takes 1 second
        >>> result2 = expensive_computation(5)  # Returns instantly from cache
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        cache = LRUCache(maxsize=maxsize, ttl=ttl)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = cache._make_key(*args, **kwargs)

            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result

            # Compute result
            result = func(*args, **kwargs)
            cache.set(key, result)
            logger.debug(f"Cache miss for {func.__name__}, result cached")

            return result

        # Attach cache to wrapper for external access
        wrapper.cache = cache  # type: ignore
        wrapper.cache_clear = cache.clear  # type: ignore
        wrapper.cache_stats = cache.stats  # type: ignore

        return wrapper

    return decorator


def cached_property_with_ttl(ttl: float = 300.0):
    """Cached property decorator with time-to-live.

    Similar to Python's @property but caches the computed value
    for a specified time period.

    Args:
        ttl: Time-to-live in seconds (default: 300)

    Returns:
        Property decorator with caching

    Example:
        >>> class DataProcessor:
        ...     @cached_property_with_ttl(ttl=60)
        ...     def expensive_data(self):
        ...         return compute_something()
    """
    def decorator(func: Callable) -> property:
        attr_name = f'_cached_{func.__name__}'
        timestamp_attr = f'_cached_ts_{func.__name__}'

        @functools.wraps(func)
        def wrapper(self):
            now = time.time()
            cached_time = getattr(self, timestamp_attr, 0)

            if now - cached_time > ttl or not hasattr(self, attr_name):
                setattr(self, attr_name, func(self))
                setattr(self, timestamp_attr, now)

            return getattr(self, attr_name)

        return property(wrapper)

    return decorator


# Convenience function to combine multiple decorators
def monitor(
    time_it: bool = True,
    profile_memory: bool = False,
    retry_config: Optional[dict] = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Convenience decorator to apply multiple monitoring decorators at once.

    Args:
        time_it: Whether to apply @timer decorator (default: True)
        profile_memory: Whether to apply @memory_profiler decorator (default: False)
        retry_config: Configuration dict for @retry decorator. If None, no retry.
                     Example: {"max_attempts": 3, "delay": 1.0, "backoff": 2.0}

    Returns:
        Combined decorator function

    Example:
        >>> @monitor(time_it=True, profile_memory=True)
        ... def process_data(data):
        ...     return analyze(data)

        >>> @monitor(
        ...     time_it=True,
        ...     profile_memory=True,
        ...     retry_config={"max_attempts": 3, "delay": 1.0}
        ... )
        ... def fetch_and_process():
        ...     data = fetch_data()
        ...     return process(data)
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        wrapped_func = func

        # Apply decorators in reverse order (innermost first)
        if retry_config:
            wrapped_func = retry(**retry_config)(wrapped_func)

        if profile_memory:
            wrapped_func = memory_profiler(wrapped_func)

        if time_it:
            wrapped_func = timer(wrapped_func)

        return wrapped_func

    return decorator


# Example usage and demonstrations
if __name__ == "__main__":
    import random

    # Configure logging for examples
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>\n"
    )

    print("=== Performance Monitoring Examples ===\n")

    # Example 1: Timer decorator
    print("1. Timer Decorator Example:")

    @timer
    def slow_computation(n: int) -> int:
        """Simulate a slow computation."""
        time.sleep(0.5)
        return sum(range(n))

    result = slow_computation(1000)
    print(f"Result: {result}\n")

    # Example 2: Memory profiler decorator
    print("2. Memory Profiler Example:")

    @memory_profiler
    def memory_intensive_task():
        """Create a large list."""
        data = [i ** 2 for i in range(1000000)]
        return len(data)

    length = memory_intensive_task()
    print(f"List length: {length}\n")

    # Example 3: Retry decorator
    print("3. Retry Decorator Example:")

    attempt_counter = {"count": 0}

    @retry(max_attempts=3, delay=0.5, backoff=2.0)
    def flaky_function():
        """Function that fails sometimes."""
        attempt_counter["count"] += 1
        if attempt_counter["count"] < 3:
            raise ConnectionError("Temporary failure")
        return "Success!"

    try:
        result = flaky_function()
        print(f"Result: {result}\n")
    except Exception as e:
        print(f"Failed: {e}\n")

    # Example 4: Combined monitoring
    print("4. Combined Monitoring Example:")

    @monitor(time_it=True, profile_memory=True, retry_config={"max_attempts": 2})
    def complex_operation(size: int):
        """Complex operation with all monitoring."""
        data = [random.random() for _ in range(size)]
        return sum(data) / len(data)

    avg = complex_operation(100000)
    print(f"Average: {avg:.6f}\n")

    # Example 5: Custom retry callback
    print("5. Retry with Custom Callback Example:")

    def custom_retry_handler(attempt: int, error: Exception):
        """Custom handler called on each retry."""
        logger.info(f"Custom handler: Attempt {attempt} failed with {type(error).__name__}")

    retry_attempt = {"count": 0}

    @retry(
        max_attempts=3,
        delay=0.3,
        exceptions=(ValueError, TypeError),
        on_retry=custom_retry_handler
    )
    def function_with_callback():
        """Function with custom retry callback."""
        retry_attempt["count"] += 1
        if retry_attempt["count"] < 2:
            raise ValueError("Not ready yet")
        return "Ready!"

    result = function_with_callback()
    print(f"Result: {result}\n")

    print("=== All Examples Completed ===")
