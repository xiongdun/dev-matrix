import logging
from typing import Any

from app.events.types import Event

logger = logging.getLogger(__name__)


def on_state_changed(event: Event) -> None:
    logger.info("State changed: %s", event.payload)


def on_snapshot_created(event: Event) -> None:
    logger.info("Snapshot created: %s", event.payload)


def on_rollback_performed(event: Event) -> None:
    logger.warning("Rollback performed: %s", event.payload)
