"""审计日志模块。

提供审计日志记录功能，支持文件和数据库两种输出方式。

主要类/函数：
    - AuditLog: 审计日志数据类。
    - AuditLogger: 审计日志记录器。
    - log_audit: 便捷函数，记录审计日志。

使用示例：
    ```python
    from app.utils.audit import AuditLogger, log_audit

    logger = AuditLogger()
    logger.log("user_login", {"user_id": "123"})

    # 或使用便捷函数
    log_audit("user_login", {"user_id": "123"})
    ```
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class AuditLog:
    """审计日志数据类。

    Attributes:
        action: 操作名称。
        user_id: 用户 ID，可选。
        project_id: 项目 ID，可选。
        details: 详细信息字典。
        timestamp: 日志时间戳，默认 UTC 当前时间。
        ip_address: IP 地址，可选。
        user_agent: 用户代理，可选。
    """

    action: str
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。

        Returns:
            Dict: 审计日志字典。
        """
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        """序列化为 JSON 字符串。

        Returns:
            str: JSON 字符串。
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditLogger:
    """审计日志记录器。

    支持文件和数据库两种输出方式。

    Attributes:
        log_file: 日志文件路径。
        use_db: 是否使用数据库存储。

    Example:
        ```python
        logger = AuditLogger("audit.log")
        logger.log("user_login", {"user_id": "123"})
        ```
    """

    def __init__(self, log_file: Optional[str] = None, use_db: bool = False):
        """初始化审计日志记录器。

        Args:
            log_file: 日志文件路径，默认使用 "logs/audit.log"。
            use_db: 是否使用数据库存储，默认 False。
        """
        self.log_file = Path(log_file) if log_file else Path("logs/audit.log")
        self.use_db = use_db
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        """确保日志目录存在。"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> AuditLog:
        """记录审计日志。

        Args:
            action: 操作名称。
            details: 详细信息字典。
            user_id: 用户 ID。
            project_id: 项目 ID。

        Returns:
            AuditLog: 审计日志实例。
        """
        audit_log = AuditLog(
            action=action,
            user_id=user_id,
            project_id=project_id,
            details=details or {},
        )

        # 写入文件
        self._write_to_file(audit_log)

        # 可选写入数据库
        if self.use_db:
            self._write_to_db(audit_log)

        return audit_log

    def _write_to_file(self, audit_log: AuditLog):
        """写入审计日志到文件。

        Args:
            audit_log: 审计日志实例。
        """
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(audit_log.to_json() + "\n")
        except Exception as exc:
            logger.error("Failed to write audit log to file: %s", exc)

    def _write_to_db(self, audit_log: AuditLog):
        """写入审计日志到数据库。

        当前为占位实现，实际应使用数据库模型存储。

        Args:
            audit_log: 审计日志实例。
        """
        # 实际实现应写入数据库
        pass

    def get_logs(
        self,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """查询审计日志。

        从日志文件中筛选符合条件的日志。

        Args:
            action: 按操作名称筛选。
            user_id: 按用户 ID 筛选。
            project_id: 按项目 ID 筛选。
            limit: 最大返回数量。

        Returns:
            list: 审计日志列表。
        """
        logs = []
        if not self.log_file.exists():
            return logs

        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if len(logs) >= limit:
                        break
                    try:
                        data = json.loads(line.strip())
                        if action and data.get("action") != action:
                            continue
                        if user_id and data.get("user_id") != user_id:
                            continue
                        if project_id and data.get("project_id") != project_id:
                            continue
                        logs.append(data)
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:
            logger.error("Failed to read audit logs: %s", exc)

        return logs


# 全局审计日志记录器实例
_default_logger = AuditLogger()


def log_audit(
    action: str,
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
) -> AuditLog:
    """便捷函数，使用默认记录器记录审计日志。

    Args:
        action: 操作名称。
        details: 详细信息字典。
        user_id: 用户 ID。
        project_id: 项目 ID。

    Returns:
        AuditLog: 审计日志实例。
    """
    return _default_logger.log(action, details, user_id, project_id)
