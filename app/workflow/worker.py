"""Temporal Worker 入口模块。

启动 Temporal Worker，注册工作流和活动。
"""

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from app.config import get_settings
from app.workflow.activities import ACTIVITY_MAP
from app.workflow.definitions import DevWorkflow

logger = logging.getLogger(__name__)


async def main():
    settings = get_settings()
    client = await Client.new(settings.temporal_host)

    worker = Worker(
        client,
        task_queue="devmatrix-task-queue",
        workflows=[DevWorkflow],
        activities=list(ACTIVITY_MAP.values()),
    )

    logger.info("Starting Temporal Worker on %s", settings.temporal_host)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
