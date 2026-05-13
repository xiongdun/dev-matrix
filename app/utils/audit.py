import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class AuditLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent:
    def __init__(
        self,
        event_type: str,
        actor: str,
        resource: str,
        action: str,
        level: AuditLevel = AuditLevel.INFO,
        details: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
    ):
        self.event_type = event_type
        self.actor = actor
        self.resource = resource
        self.action = action
        self.level = level
        self.details = details or {}
        self.project_id = project_id
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "actor": self.actor,
            "resource": self.resource,
            "action": self.action,
            "level": self.level.value,
            "details": self.details,
            "project_id": self.project_id,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditLogger:
    def __init__(self, name: str = "audit"):
        self.logger = logging.getLogger(name)
        self._handlers: list = []

    def add_handler(self, handler: logging.Handler) -> None:
        self.logger.addHandler(handler)
        self._handlers.append(handler)

    def log(
        self,
        event_type: str,
        actor: str,
        resource: str,
        action: str,
        level: AuditLevel = AuditLevel.INFO,
        details: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_type=event_type,
            actor=actor,
            resource=resource,
            action=action,
            level=level,
            details=details,
            project_id=project_id,
        )

        log_method = {
            AuditLevel.INFO: self.logger.info,
            AuditLevel.WARNING: self.logger.warning,
            AuditLevel.ERROR: self.logger.error,
            AuditLevel.CRITICAL: self.logger.critical,
        }.get(level, self.logger.info)

        log_method(event.to_json())
        return event

    def log_agent_action(
        self,
        agent_name: str,
        action: str,
        project_id: str,
        details: Optional[Dict[str, Any]] = None,
        level: AuditLevel = AuditLevel.INFO,
    ) -> AuditEvent:
        return self.log(
            event_type="agent_action",
            actor=agent_name,
            resource=f"project:{project_id}",
            action=action,
            level=level,
            details=details,
            project_id=project_id,
        )

    def log_approval(
        self,
        approver: str,
        decision: str,
        project_id: str,
        stage: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        return self.log(
            event_type="human_approval",
            actor=approver,
            resource=f"project:{project_id}",
            action=f"{decision}:{stage}",
            level=AuditLevel.INFO,
            details=details,
            project_id=project_id,
        )

    def log_state_change(
        self,
        project_id: str,
        from_status: str,
        to_status: str,
        triggered_by: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        return self.log(
            event_type="state_change",
            actor=triggered_by,
            resource=f"project:{project_id}",
            action=f"{from_status}->{to_status}",
            level=AuditLevel.INFO,
            details=details,
            project_id=project_id,
        )
