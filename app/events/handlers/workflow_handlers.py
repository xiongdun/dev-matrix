import logging
from typing import Any

from app.events.types import Event

logger = logging.getLogger(__name__)


def on_workflow_started(event: Event) -> None:
    logger.info("Workflow started: project=%s", event.project_id)


def on_workflow_completed(event: Event) -> None:
    logger.info("Workflow completed: project=%s", event.project_id)


def on_workflow_failed(event: Event) -> None:
    logger.error("Workflow failed: project=%s, error=%s", event.project_id, event.payload)
