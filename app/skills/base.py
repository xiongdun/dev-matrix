"""技能基础模块。

定义了所有技能的抽象基类 BaseSkill，以及 SkillResult 和 SkillConfig 数据类。
提供技能执行、超时处理、健康检查和序列化等核心功能。

主要类：
    - SkillResult: 技能执行结果数据类。
    - SkillConfig: 技能配置数据类。
    - BaseSkill: 技能抽象基类，所有技能必须继承此类。

使用示例：
    ```python
    class MySkill(BaseSkill):
        name = "my_skill"
        description = "Does something useful"

        async def execute(self, context: Dict[str, Any]) -> SkillResult:
            return SkillResult(output="done")
    ```
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 技能执行默认超时时间（秒）
DEFAULT_SKILL_TIMEOUT = 30.0


@dataclass
class SkillResult:
    """技能执行结果数据类。

    Attributes:
        output: 执行输出，类型任意。
        metadata: 附加元数据字典。
        success: 是否执行成功。
        error: 错误信息，成功时为 None。
    """

    output: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


@dataclass
class SkillConfig:
    """技能配置数据类。

    Attributes:
        timeout: 执行超时时间（秒）。
        retry_count: 失败重试次数。
        parameters: 附加参数字典。
    """

    timeout: int = 30
    retry_count: int = 0
    parameters: Dict[str, Any] = field(default_factory=dict)


class BaseSkill(ABC):
    """技能抽象基类。

    所有技能必须继承此类并实现 execute 方法。
    提供超时执行、健康检查和序列化等通用功能。

    Attributes:
        name: 技能名称标识。
        description: 技能描述。
        config: 技能运行时配置。

    Example:
        ```python
        class MySkill(BaseSkill):
            name = "my_skill"
            description = "Does something useful"

            async def execute(self, context: Dict[str, Any]) -> SkillResult:
                return SkillResult(output="done")
        ```
    """

    name: str = "base"
    description: str = ""

    def __init__(self, config: Optional[SkillConfig] = None):
        """初始化技能。

        Args:
            config: 技能配置实例，未提供时使用默认配置。
        """
        self.config = config or SkillConfig()

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        """执行技能。

        子类必须实现此方法。

        Args:
            context: 包含输入数据和参数的上下文字典。

        Returns:
            SkillResult: 技能执行结果。

        Raises:
            NotImplementedError: 子类未覆盖此方法时抛出。
        """
        raise NotImplementedError

    async def execute_with_timeout(self, context: Dict[str, Any]) -> SkillResult:
        """带超时和异常处理的技能执行。

        包装 execute 方法，提供：
        - 超时保护（使用 config.timeout，默认 30s）
        - 异常捕获和日志记录
        - 失败时返回标准化错误结果

        Args:
            context: 包含输入数据和参数的上下文字典。

        Returns:
            SkillResult: 执行结果。失败时返回 success=False 并填充错误信息。
        """
        timeout = getattr(self.config, "timeout", None) or DEFAULT_SKILL_TIMEOUT
        try:
            return await asyncio.wait_for(self.execute(context), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(
                "Skill '%s' execution timed out after %.1fs",
                self.name,
                timeout,
            )
            return SkillResult(
                output=None,
                success=False,
                error=f"Skill '{self.name}' execution timed out after {timeout}s",
            )
        except Exception as exc:
            logger.exception("Skill '%s' execution failed", self.name)
            return SkillResult(
                output=None,
                success=False,
                error=f"Skill '{self.name}' execution failed: {exc}",
            )

    def health_check(self) -> bool:
        """检查技能是否健康并准备就绪。

        Returns:
            bool: 技能健康状态。
        """
        return True

    def to_dict(self) -> Dict[str, Any]:
        """将技能序列化为字典。

        Returns:
            Dict: 包含技能名称、描述和配置的字典。
        """
        return {
            "name": self.name,
            "description": self.description,
            "config": {
                "timeout": self.config.timeout,
                "retry_count": self.config.retry_count,
            },
        }
