"""Advanced streaming capabilities for LLM responses.

This module provides comprehensive streaming support including:
- Token buffering and flushing
- Stream transformations (filter, map, aggregate)
- Parallel stream handling
- Multiple output destinations (file, callback, queue)
- Progress estimation
- Stream recovery on connection drops
"""

import asyncio
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Deque,
    Dict,
    Iterator,
    List,
    Optional,
    Protocol,
    TypeVar,
    Union,
)
from queue import Queue
import logging

from ai_automation_framework.core.logger import get_logger


# Type variables for generic stream processing
T = TypeVar("T")
U = TypeVar("U")


class StreamState(Enum):
    """Enumeration of possible stream states."""

    IDLE = "idle"
    STREAMING = "streaming"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"
    RECOVERING = "recovering"


@dataclass
class StreamStats:
    """Statistics for stream processing."""

    total_tokens: int = 0
    total_chunks: int = 0
    bytes_processed: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    errors: int = 0
    recoveries: int = 0

    @property
    def duration(self) -> float:
        """Calculate stream duration."""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second rate."""
        duration = self.duration
        return self.total_tokens / duration if duration > 0 else 0.0

    @property
    def chunks_per_second(self) -> float:
        """Calculate chunks per second rate."""
        duration = self.duration
        return self.total_chunks / duration if duration > 0 else 0.0


@dataclass
class StreamConfig:
    """Configuration for stream processing."""

    # Buffering settings
    buffer_size: int = 10
    flush_interval: float = 0.1  # seconds
    flush_on_newline: bool = True

    # Recovery settings
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    exponential_backoff: bool = True

    # Progress estimation
    estimate_total_tokens: Optional[int] = None

    # Memory management
    max_memory_mb: Optional[float] = None

    # Timeout settings
    chunk_timeout: Optional[float] = 30.0  # seconds


class StreamDestination(Protocol):
    """Protocol for stream output destinations."""

    def write(self, data: str) -> None:
        """Write data to destination."""
        ...

    def flush(self) -> None:
        """Flush buffered data."""
        ...

    def close(self) -> None:
        """Close the destination."""
        ...


class FileDestination:
    """File-based stream destination."""

    def __init__(self, path: Union[str, Path], mode: str = "w", encoding: str = "utf-8"):
        """
        Initialize file destination.

        Args:
            path: File path to write to
            mode: File open mode
            encoding: File encoding
        """
        self.path = Path(path)
        self.mode = mode
        self.encoding = encoding
        self._file: Optional[Any] = None
        self._open()

    def _open(self) -> None:
        """Open the file for writing."""
        self._file = open(self.path, self.mode, encoding=self.encoding)

    def write(self, data: str) -> None:
        """Write data to file."""
        if self._file:
            self._file.write(data)

    def flush(self) -> None:
        """Flush buffered data to disk."""
        if self._file:
            self._file.flush()

    def close(self) -> None:
        """Close the file."""
        if self._file:
            self._file.close()
            self._file = None


class CallbackDestination:
    """Callback-based stream destination."""

    def __init__(self, callback: Callable[[str], None]):
        """
        Initialize callback destination.

        Args:
            callback: Function to call with each chunk
        """
        self.callback = callback

    def write(self, data: str) -> None:
        """Call callback with data."""
        self.callback(data)

    def flush(self) -> None:
        """No-op for callback destination."""
        pass

    def close(self) -> None:
        """No-op for callback destination."""
        pass


class QueueDestination:
    """Queue-based stream destination."""

    def __init__(self, queue: Queue):
        """
        Initialize queue destination.

        Args:
            queue: Queue to put data into
        """
        self.queue = queue

    def write(self, data: str) -> None:
        """Put data into queue."""
        self.queue.put(data)

    def flush(self) -> None:
        """No-op for queue destination."""
        pass

    def close(self) -> None:
        """Signal queue completion."""
        self.queue.put(None)  # Sentinel value


class StreamBuffer:
    """Buffer for accumulating stream chunks with configurable flushing."""

    def __init__(self, config: StreamConfig):
        """
        Initialize stream buffer.

        Args:
            config: Stream configuration
        """
        self.config = config
        self.buffer: Deque[str] = deque(maxlen=config.buffer_size)
        self.last_flush_time = time.time()
        self._total_size = 0

    def add(self, chunk: str) -> Optional[str]:
        """
        Add chunk to buffer.

        Args:
            chunk: Text chunk to add

        Returns:
            Flushed content if buffer should be flushed, None otherwise
        """
        self.buffer.append(chunk)
        self._total_size += len(chunk)

        should_flush = False

        # Check flush conditions
        if len(self.buffer) >= self.config.buffer_size:
            should_flush = True
        elif self.config.flush_on_newline and '\n' in chunk:
            should_flush = True
        elif (time.time() - self.last_flush_time) >= self.config.flush_interval:
            should_flush = True

        if should_flush:
            return self.flush()

        return None

    def flush(self) -> str:
        """
        Flush buffer and return contents.

        Returns:
            Buffered content
        """
        content = ''.join(self.buffer)
        self.buffer.clear()
        self._total_size = 0
        self.last_flush_time = time.time()
        return content

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self.buffer) == 0

    @property
    def size(self) -> int:
        """Get total buffer size in characters."""
        return self._total_size


class StreamTransform(ABC):
    """Base class for stream transformations."""

    @abstractmethod
    def transform(self, chunk: str) -> Optional[str]:
        """
        Transform a stream chunk.

        Args:
            chunk: Input chunk

        Returns:
            Transformed chunk or None to filter out
        """
        pass

    @abstractmethod
    async def atransform(self, chunk: str) -> Optional[str]:
        """
        Async transform a stream chunk.

        Args:
            chunk: Input chunk

        Returns:
            Transformed chunk or None to filter out
        """
        pass


class FilterTransform(StreamTransform):
    """Filter stream chunks based on a predicate."""

    def __init__(self, predicate: Callable[[str], bool]):
        """
        Initialize filter transform.

        Args:
            predicate: Function that returns True to keep chunk
        """
        self.predicate = predicate

    def transform(self, chunk: str) -> Optional[str]:
        """Filter chunk based on predicate."""
        return chunk if self.predicate(chunk) else None

    async def atransform(self, chunk: str) -> Optional[str]:
        """Async filter chunk based on predicate."""
        return chunk if self.predicate(chunk) else None


class MapTransform(StreamTransform):
    """Map stream chunks using a transformation function."""

    def __init__(self, mapper: Callable[[str], str]):
        """
        Initialize map transform.

        Args:
            mapper: Function to transform each chunk
        """
        self.mapper = mapper

    def transform(self, chunk: str) -> Optional[str]:
        """Map chunk using mapper function."""
        return self.mapper(chunk)

    async def atransform(self, chunk: str) -> Optional[str]:
        """Async map chunk using mapper function."""
        return self.mapper(chunk)


class AggregateTransform(StreamTransform):
    """Aggregate stream chunks before emitting."""

    def __init__(
        self,
        aggregator: Callable[[List[str]], str],
        window_size: int = 5
    ):
        """
        Initialize aggregate transform.

        Args:
            aggregator: Function to aggregate chunks
            window_size: Number of chunks to aggregate
        """
        self.aggregator = aggregator
        self.window_size = window_size
        self.window: List[str] = []

    def transform(self, chunk: str) -> Optional[str]:
        """Aggregate chunks in a sliding window."""
        self.window.append(chunk)

        if len(self.window) >= self.window_size:
            result = self.aggregator(self.window)
            self.window = []
            return result

        return None

    async def atransform(self, chunk: str) -> Optional[str]:
        """Async aggregate chunks in a sliding window."""
        return self.transform(chunk)

    def finalize(self) -> Optional[str]:
        """Finalize any remaining chunks in the window."""
        if self.window:
            result = self.aggregator(self.window)
            self.window = []
            return result
        return None


class ProgressEstimator:
    """Estimate progress based on token count."""

    def __init__(self, estimated_total: Optional[int] = None):
        """
        Initialize progress estimator.

        Args:
            estimated_total: Estimated total tokens (if known)
        """
        self.estimated_total = estimated_total
        self.current_tokens = 0
        self.start_time = time.time()

    def update(self, token_count: int) -> None:
        """
        Update progress with new tokens.

        Args:
            token_count: Number of new tokens
        """
        self.current_tokens += token_count

    @property
    def percentage(self) -> Optional[float]:
        """Get completion percentage (0-100)."""
        if self.estimated_total and self.estimated_total > 0:
            return min(100.0, (self.current_tokens / self.estimated_total) * 100)
        return None

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time

    @property
    def estimated_remaining_time(self) -> Optional[float]:
        """Estimate remaining time in seconds."""
        if not self.estimated_total or self.current_tokens == 0:
            return None

        rate = self.current_tokens / self.elapsed_time
        remaining_tokens = self.estimated_total - self.current_tokens

        if rate > 0:
            return remaining_tokens / rate

        return None

    def get_progress_info(self) -> Dict[str, Any]:
        """
        Get comprehensive progress information.

        Returns:
            Dictionary with progress metrics
        """
        return {
            "current_tokens": self.current_tokens,
            "estimated_total": self.estimated_total,
            "percentage": self.percentage,
            "elapsed_time": self.elapsed_time,
            "estimated_remaining_time": self.estimated_remaining_time,
            "tokens_per_second": self.current_tokens / self.elapsed_time if self.elapsed_time > 0 else 0,
        }


class StreamProcessor:
    """
    Main stream processor for handling LLM streaming responses.

    Supports:
    - Token buffering with configurable flush intervals
    - Stream transformations (filter, map, aggregate)
    - Multiple output destinations
    - Progress estimation
    - Stream recovery on connection drops
    """

    def __init__(
        self,
        config: Optional[StreamConfig] = None,
        destinations: Optional[List[StreamDestination]] = None,
        transforms: Optional[List[StreamTransform]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize stream processor.

        Args:
            config: Stream configuration
            destinations: List of output destinations
            transforms: List of stream transformations
            logger: Custom logger instance
        """
        self.config = config or StreamConfig()
        self.destinations = destinations or []
        self.transforms = transforms or []
        self.logger = logger or get_logger("StreamProcessor")

        self.buffer = StreamBuffer(self.config)
        self.stats = StreamStats()
        self.progress = ProgressEstimator(self.config.estimate_total_tokens)
        self.state = StreamState.IDLE

        self._recovery_attempts = 0

    def add_destination(self, destination: StreamDestination) -> None:
        """Add an output destination."""
        self.destinations.append(destination)

    def add_transform(self, transform: StreamTransform) -> None:
        """Add a stream transformation."""
        self.transforms.append(transform)

    def _apply_transforms(self, chunk: str) -> Optional[str]:
        """Apply all transformations to a chunk."""
        result = chunk

        for transform in self.transforms:
            if result is None:
                break
            result = transform.transform(result)

        return result

    async def _apply_transforms_async(self, chunk: str) -> Optional[str]:
        """Apply all transformations to a chunk asynchronously."""
        result = chunk

        for transform in self.transforms:
            if result is None:
                break
            result = await transform.atransform(result)

        return result

    def _write_to_destinations(self, data: str) -> None:
        """Write data to all destinations."""
        for destination in self.destinations:
            try:
                destination.write(data)
            except Exception as e:
                self.logger.error(f"Error writing to destination: {e}")

    def _flush_destinations(self) -> None:
        """Flush all destinations."""
        for destination in self.destinations:
            try:
                destination.flush()
            except Exception as e:
                self.logger.error(f"Error flushing destination: {e}")

    def _close_destinations(self) -> None:
        """Close all destinations."""
        for destination in self.destinations:
            try:
                destination.close()
            except Exception as e:
                self.logger.error(f"Error closing destination: {e}")

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count from text.

        Simple estimation: ~4 characters per token on average.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        return max(1, len(text) // 4)

    def _should_recover(self) -> bool:
        """Check if stream recovery should be attempted."""
        return (
            self._recovery_attempts < self.config.max_retries
            and self.state == StreamState.ERROR
        )

    def _get_retry_delay(self) -> float:
        """Get delay before next retry with exponential backoff."""
        delay = self.config.retry_delay

        if self.config.exponential_backoff:
            delay *= (2 ** self._recovery_attempts)

        return delay

    def process_stream(
        self,
        stream: Iterator[str],
        yield_chunks: bool = True,
    ) -> Iterator[str]:
        """
        Process a synchronous stream.

        Args:
            stream: Input stream iterator
            yield_chunks: Whether to yield chunks as they're processed

        Yields:
            Processed stream chunks
        """
        self.state = StreamState.STREAMING
        self.stats = StreamStats()

        try:
            for chunk in stream:
                # Update statistics
                self.stats.total_chunks += 1
                self.stats.bytes_processed += len(chunk.encode('utf-8'))

                # Estimate tokens
                tokens = self._estimate_tokens(chunk)
                self.stats.total_tokens += tokens
                self.progress.update(tokens)

                # Apply transformations
                transformed = self._apply_transforms(chunk)

                if transformed is None:
                    continue

                # Add to buffer
                flushed = self.buffer.add(transformed)

                if flushed:
                    self._write_to_destinations(flushed)
                    if yield_chunks:
                        yield flushed
                elif yield_chunks and transformed:
                    # Yield even if not flushed for real-time streaming
                    yield transformed

            # Flush remaining buffer
            if not self.buffer.is_empty():
                final = self.buffer.flush()
                self._write_to_destinations(final)
                if yield_chunks:
                    yield final

            # Finalize aggregate transforms
            for transform in self.transforms:
                if isinstance(transform, AggregateTransform):
                    final_chunk = transform.finalize()
                    if final_chunk:
                        self._write_to_destinations(final_chunk)
                        if yield_chunks:
                            yield final_chunk

            self.state = StreamState.COMPLETED
            self.stats.end_time = time.time()

        except Exception as e:
            self.state = StreamState.ERROR
            self.stats.errors += 1
            self.logger.error(f"Stream processing error: {e}")
            raise

        finally:
            self._flush_destinations()

    async def aprocess_stream(
        self,
        stream: AsyncIterator[str],
        yield_chunks: bool = True,
    ) -> AsyncIterator[str]:
        """
        Process an asynchronous stream.

        Args:
            stream: Input async stream iterator
            yield_chunks: Whether to yield chunks as they're processed

        Yields:
            Processed stream chunks
        """
        self.state = StreamState.STREAMING
        self.stats = StreamStats()

        try:
            async for chunk in stream:
                # Update statistics
                self.stats.total_chunks += 1
                self.stats.bytes_processed += len(chunk.encode('utf-8'))

                # Estimate tokens
                tokens = self._estimate_tokens(chunk)
                self.stats.total_tokens += tokens
                self.progress.update(tokens)

                # Apply transformations
                transformed = await self._apply_transforms_async(chunk)

                if transformed is None:
                    continue

                # Add to buffer
                flushed = self.buffer.add(transformed)

                if flushed:
                    self._write_to_destinations(flushed)
                    if yield_chunks:
                        yield flushed
                elif yield_chunks and transformed:
                    # Yield even if not flushed for real-time streaming
                    yield transformed

            # Flush remaining buffer
            if not self.buffer.is_empty():
                final = self.buffer.flush()
                self._write_to_destinations(final)
                if yield_chunks:
                    yield final

            # Finalize aggregate transforms
            for transform in self.transforms:
                if isinstance(transform, AggregateTransform):
                    final_chunk = transform.finalize()
                    if final_chunk:
                        self._write_to_destinations(final_chunk)
                        if yield_chunks:
                            yield final_chunk

            self.state = StreamState.COMPLETED
            self.stats.end_time = time.time()

        except Exception as e:
            self.state = StreamState.ERROR
            self.stats.errors += 1
            self.logger.error(f"Stream processing error: {e}")
            raise

        finally:
            self._flush_destinations()

    async def aprocess_stream_with_recovery(
        self,
        stream_factory: Callable[[], AsyncIterator[str]],
        yield_chunks: bool = True,
    ) -> AsyncIterator[str]:
        """
        Process stream with automatic recovery on connection drops.

        Args:
            stream_factory: Factory function to create new stream on recovery
            yield_chunks: Whether to yield chunks as they're processed

        Yields:
            Processed stream chunks
        """
        while True:
            try:
                stream = stream_factory()

                async for chunk in self.aprocess_stream(stream, yield_chunks):
                    yield chunk

                # Successfully completed
                break

            except Exception as e:
                self.logger.warning(f"Stream error, attempting recovery: {e}")

                if not self._should_recover():
                    self.logger.error("Max recovery attempts reached")
                    raise

                self.state = StreamState.RECOVERING
                self.stats.recoveries += 1
                self._recovery_attempts += 1

                # Wait before retry
                delay = self._get_retry_delay()
                self.logger.info(f"Retrying in {delay:.1f} seconds (attempt {self._recovery_attempts}/{self.config.max_retries})")
                await asyncio.sleep(delay)

                # Reset for retry
                self.state = StreamState.IDLE

    def get_stats(self) -> StreamStats:
        """Get current stream statistics."""
        return self.stats

    def get_progress(self) -> Dict[str, Any]:
        """Get current progress information."""
        return self.progress.get_progress_info()

    def close(self) -> None:
        """Close processor and all destinations."""
        self._close_destinations()


class ParallelStreamProcessor:
    """Process multiple LLM streams in parallel."""

    def __init__(
        self,
        config: Optional[StreamConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize parallel stream processor.

        Args:
            config: Stream configuration for all processors
            logger: Custom logger instance
        """
        self.config = config or StreamConfig()
        self.logger = logger or get_logger("ParallelStreamProcessor")
        self.processors: List[StreamProcessor] = []

    async def process_parallel(
        self,
        streams: List[AsyncIterator[str]],
        destinations_per_stream: Optional[List[List[StreamDestination]]] = None,
    ) -> List[StreamStats]:
        """
        Process multiple streams in parallel.

        Args:
            streams: List of async stream iterators
            destinations_per_stream: Optional destinations for each stream

        Returns:
            List of statistics for each stream
        """
        if destinations_per_stream is None:
            destinations_per_stream = [[] for _ in streams]

        # Create processor for each stream
        self.processors = [
            StreamProcessor(
                config=self.config,
                destinations=destinations,
                logger=self.logger,
            )
            for destinations in destinations_per_stream
        ]

        # Process all streams concurrently
        tasks = [
            self._process_single(processor, stream, idx)
            for idx, (processor, stream) in enumerate(zip(self.processors, streams))
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect statistics
        stats = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Stream {idx} failed: {result}")
                stats.append(StreamStats())
            else:
                stats.append(result)

        return stats

    async def _process_single(
        self,
        processor: StreamProcessor,
        stream: AsyncIterator[str],
        index: int,
    ) -> StreamStats:
        """
        Process a single stream.

        Args:
            processor: Stream processor to use
            stream: Stream to process
            index: Stream index for logging

        Returns:
            Stream statistics
        """
        self.logger.info(f"Starting stream {index}")

        async for _ in processor.aprocess_stream(stream, yield_chunks=False):
            pass  # Just consume the stream

        self.logger.info(f"Completed stream {index}")
        return processor.get_stats()

    def get_aggregate_stats(self) -> Dict[str, Any]:
        """
        Get aggregate statistics across all streams.

        Returns:
            Dictionary with aggregate statistics
        """
        if not self.processors:
            return {}

        total_tokens = sum(p.stats.total_tokens for p in self.processors)
        total_chunks = sum(p.stats.total_chunks for p in self.processors)
        total_bytes = sum(p.stats.bytes_processed for p in self.processors)
        total_errors = sum(p.stats.errors for p in self.processors)

        durations = [p.stats.duration for p in self.processors]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)

        return {
            "num_streams": len(self.processors),
            "total_tokens": total_tokens,
            "total_chunks": total_chunks,
            "total_bytes": total_bytes,
            "total_errors": total_errors,
            "avg_duration": avg_duration,
            "max_duration": max_duration,
            "avg_tokens_per_second": total_tokens / avg_duration if avg_duration > 0 else 0,
        }


# Convenience functions for common use cases

def create_file_processor(
    file_path: Union[str, Path],
    config: Optional[StreamConfig] = None,
) -> StreamProcessor:
    """
    Create a stream processor that writes to a file.

    Args:
        file_path: Path to output file
        config: Stream configuration

    Returns:
        Configured StreamProcessor
    """
    destination = FileDestination(file_path)
    return StreamProcessor(config=config, destinations=[destination])


def create_callback_processor(
    callback: Callable[[str], None],
    config: Optional[StreamConfig] = None,
) -> StreamProcessor:
    """
    Create a stream processor with a callback destination.

    Args:
        callback: Callback function for each chunk
        config: Stream configuration

    Returns:
        Configured StreamProcessor
    """
    destination = CallbackDestination(callback)
    return StreamProcessor(config=config, destinations=[destination])


def create_queue_processor(
    queue: Queue,
    config: Optional[StreamConfig] = None,
) -> StreamProcessor:
    """
    Create a stream processor that writes to a queue.

    Args:
        queue: Queue to write chunks to
        config: Stream configuration

    Returns:
        Configured StreamProcessor
    """
    destination = QueueDestination(queue)
    return StreamProcessor(config=config, destinations=[destination])


async def merge_streams(
    *streams: AsyncIterator[str],
    separator: str = "",
) -> AsyncIterator[str]:
    """
    Merge multiple streams into a single stream.

    Args:
        *streams: Variable number of async iterators
        separator: Separator between stream chunks

    Yields:
        Merged stream chunks
    """
    for idx, stream in enumerate(streams):
        if idx > 0 and separator:
            yield separator

        async for chunk in stream:
            yield chunk


__all__ = [
    "StreamProcessor",
    "ParallelStreamProcessor",
    "StreamConfig",
    "StreamState",
    "StreamStats",
    "StreamDestination",
    "FileDestination",
    "CallbackDestination",
    "QueueDestination",
    "StreamTransform",
    "FilterTransform",
    "MapTransform",
    "AggregateTransform",
    "StreamBuffer",
    "ProgressEstimator",
    "create_file_processor",
    "create_callback_processor",
    "create_queue_processor",
    "merge_streams",
]
