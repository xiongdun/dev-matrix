"""Agent 基础模块。

定义了所有 Agent 的抽象基类 BaseAgent，以及 Proposal 和 ValidationResult 数据类。
提供状态读写、技能组合与调用、提案生成和验证等核心功能。

新增 Claude Agent SDK 集成：
    - Agent 内部执行流程重构为 SDK 风格的状态机
    - 支持工具调用（Read/Write/Edit/Bash 等）
    - 支持自定义工具和 Hooks

主要类：
    - Proposal: Agent 提案数据类。
    - ValidationResult: 提案验证结果数据类。
    - BaseAgent: Agent 抽象基类，所有 Agent 必须继承此类。

使用示例：
    ```python
    class MyAgent(BaseAgent):
        name = "my_agent"
        description = "My custom agent"
        system_prompt = "You are a helpful assistant..."

        async def generate_proposal(self, project_id, context):
            # SDK 会自动处理工具调用和状态管理
            return await self.sdk_query(
                prompt="Generate proposal...",
                options=ClaudeAgentOptions(max_turns=3)
            )
    ```
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from app.llm.router import LLMRouter
from app.state.repository import StateRepository

logger = logging.getLogger(__name__)

# 技能执行默认超时时间（秒）
DEFAULT_SKILL_TIMEOUT = 30.0

if TYPE_CHECKING:
    from app.skills.base import BaseSkill, SkillResult

# Claude Agent SDK 可选导入
try:
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        TextBlock,
        ToolResultBlock,
        ToolUseBlock,
    )
    from claude_agent_sdk import (
        query as sdk_query,
    )

    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False
    logger.warning("claude-agent-sdk not installed. Agent will fall back to LLMRouter.")


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
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """提案验证结果数据类。

    Attributes:
        is_valid: 验证是否通过。
        errors: 错误信息列表。
        warnings: 警告信息列表。
    """

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class BaseAgent(ABC):
    """Agent 抽象基类。

    所有 Agent 必须继承此类并实现 generate_proposal 和 validate_output 方法。
    提供状态读写、技能组合与调用等通用功能。

    新增 SDK 集成后，Agent 内部执行流程变为：
        1. generate_proposal: 使用 SDK query() 或 ClaudeSDKClient 与 Claude 交互
        2. SDK 自动处理工具调用（Read/Write/Edit/Bash 等）
        3. validate_output: 验证提案输出

    Attributes:
        name: Agent 名称标识。
        description: Agent 描述。
        system_prompt: Agent 的系统提示词（用于 SDK）。
        llm_router: LLM 路由实例（兼容模式）。
        state_repository: 状态仓库实例。
        _skills: 已组合的技能字典。
        _sdk_options: SDK 配置选项。

    Example:
        ```python
        agent = MyAgent(llm_router=router, state_repository=repo)
        agent.use_skill(CodeSearchSkill())
        proposal = await agent.generate_proposal("proj_1", {"prd": "..."})
        ```
    """

    name: str = "base"
    description: str = "Base agent"
    system_prompt: str = ""

    def __init__(
        self,
        llm_router: LLMRouter,
        state_repository: StateRepository,
    ):
        """初始化 Agent。

        Args:
            llm_router: LLM 路由实例，用于兼容模式（SDK 不可用时）。
            state_repository: 状态仓库实例，用于读写项目状态。
        """
        self.llm_router = llm_router
        self.state_repository = state_repository
        self._skills: dict[str, BaseSkill] = {}
        self._sdk_options: ClaudeAgentOptions | None = None

    def _build_sdk_options(self, **kwargs) -> Optional["ClaudeAgentOptions"]:
        """构建 SDK 配置选项。

        Args:
            **kwargs: 覆盖默认配置的参数。

        Returns:
            ClaudeAgentOptions 实例，或 None（SDK 不可用时）。
        """
        if not CLAUDE_SDK_AVAILABLE:
            return None

        options_dict = {
            "system_prompt": self.system_prompt
            or f"You are a {self.name} agent. {self.description}",
            "max_turns": kwargs.get("max_turns", 5),
        }

        # 允许调用方覆盖配置
        options_dict.update(kwargs)

        return ClaudeAgentOptions(**options_dict)

    async def sdk_query(
        self,
        prompt: str,
        options: Optional["ClaudeAgentOptions"] = None,
        **option_kwargs,
    ) -> str:
        """使用 Claude Agent SDK 查询。

        这是 Agent 与 Claude 交互的主要方式。SDK 会自动处理工具调用和状态管理。

        Args:
            prompt: 用户提示词。
            options: SDK 配置选项（可选，默认使用 _build_sdk_options 生成）。
            **option_kwargs: 覆盖默认配置的参数。

        Returns:
            Claude 的回复文本。

        Raises:
            RuntimeError: SDK 不可用时抛出。
        """
        if not CLAUDE_SDK_AVAILABLE:
            raise RuntimeError(
                "claude-agent-sdk is not installed. Install it with: pip install claude-agent-sdk"
            )

        if options is None:
            options = self._build_sdk_options(**option_kwargs)

        response_text = ""
        async for message in sdk_query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text
                    elif isinstance(block, ToolUseBlock):
                        # 记录工具调用
                        logger.info(
                            "Agent '%s' using tool: %s",
                            self.name,
                            block.name,
                        )
                    elif isinstance(block, ToolResultBlock):
                        # 记录工具结果
                        logger.info(
                            "Agent '%s' tool result: %s",
                            self.name,
                            getattr(block, "content", getattr(block, "output", "")),
                        )
            else:
                # 其他消息类型（如 UserMessage, SystemMessage）
                logger.debug("Agent '%s' received message: %s", self.name, message)

        return response_text

    async def sdk_query_with_tools(
        self,
        prompt: str,
        allowed_tools: list[str],
        options: Optional["ClaudeAgentOptions"] = None,
        **option_kwargs,
    ) -> str:
        """使用 Claude Agent SDK 查询，并指定允许使用的工具。

        Args:
            prompt: 用户提示词。
            allowed_tools: 允许使用的工具列表（如 ["Read", "Write", "Bash"]）。
            options: SDK 配置选项（可选）。
            **option_kwargs: 覆盖默认配置的参数。

        Returns:
            Claude 的回复文本。
        """
        if not CLAUDE_SDK_AVAILABLE:
            raise RuntimeError("claude-agent-sdk is not installed.")

        if options is None:
            options = self._build_sdk_options(**option_kwargs)

        # 设置允许的工具
        if options is not None:
            options.allowed_tools = allowed_tools  # type: ignore[union-attr]

        return await self.sdk_query(prompt=prompt, options=options)

    def read_state(self, project_id: str) -> dict[str, Any]:
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
        state_json_val = str(state.state_json)
        try:
            return json.loads(state_json_val)
        except json.JSONDecodeError as exc:
            logger.error(
                "JSON decode error reading state for project '%s': %s",
                project_id,
                exc,
            )
            raise ValueError(f"Invalid JSON in state for project '{project_id}': {exc}") from exc

    def write_state(self, project_id: str, state_dict: dict[str, Any], status: str | None = None):
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
    async def generate_proposal(self, project_id: str, context: dict[str, Any]) -> Proposal:
        """生成提案。

        子类必须实现此方法以生成特定类型的提案。
        推荐使用 self.sdk_query() 与 Claude 交互。

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

    async def run(self, project_id: str, context: dict[str, Any]) -> Proposal:
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

    def remove_skill(self, skill_name: str) -> bool:
        """移除已组合的技能。

        Args:
            skill_name: 技能名称。

        Returns:
            bool: 是否成功移除。
        """
        if skill_name in self._skills:
            del self._skills[skill_name]
            return True
        return False

    async def call_skill(self, name: str, context: dict[str, Any]) -> "SkillResult":
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
            raise TimeoutError(f"Skill '{name}' execution timed out after {timeout}s") from exc
        except Exception:
            logger.exception(
                "Skill '%s' execution failed on agent '%s'",
                name,
                self.name,
            )
            raise

    def list_skills(self) -> list[str]:
        """列出当前 Agent 已组合的所有技能名称。

        Returns:
            List[str]: 技能名称列表。
        """
        return list(self._skills.keys())
