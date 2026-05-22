#!/usr/bin/env python3
"""
Example demonstrating enhanced logging capabilities.

This example shows:
1. JSON logging format
2. Correlation ID for request tracing
3. Log context for adding extra fields
4. Performance timing decorator
5. Log level configuration from environment
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_automation_framework.core.logger import (
    setup_logger,
    get_logger,
    set_correlation_id,
    get_correlation_id,
    log_context,
    log_performance,
)


def example_basic_logging():
    """Example 1: Basic logging (backward compatible)."""
    print("\n=== Example 1: Basic Logging ===")

    logger = get_logger(__name__)
    logger.info("This is an info message")
    logger.debug("This is a debug message")
    logger.warning("This is a warning")
    logger.error("This is an error")


def example_correlation_id():
    """Example 2: Using correlation IDs for request tracing."""
    print("\n=== Example 2: Correlation ID Tracing ===")

    logger = get_logger(__name__)

    # Set correlation ID for a request
    request_id = set_correlation_id("req-12345")
    logger.info(f"Processing request with ID: {request_id}")

    # Simulate processing
    logger.info("Step 1: Validating input")
    logger.info("Step 2: Processing data")
    logger.info("Step 3: Saving results")

    # Get current correlation ID
    current_id = get_correlation_id()
    logger.info(f"Completed request {current_id}")


def example_log_context():
    """Example 3: Using log context for structured logging."""
    print("\n=== Example 3: Log Context ===")

    logger = get_logger(__name__)

    # Add context for a specific operation
    with log_context(user_id="user-789", operation="data_import"):
        logger.info("Starting data import")

        with log_context(batch_id="batch-001"):
            logger.info("Processing batch")
            logger.info("Batch complete")

        logger.info("Data import complete")


@log_performance
def slow_operation():
    """Example function with performance logging."""
    time.sleep(0.5)
    return "Operation completed"


@log_performance(level="DEBUG")
def fast_operation():
    """Another example with DEBUG level."""
    time.sleep(0.1)
    return "Quick operation"


def example_performance_logging():
    """Example 4: Performance timing decorator."""
    print("\n=== Example 4: Performance Logging ===")

    result1 = slow_operation()
    print(f"Result: {result1}")

    result2 = fast_operation()
    print(f"Result: {result2}")


def example_combined():
    """Example 5: Combining all features."""
    print("\n=== Example 5: Combined Features ===")

    logger = get_logger(__name__)

    # Set correlation ID for the entire flow
    correlation_id = set_correlation_id("flow-999")

    @log_performance
    def process_user_request(user_id: str):
        """Process a user request with full context."""
        with log_context(user_id=user_id, action="purchase"):
            logger.info("Validating user")
            time.sleep(0.1)

            logger.info("Processing payment")
            time.sleep(0.1)

            logger.info("Sending confirmation")
            return "Success"

    result = process_user_request("user-456")
    logger.info(f"Request completed: {result}")


def example_json_logging():
    """Example 6: JSON structured logging."""
    print("\n=== Example 6: JSON Logging ===")
    print("(Set LOG_FORMAT=JSON environment variable to enable)")

    # Clean up and setup JSON logging
    from loguru import logger as base_logger
    base_logger.remove()

    setup_logger(log_level="INFO", use_json=True)
    logger = get_logger(__name__)

    # Set correlation ID
    set_correlation_id("json-demo-123")

    # Log with context
    with log_context(service="api", version="1.0"):
        logger.info("Service started")
        logger.warning("High memory usage detected")

        try:
            raise ValueError("Simulated error")
        except ValueError as e:
            logger.error(f"Error occurred: {e}")


def main():
    """Run all examples."""
    print("Enhanced Logging Examples")
    print("=" * 60)

    # Examples with human-readable format
    example_basic_logging()
    example_correlation_id()
    example_log_context()
    example_performance_logging()
    example_combined()

    # Example with JSON format
    example_json_logging()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("\nTips:")
    print("- Set LOG_LEVEL=DEBUG for debug messages")
    print("- Set LOG_FORMAT=JSON for structured JSON logs")
    print("- Use correlation IDs to trace requests across services")
    print("- Use log_context() to add metadata to log messages")
    print("- Use @log_performance to automatically log timing")


if __name__ == "__main__":
    main()
