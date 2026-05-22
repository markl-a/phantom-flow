"""
Event Bus System for AI Automation Framework

This module provides a comprehensive event bus implementation for decoupled
component communication with support for both synchronous and asynchronous
event handlers, priority-based execution, event filtering, and event history.

Features:
- Event base class with metadata (timestamp, source, id)
- EventBus class for pub/sub pattern
- Sync and async event handlers
- Event filtering by type or attributes
- Priority-based handler execution
- Event history/replay capability
- Wildcard subscriptions
- Thread-safe implementation
- Weak references to prevent memory leaks
"""

import asyncio
import logging
import re
import threading
import weakref
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import (
    Any,
    Callable,
    Coroutine,
    Deque,
    Dict,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)
from uuid import uuid4


logger = logging.getLogger(__name__)


class EventPriority(IntEnum):
    """Priority levels for event handlers (higher number = higher priority)."""

    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100


@dataclass
class Event:
    """
    Base event class with metadata.

    All events in the system inherit from this class and include
    automatic timestamp, unique ID, and source tracking.

    Attributes:
        event_type: Type identifier for the event
        source: Source component/module that generated the event
        timestamp: When the event was created
        event_id: Unique identifier for this event instance
        data: Additional event-specific data
        metadata: Extra metadata for the event
    """

    event_type: str
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_id: str = field(default_factory=lambda: str(uuid4()))

    def matches_filter(self, filter_dict: Dict[str, Any]) -> bool:
        """
        Check if event matches filter criteria.

        Args:
            filter_dict: Dictionary of attribute names and values to match

        Returns:
            True if all filter criteria match, False otherwise
        """
        for key, value in filter_dict.items():
            if key == "event_type":
                if not self._match_pattern(self.event_type, value):
                    return False
            elif key == "source":
                if not self._match_pattern(self.source, value):
                    return False
            elif hasattr(self, key):
                if getattr(self, key) != value:
                    return False
            elif key in self.data:
                if self.data[key] != value:
                    return False
            elif key in self.metadata:
                if self.metadata[key] != value:
                    return False
            else:
                return False
        return True

    @staticmethod
    def _match_pattern(value: str, pattern: str) -> bool:
        """
        Match value against pattern with wildcard support.

        Supports '*' wildcard matching.

        Args:
            value: Value to match
            pattern: Pattern with optional wildcards

        Returns:
            True if value matches pattern
        """
        if pattern == "*":
            return True
        if "*" in pattern:
            # Convert wildcard pattern to regex
            regex_pattern = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
            return bool(re.match(regex_pattern, value))
        return value == pattern

    def __str__(self) -> str:
        """String representation of the event."""
        return (
            f"{self.__class__.__name__}("
            f"type={self.event_type}, "
            f"source={self.source}, "
            f"id={self.event_id[:8]}..., "
            f"time={self.timestamp.isoformat()})"
        )


EventType = TypeVar("EventType", bound=Event)


@dataclass
class EventHandler:
    """
    Container for event handler with metadata.

    Attributes:
        callback: The handler function (sync or async)
        priority: Execution priority
        event_type_pattern: Optional event type pattern for wildcard matching
        filter_dict: Optional filter criteria
        handler_id: Unique identifier for this handler
        is_async: Whether the handler is async
    """

    callback: Union[Callable[[Event], Any], Callable[[Event], Coroutine[Any, Any, Any]]]
    priority: int
    event_type_pattern: Optional[str] = None
    filter_dict: Optional[Dict[str, Any]] = None
    handler_id: str = field(default_factory=lambda: str(uuid4()))
    is_async: bool = False

    def matches_event(self, event: Event) -> bool:
        """
        Check if this handler should process the event.

        Args:
            event: Event to check

        Returns:
            True if handler should process event
        """
        # Check event type pattern if specified
        if self.event_type_pattern is not None:
            if not Event._match_pattern(event.event_type, self.event_type_pattern):
                return False

        # Check additional filters
        if self.filter_dict is None:
            return True
        return event.matches_filter(self.filter_dict)

    def __hash__(self) -> int:
        """Hash based on handler ID."""
        return hash(self.handler_id)

    def __eq__(self, other: object) -> bool:
        """Equality based on handler ID."""
        if not isinstance(other, EventHandler):
            return NotImplemented
        return self.handler_id == other.handler_id


class EventBus:
    """
    Thread-safe event bus for pub/sub pattern.

    Supports both synchronous and asynchronous event handlers,
    priority-based execution, event filtering, wildcard subscriptions,
    and event history with replay capability.

    The event bus uses weak references for handlers to prevent memory
    leaks when handler objects are deleted.
    """

    def __init__(
        self,
        max_history: int = 1000,
        enable_history: bool = True,
        enable_async: bool = True,
    ):
        """
        Initialize the event bus.

        Args:
            max_history: Maximum number of events to store in history
            enable_history: Whether to store event history
            enable_async: Whether to support async handlers
        """
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._wildcard_handlers: List[EventHandler] = []
        self._lock = threading.RLock()
        self._event_history: Deque[Event] = deque(maxlen=max_history)
        self._enable_history = enable_history
        self._enable_async = enable_async
        self._weak_refs: Set[weakref.ref] = set()
        self._stats: Dict[str, int] = defaultdict(int)

        logger.info(
            f"EventBus initialized (history={enable_history}, "
            f"max_history={max_history}, async={enable_async})"
        )

    def subscribe(
        self,
        event_type: str,
        handler: Union[
            Callable[[Event], Any],
            Callable[[Event], Coroutine[Any, Any, Any]]
        ],
        priority: int = EventPriority.NORMAL,
        filter_dict: Optional[Dict[str, Any]] = None,
        weak_ref: bool = True,
    ) -> str:
        """
        Subscribe a handler to an event type.

        Supports wildcard subscriptions using '*' in event_type.

        Args:
            event_type: Event type to subscribe to (supports wildcards)
            handler: Callback function (sync or async)
            priority: Handler execution priority
            filter_dict: Optional filter criteria for events
            weak_ref: Use weak reference to handler

        Returns:
            Handler ID that can be used for unsubscribe

        Example:
            >>> def my_handler(event: Event):
            ...     print(f"Received: {event}")
            >>> bus = EventBus()
            >>> handler_id = bus.subscribe("user.login", my_handler)
            >>> bus.subscribe("user.*", my_handler)  # Wildcard
        """
        is_async = asyncio.iscoroutinefunction(handler)

        if is_async and not self._enable_async:
            raise ValueError("Async handlers not enabled for this event bus")

        # Create handler wrapper
        event_handler = EventHandler(
            callback=handler,
            priority=priority,
            event_type_pattern=event_type if "*" in event_type else None,
            filter_dict=filter_dict,
            is_async=is_async,
        )

        with self._lock:
            if "*" in event_type:
                # Wildcard subscription
                self._wildcard_handlers.append(event_handler)
                self._wildcard_handlers.sort(key=lambda h: h.priority, reverse=True)
                logger.debug(
                    f"Added wildcard handler {event_handler.handler_id} "
                    f"for pattern '{event_type}' with priority {priority}"
                )
            else:
                # Exact event type subscription
                self._handlers[event_type].append(event_handler)
                self._handlers[event_type].sort(key=lambda h: h.priority, reverse=True)
                logger.debug(
                    f"Added handler {event_handler.handler_id} "
                    f"for type '{event_type}' with priority {priority}"
                )

            # Setup weak reference if requested
            if weak_ref:
                try:
                    ref = weakref.ref(handler, self._make_cleanup_callback(event_handler.handler_id))
                    self._weak_refs.add(ref)
                except TypeError:
                    # Some objects can't be weak referenced (e.g., lambdas)
                    logger.debug(f"Cannot create weak reference for handler {event_handler.handler_id}")

            self._stats["total_subscriptions"] += 1

        return event_handler.handler_id

    def _make_cleanup_callback(self, handler_id: str) -> Callable[[weakref.ref], None]:
        """
        Create cleanup callback for weak reference.

        Args:
            handler_id: ID of handler to clean up

        Returns:
            Cleanup callback function
        """
        def cleanup(ref: weakref.ref) -> None:
            """Remove handler when weak reference is deleted."""
            self.unsubscribe_by_id(handler_id)
            self._weak_refs.discard(ref)

        return cleanup

    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Any],
    ) -> bool:
        """
        Unsubscribe a handler from an event type.

        Args:
            event_type: Event type to unsubscribe from
            handler: Handler function to remove

        Returns:
            True if handler was found and removed
        """
        with self._lock:
            if event_type in self._handlers:
                original_count = len(self._handlers[event_type])
                self._handlers[event_type] = [
                    h for h in self._handlers[event_type]
                    if h.callback != handler
                ]
                removed = original_count > len(self._handlers[event_type])
                if removed:
                    logger.debug(f"Unsubscribed handler from '{event_type}'")
                return removed
            return False

    def unsubscribe_by_id(self, handler_id: str) -> bool:
        """
        Unsubscribe a handler by its ID.

        Args:
            handler_id: Handler ID returned from subscribe()

        Returns:
            True if handler was found and removed
        """
        with self._lock:
            # Check exact subscriptions
            for event_type, handlers in list(self._handlers.items()):
                original_count = len(handlers)
                self._handlers[event_type] = [
                    h for h in handlers if h.handler_id != handler_id
                ]
                if len(self._handlers[event_type]) < original_count:
                    if not self._handlers[event_type]:
                        del self._handlers[event_type]
                    logger.debug(f"Unsubscribed handler {handler_id} from '{event_type}'")
                    return True

            # Check wildcard subscriptions
            original_count = len(self._wildcard_handlers)
            self._wildcard_handlers = [
                h for h in self._wildcard_handlers if h.handler_id != handler_id
            ]
            if len(self._wildcard_handlers) < original_count:
                logger.debug(f"Unsubscribed wildcard handler {handler_id}")
                return True

            return False

    def unsubscribe_all(self, event_type: Optional[str] = None) -> int:
        """
        Unsubscribe all handlers from an event type or all types.

        Args:
            event_type: Event type to clear, or None for all types

        Returns:
            Number of handlers removed
        """
        with self._lock:
            if event_type is None:
                # Remove all handlers
                total = sum(len(handlers) for handlers in self._handlers.values())
                total += len(self._wildcard_handlers)
                self._handlers.clear()
                self._wildcard_handlers.clear()
                logger.info(f"Unsubscribed all {total} handlers")
                return total
            elif event_type in self._handlers:
                count = len(self._handlers[event_type])
                del self._handlers[event_type]
                logger.info(f"Unsubscribed {count} handlers from '{event_type}'")
                return count
            return 0

    def publish(self, event: Event) -> int:
        """
        Publish an event synchronously to all matching handlers.

        Handlers are executed in priority order (highest first).
        Async handlers are scheduled but not awaited.

        Args:
            event: Event to publish

        Returns:
            Number of handlers that were notified
        """
        if self._enable_history:
            with self._lock:
                self._event_history.append(event)

        handlers = self._get_matching_handlers(event)

        if not handlers:
            logger.debug(f"No handlers for event: {event}")
            return 0

        logger.debug(f"Publishing event {event} to {len(handlers)} handlers")

        executed = 0
        for handler in handlers:
            try:
                if handler.is_async:
                    # Schedule async handler
                    asyncio.create_task(self._execute_async_handler(handler, event))
                else:
                    # Execute sync handler
                    handler.callback(event)
                executed += 1
            except Exception as e:
                logger.error(
                    f"Error executing handler {handler.handler_id} "
                    f"for event {event}: {e}",
                    exc_info=True
                )

        with self._lock:
            self._stats["total_published"] += 1
            self._stats[f"published_{event.event_type}"] += 1

        return executed

    async def publish_async(self, event: Event) -> int:
        """
        Publish an event asynchronously to all matching handlers.

        Both sync and async handlers are executed, with async handlers
        being awaited.

        Args:
            event: Event to publish

        Returns:
            Number of handlers that were notified
        """
        if self._enable_history:
            with self._lock:
                self._event_history.append(event)

        handlers = self._get_matching_handlers(event)

        if not handlers:
            logger.debug(f"No handlers for event: {event}")
            return 0

        logger.debug(f"Publishing event {event} to {len(handlers)} handlers (async)")

        executed = 0
        tasks = []

        for handler in handlers:
            try:
                if handler.is_async:
                    tasks.append(self._execute_async_handler(handler, event))
                else:
                    # Execute sync handler in executor
                    loop = asyncio.get_event_loop()
                    tasks.append(
                        loop.run_in_executor(None, handler.callback, event)
                    )
                executed += 1
            except Exception as e:
                logger.error(
                    f"Error scheduling handler {handler.handler_id} "
                    f"for event {event}: {e}",
                    exc_info=True
                )

        # Wait for all handlers to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Handler {handlers[i].handler_id} raised exception: {result}",
                        exc_info=result
                    )

        with self._lock:
            self._stats["total_published"] += 1
            self._stats[f"published_{event.event_type}"] += 1

        return executed

    async def _execute_async_handler(
        self,
        handler: EventHandler,
        event: Event
    ) -> None:
        """
        Execute an async handler.

        Args:
            handler: Handler to execute
            event: Event to pass to handler
        """
        try:
            await handler.callback(event)
        except Exception as e:
            logger.error(
                f"Error in async handler {handler.handler_id}: {e}",
                exc_info=True
            )

    def _get_matching_handlers(self, event: Event) -> List[EventHandler]:
        """
        Get all handlers that match the event.

        Args:
            event: Event to match

        Returns:
            List of matching handlers in priority order
        """
        handlers = []

        with self._lock:
            # Get exact match handlers
            if event.event_type in self._handlers:
                for handler in self._handlers[event.event_type]:
                    if handler.matches_event(event):
                        handlers.append(handler)

            # Get wildcard handlers
            for handler in self._wildcard_handlers:
                if handler.matches_event(event):
                    handlers.append(handler)

        # Sort by priority (already sorted in lists, but combined list needs sorting)
        handlers.sort(key=lambda h: h.priority, reverse=True)

        return handlers

    def get_history(
        self,
        event_type: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> List[Event]:
        """
        Get event history with optional filtering.

        Args:
            event_type: Filter by event type (supports wildcards)
            filter_dict: Additional filter criteria
            limit: Maximum number of events to return

        Returns:
            List of matching events (newest first)
        """
        if not self._enable_history:
            return []

        with self._lock:
            events = list(self._event_history)

        # Filter by event type
        if event_type:
            events = [
                e for e in events
                if Event._match_pattern(e.event_type, event_type)
            ]

        # Filter by additional criteria
        if filter_dict:
            events = [e for e in events if e.matches_filter(filter_dict)]

        # Reverse to get newest first
        events = list(reversed(events))

        # Apply limit
        if limit:
            events = events[:limit]

        return events

    def replay_events(
        self,
        event_type: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> int:
        """
        Replay events from history.

        Republishes historical events matching the criteria.

        Args:
            event_type: Filter by event type (supports wildcards)
            filter_dict: Additional filter criteria
            limit: Maximum number of events to replay

        Returns:
            Number of events replayed
        """
        events = self.get_history(
            event_type=event_type,
            filter_dict=filter_dict,
            limit=limit,
        )

        logger.info(f"Replaying {len(events)} events")

        for event in reversed(events):  # Replay in original order
            self.publish(event)

        return len(events)

    def clear_history(self) -> int:
        """
        Clear event history.

        Returns:
            Number of events cleared
        """
        with self._lock:
            count = len(self._event_history)
            self._event_history.clear()
            logger.info(f"Cleared {count} events from history")
            return count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get event bus statistics.

        Returns:
            Dictionary of statistics
        """
        with self._lock:
            total_handlers = sum(len(h) for h in self._handlers.values())
            total_handlers += len(self._wildcard_handlers)

            return {
                "total_handlers": total_handlers,
                "exact_subscriptions": len(self._handlers),
                "wildcard_handlers": len(self._wildcard_handlers),
                "history_size": len(self._event_history),
                "history_enabled": self._enable_history,
                "async_enabled": self._enable_async,
                **self._stats,
            }

    def get_handlers_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get information about all registered handlers.

        Returns:
            Dictionary mapping event types to handler information
        """
        with self._lock:
            info = {}

            # Exact subscriptions
            for event_type, handlers in self._handlers.items():
                info[event_type] = [
                    {
                        "handler_id": h.handler_id,
                        "priority": h.priority,
                        "is_async": h.is_async,
                        "has_filter": h.filter_dict is not None,
                    }
                    for h in handlers
                ]

            # Wildcard subscriptions
            if self._wildcard_handlers:
                info["*"] = [
                    {
                        "handler_id": h.handler_id,
                        "priority": h.priority,
                        "is_async": h.is_async,
                        "has_filter": h.filter_dict is not None,
                    }
                    for h in self._wildcard_handlers
                ]

            return info


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_global_event_bus() -> EventBus:
    """
    Get or create the global event bus instance.

    Returns:
        Global EventBus instance
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def set_global_event_bus(event_bus: EventBus) -> None:
    """
    Set the global event bus instance.

    Args:
        event_bus: EventBus instance to set as global
    """
    global _global_event_bus
    _global_event_bus = event_bus
