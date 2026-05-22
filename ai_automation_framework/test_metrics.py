#!/usr/bin/env python3
"""Test script for the metrics module."""

import time
import json
from ai_automation_framework.core.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsRegistry,
    get_metrics_registry,
    timed,
    counter,
    gauge,
    histogram
)


def test_counter():
    """Test Counter metric."""
    print("Testing Counter...")
    c = Counter("test_counter", "A test counter")
    c.inc()
    c.inc(5)
    assert c.get() == 6.0, f"Expected 6.0, got {c.get()}"
    print(f"  ✓ Counter value: {c.get()}")


def test_gauge():
    """Test Gauge metric."""
    print("Testing Gauge...")
    g = Gauge("test_gauge", "A test gauge")
    g.set(10)
    g.inc(5)
    g.dec(3)
    assert g.get() == 12.0, f"Expected 12.0, got {g.get()}"
    print(f"  ✓ Gauge value: {g.get()}")


def test_histogram():
    """Test Histogram metric."""
    print("Testing Histogram...")
    h = Histogram("test_histogram", "A test histogram")

    # Record some observations
    for value in [0.1, 0.2, 0.5, 1.0, 2.0]:
        h.observe(value)

    stats = h.get_stats()
    assert stats["count"] == 5, f"Expected count 5, got {stats['count']}"
    assert abs(stats["sum"] - 3.8) < 0.01, f"Expected sum ~3.8, got {stats['sum']}"
    assert abs(stats["mean"] - 0.76) < 0.01, f"Expected mean ~0.76, got {stats['mean']}"

    print(f"  ✓ Histogram stats: count={stats['count']}, mean={stats['mean']:.2f}, min={stats['min']}, max={stats['max']}")

    # Test percentiles
    p50 = h.get_percentile(50)
    p95 = h.get_percentile(95)
    print(f"  ✓ Percentiles: p50={p50:.2f}, p95={p95:.2f}")


def test_registry():
    """Test MetricsRegistry."""
    print("Testing MetricsRegistry...")
    registry = MetricsRegistry.get_instance()

    # Create metrics via registry
    c = registry.counter("registry_counter", "Counter via registry")
    g = registry.gauge("registry_gauge", "Gauge via registry")
    h = registry.histogram("registry_histogram", "Histogram via registry")

    c.inc()
    g.set(42)
    h.observe(1.5)

    # Get metric back
    retrieved = registry.get_metric("registry_counter")
    assert retrieved is not None, "Failed to retrieve metric"
    assert isinstance(retrieved, Counter), "Retrieved metric is not a Counter"

    print(f"  ✓ Registry has {len(registry.get_all_metrics())} metrics")


def test_system_metrics():
    """Test system metrics collection."""
    print("Testing system metrics...")
    registry = MetricsRegistry.get_instance()

    # Update system metrics
    registry.update_system_metrics()

    # Check that system metrics exist and have values
    memory_gauge = registry.get_metric("system_memory_bytes")
    assert memory_gauge is not None, "system_memory_bytes not found"
    assert memory_gauge.get() > 0, "system_memory_bytes should be > 0"

    cpu_gauge = registry.get_metric("system_cpu_percent")
    assert cpu_gauge is not None, "system_cpu_percent not found"

    print(f"  ✓ System memory: {memory_gauge.get() / 1024 / 1024:.2f} MB")
    print(f"  ✓ System CPU: {cpu_gauge.get():.2f}%")


def test_llm_metrics():
    """Test LLM request metrics."""
    print("Testing LLM metrics...")
    registry = MetricsRegistry.get_instance()

    # Record some LLM requests
    registry.record_llm_request(duration=0.5, success=True, tokens=100, model="gpt-4")
    registry.record_llm_request(duration=1.2, success=True, tokens=200, model="gpt-4")
    registry.record_llm_request(duration=0.3, success=False, tokens=0, model="gpt-4")

    # Check counters
    total = registry.get_metric("llm_requests_total")
    success = registry.get_metric("llm_requests_success")
    error = registry.get_metric("llm_requests_error")
    tokens = registry.get_metric("llm_tokens_total")

    print(f"  ✓ Total requests: {total.get()}")
    print(f"  ✓ Successful: {success.get()}")
    print(f"  ✓ Errors: {error.get()}")
    print(f"  ✓ Total tokens: {tokens.get()}")


@timed("test_function_duration")
def slow_function():
    """Test function for timing decorator."""
    time.sleep(0.1)
    return "done"


def test_timed_decorator():
    """Test the @timed decorator."""
    print("Testing @timed decorator...")

    # Call the function
    result = slow_function()
    assert result == "done"

    # Check that histogram was created
    registry = MetricsRegistry.get_instance()
    hist = registry.get_metric("test_function_duration")
    assert hist is not None, "Histogram not created by @timed"

    stats = hist.get_stats()
    assert stats["count"] > 0, "No observations recorded"
    print(f"  ✓ Function executed in {stats['mean']:.3f}s (mean)")


def test_prometheus_export():
    """Test Prometheus format export."""
    print("Testing Prometheus export...")
    registry = MetricsRegistry.get_instance()

    # Export to Prometheus format
    prom_output = registry.export_prometheus()

    assert "# HELP" in prom_output, "Missing HELP lines"
    assert "# TYPE" in prom_output, "Missing TYPE lines"

    print(f"  ✓ Prometheus export length: {len(prom_output)} bytes")
    print("\nSample Prometheus output (first 500 chars):")
    print("-" * 60)
    print(prom_output[:500])
    print("-" * 60)


def test_json_export():
    """Test JSON format export."""
    print("\nTesting JSON export...")
    registry = MetricsRegistry.get_instance()

    # Export to JSON format
    json_output = registry.export_json()

    # Parse to verify it's valid JSON
    data = json.loads(json_output)

    assert "timestamp" in data, "Missing timestamp"
    assert "metrics" in data, "Missing metrics"
    assert "uptime_seconds" in data, "Missing uptime"

    print(f"  ✓ JSON export contains {len(data['metrics'])} metrics")
    print(f"  ✓ Uptime: {data['uptime_seconds']:.2f}s")

    print("\nSample JSON output (first 800 chars):")
    print("-" * 60)
    print(json_output[:800])
    print("-" * 60)


def test_convenience_functions():
    """Test convenience functions."""
    print("\nTesting convenience functions...")

    # Use convenience functions
    c = counter("convenience_counter", "Counter via convenience function")
    g = gauge("convenience_gauge", "Gauge via convenience function")
    h = histogram("convenience_histogram", "Histogram via convenience function")

    c.inc()
    g.set(99)
    h.observe(3.14)

    assert c.get() == 1.0
    assert g.get() == 99.0
    assert h.get_stats()["count"] == 1

    print("  ✓ All convenience functions work correctly")


def test_thread_safety():
    """Test thread-safety of metrics."""
    print("\nTesting thread safety...")
    import threading

    c = counter("thread_test_counter", "Thread safety test counter")

    def increment_counter():
        for _ in range(1000):
            c.inc()

    # Create multiple threads
    threads = [threading.Thread(target=increment_counter) for _ in range(10)]

    # Start all threads
    for t in threads:
        t.start()

    # Wait for all threads
    for t in threads:
        t.join()

    # Should be exactly 10,000 (1000 increments * 10 threads)
    assert c.get() == 10000.0, f"Expected 10000, got {c.get()}"
    print(f"  ✓ Thread-safe counter: {c.get()} increments from 10 threads")


def main():
    """Run all tests."""
    print("=" * 60)
    print("METRICS MODULE TEST SUITE")
    print("=" * 60)

    try:
        test_counter()
        test_gauge()
        test_histogram()
        test_registry()
        test_system_metrics()
        test_llm_metrics()
        test_timed_decorator()
        test_prometheus_export()
        test_json_export()
        test_convenience_functions()
        test_thread_safety()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)

        # Get final summary
        registry = get_metrics_registry()
        summary = registry.get_summary()
        print(f"\nFinal metrics count: {summary['total_metrics']}")
        print(f"Metrics by type: {summary['metrics_by_type']}")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
