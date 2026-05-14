# Agent / Skill 管理功能设计文档

## 目标
为 DevMatrix 提供 Agent 管理和 Skill 管理两大模块：
1. **Agent 管理**：查看所有 Agent、实时状态、已装载 Skill，支持动态挂载/卸载 Skill
2. **Skill 管理**：查看所有 Skill、被哪些 Agent 使用，支持自定义 Skill 配置上传与自动注册

## 架构

### 后端 API（FastAPI）
扩展现有 `/registry` 路由，新增以下端点：

| Method | Path | 说明 |
|--------|------|------|
| GET | `/registry/agents` | 列出所有已注册 Agent（已有） |
| GET | `/registry/agents/detail` | 列出所有 Agent 详情（含状态、已装载 skills） |
| POST | `/registry/agents/{agent_name}/skills/{skill_name}` | 为 Agent 挂载 Skill |
| DELETE | `/registry/agents/{agent_name}/skills/{skill_name}` | 为 Agent 卸载 Skill |
| GET | `/registry/skills` | 列出所有已注册 Skill |
| POST | `/registry/skills/upload` | 上传自定义 Skill 配置（JSON），自动注册 |

#### Agent 状态设计
由于当前 Agent 是类级别注册，没有运行时实例管理，状态采用简化模型：
- `idle` - 空闲（默认）
- `active` - 活跃（在工作流中被调用过）
- `error` - 错误（上一次执行失败）

状态存储在内存字典中（`agent_status_store`），按 agent_name 记录。

#### 自定义 Skill 上传
上传 JSON 配置格式：
```json
{
  "name": "custom_skill",
  "description": "My custom skill",
  "code": "from app.skills.base import BaseSkill, SkillResult\nfrom typing import Any, Dict\n\nclass CustomSkill(BaseSkill):\n    name = 'custom_skill'\n    description = 'My custom skill'\n    async def execute(self, context: Dict[str, Any]) -> SkillResult:\n        return SkillResult(output='done')\n",
  "config": {
    "timeout": 30,
    "retry_count": 0
  }
}
```

后端将 `code` 写入 `app/skills/custom/` 目录（自动创建），文件名 `{name}.py`，然后动态 import 并注册到 `skill_registry`。

### 前端页面

#### Agent 管理页 (`/agents`)
- 表格展示所有 Agent：名称、描述、状态（彩色 badge）、已装载 Skills
- 点击 Agent 展开详情：Skill 列表 + 可用 Skill 列表
- 操作：挂载 Skill（下拉选择 + 确认）、卸载 Skill（按钮）

#### Skill 管理页 (`/skills`)
- 表格展示所有 Skill：名称、描述、被哪些 Agent 使用
- 上传区域：拖拽或点击上传 JSON 配置文件
- 上传后自动注册，刷新列表

### 文件变更

**后端：**
- `app/api/registry.py` - 扩展现有路由，新增所有端点
- `app/core/registry/agent_registry.py` - 添加 agent 实例创建和状态追踪辅助

**前端：**
- `frontend/src/router.ts` - 新增 `/agents`、`/skills` 路由
- `frontend/src/components/Sidebar.vue` - 新增导航项
- `frontend/src/api/index.ts` - 新增 API 调用方法
- `frontend/src/pages/AgentsPage.vue` - 新建 Agent 管理页
- `frontend/src/pages/SkillsPage.vue` - 新建 Skill 管理页
- `frontend/src/i18n/locales/zh.json` / `en.json` - 新增翻译

## UI 风格
延续现有 Linear/Vercel Dark 风格，使用 CSS 变量，保持与 Dashboard、Settings 一致的视觉语言。
