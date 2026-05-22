"""
Comprehensive unit tests for Circuit Breaker module.

Tests cover:
- Circuit state transitions (CLOSED → OPEN → HALF_OPEN → CLOSED)
- Failure threshold triggers
- Recovery timeout behavior
- Decorator functionality (sync and async)
- Statistics tracking
- Registry management
- Thread safety
"""

import asyncio
import time
import pytest
from unittest.mock import Mock, patch
from ai_automation_framework.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerRegistry,
    CircuitBreakerStats,
    CircuitState,
    get_breaker,
    get_registry,
    circuit_breaker,
)


@pytest.mark.unit
class TestCircuitBreakerStats:
    """Test CircuitBreakerStats class."""

    def test_stats_initialization(self):
        """Test that stats are initialized with zero values."""
        stats = CircuitBreakerStats()
        assert stats.success_count == 0
        assert stats.failure_count == 0
        assert stats.consecutive_failures == 0
        assert stats.consecutive_successes == 0
        assert stats.total_requests == 0
        assert stats.rejected_requests == 0

    def test_record_success(self):
        """Test recording a successful call."""
        stats = CircuitBreakerStats()
        stats.record_success()

        assert stats.success_count == 1
        assert stats.consecutive_successes == 1
        assert stats.consecutive_failures == 0
        assert stats.total_requests == 1
        assert stats.last_success_time is not None

    def test_record_failure(self):
        """Test recording a failed call."""
        stats = CircuitBreakerStats()
        stats.record_failure()

        assert stats.failure_count == 1
        assert stats.consecutive_failures == 1
        assert stats.consecutive_successes == 0
        assert stats.total_requests == 1
        assert stats.last_failure_time is not None

    def test_record_rejected(self):
        """Test recording a rejected call."""
        stats = CircuitBreakerStats()
        stats.record_rejected()

        assert stats.rejected_requests == 1
        assert stats.total_requests == 0  # Rejected calls don't count in total

    def test_failure_rate_calculation(self):
        """Test failure rate calculation."""
        stats = CircuitBreakerStats()

        # No requests yet
        assert stats.get_failure_rate() == 0.0

        # 3 successes, 2 failures
        stats.record_success()
        stats.record_success()
        stats.record_success()
        stats.record_failure()
        stats.record_failure()

        assert stats.get_failure_rate() == 0.4  # 2/5 = 0.4

    def test_reset_stats(self):
        """Test resetting all statistics."""
        stats = CircuitBreakerStats()
        stats.record_success()
        stats.record_failure()
        stats.record_rejected()

        stats.reset()

        assert stats.success_count == 0
        assert stats.failure_count == 0
        assert stats.rejected_requests == 0
        assert stats.total_requests == 0

    def test_reset_consecutive_counts(self):
        """Test resetting consecutive counts only."""
        stats = CircuitBreakerStats()
        stats.record_success()
        stats.record_success()
        stats.record_failure()

        stats.reset_consecutive_counts()

        assert stats.consecutive_successes == 0
        assert stats.consecutive_failures == 0
        assert stats.success_count == 2  # Not reset
        assert stats.failure_count == 1  # Not reset

    def test_stats_dict(self):
        """Test converting stats to dictionary."""
        stats = CircuitBreakerStats()
        stats.record_success()
        stats.record_failure()

        stats_dict = stats.get_stats_dict()

        assert "success_count" in stats_dict
        assert "failure_count" in stats_dict
        assert "failure_rate" in stats_dict
        assert stats_dict["success_count"] == 1
        assert stats_dict["failure_count"] == 1


@pytest.mark.unit
class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    def test_initialization(self):
        """Test circuit breaker initialization."""
        breaker = CircuitBreaker(
            name="test_breaker",
            failure_threshold=3,
            recovery_timeout=30.0
        )

        assert breaker.name == "test_breaker"
        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 30.0
        assert breaker.state == CircuitState.CLOSED

    def test_state_transition_closed_to_open(self):
        """Test transition from CLOSED to OPEN when failure threshold is reached."""
        breaker = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60.0)

        # Simulate failures
        for i in range(3):
            try:
                with breaker:
                    raise ValueError("Test error")
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN
        assert breaker.stats.consecutive_failures == 0  # Reset after transition

    def test_circuit_open_rejects_calls(self):
        """Test that OPEN circuit rejects calls immediately."""
        breaker = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=60.0)

        # Open the circuit
        for _ in range(2):
            try:
                with breaker:
                    raise ValueError("Test error")
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN

        # Next call should be rejected
        with pytest.raises(CircuitBreakerError):
            with breaker:
                pass

        assert breaker.stats.rejected_requests == 1

    def test_recovery_timeout_transition_to_half_open(self):
        """Test transition from OPEN to HALF_OPEN after recovery timeout."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.1  # Short timeout for testing
        )

        # Open the circuit
        for _ in range(2):
            try:
                with breaker:
                    raise ValueError("Test error")
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.15)

        # Next call should transition to HALF_OPEN
        try:
            with breaker:
                pass  # Success
        except CircuitBreakerError:
            pytest.fail("Should have transitioned to HALF_OPEN")

        assert breaker.state == CircuitState.HALF_OPEN

    def test_half_open_success_closes_circuit(self):
        """Test that successful calls in HALF_OPEN state close the circuit."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.1,
            success_threshold=2
        )

        # Open the circuit
        for _ in range(2):
            try:
                with breaker:
                    raise ValueError("Test error")
            except ValueError:
                pass

        time.sleep(0.15)

        # Successful calls in HALF_OPEN
        for _ in range(2):
            with breaker:
                pass  # Success

        assert breaker.state == CircuitState.CLOSED

    def test_half_open_failure_reopens_circuit(self):
        """Test that failure in HALF_OPEN state reopens the circuit."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.1
        )

        # Open the circuit
        for _ in range(2):
            try:
                with breaker:
                    raise ValueError("Test error")
            except ValueError:
                pass

        time.sleep(0.15)

        # Fail in HALF_OPEN
        try:
            with breaker:
                raise ValueError("Still failing")
        except ValueError:
            pass

        assert breaker.state == CircuitState.OPEN

    def test_half_open_max_calls_limit(self):
        """Test that HALF_OPEN state limits concurrent calls."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=1,
            recovery_timeout=0.1,
            half_open_max_calls=1
        )

        # Open the circuit
        try:
            with breaker:
                raise ValueError("Test error")
        except ValueError:
            pass

        time.sleep(0.15)

        # First call in HALF_OPEN should work
        # We need to simulate concurrent access
        # Since this is synchronous, we'll test the rejection logic
        breaker._before_call()  # Increments half_open_calls

        # Second call should be rejected
        with pytest.raises(CircuitBreakerError) as exc_info:
            breaker._before_call()

        assert "HALF_OPEN" in str(exc_info.value)

    def test_decorator_sync_success(self):
        """Test decorator with successful synchronous function."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        @breaker.decorator
        def test_func(x, y):
            return x + y

        result = test_func(2, 3)

        assert result == 5
        assert breaker.stats.success_count == 1
        assert breaker.state == CircuitState.CLOSED

    def test_decorator_sync_failure(self):
        """Test decorator with failing synchronous function."""
        breaker = CircuitBreaker(name="test", failure_threshold=2)

        @breaker.decorator
        def test_func():
            raise ValueError("Test error")

        # First failure
        with pytest.raises(ValueError):
            test_func()

        # Second failure should open circuit
        with pytest.raises(ValueError):
            test_func()

        assert breaker.state == CircuitState.OPEN
        assert breaker.stats.failure_count == 2

    @pytest.mark.asyncio
    async def test_async_decorator_success(self):
        """Test async decorator with successful function."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        @breaker.async_decorator
        async def test_func(x, y):
            await asyncio.sleep(0.01)
            return x + y

        result = await test_func(2, 3)

        assert result == 5
        assert breaker.stats.success_count == 1

    @pytest.mark.asyncio
    async def test_async_decorator_failure(self):
        """Test async decorator with failing function."""
        breaker = CircuitBreaker(name="test", failure_threshold=2)

        @breaker.async_decorator
        async def test_func():
            await asyncio.sleep(0.01)
            raise ValueError("Test error")

        # Trigger failures
        for _ in range(2):
            with pytest.raises(ValueError):
                await test_func()

        assert breaker.state == CircuitState.OPEN

    def test_call_method(self):
        """Test call() method for wrapping functions."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        def test_func(x, y):
            return x * y

        result = breaker.call(test_func, 3, 4)

        assert result == 12
        assert breaker.stats.success_count == 1

    @pytest.mark.asyncio
    async def test_call_async_method(self):
        """Test call_async() method."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        async def test_func(x, y):
            await asyncio.sleep(0.01)
            return x * y

        result = await breaker.call_async(test_func, 3, 4)

        assert result == 12
        assert breaker.stats.success_count == 1

    def test_expected_exception_filter(self):
        """Test that only expected exceptions trigger circuit breaker."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            expected_exception=ValueError
        )

        # ValueError should count as failure
        try:
            with breaker:
                raise ValueError("Expected")
        except ValueError:
            pass

        assert breaker.stats.failure_count == 1

        # RuntimeError should not count (will propagate but not affect breaker)
        try:
            with breaker:
                raise RuntimeError("Unexpected")
        except RuntimeError:
            pass

        # Circuit should still be CLOSED because RuntimeError doesn't count
        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.failure_count == 1

    def test_reset_circuit(self):
        """Test manual reset of circuit breaker."""
        breaker = CircuitBreaker(name="test", failure_threshold=2)

        # Open the circuit
        for _ in range(2):
            try:
                with breaker:
                    raise ValueError("Test error")
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN

        # Reset
        breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.success_count == 0
        assert breaker.stats.failure_count == 0

    def test_get_state_info(self):
        """Test getting state information."""
        breaker = CircuitBreaker(
            name="test_breaker",
            failure_threshold=5,
            recovery_timeout=60.0
        )

        info = breaker.get_state_info()

        assert info["name"] == "test_breaker"
        assert info["state"] == "closed"
        assert info["failure_threshold"] == 5
        assert info["recovery_timeout"] == 60.0
        assert "stats" in info

    def test_callbacks_on_open(self):
        """Test that on_open callback is triggered."""
        callback_mock = Mock()
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            on_open=callback_mock
        )

        # Trigger circuit opening
        for _ in range(2):
            try:
                with breaker:
                    raise ValueError("Test error")
            except ValueError:
                pass

        callback_mock.assert_called_once_with("test")

    def test_callbacks_on_close(self):
        """Test that on_close callback is triggered."""
        callback_mock = Mock()
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.1,
            success_threshold=1,
            on_close=callback_mock
        )

        # Open circuit
        for _ in range(2):
            try:
                with breaker:
                    raise ValueError("Test error")
            except ValueError:
                pass

        time.sleep(0.15)

        # Close circuit
        with breaker:
            pass

        callback_mock.assert_called_once_with("test")

    def test_callbacks_on_half_open(self):
        """Test that on_half_open callback is triggered."""
        callback_mock = Mock()
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.1,
            on_half_open=callback_mock
        )

        # Open circuit
        for _ in range(2):
            try:
                with breaker:
                    raise ValueError("Test error")
            except ValueError:
                pass

        time.sleep(0.15)

        # Transition to half-open
        with breaker:
            pass

        callback_mock.assert_called_once_with("test")


@pytest.mark.unit
class TestCircuitBreakerRegistry:
    """Test CircuitBreakerRegistry class."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = CircuitBreakerRegistry()
        assert len(registry.get_all()) == 0

    def test_register_breaker(self):
        """Test registering a circuit breaker."""
        registry = CircuitBreakerRegistry()
        breaker = CircuitBreaker(name="test")

        registry.register(breaker)

        assert registry.get("test") == breaker

    def test_register_duplicate_name_raises_error(self):
        """Test that registering duplicate name raises ValueError."""
        registry = CircuitBreakerRegistry()
        breaker1 = CircuitBreaker(name="test")
        breaker2 = CircuitBreaker(name="test")

        registry.register(breaker1)

        with pytest.raises(ValueError):
            registry.register(breaker2)

    def test_get_or_create(self):
        """Test get_or_create functionality."""
        registry = CircuitBreakerRegistry()

        # Create new
        breaker1 = registry.get_or_create("test", failure_threshold=5)
        assert breaker1.name == "test"
        assert breaker1.failure_threshold == 5

        # Get existing
        breaker2 = registry.get_or_create("test", failure_threshold=10)
        assert breaker1 is breaker2
        assert breaker2.failure_threshold == 5  # Original settings preserved

    def test_get_nonexistent_breaker(self):
        """Test getting a non-existent breaker returns None."""
        registry = CircuitBreakerRegistry()
        assert registry.get("nonexistent") is None

    def test_remove_breaker(self):
        """Test removing a circuit breaker."""
        registry = CircuitBreakerRegistry()
        breaker = CircuitBreaker(name="test")
        registry.register(breaker)

        result = registry.remove("test")

        assert result is True
        assert registry.get("test") is None

    def test_remove_nonexistent_breaker(self):
        """Test removing non-existent breaker returns False."""
        registry = CircuitBreakerRegistry()
        result = registry.remove("nonexistent")
        assert result is False

    def test_get_all_names(self):
        """Test getting all registered breaker names."""
        registry = CircuitBreakerRegistry()
        registry.get_or_create("breaker1")
        registry.get_or_create("breaker2")
        registry.get_or_create("breaker3")

        names = registry.get_all_names()

        assert len(names) == 3
        assert "breaker1" in names
        assert "breaker2" in names
        assert "breaker3" in names

    def test_get_summary(self):
        """Test getting summary of all breakers."""
        registry = CircuitBreakerRegistry()
        registry.get_or_create("breaker1", failure_threshold=5)
        registry.get_or_create("breaker2", failure_threshold=10)

        summary = registry.get_summary()

        assert len(summary) == 2
        assert all("name" in item for item in summary)
        assert all("state" in item for item in summary)

    def test_reset_all(self):
        """Test resetting all circuit breakers."""
        registry = CircuitBreakerRegistry()
        breaker1 = registry.get_or_create("breaker1", failure_threshold=1)
        breaker2 = registry.get_or_create("breaker2", failure_threshold=1)

        # Open both circuits
        for breaker in [breaker1, breaker2]:
            try:
                with breaker:
                    raise ValueError("Test error")
            except ValueError:
                pass

        assert breaker1.state == CircuitState.OPEN
        assert breaker2.state == CircuitState.OPEN

        registry.reset_all()

        assert breaker1.state == CircuitState.CLOSED
        assert breaker2.state == CircuitState.CLOSED

    def test_clear_registry(self):
        """Test clearing all breakers from registry."""
        registry = CircuitBreakerRegistry()
        registry.get_or_create("breaker1")
        registry.get_or_create("breaker2")

        assert len(registry.get_all()) == 2

        registry.clear()

        assert len(registry.get_all()) == 0


@pytest.mark.unit
class TestGlobalFunctions:
    """Test global helper functions."""

    def test_get_registry(self):
        """Test getting global registry."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2  # Same instance

    def test_get_breaker(self):
        """Test getting breaker from global registry."""
        breaker = get_breaker("test_global", failure_threshold=7)

        assert breaker.name == "test_global"
        assert breaker.failure_threshold == 7

    def test_circuit_breaker_decorator(self):
        """Test global circuit_breaker decorator."""

        @circuit_breaker("decorated_func", failure_threshold=2)
        def test_func(x):
            if x < 0:
                raise ValueError("Negative value")
            return x * 2

        # Should work
        result = test_func(5)
        assert result == 10

        # Should fail and count toward threshold
        with pytest.raises(ValueError):
            test_func(-1)

        with pytest.raises(ValueError):
            test_func(-1)

        # Circuit should be open
        with pytest.raises(CircuitBreakerError):
            test_func(5)

    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_async(self):
        """Test global circuit_breaker decorator with async function."""

        @circuit_breaker("async_decorated_func", failure_threshold=2)
        async def test_func(x):
            await asyncio.sleep(0.01)
            if x < 0:
                raise ValueError("Negative value")
            return x * 2

        # Should work
        result = await test_func(5)
        assert result == 10

        # Should fail
        with pytest.raises(ValueError):
            await test_func(-1)


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_failure_threshold(self):
        """Test that zero failure threshold behaves correctly."""
        breaker = CircuitBreaker(name="test", failure_threshold=0)

        # Should still be in CLOSED state initially
        assert breaker.state == CircuitState.CLOSED

    def test_very_short_recovery_timeout(self):
        """Test very short recovery timeout."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=1,
            recovery_timeout=0.001
        )

        # Open circuit
        try:
            with breaker:
                raise ValueError("Test error")
        except ValueError:
            pass

        # Very short wait
        time.sleep(0.002)

        # Should transition to HALF_OPEN
        with breaker:
            pass

        assert breaker.state == CircuitState.HALF_OPEN

    def test_multiple_exception_types(self):
        """Test handling multiple exception types."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            expected_exception=(ValueError, RuntimeError)
        )

        # ValueError should count
        try:
            with breaker:
                raise ValueError("Error 1")
        except ValueError:
            pass

        # RuntimeError should count
        try:
            with breaker:
                raise RuntimeError("Error 2")
        except RuntimeError:
            pass

        assert breaker.state == CircuitState.OPEN

    def test_concurrent_access_thread_safety(self):
        """Test thread-safe concurrent access."""
        import threading

        breaker = CircuitBreaker(name="test", failure_threshold=10)
        success_count = [0]

        def worker():
            try:
                with breaker:
                    time.sleep(0.001)
                    success_count[0] += 1
            except Exception:
                pass

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert breaker.stats.success_count == 10
        assert success_count[0] == 10
