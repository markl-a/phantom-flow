"""
Comprehensive caching layer with LRU, TTL, async support, and optional Redis backend.

This module provides a flexible caching system with:
- In-memory LRU cache with TTL support
- Function result caching decorators (sync and async)
- Thread-safe operations
- Cache statistics (hits, misses, hit rate)
- Multiple invalidation methods
- Optional Redis backend with automatic fallback to in-memory
"""

import asyncio
import functools
import hashlib
import json
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union
from ai_automation_framework.core.logger import get_logger

# Optional Redis support
try:
    import redis
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = get_logger(__name__)

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class CacheEntry:
    """Represents a single cache entry with metadata."""
    value: Any
    timestamp: float
    ttl: Optional[float] = None
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl

    def touch(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_accessed = time.time()


@dataclass
class CacheStats:
    """Cache statistics for monitoring performance."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    expirations: int = 0

    @property
    def total_requests(self) -> int:
        """Total cache requests (hits + misses)."""
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as a percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100

    def reset(self) -> None:
        """Reset all statistics."""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.evictions = 0
        self.expirations = 0

    def to_dict(self) -> Dict[str, Union[int, float]]:
        """Convert statistics to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "total_requests": self.total_requests,
            "hit_rate": round(self.hit_rate, 2),
        }


class LRUCache:
    """
    Thread-safe in-memory LRU cache with TTL support.

    Features:
    - Least Recently Used eviction policy
    - Per-entry TTL support
    - Thread-safe operations
    - Automatic cleanup of expired entries
    - Comprehensive statistics tracking
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[float] = None,
        cleanup_interval: float = 60.0
    ):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of entries in the cache
            default_ttl: Default time-to-live in seconds (None for no expiration)
            cleanup_interval: Interval in seconds for automatic cleanup of expired entries
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval

        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats()
        self._cleanup_task: Optional[threading.Thread] = None
        self._running = False

        logger.info(
            f"Initialized LRUCache with max_size={max_size}, "
            f"default_ttl={default_ttl}s, cleanup_interval={cleanup_interval}s"
        )

    def start_cleanup(self) -> None:
        """Start background cleanup thread for expired entries."""
        if self._cleanup_task is not None and self._cleanup_task.is_alive():
            return

        self._running = True
        self._cleanup_task = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_task.start()
        logger.info("Started cache cleanup thread")

    def stop_cleanup(self) -> None:
        """Stop background cleanup thread."""
        self._running = False
        if self._cleanup_task is not None:
            self._cleanup_task.join(timeout=5.0)
        logger.info("Stopped cache cleanup thread")

    def _cleanup_loop(self) -> None:
        """Background loop for cleaning up expired entries."""
        while self._running:
            try:
                time.sleep(self.cleanup_interval)
                self.cleanup_expired()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found or expired

        Returns:
            Cached value or default
        """
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                logger.debug(f"Cache miss: {key}")
                return default

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired():
                self._stats.misses += 1
                self._stats.expirations += 1
                del self._cache[key]
                logger.debug(f"Cache expired: {key}")
                return default

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            self._stats.hits += 1
            logger.debug(f"Cache hit: {key}")
            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default_ttl if None)
        """
        with self._lock:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.default_ttl

            # Check if we need to evict
            if key not in self._cache and len(self._cache) >= self.max_size:
                # Evict least recently used
                evicted_key, _ = self._cache.popitem(last=False)
                self._stats.evictions += 1
                logger.debug(f"Evicted LRU entry: {evicted_key}")

            # Add or update entry
            entry = CacheEntry(value=value, timestamp=time.time(), ttl=ttl)
            self._cache[key] = entry
            self._cache.move_to_end(key)
            self._stats.sets += 1
            logger.debug(f"Cache set: {key} (ttl={ttl}s)")

    def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """
        批量獲取緩存值，減少鎖開銷

        相比多次調用 get()，batch_get() 只需要獲取一次鎖，
        大幅減少鎖競爭和上下文切換開銷。

        Args:
            keys: 要獲取的鍵列表

        Returns:
            字典，包含找到的鍵值對（過期和不存在的鍵會被排除）

        Example:
            >>> cache = LRUCache()
            >>> cache.set("key1", "value1")
            >>> cache.set("key2", "value2")
            >>> results = cache.batch_get(["key1", "key2", "key3"])
            >>> # results = {"key1": "value1", "key2": "value2"}
            >>> # "key3" not in results (not found)
        """
        results = {}

        with self._lock:
            for key in keys:
                if key not in self._cache:
                    self._stats.misses += 1
                    continue

                entry = self._cache[key]

                # Check expiration
                if entry.is_expired():
                    self._stats.misses += 1
                    self._stats.expirations += 1
                    del self._cache[key]
                    continue

                # Move to end (most recently used)
                self._cache.move_to_end(key)
                entry.touch()
                self._stats.hits += 1
                results[key] = entry.value

        logger.debug(f"Batch get: {len(keys)} keys requested, {len(results)} found")
        return results

    def batch_set(self, items: Dict[str, Any], ttl: Optional[float] = None) -> None:
        """
        批量設置緩存值

        相比多次調用 set()，batch_set() 只需要獲取一次鎖，
        並且可以更高效地處理驅逐邏輯。

        Args:
            items: 要設置的鍵值對字典
            ttl: 所有項目的 TTL（秒），None 使用默認 TTL

        Example:
            >>> cache = LRUCache()
            >>> items = {
            ...     "key1": "value1",
            ...     "key2": "value2",
            ...     "key3": "value3"
            ... }
            >>> cache.batch_set(items, ttl=300)
        """
        with self._lock:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.default_ttl

            for key, value in items.items():
                # Check if we need to evict
                if key not in self._cache and len(self._cache) >= self.max_size:
                    # Evict least recently used
                    evicted_key, _ = self._cache.popitem(last=False)
                    self._stats.evictions += 1
                    logger.debug(f"Evicted LRU entry: {evicted_key}")

                # Add or update entry
                entry = CacheEntry(value=value, timestamp=time.time(), ttl=ttl)
                self._cache[key] = entry
                self._cache.move_to_end(key)
                self._stats.sets += 1

        logger.debug(f"Batch set: {len(items)} items (ttl={ttl}s)")

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.deletes += 1
                logger.debug(f"Cache delete: {key}")
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cleared {count} cache entries")

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of expired entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                del self._cache[key]
                self._stats.expirations += 1

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired entries")

            return len(expired_keys)

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern (simple substring match).

        Args:
            pattern: Pattern to match against keys

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            matching_keys = [key for key in self._cache if pattern in key]
            for key in matching_keys:
                del self._cache[key]
                self._stats.deletes += 1

            if matching_keys:
                logger.info(f"Invalidated {len(matching_keys)} entries matching '{pattern}'")

            return len(matching_keys)

    def get_stats(self) -> Dict[str, Union[int, float]]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            stats = self._stats.to_dict()
            stats.update({
                "size": len(self._cache),
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
            })
            return stats

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        with self._lock:
            self._stats.reset()
            logger.info("Reset cache statistics")

    def __len__(self) -> int:
        """Return number of entries in cache."""
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache (doesn't update stats)."""
        with self._lock:
            if key not in self._cache:
                return False
            entry = self._cache[key]
            return not entry.is_expired()


class AsyncLRUCache:
    """
    Async wrapper around LRUCache for use in async contexts.

    Provides async-compatible interface while maintaining thread-safety.
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[float] = None,
        cleanup_interval: float = 60.0
    ):
        """
        Initialize async LRU cache.

        Args:
            max_size: Maximum number of entries in the cache
            default_ttl: Default time-to-live in seconds
            cleanup_interval: Interval in seconds for cleanup
        """
        self._cache = LRUCache(max_size, default_ttl, cleanup_interval)
        self._lock = asyncio.Lock()

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache (async)."""
        async with self._lock:
            return await asyncio.to_thread(self._cache.get, key, default)

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache (async)."""
        async with self._lock:
            await asyncio.to_thread(self._cache.set, key, value, ttl)

    async def delete(self, key: str) -> bool:
        """Delete entry from cache (async)."""
        async with self._lock:
            return await asyncio.to_thread(self._cache.delete, key)

    async def clear(self) -> None:
        """Clear all entries from cache (async)."""
        async with self._lock:
            await asyncio.to_thread(self._cache.clear)

    async def cleanup_expired(self) -> int:
        """Remove expired entries (async)."""
        async with self._lock:
            return await asyncio.to_thread(self._cache.cleanup_expired)

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate entries matching pattern (async)."""
        async with self._lock:
            return await asyncio.to_thread(self._cache.invalidate_pattern, pattern)

    async def get_stats(self) -> Dict[str, Union[int, float]]:
        """Get cache statistics (async)."""
        async with self._lock:
            return await asyncio.to_thread(self._cache.get_stats)

    async def reset_stats(self) -> None:
        """Reset cache statistics (async)."""
        async with self._lock:
            await asyncio.to_thread(self._cache.reset_stats)

    def start_cleanup(self) -> None:
        """Start background cleanup."""
        self._cache.start_cleanup()

    def stop_cleanup(self) -> None:
        """Stop background cleanup."""
        self._cache.stop_cleanup()


class RedisCache:
    """
    Redis-backed cache with fallback to in-memory LRU cache.

    Automatically falls back to in-memory cache if Redis is unavailable.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_size: int = 1000,
        default_ttl: Optional[float] = None,
        key_prefix: str = "cache:",
        fallback_to_memory: bool = True
    ):
        """
        Initialize Redis cache with optional fallback.

        Args:
            redis_url: Redis connection URL
            max_size: Maximum size for fallback in-memory cache
            default_ttl: Default time-to-live in seconds
            key_prefix: Prefix for all Redis keys
            fallback_to_memory: Use in-memory cache if Redis unavailable
        """
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.fallback_to_memory = fallback_to_memory

        self._redis: Optional[redis.Redis] = None
        self._fallback_cache: Optional[LRUCache] = None
        self._stats = CacheStats()
        self._using_fallback = False

        if not REDIS_AVAILABLE:
            logger.warning("Redis library not available, using in-memory cache")
            self._using_fallback = True
            self._fallback_cache = LRUCache(max_size, default_ttl)
        else:
            try:
                self._redis = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self._redis.ping()
                logger.info(f"Connected to Redis at {redis_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                if fallback_to_memory:
                    logger.info("Falling back to in-memory cache")
                    self._using_fallback = True
                    self._fallback_cache = LRUCache(max_size, default_ttl)
                else:
                    raise

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.key_prefix}{key}"

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        if self._using_fallback:
            return self._fallback_cache.get(key, default)

        try:
            redis_key = self._make_key(key)
            value = self._redis.get(redis_key)

            if value is None:
                self._stats.misses += 1
                return default

            self._stats.hits += 1
            # Deserialize JSON
            return json.loads(value)

        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self._stats.misses += 1
            return default

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache."""
        if self._using_fallback:
            self._fallback_cache.set(key, value, ttl)
            return

        try:
            redis_key = self._make_key(key)
            serialized = json.dumps(value)

            if ttl is None:
                ttl = self.default_ttl

            if ttl:
                self._redis.setex(redis_key, int(ttl), serialized)
            else:
                self._redis.set(redis_key, serialized)

            self._stats.sets += 1

        except Exception as e:
            logger.error(f"Redis set error: {e}")

    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        if self._using_fallback:
            return self._fallback_cache.delete(key)

        try:
            redis_key = self._make_key(key)
            deleted = self._redis.delete(redis_key)
            if deleted:
                self._stats.deletes += 1
            return bool(deleted)

        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    def clear(self) -> None:
        """Clear all entries with the key prefix."""
        if self._using_fallback:
            self._fallback_cache.clear()
            return

        try:
            pattern = f"{self.key_prefix}*"
            keys = list(self._redis.scan_iter(match=pattern))
            if keys:
                self._redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")

        except Exception as e:
            logger.error(f"Redis clear error: {e}")

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern."""
        if self._using_fallback:
            return self._fallback_cache.invalidate_pattern(pattern)

        try:
            redis_pattern = f"{self.key_prefix}*{pattern}*"
            keys = list(self._redis.scan_iter(match=redis_pattern))
            if keys:
                deleted = self._redis.delete(*keys)
                self._stats.deletes += deleted
                logger.info(f"Invalidated {deleted} entries matching '{pattern}'")
                return deleted
            return 0

        except Exception as e:
            logger.error(f"Redis invalidate_pattern error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Union[int, float, str]]:
        """Get cache statistics."""
        stats = self._stats.to_dict()
        stats["backend"] = "fallback" if self._using_fallback else "redis"
        stats["redis_url"] = self.redis_url if not self._using_fallback else "N/A"

        if self._using_fallback:
            stats.update(self._fallback_cache.get_stats())

        return stats

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._stats.reset()
        if self._using_fallback:
            self._fallback_cache.reset_stats()


class AsyncRedisCache:
    """Async Redis cache with fallback to async in-memory cache."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_size: int = 1000,
        default_ttl: Optional[float] = None,
        key_prefix: str = "cache:",
        fallback_to_memory: bool = True
    ):
        """Initialize async Redis cache."""
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.fallback_to_memory = fallback_to_memory

        self._redis: Optional[aioredis.Redis] = None
        self._fallback_cache: Optional[AsyncLRUCache] = None
        self._stats = CacheStats()
        self._using_fallback = False
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure Redis connection is initialized."""
        if self._initialized:
            return

        if not REDIS_AVAILABLE:
            logger.warning("Redis library not available, using in-memory cache")
            self._using_fallback = True
            self._fallback_cache = AsyncLRUCache(
                max_size=1000,
                default_ttl=self.default_ttl
            )
        else:
            try:
                self._redis = await aioredis.from_url(
                    self.redis_url,
                    decode_responses=True
                )
                await self._redis.ping()
                logger.info(f"Connected to Redis at {self.redis_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                if self.fallback_to_memory:
                    logger.info("Falling back to in-memory cache")
                    self._using_fallback = True
                    self._fallback_cache = AsyncLRUCache(
                        max_size=1000,
                        default_ttl=self.default_ttl
                    )
                else:
                    raise

        self._initialized = True

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.key_prefix}{key}"

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache (async)."""
        await self._ensure_initialized()

        if self._using_fallback:
            return await self._fallback_cache.get(key, default)

        try:
            redis_key = self._make_key(key)
            value = await self._redis.get(redis_key)

            if value is None:
                self._stats.misses += 1
                return default

            self._stats.hits += 1
            return json.loads(value)

        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self._stats.misses += 1
            return default

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache (async)."""
        await self._ensure_initialized()

        if self._using_fallback:
            await self._fallback_cache.set(key, value, ttl)
            return

        try:
            redis_key = self._make_key(key)
            serialized = json.dumps(value)

            if ttl is None:
                ttl = self.default_ttl

            if ttl:
                await self._redis.setex(redis_key, int(ttl), serialized)
            else:
                await self._redis.set(redis_key, serialized)

            self._stats.sets += 1

        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def delete(self, key: str) -> bool:
        """Delete entry from cache (async)."""
        await self._ensure_initialized()

        if self._using_fallback:
            return await self._fallback_cache.delete(key)

        try:
            redis_key = self._make_key(key)
            deleted = await self._redis.delete(redis_key)
            if deleted:
                self._stats.deletes += 1
            return bool(deleted)

        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def clear(self) -> None:
        """Clear all entries (async)."""
        await self._ensure_initialized()

        if self._using_fallback:
            await self._fallback_cache.clear()
            return

        try:
            pattern = f"{self.key_prefix}*"
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await self._redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")

        except Exception as e:
            logger.error(f"Redis clear error: {e}")

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate entries matching pattern (async)."""
        await self._ensure_initialized()

        if self._using_fallback:
            return await self._fallback_cache.invalidate_pattern(pattern)

        try:
            redis_pattern = f"{self.key_prefix}*{pattern}*"
            keys = []
            async for key in self._redis.scan_iter(match=redis_pattern):
                keys.append(key)
            if keys:
                deleted = await self._redis.delete(*keys)
                self._stats.deletes += deleted
                logger.info(f"Invalidated {deleted} entries matching '{pattern}'")
                return deleted
            return 0

        except Exception as e:
            logger.error(f"Redis invalidate_pattern error: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Union[int, float, str]]:
        """Get cache statistics (async)."""
        await self._ensure_initialized()

        stats = self._stats.to_dict()
        stats["backend"] = "fallback" if self._using_fallback else "redis"
        stats["redis_url"] = self.redis_url if not self._using_fallback else "N/A"

        if self._using_fallback:
            fallback_stats = await self._fallback_cache.get_stats()
            stats.update(fallback_stats)

        return stats

    async def reset_stats(self) -> None:
        """Reset cache statistics (async)."""
        await self._ensure_initialized()

        self._stats.reset()
        if self._using_fallback:
            await self._fallback_cache.reset_stats()

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()


def _generate_cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Hash string to use as cache key
    """
    # Create a deterministic representation
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.sha256(key_str.encode()).hexdigest()


def cached(
    cache: Optional[LRUCache] = None,
    ttl: Optional[float] = None,
    key_func: Optional[Callable[..., str]] = None
) -> Callable[[F], F]:
    """
    Decorator for caching function results (synchronous functions).

    Args:
        cache: Cache instance to use (creates default if None)
        ttl: Time-to-live for cached results in seconds
        key_func: Optional custom function to generate cache keys

    Returns:
        Decorated function

    Example:
        >>> @cached(ttl=60)
        ... def expensive_function(x, y):
        ...     return x + y
    """
    if cache is None:
        cache = LRUCache()

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}.{func.__name__}:{_generate_cache_key(*args, **kwargs)}"

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        # Add cache control methods
        wrapper.cache = cache
        wrapper.cache_clear = cache.clear
        wrapper.cache_stats = cache.get_stats

        return wrapper

    return decorator


def async_cached(
    cache: Optional[AsyncLRUCache] = None,
    ttl: Optional[float] = None,
    key_func: Optional[Callable[..., str]] = None
) -> Callable[[F], F]:
    """
    Decorator for caching async function results.

    Args:
        cache: Async cache instance to use (creates default if None)
        ttl: Time-to-live for cached results in seconds
        key_func: Optional custom function to generate cache keys

    Returns:
        Decorated async function

    Example:
        >>> @async_cached(ttl=60)
        ... async def expensive_async_function(x, y):
        ...     await asyncio.sleep(1)
        ...     return x + y
    """
    if cache is None:
        cache = AsyncLRUCache()

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}.{func.__name__}:{_generate_cache_key(*args, **kwargs)}"

            # Try to get from cache
            result = await cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result

        # Add cache control methods
        wrapper.cache = cache
        wrapper.cache_clear = cache.clear
        wrapper.cache_stats = cache.get_stats

        return wrapper

    return decorator


# Global cache instances
_default_cache: Optional[LRUCache] = None
_default_async_cache: Optional[AsyncLRUCache] = None


def get_cache(
    max_size: int = 1000,
    default_ttl: Optional[float] = None
) -> LRUCache:
    """
    Get or create the default global cache instance.

    Args:
        max_size: Maximum cache size
        default_ttl: Default TTL in seconds

    Returns:
        Global LRUCache instance
    """
    global _default_cache

    if _default_cache is None:
        _default_cache = LRUCache(max_size=max_size, default_ttl=default_ttl)
        _default_cache.start_cleanup()

    return _default_cache


def get_async_cache(
    max_size: int = 1000,
    default_ttl: Optional[float] = None
) -> AsyncLRUCache:
    """
    Get or create the default global async cache instance.

    Args:
        max_size: Maximum cache size
        default_ttl: Default TTL in seconds

    Returns:
        Global AsyncLRUCache instance
    """
    global _default_async_cache

    if _default_async_cache is None:
        _default_async_cache = AsyncLRUCache(max_size=max_size, default_ttl=default_ttl)
        _default_async_cache.start_cleanup()

    return _default_async_cache


# Backwards compatibility with old ResponseCache
class ResponseCache:
    """
    Legacy response cache for LLM responses (disk-based).

    Maintained for backwards compatibility. Consider using the new
    LRUCache or RedisCache for better performance.
    """

    def __init__(
        self,
        cache_dir: str = "./cache",
        ttl_hours: int = 24,
        max_size_mb: int = 100
    ):
        """Initialize legacy response cache."""
        from pathlib import Path

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self.max_size_bytes = max_size_mb * 1024 * 1024

        logger.info(f"Initialized legacy ResponseCache at {self.cache_dir}")

    def _generate_key(
        self,
        prompt: str,
        model: str,
        temperature: float,
        **kwargs
    ) -> str:
        """Generate cache key from request parameters."""
        params = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            **kwargs
        }
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.sha256(param_str.encode()).hexdigest()

    def get(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        **kwargs
    ) -> Optional[str]:
        """Get cached response if available and not expired."""
        from pathlib import Path

        cache_key = self._generate_key(prompt, model, temperature, **kwargs)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                entry = json.load(f)

            cached_time = datetime.fromisoformat(entry['timestamp'])
            if datetime.now() - cached_time > self.ttl:
                cache_file.unlink()
                return None

            return entry['response']

        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None

    def set(
        self,
        prompt: str,
        response: str,
        model: str,
        temperature: float = 0.7,
        **kwargs
    ) -> None:
        """Cache a response."""
        cache_key = self._generate_key(prompt, model, temperature, **kwargs)
        cache_file = self.cache_dir / f"{cache_key}.json"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "model": model,
            "temperature": temperature,
            "params": kwargs
        }

        try:
            with open(cache_file, 'w') as f:
                json.dump(entry, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing cache: {e}")

    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)

            return {
                "total_entries": len(cache_files),
                "total_size_mb": total_size / 1024 / 1024,
                "cache_dir": str(self.cache_dir.absolute()),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"total_entries": 0, "total_size_mb": 0.0}


__all__ = [
    "LRUCache",
    "AsyncLRUCache",
    "RedisCache",
    "AsyncRedisCache",
    "CacheEntry",
    "CacheStats",
    "cached",
    "async_cached",
    "get_cache",
    "get_async_cache",
    "ResponseCache",  # Legacy
]
