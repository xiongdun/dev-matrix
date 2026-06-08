"""可观测性模块。

支持：
- Token 消耗统计
- 性能指标采集
- 成本分析
- Dashboard 数据聚合
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """指标数据点。"""
    timestamp: datetime
    value: float
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class TokenMetrics:
    """Token 消耗指标。"""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    by_agent: dict[str, dict[str, Any]] = field(default_factory=dict)
    by_sdk: dict[str, dict[str, Any]] = field(default_factory=dict)
    by_model: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """性能指标。"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    response_times: list[float] = field(default_factory=list)


class MetricsCollector:
    """指标收集器。"""

    def __init__(self, max_points: int = 10000):
        self._token_metrics = TokenMetrics()
        self._performance = PerformanceMetrics()
        self._response_times: list[float] = []
        self._max_points = max_points
        self._hourly_tokens: dict[str, int] = defaultdict(int)
        self._daily_costs: dict[str, float] = defaultdict(float)

    def record_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        cost: float = 0.0,
        agent_role: str = "",
        sdk_name: str = "",
        model: str = "",
    ) -> None:
        """记录 token 使用。"""
        self._token_metrics.total_input_tokens += input_tokens
        self._token_metrics.total_output_tokens += output_tokens
        self._token_metrics.total_tokens += input_tokens + output_tokens
        self._token_metrics.total_cost += cost

        # 按 Agent 统计
        if agent_role:
            if agent_role not in self._token_metrics.by_agent:
                self._token_metrics.by_agent[agent_role] = {"tokens": 0, "cost": 0.0}
            self._token_metrics.by_agent[agent_role]["tokens"] += input_tokens + output_tokens
            self._token_metrics.by_agent[agent_role]["cost"] += cost

        # 按 SDK 统计
        if sdk_name:
            if sdk_name not in self._token_metrics.by_sdk:
                self._token_metrics.by_sdk[sdk_name] = {"tokens": 0, "cost": 0.0}
            self._token_metrics.by_sdk[sdk_name]["tokens"] += input_tokens + output_tokens
            self._token_metrics.by_sdk[sdk_name]["cost"] += cost

        # 按模型统计
        if model:
            if model not in self._token_metrics.by_model:
                self._token_metrics.by_model[model] = {"tokens": 0, "cost": 0.0}
            self._token_metrics.by_model[model]["tokens"] += input_tokens + output_tokens
            self._token_metrics.by_model[model]["cost"] += cost

        # 按小时统计
        hour_key = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:00")
        self._hourly_tokens[hour_key] += input_tokens + output_tokens

        # 按天统计成本
        day_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._daily_costs[day_key] += cost

    def record_request(
        self,
        duration_ms: float,
        success: bool = True,
    ) -> None:
        """记录请求性能。"""
        self._performance.total_requests += 1
        if success:
            self._performance.successful_requests += 1
        else:
            self._performance.failed_requests += 1

        self._response_times.append(duration_ms)
        if len(self._response_times) > self._max_points:
            self._response_times = self._response_times[-self._max_points:]

        # 计算百分位数
        if self._response_times:
            sorted_times = sorted(self._response_times)
            self._performance.avg_response_time_ms = sum(sorted_times) / len(sorted_times)
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)
            self._performance.p95_response_time_ms = sorted_times[min(p95_idx, len(sorted_times) - 1)]
            self._performance.p99_response_time_ms = sorted_times[min(p99_idx, len(sorted_times) - 1)]

    def get_token_metrics(self) -> TokenMetrics:
        return self._token_metrics

    def get_performance_metrics(self) -> PerformanceMetrics:
        return self._performance

    def get_hourly_tokens(self, hours: int = 24) -> dict[str, int]:
        """获取最近 N 小时的 token 使用。"""
        return dict(sorted(self._hourly_tokens.items())[-hours:])

    def get_daily_costs(self, days: int = 7) -> dict[str, float]:
        """获取最近 N 天的成本。"""
        return dict(sorted(self._daily_costs.items())[-days:])

    def get_dashboard_data(self) -> dict[str, Any]:
        """获取 Dashboard 数据。"""
        return {
            "tokens": {
                "total": self._token_metrics.total_tokens,
                "input": self._token_metrics.total_input_tokens,
                "output": self._token_metrics.total_output_tokens,
                "cost": round(self._token_metrics.total_cost, 4),
                "by_agent": self._token_metrics.by_agent,
                "by_sdk": self._token_metrics.by_sdk,
                "by_model": self._token_metrics.by_model,
            },
            "performance": {
                "total_requests": self._performance.total_requests,
                "success_rate": round(
                    self._performance.successful_requests / max(self._performance.total_requests, 1) * 100, 1
                ),
                "avg_response_ms": round(self._performance.avg_response_time_ms, 2),
                "p95_response_ms": round(self._performance.p95_response_time_ms, 2),
                "p99_response_ms": round(self._performance.p99_response_time_ms, 2),
            },
            "hourly_tokens": self.get_hourly_tokens(),
            "daily_costs": self.get_daily_costs(),
        }


# 全局指标收集器
metrics = MetricsCollector()
