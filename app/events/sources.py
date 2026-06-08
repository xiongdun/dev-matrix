"""外部事件源适配器模块。

支持：
- GitHub Webhook 接收
- 文件系统监控
- 定时事件触发
- 自定义 Webhook
"""

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from app.events.enhanced_bus import EnhancedEvent, EventSource, enhanced_bus

logger = logging.getLogger(__name__)
router = APIRouter()


# ===== GitHub Webhook =====

@router.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default=""),
    x_github_delivery: str = Header(default=""),
    x_hub_signature_256: str = Header(default=""),
):
    """接收 GitHub Webhook 事件。

    支持的事件类型：
    - push: 代码推送
    - pull_request: PR 创建/更新/合并
    - issues: Issue 创建/更新
    - workflow_run: GitHub Actions 运行结果
    """
    body = await request.body()

    # 验证签名（可选）
    webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    if webhook_secret:
        expected_sig = "sha256=" + hmac.new(
            webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(x_hub_signature_256, expected_sig):
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # 映射 GitHub 事件到 DevMatrix 事件
    event_type_map = {
        "push": "github.push",
        "pull_request": "github.pull_request",
        "issues": "github.issue",
        "workflow_run": "github.workflow_run",
    }

    event_type = event_type_map.get(x_github_event, f"github.{x_github_event}")

    event = EnhancedEvent(
        type=event_type,
        payload={
            "github_event": x_github_event,
            "delivery_id": x_github_delivery,
            "data": payload,
            "repository": payload.get("repository", {}).get("full_name", ""),
            "sender": payload.get("sender", {}).get("login", ""),
        },
        source="github",
        source_type=EventSource.WEBHOOK,
        project_id=payload.get("repository", {}).get("name", ""),
    )

    await enhanced_bus.publish(event)

    return {"status": "ok", "event_type": event_type}


# ===== 通用 Webhook =====

@router.post("/webhook/custom/{source}")
async def custom_webhook(
    source: str,
    request: Request,
    x_webhook_secret: str = Header(default=""),
):
    """接收自定义 Webhook 事件。

    Args:
        source: 事件来源标识（如 jira、gitlab、slack 等）
    """
    body = await request.body()

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        payload = {"raw": body.decode("utf-8", errors="replace")}

    event = EnhancedEvent(
        type=f"webhook.{source}",
        payload=payload,
        source=source,
        source_type=EventSource.WEBHOOK,
    )

    await enhanced_bus.publish(event)

    return {"status": "ok", "source": source}


# ===== 文件系统事件 =====

class FileWatcher:
    """文件系统监控器。

    监控指定目录的文件变更，发布文件事件。
    """

    def __init__(self, watch_dirs: list[str] | None = None):
        self.watch_dirs = watch_dirs or []
        self._watched_files: dict[str, float] = {}  # path -> mtime
        self._running = False

    def scan(self) -> list[EnhancedEvent]:
        """扫描文件变更，返回事件列表。"""
        events = []
        for watch_dir in self.watch_dirs:
            path = Path(watch_dir)
            if not path.exists():
                continue

            for file_path in path.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    try:
                        mtime = file_path.stat().st_mtime
                        str_path = str(file_path)

                        if str_path in self._watched_files:
                            if mtime > self._watched_files[str_path]:
                                events.append(
                                    EnhancedEvent(
                                        type="file.modified",
                                        payload={"path": str_path, "name": file_path.name},
                                        source="file_watcher",
                                        source_type=EventSource.FILE_WATCHER,
                                    )
                                )
                        else:
                            events.append(
                                EnhancedEvent(
                                    type="file.created",
                                    payload={"path": str_path, "name": file_path.name},
                                    source="file_watcher",
                                    source_type=EventSource.FILE_WATCHER,
                                )
                            )

                        self._watched_files[str_path] = mtime
                    except OSError:
                        continue

        return events


# ===== 定时事件 =====

class CronEventSource:
    """定时事件源。

    基于 APScheduler 的定时事件触发。
    """

    def __init__(self):
        self._jobs: dict[str, dict] = {}

    def add_job(
        self,
        job_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        interval_seconds: int = 3600,
    ) -> None:
        """添加定时任务。"""
        self._jobs[job_id] = {
            "event_type": event_type,
            "payload": payload or {},
            "interval": interval_seconds,
            "last_run": None,
        }
        logger.info("Added cron job: %s (every %ds)", job_id, interval_seconds)

    def remove_job(self, job_id: str) -> None:
        """移除定时任务。"""
        self._jobs.pop(job_id, None)

    async def tick(self) -> None:
        """检查并触发到期的定时事件。"""
        now = datetime.now(timezone.utc)
        for job_id, job in self._jobs.items():
            last_run = job["last_run"]
            if last_run is None or (now - last_run).total_seconds() >= job["interval"]:
                event = EnhancedEvent(
                    type=job["event_type"],
                    payload={**job["payload"], "cron_job_id": job_id},
                    source="cron",
                    source_type=EventSource.CRON,
                )
                await enhanced_bus.publish(event)
                job["last_run"] = now
                logger.info("Cron job triggered: %s", job_id)


# 全局实例
file_watcher = FileWatcher()
cron_source = CronEventSource()
