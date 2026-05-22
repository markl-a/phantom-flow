# Metrics Collection and Monitoring System

## Overview

The AI Automation Framework now includes a comprehensive metrics collection and monitoring system located at `ai_automation_framework/core/metrics.py`. This system provides robust, thread-safe metric collection with support for multiple export formats.

## Features

### 1. Metric Types

#### Counter
- **Purpose**: Track cumulative values that only increase
- **Use Cases**: Total requests, total errors, cumulative costs
- **Methods**: `inc()`, `get()`, `reset()`

```python
from ai_automation_framework.core import counter

requests = counter("requests_total", "Total number of requests")
requests.inc()      # Increment by 1
requests.inc(5)     # Increment by 5
print(requests.get())  # Get current value
```

#### Gauge
- **Purpose**: Track values that can go up and down
- **Use Cases**: Active connections, memory usage, temperature
- **Methods**: `set()`, `inc()`, `dec()`, `get()`, `reset()`

```python
from ai_automation_framework.core import gauge

active_users = gauge("active_users", "Number of active users")
active_users.set(10)   # Set to 10
active_users.inc()     # Now 11
active_users.dec(5)    # Now 6
print(active_users.get())
```

#### Histogram
- **Purpose**: Track distribution of observations
- **Use Cases**: Request duration, response sizes, latencies
- **Methods**: `observe()`, `get_stats()`, `get_percentile()`, `reset()`

```python
from ai_automation_framework.core import histogram

duration = histogram("request_duration", "Request duration in seconds")
duration.observe(0.5)
duration.observe(1.2)

stats = duration.get_stats()
print(f"Average: {stats['mean']}")
print(f"Min: {stats['min']}, Max: {stats['max']}")
print(f"P95: {duration.get_percentile(95)}")
```

### 2. MetricsRegistry (Singleton Pattern)

The `MetricsRegistry` manages all metrics in a thread-safe singleton instance.

```python
from ai_automation_framework.core import get_metrics_registry

registry = get_metrics_registry()

# Create metrics via registry
counter = registry.counter("my_counter", "Description")
gauge = registry.gauge("my_gauge", "Description")
histogram = registry.histogram("my_histogram", "Description")

# Get existing metrics
metric = registry.get_metric("my_counter")
all_metrics = registry.get_all_metrics()
```

### 3. Timing Decorator

Automatically time function execution and record in a histogram.

```python
from ai_automation_framework.core import timed

@timed("api_call_duration")
def call_api():
    # Your code here
    pass

# Also works with async functions
@timed("async_operation_duration")
async def async_operation():
    # Your async code here
    pass
```

### 4. Memory Usage Tracking

Automatic system resource monitoring.

```python
from ai_automation_framework.core import get_metrics_registry

registry = get_metrics_registry()
registry.update_system_metrics()

# Access system metrics
memory = registry.get_metric("system_memory_bytes").get()
cpu = registry.get_metric("system_cpu_percent").get()
```

Available system metrics:
- `system_memory_bytes` - System memory usage in bytes
- `system_memory_percent` - System memory usage percentage
- `process_memory_bytes` - Process memory usage in bytes
- `system_cpu_percent` - System CPU usage percentage
- `process_cpu_percent` - Process CPU usage percentage

### 5. LLM Request/Response Metrics

Specialized metrics for tracking LLM API calls.

```python
from ai_automation_framework.core import get_metrics_registry

registry = get_metrics_registry()

# Record an LLM request
registry.record_llm_request(
    duration=1.5,
    success=True,
    tokens=750,
    model="gpt-4"
)

# Access LLM metrics
total_requests = registry.get_metric("llm_requests_total").get()
success_count = registry.get_metric("llm_requests_success").get()
error_count = registry.get_metric("llm_requests_error").get()
total_tokens = registry.get_metric("llm_tokens_total").get()
```

Available LLM metrics:
- `llm_requests_total` - Total number of LLM requests
- `llm_requests_success` - Successful LLM requests
- `llm_requests_error` - Failed LLM requests
- `llm_tokens_total` - Total tokens used
- `llm_request_duration_seconds` - Histogram of request durations

### 6. Prometheus Export

Export metrics in Prometheus text format for Prometheus/Grafana integration.

```python
from ai_automation_framework.core import get_metrics_registry

registry = get_metrics_registry()
prometheus_output = registry.export_prometheus()

# Save to file for Prometheus scraping
with open("/metrics", "w") as f:
    f.write(prometheus_output)
```

Output format:
```
# HELP requests_total Total number of requests
# TYPE requests_total counter
requests_total 42.0

# HELP response_time_seconds Response time in seconds
# TYPE response_time_seconds histogram
response_time_seconds_bucket{le="0.5"} 10
response_time_seconds_bucket{le="1.0"} 25
...
```

### 7. JSON Export

Export metrics in JSON format for custom dashboards.

```python
from ai_automation_framework.core import get_metrics_registry
import json

registry = get_metrics_registry()
json_output = registry.export_json()

# Parse the JSON
data = json.loads(json_output)
print(f"Timestamp: {data['timestamp']}")
print(f"Uptime: {data['uptime_seconds']}s")
print(f"Total metrics: {len(data['metrics'])}")

# Save to file
with open("metrics.json", "w") as f:
    f.write(json_output)
```

Output structure:
```json
{
  "timestamp": "2025-12-15T14:43:37.016105",
  "uptime_seconds": 123.45,
  "metrics": {
    "metric_name": {
      "type": "counter",
      "value": 42.0,
      "timestamp": 1765809817.016,
      "labels": {},
      "help": "Description"
    }
  }
}
```

## Thread Safety

All metric types are thread-safe using Python's `threading.Lock`:

```python
import threading
from ai_automation_framework.core import counter

c = counter("concurrent_counter")

def increment():
    for _ in range(1000):
        c.inc()

# Create 10 threads
threads = [threading.Thread(target=increment) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(c.get())  # Will always be 10000
```

## Metric Labels

Add labels to metrics for better classification:

```python
from ai_automation_framework.core import counter

http_200 = counter(
    "http_requests",
    "HTTP requests",
    labels={"status": "200", "method": "GET"}
)

http_500 = counter(
    "http_requests",
    "HTTP requests",
    labels={"status": "500", "method": "POST"}
)
```

## Complete Application Example

```python
from ai_automation_framework.core import (
    get_metrics_registry,
    counter,
    gauge,
    histogram,
    timed
)
import time

class APIService:
    """Example API service with comprehensive metrics."""

    def __init__(self):
        # Create metrics
        self.requests = counter(
            "api_requests_total",
            "Total API requests"
        )
        self.active = gauge(
            "api_active_requests",
            "Active API requests"
        )
        self.duration = histogram(
            "api_request_duration",
            "API request duration in seconds"
        )
        self.errors = counter(
            "api_errors_total",
            "Total API errors"
        )

    @timed("api_process_request")
    def process_request(self, data):
        """Process an API request with metrics."""
        self.requests.inc()
        self.active.inc()

        start = time.time()
        try:
            # Process the request
            result = self._do_processing(data)
            return result

        except Exception as e:
            self.errors.inc()
            raise

        finally:
            duration = time.time() - start
            self.duration.observe(duration)
            self.active.dec()

    def _do_processing(self, data):
        # Your processing logic here
        time.sleep(0.1)
        return {"status": "success"}

# Usage
service = APIService()

# Process some requests
for i in range(10):
    service.process_request({"id": i})

# Get metrics summary
registry = get_metrics_registry()
print(registry.export_json())
```

## Integration with Existing Systems

### Flask Integration

```python
from flask import Flask, Response
from ai_automation_framework.core import get_metrics_registry, timed

app = Flask(__name__)

@app.route("/metrics")
def metrics():
    registry = get_metrics_registry()
    return Response(
        registry.export_prometheus(),
        mimetype="text/plain"
    )

@app.route("/api/data")
@timed("api_data_endpoint")
def get_data():
    # Your endpoint logic
    return {"data": "..."}
```

### FastAPI Integration

```python
from fastapi import FastAPI
from ai_automation_framework.core import get_metrics_registry, timed

app = FastAPI()

@app.get("/metrics")
def metrics():
    registry = get_metrics_registry()
    return registry.export_json()

@app.get("/api/data")
@timed("api_data_endpoint")
async def get_data():
    # Your endpoint logic
    return {"data": "..."}
```

## Best Practices

1. **Use Descriptive Names**: Use clear, descriptive metric names
   ```python
   # Good
   counter("http_requests_total", "Total HTTP requests")

   # Bad
   counter("count", "counter")
   ```

2. **Add Help Text**: Always provide descriptive help text
   ```python
   histogram("api_latency", "API response latency in seconds")
   ```

3. **Use Labels Wisely**: Don't create too many label combinations
   ```python
   # Good - limited label values
   counter("requests", labels={"status": "200"})

   # Bad - unbounded label values
   counter("requests", labels={"user_id": "12345"})  # Don't do this!
   ```

4. **Choose the Right Metric Type**:
   - Counter: For things that accumulate (requests, errors, bytes sent)
   - Gauge: For things that vary (connections, memory, queue size)
   - Histogram: For distributions (latency, request size, duration)

5. **Update System Metrics Periodically**:
   ```python
   import threading

   def update_metrics_loop():
       while True:
           registry.update_system_metrics()
           time.sleep(60)  # Update every minute

   thread = threading.Thread(target=update_metrics_loop, daemon=True)
   thread.start()
   ```

## Testing

Run the test suite:
```bash
python3 test_metrics.py
```

Run the examples:
```bash
python3 examples/metrics_usage_example.py
```

## Files Created

- `/home/user/Automation_with_AI/ai_automation_framework/core/metrics.py` - Main metrics module
- `/home/user/Automation_with_AI/test_metrics.py` - Comprehensive test suite
- `/home/user/Automation_with_AI/examples/metrics_usage_example.py` - Usage examples
- `/home/user/Automation_with_AI/METRICS_DOCUMENTATION.md` - This documentation

## API Reference

### Counter
- `__init__(name, help_text, labels)` - Create counter
- `inc(amount=1.0)` - Increment counter
- `get()` - Get current value
- `reset()` - Reset to zero
- `snapshot()` - Get metric snapshot

### Gauge
- `__init__(name, help_text, labels)` - Create gauge
- `set(value)` - Set to specific value
- `inc(amount=1.0)` - Increment gauge
- `dec(amount=1.0)` - Decrement gauge
- `get()` - Get current value
- `reset()` - Reset to zero
- `snapshot()` - Get metric snapshot

### Histogram
- `__init__(name, help_text, labels, buckets)` - Create histogram
- `observe(value)` - Record observation
- `get_stats()` - Get statistics (count, sum, min, max, mean, buckets)
- `get_percentile(percentile)` - Get percentile value (0-100)
- `reset()` - Reset histogram
- `snapshot()` - Get metric snapshot

### MetricsRegistry
- `get_instance()` - Get singleton instance (class method)
- `counter(name, help_text, labels)` - Get/create counter
- `gauge(name, help_text, labels)` - Get/create gauge
- `histogram(name, help_text, labels, buckets)` - Get/create histogram
- `get_metric(name)` - Get metric by name
- `get_all_metrics()` - Get all metrics
- `update_system_metrics()` - Update system resource metrics
- `record_llm_request(duration, success, tokens, model)` - Record LLM request
- `export_prometheus()` - Export in Prometheus format
- `export_json()` - Export in JSON format
- `get_summary()` - Get metrics summary
- `reset_all()` - Reset all metrics

### Decorators and Functions
- `@timed(metric_name)` - Time function execution
- `get_metrics_registry()` - Get registry instance
- `counter(name, help_text, labels)` - Convenience function
- `gauge(name, help_text, labels)` - Convenience function
- `histogram(name, help_text, labels, buckets)` - Convenience function

## Dependencies

- `psutil` - For system metrics (already installed)
- `threading` - For thread safety (built-in)
- `json` - For JSON export (built-in)
- `time` - For timing (built-in)
