import logging

from app.events.types import Event

logger = logging.getLogger(__name__)


def on_approval_required(event: Event) -> None:
    logger.info(
        "Approval required: project=%s, stage=%s",
        event.project_id,
        event.payload.get("stage"),
    )


def on_approval_approved(event: Event) -> None:
    logger.info("Approval approved: project=%s", event.project_id)


def on_approval_rejected(event: Event) -> None:
    logger.warning("Approval rejected: project=%s", event.project_id)
