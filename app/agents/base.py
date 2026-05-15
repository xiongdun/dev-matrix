"""Agent 基础模块。

定义了所有 Agent 的抽象基类 BaseAgent，以及 Proposal 和 ValidationResult 数据类。
提供状态读写、技能组合与调用、提案生成和验证等核心功能。

主要类：
    - Proposal: Agent 提案数据类。
    - ValidationResult: 提案验证结果数据类。
    - BaseAgent: Agent 抽象基类，所有 Agent 必须继承此类。

使用示例：
    ```python
    class MyAgent(BaseAgent):
        name = "my_agent"
        description = "My custom agent"

        async def generate_proposal(self, project_id, context):
            # 实现提案生成逻辑
            return Proposal(agent_name=self.name, content="...")

        async def validate_output(self, project_id, proposal):
            # 实现验证逻辑
            return ValidationResult(is_valid=True)
    ```
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.llm.router import LLMRouter
from app.state.repository import StateRepository

logger = logging.getLogger(__name__)

# 技能执行默认超时时间（秒）
DEFAULT_SKILL_TIMEOUT = 30.0


@dataclass
class Proposal:
    """Agent 提案数据类。

    Attributes:
        agent_name: 生成提案的 Agent 名称。
        content: 提案内容文本。
        metadata: 附加元数据字典。
    """
    agent_name: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """提案验证结果数据类。

    Attributes:
        is_valid: 验证是否通过。
        errors: 错误信息列表。
        warnings: 警告信息列表。
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BaseAgent(ABC):
    """Agent 抽象基类。

    所有 Agent 必须继承此类并实现 generate_proposal 和 validate_output 方法。
    提供状态读写、技能组合与调用等通用功能。

    Attributes:
        name: Agent 名称标识。
        description: Agent 描述。
        llm_router: LLM 路由实例。
        state_repository: 状态仓库实例。
        _skills: 已组合的技能字典。

    Example:
        ```python
        agent = MyAgent(llm_router=router, state_repository=repo)
        agent.use_skill(CodeSearchSkill())
        proposal = await agent.generate_proposal("proj_1", {"prd": "..."})
        ```
    """

    name: str = "base"
    description: str = "Base agent"

    def __init__(
        self,
        llm_router: LLMRouter,
        state_repository: StateRepository,
    ):
        """初始化 Agent。

        Args:
            llm_router: LLM 路由实例，用于调用语言模型。
            state_repository: 状态仓库实例，用于读写项目状态。
        """
        self.llm_router = llm_router
        self.state_repository = state_repository
        self._skills: Dict[str, "BaseSkill"] = {}

    def read_state(self, project_id: str) -> Dict[str, Any]:
        """读取指定项目的当前状态。

        从状态仓库读取并解析 JSON 状态数据。

        Args:
            project_id: 项目 ID。

        Returns:
            Dict: 解析后的状态字典，状态不存在或为空时返回空字典。

        Raises:
            ValueError: JSON 解析失败时抛出。
        """
        state = self.state_repository.get_state(project_id)
        if state is None or not state.state_json:
            return {}
        try:
            return json.loads(state.state_json)
        except json.JSONDecodeError as exc:
            logger.error(
                "JSON decode error reading state for project '%s': %s",
                project_id,
                exc,
            )
            raise ValueError(
                f"Invalid JSON in state for project '{project_id}': {exc}"
            ) from exc

    def write_state(self, project_id: str, state_dict: Dict[str, Any], status: Optional[str] = None):
        """写入指定项目的状态。

        将字典序列化为 JSON 并保存到状态仓库。

        Args:
            project_id: 项目 ID。
            state_dict: 要保存的状态字典。
            status: 可选的状态字符串。

        Raises:
            ValueError: JSON 序列化失败时抛出。
        """
        try:
            state_json = json.dumps(state_dict, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            logger.error(
                "JSON serialization error writing state for project '%s': %s",
                project_id,
                exc,
            )
            raise ValueError(
                f"Failed to serialize state for project '{project_id}': {exc}"
            ) from exc
        self.state_repository.update_state(
            project_id=project_id,
            state_json=state_json,
            status=status,
        )

    @abstractmethod
    async def generate_proposal(self, project_id: str, context: Dict[str, Any]) -> Proposal:
        """生成提案。

        子类必须实现此方法以生成特定类型的提案。

        Args:
            project_id: 项目 ID。
            context: 上下文字典，包含生成提案所需的输入数据。

        Returns:
            Proposal: 生成的提案。
        """
        pass

    @abstractmethod
    async def validate_output(self, project_id: str, proposal: Proposal) -> ValidationResult:
        """验证提案输出。

        子类必须实现此方法以验证生成的提案。

        Args:
            project_id: 项目 ID。
            proposal: 要验证的提案。

        Returns:
            ValidationResult: 验证结果。
        """
        pass

    async def run(self, project_id: str, context: Dict[str, Any]) -> Proposal:
        """运行 Agent 的完整流程：生成提案并验证。

        Args:
            project_id: 项目 ID。
            context: 上下文字典。

        Returns:
            Proposal: 验证通过的提案。

        Raises:
            ValueError: 验证失败时抛出。
        """
        proposal = await self.generate_proposal(project_id, context)
        validation = await self.validate_output(project_id, proposal)
        if not validation.is_valid:
            raise ValueError(f"Validation failed: {validation.errors}")
        return proposal

    # ===== 技能组合 API =====

    def use_skill(self, skill: "BaseSkill") -> "BaseAgent":
        """将技能组合到当前 Agent，支持链式调用。

        Args:
            skill: 要组合的技能实例。

        Returns:
            BaseAgent: 返回自身以支持链式调用。
        """
        self._skills[skill.name] = skill
        return self

    def has_skill(self, name: str) -> bool:
        """检查 Agent 是否已组合指定技能。

        Args:
            name: 技能名称。

        Returns:
            bool: 是否已组合该技能。
        """
        return name in self._skills

    async def call_skill(self, name: str, context: Dict[str, Any]) -> "SkillResult":
        """按名称执行已组合的技能，带超时保护。

        Args:
            name: 技能名称。
            context: 执行上下文字典。

        Returns:
            SkillResult: 技能执行结果。

        Raises:
            ValueError: 技能未组合时抛出。
            TimeoutError: 执行超时时抛出。
        """
        skill = self._skills.get(name)
        if skill is None:
            raise ValueError(f"Skill '{name}' not composed into agent '{self.name}'")

        timeout = getattr(skill.config, "timeout", None) or DEFAULT_SKILL_TIMEOUT
        try:
            return await asyncio.wait_for(skill.execute(context), timeout=timeout)
        except asyncio.TimeoutError as exc:
            logger.error(
                "Skill '%s' execution timed out after %.1fs on agent '%s'",
                name,
                timeout,
                self.name,
            )
            raise TimeoutError(
                f"Skill '{name}' execution timed out after {timeout}s"
            ) from exc
        except Exception as exc:
            logger.exception(
                "Skill '%s' execution failed on agent '%s'",
                name,
                self.name,
            )
            raise

    def list_skills(self) -> List[str]:
        """列出当前 Agent 已组合的所有技能名称。

        Returns:
            List[str]: 技能名称列表。
        """
        return list(self._skills.keys())
