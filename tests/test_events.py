import pytest

from app.events.bus import EventBus
from app.events.types import Event, EventTypes


class TestEventBus:
    @pytest.fixture
    def bus(self):
        return EventBus()

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, bus):
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(EventTypes.WORKFLOW_STARTED, handler)
        event = Event(type=EventTypes.WORKFLOW_STARTED, payload={"project_id": "p1"})
        await bus.publish(event)

        assert len(received) == 1
        assert received[0].type == EventTypes.WORKFLOW_STARTED

    @pytest.mark.asyncio
    async def test_unsubscribe(self, bus):
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(EventTypes.WORKFLOW_STARTED, handler)
        bus.unsubscribe(EventTypes.WORKFLOW_STARTED, handler)
        event = Event(type=EventTypes.WORKFLOW_STARTED)
        await bus.publish(event)

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_async_handler(self, bus):
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(EventTypes.AGENT_COMPLETED, handler)
        event = Event(type=EventTypes.AGENT_COMPLETED)
        await bus.publish(event)

        assert len(received) == 1
