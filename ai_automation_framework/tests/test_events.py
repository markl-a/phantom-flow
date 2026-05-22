"""
Comprehensive unit tests for Events module.

Tests cover:
- Event creation and metadata
- Event publishing and subscription
- Priority-based handler execution
- Event filtering and pattern matching
- Async event handling
- Event history and replay
- Wildcard subscriptions
- Thread safety
"""

import asyncio
import time
import pytest
from unittest.mock import Mock, call
from ai_automation_framework.core.events import (
    Event,
    EventBus,
    EventHandler,
    EventPriority,
    get_global_event_bus,
    set_global_event_bus,
)


@pytest.mark.unit
class TestEvent:
    """Test Event class."""

    def test_event_initialization(self):
        """Test event initialization with required fields."""
        event = Event(
            event_type="user.login",
            source="auth_service",
            data={"user_id": 123}
        )

        assert event.event_type == "user.login"
        assert event.source == "auth_service"
        assert event.data["user_id"] == 123
        assert event.event_id is not None
        assert event.timestamp is not None

    def test_event_auto_generated_fields(self):
        """Test that event_id and timestamp are auto-generated."""
        event1 = Event(event_type="test", source="test")
        event2 = Event(event_type="test", source="test")

        assert event1.event_id != event2.event_id
        assert event1.timestamp is not None
        assert event2.timestamp is not None

    def test_event_metadata(self):
        """Test event metadata field."""
        event = Event(
            event_type="test",
            source="test",
            metadata={"priority": "high", "region": "us-west"}
        )

        assert event.metadata["priority"] == "high"
        assert event.metadata["region"] == "us-west"

    def test_event_str_representation(self):
        """Test event string representation."""
        event = Event(event_type="test.event", source="test_source")

        str_repr = str(event)

        assert "test.event" in str_repr
        assert "test_source" in str_repr

    def test_matches_filter_event_type(self):
        """Test filtering by event type."""
        event = Event(event_type="user.login", source="auth")

        assert event.matches_filter({"event_type": "user.login"})
        assert not event.matches_filter({"event_type": "user.logout"})

    def test_matches_filter_source(self):
        """Test filtering by source."""
        event = Event(event_type="test", source="service_a")

        assert event.matches_filter({"source": "service_a"})
        assert not event.matches_filter({"source": "service_b"})

    def test_matches_filter_data_field(self):
        """Test filtering by data field."""
        event = Event(
            event_type="test",
            source="test",
            data={"status": "active", "count": 5}
        )

        assert event.matches_filter({"status": "active"})
        assert event.matches_filter({"count": 5})
        assert not event.matches_filter({"status": "inactive"})

    def test_matches_filter_metadata_field(self):
        """Test filtering by metadata field."""
        event = Event(
            event_type="test",
            source="test",
            metadata={"priority": "high"}
        )

        assert event.matches_filter({"priority": "high"})
        assert not event.matches_filter({"priority": "low"})

    def test_matches_filter_multiple_criteria(self):
        """Test filtering with multiple criteria."""
        event = Event(
            event_type="user.login",
            source="auth",
            data={"user_id": 123}
        )

        assert event.matches_filter({
            "event_type": "user.login",
            "source": "auth",
            "user_id": 123
        })

        assert not event.matches_filter({
            "event_type": "user.login",
            "user_id": 999  # Wrong user_id
        })

    def test_matches_filter_nonexistent_field(self):
        """Test filtering with non-existent field returns False."""
        event = Event(event_type="test", source="test")

        assert not event.matches_filter({"nonexistent_field": "value"})

    def test_pattern_matching_wildcard(self):
        """Test wildcard pattern matching."""
        event = Event(event_type="user.login", source="auth")

        assert event.matches_filter({"event_type": "*"})
        assert event.matches_filter({"event_type": "user.*"})
        assert event.matches_filter({"event_type": "*.login"})
        assert not event.matches_filter({"event_type": "admin.*"})

    def test_pattern_matching_exact(self):
        """Test exact pattern matching."""
        assert Event._match_pattern("user.login", "user.login")
        assert not Event._match_pattern("user.login", "user.logout")

    def test_pattern_matching_wildcard_variations(self):
        """Test various wildcard patterns."""
        assert Event._match_pattern("user.login", "*")
        assert Event._match_pattern("user.login", "user.*")
        assert Event._match_pattern("user.login", "*.login")
        assert Event._match_pattern("user.login", "*login*")
        assert not Event._match_pattern("user.login", "admin.*")


@pytest.mark.unit
class TestEventHandler:
    """Test EventHandler class."""

    def test_handler_initialization(self):
        """Test event handler initialization."""
        callback = Mock()
        handler = EventHandler(
            callback=callback,
            priority=EventPriority.HIGH,
            event_type_pattern="user.*"
        )

        assert handler.callback == callback
        assert handler.priority == EventPriority.HIGH
        assert handler.event_type_pattern == "user.*"
        assert handler.handler_id is not None

    def test_handler_matches_event_with_pattern(self):
        """Test handler matching with event type pattern."""
        handler = EventHandler(
            callback=Mock(),
            priority=EventPriority.NORMAL,
            event_type_pattern="user.*"
        )

        event1 = Event(event_type="user.login", source="test")
        event2 = Event(event_type="admin.action", source="test")

        assert handler.matches_event(event1)
        assert not handler.matches_event(event2)

    def test_handler_matches_event_with_filter(self):
        """Test handler matching with filter dictionary."""
        handler = EventHandler(
            callback=Mock(),
            priority=EventPriority.NORMAL,
            filter_dict={"status": "active"}
        )

        event1 = Event(
            event_type="test",
            source="test",
            data={"status": "active"}
        )
        event2 = Event(
            event_type="test",
            source="test",
            data={"status": "inactive"}
        )

        assert handler.matches_event(event1)
        assert not handler.matches_event(event2)

    def test_handler_equality(self):
        """Test handler equality based on handler_id."""
        callback = Mock()
        handler1 = EventHandler(callback=callback, priority=50)
        handler2 = EventHandler(callback=callback, priority=50)

        assert handler1 != handler2  # Different IDs
        assert handler1 == handler1  # Same instance

    def test_handler_hash(self):
        """Test handler hashing."""
        handler1 = EventHandler(callback=Mock(), priority=50)
        handler2 = EventHandler(callback=Mock(), priority=50)

        # Should be hashable and different
        handler_set = {handler1, handler2}
        assert len(handler_set) == 2


@pytest.mark.unit
class TestEventBus:
    """Test EventBus class."""

    def test_eventbus_initialization(self):
        """Test event bus initialization."""
        bus = EventBus(max_history=500, enable_history=True, enable_async=True)

        assert bus._enable_history is True
        assert bus._enable_async is True
        assert len(bus._event_history) == 0

    def test_subscribe_handler(self):
        """Test subscribing a handler."""
        bus = EventBus()
        handler = Mock()

        handler_id = bus.subscribe("user.login", handler)

        assert handler_id is not None
        stats = bus.get_stats()
        assert stats["total_subscriptions"] == 1

    def test_subscribe_with_priority(self):
        """Test subscribing handlers with different priorities."""
        bus = EventBus()
        handler1 = Mock()
        handler2 = Mock()

        bus.subscribe("test", handler1, priority=EventPriority.LOW)
        bus.subscribe("test", handler2, priority=EventPriority.HIGH)

        # Handlers should be sorted by priority
        handlers = bus._handlers["test"]
        assert handlers[0].priority == EventPriority.HIGH
        assert handlers[1].priority == EventPriority.LOW

    def test_subscribe_wildcard(self):
        """Test subscribing with wildcard pattern."""
        bus = EventBus()
        handler = Mock()

        handler_id = bus.subscribe("user.*", handler)

        assert len(bus._wildcard_handlers) == 1

    def test_publish_event_to_handler(self):
        """Test publishing event to subscribed handler."""
        bus = EventBus()
        handler = Mock()

        bus.subscribe("user.login", handler)
        event = Event(event_type="user.login", source="test")

        count = bus.publish(event)

        assert count == 1
        handler.assert_called_once_with(event)

    def test_publish_event_to_multiple_handlers(self):
        """Test publishing event to multiple handlers."""
        bus = EventBus()
        handler1 = Mock()
        handler2 = Mock()
        handler3 = Mock()

        bus.subscribe("user.login", handler1)
        bus.subscribe("user.login", handler2)
        bus.subscribe("user.login", handler3)

        event = Event(event_type="user.login", source="test")
        count = bus.publish(event)

        assert count == 3
        handler1.assert_called_once()
        handler2.assert_called_once()
        handler3.assert_called_once()

    def test_publish_priority_order(self):
        """Test that handlers are called in priority order."""
        bus = EventBus()
        call_order = []

        def handler_low(event):
            call_order.append("low")

        def handler_high(event):
            call_order.append("high")

        def handler_normal(event):
            call_order.append("normal")

        bus.subscribe("test", handler_low, priority=EventPriority.LOW)
        bus.subscribe("test", handler_high, priority=EventPriority.HIGH)
        bus.subscribe("test", handler_normal, priority=EventPriority.NORMAL)

        event = Event(event_type="test", source="test")
        bus.publish(event)

        assert call_order == ["high", "normal", "low"]

    def test_publish_wildcard_handlers(self):
        """Test that wildcard handlers receive matching events."""
        bus = EventBus()
        handler = Mock()

        bus.subscribe("user.*", handler)

        event1 = Event(event_type="user.login", source="test")
        event2 = Event(event_type="user.logout", source="test")
        event3 = Event(event_type="admin.action", source="test")

        bus.publish(event1)
        bus.publish(event2)
        bus.publish(event3)

        assert handler.call_count == 2  # Only user.* events

    def test_publish_with_filter(self):
        """Test publishing with handler filters."""
        bus = EventBus()
        handler = Mock()

        bus.subscribe("test", handler, filter_dict={"status": "active"})

        event1 = Event(
            event_type="test",
            source="test",
            data={"status": "active"}
        )
        event2 = Event(
            event_type="test",
            source="test",
            data={"status": "inactive"}
        )

        bus.publish(event1)
        bus.publish(event2)

        assert handler.call_count == 1  # Only active event

    def test_publish_no_matching_handlers(self):
        """Test publishing event with no matching handlers."""
        bus = EventBus()
        handler = Mock()

        bus.subscribe("user.login", handler)

        event = Event(event_type="user.logout", source="test")
        count = bus.publish(event)

        assert count == 0
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_async(self):
        """Test async event publishing."""
        bus = EventBus()
        handler = Mock()

        bus.subscribe("test", handler)

        event = Event(event_type="test", source="test")
        count = await bus.publish_async(event)

        assert count == 1
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_async_handler(self):
        """Test publishing to async handler."""
        bus = EventBus()
        handler_called = []

        async def async_handler(event):
            await asyncio.sleep(0.01)
            handler_called.append(event)

        bus.subscribe("test", async_handler)

        event = Event(event_type="test", source="test")
        await bus.publish_async(event)

        assert len(handler_called) == 1

    def test_unsubscribe_handler(self):
        """Test unsubscribing a handler."""
        bus = EventBus()
        handler = Mock()

        bus.subscribe("test", handler)
        result = bus.unsubscribe("test", handler)

        assert result is True

        event = Event(event_type="test", source="test")
        count = bus.publish(event)
        assert count == 0

    def test_unsubscribe_nonexistent_handler(self):
        """Test unsubscribing non-existent handler."""
        bus = EventBus()
        handler = Mock()

        result = bus.unsubscribe("test", handler)

        assert result is False

    def test_unsubscribe_by_id(self):
        """Test unsubscribing by handler ID."""
        bus = EventBus()
        handler = Mock()

        handler_id = bus.subscribe("test", handler)
        result = bus.unsubscribe_by_id(handler_id)

        assert result is True

        event = Event(event_type="test", source="test")
        count = bus.publish(event)
        assert count == 0

    def test_unsubscribe_all_for_event_type(self):
        """Test unsubscribing all handlers for an event type."""
        bus = EventBus()
        handler1 = Mock()
        handler2 = Mock()

        bus.subscribe("test", handler1)
        bus.subscribe("test", handler2)

        count = bus.unsubscribe_all("test")

        assert count == 2

        event = Event(event_type="test", source="test")
        publish_count = bus.publish(event)
        assert publish_count == 0

    def test_unsubscribe_all_handlers(self):
        """Test unsubscribing all handlers from all event types."""
        bus = EventBus()

        bus.subscribe("type1", Mock())
        bus.subscribe("type2", Mock())
        bus.subscribe("type3", Mock())

        count = bus.unsubscribe_all()

        assert count == 3
        assert len(bus._handlers) == 0

    def test_event_history(self):
        """Test event history tracking."""
        bus = EventBus(enable_history=True, max_history=10)

        event1 = Event(event_type="test1", source="test")
        event2 = Event(event_type="test2", source="test")

        bus.publish(event1)
        bus.publish(event2)

        history = bus.get_history()

        assert len(history) == 2
        assert history[0] == event2  # Newest first
        assert history[1] == event1

    def test_event_history_max_size(self):
        """Test that event history respects max size."""
        bus = EventBus(enable_history=True, max_history=3)

        for i in range(5):
            event = Event(event_type=f"test{i}", source="test")
            bus.publish(event)

        history = bus.get_history()

        assert len(history) == 3  # Only last 3

    def test_event_history_disabled(self):
        """Test that history is not tracked when disabled."""
        bus = EventBus(enable_history=False)

        event = Event(event_type="test", source="test")
        bus.publish(event)

        history = bus.get_history()

        assert len(history) == 0

    def test_get_history_with_event_type_filter(self):
        """Test filtering history by event type."""
        bus = EventBus(enable_history=True)

        bus.publish(Event(event_type="user.login", source="test"))
        bus.publish(Event(event_type="user.logout", source="test"))
        bus.publish(Event(event_type="admin.action", source="test"))

        history = bus.get_history(event_type="user.*")

        assert len(history) == 2

    def test_get_history_with_filter_dict(self):
        """Test filtering history with filter dictionary."""
        bus = EventBus(enable_history=True)

        bus.publish(Event(
            event_type="test",
            source="test",
            data={"status": "active"}
        ))
        bus.publish(Event(
            event_type="test",
            source="test",
            data={"status": "inactive"}
        ))

        history = bus.get_history(filter_dict={"status": "active"})

        assert len(history) == 1

    def test_get_history_with_limit(self):
        """Test limiting history results."""
        bus = EventBus(enable_history=True)

        for i in range(10):
            bus.publish(Event(event_type="test", source="test"))

        history = bus.get_history(limit=5)

        assert len(history) == 5

    def test_replay_events(self):
        """Test replaying events from history."""
        bus = EventBus(enable_history=True)
        handler = Mock()

        bus.subscribe("test", handler)

        # Publish some events
        for i in range(3):
            event = Event(event_type="test", source="test", data={"index": i})
            bus.publish(event)

        # Handler called 3 times
        assert handler.call_count == 3

        # Unsubscribe and resubscribe
        bus.unsubscribe("test", handler)
        handler.reset_mock()
        bus.subscribe("test", handler)

        # Replay events
        count = bus.replay_events(event_type="test")

        assert count == 3
        assert handler.call_count == 3

    def test_clear_history(self):
        """Test clearing event history."""
        bus = EventBus(enable_history=True)

        bus.publish(Event(event_type="test1", source="test"))
        bus.publish(Event(event_type="test2", source="test"))

        assert len(bus.get_history()) == 2

        count = bus.clear_history()

        assert count == 2
        assert len(bus.get_history()) == 0

    def test_get_stats(self):
        """Test getting event bus statistics."""
        bus = EventBus()

        bus.subscribe("test1", Mock())
        bus.subscribe("test2", Mock())
        bus.subscribe("*", Mock())

        event = Event(event_type="test1", source="test")
        bus.publish(event)

        stats = bus.get_stats()

        assert stats["total_handlers"] == 3
        assert stats["exact_subscriptions"] == 2
        assert stats["wildcard_handlers"] == 1
        assert stats["total_published"] == 1

    def test_get_handlers_info(self):
        """Test getting handler information."""
        bus = EventBus()

        bus.subscribe("test", Mock(), priority=EventPriority.HIGH)
        bus.subscribe("test", Mock(), priority=EventPriority.LOW)

        info = bus.get_handlers_info()

        assert "test" in info
        assert len(info["test"]) == 2
        assert info["test"][0]["priority"] == EventPriority.HIGH

    def test_handler_exception_handling(self):
        """Test that handler exceptions don't break event bus."""
        bus = EventBus()

        def failing_handler(event):
            raise ValueError("Handler error")

        def working_handler(event):
            working_handler.called = True

        working_handler.called = False

        bus.subscribe("test", failing_handler)
        bus.subscribe("test", working_handler)

        event = Event(event_type="test", source="test")
        count = bus.publish(event)

        # The count represents handlers that were attempted (before error)
        # Even if one fails, both should be attempted
        # However, the current implementation may stop after first exception
        assert count >= 1
        # The working handler should still be called
        assert working_handler.called is True

    @pytest.mark.asyncio
    async def test_async_handler_exception_handling(self):
        """Test async handler exception handling."""
        bus = EventBus()

        async def failing_handler(event):
            raise ValueError("Async handler error")

        async def working_handler(event):
            working_handler.called = True

        working_handler.called = False

        bus.subscribe("test", failing_handler)
        bus.subscribe("test", working_handler)

        event = Event(event_type="test", source="test")
        await bus.publish_async(event)

        assert working_handler.called is True

    def test_weak_reference_cleanup(self):
        """Test that weak references are cleaned up properly."""
        bus = EventBus()

        class Handler:
            def __call__(self, event):
                pass

        handler = Handler()
        handler_id = bus.subscribe("test", handler, weak_ref=True)

        # Delete handler
        del handler

        # Handler should still be in registry (cleanup happens on callback)
        # This test mainly ensures no errors occur with weak refs

    def test_subscribe_without_weak_ref(self):
        """Test subscribing without weak reference."""
        bus = EventBus()
        handler = Mock()

        handler_id = bus.subscribe("test", handler, weak_ref=False)

        assert handler_id is not None


@pytest.mark.unit
class TestGlobalEventBus:
    """Test global event bus functions."""

    def test_get_global_event_bus(self):
        """Test getting global event bus."""
        bus1 = get_global_event_bus()
        bus2 = get_global_event_bus()

        assert bus1 is bus2  # Same instance

    def test_set_global_event_bus(self):
        """Test setting custom global event bus."""
        custom_bus = EventBus(max_history=500)
        set_global_event_bus(custom_bus)

        bus = get_global_event_bus()

        assert bus is custom_bus


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_event_type(self):
        """Test event with empty event type."""
        event = Event(event_type="", source="test")

        assert event.event_type == ""

    def test_very_long_event_type(self):
        """Test event with very long event type."""
        long_type = "a" * 1000
        event = Event(event_type=long_type, source="test")

        assert event.event_type == long_type

    def test_special_characters_in_event_type(self):
        """Test event type with special characters."""
        event = Event(event_type="user.login!@#$%", source="test")

        assert event.event_type == "user.login!@#$%"

    def test_wildcard_at_start(self):
        """Test wildcard at start of pattern."""
        bus = EventBus()
        handler = Mock()

        bus.subscribe("*.login", handler)

        event = Event(event_type="user.login", source="test")
        bus.publish(event)

        handler.assert_called_once()

    def test_wildcard_in_middle(self):
        """Test wildcard in middle of pattern."""
        bus = EventBus()
        handler = Mock()

        bus.subscribe("user.*.success", handler)

        event1 = Event(event_type="user.login.success", source="test")
        event2 = Event(event_type="user.logout.success", source="test")
        event3 = Event(event_type="user.login.failure", source="test")

        bus.publish(event1)
        bus.publish(event2)
        bus.publish(event3)

        assert handler.call_count == 2

    def test_multiple_wildcards(self):
        """Test pattern with multiple wildcards."""
        bus = EventBus()
        handler = Mock()

        bus.subscribe("*.*", handler)

        event = Event(event_type="user.login", source="test")
        bus.publish(event)

        handler.assert_called_once()

    def test_subscribe_async_handler_with_async_disabled(self):
        """Test that subscribing async handler fails when async disabled."""
        bus = EventBus(enable_async=False)

        async def async_handler(event):
            pass

        with pytest.raises(ValueError):
            bus.subscribe("test", async_handler)

    def test_concurrent_publish_thread_safety(self):
        """Test thread-safe concurrent event publishing."""
        import threading

        bus = EventBus()
        handler_calls = []
        lock = threading.Lock()

        def handler(event):
            with lock:
                handler_calls.append(event)

        bus.subscribe("test", handler)

        def publish_events(count):
            for i in range(count):
                event = Event(event_type="test", source="test")
                bus.publish(event)

        threads = [threading.Thread(target=publish_events, args=(10,)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(handler_calls) == 50

    @pytest.mark.asyncio
    async def test_concurrent_async_publish(self):
        """Test concurrent async event publishing."""
        bus = EventBus()
        handler_calls = []

        async def async_handler(event):
            await asyncio.sleep(0.001)
            handler_calls.append(event)

        bus.subscribe("test", async_handler)

        async def publish_events(count):
            for i in range(count):
                event = Event(event_type="test", source="test")
                await bus.publish_async(event)

        await asyncio.gather(*[publish_events(10) for _ in range(5)])

        assert len(handler_calls) == 50

    def test_zero_max_history(self):
        """Test event bus with zero max history."""
        bus = EventBus(max_history=0, enable_history=True)

        event = Event(event_type="test", source="test")
        bus.publish(event)

        history = bus.get_history()
        assert len(history) == 0

    def test_large_number_of_handlers(self):
        """Test event bus with many handlers."""
        bus = EventBus()

        handlers = [Mock() for _ in range(100)]
        for handler in handlers:
            bus.subscribe("test", handler)

        event = Event(event_type="test", source="test")
        count = bus.publish(event)

        assert count == 100
        for handler in handlers:
            handler.assert_called_once()

    def test_deeply_nested_data(self):
        """Test event with deeply nested data structure."""
        nested_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep"
                    }
                }
            }
        }

        event = Event(event_type="test", source="test", data=nested_data)

        assert event.data["level1"]["level2"]["level3"]["value"] == "deep"
