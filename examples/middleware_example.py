#!/usr/bin/env python3
"""
Comprehensive example demonstrating the middleware system.

This example shows how to use the middleware system for request/response
processing pipelines with various built-in middleware components.
"""

import asyncio
import time
from ai_automation_framework.core import (
    MiddlewareStack,
    MiddlewareContext,
    Middleware,
    ConditionalMiddleware,
    LoggingMiddleware,
    TimingMiddleware,
    RetryMiddleware,
    CacheMiddleware,
    RateLimitMiddleware,
    middleware_decorator,
)


# ==============================================================================
# Example 1: Basic Middleware Stack
# ==============================================================================

def example_basic_stack():
    """Demonstrate basic middleware stack usage."""
    print("\n" + "="*80)
    print("Example 1: Basic Middleware Stack")
    print("="*80)

    # Create a handler function
    def process_request(request):
        """Simple request processor."""
        return f"Processed: {request.upper()}"

    # Create middleware stack
    stack = MiddlewareStack([
        LoggingMiddleware(log_request=True, log_response=True),
        TimingMiddleware(warn_threshold=0.5),
    ])

    # Execute with middleware
    result = stack.execute(process_request, request="hello world")
    print(f"\nResult: {result}")


# ==============================================================================
# Example 2: Custom Middleware
# ==============================================================================

class AuthenticationMiddleware(Middleware):
    """Custom middleware for authentication."""

    def __init__(self, required_token: str = "secret123"):
        super().__init__(name="Authentication")
        self.required_token = required_token

    def before(self, context: MiddlewareContext):
        """Verify authentication token."""
        token = context.get("auth_token")

        if token != self.required_token:
            self.logger.warning("Authentication failed")
            context.response = {"error": "Unauthorized"}
            context.stop()  # Short-circuit the pipeline
        else:
            self.logger.info("Authentication successful")


def example_custom_middleware():
    """Demonstrate custom middleware."""
    print("\n" + "="*80)
    print("Example 2: Custom Middleware (Authentication)")
    print("="*80)

    def secure_handler(request):
        """Handler that requires authentication."""
        return {"data": f"Secret data for: {request}"}

    stack = MiddlewareStack([
        AuthenticationMiddleware(required_token="secret123"),
        LoggingMiddleware(),
    ])

    # Try without token (should fail)
    print("\nAttempt 1: No auth token")
    result1 = stack.execute(secure_handler, request="user1")
    print(f"Result: {result1}")

    # Try with valid token (should succeed)
    print("\nAttempt 2: Valid auth token")
    result2 = stack.execute(secure_handler, request="user2", auth_token="secret123")
    print(f"Result: {result2}")


# ==============================================================================
# Example 3: Conditional Middleware
# ==============================================================================

def example_conditional_middleware():
    """Demonstrate conditional middleware."""
    print("\n" + "="*80)
    print("Example 3: Conditional Middleware")
    print("="*80)

    # Only log requests that are marked as important
    def is_important_request(ctx: MiddlewareContext) -> bool:
        return ctx.get("priority") == "high"

    stack = MiddlewareStack([
        ConditionalMiddleware(
            condition=is_important_request,
            delegate=LoggingMiddleware(log_request=True, log_metadata=True)
        ),
        TimingMiddleware(),
    ])

    def handler(request):
        return f"Handled: {request}"

    # Low priority request (won't be logged)
    print("\nLow priority request:")
    stack.execute(handler, request="low priority", priority="low")

    # High priority request (will be logged)
    print("\nHigh priority request:")
    stack.execute(handler, request="high priority", priority="high")


# ==============================================================================
# Example 4: Cache Middleware
# ==============================================================================

def example_cache_middleware():
    """Demonstrate cache middleware."""
    print("\n" + "="*80)
    print("Example 4: Cache Middleware")
    print("="*80)

    def expensive_operation(request):
        """Simulate expensive operation."""
        time.sleep(0.2)  # Simulate processing delay
        return f"Result for {request}"

    stack = MiddlewareStack([
        CacheMiddleware(cache_dir="./middleware_cache", ttl_hours=1),
        TimingMiddleware(),
    ])

    # First call - cache miss
    print("\nFirst call (cache miss - slow):")
    result1 = stack.execute(expensive_operation, request="test_data")
    print(f"Result: {result1}")

    # Second call - cache hit
    print("\nSecond call (cache hit - fast):")
    result2 = stack.execute(expensive_operation, request="test_data")
    print(f"Result: {result2}")


# ==============================================================================
# Example 5: Rate Limiting
# ==============================================================================

def example_rate_limiting():
    """Demonstrate rate limiting middleware."""
    print("\n" + "="*80)
    print("Example 5: Rate Limiting")
    print("="*80)

    # Custom rate limit key based on user
    def get_user_key(ctx: MiddlewareContext) -> str:
        return ctx.get("user_id", "anonymous")

    stack = MiddlewareStack([
        RateLimitMiddleware(
            max_requests=3,
            window_seconds=5,
            key_func=get_user_key
        ),
    ])

    def api_handler(request):
        return {"status": "success", "data": request}

    # Try 5 requests - only 3 should succeed
    print("\nMaking 5 requests (limit: 3 per 5 seconds):")
    for i in range(5):
        try:
            result = stack.execute(api_handler, request=f"request_{i+1}", user_id="user123")
            print(f"✓ Request {i+1}: {result}")
        except RuntimeError as e:
            print(f"✗ Request {i+1}: Rate limited")


# ==============================================================================
# Example 6: Async Middleware
# ==============================================================================

async def example_async_middleware():
    """Demonstrate async middleware."""
    print("\n" + "="*80)
    print("Example 6: Async Middleware")
    print("="*80)

    async def async_handler(request):
        """Async request handler."""
        await asyncio.sleep(0.1)  # Simulate async I/O
        return f"Async result: {request}"

    stack = MiddlewareStack([
        LoggingMiddleware(),
        TimingMiddleware(),
    ])

    # Execute async
    result = await stack.execute_async(async_handler, request="async test")
    print(f"Result: {result}")


# ==============================================================================
# Example 7: Middleware Decorator
# ==============================================================================

def example_middleware_decorator():
    """Demonstrate middleware decorator."""
    print("\n" + "="*80)
    print("Example 7: Middleware Decorator")
    print("="*80)

    @middleware_decorator(
        LoggingMiddleware(),
        TimingMiddleware(),
        CacheMiddleware(cache_dir="./decorator_cache")
    )
    def decorated_function(data):
        """Function with automatic middleware."""
        time.sleep(0.1)
        return f"Processed: {data}"

    # First call
    print("\nFirst call:")
    result1 = decorated_function("test")
    print(f"Result: {result1}")

    # Second call (cached)
    print("\nSecond call (cached):")
    result2 = decorated_function("test")
    print(f"Result: {result2}")


# ==============================================================================
# Example 8: Complex Pipeline
# ==============================================================================

class ValidationMiddleware(Middleware):
    """Validate request data."""

    def before(self, context: MiddlewareContext):
        """Validate request."""
        request = context.request
        if not isinstance(request, dict):
            raise ValueError("Request must be a dictionary")

        if "data" not in request:
            raise ValueError("Request must contain 'data' field")


class TransformMiddleware(Middleware):
    """Transform request/response data."""

    def before(self, context: MiddlewareContext):
        """Transform request."""
        if isinstance(context.request, dict):
            # Add timestamp to request
            context.request["timestamp"] = time.time()

    def after(self, context: MiddlewareContext):
        """Transform response."""
        if isinstance(context.response, dict):
            # Add processing info to response
            context.response["processed_at"] = time.time()
            context.response["elapsed"] = context.elapsed_time


def example_complex_pipeline():
    """Demonstrate complex middleware pipeline."""
    print("\n" + "="*80)
    print("Example 8: Complex Pipeline")
    print("="*80)

    def business_logic(request):
        """Core business logic."""
        data = request.get("data", "")
        return {
            "result": data.upper(),
            "length": len(data)
        }

    # Build comprehensive middleware stack
    stack = MiddlewareStack([
        LoggingMiddleware(log_request=True, log_response=True),
        TimingMiddleware(warn_threshold=0.1),
        ValidationMiddleware(),
        TransformMiddleware(),
        CacheMiddleware(cache_dir="./pipeline_cache"),
    ])

    # Process request
    request = {"data": "hello world", "user": "admin"}
    result = stack.execute(business_logic, request=request)

    print(f"\nOriginal request: {request}")
    print(f"Final result: {result}")


# ==============================================================================
# Example 9: Error Handling
# ==============================================================================

class ErrorHandlingMiddleware(Middleware):
    """Handle and log errors."""

    def on_error(self, context: MiddlewareContext, error: Exception):
        """Handle errors gracefully."""
        self.logger.error(f"Error occurred: {error}")
        context.response = {
            "error": str(error),
            "type": error.__class__.__name__
        }
        context.add_error(error)


def example_error_handling():
    """Demonstrate error handling in middleware."""
    print("\n" + "="*80)
    print("Example 9: Error Handling")
    print("="*80)

    def failing_handler(request):
        """Handler that sometimes fails."""
        if request == "fail":
            raise ValueError("Intentional failure")
        return f"Success: {request}"

    stack = MiddlewareStack([
        ErrorHandlingMiddleware(),
        LoggingMiddleware(),
    ])

    # Successful request
    print("\nSuccessful request:")
    result1 = stack.execute(failing_handler, request="success")
    print(f"Result: {result1}")

    # Failing request
    print("\nFailing request:")
    try:
        result2 = stack.execute(failing_handler, request="fail")
    except ValueError as e:
        print(f"Caught error: {e}")


# ==============================================================================
# Main
# ==============================================================================

def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("MIDDLEWARE SYSTEM EXAMPLES")
    print("="*80)

    # Run synchronous examples
    example_basic_stack()
    example_custom_middleware()
    example_conditional_middleware()
    example_cache_middleware()
    example_rate_limiting()
    example_middleware_decorator()
    example_complex_pipeline()
    example_error_handling()

    # Run async example
    asyncio.run(example_async_middleware())

    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETED")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
