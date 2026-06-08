"""Claude Code SDK 适配器。

基于 claude-agent-sdk (Claude Code CLI) 实现 BaseSDK 接口。
"""

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from app.sdk.base import BaseSDK, SDKMessage, SDKRegistry, SDKResponse

logger = logging.getLogger(__name__)

try:
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        TextBlock,
        ToolResultBlock,
        ToolUseBlock,
    )
    from claude_agent_sdk import query as sdk_query

    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False
    logger.warning("claude-agent-sdk not installed")


@SDKRegistry.register("claude_code")
class ClaudeCodeSDK(BaseSDK):
    """Claude Code SDK 适配器。"""

    name = "claude_code"
    display_name = "Claude Code"
    description = "基于 Claude Code CLI 的 Agent SDK，支持文件读写、代码执行等工具"

    def __init__(self, max_turns: int = 20, sandbox_enabled: bool = True):
        self.max_turns = max_turns
        self.sandbox_enabled = sandbox_enabled

    def is_available(self) -> bool:
        return CLAUDE_SDK_AVAILABLE

    async def chat(
        self,
        message: str,
        system_prompt: str,
        history: list[dict[str, str]] | None = None,
        **kwargs,
    ) -> SDKResponse:
        """使用 Claude Code SDK 发送消息。"""
        if not CLAUDE_SDK_AVAILABLE:
            return SDKResponse(
                content="",
                success=False,
                error="claude-agent-sdk not installed",
            )

        max_turns = kwargs.get("max_turns", self.max_turns)
        sandbox: Any = None
        if self.sandbox_enabled:
            sandbox = {
                "enabled": True,
                "autoAllowBashIfSandboxed": True,
            }
            logger.info("Sandbox enabled for Claude Code SDK")

        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            max_turns=max_turns,
            continue_conversation=False,
            sandbox=sandbox,
        )

        ai_content = ""
        tool_calls: list[dict] = []

        try:
            async for msg in sdk_query(prompt=message, options=options):
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            ai_content += block.text
                        elif isinstance(block, ToolUseBlock):
                            tool_calls.append({
                                "name": block.name,
                                "input": getattr(block, "input", {}) or {},
                            })
                        elif isinstance(block, ToolResultBlock):
                            result = getattr(block, "content", getattr(block, "output", ""))
                            if tool_calls:
                                tool_calls[-1]["output"] = result

            return SDKResponse(
                content=ai_content,
                tool_calls=tool_calls,
                metadata={"sdk": self.name, "max_turns": max_turns},
            )
        except Exception as e:
            logger.exception("Claude Code SDK error")
            return SDKResponse(content="", success=False, error=str(e))

    async def chat_stream(
        self,
        message: str,
        system_prompt: str,
        history: list[dict[str, str]] | None = None,
        **kwargs,
    ) -> AsyncIterator[SDKMessage]:
        """Claude Code SDK 流式输出（非真正流式，整块返回）。"""
        response = await self.chat(message, system_prompt, history, **kwargs)

        if response.tool_calls:
            for tc in response.tool_calls:
                yield SDKMessage(
                    type="tool_call",
                    content=json.dumps(tc, ensure_ascii=False),
                    metadata={"name": tc.get("name", ""), "input": tc.get("input", {})},
                )

        if response.content:
            yield SDKMessage(type="text", content=response.content)

        if response.error:
            yield SDKMessage(type="error", content=response.error)

        yield SDKMessage(type="done", content="")
