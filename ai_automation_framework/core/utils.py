"""Utility functions for the AI Automation Framework."""

import asyncio
import functools
import json
import time
import threading
from typing import Any, Callable, List, Optional, TypeVar, Union
from ai_automation_framework.core.logger import get_logger


logger = get_logger(__name__)

T = TypeVar('T')


def retry(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff (delay = backoff_factor * (2 ** attempt))
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function called on each retry with (exception, attempt)

    Example:
        @retry(max_retries=3, backoff_factor=0.5)
        def unstable_function():
            # Function that might fail
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise

                    delay = backoff_factor * (2 ** attempt)
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {delay:.2f}s... Error: {e}"
                    )

                    if on_retry:
                        on_retry(e, attempt + 1)

                    time.sleep(delay)

            # This should never be reached, but for type safety
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def async_retry(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator to retry an async function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff (delay = backoff_factor * (2 ** attempt))
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function called on each retry with (exception, attempt)

    Example:
        @async_retry(max_retries=3, backoff_factor=0.5)
        async def unstable_async_function():
            # Async function that might fail
            pass
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"Async function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise

                    delay = backoff_factor * (2 ** attempt)
                    logger.warning(
                        f"Async function {func.__name__} failed (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {delay:.2f}s... Error: {e}"
                    )

                    if on_retry:
                        on_retry(e, attempt + 1)

                    await asyncio.sleep(delay)

            # This should never be reached, but for type safety
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def timeout(seconds: float):
    """
    Decorator to add timeout to function execution.

    Args:
        seconds: Maximum execution time in seconds

    Example:
        @timeout(5.0)
        def slow_function():
            # Function that might take too long
            pass

    Raises:
        TimeoutError: If function execution exceeds timeout
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            result = [None]
            exception = [None]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=seconds)

            if thread.is_alive():
                logger.error(f"Function {func.__name__} timed out after {seconds}s")
                raise TimeoutError(
                    f"Function {func.__name__} execution exceeded timeout of {seconds}s"
                )

            if exception[0]:
                raise exception[0]

            return result[0]

        return wrapper
    return decorator


class RateLimiter:
    """
    Token bucket rate limiter for controlling function call rates.

    Implements the token bucket algorithm to limit the rate of operations.
    Tokens are added to the bucket at a constant rate, and operations
    consume tokens. If no tokens are available, the operation blocks.

    Example:
        limiter = RateLimiter(rate=10, capacity=20)  # 10 tokens/sec, max 20 tokens

        @limiter.limit
        def api_call():
            # This function will be rate limited
            pass
    """

    def __init__(self, rate: float, capacity: Optional[int] = None):
        """
        Initialize rate limiter.

        Args:
            rate: Rate of token generation (tokens per second)
            capacity: Maximum bucket capacity (defaults to rate if not specified)
        """
        self.rate = rate
        self.capacity = capacity if capacity is not None else int(rate)
        self.tokens = float(self.capacity)
        self.last_update = time.time()
        self.lock = threading.Lock()

        logger.debug(f"Initialized RateLimiter: rate={rate}/s, capacity={self.capacity}")

    def _add_tokens(self) -> None:
        """Add tokens based on elapsed time since last update."""
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_update = now

    def acquire(self, tokens: int = 1, blocking: bool = True) -> bool:
        """
        Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire
            blocking: If True, wait for tokens to be available. If False, return immediately

        Returns:
            True if tokens were acquired, False otherwise
        """
        with self.lock:
            self._add_tokens()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            if not blocking:
                return False

            # Calculate wait time
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.rate

        # Wait outside the lock
        logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s for tokens")
        time.sleep(wait_time)

        # Try again after waiting
        with self.lock:
            self._add_tokens()
            self.tokens -= tokens
            return True

    def limit(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator to rate limit a function.

        Example:
            limiter = RateLimiter(rate=5)

            @limiter.limit
            def rate_limited_function():
                pass
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            self.acquire()
            return func(*args, **kwargs)

        return wrapper

    async def async_limit(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator to rate limit an async function.

        Example:
            limiter = RateLimiter(rate=5)

            @limiter.async_limit
            async def rate_limited_async_function():
                pass
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # For async, we need to handle waiting differently
            while not self.acquire(blocking=False):
                await asyncio.sleep(0.1)

            return await func(*args, **kwargs)

        return wrapper

    def wait_for_token(self) -> None:
        """
        Wait until a token is available and consume it.

        This is a compatibility alias for acquire() that blocks until
        a token is available. Used for backwards compatibility with
        code that expects the wait_for_token() interface.
        """
        self.acquire(tokens=1, blocking=True)


def chunk_list(items: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split a list into chunks of specified size.

    Args:
        items: List to split into chunks
        chunk_size: Maximum size of each chunk

    Returns:
        List of chunked lists

    Example:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    chunks = []
    for i in range(0, len(items), chunk_size):
        chunks.append(items[i:i + chunk_size])

    return chunks


def safe_json_loads(
    json_string: str,
    default: Any = None,
    log_errors: bool = True
) -> Any:
    """
    Safely parse JSON string with default fallback on failure.

    Args:
        json_string: JSON string to parse
        default: Default value to return on parse failure
        log_errors: Whether to log parsing errors

    Returns:
        Parsed JSON object or default value

    Example:
        >>> safe_json_loads('{"key": "value"}')
        {'key': 'value'}
        >>> safe_json_loads('invalid json', default={})
        {}
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        if log_errors:
            logger.warning(f"Failed to parse JSON: {e}. Returning default value.")
        return default


def truncate_string(
    text: str,
    max_length: int,
    ellipsis: str = "...",
    position: str = "end"
) -> str:
    """
    Truncate string to maximum length with ellipsis.

    Args:
        text: String to truncate
        max_length: Maximum length including ellipsis
        ellipsis: String to use for ellipsis (default: "...")
        position: Where to truncate - "end", "middle", or "start"

    Returns:
        Truncated string with ellipsis if needed

    Example:
        >>> truncate_string("Hello World", 8)
        "Hello..."
        >>> truncate_string("Hello World", 8, position="middle")
        "Hel...ld"
        >>> truncate_string("Hello World", 8, position="start")
        "...World"
    """
    if len(text) <= max_length:
        return text

    if max_length < len(ellipsis):
        return text[:max_length]

    if position == "end":
        return text[:max_length - len(ellipsis)] + ellipsis

    elif position == "start":
        return ellipsis + text[-(max_length - len(ellipsis)):]

    elif position == "middle":
        # Calculate how much text to keep on each side
        available_length = max_length - len(ellipsis)
        left_length = available_length // 2
        right_length = available_length - left_length

        return text[:left_length] + ellipsis + text[-right_length:]

    else:
        raise ValueError(f"Invalid position: {position}. Must be 'end', 'middle', or 'start'")


def format_bytes(size_bytes: Union[int, float]) -> str:
    """
    Format bytes into human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB", "500 KB")

    Example:
        >>> format_bytes(1536)
        "1.50 KB"
        >>> format_bytes(1048576)
        "1.00 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.2f} PB"


def merge_dicts(*dicts: dict, deep: bool = False) -> dict:
    """
    Merge multiple dictionaries into one.

    Args:
        *dicts: Dictionaries to merge
        deep: If True, perform deep merge (nested dicts are merged recursively)

    Returns:
        Merged dictionary

    Example:
        >>> merge_dicts({'a': 1}, {'b': 2})
        {'a': 1, 'b': 2}
        >>> merge_dicts({'a': {'x': 1}}, {'a': {'y': 2}}, deep=True)
        {'a': {'x': 1, 'y': 2}}
    """
    if not dicts:
        return {}

    if not deep:
        result = {}
        for d in dicts:
            result.update(d)
        return result

    # Deep merge
    result = {}
    for d in dicts:
        for key, value in d.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value, deep=True)
            else:
                result[key] = value

    return result
