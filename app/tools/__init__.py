"""Agent 工具执行模块。

提供代码搜索（Read/Search）、文件编辑（Write/Edit）、命令执行（Bash）等工具，
供 Agent SDK 在工作台实时对话模式中调用。

主要工具：
    - Read: 读取文件内容
    - Search: 在代码库中搜索文本
    - Write: 写入/创建文件
    - Edit: 编辑文件（搜索替换）
    - Bash: 执行 shell 命令
"""

from .executor import ToolExecutor, execute_tool

__all__ = ["ToolExecutor", "execute_tool"]
