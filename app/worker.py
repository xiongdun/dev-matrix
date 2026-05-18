import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from app.config import get_settings
from app.workflow.activities import (
    create_state_snapshot,
    send_approval_request,
    execute_agent_task,
    wait_for_approval,
    rollback_state,
    notify_completion,
)
from app.workflow.definitions import DevWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    settings = get_settings()
    client = await Client.connect(settings.temporal_host)

    worker = Worker(
        client,
        task_queue="devmatrix-task-queue",
        workflows=[DevWorkflow],
        activities=[
            create_state_snapshot,
            send_approval_request,
            execute_agent_task,
            wait_for_approval,
            rollback_state,
            notify_completion,
        ],
    )

    logger.info("Starting Temporal worker on %s", settings.temporal_host)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
