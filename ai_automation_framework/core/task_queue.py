"""Task queue system for background job processing in the AI Automation Framework."""

import json
import threading
import time
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union
from queue import PriorityQueue, Queue, Empty

from ai_automation_framework.core.logger import get_logger


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class QueueMode(Enum):
    """Queue processing mode."""

    FIFO = "fifo"  # First In First Out
    PRIORITY = "priority"  # Priority-based


@dataclass
class TaskResult:
    """Result of a task execution."""

    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Task:
    """
    Represents a task for background processing.

    Attributes:
        task_id: Unique identifier for the task
        func: Callable function to execute
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function
        priority: Task priority (lower number = higher priority)
        status: Current task status
        max_retries: Maximum number of retry attempts
        retry_count: Current retry attempt count
        retry_delay: Delay in seconds between retries
        scheduled_time: Time when task should be executed (for delayed tasks)
        dependencies: Set of task IDs that must complete before this task
        result: Task execution result
        created_at: Task creation timestamp
        started_at: Task start timestamp
        completed_at: Task completion timestamp
        metadata: Additional task metadata
        progress_callback: Optional callback for progress updates
    """

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    func: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    status: TaskStatus = TaskStatus.PENDING
    max_retries: int = 3
    retry_count: int = 0
    retry_delay: float = 1.0
    scheduled_time: Optional[datetime] = None
    dependencies: Set[str] = field(default_factory=set)
    result: Optional[TaskResult] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    progress_callback: Optional[Callable[[str, float], None]] = None

    def __lt__(self, other: 'Task') -> bool:
        """Compare tasks by priority for priority queue."""
        return self.priority < other.priority

    def can_execute(self, completed_tasks: Set[str]) -> bool:
        """
        Check if task can be executed based on dependencies.

        Args:
            completed_tasks: Set of completed task IDs

        Returns:
            True if all dependencies are met
        """
        return self.dependencies.issubset(completed_tasks)

    def is_ready(self) -> bool:
        """
        Check if scheduled task is ready to execute.

        Returns:
            True if task is ready (not scheduled or scheduled time has passed)
        """
        if self.scheduled_time is None:
            return True
        return datetime.now() >= self.scheduled_time

    def update_progress(self, progress: float) -> None:
        """
        Update task progress.

        Args:
            progress: Progress value between 0.0 and 1.0
        """
        if self.progress_callback:
            try:
                self.progress_callback(self.task_id, progress)
            except Exception as e:
                # Don't fail task if callback fails
                logger = get_logger(__name__)
                logger.warning(f"Progress callback failed for task {self.task_id}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert task to dictionary (for serialization).

        Returns:
            Dictionary representation of task (excluding non-serializable fields)
        """
        return {
            'task_id': self.task_id,
            'priority': self.priority,
            'status': self.status.value,
            'max_retries': self.max_retries,
            'retry_count': self.retry_count,
            'retry_delay': self.retry_delay,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'dependencies': list(self.dependencies),
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.metadata,
            'result': {
                'success': self.result.success,
                'error': self.result.error,
                'execution_time': self.result.execution_time,
                'timestamp': self.result.timestamp.isoformat(),
            } if self.result else None,
        }


class TaskQueue:
    """
    Thread-safe task queue for background job processing.

    Supports FIFO and priority queue modes, concurrent execution with worker pool,
    task scheduling, dependencies, progress tracking, and persistence.
    """

    def __init__(
        self,
        name: str = "TaskQueue",
        mode: QueueMode = QueueMode.FIFO,
        max_workers: int = 4,
        persistent: bool = False,
        persistence_file: Optional[str] = None,
    ):
        """
        Initialize the task queue.

        Args:
            name: Queue name for logging
            mode: Queue processing mode (FIFO or PRIORITY)
            max_workers: Maximum number of concurrent workers
            persistent: Enable persistent queue backup
            persistence_file: Path to persistence file (auto-generated if not provided)
        """
        self.name = name
        self.mode = mode
        self.max_workers = max_workers
        self.persistent = persistent
        self.logger = get_logger(f"{__name__}.{name}")

        # Queue structures
        if mode == QueueMode.PRIORITY:
            self._queue: Union[Queue, PriorityQueue] = PriorityQueue()
        else:
            self._queue = Queue()

        # Task tracking
        self._tasks: Dict[str, Task] = {}
        self._completed_tasks: Set[str] = set()
        self._scheduled_tasks: List[Task] = []
        self._dependency_graph: Dict[str, Set[str]] = {}  # task_id -> dependents

        # Threading
        self._lock = threading.RLock()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._futures: Dict[str, Future] = {}
        self._running = False
        self._shutdown_event = threading.Event()
        self._scheduler_thread: Optional[threading.Thread] = None

        # Persistence
        self._persistence_file = Path(persistence_file) if persistence_file else Path(f".task_queue_{name}.json")
        if self.persistent:
            self._load_state()

        self.logger.info(f"TaskQueue '{name}' initialized with mode={mode.value}, max_workers={max_workers}")

    def start(self) -> None:
        """Start the task queue and worker pool."""
        with self._lock:
            if self._running:
                self.logger.warning("TaskQueue is already running")
                return

            self._running = True
            self._shutdown_event.clear()
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix=f"{self.name}-worker")

            # Start scheduler thread for delayed tasks
            self._scheduler_thread = threading.Thread(
                target=self._scheduler_loop,
                name=f"{self.name}-scheduler",
                daemon=True
            )
            self._scheduler_thread.start()

            self.logger.info(f"TaskQueue '{self.name}' started with {self.max_workers} workers")

    def stop(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """
        Stop the task queue gracefully.

        Args:
            wait: Wait for running tasks to complete
            timeout: Maximum time to wait in seconds
        """
        with self._lock:
            if not self._running:
                self.logger.warning("TaskQueue is not running")
                return

            self.logger.info(f"Stopping TaskQueue '{self.name}'...")
            self._running = False
            self._shutdown_event.set()

        # Stop scheduler thread
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=5.0)

        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=wait, cancel_futures=not wait)
            self._executor = None

        # Save state if persistent
        if self.persistent:
            self._save_state()

        self.logger.info(f"TaskQueue '{self.name}' stopped")

    def submit(
        self,
        func: Callable,
        *args,
        priority: int = 0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        scheduled_time: Optional[Union[datetime, timedelta]] = None,
        dependencies: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        **kwargs
    ) -> str:
        """
        Submit a task to the queue.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            priority: Task priority (lower = higher priority)
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            scheduled_time: When to execute the task (datetime or timedelta from now)
            dependencies: Set of task IDs that must complete first
            metadata: Additional task metadata
            progress_callback: Callback for progress updates (task_id, progress)
            **kwargs: Keyword arguments for the function

        Returns:
            Task ID
        """
        # Handle scheduled_time as timedelta
        if isinstance(scheduled_time, timedelta):
            scheduled_time = datetime.now() + scheduled_time

        task = Task(
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            scheduled_time=scheduled_time,
            dependencies=dependencies or set(),
            metadata=metadata or {},
            progress_callback=progress_callback,
        )

        if scheduled_time:
            task.status = TaskStatus.SCHEDULED

        with self._lock:
            self._tasks[task.task_id] = task

            # Track dependencies
            for dep_id in task.dependencies:
                if dep_id not in self._dependency_graph:
                    self._dependency_graph[dep_id] = set()
                self._dependency_graph[dep_id].add(task.task_id)

            # Add to appropriate queue
            if task.scheduled_time:
                self._scheduled_tasks.append(task)
                self._scheduled_tasks.sort(key=lambda t: t.scheduled_time or datetime.max)
            elif task.can_execute(self._completed_tasks):
                self._enqueue_task(task)

            self.logger.debug(f"Task {task.task_id} submitted with priority={priority}, scheduled={scheduled_time}")

        # Auto-start if not running
        if not self._running:
            self.start()

        return task.task_id

    def _enqueue_task(self, task: Task) -> None:
        """
        Add task to the execution queue.

        Args:
            task: Task to enqueue
        """
        if self.mode == QueueMode.PRIORITY:
            self._queue.put(task)
        else:
            self._queue.put(task)

        # Submit to executor
        if self._executor:
            future = self._executor.submit(self._execute_task, task)
            self._futures[task.task_id] = future

    def _scheduler_loop(self) -> None:
        """Background thread to check and enqueue scheduled tasks."""
        while self._running and not self._shutdown_event.is_set():
            try:
                with self._lock:
                    now = datetime.now()
                    ready_tasks = []

                    # Find ready tasks
                    for task in self._scheduled_tasks[:]:
                        if task.is_ready() and task.can_execute(self._completed_tasks):
                            ready_tasks.append(task)
                            self._scheduled_tasks.remove(task)

                    # Enqueue ready tasks
                    for task in ready_tasks:
                        task.status = TaskStatus.PENDING
                        self._enqueue_task(task)
                        self.logger.debug(f"Scheduled task {task.task_id} is now ready for execution")

                # Sleep briefly to avoid busy waiting
                time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(1.0)

    def _execute_task(self, task: Task) -> None:
        """
        Execute a task with retry logic.

        Args:
            task: Task to execute
        """
        while task.retry_count <= task.max_retries:
            try:
                # Update status
                with self._lock:
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.now()

                self.logger.info(f"Executing task {task.task_id} (attempt {task.retry_count + 1}/{task.max_retries + 1})")

                # Execute function
                start_time = time.time()
                result = task.func(*task.args, **task.kwargs)
                execution_time = time.time() - start_time

                # Mark as completed
                with self._lock:
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()
                    task.result = TaskResult(
                        success=True,
                        result=result,
                        execution_time=execution_time,
                    )
                    self._completed_tasks.add(task.task_id)

                    # Trigger dependent tasks
                    self._trigger_dependents(task.task_id)

                self.logger.info(f"Task {task.task_id} completed successfully in {execution_time:.2f}s")

                # Update progress to 100%
                task.update_progress(1.0)

                # Save state if persistent
                if self.persistent:
                    self._save_state()

                return

            except Exception as e:
                self.logger.error(f"Task {task.task_id} failed (attempt {task.retry_count + 1}): {e}")

                task.retry_count += 1

                if task.retry_count > task.max_retries:
                    # Max retries exceeded
                    with self._lock:
                        task.status = TaskStatus.FAILED
                        task.completed_at = datetime.now()
                        task.result = TaskResult(
                            success=False,
                            error=str(e),
                            execution_time=time.time() - (task.started_at.timestamp() if task.started_at else time.time()),
                        )

                    self.logger.error(f"Task {task.task_id} failed after {task.max_retries + 1} attempts")

                    # Save state if persistent
                    if self.persistent:
                        self._save_state()

                    return
                else:
                    # Retry with delay
                    with self._lock:
                        task.status = TaskStatus.RETRYING

                    self.logger.info(f"Retrying task {task.task_id} in {task.retry_delay}s...")
                    time.sleep(task.retry_delay)

    def _trigger_dependents(self, task_id: str) -> None:
        """
        Trigger tasks that depend on the completed task.

        Args:
            task_id: ID of completed task
        """
        if task_id not in self._dependency_graph:
            return

        dependent_ids = self._dependency_graph[task_id]

        for dep_id in dependent_ids:
            task = self._tasks.get(dep_id)
            if task and task.status == TaskStatus.PENDING and task.can_execute(self._completed_tasks):
                if task.is_ready():
                    self._enqueue_task(task)
                    self.logger.debug(f"Triggered dependent task {dep_id}")

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or scheduled task.

        Args:
            task_id: Task ID to cancel

        Returns:
            True if task was cancelled, False otherwise
        """
        with self._lock:
            task = self._tasks.get(task_id)

            if not task:
                self.logger.warning(f"Task {task_id} not found")
                return False

            if task.status in (TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.FAILED):
                self.logger.warning(f"Cannot cancel task {task_id} with status {task.status.value}")
                return False

            # Cancel future if exists
            if task_id in self._futures:
                self._futures[task_id].cancel()
                del self._futures[task_id]

            # Remove from scheduled tasks
            if task in self._scheduled_tasks:
                self._scheduled_tasks.remove(task)

            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()

            self.logger.info(f"Task {task_id} cancelled")

            if self.persistent:
                self._save_state()

            return True

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get the status of a task.

        Args:
            task_id: Task ID

        Returns:
            Task status or None if not found
        """
        with self._lock:
            task = self._tasks.get(task_id)
            return task.status if task else None

    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """
        Get the result of a completed task.

        Args:
            task_id: Task ID

        Returns:
            Task result or None if not completed
        """
        with self._lock:
            task = self._tasks.get(task_id)
            return task.result if task else None

    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Optional[TaskResult]:
        """
        Wait for a task to complete and return its result.

        Args:
            task_id: Task ID
            timeout: Maximum time to wait in seconds

        Returns:
            Task result or None if timeout
        """
        start_time = time.time()

        while True:
            with self._lock:
                task = self._tasks.get(task_id)

                if not task:
                    self.logger.warning(f"Task {task_id} not found")
                    return None

                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                    return task.result

            # Check timeout
            if timeout and (time.time() - start_time) >= timeout:
                self.logger.warning(f"Timeout waiting for task {task_id}")
                return None

            time.sleep(0.1)

    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Dictionary with queue statistics
        """
        with self._lock:
            stats = {
                'total_tasks': len(self._tasks),
                'pending': sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING),
                'scheduled': sum(1 for t in self._tasks.values() if t.status == TaskStatus.SCHEDULED),
                'running': sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING),
                'completed': sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED),
                'failed': sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED),
                'cancelled': sum(1 for t in self._tasks.values() if t.status == TaskStatus.CANCELLED),
                'queue_size': self._queue.qsize(),
                'is_running': self._running,
                'max_workers': self.max_workers,
            }
            return stats

    def clear_completed_tasks(self) -> int:
        """
        Clear completed, failed, and cancelled tasks from memory.

        Returns:
            Number of tasks cleared
        """
        with self._lock:
            tasks_to_remove = [
                task_id for task_id, task in self._tasks.items()
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
            ]

            for task_id in tasks_to_remove:
                del self._tasks[task_id]
                if task_id in self._futures:
                    del self._futures[task_id]
                if task_id in self._dependency_graph:
                    del self._dependency_graph[task_id]

            self.logger.info(f"Cleared {len(tasks_to_remove)} completed tasks")

            if self.persistent:
                self._save_state()

            return len(tasks_to_remove)

    def _save_state(self) -> None:
        """Save queue state to file."""
        try:
            with self._lock:
                state = {
                    'name': self.name,
                    'mode': self.mode.value,
                    'tasks': {
                        task_id: task.to_dict()
                        for task_id, task in self._tasks.items()
                    },
                    'completed_tasks': list(self._completed_tasks),
                    'timestamp': datetime.now().isoformat(),
                }

            self._persistence_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self._persistence_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)

            self.logger.debug(f"State saved to {self._persistence_file}")

        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def _load_state(self) -> None:
        """Load queue state from file."""
        try:
            if not self._persistence_file.exists():
                self.logger.debug("No persistence file found")
                return

            with open(self._persistence_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # Note: We can only restore task metadata, not the actual functions
            # Functions need to be re-submitted by the application
            self._completed_tasks = set(state.get('completed_tasks', []))

            self.logger.info(f"State loaded from {self._persistence_file} (task functions need re-submission)")

        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop(wait=True)

    def __repr__(self) -> str:
        """String representation."""
        stats = self.get_queue_stats()
        return (
            f"TaskQueue(name='{self.name}', mode={self.mode.value}, "
            f"workers={self.max_workers}, running={self._running}, "
            f"pending={stats['pending']}, completed={stats['completed']})"
        )


# Example usage and testing
if __name__ == "__main__":
    import random

    # Example task function
    def example_task(task_num: int, sleep_time: float = 1.0) -> str:
        """Example task that sleeps and returns a message."""
        print(f"Task {task_num} starting (will sleep {sleep_time}s)")
        time.sleep(sleep_time)

        # Simulate random failures for retry testing
        if random.random() < 0.2:  # 20% failure rate
            raise Exception(f"Random failure in task {task_num}")

        return f"Task {task_num} completed!"

    # Create and start queue
    print("Creating task queue...")
    queue = TaskQueue(
        name="example-queue",
        mode=QueueMode.PRIORITY,
        max_workers=3,
        persistent=True,
    )

    # Submit tasks with different priorities
    print("\nSubmitting tasks...")
    task_ids = []

    # High priority task
    task_ids.append(queue.submit(example_task, 1, 0.5, priority=1))

    # Low priority task
    task_ids.append(queue.submit(example_task, 2, 0.5, priority=10))

    # Scheduled task (delayed 2 seconds)
    task_ids.append(queue.submit(
        example_task, 3, 0.5,
        scheduled_time=timedelta(seconds=2),
        priority=5
    ))

    # Task with dependency
    dep_task = queue.submit(example_task, 4, 0.3, priority=5)
    task_ids.append(queue.submit(
        example_task, 5, 0.3,
        dependencies={dep_task},
        priority=5
    ))

    # Print stats
    print("\nQueue stats:")
    stats = queue.get_queue_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Wait for all tasks
    print("\nWaiting for tasks to complete...")
    for task_id in task_ids:
        result = queue.wait_for_task(task_id, timeout=10.0)
        if result:
            print(f"Task {task_id[:8]}... {result.success}: {result.result if result.success else result.error}")

    # Final stats
    print("\nFinal queue stats:")
    stats = queue.get_queue_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Stop queue
    print("\nStopping queue...")
    queue.stop()
    print("Done!")
