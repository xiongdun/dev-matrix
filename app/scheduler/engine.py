"""定时任务调度引擎。

基于 APScheduler 的调度器封装，支持 cron/interval/date 三种触发器，
以及创建工作流实例和执行系统任务两种任务类型。

主要功能：
    - 启动/关闭调度器
    - 动态添加/更新/移除任务
    - 立即执行任务
    - 记录执行日志
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.orm import Session

from app.state.models import ScheduledTaskModel, ScheduledTaskLogModel, get_db

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> Optional["TaskScheduler"]:
    """获取全局调度器实例。"""
    global _scheduler
    if _scheduler is None:
        return None
    return TaskScheduler(_scheduler)


class TaskScheduler:
    """调度器封装类。"""

    def __init__(self, scheduler: AsyncIOScheduler):
        self._scheduler = scheduler

    def start(self):
        """启动调度器。"""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        """关闭调度器。"""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler shutdown")

    def _build_trigger(self, task: ScheduledTaskModel):
        """根据任务配置构建触发器。"""
        trigger_type = task.trigger_type
        expr = task.cron_expression

        if trigger_type == "cron":
            parts = expr.split()
            if len(parts) == 5:
                return CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4],
                )
            return CronTrigger()

        elif trigger_type == "interval":
            try:
                config = json.loads(expr) if expr else {}
            except json.JSONDecodeError:
                config = {}
            return IntervalTrigger(
                weeks=config.get("weeks", 0),
                days=config.get("days", 0),
                hours=config.get("hours", 0),
                minutes=config.get("minutes", 0),
                seconds=config.get("seconds", 0),
            )

        elif trigger_type == "date":
            try:
                run_date = datetime.fromisoformat(expr)
            except (ValueError, TypeError):
                run_date = datetime.utcnow()
            return DateTrigger(run_date=run_date)

        return CronTrigger()

    def add_task(self, task: ScheduledTaskModel):
        """添加任务到调度器。"""
        if not task.is_enabled:
            return

        job_id = f"scheduled_task_{task.id}"

        # 移除已存在的 job
        try:
            self._scheduler.remove_job(job_id)
        except Exception:
            pass

        trigger = self._build_trigger(task)
        self._scheduler.add_job(
            func=_execute_task_wrapper,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            args=[task.id],
        )
        logger.info("Added scheduled task id=%d to scheduler", task.id)

    def update_task(self, task: ScheduledTaskModel):
        """更新调度器中的任务。"""
        self.remove_task(task.id)
        if task.is_enabled:
            self.add_task(task)
        logger.info("Updated scheduled task id=%d in scheduler", task.id)

    def remove_task(self, task_id: int):
        """从调度器移除任务。"""
        job_id = f"scheduled_task_{task_id}"
        try:
            self._scheduler.remove_job(job_id)
            logger.info("Removed scheduled task id=%d from scheduler", task_id)
        except Exception:
            pass

    def execute_task_now(self, task: ScheduledTaskModel, db: Session) -> ScheduledTaskLogModel:
        """立即执行任务。"""
        return _execute_task(task, db)


def _execute_task_wrapper(task_id: int):
    """APScheduler 调用的包装函数。"""
    db = next(get_db())
    try:
        task = db.query(ScheduledTaskModel).filter(ScheduledTaskModel.id == task_id).first()
        if task and task.is_enabled:
            _execute_task(task, db)
    except Exception:
        logger.exception("Scheduled task wrapper failed for task_id=%d", task_id)
    finally:
        db.close()


def _execute_task(task: ScheduledTaskModel, db: Session) -> ScheduledTaskLogModel:
    """执行定时任务核心逻辑。"""
    log = ScheduledTaskLogModel(
        task_id=task.id,
        status="running",
        output="",
        error="",
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    try:
        config = json.loads(task.config_json) if task.config_json else {}

        if task.task_type == "workflow_instance":
            _run_workflow_instance_task(task, config, db)
        else:
            _run_system_task(task, config, db)

        log.status = "success"
        log.output = f"Task '{task.name}' executed successfully at {datetime.utcnow().isoformat()}"
        task.last_run_at = datetime.utcnow()

    except Exception as exc:
        logger.exception("Scheduled task id=%d failed", task.id)
        log.status = "failed"
        log.error = str(exc)

    log.completed_at = datetime.utcnow()
    db.commit()
    return log


def _run_workflow_instance_task(task: ScheduledTaskModel, config: Dict[str, Any], db: Session):
    """执行创建工作流实例任务。"""
    template_id = config.get("template_id")
    project_id = config.get("project_id")
    context = config.get("context", {})

    if not template_id or not project_id:
        raise ValueError("template_id and project_id are required for workflow_instance task")

    from app.api.workflow_config import instantiate_template
    from pydantic import BaseModel

    class Payload(BaseModel):
        project_id: str
        context: Dict[str, Any] = {}

    payload = Payload(project_id=project_id, context=context)
    result = instantiate_template(template_id, payload, db)
    logger.info(
        "Scheduled workflow instance created: %s for project %s",
        result.instance_id,
        project_id,
    )


def _run_system_task(task: ScheduledTaskModel, config: Dict[str, Any], db: Session):
    """执行系统任务。"""
    task_name = config.get("system_task_name", "unknown")
    logger.info("Running system task: %s", task_name)

    # 预留扩展点：根据 task_name 执行不同的系统任务
    if task_name == "cleanup_logs":
        logger.info("Cleanup logs task executed")
    elif task_name == "backup_database":
        logger.info("Backup database task executed")
    else:
        logger.info("Generic system task executed: %s", task_name)


def init_scheduler() -> TaskScheduler:
    """初始化并启动调度器，加载数据库中所有启用的任务。"""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()

    scheduler = TaskScheduler(_scheduler)
    scheduler.start()

    # 加载数据库中所有启用的任务
    db = next(get_db())
    try:
        tasks = db.query(ScheduledTaskModel).filter(ScheduledTaskModel.is_enabled == 1).all()
        for task in tasks:
            scheduler.add_task(task)
        logger.info("Loaded %d scheduled tasks from database", len(tasks))
    except Exception:
        logger.exception("Failed to load scheduled tasks from database")
    finally:
        db.close()

    return scheduler
