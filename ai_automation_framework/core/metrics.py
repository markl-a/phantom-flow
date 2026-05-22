"""Metrics collection and monitoring system for the AI Automation Framework.

This module provides a comprehensive metrics collection system with support for
multiple metric types, thread-safe operations, and various export formats.
"""

import functools
import json
import psutil
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from ai_automation_framework.core.logger import get_logger


logger = get_logger(__name__)

T = TypeVar('T')


@dataclass
class MetricSnapshot:
    """Snapshot of a metric at a point in time."""

    name: str
    type: str
    value: Union[int, float, Dict[str, Any]]
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    help_text: str = ""


class Counter:
    """
    A counter metric that only increases.

    Counters are typically used for tracking cumulative values like
    total requests, total errors, etc.

    Thread-safe implementation using locks.

    Example:
        counter = Counter("http_requests_total", "Total HTTP requests")
        counter.inc()  # Increment by 1
        counter.inc(5)  # Increment by 5
    """

    def __init__(self, name: str, help_text: str = "", labels: Optional[Dict[str, str]] = None):
        """
        Initialize counter.

        Args:
            name: Metric name
            help_text: Description of what this metric measures
            labels: Optional labels for metric classification
        """
        self.name = name
        self.help_text = help_text
        self.labels = labels or {}
        self._value = 0.0
        self._lock = threading.Lock()

        logger.debug(f"Initialized Counter: {name}")

    def inc(self, amount: float = 1.0) -> None:
        """
        Increment counter by specified amount.

        Args:
            amount: Amount to increment (must be non-negative)

        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError("Counter increment must be non-negative")

        with self._lock:
            self._value += amount

    def get(self) -> float:
        """
        Get current counter value.

        Returns:
            Current counter value
        """
        with self._lock:
            return self._value

    def reset(self) -> None:
        """Reset counter to zero."""
        with self._lock:
            self._value = 0.0
            logger.debug(f"Reset Counter: {self.name}")

    def snapshot(self) -> MetricSnapshot:
        """
        Create a snapshot of current metric state.

        Returns:
            MetricSnapshot instance
        """
        return MetricSnapshot(
            name=self.name,
            type="counter",
            value=self.get(),
            timestamp=time.time(),
            labels=self.labels.copy(),
            help_text=self.help_text
        )


class Gauge:
    """
    A gauge metric that can go up and down.

    Gauges are typically used for tracking values that can increase or decrease,
    like active connections, memory usage, temperature, etc.

    Thread-safe implementation using locks.

    Example:
        gauge = Gauge("active_connections", "Number of active connections")
        gauge.set(10)
        gauge.inc()  # Now 11
        gauge.dec(5)  # Now 6
    """

    def __init__(self, name: str, help_text: str = "", labels: Optional[Dict[str, str]] = None):
        """
        Initialize gauge.

        Args:
            name: Metric name
            help_text: Description of what this metric measures
            labels: Optional labels for metric classification
        """
        self.name = name
        self.help_text = help_text
        self.labels = labels or {}
        self._value = 0.0
        self._lock = threading.Lock()

        logger.debug(f"Initialized Gauge: {name}")

    def set(self, value: float) -> None:
        """
        Set gauge to specific value.

        Args:
            value: Value to set
        """
        with self._lock:
            self._value = value

    def inc(self, amount: float = 1.0) -> None:
        """
        Increment gauge by specified amount.

        Args:
            amount: Amount to increment
        """
        with self._lock:
            self._value += amount

    def dec(self, amount: float = 1.0) -> None:
        """
        Decrement gauge by specified amount.

        Args:
            amount: Amount to decrement
        """
        with self._lock:
            self._value -= amount

    def get(self) -> float:
        """
        Get current gauge value.

        Returns:
            Current gauge value
        """
        with self._lock:
            return self._value

    def reset(self) -> None:
        """Reset gauge to zero."""
        with self._lock:
            self._value = 0.0
            logger.debug(f"Reset Gauge: {self.name}")

    def snapshot(self) -> MetricSnapshot:
        """
        Create a snapshot of current metric state.

        Returns:
            MetricSnapshot instance
        """
        return MetricSnapshot(
            name=self.name,
            type="gauge",
            value=self.get(),
            timestamp=time.time(),
            labels=self.labels.copy(),
            help_text=self.help_text
        )


class Histogram:
    """
    A histogram metric for tracking distributions.

    Histograms track the distribution of observations in configurable buckets
    and calculate summary statistics (count, sum, min, max, mean).

    Thread-safe implementation using locks.

    Example:
        histogram = Histogram("request_duration_seconds", "Request duration")
        histogram.observe(0.5)  # Record 0.5 seconds
        histogram.observe(1.2)  # Record 1.2 seconds
        stats = histogram.get_stats()  # Get summary statistics
    """

    # Default buckets for histogram (in seconds for duration tracking)
    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def __init__(
        self,
        name: str,
        help_text: str = "",
        labels: Optional[Dict[str, str]] = None,
        buckets: Optional[List[float]] = None
    ):
        """
        Initialize histogram.

        Args:
            name: Metric name
            help_text: Description of what this metric measures
            labels: Optional labels for metric classification
            buckets: Custom bucket boundaries (uses DEFAULT_BUCKETS if not provided)
        """
        self.name = name
        self.help_text = help_text
        self.labels = labels or {}
        self.buckets = sorted(buckets) if buckets else self.DEFAULT_BUCKETS

        self._count = 0
        self._sum = 0.0
        self._min = float('inf')
        self._max = float('-inf')
        self._bucket_counts = defaultdict(int)
        self._observations = []
        self._lock = threading.Lock()

        logger.debug(f"Initialized Histogram: {name} with {len(self.buckets)} buckets")

    def observe(self, value: float) -> None:
        """
        Record an observation.

        Args:
            value: Value to observe
        """
        with self._lock:
            self._count += 1
            self._sum += value
            self._min = min(self._min, value)
            self._max = max(self._max, value)
            self._observations.append(value)

            # Update bucket counts
            for bucket in self.buckets:
                if value <= bucket:
                    self._bucket_counts[bucket] += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics.

        Returns:
            Dictionary with count, sum, min, max, mean, and bucket distributions
        """
        with self._lock:
            if self._count == 0:
                return {
                    "count": 0,
                    "sum": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "mean": 0.0,
                    "buckets": {}
                }

            return {
                "count": self._count,
                "sum": self._sum,
                "min": self._min,
                "max": self._max,
                "mean": self._sum / self._count,
                "buckets": dict(self._bucket_counts)
            }

    def get_percentile(self, percentile: float) -> float:
        """
        Calculate percentile value.

        Args:
            percentile: Percentile to calculate (0-100)

        Returns:
            Value at the specified percentile
        """
        if not 0 <= percentile <= 100:
            raise ValueError("Percentile must be between 0 and 100")

        with self._lock:
            if not self._observations:
                return 0.0

            sorted_obs = sorted(self._observations)
            index = int((percentile / 100) * len(sorted_obs))
            index = min(index, len(sorted_obs) - 1)

            return sorted_obs[index]

    def reset(self) -> None:
        """Reset histogram to initial state."""
        with self._lock:
            self._count = 0
            self._sum = 0.0
            self._min = float('inf')
            self._max = float('-inf')
            self._bucket_counts.clear()
            self._observations.clear()
            logger.debug(f"Reset Histogram: {self.name}")

    def snapshot(self) -> MetricSnapshot:
        """
        Create a snapshot of current metric state.

        Returns:
            MetricSnapshot instance
        """
        stats = self.get_stats()

        # Add percentiles
        if self._count > 0:
            stats["p50"] = self.get_percentile(50)
            stats["p95"] = self.get_percentile(95)
            stats["p99"] = self.get_percentile(99)

        return MetricSnapshot(
            name=self.name,
            type="histogram",
            value=stats,
            timestamp=time.time(),
            labels=self.labels.copy(),
            help_text=self.help_text
        )


class MetricsRegistry:
    """
    Registry for managing all metrics.

    Implements singleton pattern to ensure a single global registry.
    Thread-safe implementation for concurrent access.

    Example:
        registry = MetricsRegistry.get_instance()
        counter = registry.counter("requests_total", "Total requests")
        counter.inc()
    """

    _instance: Optional['MetricsRegistry'] = None
    _lock = threading.Lock()

    def __init__(self):
        """Initialize metrics registry."""
        if MetricsRegistry._instance is not None:
            raise RuntimeError("Use get_instance() to get MetricsRegistry instance")

        self._metrics: Dict[str, Union[Counter, Gauge, Histogram]] = {}
        self._metrics_lock = threading.Lock()
        self._start_time = time.time()

        # Initialize system metrics
        self._init_system_metrics()

        logger.info("MetricsRegistry initialized")

    @classmethod
    def get_instance(cls) -> 'MetricsRegistry':
        """
        Get singleton instance of MetricsRegistry.

        Returns:
            MetricsRegistry instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()

        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (useful for testing)."""
        with cls._lock:
            cls._instance = None

    def _init_system_metrics(self) -> None:
        """Initialize system-level metrics."""
        # Memory metrics
        self.gauge("system_memory_bytes", "System memory usage in bytes")
        self.gauge("system_memory_percent", "System memory usage percentage")
        self.gauge("process_memory_bytes", "Process memory usage in bytes")

        # CPU metrics
        self.gauge("system_cpu_percent", "System CPU usage percentage")
        self.gauge("process_cpu_percent", "Process CPU usage percentage")

        # LLM metrics
        self.counter("llm_requests_total", "Total LLM requests")
        self.counter("llm_requests_success", "Successful LLM requests")
        self.counter("llm_requests_error", "Failed LLM requests")
        self.counter("llm_tokens_total", "Total tokens used")
        self.histogram("llm_request_duration_seconds", "LLM request duration")

        logger.debug("System metrics initialized")

    def counter(
        self,
        name: str,
        help_text: str = "",
        labels: Optional[Dict[str, str]] = None
    ) -> Counter:
        """
        Get or create a counter metric.

        Args:
            name: Metric name
            help_text: Description of the metric
            labels: Optional labels

        Returns:
            Counter instance
        """
        with self._metrics_lock:
            if name not in self._metrics:
                self._metrics[name] = Counter(name, help_text, labels)

            metric = self._metrics[name]

            if not isinstance(metric, Counter):
                raise TypeError(f"Metric {name} already exists as {type(metric).__name__}")

            return metric

    def gauge(
        self,
        name: str,
        help_text: str = "",
        labels: Optional[Dict[str, str]] = None
    ) -> Gauge:
        """
        Get or create a gauge metric.

        Args:
            name: Metric name
            help_text: Description of the metric
            labels: Optional labels

        Returns:
            Gauge instance
        """
        with self._metrics_lock:
            if name not in self._metrics:
                self._metrics[name] = Gauge(name, help_text, labels)

            metric = self._metrics[name]

            if not isinstance(metric, Gauge):
                raise TypeError(f"Metric {name} already exists as {type(metric).__name__}")

            return metric

    def histogram(
        self,
        name: str,
        help_text: str = "",
        labels: Optional[Dict[str, str]] = None,
        buckets: Optional[List[float]] = None
    ) -> Histogram:
        """
        Get or create a histogram metric.

        Args:
            name: Metric name
            help_text: Description of the metric
            labels: Optional labels
            buckets: Custom bucket boundaries

        Returns:
            Histogram instance
        """
        with self._metrics_lock:
            if name not in self._metrics:
                self._metrics[name] = Histogram(name, help_text, labels, buckets)

            metric = self._metrics[name]

            if not isinstance(metric, Histogram):
                raise TypeError(f"Metric {name} already exists as {type(metric).__name__}")

            return metric

    def get_metric(self, name: str) -> Optional[Union[Counter, Gauge, Histogram]]:
        """
        Get a metric by name.

        Args:
            name: Metric name

        Returns:
            Metric instance or None if not found
        """
        with self._metrics_lock:
            return self._metrics.get(name)

    def get_all_metrics(self) -> Dict[str, Union[Counter, Gauge, Histogram]]:
        """
        Get all registered metrics.

        Returns:
            Dictionary of all metrics
        """
        with self._metrics_lock:
            return self._metrics.copy()

    def update_system_metrics(self) -> None:
        """Update system resource metrics."""
        try:
            # Update memory metrics
            memory = psutil.virtual_memory()
            self.gauge("system_memory_bytes").set(memory.used)
            self.gauge("system_memory_percent").set(memory.percent)

            # Update process memory
            process = psutil.Process()
            process_memory = process.memory_info().rss
            self.gauge("process_memory_bytes").set(process_memory)

            # Update CPU metrics
            self.gauge("system_cpu_percent").set(psutil.cpu_percent(interval=0.1))
            self.gauge("process_cpu_percent").set(process.cpu_percent(interval=0.1))

        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")

    def record_llm_request(
        self,
        duration: float,
        success: bool,
        tokens: int = 0,
        model: str = ""
    ) -> None:
        """
        Record an LLM request metric.

        Args:
            duration: Request duration in seconds
            success: Whether the request was successful
            tokens: Number of tokens used
            model: Model name
        """
        self.counter("llm_requests_total").inc()

        if success:
            self.counter("llm_requests_success").inc()
        else:
            self.counter("llm_requests_error").inc()

        if tokens > 0:
            self.counter("llm_tokens_total").inc(tokens)

        self.histogram("llm_request_duration_seconds").observe(duration)

        logger.debug(f"Recorded LLM request: model={model}, duration={duration:.3f}s, success={success}")

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []

        # Update system metrics before export
        self.update_system_metrics()

        with self._metrics_lock:
            for name, metric in sorted(self._metrics.items()):
                snapshot = metric.snapshot()

                # Add HELP line
                if snapshot.help_text:
                    lines.append(f"# HELP {name} {snapshot.help_text}")

                # Add TYPE line
                lines.append(f"# TYPE {name} {snapshot.type}")

                # Format labels
                label_str = ""
                if snapshot.labels:
                    label_pairs = [f'{k}="{v}"' for k, v in snapshot.labels.items()]
                    label_str = "{" + ",".join(label_pairs) + "}"

                # Add metric value(s)
                if snapshot.type in ("counter", "gauge"):
                    lines.append(f"{name}{label_str} {snapshot.value}")

                elif snapshot.type == "histogram":
                    stats = snapshot.value

                    # Add bucket counts
                    for bucket, count in sorted(stats.get("buckets", {}).items()):
                        lines.append(f'{name}_bucket{{le="{bucket}"}}{label_str} {count}')

                    # Add +Inf bucket
                    lines.append(f'{name}_bucket{{le="+Inf"}}{label_str} {stats["count"]}')

                    # Add sum and count
                    lines.append(f"{name}_sum{label_str} {stats['sum']}")
                    lines.append(f"{name}_count{label_str} {stats['count']}")

                lines.append("")  # Empty line between metrics

        return "\n".join(lines)

    def export_json(self) -> str:
        """
        Export metrics in JSON format for custom dashboards.

        Returns:
            JSON-formatted metrics string
        """
        # Update system metrics before export
        self.update_system_metrics()

        metrics_data = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self._start_time,
            "metrics": {}
        }

        with self._metrics_lock:
            for name, metric in self._metrics.items():
                snapshot = metric.snapshot()

                metrics_data["metrics"][name] = {
                    "type": snapshot.type,
                    "value": snapshot.value,
                    "timestamp": snapshot.timestamp,
                    "labels": snapshot.labels,
                    "help": snapshot.help_text
                }

        return json.dumps(metrics_data, indent=2)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metrics.

        Returns:
            Dictionary with metric summaries
        """
        self.update_system_metrics()

        summary = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self._start_time,
            "total_metrics": len(self._metrics),
            "metrics_by_type": defaultdict(int),
            "snapshots": {}
        }

        with self._metrics_lock:
            for name, metric in self._metrics.items():
                metric_type = type(metric).__name__.lower()
                summary["metrics_by_type"][metric_type] += 1
                summary["snapshots"][name] = asdict(metric.snapshot())

        summary["metrics_by_type"] = dict(summary["metrics_by_type"])

        return summary

    def reset_all(self) -> None:
        """Reset all metrics to their initial state."""
        with self._metrics_lock:
            for metric in self._metrics.values():
                metric.reset()

        logger.info("All metrics reset")


def timed(metric_name: Optional[str] = None):
    """
    Decorator to time function execution and record in histogram.

    Args:
        metric_name: Name of the histogram metric (defaults to function name)

    Example:
        @timed("api_request_duration")
        def api_request():
            # Function to time
            pass

        @timed()  # Uses function name as metric name
        def process_data():
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Determine metric name
        hist_name = metric_name or f"{func.__name__}_duration_seconds"

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            registry = MetricsRegistry.get_instance()
            histogram = registry.histogram(
                hist_name,
                f"Duration of {func.__name__} in seconds"
            )

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                histogram.observe(duration)
                logger.debug(f"{func.__name__} executed in {duration:.3f}s")

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            registry = MetricsRegistry.get_instance()
            histogram = registry.histogram(
                hist_name,
                f"Duration of {func.__name__} in seconds"
            )

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                histogram.observe(duration)
                logger.debug(f"{func.__name__} executed in {duration:.3f}s")

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_metrics_registry() -> MetricsRegistry:
    """
    Get the global metrics registry instance.

    Returns:
        MetricsRegistry singleton instance
    """
    return MetricsRegistry.get_instance()


# Convenience functions for quick metric access
def counter(name: str, help_text: str = "", labels: Optional[Dict[str, str]] = None) -> Counter:
    """
    Get or create a counter metric.

    Args:
        name: Metric name
        help_text: Description of the metric
        labels: Optional labels

    Returns:
        Counter instance
    """
    return get_metrics_registry().counter(name, help_text, labels)


def gauge(name: str, help_text: str = "", labels: Optional[Dict[str, str]] = None) -> Gauge:
    """
    Get or create a gauge metric.

    Args:
        name: Metric name
        help_text: Description of the metric
        labels: Optional labels

    Returns:
        Gauge instance
    """
    return get_metrics_registry().gauge(name, help_text, labels)


def histogram(
    name: str,
    help_text: str = "",
    labels: Optional[Dict[str, str]] = None,
    buckets: Optional[List[float]] = None
) -> Histogram:
    """
    Get or create a histogram metric.

    Args:
        name: Metric name
        help_text: Description of the metric
        labels: Optional labels
        buckets: Custom bucket boundaries

    Returns:
        Histogram instance
    """
    return get_metrics_registry().histogram(name, help_text, labels, buckets)
