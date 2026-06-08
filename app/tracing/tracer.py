"""执行追踪系统模块。

支持：
- Agent 调用链路追踪
- Token 消耗统计
- 性能指标采集
- 错误追踪
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TraceSpan:
    """追踪跨度。"""
    id: str = ""
    trace_id: str = ""
    parent_id: str | None = None
    name: str = ""
    agent_role: str = ""
    sdk_name: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    status: str = "ok"  # ok / error / timeout
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    token_usage: dict[str, int] = field(default_factory=dict)  # input/output/total
    children: list = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def finish(self, status: str = "ok", error: str | None = None):
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "agent_role": self.agent_role,
            "sdk_name": self.sdk_name,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "error": self.error,
            "token_usage": self.token_usage,
            "metadata": self.metadata,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class Trace:
    """完整追踪。"""
    id: str = ""
    project_id: str = ""
    task_id: int = 0
    user_id: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0
    spans: list[TraceSpan] = field(default_factory=list)
    status: str = "running"

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def finish(self):
        self.completed_at = datetime.now(timezone.utc)
        if self.spans:
            self.duration_ms = sum(s.duration_ms for s in self.spans)
            self.total_tokens = sum(
                s.token_usage.get("total", 0) for s in self.spans
            )
        self.status = "completed" if all(s.status == "ok" for s in self.spans) else "failed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": round(self.duration_ms, 2),
            "total_tokens": self.total_tokens,
            "status": self.status,
            "spans": [s.to_dict() for s in self.spans],
        }


class ExecutionTracer:
    """执行追踪器。"""

    def __init__(self, max_traces: int = 100):
        self._traces: dict[str, Trace] = {}
        self._max_traces = max_traces
        self._active_spans: dict[str, TraceSpan] = {}

    def start_trace(
        self,
        project_id: str = "",
        task_id: int = 0,
        user_id: int = 0,
    ) -> Trace:
        """开始新的追踪。"""
        trace = Trace(
            project_id=project_id,
            task_id=task_id,
            user_id=user_id,
        )
        self._traces[trace.id] = trace

        # 清理旧追踪
        if len(self._traces) > self._max_traces:
            oldest = sorted(self._traces.keys())[:len(self._traces) - self._max_traces]
            for k in oldest:
                del self._traces[k]

        logger.info("Trace started: %s", trace.id)
        return trace

    @asynccontextmanager
    async def span(
        self,
        trace: Trace,
        name: str,
        agent_role: str = "",
        sdk_name: str = "",
        parent_span: TraceSpan | None = None,
    ):
        """创建追踪跨度（上下文管理器）。"""
        span = TraceSpan(
            trace_id=trace.id,
            parent_id=parent_span.id if parent_span else None,
            name=name,
            agent_role=agent_role,
            sdk_name=sdk_name,
            start_time=time.time(),
        )

        if parent_span:
            parent_span.children.append(span)
        else:
            trace.spans.append(span)

        self._active_spans[span.id] = span

        try:
            yield span
            span.finish(status="ok")
        except Exception as e:
            span.finish(status="error", error=str(e))
            raise
        finally:
            self._active_spans.pop(span.id, None)

    def record_tokens(
        self,
        span: TraceSpan,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """记录 token 消耗。"""
        span.token_usage = {
            "input": input_tokens,
            "output": output_tokens,
            "total": input_tokens + output_tokens,
        }

    def get_trace(self, trace_id: str) -> Trace | None:
        return self._traces.get(trace_id)

    def get_recent_traces(self, limit: int = 20) -> list[Trace]:
        traces = sorted(
            self._traces.values(),
            key=lambda t: t.started_at,
            reverse=True,
        )
        return traces[:limit]

    def get_stats(self) -> dict[str, Any]:
        all_spans = []
        for trace in self._traces.values():
            all_spans.extend(trace.spans)

        if not all_spans:
            return {"total_traces": len(self._traces), "total_spans": 0}

        durations = [s.duration_ms for s in all_spans if s.duration_ms > 0]
        total_tokens = sum(s.token_usage.get("total", 0) for s in all_spans)

        return {
            "total_traces": len(self._traces),
            "total_spans": len(all_spans),
            "avg_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0,
            "total_tokens": total_tokens,
            "error_count": sum(1 for s in all_spans if s.status == "error"),
        }


# 全局追踪器
tracer = ExecutionTracer()
