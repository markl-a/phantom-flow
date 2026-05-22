#!/usr/bin/env python3
"""
Example usage of the metrics collection system.

This example demonstrates how to use the metrics system in your
AI Automation Framework applications.
"""

import time
from ai_automation_framework.core import (
    get_metrics_registry,
    counter,
    gauge,
    histogram,
    timed
)


# Example 1: Using convenience functions to create metrics
def example_basic_metrics():
    """Basic example of creating and using metrics."""
    print("Example 1: Basic Metrics Usage")
    print("-" * 60)

    # Create a counter
    requests_counter = counter(
        "api_requests_total",
        "Total number of API requests"
    )

    # Create a gauge
    active_connections = gauge(
        "active_connections",
        "Number of active connections"
    )

    # Create a histogram
    response_time = histogram(
        "api_response_time_seconds",
        "API response time in seconds"
    )

    # Use the metrics
    for i in range(5):
        requests_counter.inc()
        active_connections.set(i + 1)
        response_time.observe(0.1 + i * 0.1)

    print(f"Total requests: {requests_counter.get()}")
    print(f"Active connections: {active_connections.get()}")
    print(f"Response time stats: {response_time.get_stats()}")
    print()


# Example 2: Using the @timed decorator
@timed("data_processing_duration")
def process_data(items):
    """Example function that processes data."""
    time.sleep(0.2)  # Simulate processing
    return len(items)


def example_timed_decorator():
    """Example of using the @timed decorator."""
    print("Example 2: Using @timed Decorator")
    print("-" * 60)

    # Call the function multiple times
    for i in range(3):
        result = process_data([1, 2, 3, 4, 5])
        print(f"Processed {result} items")

    # Get the timing statistics
    registry = get_metrics_registry()
    duration_hist = registry.get_metric("data_processing_duration")
    stats = duration_hist.get_stats()

    print(f"\nTiming statistics:")
    print(f"  Call count: {stats['count']}")
    print(f"  Average duration: {stats['mean']:.3f}s")
    print(f"  Min duration: {stats['min']:.3f}s")
    print(f"  Max duration: {stats['max']:.3f}s")
    print()


# Example 3: Using metrics with labels
def example_labels():
    """Example of using metrics with labels."""
    print("Example 3: Metrics with Labels")
    print("-" * 60)

    # Create metrics with labels
    http_requests = counter(
        "http_requests_by_status",
        "HTTP requests by status code",
        labels={"status": "200"}
    )

    http_errors = counter(
        "http_requests_by_status",
        "HTTP requests by status code",
        labels={"status": "500"}
    )

    # Simulate some requests
    http_requests.inc(100)
    http_errors.inc(5)

    print(f"Successful requests (200): {http_requests.get()}")
    print(f"Error requests (500): {http_errors.get()}")
    print()


# Example 4: Tracking LLM requests
def example_llm_tracking():
    """Example of tracking LLM requests."""
    print("Example 4: Tracking LLM Requests")
    print("-" * 60)

    registry = get_metrics_registry()

    # Simulate some LLM requests
    registry.record_llm_request(
        duration=0.8,
        success=True,
        tokens=500,
        model="gpt-4"
    )

    registry.record_llm_request(
        duration=1.2,
        success=True,
        tokens=750,
        model="gpt-4"
    )

    registry.record_llm_request(
        duration=0.5,
        success=False,
        tokens=0,
        model="gpt-4"
    )

    # Get the metrics
    total = registry.get_metric("llm_requests_total").get()
    success = registry.get_metric("llm_requests_success").get()
    errors = registry.get_metric("llm_requests_error").get()
    tokens = registry.get_metric("llm_tokens_total").get()

    print(f"Total LLM requests: {total}")
    print(f"Successful: {success}")
    print(f"Errors: {errors}")
    print(f"Total tokens used: {tokens}")
    print()


# Example 5: Exporting metrics
def example_export_metrics():
    """Example of exporting metrics in different formats."""
    print("Example 5: Exporting Metrics")
    print("-" * 60)

    registry = get_metrics_registry()

    # Export to Prometheus format
    prometheus_output = registry.export_prometheus()
    print("Prometheus format (first 500 chars):")
    print(prometheus_output[:500])
    print("...\n")

    # Export to JSON format
    json_output = registry.export_json()
    print("JSON format (first 400 chars):")
    print(json_output[:400])
    print("...\n")

    # Get summary
    summary = registry.get_summary()
    print(f"Total metrics: {summary['total_metrics']}")
    print(f"Metrics by type: {summary['metrics_by_type']}")
    print()


# Example 6: System metrics
def example_system_metrics():
    """Example of collecting system metrics."""
    print("Example 6: System Metrics")
    print("-" * 60)

    registry = get_metrics_registry()

    # Update system metrics
    registry.update_system_metrics()

    # Get system metrics
    memory_bytes = registry.get_metric("system_memory_bytes").get()
    memory_percent = registry.get_metric("system_memory_percent").get()
    cpu_percent = registry.get_metric("system_cpu_percent").get()

    print(f"System memory usage: {memory_bytes / 1024 / 1024:.2f} MB ({memory_percent:.1f}%)")
    print(f"System CPU usage: {cpu_percent:.1f}%")
    print()


# Example 7: Custom application metrics
class APIServer:
    """Example API server with metrics."""

    def __init__(self):
        """Initialize API server with metrics."""
        self.requests = counter("api_server_requests", "Total API server requests")
        self.active_requests = gauge("api_server_active_requests", "Active API requests")
        self.request_duration = histogram("api_server_duration", "API request duration")

    @timed("api_server_handle_request")
    def handle_request(self, endpoint: str):
        """Handle an API request."""
        self.requests.inc()
        self.active_requests.inc()

        try:
            # Simulate request processing
            time.sleep(0.05)
            return {"status": "success", "endpoint": endpoint}

        finally:
            self.active_requests.dec()


def example_application_metrics():
    """Example of using metrics in an application."""
    print("Example 7: Application Metrics")
    print("-" * 60)

    server = APIServer()

    # Simulate some API requests
    endpoints = ["/users", "/posts", "/comments", "/users", "/posts"]
    for endpoint in endpoints:
        response = server.handle_request(endpoint)
        print(f"Request to {endpoint}: {response['status']}")

    # Check metrics
    print(f"\nTotal requests: {server.requests.get()}")
    print(f"Active requests: {server.active_requests.get()}")

    stats = server.request_duration.get_stats()
    print(f"Average request duration: {stats['mean']:.3f}s")
    print()


def main():
    """Run all examples."""
    print("=" * 60)
    print("METRICS SYSTEM USAGE EXAMPLES")
    print("=" * 60)
    print()

    example_basic_metrics()
    example_timed_decorator()
    example_labels()
    example_llm_tracking()
    example_system_metrics()
    example_application_metrics()
    example_export_metrics()

    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
