"""Agent 生命周期管理模块。

支持：
- Agent 实例创建/暂停/恢复/销毁
- 健康监控（心跳机制）
- 资源限制（Token 预算、时间限制、并发控制）
- Agent 运行状态管理
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    """Agent 运行状态。"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"
    DESTROYED = "destroyed"


class AgentHealth(str, Enum):
    """Agent 健康状态。"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ResourceLimits:
    """资源限制。"""
    max_tokens: int = 100000        # 最大 token 消耗
    max_duration_seconds: int = 3600  # 最大运行时间（秒）
    max_concurrent_tasks: int = 3     # 最大并发任务数
    max_retries: int = 3              # 最大重试次数
    cooldown_seconds: int = 10        # 任务间冷却时间


@dataclass
class ResourceUsage:
    """资源使用情况。"""
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost: float = 0.0
    task_count: int = 0
    error_count: int = 0
    start_time: float = 0.0
    last_active: float = 0.0


@dataclass
class AgentInstance:
    """Agent 实例。"""
    id: str = ""
    agent_role: str = ""
    state: AgentState = AgentState.IDLE
    health: AgentHealth = AgentHealth.UNKNOWN
    limits: ResourceLimits = field(default_factory=ResourceLimits)
    usage: ResourceUsage = field(default_factory=ResourceUsage)
    last_heartbeat: datetime | None = None
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not self.id:
            self.id = f"{self.agent_role}-{uuid.uuid4().hex[:6]}"

    def is_available(self) -> bool:
        """检查 Agent 是否可接受新任务。"""
        if self.state != AgentState.RUNNING:
            return False
        if self.usage.task_count >= self.limits.max_concurrent_tasks:
            return False
        if self.usage.total_tokens >= self.limits.max_tokens:
            return False
        return True

    def check_health(self, timeout_seconds: int = 60) -> AgentHealth:
        """检查健康状态。"""
        if self.state == AgentState.ERROR:
            return AgentHealth.UNHEALTHY
        if not self.last_heartbeat:
            return AgentHealth.UNKNOWN
        elapsed = (datetime.now(timezone.utc) - self.last_heartbeat).total_seconds()
        if elapsed > timeout_seconds * 2:
            return AgentHealth.UNHEALTHY
        if elapsed > timeout_seconds:
            return AgentHealth.DEGRADED
        return AgentHealth.HEALTHY

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_role": self.agent_role,
            "state": self.state.value,
            "health": self.health.value,
            "limits": {
                "max_tokens": self.limits.max_tokens,
                "max_duration_seconds": self.limits.max_duration_seconds,
                "max_concurrent_tasks": self.limits.max_concurrent_tasks,
            },
            "usage": {
                "total_tokens": self.usage.total_tokens,
                "total_cost": round(self.usage.total_cost, 4),
                "task_count": self.usage.task_count,
                "error_count": self.usage.error_count,
            },
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
        }


class AgentLifecycleManager:
    """Agent 生命周期管理器。"""

    def __init__(self):
        self._instances: dict[str, AgentInstance] = {}
        self._health_check_interval = 30  # 秒
        self._health_check_task: asyncio.Task | None = None

    def create_instance(
        self,
        agent_role: str,
        limits: ResourceLimits | None = None,
    ) -> AgentInstance:
        """创建 Agent 实例。"""
        instance = AgentInstance(
            agent_role=agent_role,
            limits=limits or ResourceLimits(),
            usage=ResourceUsage(start_time=time.time()),
        )
        self._instances[instance.id] = instance
        logger.info("Agent instance created: %s (%s)", instance.id, agent_role)
        return instance

    async def start(self, instance_id: str) -> bool:
        """启动 Agent。"""
        instance = self._instances.get(instance_id)
        if not instance:
            return False

        if instance.state in (AgentState.RUNNING, AgentState.STARTING):
            return True

        instance.state = AgentState.STARTING
        try:
            # 这里可以添加实际的 Agent 启动逻辑
            instance.state = AgentState.RUNNING
            instance.health = AgentHealth.HEALTHY
            instance.last_heartbeat = datetime.now(timezone.utc)
            logger.info("Agent started: %s", instance_id)
            return True
        except Exception as e:
            instance.state = AgentState.ERROR
            instance.error_message = str(e)
            logger.exception("Failed to start agent: %s", instance_id)
            return False

    async def pause(self, instance_id: str) -> bool:
        """暂停 Agent。"""
        instance = self._instances.get(instance_id)
        if not instance or instance.state != AgentState.RUNNING:
            return False

        instance.state = AgentState.PAUSED
        logger.info("Agent paused: %s", instance_id)
        return True

    async def resume(self, instance_id: str) -> bool:
        """恢复 Agent。"""
        instance = self._instances.get(instance_id)
        if not instance or instance.state != AgentState.PAUSED:
            return False

        instance.state = AgentState.RUNNING
        logger.info("Agent resumed: %s", instance_id)
        return True

    async def destroy(self, instance_id: str) -> bool:
        """销毁 Agent。"""
        instance = self._instances.get(instance_id)
        if not instance:
            return False

        instance.state = AgentState.DESTROYED
        logger.info("Agent destroyed: %s", instance_id)
        return True

    def get_instance(self, instance_id: str) -> AgentInstance | None:
        return self._instances.get(instance_id)

    def list_instances(
        self,
        agent_role: str | None = None,
        state: AgentState | None = None,
    ) -> list[AgentInstance]:
        """列出 Agent 实例。"""
        instances = list(self._instances.values())
        if agent_role:
            instances = [i for i in instances if i.agent_role == agent_role]
        if state:
            instances = [i for i in instances if i.state == state]
        return instances

    def record_token_usage(
        self,
        instance_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
    ) -> None:
        """记录 token 使用。"""
        instance = self._instances.get(instance_id)
        if not instance:
            return

        instance.usage.input_tokens += input_tokens
        instance.usage.output_tokens += output_tokens
        instance.usage.total_tokens += input_tokens + output_tokens
        instance.usage.total_cost += cost
        instance.usage.last_active = time.time()
        instance.last_heartbeat = datetime.now(timezone.utc)

    def record_task_start(self, instance_id: str) -> None:
        """记录任务开始。"""
        instance = self._instances.get(instance_id)
        if instance:
            instance.usage.task_count += 1

    def record_task_end(self, instance_id: str, success: bool = True) -> None:
        """记录任务结束。"""
        instance = self._instances.get(instance_id)
        if instance:
            instance.usage.task_count = max(0, instance.usage.task_count - 1)
            if not success:
                instance.usage.error_count += 1

    def heartbeat(self, instance_id: str) -> None:
        """更新心跳。"""
        instance = self._instances.get(instance_id)
        if instance:
            instance.last_heartbeat = datetime.now(timezone.utc)

    async def start_health_checks(self) -> None:
        """启动健康检查后台任务。"""
        async def _check_loop():
            while True:
                await asyncio.sleep(self._health_check_interval)
                for instance in self._instances.values():
                    if instance.state == AgentState.RUNNING:
                        instance.health = instance.check_health()
                        if instance.health == AgentHealth.UNHEALTHY:
                            logger.warning("Agent %s is unhealthy", instance.id)

        self._health_check_task = asyncio.create_task(_check_loop())
        logger.info("Health check started (interval=%ds)", self._health_check_interval)

    def stop_health_checks(self) -> None:
        """停止健康检查。"""
        if self._health_check_task:
            self._health_check_task.cancel()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息。"""
        instances = list(self._instances.values())
        return {
            "total_instances": len(instances),
            "by_state": {s.value: sum(1 for i in instances if i.state == s) for s in AgentState},
            "by_health": {h.value: sum(1 for i in instances if i.health == h) for h in AgentHealth},
            "total_tokens": sum(i.usage.total_tokens for i in instances),
            "total_cost": round(sum(i.usage.total_cost for i in instances), 4),
            "total_tasks": sum(i.usage.task_count for i in instances),
        }


# 全局生命周期管理器
lifecycle_manager = AgentLifecycleManager()
