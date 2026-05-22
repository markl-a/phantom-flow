"""Comprehensive tests for the middleware module.

This module contains tests for all middleware components including:
- MiddlewareContext
- Middleware base class
- LoggingMiddleware
- TimingMiddleware
- RetryMiddleware
- CacheMiddleware
- RateLimitMiddleware
- MiddlewareStack
- middleware_decorator
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, MagicMock, patch, call
from typing import Any

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

from ai_automation_framework.core.middleware import (
    MiddlewareContext,
    Middleware,
    ConditionalMiddleware,
    LoggingMiddleware,
    TimingMiddleware,
    RetryMiddleware,
    CacheMiddleware,
    RateLimitMiddleware,
    MiddlewareStack,
    middleware_decorator,
)


# ============================================================================
# MiddlewareContext Tests
# ============================================================================


class TestMiddlewareContext:
    """Tests for MiddlewareContext class."""

    def test_context_creation(self):
        """Test creating a middleware context."""
        request = {"data": "test"}
        context = MiddlewareContext(request=request, user_id="123")

        assert context.request == request
        assert context.response is None
        assert context.short_circuit is False
        assert context.metadata["user_id"] == "123"
        assert len(context.errors) == 0

    def test_context_set_get(self):
        """Test setting and getting metadata values."""
        context = MiddlewareContext()

        context.set("key1", "value1")
        context.set("key2", 42)

        assert context.get("key1") == "value1"
        assert context.get("key2") == 42
        assert context.get("nonexistent") is None
        assert context.get("nonexistent", "default") == "default"

    def test_context_has(self):
        """Test checking if metadata key exists."""
        context = MiddlewareContext()

        context.set("existing_key", "value")

        assert context.has("existing_key") is True
        assert context.has("nonexistent_key") is False

    def test_context_stop(self):
        """Test stopping pipeline execution."""
        context = MiddlewareContext()

        assert context.short_circuit is False
        context.stop()
        assert context.short_circuit is True

    def test_context_add_error(self):
        """Test adding errors to context."""
        context = MiddlewareContext()

        error1 = ValueError("Error 1")
        error2 = RuntimeError("Error 2")

        context.add_error(error1)
        context.add_error(error2)

        assert len(context.errors) == 2
        assert context.errors[0] == error1
        assert context.errors[1] == error2

    def test_context_elapsed_time(self):
        """Test elapsed time calculation."""
        context = MiddlewareContext()

        # Should be very small initially
        assert context.elapsed_time < 0.1

        # Wait a bit
        time.sleep(0.05)

        # Should have increased
        assert context.elapsed_time >= 0.05

    def test_context_to_dict(self):
        """Test converting context to dictionary."""
        request = {"data": "test"}
        context = MiddlewareContext(request=request, user="alice")

        context.response = {"result": "success"}
        context.set("extra", "info")
        context.add_error(ValueError("test error"))

        context_dict = context.to_dict()

        assert context_dict["request"] == request
        assert context_dict["response"] == {"result": "success"}
        assert context_dict["metadata"]["user"] == "alice"
        assert context_dict["metadata"]["extra"] == "info"
        assert context_dict["short_circuit"] is False
        assert "elapsed_time" in context_dict
        assert len(context_dict["errors"]) == 1
        assert "test error" in context_dict["errors"][0]


# ============================================================================
# Middleware Base Class Tests
# ============================================================================


class TestMiddleware:
    """Tests for Middleware base class."""

    def test_middleware_creation(self):
        """Test creating a middleware instance."""
        mw = Middleware(name="TestMW", enabled=True)

        assert mw.name == "TestMW"
        assert mw.enabled is True
        assert mw.logger is not None

    def test_middleware_default_name(self):
        """Test middleware uses class name by default."""
        mw = Middleware()

        assert mw.name == "Middleware"

    def test_middleware_before_hook(self):
        """Test before hook is callable."""
        mw = Middleware()
        context = MiddlewareContext(request="test")

        # Should not raise
        mw.before(context)

    def test_middleware_after_hook(self):
        """Test after hook is callable."""
        mw = Middleware()
        context = MiddlewareContext(request="test")

        # Should not raise
        mw.after(context)

    @pytest.mark.asyncio
    async def test_middleware_async_hooks(self):
        """Test async hooks call sync versions by default."""
        mw = Middleware()
        context = MiddlewareContext(request="test")

        # Should not raise
        await mw.before_async(context)
        await mw.after_async(context)

    def test_middleware_should_run_enabled(self):
        """Test should_run returns True when enabled."""
        mw = Middleware(enabled=True)
        context = MiddlewareContext()

        assert mw.should_run(context) is True

    def test_middleware_should_run_disabled(self):
        """Test should_run returns False when disabled."""
        mw = Middleware(enabled=False)
        context = MiddlewareContext()

        assert mw.should_run(context) is False

    @patch('ai_automation_framework.core.middleware.get_logger')
    def test_middleware_on_error(self, mock_get_logger):
        """Test error handling."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mw = Middleware()
        context = MiddlewareContext()
        error = ValueError("test error")

        mw.on_error(context, error)

        # Should log error
        mock_logger.error.assert_called_once()
        assert "test error" in str(mock_logger.error.call_args)

        # Should add error to context
        assert len(context.errors) == 1
        assert context.errors[0] == error


class TestConditionalMiddleware:
    """Tests for ConditionalMiddleware."""

    def test_conditional_middleware_runs_when_true(self):
        """Test conditional middleware runs when condition is true."""
        delegate = Mock(spec=Middleware)
        delegate.name = "Delegate"
        condition = Mock(return_value=True)

        mw = ConditionalMiddleware(condition=condition, delegate=delegate)
        context = MiddlewareContext()

        mw.before(context)

        condition.assert_called_once_with(context)
        delegate.before.assert_called_once_with(context)

    def test_conditional_middleware_skips_when_false(self):
        """Test conditional middleware skips when condition is false."""
        delegate = Mock(spec=Middleware)
        delegate.name = "Delegate"
        condition = Mock(return_value=False)

        mw = ConditionalMiddleware(condition=condition, delegate=delegate)
        context = MiddlewareContext()

        mw.before(context)

        condition.assert_called_once_with(context)
        delegate.before.assert_not_called()

    @pytest.mark.asyncio
    async def test_conditional_middleware_async(self):
        """Test conditional middleware async hooks."""
        delegate = Mock(spec=Middleware)
        delegate.name = "Delegate"
        delegate.before_async = Mock(return_value=asyncio.Future())
        delegate.before_async.return_value.set_result(None)
        condition = Mock(return_value=True)

        mw = ConditionalMiddleware(condition=condition, delegate=delegate)
        context = MiddlewareContext()

        await mw.before_async(context)

        delegate.before_async.assert_called_once_with(context)


# ============================================================================
# LoggingMiddleware Tests
# ============================================================================


class TestLoggingMiddleware:
    """Tests for LoggingMiddleware."""

    @patch('ai_automation_framework.core.middleware.get_logger')
    def test_logging_middleware_logs_request(self, mock_get_logger):
        """Test logging middleware logs request."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mw = LoggingMiddleware(log_request=True, log_response=False)
        context = MiddlewareContext(request="test request")

        mw.before(context)

        # Should log request
        mock_logger.info.assert_called_once()
        assert "test request" in str(mock_logger.info.call_args)

    @patch('ai_automation_framework.core.middleware.get_logger')
    def test_logging_middleware_logs_response(self, mock_get_logger):
        """Test logging middleware logs response."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mw = LoggingMiddleware(log_request=False, log_response=True)
        context = MiddlewareContext(request="test")
        context.response = "test response"

        mw.after(context)

        # Should log response
        mock_logger.info.assert_called_once()
        call_str = str(mock_logger.info.call_args)
        assert "test response" in call_str
        assert "elapsed" in call_str

    @patch('ai_automation_framework.core.middleware.get_logger')
    def test_logging_middleware_logs_metadata(self, mock_get_logger):
        """Test logging middleware logs metadata when enabled."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mw = LoggingMiddleware(log_request=True, log_metadata=True)
        context = MiddlewareContext(request="test", user_id="123")

        mw.before(context)

        # Should log request and metadata
        assert mock_logger.info.call_count == 1
        assert mock_logger.debug.call_count == 1
        assert "user_id" in str(mock_logger.debug.call_args)

    @patch('ai_automation_framework.core.middleware.get_logger')
    def test_logging_middleware_warns_on_errors(self, mock_get_logger):
        """Test logging middleware warns when errors occurred."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mw = LoggingMiddleware(log_response=True)
        context = MiddlewareContext(request="test")
        context.response = "response"
        context.add_error(ValueError("test error"))

        mw.after(context)

        # Should log response and warn about errors
        mock_logger.info.assert_called_once()
        mock_logger.warning.assert_called_once()
        assert "Errors occurred" in str(mock_logger.warning.call_args)


# ============================================================================
# TimingMiddleware Tests
# ============================================================================


class TestTimingMiddleware:
    """Tests for TimingMiddleware."""

    def test_timing_middleware_tracks_time(self):
        """Test timing middleware tracks execution time."""
        mw = TimingMiddleware(store_in_context=True)
        context = MiddlewareContext(request="test")

        mw.before(context)

        # Simulate some work
        time.sleep(0.05)

        mw.after(context)

        # Should have stored elapsed time
        elapsed = context.get("elapsed_time")
        assert elapsed is not None
        assert elapsed >= 0.05

    @patch('ai_automation_framework.core.middleware.get_logger')
    def test_timing_middleware_warns_on_threshold(self, mock_get_logger):
        """Test timing middleware warns when threshold exceeded."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mw = TimingMiddleware(warn_threshold=0.01)
        context = MiddlewareContext(request="test")

        mw.before(context)
        time.sleep(0.02)  # Exceed threshold
        mw.after(context)

        # Should have logged warning
        mock_logger.warning.assert_called_once()
        call_str = str(mock_logger.warning.call_args)
        assert "threshold" in call_str

    @patch('ai_automation_framework.core.middleware.get_logger')
    def test_timing_middleware_info_under_threshold(self, mock_get_logger):
        """Test timing middleware logs info when under threshold."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mw = TimingMiddleware(warn_threshold=1.0)
        context = MiddlewareContext(request="test")

        mw.before(context)
        mw.after(context)

        # Should have logged info (not warning)
        mock_logger.info.assert_called_once()
        mock_logger.warning.assert_not_called()

    def test_timing_middleware_handles_missing_start(self):
        """Test timing middleware handles missing start time gracefully."""
        mw = TimingMiddleware()
        context = MiddlewareContext(request="test")

        # Call after without before
        mw.after(context)

        # Should not crash


# ============================================================================
# RetryMiddleware Tests
# ============================================================================


class TestRetryMiddleware:
    """Tests for RetryMiddleware."""

    def test_retry_middleware_succeeds_first_try(self):
        """Test retry middleware succeeds on first attempt."""
        mw = RetryMiddleware(max_attempts=3)

        func = Mock(return_value="success")
        result = mw.execute_with_retry(func)

        assert result == "success"
        func.assert_called_once()

    @patch('time.sleep')
    def test_retry_middleware_retries_on_failure(self, mock_sleep):
        """Test retry middleware retries on failure."""
        mw = RetryMiddleware(max_attempts=3, base_delay=1.0)

        # Fail twice, then succeed
        func = Mock(side_effect=[ValueError("error"), ValueError("error"), "success"])
        result = mw.execute_with_retry(func, exceptions=(ValueError,))

        assert result == "success"
        assert func.call_count == 3

        # Should have slept twice (after first two failures)
        assert mock_sleep.call_count == 2

    @patch('time.sleep')
    def test_retry_middleware_exponential_backoff(self, mock_sleep):
        """Test retry middleware uses exponential backoff."""
        mw = RetryMiddleware(
            max_attempts=3,
            base_delay=1.0,
            exponential_base=2.0
        )

        func = Mock(side_effect=[ValueError("error"), ValueError("error"), "success"])
        mw.execute_with_retry(func, exceptions=(ValueError,))

        # Should sleep with exponential backoff: 1.0, 2.0
        calls = [call(1.0), call(2.0)]
        mock_sleep.assert_has_calls(calls)

    @patch('time.sleep')
    def test_retry_middleware_max_delay(self, mock_sleep):
        """Test retry middleware respects max delay."""
        mw = RetryMiddleware(
            max_attempts=4,
            base_delay=10.0,
            max_delay=15.0,
            exponential_base=2.0
        )

        func = Mock(side_effect=[ValueError()] * 3 + ["success"])
        mw.execute_with_retry(func, exceptions=(ValueError,))

        # Delays would be: 10, 20, 40 but capped at 15
        # So actual delays: 10, 15, 15
        calls = [call(10.0), call(15.0), call(15.0)]
        mock_sleep.assert_has_calls(calls)

    def test_retry_middleware_raises_after_max_attempts(self):
        """Test retry middleware raises after max attempts."""
        mw = RetryMiddleware(max_attempts=3)

        func = Mock(side_effect=ValueError("persistent error"))

        with pytest.raises(ValueError, match="persistent error"):
            mw.execute_with_retry(func, exceptions=(ValueError,))

        assert func.call_count == 3

    def test_retry_middleware_only_catches_specified_exceptions(self):
        """Test retry middleware only catches specified exceptions."""
        mw = RetryMiddleware(max_attempts=3, exceptions=(ValueError,))

        func = Mock(side_effect=RuntimeError("wrong type"))

        # Should not retry RuntimeError
        with pytest.raises(RuntimeError):
            mw.execute_with_retry(func)

        func.assert_called_once()

    @pytest.mark.asyncio
    @patch('asyncio.sleep')
    async def test_retry_middleware_async(self, mock_sleep):
        """Test retry middleware async functionality."""
        # Make asyncio.sleep return immediately
        mock_sleep.return_value = asyncio.Future()
        mock_sleep.return_value.set_result(None)

        mw = RetryMiddleware(
            max_attempts=3,
            base_delay=1.0,
            exceptions=(ValueError,)
        )

        # Fail twice, then succeed
        async def async_func():
            if async_func.call_count < 2:
                async_func.call_count += 1
                raise ValueError("error")
            return "success"

        async_func.call_count = 0

        result = await mw.execute_with_retry_async(async_func)

        assert result == "success"
        assert mock_sleep.call_count == 2


# ============================================================================
# CacheMiddleware Tests
# ============================================================================


class TestCacheMiddleware:
    """Tests for CacheMiddleware."""

    @patch('ai_automation_framework.core.middleware.ResponseCache')
    def test_cache_middleware_cache_hit(self, mock_cache_class):
        """Test cache middleware returns cached response on hit."""
        mock_cache = Mock()
        mock_cache.get.return_value = "cached response"
        mock_cache_class.return_value = mock_cache

        mw = CacheMiddleware(cache=mock_cache)
        context = MiddlewareContext(request={"query": "test"})

        mw.before(context)

        # Should get from cache
        mock_cache.get.assert_called_once()

        # Should set response and short-circuit
        assert context.response == "cached response"
        assert context.get("_cache_hit") is True
        assert context.short_circuit is True

    @patch('ai_automation_framework.core.middleware.ResponseCache')
    def test_cache_middleware_cache_miss(self, mock_cache_class):
        """Test cache middleware handles cache miss."""
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache

        mw = CacheMiddleware(cache=mock_cache)
        context = MiddlewareContext(request={"query": "test"})

        mw.before(context)

        # Should get from cache
        mock_cache.get.assert_called_once()

        # Should not set response or short-circuit
        assert context.response is None
        assert context.get("_cache_hit") is False
        assert context.short_circuit is False

    @patch('ai_automation_framework.core.middleware.ResponseCache')
    def test_cache_middleware_stores_response(self, mock_cache_class):
        """Test cache middleware stores response after processing."""
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache

        mw = CacheMiddleware(cache=mock_cache)
        context = MiddlewareContext(request={"query": "test"})

        # Simulate cache miss
        mw.before(context)

        # Set response
        context.response = "new response"

        # After hook should store in cache
        mw.after(context)

        mock_cache.set.assert_called_once()
        assert mock_cache.set.call_args[1]["response"] == "new response"

    @patch('ai_automation_framework.core.middleware.ResponseCache')
    def test_cache_middleware_skips_store_on_hit(self, mock_cache_class):
        """Test cache middleware doesn't store when already cached."""
        mock_cache = Mock()
        mock_cache.get.return_value = "cached"
        mock_cache_class.return_value = mock_cache

        mw = CacheMiddleware(cache=mock_cache)
        context = MiddlewareContext(request={"query": "test"})

        mw.before(context)
        mw.after(context)

        # Should not call set
        mock_cache.set.assert_not_called()

    def test_cache_middleware_custom_key_generator(self):
        """Test cache middleware with custom key generator."""
        mock_cache = Mock()
        mock_cache.get.return_value = None

        def custom_key_gen(ctx):
            return f"custom_key_{ctx.request}"

        mw = CacheMiddleware(cache=mock_cache, key_generator=custom_key_gen)
        context = MiddlewareContext(request="test123")

        mw.before(context)

        assert context.get("_cache_key") == "custom_key_test123"

    @patch('ai_automation_framework.core.middleware.ResponseCache')
    def test_cache_middleware_handles_errors_gracefully(self, mock_cache_class):
        """Test cache middleware handles cache errors gracefully."""
        mock_cache = Mock()
        mock_cache.get.side_effect = Exception("cache error")
        mock_cache_class.return_value = mock_cache

        mw = CacheMiddleware(cache=mock_cache)
        context = MiddlewareContext(request={"query": "test"})

        # Should not raise, just mark as miss
        mw.before(context)

        assert context.get("_cache_hit") is False
        assert context.short_circuit is False


# ============================================================================
# RateLimitMiddleware Tests
# ============================================================================


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware."""

    def test_rate_limit_middleware_allows_under_limit(self):
        """Test rate limit middleware allows requests under limit."""
        mw = RateLimitMiddleware(max_requests=5, window_seconds=60.0)
        context = MiddlewareContext(request="test")

        # Should not raise
        mw.before(context)

        assert context.get("rate_limited") is False

    def test_rate_limit_middleware_blocks_over_limit(self):
        """Test rate limit middleware blocks requests over limit."""
        mw = RateLimitMiddleware(max_requests=3, window_seconds=60.0)

        # Make 3 requests (at the limit)
        for _ in range(3):
            context = MiddlewareContext(request="test")
            mw.before(context)

        # 4th request should be blocked
        context = MiddlewareContext(request="test")
        with pytest.raises(RuntimeError, match="Rate limit exceeded"):
            mw.before(context)

        assert context.get("rate_limited") is True
        assert context.short_circuit is True

    def test_rate_limit_middleware_window_expiration(self):
        """Test rate limit middleware resets after window expires."""
        mw = RateLimitMiddleware(max_requests=2, window_seconds=0.1)

        # Make 2 requests (at the limit)
        for _ in range(2):
            context = MiddlewareContext(request="test")
            mw.before(context)

        # Wait for window to expire
        time.sleep(0.15)

        # Should allow new request
        context = MiddlewareContext(request="test")
        mw.before(context)  # Should not raise

        assert context.get("rate_limited") is False

    def test_rate_limit_middleware_custom_key_func(self):
        """Test rate limit middleware with custom key function."""
        def key_func(ctx):
            return ctx.get("user_id", "anonymous")

        mw = RateLimitMiddleware(
            max_requests=2,
            window_seconds=60.0,
            key_func=key_func
        )

        # User 1 makes 2 requests
        for _ in range(2):
            context = MiddlewareContext(request="test")
            context.set("user_id", "user1")
            mw.before(context)

        # User 1 is now rate limited
        context = MiddlewareContext(request="test")
        context.set("user_id", "user1")
        with pytest.raises(RuntimeError, match="Rate limit exceeded"):
            mw.before(context)

        # But user 2 can still make requests
        context = MiddlewareContext(request="test")
        context.set("user_id", "user2")
        mw.before(context)  # Should not raise

        assert context.get("rate_limited") is False

    def test_rate_limit_middleware_sets_retry_after(self):
        """Test rate limit middleware sets retry_after in context."""
        mw = RateLimitMiddleware(max_requests=1, window_seconds=30.0)

        # Make 1 request (at the limit)
        context = MiddlewareContext(request="test")
        mw.before(context)

        # 2nd request should be blocked and set retry_after
        context = MiddlewareContext(request="test")
        with pytest.raises(RuntimeError):
            mw.before(context)

        assert context.get("retry_after") == 30.0
        assert context.get("rate_limit_key") == "default"


# ============================================================================
# MiddlewareStack Tests
# ============================================================================


class TestMiddlewareStack:
    """Tests for MiddlewareStack."""

    def test_middleware_stack_creation(self):
        """Test creating a middleware stack."""
        mw1 = Middleware(name="MW1")
        mw2 = Middleware(name="MW2")

        stack = MiddlewareStack([mw1, mw2])

        assert len(stack) == 2
        assert list(stack) == [mw1, mw2]

    def test_middleware_stack_add(self):
        """Test adding middleware to stack."""
        stack = MiddlewareStack()
        mw1 = Middleware(name="MW1")
        mw2 = Middleware(name="MW2")

        stack.add(mw1).add(mw2)

        assert len(stack) == 2
        assert list(stack) == [mw1, mw2]

    def test_middleware_stack_remove(self):
        """Test removing middleware from stack."""
        mw1 = Middleware(name="MW1")
        mw2 = Middleware(name="MW2")
        stack = MiddlewareStack([mw1, mw2])

        stack.remove(mw1)

        assert len(stack) == 1
        assert list(stack) == [mw2]

    def test_middleware_stack_clear(self):
        """Test clearing middleware stack."""
        mw1 = Middleware(name="MW1")
        mw2 = Middleware(name="MW2")
        stack = MiddlewareStack([mw1, mw2])

        stack.clear()

        assert len(stack) == 0

    def test_middleware_stack_execution_order(self):
        """Test middleware stack executes in correct order."""
        order = []

        class TrackingMiddleware(Middleware):
            def __init__(self, name):
                super().__init__(name=name)
                self.order = order

            def before(self, context):
                self.order.append(f"{self.name}_before")

            def after(self, context):
                self.order.append(f"{self.name}_after")

        mw1 = TrackingMiddleware("MW1")
        mw2 = TrackingMiddleware("MW2")
        mw3 = TrackingMiddleware("MW3")

        stack = MiddlewareStack([mw1, mw2, mw3])

        def handler(request):
            order.append("handler")
            return f"processed: {request}"

        result = stack.execute(handler, request="test")

        # Before hooks in order, handler, after hooks in reverse
        assert order == [
            "MW1_before",
            "MW2_before",
            "MW3_before",
            "handler",
            "MW3_after",
            "MW2_after",
            "MW1_after",
        ]

        assert result == "processed: test"

    def test_middleware_stack_short_circuit(self):
        """Test middleware stack short-circuits when requested."""
        order = []

        class ShortCircuitMiddleware(Middleware):
            def before(self, context):
                order.append(f"{self.name}_before")
                if self.name == "MW2":
                    context.response = "short_circuited"
                    context.stop()

            def after(self, context):
                order.append(f"{self.name}_after")

        mw1 = ShortCircuitMiddleware(name="MW1")
        mw2 = ShortCircuitMiddleware(name="MW2")
        mw3 = ShortCircuitMiddleware(name="MW3")

        stack = MiddlewareStack([mw1, mw2, mw3])

        def handler(request):
            order.append("handler")
            return f"processed: {request}"

        result = stack.execute(handler, request="test")

        # Should stop at MW2, not execute MW3 before or handler
        # When short-circuited, remaining before hooks and handler are skipped
        # But it immediately returns without running after hooks
        assert order == [
            "MW1_before",
            "MW2_before",
        ]

        assert result == "short_circuited"
        assert "handler" not in order
        assert "MW3_before" not in order
        assert "MW1_after" not in order
        assert "MW2_after" not in order

    def test_middleware_stack_disabled_middleware(self):
        """Test middleware stack skips disabled middleware."""
        order = []

        class TrackingMiddleware(Middleware):
            def before(self, context):
                order.append(f"{self.name}_before")

            def after(self, context):
                order.append(f"{self.name}_after")

        mw1 = TrackingMiddleware(name="MW1", enabled=True)
        mw2 = TrackingMiddleware(name="MW2", enabled=False)
        mw3 = TrackingMiddleware(name="MW3", enabled=True)

        stack = MiddlewareStack([mw1, mw2, mw3])

        def handler(request):
            order.append("handler")
            return "result"

        stack.execute(handler, request="test")

        # MW2 should be skipped
        assert "MW2_before" not in order
        assert "MW2_after" not in order
        assert order == [
            "MW1_before",
            "MW3_before",
            "handler",
            "MW3_after",
            "MW1_after",
        ]

    def test_middleware_stack_error_handling(self):
        """Test middleware stack handles errors appropriately."""
        class ErrorMiddleware(Middleware):
            def before(self, context):
                if self.name == "ErrorMW":
                    raise ValueError("test error")

        mw1 = Middleware(name="MW1")
        error_mw = ErrorMiddleware(name="ErrorMW")
        mw3 = Middleware(name="MW3")

        stack = MiddlewareStack([mw1, error_mw, mw3])

        def handler(request):
            return "result"

        # Should propagate error
        with pytest.raises(ValueError, match="test error"):
            stack.execute(handler, request="test")

    @pytest.mark.asyncio
    async def test_middleware_stack_async_execution(self):
        """Test middleware stack async execution."""
        order = []

        class AsyncTrackingMiddleware(Middleware):
            async def before_async(self, context):
                await asyncio.sleep(0.001)
                order.append(f"{self.name}_before")

            async def after_async(self, context):
                await asyncio.sleep(0.001)
                order.append(f"{self.name}_after")

        mw1 = AsyncTrackingMiddleware(name="MW1")
        mw2 = AsyncTrackingMiddleware(name="MW2")

        stack = MiddlewareStack([mw1, mw2])

        async def handler(request):
            order.append("handler")
            return f"processed: {request}"

        result = await stack.execute_async(handler, request="test")

        assert order == [
            "MW1_before",
            "MW2_before",
            "handler",
            "MW2_after",
            "MW1_after",
        ]

        assert result == "processed: test"

    def test_middleware_stack_context_kwargs(self):
        """Test middleware stack passes context kwargs."""
        stack = MiddlewareStack()

        def handler(request):
            return request

        result = stack.execute(
            handler,
            request="test",
            user_id="123",
            session="abc"
        )

        assert result == "test"


# ============================================================================
# middleware_decorator Tests
# ============================================================================


class TestMiddlewareDecorator:
    """Tests for middleware_decorator."""

    def test_middleware_decorator_basic(self):
        """Test basic middleware decorator usage."""
        order = []

        class TrackingMiddleware(Middleware):
            def before(self, context):
                order.append(f"{self.name}_before")

            def after(self, context):
                order.append(f"{self.name}_after")

        @middleware_decorator(
            TrackingMiddleware(name="MW1"),
            TrackingMiddleware(name="MW2")
        )
        def my_handler(request):
            order.append("handler")
            return f"processed: {request}"

        result = my_handler("test")

        assert order == [
            "MW1_before",
            "MW2_before",
            "handler",
            "MW2_after",
            "MW1_after",
        ]

        assert result == "processed: test"

    @pytest.mark.asyncio
    async def test_middleware_decorator_async(self):
        """Test middleware decorator with async function."""
        order = []

        class AsyncTrackingMiddleware(Middleware):
            async def before_async(self, context):
                order.append(f"{self.name}_before")

            async def after_async(self, context):
                order.append(f"{self.name}_after")

        @middleware_decorator(
            AsyncTrackingMiddleware(name="MW1"),
            use_async=True
        )
        async def my_async_handler(request):
            order.append("handler")
            return f"processed: {request}"

        result = await my_async_handler("test")

        assert order == [
            "MW1_before",
            "handler",
            "MW1_after",
        ]

        assert result == "processed: test"

    def test_middleware_decorator_with_logging_and_timing(self):
        """Test middleware decorator with real middleware."""
        @middleware_decorator(
            LoggingMiddleware(log_request=False, log_response=False),
            TimingMiddleware(store_in_context=False)
        )
        def my_handler(request):
            return f"processed: {request}"

        result = my_handler("test")

        assert result == "processed: test"

    def test_middleware_decorator_preserves_function_metadata(self):
        """Test middleware decorator preserves function metadata."""
        @middleware_decorator(Middleware())
        def my_handler(request):
            """Handler docstring."""
            return request

        assert my_handler.__name__ == "my_handler"
        assert my_handler.__doc__ == "Handler docstring."


# ============================================================================
# Integration Tests
# ============================================================================


class TestMiddlewareIntegration:
    """Integration tests for middleware system."""

    def test_full_pipeline_with_caching(self):
        """Test full pipeline with caching middleware."""
        mock_cache = Mock()
        mock_cache.get.return_value = None  # Cache miss first time

        call_count = 0

        def expensive_handler(request):
            nonlocal call_count
            call_count += 1
            return f"result_{request}"

        stack = MiddlewareStack([
            LoggingMiddleware(log_request=False, log_response=False),
            CacheMiddleware(cache=mock_cache),
            TimingMiddleware(store_in_context=False),
        ])

        # First call - cache miss
        result1 = stack.execute(expensive_handler, request="test")
        assert result1 == "result_test"
        assert call_count == 1
        mock_cache.set.assert_called_once()

        # Second call - cache hit
        mock_cache.get.return_value = "result_test"
        result2 = stack.execute(expensive_handler, request="test")
        assert result2 == "result_test"
        assert call_count == 1  # Handler not called again

    def test_full_pipeline_with_retry(self):
        """Test full pipeline with retry middleware."""
        call_count = 0

        def flaky_handler(request):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("temporary error")
            return f"result_{request}"

        retry_mw = RetryMiddleware(
            max_attempts=3,
            base_delay=0.01,
            exceptions=(ValueError,)
        )

        stack = MiddlewareStack([
            LoggingMiddleware(log_request=False, log_response=False),
            TimingMiddleware(store_in_context=False),
        ])

        # Handler fails, but we wrap it with retry
        result = retry_mw.execute_with_retry(
            lambda: stack.execute(flaky_handler, request="test")
        )

        assert result == "result_test"
        assert call_count == 3

    def test_full_pipeline_with_rate_limiting(self):
        """Test full pipeline with rate limiting."""
        stack = MiddlewareStack([
            RateLimitMiddleware(max_requests=2, window_seconds=60.0),
            LoggingMiddleware(log_request=False, log_response=False),
        ])

        def handler(request):
            return f"result_{request}"

        # First two requests succeed
        result1 = stack.execute(handler, request="test1")
        result2 = stack.execute(handler, request="test2")

        assert result1 == "result_test1"
        assert result2 == "result_test2"

        # Third request should be rate limited
        with pytest.raises(RuntimeError, match="Rate limit exceeded"):
            stack.execute(handler, request="test3")

    @pytest.mark.asyncio
    async def test_async_pipeline_integration(self):
        """Test async pipeline with multiple middleware."""
        order = []

        class AsyncLoggingMiddleware(Middleware):
            async def before_async(self, context):
                order.append("log_before")

            async def after_async(self, context):
                order.append("log_after")

        class AsyncTimingMiddleware(Middleware):
            async def before_async(self, context):
                order.append("timing_before")

            async def after_async(self, context):
                order.append("timing_after")

        stack = MiddlewareStack([
            AsyncLoggingMiddleware(name="Logger"),
            AsyncTimingMiddleware(name="Timer"),
        ])

        async def handler(request):
            order.append("handler")
            return f"result_{request}"

        result = await stack.execute_async(handler, request="test")

        assert result == "result_test"
        assert order == [
            "log_before",
            "timing_before",
            "handler",
            "timing_after",
            "log_after",
        ]
