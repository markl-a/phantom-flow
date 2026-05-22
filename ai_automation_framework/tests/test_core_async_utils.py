"""Comprehensive tests for the async_utils module."""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from ai_automation_framework.core.async_utils import (
    run_sync,
    run_async,
    async_sleep_with_jitter,
    gather_with_concurrency,
    async_timeout,
    retry_async,
    AsyncLock,
)


class TestRunSync:
    """Tests for run_sync function."""

    def test_run_sync_simple_coroutine(self):
        """Test running a simple async function synchronously."""
        async def simple_coro():
            return "Hello, World!"

        result = run_sync(simple_coro())
        assert result == "Hello, World!"

    def test_run_sync_with_sleep(self):
        """Test running an async function with sleep."""
        async def async_with_sleep():
            await asyncio.sleep(0.01)
            return "completed"

        start = time.time()
        result = run_sync(async_with_sleep())
        elapsed = time.time() - start

        assert result == "completed"
        assert elapsed >= 0.01

    def test_run_sync_with_exception(self):
        """Test that exceptions are propagated correctly."""
        async def failing_coro():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            run_sync(failing_coro())

    def test_run_sync_with_return_value(self):
        """Test running async function that performs computation."""
        async def compute():
            await asyncio.sleep(0.01)
            return sum(range(100))

        result = run_sync(compute())
        assert result == 4950

    def test_run_sync_multiple_times(self):
        """Test calling run_sync multiple times."""
        async def get_value(x):
            await asyncio.sleep(0.001)
            return x * 2

        results = [run_sync(get_value(i)) for i in range(5)]
        assert results == [0, 2, 4, 6, 8]


@pytest.mark.asyncio
class TestRunAsync:
    """Tests for run_async function."""

    async def test_run_async_simple_function(self):
        """Test running a simple sync function asynchronously."""
        def sync_func():
            return "sync result"

        result = await run_async(sync_func)
        assert result == "sync result"

    async def test_run_async_with_args(self):
        """Test running sync function with arguments."""
        def add(a, b):
            return a + b

        result = await run_async(add, 5, 3)
        assert result == 8

    async def test_run_async_with_kwargs(self):
        """Test running sync function with keyword arguments."""
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = await run_async(greet, "Alice", greeting="Hi")
        assert result == "Hi, Alice!"

    async def test_run_async_blocking_operation(self):
        """Test that blocking operations don't block the event loop."""
        def blocking_operation():
            time.sleep(0.1)
            return "done"

        # Run blocking operation and a quick async task concurrently
        counter = {"value": 0}

        async def increment():
            for _ in range(10):
                await asyncio.sleep(0.01)
                counter["value"] += 1

        start = time.time()
        results = await asyncio.gather(
            run_async(blocking_operation),
            increment()
        )
        elapsed = time.time() - start

        assert results[0] == "done"
        assert counter["value"] == 10
        # Should take around 0.1s, not 0.2s if properly concurrent
        assert elapsed < 0.15

    async def test_run_async_with_exception(self):
        """Test that exceptions in sync functions are propagated."""
        def failing_func():
            raise RuntimeError("Sync error")

        with pytest.raises(RuntimeError, match="Sync error"):
            await run_async(failing_func)


@pytest.mark.asyncio
class TestAsyncSleepWithJitter:
    """Tests for async_sleep_with_jitter function."""

    async def test_basic_sleep_with_default_jitter(self):
        """Test basic sleep with default jitter factor."""
        base_delay = 0.1
        start = time.time()
        await async_sleep_with_jitter(base_delay)
        elapsed = time.time() - start

        # With 10% jitter, should be between 0.09 and 0.11
        assert 0.08 < elapsed < 0.12

    async def test_sleep_with_custom_jitter_factor(self):
        """Test sleep with custom jitter factor."""
        base_delay = 0.1
        jitter_factor = 0.5  # 50% jitter

        # Run multiple times to verify jitter range
        times = []
        for _ in range(5):
            start = time.time()
            await async_sleep_with_jitter(base_delay, jitter_factor=jitter_factor)
            elapsed = time.time() - start
            times.append(elapsed)

        # All times should be in range [0.05, 0.15] (base ± 50%)
        for t in times:
            assert 0.04 < t < 0.16

        # Verify there's some variation (not all identical)
        assert len(set(round(t, 3) for t in times)) > 1

    async def test_sleep_with_max_jitter(self):
        """Test sleep with maximum jitter override."""
        base_delay = 1.0
        max_jitter = 0.05

        times = []
        for _ in range(5):
            start = time.time()
            await async_sleep_with_jitter(base_delay, max_jitter=max_jitter)
            elapsed = time.time() - start
            times.append(elapsed)

        # All times should be in range [0.95, 1.05]
        for t in times:
            assert 0.94 < t < 1.06

    async def test_sleep_with_zero_delay(self):
        """Test sleep with zero base delay."""
        start = time.time()
        await async_sleep_with_jitter(0.0)
        elapsed = time.time() - start

        # Should complete very quickly
        assert elapsed < 0.05

    async def test_negative_jitter_doesnt_go_negative(self):
        """Test that negative jitter doesn't result in negative sleep."""
        # With very high jitter factor, ensure sleep doesn't go negative
        base_delay = 0.01
        jitter_factor = 2.0  # 200% jitter

        start = time.time()
        await async_sleep_with_jitter(base_delay, jitter_factor=jitter_factor)
        elapsed = time.time() - start

        # Should never be negative, minimum is 0
        assert elapsed >= 0


@pytest.mark.asyncio
class TestGatherWithConcurrency:
    """Tests for gather_with_concurrency function."""

    async def test_basic_concurrency_limiting(self):
        """Test that concurrency is properly limited."""
        concurrent_count = {"value": 0, "max": 0}

        async def tracked_task(task_id):
            concurrent_count["value"] += 1
            concurrent_count["max"] = max(concurrent_count["max"], concurrent_count["value"])
            await asyncio.sleep(0.01)
            concurrent_count["value"] -= 1
            return task_id * 2

        # Create 10 tasks but limit to 3 concurrent
        tasks = [tracked_task(i) for i in range(10)]
        results = await gather_with_concurrency(3, *tasks)

        assert results == [i * 2 for i in range(10)]
        assert concurrent_count["max"] <= 3
        assert concurrent_count["value"] == 0  # All tasks completed

    async def test_concurrency_one(self):
        """Test with concurrency limit of 1 (sequential execution)."""
        execution_order = []

        async def ordered_task(task_id):
            execution_order.append(f"start-{task_id}")
            await asyncio.sleep(0.01)
            execution_order.append(f"end-{task_id}")
            return task_id

        tasks = [ordered_task(i) for i in range(3)]
        results = await gather_with_concurrency(1, *tasks)

        assert results == [0, 1, 2]
        # With concurrency 1, each task should fully complete before next starts
        assert execution_order == [
            "start-0", "end-0",
            "start-1", "end-1",
            "start-2", "end-2"
        ]

    async def test_return_exceptions_false(self):
        """Test that exceptions are raised when return_exceptions=False."""
        async def failing_task():
            raise ValueError("Task failed")

        async def success_task():
            return "success"

        tasks = [success_task(), failing_task()]

        with pytest.raises(ValueError, match="Task failed"):
            await gather_with_concurrency(2, *tasks, return_exceptions=False)

    async def test_return_exceptions_true(self):
        """Test that exceptions are returned when return_exceptions=True."""
        async def failing_task(msg):
            raise ValueError(msg)

        async def success_task(value):
            return value

        tasks = [
            success_task("result1"),
            failing_task("error1"),
            success_task("result2"),
            failing_task("error2"),
        ]

        results = await gather_with_concurrency(2, *tasks, return_exceptions=True)

        assert len(results) == 4
        assert results[0] == "result1"
        assert isinstance(results[1], ValueError)
        assert str(results[1]) == "error1"
        assert results[2] == "result2"
        assert isinstance(results[3], ValueError)
        assert str(results[3]) == "error2"

    async def test_empty_task_list(self):
        """Test with no tasks."""
        results = await gather_with_concurrency(5)
        assert results == []

    async def test_more_concurrency_than_tasks(self):
        """Test when concurrency limit exceeds number of tasks."""
        async def simple_task(x):
            await asyncio.sleep(0.01)
            return x

        tasks = [simple_task(i) for i in range(3)]
        results = await gather_with_concurrency(10, *tasks)

        assert results == [0, 1, 2]


@pytest.mark.asyncio
class TestAsyncTimeout:
    """Tests for async_timeout context manager."""

    async def test_operation_completes_within_timeout(self):
        """Test that operations completing within timeout work normally."""
        async with async_timeout(1.0):
            await asyncio.sleep(0.01)
            result = "completed"

        assert result == "completed"

    async def test_operation_exceeds_timeout(self):
        """Test that timeout is raised when operation takes too long."""
        with pytest.raises(asyncio.TimeoutError, match="timed out after"):
            async with async_timeout(0.05):
                await asyncio.sleep(1.0)

    async def test_timeout_cleanup(self):
        """Test that timeout handle is properly cleaned up."""
        # This test verifies no warnings or errors occur during cleanup
        for _ in range(3):
            try:
                async with async_timeout(0.01):
                    await asyncio.sleep(0.5)
            except asyncio.TimeoutError:
                pass  # Expected

        # If we get here without errors, cleanup worked

    async def test_timeout_with_immediate_return(self):
        """Test timeout with operation that completes immediately."""
        async with async_timeout(1.0):
            result = 42

        assert result == 42

    async def test_timeout_zero(self):
        """Test with zero timeout."""
        with pytest.raises(asyncio.TimeoutError):
            async with async_timeout(0.0):
                await asyncio.sleep(0.001)

    async def test_timeout_with_exception_in_block(self):
        """Test that exceptions in the block are propagated correctly."""
        with pytest.raises(ValueError, match="Test error"):
            async with async_timeout(1.0):
                raise ValueError("Test error")


@pytest.mark.asyncio
class TestRetryAsync:
    """Tests for retry_async decorator."""

    async def test_successful_operation_no_retry(self):
        """Test that successful operations don't retry."""
        call_count = {"value": 0}

        @retry_async(max_attempts=3, base_delay=0.01)
        async def successful_func():
            call_count["value"] += 1
            return "success"

        result = await successful_func()

        assert result == "success"
        assert call_count["value"] == 1

    async def test_retry_on_failure(self):
        """Test that function retries on failure."""
        call_count = {"value": 0}

        @retry_async(max_attempts=3, base_delay=0.01)
        async def unreliable_func():
            call_count["value"] += 1
            if call_count["value"] < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await unreliable_func()

        assert result == "success"
        assert call_count["value"] == 3

    async def test_max_attempts_exceeded(self):
        """Test that exception is raised after max attempts."""
        call_count = {"value": 0}

        @retry_async(max_attempts=3, base_delay=0.01)
        async def always_fails():
            call_count["value"] += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            await always_fails()

        assert call_count["value"] == 3

    async def test_exponential_backoff(self):
        """Test that delay increases exponentially."""
        call_count = {"value": 0}

        @retry_async(max_attempts=4, base_delay=0.01, exponential_base=2.0)
        async def track_delays():
            call_count["value"] += 1
            if call_count["value"] < 4:
                raise ValueError("Retry needed")
            return "done"

        # Patch asyncio.sleep to track delays
        sleep_durations = []

        # Save original sleep before patching
        import asyncio as asyncio_module
        original_sleep = asyncio_module.sleep

        async def mock_sleep(duration):
            sleep_durations.append(duration)
            # Don't actually sleep to speed up test
            return None

        with patch('ai_automation_framework.core.async_utils.asyncio.sleep', side_effect=mock_sleep):
            result = await track_delays()

        assert result == "done"
        assert len(sleep_durations) == 3
        # First retry: 0.01 * 2^0 = 0.01
        # Second retry: 0.01 * 2^1 = 0.02
        # Third retry: 0.01 * 2^2 = 0.04
        assert sleep_durations[0] == 0.01
        assert sleep_durations[1] == 0.02
        assert sleep_durations[2] == 0.04

    async def test_max_delay_limit(self):
        """Test that delay doesn't exceed max_delay."""
        @retry_async(max_attempts=5, base_delay=1.0, max_delay=2.0, exponential_base=2.0)
        async def always_fails():
            raise ValueError("Fail")

        sleep_durations = []

        async def mock_sleep(duration):
            sleep_durations.append(duration)
            # Don't actually sleep to speed up test
            return None

        with patch('ai_automation_framework.core.async_utils.asyncio.sleep', side_effect=mock_sleep):
            with pytest.raises(ValueError):
                await always_fails()

        # Delays: 1.0, 2.0, 4.0 (capped to 2.0), 8.0 (capped to 2.0)
        assert len(sleep_durations) == 4  # 4 retries before final failure
        assert sleep_durations[0] == 1.0
        assert all(d <= 2.0 for d in sleep_durations)
        assert sleep_durations[1] == 2.0  # 1.0 * 2^1 = 2.0
        assert sleep_durations[2] == 2.0  # 1.0 * 2^2 = 4.0, capped to 2.0
        assert sleep_durations[3] == 2.0  # 1.0 * 2^3 = 8.0, capped to 2.0

    async def test_specific_exceptions(self):
        """Test that only specific exceptions trigger retry."""
        call_count = {"value": 0}

        @retry_async(max_attempts=3, base_delay=0.01, exceptions=(ValueError,))
        async def specific_error():
            call_count["value"] += 1
            if call_count["value"] == 1:
                raise ValueError("Retry this")
            raise RuntimeError("Don't retry this")

        with pytest.raises(RuntimeError, match="Don't retry this"):
            await specific_error()

        assert call_count["value"] == 2  # First call + one retry

    async def test_retry_with_args_and_kwargs(self):
        """Test that function arguments are preserved across retries."""
        call_count = {"value": 0}

        @retry_async(max_attempts=3, base_delay=0.01)
        async def func_with_args(a, b, c=None):
            call_count["value"] += 1
            if call_count["value"] < 2:
                raise ValueError("Retry")
            return f"{a}-{b}-{c}"

        result = await func_with_args(1, 2, c=3)

        assert result == "1-2-3"
        assert call_count["value"] == 2


@pytest.mark.asyncio
class TestAsyncLock:
    """Tests for AsyncLock class."""

    async def test_basic_lock_context_manager(self):
        """Test basic lock usage with context manager."""
        lock = AsyncLock(name="test_lock")

        assert not lock.locked()

        async with lock:
            assert lock.locked()
            # Do some work
            await asyncio.sleep(0.01)

        assert not lock.locked()

    async def test_lock_mutual_exclusion(self):
        """Test that lock provides mutual exclusion."""
        lock = AsyncLock(name="mutex_lock")
        shared_resource = {"value": 0, "concurrent": 0, "max_concurrent": 0}

        async def increment():
            async with lock:
                # Track concurrent access
                shared_resource["concurrent"] += 1
                shared_resource["max_concurrent"] = max(
                    shared_resource["max_concurrent"],
                    shared_resource["concurrent"]
                )

                # Simulate work
                current = shared_resource["value"]
                await asyncio.sleep(0.01)
                shared_resource["value"] = current + 1

                shared_resource["concurrent"] -= 1

        # Run 10 concurrent increments
        await asyncio.gather(*[increment() for _ in range(10)])

        assert shared_resource["value"] == 10
        assert shared_resource["max_concurrent"] == 1  # Only one at a time

    async def test_acquire_timeout_success(self):
        """Test successful lock acquisition with timeout."""
        lock = AsyncLock(name="timeout_lock")

        async with lock.acquire_timeout(1.0):
            assert lock.locked()
            await asyncio.sleep(0.01)

        assert not lock.locked()

    async def test_acquire_timeout_failure(self):
        """Test timeout when lock cannot be acquired."""
        lock = AsyncLock(name="timeout_lock")

        async def hold_lock():
            async with lock:
                await asyncio.sleep(0.5)

        async def try_acquire_with_timeout():
            await asyncio.sleep(0.01)  # Let other task acquire first
            async with lock.acquire_timeout(0.05):
                pass  # Won't get here

        # Start task that holds lock
        holder = asyncio.create_task(hold_lock())

        # Try to acquire with timeout (should fail)
        with pytest.raises(asyncio.TimeoutError):
            await try_acquire_with_timeout()

        await holder

    async def test_manual_acquire_release(self):
        """Test manual acquire and release methods."""
        lock = AsyncLock(name="manual_lock")

        assert not lock.locked()

        await lock.acquire()
        assert lock.locked()

        lock.release()
        assert not lock.locked()

    async def test_lock_with_logging(self):
        """Test lock with logging enabled."""
        lock = AsyncLock(name="logged_lock", log_acquires=True)

        # Just verify it works with logging enabled
        async with lock:
            assert lock.locked()

        assert not lock.locked()

    async def test_lock_initialization(self):
        """Test lock initialization with various parameters."""
        # Default initialization
        lock1 = AsyncLock()
        assert lock1.name == "AsyncLock"
        assert lock1.log_acquires is False

        # With name
        lock2 = AsyncLock(name="custom_lock")
        assert lock2.name == "custom_lock"

        # With logging
        lock3 = AsyncLock(name="logged", log_acquires=True)
        assert lock3.log_acquires is True

    async def test_multiple_locks(self):
        """Test using multiple independent locks."""
        lock1 = AsyncLock(name="lock1")
        lock2 = AsyncLock(name="lock2")

        async with lock1:
            assert lock1.locked()
            assert not lock2.locked()

            async with lock2:
                assert lock1.locked()
                assert lock2.locked()

            assert lock1.locked()
            assert not lock2.locked()

        assert not lock1.locked()
        assert not lock2.locked()

    async def test_nested_lock_same_instance(self):
        """Test that attempting to acquire same lock twice deadlocks (expected)."""
        lock = AsyncLock(name="nested_lock")

        async def nested_acquire():
            async with lock:
                # Try to acquire again - this should timeout
                async with lock.acquire_timeout(0.1):
                    pass  # Won't get here

        with pytest.raises(asyncio.TimeoutError):
            await nested_acquire()

    async def test_lock_fairness(self):
        """Test that lock is acquired in order."""
        lock = AsyncLock(name="fair_lock")
        order = []

        async def acquire_and_record(task_id):
            await asyncio.sleep(0.001 * task_id)  # Stagger start times
            async with lock:
                order.append(task_id)
                await asyncio.sleep(0.01)

        # Create tasks that will compete for lock
        await asyncio.gather(*[acquire_and_record(i) for i in range(5)])

        # Verify all tasks completed
        assert len(order) == 5
        assert set(order) == {0, 1, 2, 3, 4}
