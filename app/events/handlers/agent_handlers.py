import logging

from app.events.types import Event

logger = logging.getLogger(__name__)


def on_agent_started(event: Event) -> None:
    logger.info("Agent started: %s", event.payload)


def on_agent_completed(event: Event) -> None:
    logger.info("Agent completed: %s", event.payload)


def on_agent_failed(event: Event) -> None:
    logger.error("Agent failed: %s", event.payload)
