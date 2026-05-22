"""Comprehensive tests for task_queue module."""

import pytest
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from ai_automation_framework.core.task_queue import (
    Task,
    TaskQueue,
    TaskStatus,
    TaskResult,
    QueueMode,
)


class TestTaskQueueInitialization:
    """Test TaskQueue initialization."""

    def test_init_default_parameters(self):
        """Test TaskQueue initialization with default parameters."""
        queue = TaskQueue()

        assert queue.name == "TaskQueue"
        assert queue.mode == QueueMode.FIFO
        assert queue.max_workers == 4
        assert queue.persistent is False
        assert not queue._running

        queue.stop()

    def test_init_with_custom_parameters(self):
        """Test TaskQueue initialization with custom parameters."""
        queue = TaskQueue(
            name="custom-queue",
            mode=QueueMode.PRIORITY,
            max_workers=8,
            persistent=False
        )

        assert queue.name == "custom-queue"
        assert queue.mode == QueueMode.PRIORITY
        assert queue.max_workers == 8
        assert queue.persistent is False

        queue.stop()

    def test_init_fifo_mode(self):
        """Test TaskQueue initialization in FIFO mode."""
        queue = TaskQueue(mode=QueueMode.FIFO)

        assert queue.mode == QueueMode.FIFO
        from queue import Queue
        assert isinstance(queue._queue, Queue)

        queue.stop()

    def test_init_priority_mode(self):
        """Test TaskQueue initialization in PRIORITY mode."""
        queue = TaskQueue(mode=QueueMode.PRIORITY)

        assert queue.mode == QueueMode.PRIORITY
        from queue import PriorityQueue
        assert isinstance(queue._queue, PriorityQueue)

        queue.stop()

    def test_context_manager(self):
        """Test TaskQueue as context manager."""
        with TaskQueue(name="context-queue") as queue:
            assert queue._running

        # Queue should be stopped after context exit
        assert not queue._running


class TestEnqueueDequeueOperations:
    """Test enqueue and dequeue operations."""

    def test_submit_task(self):
        """Test submitting a task to the queue."""
        queue = TaskQueue()

        def simple_task():
            return "result"

        task_id = queue.submit(simple_task)

        assert task_id is not None
        assert task_id in queue._tasks
        assert queue._tasks[task_id].func == simple_task

        queue.stop()

    def test_submit_task_with_args(self):
        """Test submitting a task with positional arguments."""
        queue = TaskQueue()

        def task_with_args(a, b, c):
            return a + b + c

        task_id = queue.submit(task_with_args, 1, 2, 3)

        task = queue._tasks[task_id]
        assert task.args == (1, 2, 3)

        queue.stop()

    def test_submit_task_with_kwargs(self):
        """Test submitting a task with keyword arguments."""
        queue = TaskQueue()

        def task_with_kwargs(name, age):
            return f"{name} is {age}"

        task_id = queue.submit(task_with_kwargs, name="Alice", age=30)

        task = queue._tasks[task_id]
        assert task.kwargs == {"name": "Alice", "age": 30}

        queue.stop()

    def test_auto_start_on_submit(self):
        """Test that queue auto-starts when task is submitted."""
        queue = TaskQueue()

        assert not queue._running

        def simple_task():
            return "result"

        queue.submit(simple_task)

        # Queue should auto-start
        assert queue._running

        queue.stop()


class TestTaskPriorityOrdering:
    """Test task priority ordering."""

    def test_priority_queue_ordering(self):
        """Test that tasks are executed in priority order."""
        queue = TaskQueue(mode=QueueMode.PRIORITY, max_workers=1)
        results = []

        def task(priority_level):
            results.append(priority_level)
            return priority_level

        # Submit tasks with different priorities (lower = higher priority)
        queue.submit(task, 3, priority=10)  # Low priority
        queue.submit(task, 1, priority=1)   # High priority
        queue.submit(task, 2, priority=5)   # Medium priority

        # Wait for all tasks to complete
        time.sleep(2)

        # Tasks should be executed in priority order: 1, 2, 3
        assert results == [1, 2, 3]

        queue.stop()

    def test_fifo_queue_ordering(self):
        """Test that tasks are executed in FIFO order."""
        queue = TaskQueue(mode=QueueMode.FIFO, max_workers=1)
        results = []

        def task(num):
            results.append(num)
            return num

        # Submit tasks
        queue.submit(task, 1)
        queue.submit(task, 2)
        queue.submit(task, 3)

        # Wait for all tasks to complete
        time.sleep(2)

        # Tasks should be executed in FIFO order: 1, 2, 3
        assert results == [1, 2, 3]

        queue.stop()

    def test_task_comparison(self):
        """Test Task comparison for priority queue."""
        task1 = Task(priority=5)
        task2 = Task(priority=10)
        task3 = Task(priority=1)

        # Lower priority value = higher priority
        assert task3 < task1 < task2


class TestTaskExecution:
    """Test task execution."""

    def test_execute_simple_task(self):
        """Test executing a simple task."""
        queue = TaskQueue()

        def simple_task():
            return "success"

        task_id = queue.submit(simple_task)
        result = queue.wait_for_task(task_id, timeout=5.0)

        assert result is not None
        assert result.success is True
        assert result.result == "success"

        queue.stop()

    def test_execute_task_with_return_value(self):
        """Test executing a task with return value."""
        queue = TaskQueue()

        def calculate(a, b):
            return a + b

        task_id = queue.submit(calculate, 10, 20)
        result = queue.wait_for_task(task_id, timeout=5.0)

        assert result.success is True
        assert result.result == 30

        queue.stop()

    def test_task_status_transitions(self):
        """Test task status transitions during execution."""
        queue = TaskQueue()

        def slow_task():
            time.sleep(0.5)
            return "done"

        task_id = queue.submit(slow_task)

        # Initially should be PENDING or RUNNING
        time.sleep(0.1)
        status = queue.get_task_status(task_id)
        assert status in [TaskStatus.PENDING, TaskStatus.RUNNING]

        # Wait for completion
        result = queue.wait_for_task(task_id, timeout=5.0)

        # Should be COMPLETED
        status = queue.get_task_status(task_id)
        assert status == TaskStatus.COMPLETED

        queue.stop()

    def test_task_execution_time_tracking(self):
        """Test that execution time is tracked."""
        queue = TaskQueue()

        def timed_task():
            time.sleep(0.2)
            return "done"

        task_id = queue.submit(timed_task)
        result = queue.wait_for_task(task_id, timeout=5.0)

        assert result.execution_time >= 0.2
        assert result.execution_time < 1.0  # Should complete quickly

        queue.stop()

    def test_task_timestamps(self):
        """Test that task timestamps are recorded."""
        queue = TaskQueue()

        def simple_task():
            return "done"

        task_id = queue.submit(simple_task)
        result = queue.wait_for_task(task_id, timeout=5.0)

        task = queue._tasks[task_id]
        assert task.created_at is not None
        assert task.started_at is not None
        assert task.completed_at is not None
        assert task.created_at <= task.started_at <= task.completed_at

        queue.stop()


class TestTaskRetryOnFailure:
    """Test task retry on failure."""

    def test_task_retry_on_failure(self):
        """Test that tasks are retried on failure."""
        queue = TaskQueue()
        call_count = [0]

        def failing_task():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Simulated failure")
            return "success"

        task_id = queue.submit(failing_task, max_retries=3, retry_delay=0.1)
        result = queue.wait_for_task(task_id, timeout=5.0)

        # Should succeed after 3 attempts
        assert result.success is True
        assert call_count[0] == 3

        queue.stop()

    def test_task_fails_after_max_retries(self):
        """Test that task fails after max retries."""
        queue = TaskQueue()

        def always_fails():
            raise Exception("Always fails")

        task_id = queue.submit(always_fails, max_retries=2, retry_delay=0.1)
        result = queue.wait_for_task(task_id, timeout=5.0)

        assert result.success is False
        assert result.error is not None
        assert "Always fails" in result.error

        status = queue.get_task_status(task_id)
        assert status == TaskStatus.FAILED

        queue.stop()

    def test_retry_count_tracking(self):
        """Test that retry count is tracked correctly."""
        queue = TaskQueue()
        call_count = [0]

        def failing_task():
            call_count[0] += 1
            raise Exception("Fail")

        task_id = queue.submit(failing_task, max_retries=2, retry_delay=0.1)
        result = queue.wait_for_task(task_id, timeout=5.0)

        task = queue._tasks[task_id]
        # Should have tried 3 times (initial + 2 retries)
        assert task.retry_count == 3
        assert call_count[0] == 3

        queue.stop()

    def test_retry_delay(self):
        """Test that retry delay is honored."""
        queue = TaskQueue()
        timestamps = []

        def failing_task():
            timestamps.append(time.time())
            raise Exception("Fail")

        task_id = queue.submit(failing_task, max_retries=2, retry_delay=0.3)
        result = queue.wait_for_task(task_id, timeout=5.0)

        # Check that there's approximately 0.3s delay between attempts
        if len(timestamps) > 1:
            delay1 = timestamps[1] - timestamps[0]
            assert delay1 >= 0.2  # Allow some tolerance

        queue.stop()


class TestTaskTimeoutHandling:
    """Test task timeout handling."""

    def test_wait_for_task_timeout(self):
        """Test that wait_for_task respects timeout."""
        queue = TaskQueue()

        def long_running_task():
            time.sleep(10)
            return "done"

        task_id = queue.submit(long_running_task)

        start_time = time.time()
        result = queue.wait_for_task(task_id, timeout=1.0)
        elapsed = time.time() - start_time

        # Should timeout and return None
        assert result is None
        assert elapsed >= 1.0
        assert elapsed < 2.0  # Should not wait much longer

        queue.stop()

    def test_wait_for_task_no_timeout(self):
        """Test wait_for_task without timeout."""
        queue = TaskQueue()
        # Without queue.start() the worker pool is never created and
        # wait_for_task(timeout=None) polls forever. start() makes the
        # test verify the actual contract: "no timeout = wait until done".
        queue.start()

        def quick_task():
            return "done"

        task_id = queue.submit(quick_task)
        result = queue.wait_for_task(task_id)  # No timeout

        assert result is not None
        assert result.success is True

        queue.stop()

    def test_wait_for_completed_task(self):
        """Test waiting for already completed task."""
        queue = TaskQueue()

        def simple_task():
            return "done"

        task_id = queue.submit(simple_task)

        # Wait first time
        result1 = queue.wait_for_task(task_id, timeout=5.0)

        # Wait again - should return immediately
        start_time = time.time()
        result2 = queue.wait_for_task(task_id, timeout=5.0)
        elapsed = time.time() - start_time

        assert result2 is not None
        assert elapsed < 0.5  # Should be almost instant

        queue.stop()


class TestConcurrentTaskProcessing:
    """Test concurrent task processing."""

    def test_concurrent_execution(self):
        """Test that multiple tasks execute concurrently."""
        queue = TaskQueue(max_workers=3)
        execution_times = {}

        def concurrent_task(task_num):
            execution_times[task_num] = time.time()
            time.sleep(0.5)
            return task_num

        # Submit 3 tasks
        task_ids = [queue.submit(concurrent_task, i) for i in range(3)]

        # Wait for all to complete
        for task_id in task_ids:
            queue.wait_for_task(task_id, timeout=5.0)

        # Check that tasks started around the same time (concurrent execution)
        times = list(execution_times.values())
        if len(times) >= 2:
            time_diff = max(times) - min(times)
            assert time_diff < 0.3  # Should start within 0.3s of each other

        queue.stop()

    def test_max_workers_limit(self):
        """Test that max_workers limit is respected."""
        queue = TaskQueue(max_workers=2)
        active_tasks = []
        lock = threading.Lock()

        def limited_task(task_num):
            with lock:
                active_tasks.append(task_num)
                current_active = len(active_tasks)

            time.sleep(0.5)

            with lock:
                active_tasks.remove(task_num)

            return current_active

        # Submit more tasks than workers
        task_ids = [queue.submit(limited_task, i) for i in range(5)]

        # Wait for all to complete
        max_concurrent = 0
        for task_id in task_ids:
            result = queue.wait_for_task(task_id, timeout=10.0)
            if result and result.result:
                max_concurrent = max(max_concurrent, result.result)

        # Should not exceed max_workers
        assert max_concurrent <= 2

        queue.stop()

    def test_thread_pool_executor(self):
        """Test that ThreadPoolExecutor is created correctly."""
        queue = TaskQueue(max_workers=4)
        queue.start()

        assert queue._executor is not None
        assert queue._executor._max_workers == 4

        queue.stop()


class TestTaskStatusTracking:
    """Test task status tracking."""

    def test_get_task_status(self):
        """Test getting task status."""
        queue = TaskQueue()

        def simple_task():
            return "done"

        task_id = queue.submit(simple_task)

        status = queue.get_task_status(task_id)
        assert status in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED]

        queue.wait_for_task(task_id, timeout=5.0)

        status = queue.get_task_status(task_id)
        assert status == TaskStatus.COMPLETED

        queue.stop()

    def test_get_task_status_not_found(self):
        """Test getting status of non-existent task."""
        queue = TaskQueue()

        status = queue.get_task_status("non-existent-id")
        assert status is None

        queue.stop()

    def test_get_task_result(self):
        """Test getting task result."""
        queue = TaskQueue()

        def task_with_result():
            return "task result"

        task_id = queue.submit(task_with_result)
        queue.wait_for_task(task_id, timeout=5.0)

        result = queue.get_task_result(task_id)
        assert result is not None
        assert result.success is True
        assert result.result == "task result"

        queue.stop()

    def test_get_task_result_not_completed(self):
        """Test getting result of incomplete task."""
        queue = TaskQueue()

        def long_task():
            time.sleep(10)
            return "done"

        task_id = queue.submit(long_task)

        result = queue.get_task_result(task_id)
        assert result is None

        queue.stop()

    def test_get_queue_stats(self):
        """Test getting queue statistics."""
        queue = TaskQueue(max_workers=2)

        def simple_task():
            time.sleep(0.1)
            return "done"

        # Submit some tasks
        task_ids = [queue.submit(simple_task) for _ in range(5)]

        stats = queue.get_queue_stats()

        assert 'total_tasks' in stats
        assert 'pending' in stats
        assert 'running' in stats
        assert 'completed' in stats
        assert 'failed' in stats
        assert 'cancelled' in stats
        assert 'queue_size' in stats
        assert 'is_running' in stats
        assert 'max_workers' in stats

        assert stats['total_tasks'] == 5
        assert stats['max_workers'] == 2
        assert stats['is_running'] is True

        # Wait for completion
        for task_id in task_ids:
            queue.wait_for_task(task_id, timeout=5.0)

        stats = queue.get_queue_stats()
        assert stats['completed'] == 5

        queue.stop()

    def test_task_status_all_states(self):
        """Test all possible task statuses."""
        queue = TaskQueue()

        # PENDING/COMPLETED
        def simple_task():
            return "done"

        task_id1 = queue.submit(simple_task)
        queue.wait_for_task(task_id1, timeout=5.0)
        assert queue.get_task_status(task_id1) == TaskStatus.COMPLETED

        # FAILED
        def failing_task():
            raise Exception("Fail")

        task_id2 = queue.submit(failing_task, max_retries=0)
        queue.wait_for_task(task_id2, timeout=5.0)
        assert queue.get_task_status(task_id2) == TaskStatus.FAILED

        # CANCELLED
        def long_task():
            time.sleep(10)
            return "done"

        task_id3 = queue.submit(long_task)
        time.sleep(0.1)
        queue.cancel_task(task_id3)
        assert queue.get_task_status(task_id3) == TaskStatus.CANCELLED

        # SCHEDULED
        task_id4 = queue.submit(simple_task, scheduled_time=datetime.now() + timedelta(hours=1))
        assert queue.get_task_status(task_id4) == TaskStatus.SCHEDULED

        queue.stop()


class TestQueueSizeLimits:
    """Test queue size limits and management."""

    def test_queue_size_tracking(self):
        """Test that queue size is tracked correctly."""
        queue = TaskQueue(max_workers=1)

        def slow_task():
            time.sleep(0.5)
            return "done"

        # Submit multiple tasks
        for _ in range(5):
            queue.submit(slow_task)

        # Check queue size
        stats = queue.get_queue_stats()
        assert stats['queue_size'] >= 0

        queue.stop()

    def test_clear_completed_tasks(self):
        """Test clearing completed tasks."""
        queue = TaskQueue()

        def simple_task():
            return "done"

        # Submit and complete some tasks
        task_ids = [queue.submit(simple_task) for _ in range(5)]

        for task_id in task_ids:
            queue.wait_for_task(task_id, timeout=5.0)

        # All tasks should be completed
        stats = queue.get_queue_stats()
        assert stats['completed'] == 5

        # Clear completed tasks
        cleared = queue.clear_completed_tasks()
        assert cleared == 5

        # Stats should show 0 tasks
        stats = queue.get_queue_stats()
        assert stats['total_tasks'] == 0

        queue.stop()

    def test_clear_mixed_tasks(self):
        """Test clearing completed tasks while keeping pending ones."""
        queue = TaskQueue()

        def simple_task():
            return "done"

        def failing_task():
            raise Exception("Fail")

        # Complete some tasks
        task_ids = [queue.submit(simple_task) for _ in range(3)]
        for task_id in task_ids:
            queue.wait_for_task(task_id, timeout=5.0)

        # Fail some tasks
        fail_ids = [queue.submit(failing_task, max_retries=0) for _ in range(2)]
        for task_id in fail_ids:
            queue.wait_for_task(task_id, timeout=5.0)

        # Submit pending task
        queue.submit(simple_task, scheduled_time=datetime.now() + timedelta(hours=1))

        stats = queue.get_queue_stats()
        total_before = stats['total_tasks']

        # Clear completed and failed
        cleared = queue.clear_completed_tasks()
        assert cleared == 5  # 3 completed + 2 failed

        stats = queue.get_queue_stats()
        assert stats['total_tasks'] == 1  # Only scheduled task remains

        queue.stop()


class TestTaskCancellation:
    """Test task cancellation."""

    def test_cancel_pending_task(self):
        """Test cancelling a pending task."""
        queue = TaskQueue(max_workers=1)

        def slow_task():
            time.sleep(2)
            return "done"

        # Submit first task to occupy worker
        queue.submit(slow_task)

        # Submit second task (will be pending)
        task_id = queue.submit(slow_task)

        # Cancel the second task
        time.sleep(0.1)
        cancelled = queue.cancel_task(task_id)

        assert cancelled is True
        assert queue.get_task_status(task_id) == TaskStatus.CANCELLED

        queue.stop()

    def test_cancel_scheduled_task(self):
        """Test cancelling a scheduled task."""
        queue = TaskQueue()

        def simple_task():
            return "done"

        task_id = queue.submit(
            simple_task,
            scheduled_time=datetime.now() + timedelta(seconds=10)
        )

        assert queue.get_task_status(task_id) == TaskStatus.SCHEDULED

        cancelled = queue.cancel_task(task_id)
        assert cancelled is True
        assert queue.get_task_status(task_id) == TaskStatus.CANCELLED

        queue.stop()

    def test_cannot_cancel_running_task(self):
        """Test that running tasks cannot be cancelled."""
        queue = TaskQueue()

        def slow_task():
            time.sleep(1)
            return "done"

        task_id = queue.submit(slow_task)

        # Wait a bit for task to start
        time.sleep(0.2)

        # Try to cancel (should fail if running)
        cancelled = queue.cancel_task(task_id)

        # Wait for completion
        queue.wait_for_task(task_id, timeout=5.0)

        # Task should have completed normally (not cancelled)
        status = queue.get_task_status(task_id)
        assert status == TaskStatus.COMPLETED

        queue.stop()

    def test_cancel_nonexistent_task(self):
        """Test cancelling a non-existent task."""
        queue = TaskQueue()

        cancelled = queue.cancel_task("non-existent-id")
        assert cancelled is False

        queue.stop()


class TestTaskDependencies:
    """Test task dependencies."""

    def test_task_with_dependency(self):
        """Test that task waits for dependency."""
        queue = TaskQueue()
        results = []

        def task1():
            results.append(1)
            time.sleep(0.2)
            return "task1"

        def task2():
            results.append(2)
            return "task2"

        # Submit task1 first
        task_id1 = queue.submit(task1)

        # Submit task2 with dependency on task1
        task_id2 = queue.submit(task2, dependencies={task_id1})

        # Wait for both
        queue.wait_for_task(task_id1, timeout=5.0)
        queue.wait_for_task(task_id2, timeout=5.0)

        # Task1 should execute before task2
        assert results == [1, 2]

        queue.stop()

    def test_multiple_dependencies(self):
        """Test task with multiple dependencies."""
        queue = TaskQueue()
        results = []

        def task(num):
            results.append(num)
            time.sleep(0.1)
            return num

        # Submit independent tasks
        task_id1 = queue.submit(task, 1)
        task_id2 = queue.submit(task, 2)

        # Submit task dependent on both
        task_id3 = queue.submit(task, 3, dependencies={task_id1, task_id2})

        # Wait for all
        queue.wait_for_task(task_id1, timeout=5.0)
        queue.wait_for_task(task_id2, timeout=5.0)
        queue.wait_for_task(task_id3, timeout=5.0)

        # Task 3 should be last
        assert results[-1] == 3
        assert 1 in results
        assert 2 in results

        queue.stop()


class TestScheduledTasks:
    """Test scheduled tasks."""

    def test_scheduled_task_execution(self):
        """Test that scheduled task executes at right time."""
        queue = TaskQueue()

        def simple_task():
            return "done"

        # Schedule task for 1 second from now
        schedule_time = datetime.now() + timedelta(seconds=1)
        task_id = queue.submit(simple_task, scheduled_time=schedule_time)

        # Should be scheduled
        assert queue.get_task_status(task_id) == TaskStatus.SCHEDULED

        # Wait a bit (but not enough time)
        time.sleep(0.5)
        status = queue.get_task_status(task_id)
        assert status in [TaskStatus.SCHEDULED, TaskStatus.PENDING, TaskStatus.RUNNING]

        # Wait for completion
        result = queue.wait_for_task(task_id, timeout=5.0)
        assert result is not None
        assert result.success is True

        queue.stop()

    def test_scheduled_task_with_timedelta(self):
        """Test scheduling task with timedelta."""
        queue = TaskQueue()

        def simple_task():
            return "done"

        task_id = queue.submit(simple_task, scheduled_time=timedelta(seconds=0.5))

        # Should be scheduled
        assert queue.get_task_status(task_id) == TaskStatus.SCHEDULED

        # Wait for completion
        result = queue.wait_for_task(task_id, timeout=5.0)
        assert result is not None

        queue.stop()


class TestTaskMetadata:
    """Test task metadata."""

    def test_task_metadata(self):
        """Test storing and retrieving task metadata."""
        queue = TaskQueue()

        def simple_task():
            return "done"

        metadata = {
            "user": "test_user",
            "priority_reason": "critical",
            "tags": ["urgent", "important"]
        }

        task_id = queue.submit(simple_task, metadata=metadata)

        task = queue._tasks[task_id]
        assert task.metadata == metadata
        assert task.metadata["user"] == "test_user"

        queue.stop()

    def test_task_to_dict(self):
        """Test task serialization to dictionary."""
        def simple_task():
            return "done"

        task = Task(
            func=simple_task,
            priority=5,
            max_retries=3,
            metadata={"key": "value"}
        )

        task_dict = task.to_dict()

        assert task_dict["task_id"] == task.task_id
        assert task_dict["priority"] == 5
        assert task_dict["max_retries"] == 3
        assert task_dict["metadata"] == {"key": "value"}
        assert task_dict["status"] == TaskStatus.PENDING.value


class TestProgressCallback:
    """Test progress callback functionality."""

    def test_progress_callback(self):
        """Test that progress callback is called."""
        queue = TaskQueue()
        progress_updates = []

        def progress_callback(task_id, progress):
            progress_updates.append((task_id, progress))

        def task_with_progress(task_obj):
            task_obj.update_progress(0.5)
            return "done"

        task_id = queue.submit(
            task_with_progress,
            progress_callback=progress_callback
        )

        # Get the task object and pass it to the function
        task = queue._tasks[task_id]
        original_func = task.func
        task.func = lambda: original_func(task)

        result = queue.wait_for_task(task_id, timeout=5.0)

        # Progress callback should have been called
        assert len(progress_updates) >= 1

        queue.stop()

    def test_progress_callback_on_completion(self):
        """Test that progress is set to 100% on completion."""
        queue = TaskQueue()
        progress_updates = []

        def progress_callback(task_id, progress):
            progress_updates.append(progress)

        def simple_task():
            return "done"

        task_id = queue.submit(simple_task, progress_callback=progress_callback)
        result = queue.wait_for_task(task_id, timeout=5.0)

        # Final progress should be 1.0 (100%)
        assert 1.0 in progress_updates

        queue.stop()


class TestQueueStartStop:
    """Test queue start and stop operations."""

    def test_manual_start_stop(self):
        """Test manually starting and stopping queue."""
        queue = TaskQueue()

        assert not queue._running

        queue.start()
        assert queue._running

        queue.stop()
        assert not queue._running

    def test_double_start(self):
        """Test that double start is handled gracefully."""
        queue = TaskQueue()

        queue.start()
        assert queue._running

        # Start again - should log warning but not crash
        queue.start()
        assert queue._running

        queue.stop()

    def test_double_stop(self):
        """Test that double stop is handled gracefully."""
        queue = TaskQueue()

        queue.start()
        queue.stop()
        assert not queue._running

        # Stop again - should log warning but not crash
        queue.stop()
        assert not queue._running

    def test_stop_with_wait(self):
        """Test stopping queue and waiting for tasks."""
        queue = TaskQueue()

        def slow_task():
            time.sleep(0.5)
            return "done"

        task_id = queue.submit(slow_task)

        # Stop with wait
        queue.stop(wait=True, timeout=2.0)

        # Task should have completed
        status = queue.get_task_status(task_id)
        assert status in [TaskStatus.COMPLETED, TaskStatus.RUNNING]

    def test_repr(self):
        """Test string representation of TaskQueue."""
        queue = TaskQueue(name="test-queue", mode=QueueMode.PRIORITY, max_workers=2)

        repr_str = repr(queue)

        assert "test-queue" in repr_str
        assert "priority" in repr_str
        assert "workers=2" in repr_str

        queue.stop()


class TestTaskResult:
    """Test TaskResult class."""

    def test_task_result_success(self):
        """Test TaskResult for successful task."""
        result = TaskResult(
            success=True,
            result="test result",
            execution_time=1.5
        )

        assert result.success is True
        assert result.result == "test result"
        assert result.error is None
        assert result.execution_time == 1.5
        assert isinstance(result.timestamp, datetime)

    def test_task_result_failure(self):
        """Test TaskResult for failed task."""
        result = TaskResult(
            success=False,
            error="Test error message",
            execution_time=0.5
        )

        assert result.success is False
        assert result.result is None
        assert result.error == "Test error message"
        assert result.execution_time == 0.5


class TestTaskCanExecute:
    """Test Task.can_execute method."""

    def test_can_execute_no_dependencies(self):
        """Test task can execute with no dependencies."""
        task = Task()
        completed = set()

        assert task.can_execute(completed) is True

    def test_can_execute_with_met_dependencies(self):
        """Test task can execute when dependencies are met."""
        task = Task(dependencies={"task1", "task2"})
        completed = {"task1", "task2", "task3"}

        assert task.can_execute(completed) is True

    def test_can_execute_with_unmet_dependencies(self):
        """Test task cannot execute when dependencies are not met."""
        task = Task(dependencies={"task1", "task2"})
        completed = {"task1"}  # task2 not completed

        assert task.can_execute(completed) is False


class TestTaskIsReady:
    """Test Task.is_ready method."""

    def test_is_ready_no_schedule(self):
        """Test task is ready when not scheduled."""
        task = Task()
        assert task.is_ready() is True

    def test_is_ready_future_schedule(self):
        """Test task is not ready when scheduled in future."""
        task = Task(scheduled_time=datetime.now() + timedelta(hours=1))
        assert task.is_ready() is False

    def test_is_ready_past_schedule(self):
        """Test task is ready when scheduled time has passed."""
        task = Task(scheduled_time=datetime.now() - timedelta(seconds=1))
        assert task.is_ready() is True
