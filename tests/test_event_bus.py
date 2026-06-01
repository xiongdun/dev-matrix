import asyncio
from unittest.mock import patch

import pytest

from app.events.bus import EventBus
from app.events.types import Event


class TestEventBus:
    @pytest.fixture
    def bus(self):
        bus = EventBus()
        yield bus
        bus.clear()

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, bus):
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("test.event", handler)
        event = Event(type="test.event", payload={"key": "value"})
        await bus.publish(event)

        assert len(received) == 1
        assert received[0].type == "test.event"
        assert received[0].payload == {"key": "value"}

    @pytest.mark.asyncio
    async def test_unsubscribe(self, bus):
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("test.event", handler)
        bus.unsubscribe("test.event", handler)
        event = Event(type="test.event")
        await bus.publish(event)

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_publish_no_handlers(self, bus):
        event = Event(type="no.handlers", payload={})
        await bus.publish(event)

    @pytest.mark.asyncio
    async def test_publish_handler_exception(self, bus):
        def bad_handler(event):
            raise RuntimeError("handler error")

        bus.subscribe("test.event", bad_handler)
        event = Event(type="test.event", payload={})

        with patch("app.events.bus.logger.exception") as mock_log:
            await bus.publish(event)
            mock_log.assert_called_once()
            assert "raised an exception" in mock_log.call_args[0][0]

    @pytest.mark.asyncio
    async def test_clear(self, bus):
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("test.event", handler)
        bus.clear()
        event = Event(type="test.event")
        await bus.publish(event)

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_multiple_handlers(self, bus):
        received1 = []
        received2 = []

        def handler1(event):
            received1.append(event)

        def handler2(event):
            received2.append(event)

        bus.subscribe("test.event", handler1)
        bus.subscribe("test.event", handler2)
        event = Event(type="test.event")
        await bus.publish(event)

        assert len(received1) == 1
        assert len(received2) == 1

    @pytest.mark.asyncio
    async def test_async_handler(self, bus):
        received = []

        async def async_handler(event):
            await asyncio.sleep(0.01)
            received.append(event)

        bus.subscribe("test.event", async_handler)
        event = Event(type="test.event")
        await bus.publish(event)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_unsubscribe_not_subscribed(self, bus):
        def handler(event):
            pass

        bus.unsubscribe("test.event", handler)

    @pytest.mark.asyncio
    async def test_handler_timeout(self, bus, monkeypatch):
        async def slow_handler(event):
            await asyncio.sleep(100)

        monkeypatch.setattr("app.events.bus.DEFAULT_SUBSCRIBER_TIMEOUT", 0.01)
        bus.subscribe("test.event", slow_handler)
        event = Event(type="test.event")

        with patch("app.events.bus.logger.error") as mock_log:
            await bus.publish(event)
            mock_log.assert_called_once()
            assert "timed out" in mock_log.call_args[0][0]
