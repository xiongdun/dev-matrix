"""项目状态机模块。

定义项目状态的合法集合、转换规则和守卫条件。
确保状态转换的一致性和可追溯性。

主要类：
    - ProjectStatus: 项目状态枚举。
    - StateMachine: 状态机，管理状态转换逻辑。
"""

from enum import Enum
from typing import List, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class ProjectStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    GENERATING_PRD = "generating_prd"
    DESIGNING = "designing"
    DEVELOPING = "developing"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"


TRANSITIONS: dict[str, Set[str]] = {
    ProjectStatus.PENDING: {ProjectStatus.ANALYZING, ProjectStatus.FAILED},
    ProjectStatus.ANALYZING: {ProjectStatus.AWAITING_APPROVAL, ProjectStatus.FAILED},
    ProjectStatus.AWAITING_APPROVAL: {ProjectStatus.APPROVED, ProjectStatus.REJECTED},
    ProjectStatus.APPROVED: {ProjectStatus.GENERATING_PRD, ProjectStatus.DESIGNING, ProjectStatus.DEVELOPING, ProjectStatus.TESTING, ProjectStatus.COMPLETED},
    ProjectStatus.REJECTED: {ProjectStatus.ANALYZING, ProjectStatus.AWAITING_APPROVAL},
    ProjectStatus.GENERATING_PRD: {ProjectStatus.AWAITING_APPROVAL, ProjectStatus.FAILED},
    ProjectStatus.DESIGNING: {ProjectStatus.AWAITING_APPROVAL, ProjectStatus.FAILED},
    ProjectStatus.DEVELOPING: {ProjectStatus.AWAITING_APPROVAL, ProjectStatus.FAILED},
    ProjectStatus.TESTING: {ProjectStatus.AWAITING_APPROVAL, ProjectStatus.COMPLETED, ProjectStatus.FAILED},
    ProjectStatus.COMPLETED: set(),
    ProjectStatus.FAILED: {ProjectStatus.PENDING, ProjectStatus.ROLLBACK},
    ProjectStatus.ROLLBACK: {ProjectStatus.AWAITING_APPROVAL, ProjectStatus.PENDING},
}

STAGE_STATUS_MAP = {
    "analyze_requirement": ProjectStatus.ANALYZING,
    "generate_prd": ProjectStatus.GENERATING_PRD,
    "design_architecture": ProjectStatus.DESIGNING,
    "develop_code": ProjectStatus.DEVELOPING,
    "execute_tests": ProjectStatus.TESTING,
}


class StateMachine:
    """项目状态机。

    管理项目状态转换，确保只有合法的转换才能执行。

    Example:
        sm = StateMachine()
        sm.transition("pending", "analyzing")  # OK
        sm.transition("pending", "completed")  # raises ValueError
    """

    @staticmethod
    def can_transition(from_status: str, to_status: str) -> bool:
        from_enum = ProjectStatus(from_status)
        to_enum = ProjectStatus(to_status)
        allowed = TRANSITIONS.get(from_enum, set())
        return to_enum in allowed

    @staticmethod
    def transition(from_status: str, to_status: str) -> str:
        if not StateMachine.can_transition(from_status, to_status):
            raise ValueError(f"Invalid transition: {from_status} -> {to_status}")
        logger.info("State transition: %s -> %s", from_status, to_status)
        return to_status

    @staticmethod
    def get_allowed_transitions(status: str) -> List[str]:
        from_enum = ProjectStatus(status)
        return [s.value for s in TRANSITIONS.get(from_enum, set())]

    @staticmethod
    def stage_to_status(stage_id: str) -> str:
        return STAGE_STATUS_MAP.get(stage_id, ProjectStatus.ANALYZING).value
