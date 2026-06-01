"""静态分析引擎，封装 semgrep 调用。"""

import json
import logging
import subprocess
import tempfile
from typing import Any

logger = logging.getLogger(__name__)


class StaticAnalysisEngine:
    """静态分析引擎。"""

    def __init__(self) -> None:
        self._check_semgrep()

    def _check_semgrep(self) -> None:
        """检查 semgrep 是否已安装。"""
        try:
            subprocess.run(
                ["semgrep", "--version"],
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning(
                "semgrep not found. Static analysis will be disabled. "
                "Install with: pip install semgrep"
            )

    def analyze_diff(self, diff: str) -> list[dict[str, Any]]:
        """分析代码 diff。

        Args:
            diff: 代码 diff 字符串。

        Returns:
            List[Dict]: 发现的问题列表。
        """
        try:
            # 将 diff 写入临时文件
            with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as f:
                f.write(diff)
                diff_path = f.name

            # 运行 semgrep
            result = subprocess.run(
                [
                    "semgrep",
                    "--config=auto",
                    "--json",
                    "--quiet",
                    diff_path,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode not in (0, 1):  # 0 = no findings, 1 = findings
                logger.error("semgrep failed: %s", result.stderr)
                return []

            output = json.loads(result.stdout)
            findings = output.get("results", [])

            # 转换为统一格式
            issues = []
            for finding in findings:
                issue = {
                    "file": finding.get("path", ""),
                    "line": finding.get("start", {}).get("line"),
                    "severity": self._map_severity(
                        finding.get("extra", {}).get("severity", "WARNING")
                    ),
                    "category": self._map_category(finding.get("check_id", "")),
                    "title": finding.get("extra", {}).get("message", "Unknown issue"),
                    "description": finding.get("extra", {}).get("message", ""),
                    "suggestion": finding.get("extra", {}).get("fix", ""),
                }
                issues.append(issue)

            return issues

        except subprocess.TimeoutExpired:
            logger.error("semgrep timed out")
            return []
        except Exception:
            logger.exception("Static analysis failed")
            return []

    def _map_severity(self, severity: str) -> str:
        """映射 semgrep 严重级别到内部级别。"""
        mapping = {
            "ERROR": "must_fix",
            "WARNING": "should_fix",
            "INFO": "nice_to_have",
        }
        return mapping.get(severity.upper(), "should_fix")

    def _map_category(self, check_id: str) -> str:
        """映射 semgrep check_id 到内部类别。"""
        check_id_lower = check_id.lower()
        if "security" in check_id_lower or "sql" in check_id_lower or "xss" in check_id_lower:
            return "security"
        if "performance" in check_id_lower:
            return "performance"
        if "style" in check_id_lower or "format" in check_id_lower:
            return "style"
        if "test" in check_id_lower:
            return "testing"
        return "maintainability"
