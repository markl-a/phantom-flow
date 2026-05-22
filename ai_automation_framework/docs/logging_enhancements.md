# Enhanced Logging Features

## Overview

The logging module has been enhanced with structured logging capabilities while maintaining full backward compatibility with existing code.

## New Features

### 1. JSON Logging Format

Enable JSON structured logging for better integration with log aggregation systems.

**Usage:**

```python
from ai_automation_framework.core.logger import setup_logger, get_logger

# Programmatic setup
setup_logger(use_json=True, log_level="INFO")

# Or via environment variable
# Set LOG_FORMAT=JSON
logger = get_logger(__name__)
logger.info("This will be logged as JSON")
```

**Output:**
```json
{
  "timestamp": "2025-12-15T11:40:57.752725+00:00",
  "level": "INFO",
  "logger": "__main__",
  "function": "my_function",
  "line": 42,
  "message": "This will be logged as JSON",
  "correlation_id": "abc-123",
  "extra": {"user_id": "123"}
}
```

### 2. Correlation ID Support

Track requests across service boundaries with correlation IDs.

**Usage:**

```python
from ai_automation_framework.core.logger import set_correlation_id, get_correlation_id, clear_correlation_id

# Set a correlation ID (auto-generates UUID if not provided)
correlation_id = set_correlation_id()  # Auto-generate
# or
correlation_id = set_correlation_id("custom-id-123")  # Custom ID

# All logs will now include this correlation ID
logger.info("Processing request")  # Includes correlation_id in logs

# Get current correlation ID
current_id = get_correlation_id()

# Clear when done
clear_correlation_id()
```

### 3. Log Context Manager

Temporarily add extra fields to log messages within a specific scope.

**Usage:**

```python
from ai_automation_framework.core.logger import log_context

# Add context for a block of code
with log_context(user_id="user-123", operation="checkout"):
    logger.info("Starting checkout")  # Includes user_id and operation
    logger.info("Payment processed")  # Also includes context

logger.info("Outside context")  # No extra fields

# Nested contexts
with log_context(request_id="req-456"):
    with log_context(step="validation"):
        logger.info("Validating")  # Includes both request_id and step
```

### 4. Performance Timing Decorator

Automatically log function execution time.

**Usage:**

```python
from ai_automation_framework.core.logger import log_performance

# Basic usage
@log_performance
def process_data(data):
    # Your code here
    return result

# Custom log level
@log_performance(level="DEBUG")
def quick_operation():
    # Your code here
    return result

# Usage
result = process_data(my_data)
# Logs:
# - "Starting process_data" at function entry
# - "Completed process_data in 1.23s" at function exit
# - "Failed process_data after 0.50s: error message" on exception
```

**Features:**
- Logs function start and completion
- Includes execution duration in seconds and milliseconds
- Automatically logs errors with timing if function fails
- Includes correlation ID if set
- Preserves function metadata with `@wraps`

### 5. Environment Variable Configuration

Configure logging behavior via environment variables.

**Environment Variables:**

- `LOG_LEVEL`: Set log level (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
  - Default: INFO
  - Example: `export LOG_LEVEL=DEBUG`

- `LOG_FORMAT`: Set output format
  - Values: `JSON` for JSON format, anything else for human-readable
  - Default: human-readable
  - Example: `export LOG_FORMAT=JSON`

**Usage:**

```bash
# Enable debug logging with JSON format
export LOG_LEVEL=DEBUG
export LOG_FORMAT=JSON

python your_script.py
```

## Backward Compatibility

All existing code continues to work without any changes:

```python
from ai_automation_framework.core.logger import get_logger

logger = get_logger(__name__)
logger.info("This still works exactly as before")
logger.debug("No changes needed to existing code")
```

## Complete Example

```python
from ai_automation_framework.core.logger import (
    setup_logger,
    get_logger,
    set_correlation_id,
    log_context,
    log_performance,
)

# Setup (optional - auto-initialized with defaults)
setup_logger(log_level="INFO", use_json=False)
logger = get_logger(__name__)

# Set correlation ID for request tracing
request_id = set_correlation_id("req-789")

# Use context for structured data
with log_context(user_id="user-123", action="purchase"):

    @log_performance
    def process_purchase(amount):
        logger.info(f"Processing purchase of ${amount}")
        # Business logic here
        return "success"

    result = process_purchase(99.99)
    logger.info(f"Purchase result: {result}")
```

## JSON Output Example

With `use_json=True` or `LOG_FORMAT=JSON`, the above produces:

```json
{"timestamp": "2025-12-15T11:40:57.752725+00:00", "level": "INFO", "logger": "__main__", "function": "wrapper", "line": 266, "message": "Starting process_purchase", "correlation_id": "req-789", "extra": {"user_id": "user-123", "action": "purchase"}}
{"timestamp": "2025-12-15T11:40:57.753041+00:00", "level": "INFO", "logger": "__main__", "function": "process_purchase", "line": 42, "message": "Processing purchase of $99.99", "correlation_id": "req-789", "extra": {"user_id": "user-123", "action": "purchase"}}
{"timestamp": "2025-12-15T11:40:57.850123+00:00", "level": "INFO", "logger": "__main__", "function": "wrapper", "line": 276, "message": "Completed process_purchase in 0.10s", "correlation_id": "req-789", "extra": {"user_id": "user-123", "action": "purchase", "duration_ms": 100.0}}
```

## Best Practices

1. **Always set correlation IDs for request handling:**
   ```python
   correlation_id = set_correlation_id(request.headers.get('X-Request-ID'))
   try:
       # Handle request
       pass
   finally:
       clear_correlation_id()
   ```

2. **Use log_context for consistent metadata:**
   ```python
   with log_context(user_id=user.id, tenant_id=tenant.id):
       # All logs in this block include user and tenant info
       process_user_action()
   ```

3. **Use @log_performance for monitoring critical functions:**
   ```python
   @log_performance
   def expensive_operation():
       # Automatically logs timing
       pass
   ```

4. **Enable JSON logging in production:**
   ```bash
   export LOG_FORMAT=JSON
   ```
   This makes logs easier to parse and analyze with tools like ELK, Splunk, etc.

## API Reference

### Functions

- `setup_logger(log_file=None, log_level=None, rotation="10 MB", retention="1 week", use_json=False)`: Configure logging
- `get_logger(name=None)`: Get logger instance
- `set_correlation_id(correlation_id=None)`: Set correlation ID (returns the ID)
- `get_correlation_id()`: Get current correlation ID
- `clear_correlation_id()`: Clear correlation ID
- `log_context(**kwargs)`: Context manager for extra fields
- `log_performance(func=None, *, level="INFO")`: Decorator for performance logging

### Environment Variables

- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FORMAT`: Output format (JSON or human-readable)
