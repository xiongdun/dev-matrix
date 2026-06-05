"""记忆系统管理模块。

提供用户记忆、Agent 记忆、项目记忆的读写能力。
记忆以 Markdown 文件存储，按 user_id 隔离。

目录结构：
    user/
    ├── {user_id}/
    │   ├── profile.md         # 用户画像
    │   ├── memory.md          # 用户级记忆
    │   └── projects/
    │       └── {project_id}.md  # 项目记忆
    └── _shared/
        └── {agent_role}.md    # Agent 共享记忆

记忆文件格式：
    # 标题
    ## 分类
    - **key** — value
      - 置信度: 0.9
      - 来源: user_feedback
      - 时间: 2026-06-04
"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MEMORY_ROOT = Path(__file__).parent.parent.parent / "workspace" / "users"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _read_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _write_file(path: Path, content: str) -> None:
    _ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


# ===== 解析器 =====


def _parse_memories_md(content: str) -> list[dict[str, Any]]:
    """解析 memory.md 中的记忆条目。"""
    memories = []
    current_type = ""
    for line in content.split("\n"):
        # 检测分类标题
        if line.startswith("## "):
            current_type = line[3:].strip().lower()
            continue
        # 解析记忆条目: - **key** — value  或  - **key** - value
        m = re.match(r"^- \*\*(.+?)\*\*\s*[—\-]\s*(.+)$", line)
        if m:
            item: dict[str, Any] = {
                "type": current_type,
                "key": m.group(1).strip(),
                "value": m.group(2).strip(),
            }
            memories.append(item)
            continue
        # 解析子属性: - 置信度: 0.9
        if memories and line.startswith("  - "):
            sub = line[4:].strip()
            sm = re.match(r"^(置信度|来源|时间):\s*(.+)$", sub)
            if sm:
                k, v = sm.group(1), sm.group(2)
                if k == "置信度":
                    memories[-1]["confidence"] = float(v)
                elif k == "来源":
                    memories[-1]["source"] = v
                elif k == "时间":
                    memories[-1]["created_at"] = v
    return memories


def _build_memories_md(memories: list[dict[str, Any]]) -> str:
    """生成 memory.md 内容。"""
    lines = ["# 用户记忆", "", "记录纠正、反馈、学习到的偏好。", ""]

    # 按 type 分组
    groups: dict[str, list[dict[str, Any]]] = {}
    for m in memories:
        t = m.get("type", "其他")
        groups.setdefault(t, []).append(m)

    for group_name, items in groups.items():
        lines.append(f"---\n")
        lines.append(f"## {group_name}")
        lines.append("")
        for item in items:
            lines.append(f"- **{item['key']}** — {item.get('value', '')}")
            if "confidence" in item:
                lines.append(f"  - 置信度: {item['confidence']}")
            if "source" in item:
                lines.append(f"  - 来源: {item['source']}")
            if "created_at" in item:
                lines.append(f"  - 时间: {item['created_at']}")
        lines.append("")

    return "\n".join(lines)


def _parse_profile_md(content: str) -> dict[str, Any]:
    """解析 profile.md。"""
    profile: dict[str, Any] = {}
    preferences: dict[str, str] = {}
    patterns: dict[str, str] = {}
    section = ""

    for line in content.split("\n"):
        if "## 偏好设置" in line:
            section = "prefs"
            continue
        if "## 交互模式" in line:
            section = "patterns"
            continue
        # 解析表格行: | key | value |
        m = re.match(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|$", line)
        if m and m.group(1).strip() not in ("项目", "模式", "------") and "---" not in line:
            k, v = m.group(1).strip(), m.group(2).strip()
            if section == "prefs":
                preferences[k] = v
            elif section == "patterns":
                patterns[k] = v
        # 解析基础信息: - **key**: value
        bm = re.match(r"^- \*\*(.+?)\*\*:\s*(.+)$", line)
        if bm:
            profile[bm.group(1).strip()] = bm.group(2).strip()

    if preferences:
        profile["preferences"] = preferences
    if patterns:
        profile["patterns"] = patterns
    return profile


def _build_profile_md(profile: dict[str, Any]) -> str:
    """生成 profile.md 内容。"""
    lines = ["# 用户画像", ""]
    for k, v in profile.items():
        if k in ("preferences", "patterns"):
            continue
        lines.append(f"- **{k}**: {v}")

    prefs = profile.get("preferences", {})
    if prefs:
        lines.extend(["", "## 偏好设置", "", "| 项目 | 值 |", "|------|-----|"])
        for k, v in prefs.items():
            lines.append(f"| {k} | {v} |")

    patterns = profile.get("patterns", {})
    if patterns:
        lines.extend(["", "## 交互模式（系统学习）", "", "| 模式 | 值 |", "|------|-----|"])
        for k, v in patterns.items():
            lines.append(f"| {k} | {v} |")

    return "\n".join(lines) + "\n"


def _parse_project_md(content: str) -> dict[str, Any]:
    """解析项目记忆 .md。"""
    data: dict[str, Any] = {}
    decisions: list[dict[str, Any]] = []
    feedback: list[dict[str, Any]] = []
    context: dict[str, str] = {}
    section = ""

    for line in content.split("\n"):
        if "## 项目上下文" in line:
            section = "context"
            continue
        if "## Agent 决策" in line:
            section = "decisions"
            continue
        if "## 用户反馈" in line:
            section = "feedback"
            continue

        if section == "context":
            m = re.match(r"^- \*\*(.+?)\*\*:\s*(.+)$", line)
            if m:
                context[m.group(1).strip()] = m.group(2).strip()

        elif section == "decisions":
            m = re.match(r"^- (.+?):\s*(.+)$", line)
            if m:
                decisions.append({"agent": m.group(1).strip(), "decision": m.group(2).strip()})
            sub = re.match(r"^\s+- 审批人:\s*(.+)$", line)
            if sub and decisions:
                decisions[-1]["approved_by"] = sub.group(1).strip()
            sub = re.match(r"^\s+- 时间:\s*(.+)$", line)
            if sub and decisions:
                decisions[-1]["created_at"] = sub.group(1).strip()

        elif section == "feedback":
            m = re.match(r"^- (.+)$", line)
            if m and "时间:" not in line:
                feedback.append({"content": m.group(1).strip()})
            sub = re.match(r"^\s+- 时间:\s*(.+)$", line)
            if sub and feedback:
                feedback[-1]["created_at"] = sub.group(1).strip()

    if context:
        data["context"] = context
    if decisions:
        data["decisions"] = decisions
    if feedback:
        data["feedback"] = feedback
    return data


def _build_project_md(data: dict[str, Any]) -> str:
    """生成项目记忆 .md。"""
    lines = [f"# 项目记忆 — {data.get('project_id', 'unknown')}", ""]

    ctx = data.get("context", {})
    if ctx:
        lines.extend(["## 项目上下文", ""])
        for k, v in ctx.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")

    decisions = data.get("decisions", [])
    if decisions:
        lines.extend(["## Agent 决策", ""])
        for d in decisions:
            lines.append(f"- {d.get('agent', '?')}: {d.get('decision', '')}")
            if "approved_by" in d:
                lines.append(f"  - 审批人: {d['approved_by']}")
            if "created_at" in d:
                lines.append(f"  - 时间: {d['created_at']}")
        lines.append("")

    feedback = data.get("feedback", [])
    if feedback:
        lines.extend(["## 用户反馈", ""])
        for f in feedback:
            lines.append(f"- {f.get('content', '')}")
            if "created_at" in f:
                lines.append(f"  - 时间: {f['created_at']}")
        lines.append("")

    return "\n".join(lines) + "\n"


def _parse_agent_md(content: str) -> dict[str, Any]:
    """解析 Agent 共享记忆 .md。"""
    data: dict[str, Any] = {}
    knowledge: list[dict[str, Any]] = []
    mistakes: list[dict[str, Any]] = []
    patterns: list[dict[str, Any]] = []
    section = ""

    for line in content.split("\n"):
        if "## 角色知识" in line:
            section = "knowledge"
            continue
        if "## 常见错误" in line:
            section = "mistakes"
            continue
        if "## 成功模式" in line:
            section = "patterns"
            continue

        if section == "knowledge":
            m = re.match(r"^- \*\*(.+?)\*\*:\s*(.+)$", line)
            if m:
                knowledge.append({"key": m.group(1).strip(), "value": m.group(2).strip()})
            sub = re.match(r"^\s+- 来源:\s*(.+)$", line)
            if sub and knowledge:
                knowledge[-1]["source"] = sub.group(1).strip()

        elif section == "mistakes":
            m = re.match(r"^- \*\*(.+?)\*\*:\s*(.+)$", line)
            if m:
                mistakes.append({"key": m.group(1).strip(), "value": m.group(2).strip()})
            sub = re.match(r"^\s+- 频率:\s*(.+)$", line)
            if sub and mistakes:
                mistakes[-1]["frequency"] = int(sub.group(1).strip())

        elif section == "patterns":
            m = re.match(r"^- \*\*(.+?)\*\*:\s*(.+)$", line)
            if m:
                patterns.append({"key": m.group(1).strip(), "value": m.group(2).strip()})
            sub = re.match(r"^\s+- 置信度:\s*(.+)$", line)
            if sub and patterns:
                patterns[-1]["confidence"] = float(sub.group(1).strip())

    if knowledge:
        data["knowledge"] = knowledge
    if mistakes:
        data["common_mistakes"] = mistakes
    if patterns:
        data["success_patterns"] = patterns
    return data


def _build_agent_md(data: dict[str, Any]) -> str:
    """生成 Agent 共享记忆 .md。"""
    lines = [f"# Agent 共享记忆 — {data.get('agent_role', 'unknown')}", ""]

    knowledge = data.get("knowledge", [])
    if knowledge:
        lines.extend(["## 角色知识", ""])
        for k in knowledge:
            lines.append(f"- **{k.get('key', '')}**: {k.get('value', '')}")
            if "source" in k:
                lines.append(f"  - 来源: {k['source']}")
        lines.append("")

    mistakes = data.get("common_mistakes", [])
    if mistakes:
        lines.extend(["## 常见错误", ""])
        for m in mistakes:
            lines.append(f"- **{m.get('key', '')}**: {m.get('value', '')}")
            if "frequency" in m:
                lines.append(f"  - 频率: {m['frequency']}")
        lines.append("")

    patterns = data.get("success_patterns", [])
    if patterns:
        lines.extend(["## 成功模式", ""])
        for p in patterns:
            lines.append(f"- **{p.get('key', '')}**: {p.get('value', '')}")
            if "confidence" in p:
                lines.append(f"  - 置信度: {p['confidence']}")
        lines.append("")

    return "\n".join(lines) + "\n"


# ===== 管理器 =====


class UserMemoryManager:
    """用户记忆管理器。"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user_dir = MEMORY_ROOT / str(user_id)
        self.profile_path = self.user_dir / "profile.md"
        self.memory_path = self.user_dir / "memory.md"
        self.projects_dir = self.user_dir / "projects"
        _ensure_dir(self.projects_dir)

    def get_profile(self) -> dict[str, Any]:
        return _parse_profile_md(_read_file(self.profile_path))

    def update_profile(self, updates: dict[str, Any]) -> None:
        profile = self.get_profile()
        for k, v in updates.items():
            if isinstance(v, dict) and k in profile and isinstance(profile[k], dict):
                profile[k].update(v)
            else:
                profile[k] = v
        _write_file(self.profile_path, _build_profile_md(profile))

    def get_memories(self, memory_type: str | None = None) -> list[dict[str, Any]]:
        memories = _parse_memories_md(_read_file(self.memory_path))
        if memory_type:
            memories = [m for m in memories if m.get("type") == memory_type]
        return memories

    def add_memory(
        self,
        memory_type: str,
        key: str,
        value: str,
        source: str = "user_feedback",
        confidence: float = 1.0,
    ) -> None:
        memories = self.get_memories()
        for m in memories:
            if m.get("key") == key:
                m["value"] = value
                m["source"] = source
                m["confidence"] = confidence
                m["created_at"] = datetime.now().strftime("%Y-%m-%d")
                _write_file(self.memory_path, _build_memories_md(memories))
                return
        memories.append(
            {
                "type": memory_type,
                "key": key,
                "value": value,
                "source": source,
                "confidence": confidence,
                "created_at": datetime.now().strftime("%Y-%m-%d"),
            }
        )
        _write_file(self.memory_path, _build_memories_md(memories))

    def remove_memory(self, key: str) -> bool:
        memories = self.get_memories()
        before = len(memories)
        memories = [m for m in memories if m.get("key") != key]
        if len(memories) < before:
            _write_file(self.memory_path, _build_memories_md(memories))
            return True
        return False

    def clear_memories(self) -> None:
        _write_file(self.memory_path, _build_memories_md([]))

    def get_project_memory(self, project_id: str) -> dict[str, Any]:
        path = self.projects_dir / f"{project_id}.md"
        data = _parse_project_md(_read_file(path))
        data["project_id"] = project_id
        return data

    def update_project_memory(self, project_id: str, updates: dict[str, Any]) -> None:
        path = self.projects_dir / f"{project_id}.md"
        data = _parse_project_md(_read_file(path))
        data["project_id"] = project_id
        for k, v in updates.items():
            if isinstance(v, dict) and k in data and isinstance(data[k], dict):
                data[k].update(v)
            elif isinstance(v, list) and k in data and isinstance(data[k], list):
                data[k].extend(v)
            else:
                data[k] = v
        _write_file(path, _build_project_md(data))

    def add_project_decision(self, project_id: str, agent: str, decision: str) -> None:
        self.update_project_memory(
            project_id,
            {
                "decisions": [
                    {
                        "agent": agent,
                        "decision": decision,
                        "approved_by": str(self.user_id),
                        "created_at": datetime.now().strftime("%Y-%m-%d"),
                    }
                ]
            },
        )

    def add_project_feedback(self, project_id: str, content: str) -> None:
        self.update_project_memory(
            project_id,
            {
                "feedback": [
                    {
                        "content": content,
                        "created_at": datetime.now().strftime("%Y-%m-%d"),
                    }
                ]
            },
        )


class AgentMemoryManager:
    """Agent 共享记忆管理器。"""

    def __init__(self, agent_role: str):
        self.agent_role = agent_role
        self.shared_dir = MEMORY_ROOT / "_shared"
        self.agent_path = self.shared_dir / f"{agent_role}.md"
        _ensure_dir(self.shared_dir)

    def get_memory(self) -> dict[str, Any]:
        data = _parse_agent_md(_read_file(self.agent_path))
        data["agent_role"] = self.agent_role
        return data

    def add_knowledge(self, key: str, value: str, source: str = "learned") -> None:
        data = self.get_memory()
        knowledge = data.get("knowledge", [])
        for k in knowledge:
            if k.get("key") == key:
                k["value"] = value
                k["source"] = source
                _write_file(self.agent_path, _build_agent_md(data))
                return
        knowledge.append({"key": key, "value": value, "source": source})
        data["knowledge"] = knowledge
        _write_file(self.agent_path, _build_agent_md(data))

    def add_mistake(self, key: str, value: str) -> None:
        data = self.get_memory()
        mistakes = data.get("common_mistakes", [])
        for m in mistakes:
            if m.get("key") == key:
                m["frequency"] = m.get("frequency", 0) + 1
                _write_file(self.agent_path, _build_agent_md(data))
                return
        mistakes.append({"key": key, "value": value, "frequency": 1})
        data["common_mistakes"] = mistakes
        _write_file(self.agent_path, _build_agent_md(data))

    def add_success_pattern(self, key: str, value: str, confidence: float = 0.8) -> None:
        data = self.get_memory()
        patterns = data.get("success_patterns", [])
        for p in patterns:
            if p.get("key") == key:
                p["value"] = value
                p["confidence"] = confidence
                _write_file(self.agent_path, _build_agent_md(data))
                return
        patterns.append({"key": key, "value": value, "confidence": confidence})
        data["success_patterns"] = patterns
        _write_file(self.agent_path, _build_agent_md(data))


def build_memory_prompt(user_id: int, agent_role: str, project_id: str | None = None) -> str:
    """组装记忆上下文，注入到 system prompt 中。"""
    parts = []

    # 1. 用户偏好
    user_mgr = UserMemoryManager(user_id)
    profile = user_mgr.get_profile()
    prefs = profile.get("preferences", {})
    if prefs:
        lang = prefs.get("语言", prefs.get("language", "zh"))
        style = prefs.get("沟通风格", prefs.get("communication_style", "concise"))
        parts.append(f"用户偏好：语言={lang}，风格={style}")

    # 2. 用户记忆（最近 5 条高置信度）
    memories = user_mgr.get_memories()
    high_conf = [m for m in memories if m.get("confidence", 0) >= 0.8][-5:]
    if high_conf:
        mem_lines = [f"- {m['key']}: {m.get('value', '')}" for m in high_conf]
        parts.append("用户记忆：\n" + "\n".join(mem_lines))

    # 3. Agent 共享记忆
    agent_mgr = AgentMemoryManager(agent_role)
    agent_mem = agent_mgr.get_memory()
    mistakes = agent_mem.get("common_mistakes", [])
    if mistakes:
        mistake_lines = [f"- {m['key']}" for m in mistakes[:3]]
        parts.append("避免以下常见错误：\n" + "\n".join(mistake_lines))

    patterns = agent_mem.get("success_patterns", [])
    if patterns:
        pattern_lines = [f"- {p['value']}" for p in patterns[:3]]
        parts.append("成功模式：\n" + "\n".join(pattern_lines))

    # 4. 项目记忆
    if project_id:
        proj_mem = user_mgr.get_project_memory(project_id)
        decisions = proj_mem.get("decisions", [])
        if decisions:
            last_decisions = decisions[-3:]
            dec_lines = [f"- {d['decision']}" for d in last_decisions]
            parts.append("项目决策：\n" + "\n".join(dec_lines))

        feedback = proj_mem.get("feedback", [])
        if feedback:
            last_feedback = feedback[-3:]
            fb_lines = [f"- {f['content']}" for f in last_feedback]
            parts.append("项目反馈：\n" + "\n".join(fb_lines))

    if not parts:
        return ""

    return "\n\n---\n记忆上下文（仅供参考，不要主动提及）：\n" + "\n\n".join(parts)


# ===== Soul 解析 =====


def _parse_soul_md(content: str) -> dict[str, Any]:
    """解析 soul.md，提取 AI 人设和用户画像。"""
    data: dict[str, Any] = {}
    ai_persona: dict[str, str] = {}
    user_profile: dict[str, str] = {}
    project_context: dict[str, str] = {}
    section = ""

    for line in content.split("\n"):
        if "## AI 人设" in line:
            section = "ai"
            continue
        if "## 用户画像" in line:
            section = "user"
            continue
        if "## 项目上下文" in line:
            section = "project"
            continue

        m = re.match(r"^- \*\*(.+?)\*\*:\s*(.+)$", line)
        if m:
            k, v = m.group(1).strip(), m.group(2).strip()
            if section == "ai":
                ai_persona[k] = v
            elif section == "user":
                user_profile[k] = v
            elif section == "project":
                project_context[k] = v

    if ai_persona:
        data["ai_persona"] = ai_persona
    if user_profile:
        data["user_profile"] = user_profile
    if project_context:
        data["project_context"] = project_context
    return data


def get_soul_prompt(user_id: int) -> str:
    """读取 soul.md 并返回注入到 system prompt 的内容。"""
    soul_path = MEMORY_ROOT / str(user_id) / "soul.md"
    if not soul_path.exists():
        return ""

    content = _read_file(soul_path)
    data = _parse_soul_md(content)
    if not data:
        return ""

    parts = []

    ai = data.get("ai_persona", {})
    if ai:
        lines = [f"- {k}: {v}" for k, v in ai.items()]
        parts.append("AI 人设：\n" + "\n".join(lines))

    user = data.get("user_profile", {})
    if user:
        lines = [f"- {k}: {v}" for k, v in user.items()]
        parts.append("用户画像：\n" + "\n".join(lines))

    proj = data.get("project_context", {})
    if proj:
        lines = [f"- {k}: {v}" for k, v in proj.items()]
        parts.append("项目上下文：\n" + "\n".join(lines))

    return "\n\n".join(parts)


# ===== Skill 解析 =====


def get_user_skills(user_id: int) -> list[dict[str, Any]]:
    """扫描用户 skill/ 目录，返回技能列表。"""
    skill_dir = MEMORY_ROOT / str(user_id) / "skill"
    if not skill_dir.exists():
        return []

    skills = []
    for md_file in sorted(skill_dir.glob("*.md")):
        content = _read_file(md_file)
        skill = _parse_skill_md(content, md_file.stem)
        if skill:
            skills.append(skill)
    return skills


def _parse_skill_md(content: str, name: str) -> dict[str, Any]:
    """解析技能 .md 文件。"""
    skill: dict[str, Any] = {"name": name}
    section = ""

    for line in content.split("\n"):
        if line.startswith("# ") and not skill.get("title"):
            skill["title"] = line[2:].strip()
            continue
        if "## 描述" in line:
            section = "desc"
            continue
        if "## 触发条件" in line:
            section = "trigger"
            continue
        if "## 执行步骤" in line:
            section = "steps"
            continue
        if "## 输出格式" in line:
            section = "output"
            continue
        if "## 约束" in line:
            section = "constraints"
            continue

        if section == "desc" and line.strip():
            skill["description"] = skill.get("description", "") + line.strip() + "\n"
        elif section == "trigger" and line.startswith("- "):
            skill.setdefault("triggers", []).append(line[2:].strip())
        elif section == "steps" and line.strip():
            skill.setdefault("steps", []).append(line.strip())
        elif section == "constraints" and line.startswith("- "):
            skill.setdefault("constraints", []).append(line[2:].strip())

    return skill


def get_skills_prompt(user_id: int) -> str:
    """组装用户技能注入到 system prompt。"""
    skills = get_user_skills(user_id)
    if not skills:
        return ""

    parts = []
    for skill in skills:
        lines = [f"### {skill.get('name', '')}"]
        if skill.get("description"):
            lines.append(skill["description"].strip())
        if skill.get("triggers"):
            lines.append("触发条件：" + "、".join(skill["triggers"]))
        if skill.get("constraints"):
            lines.append("约束：" + "、".join(skill["constraints"]))
        parts.append("\n".join(lines))

    return "\n\n## 可用技能\n\n" + "\n\n".join(parts)


# ===== MCP 解析 =====


def get_user_mcp_servers(user_id: int) -> list[dict[str, Any]]:
    """扫描用户 mcp/ 目录，返回 MCP 服务器配置列表。"""
    mcp_dir = MEMORY_ROOT / str(user_id) / "mcp"
    if not mcp_dir.exists():
        return []

    servers = []
    for md_file in sorted(mcp_dir.glob("*.md")):
        content = _read_file(md_file)
        server = _parse_mcp_md(content, md_file.stem)
        if server:
            servers.append(server)
    return servers


def _parse_mcp_md(content: str, name: str) -> dict[str, Any]:
    """解析 MCP 服务器 .md 文件。"""
    server: dict[str, Any] = {"name": name}
    section = ""

    for line in content.split("\n"):
        if line.startswith("# ") and not server.get("title"):
            server["title"] = line[2:].strip()
            continue
        if "## 服务器信息" in line:
            section = "info"
            continue
        if "## 环境变量" in line:
            section = "env"
            continue
        if "## 可用工具" in line:
            section = "tools"
            continue

        if section == "info":
            m = re.match(r"^- \*\*(.+?)\*\*:\s*(.+)$", line)
            if m:
                k, v = m.group(1).strip(), m.group(2).strip()
                server[k] = v

        elif section == "env":
            m = re.match(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|.*\|$", line)
            if m and m.group(1).strip() != "变量" and "---" not in line:
                var_name = m.group(1).strip()
                var_desc = m.group(2).strip()
                server.setdefault("env_vars", []).append(
                    {"name": var_name, "description": var_desc}
                )

        elif section == "tools":
            m = re.match(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|$", line)
            if m and m.group(1).strip() != "工具" and "---" not in line:
                server.setdefault("tools", []).append(
                    {"name": m.group(1).strip(), "description": m.group(2).strip()}
                )

    return server


def build_mcp_options(user_id: int) -> list[dict[str, Any]]:
    """将用户 MCP 配置转换为 ClaudeAgentOptions.mcp_servers 格式。"""
    servers = get_user_mcp_servers(user_id)
    mcp_configs = []

    for server in servers:
        command = server.get("命令", "")
        if not command:
            continue

        # 解析命令和参数
        cmd_parts = command.split()
        cmd = cmd_parts[0] if cmd_parts else ""
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []

        # 从环境变量读取实际值
        env = {}
        for var in server.get("env_vars", []):
            var_name = var["name"]
            env[var_name] = os.environ.get(var_name, "")

        mcp_configs.append(
            {
                "name": server.get("name", ""),
                "command": cmd,
                "args": args,
                "env": env,
            }
        )

    return mcp_configs
