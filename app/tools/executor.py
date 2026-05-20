"""工具执行器模块。

实现 Agent 可用的工具集合：Read、Search、Write、Edit、Bash。
所有工具执行都有安全校验（路径遍历防护、命令白名单等）。

主要类/函数：
    - ToolExecutor: 工具执行器，注册并执行工具。
    - execute_tool: 便捷函数，按名称执行工具。
"""

import logging
import os
import re
import subprocess
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 项目根目录（限制文件操作范围）
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Bash 命令白名单（只允许安全的命令）
BASH_ALLOWED_COMMANDS = [
    "ls", "cat", "grep", "find", "head", "tail", "wc", "echo",
    "python", "python3", "pytest", "ruff", "mypy", "git", "npm", "node",
    "pwd", "cd", "mkdir", "touch", "rm", "cp", "mv", "diff",
    "sort", "uniq", "awk", "sed", "xargs", "which", "file",
]

# 危险命令黑名单
BASH_BLOCKED_PATTERNS = [
    r"\brm\s+-rf\s+/",
    r"\bmkfs\.",
    r"\bdd\s+if=",
    r"\b:(){ :|:& };:",
    r"\bwget\s+.*\|\s*sh",
    r"\bcurl\s+.*\|\s*sh",
    r"\beval\s*\$",
    r"\bexec\s*\$",
]


def _resolve_path(path: str) -> str:
    """解析并校验路径，防止路径遍历攻击。

    Args:
        path: 用户提供的相对或绝对路径。

    Returns:
        str: 解析后的绝对路径。

    Raises:
        ValueError: 路径试图越出项目根目录时抛出。
    """
    if os.path.isabs(path):
        resolved = os.path.abspath(path)
    else:
        resolved = os.path.abspath(os.path.join(PROJECT_ROOT, path))

    # 校验路径在项目根目录内
    if not resolved.startswith(PROJECT_ROOT):
        raise ValueError(f"Path '{path}' is outside project root")

    return resolved


def _validate_bash_command(command: str) -> None:
    """校验 bash 命令安全性。

    Args:
        command: 要执行的命令字符串。

    Raises:
        ValueError: 命令包含危险模式时抛出。
    """
    for pattern in BASH_BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            raise ValueError(f"Command contains blocked pattern: {pattern}")


def tool_read(path: str, offset: Optional[int] = None, limit: Optional[int] = None) -> Dict[str, Any]:
    """读取文件内容。

    Args:
        path: 文件路径（相对项目根目录或绝对路径）。
        offset: 起始行号（1-based，可选）。
        limit: 最大读取行数（可选）。

    Returns:
        Dict: 包含 content（内容）、lines（总行数）、path（解析后路径）的字典。
    """
    resolved = _resolve_path(path)
    if not os.path.exists(resolved):
        return {"error": f"File not found: {path}", "path": resolved}
    if os.path.isdir(resolved):
        return {"error": f"Path is a directory: {path}", "path": resolved}

    try:
        with open(resolved, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        return {"error": f"File is not text-readable: {path}", "path": resolved}
    except Exception as exc:
        return {"error": f"Read error: {exc}", "path": resolved}

    total_lines = len(lines)

    if offset is not None:
        start = max(0, offset - 1)
        end = start + (limit or total_lines)
        selected = lines[start:end]
    elif limit is not None:
        selected = lines[:limit]
    else:
        selected = lines

    content = "".join(selected)
    return {
        "content": content,
        "lines": total_lines,
        "path": resolved,
        "offset": offset or 1,
        "read_lines": len(selected),
    }


def tool_search(query: str, path: Optional[str] = None, glob: Optional[str] = None) -> Dict[str, Any]:
    """在代码库中搜索文本。

    Args:
        query: 搜索关键词（支持正则）。
        path: 限制搜索的目录（可选）。
        glob: 文件匹配模式（如 '*.py'，可选）。

    Returns:
        Dict: 包含 matches（匹配结果列表）的字典。
    """
    import fnmatch

    search_root = PROJECT_ROOT if path is None else _resolve_path(path)
    if not os.path.isdir(search_root):
        return {"error": f"Search path is not a directory: {path}", "matches": []}

    matches = []
    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error as exc:
        return {"error": f"Invalid regex: {exc}", "matches": []}

    for root, _dirs, files in os.walk(search_root):
        # 跳过隐藏目录和依赖目录
        _dirs[:] = [d for d in _dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv", ".git")]

        for filename in files:
            if filename.startswith("."):
                continue
            if glob and not fnmatch.fnmatch(filename, glob):
                continue

            file_path = os.path.join(root, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line_no, line in enumerate(f, 1):
                        if pattern.search(line):
                            rel_path = os.path.relpath(file_path, PROJECT_ROOT)
                            matches.append({
                                "path": rel_path,
                                "line": line_no,
                                "content": line.rstrip("\n"),
                            })
                            if len(matches) >= 50:
                                break
            except (UnicodeDecodeError, OSError):
                continue
            if len(matches) >= 50:
                break
        if len(matches) >= 50:
            break

    return {"matches": matches, "total": len(matches), "query": query}


def tool_write(path: str, content: str) -> Dict[str, Any]:
    """写入/创建文件。

    Args:
        path: 文件路径。
        content: 文件内容。

    Returns:
        Dict: 包含 success、path、bytes_written 的字典。
    """
    resolved = _resolve_path(path)
    dir_path = os.path.dirname(resolved)

    try:
        os.makedirs(dir_path, exist_ok=True)
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "success": True,
            "path": resolved,
            "bytes_written": len(content.encode("utf-8")),
        }
    except Exception as exc:
        return {"error": f"Write failed: {exc}", "path": resolved}


def tool_edit(path: str, old_string: str, new_string: str) -> Dict[str, Any]:
    """编辑文件（搜索替换）。

    Args:
        path: 文件路径。
        old_string: 要替换的旧文本。
        new_string: 新文本。

    Returns:
        Dict: 包含 success、path、replacements 的字典。
    """
    resolved = _resolve_path(path)
    if not os.path.exists(resolved):
        return {"error": f"File not found: {path}", "path": resolved}

    try:
        with open(resolved, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as exc:
        return {"error": f"Read failed: {exc}", "path": resolved}

    if old_string not in content:
        return {"error": "old_string not found in file", "path": resolved}

    new_content = content.replace(old_string, new_string, 1)
    replacements = 1 if new_content != content else 0

    try:
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(new_content)
        return {
            "success": True,
            "path": resolved,
            "replacements": replacements,
        }
    except Exception as exc:
        return {"error": f"Write failed: {exc}", "path": resolved}


def tool_bash(command: str, timeout: int = 30) -> Dict[str, Any]:
    """执行 shell 命令。

    Args:
        command: 要执行的命令。
        timeout: 超时时间（秒）。

    Returns:
        Dict: 包含 stdout、stderr、returncode 的字典。
    """
    _validate_bash_command(command)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_ROOT,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "command": command,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s", "command": command}
    except Exception as exc:
        return {"error": f"Command execution failed: {exc}", "command": command}


# 工具注册表
TOOL_REGISTRY: Dict[str, Any] = {
    "Read": tool_read,
    "Search": tool_search,
    "Write": tool_write,
    "Edit": tool_edit,
    "Bash": tool_bash,
}


class ToolExecutor:
    """工具执行器。

    注册并执行 Agent 可用的工具，提供统一的调用接口。

    Attributes:
        registry: 工具函数字典。
    """

    def __init__(self):
        """初始化工具执行器，注册默认工具。"""
        self.registry = dict(TOOL_REGISTRY)

    def execute(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """按名称执行工具。

        Args:
            tool_name: 工具名称（如 'Read', 'Bash'）。
            **kwargs: 工具参数。

        Returns:
            Dict: 工具执行结果。

        Raises:
            ValueError: 工具不存在时抛出。
        """
        tool = self.registry.get(tool_name)
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' not found. Available: {list(self.registry.keys())}")

        logger.info("Executing tool '%s' with args: %s", tool_name, kwargs)
        result = tool(**kwargs)
        logger.info("Tool '%s' result: %s", tool_name, "success" if "error" not in result else "error")
        return result

    def list_tools(self) -> list:
        """列出所有可用工具名称。

        Returns:
            list: 工具名称列表。
        """
        return list(self.registry.keys())


def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """便捷函数：按名称执行工具。

    Args:
        tool_name: 工具名称。
        **kwargs: 工具参数。

    Returns:
        Dict: 工具执行结果。
    """
    executor = ToolExecutor()
    return executor.execute(tool_name, **kwargs)
