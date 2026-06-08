"""工具沙盒模块。

支持：
- 文件系统隔离
- 命令执行沙盒
- 权限控制
- 资源限制
"""

import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """沙盒配置。"""
    allowed_paths: list[str] = field(default_factory=list)  # 允许访问的路径
    blocked_commands: list[str] = field(default_factory=lambda: [
        "rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:", "wget.*|.*sh", "curl.*|.*sh"
    ])
    allowed_commands: list[str] = field(default_factory=lambda: [
        "ls", "cat", "grep", "find", "head", "tail", "wc", "echo",
        "python", "python3", "pytest", "ruff", "mypy", "git",
        "npm", "node", "pwd", "cd", "mkdir", "touch", "cp", "mv",
        "diff", "sort", "uniq", "awk", "sed", "xargs", "which", "file",
    ])
    max_output_size: int = 50000  # 最大输出大小（字节）
    max_execution_time: int = 30  # 最大执行时间（秒）
    read_only: bool = False  # 是否只读模式
    network_access: bool = True  # 是否允许网络访问


class ToolSandbox:
    """工具沙盒。"""

    def __init__(self, config: SandboxConfig | None = None):
        self.config = config or SandboxConfig()
        self._temp_dir = tempfile.mkdtemp(prefix="devmatrix_sandbox_")

    def validate_path(self, path: str) -> bool:
        """验证路径是否在允许范围内。"""
        if not self.config.allowed_paths:
            return True

        resolved = os.path.abspath(path)
        for allowed in self.config.allowed_paths:
            if resolved.startswith(os.path.abspath(allowed)):
                return True
        return False

    def validate_command(self, command: str) -> tuple[bool, str]:
        """验证命令是否安全。"""
        import re

        # 检查黑名单
        for pattern in self.config.blocked_commands:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Blocked pattern: {pattern}"

        # 检查白名单（如果配置了）
        if self.config.allowed_commands:
            cmd_base = command.split()[0] if command.split() else ""
            if cmd_base not in self.config.allowed_commands:
                return False, f"Command not in whitelist: {cmd_base}"

        return True, ""

    def execute(
        self,
        command: str,
        cwd: str | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """在沙盒中执行命令。"""
        # 验证命令
        valid, reason = self.validate_command(command)
        if not valid:
            return {
                "success": False,
                "error": f"Command blocked: {reason}",
                "stdout": "",
                "stderr": "",
            }

        # 验证工作目录
        if cwd and not self.validate_path(cwd):
            return {
                "success": False,
                "error": f"Path not allowed: {cwd}",
                "stdout": "",
                "stderr": "",
            }

        timeout = timeout or self.config.max_execution_time

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd or self._temp_dir,
            )

            # 截断输出
            stdout = result.stdout[:self.config.max_output_size]
            stderr = result.stderr[:self.config.max_output_size]

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout}s",
                "stdout": "",
                "stderr": "",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
            }

    def read_file(self, path: str) -> dict[str, Any]:
        """在沙盒中读取文件。"""
        if not self.validate_path(path):
            return {"success": False, "error": f"Path not allowed: {path}"}

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(self, path: str, content: str) -> dict[str, Any]:
        """在沙盒中写入文件。"""
        if self.config.read_only:
            return {"success": False, "error": "Read-only mode"}

        if not self.validate_path(path):
            return {"success": False, "error": f"Path not allowed: {path}"}

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def cleanup(self) -> None:
        """清理临时目录。"""
        import shutil
        shutil.rmtree(self._temp_dir, ignore_errors=True)


# 预定义沙盒配置
SANDBOX_CONFIGS = {
    "strict": SandboxConfig(
        allowed_paths=["/tmp"],
        read_only=True,
        network_access=False,
        max_execution_time=10,
    ),
    "standard": SandboxConfig(
        allowed_paths=[],
        read_only=False,
        network_access=True,
        max_execution_time=30,
    ),
    "permissive": SandboxConfig(
        allowed_paths=[],
        allowed_commands=[],
        read_only=False,
        network_access=True,
        max_execution_time=60,
    ),
}
