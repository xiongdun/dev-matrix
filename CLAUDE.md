# DevMatrix — Claude Coding Context

## Project Overview

DevMatrix is a **Multi-role Collaborative Software Development Agent Operating System**.
It orchestrates multiple AI agents (Business Analyst, Product Manager, Architect, Developer, QA, Code Reviewer) through state-driven workflows with human-in-the-loop approval checkpoints.

**LLM Backend**: Xiaomi mimo-v2.5-pro via Anthropic protocol (claude-agent-sdk + Claude Code CLI).

## Architecture

### 6-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 6: Execution Layer (Docker/Firecracker Sandbox)     │
├─────────────────────────────────────────────────────────────┤
│  Layer 5: Human Approval (REST API + Vue 3 Web UI)         │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Multi-Agent Layer (6 Specialized Agents)         │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Code Intelligence (Code Graph + Neo4j)           │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: State Memory (SQLite/PostgreSQL + Snapshots)     │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Workflow Orchestrator (Temporal)                 │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI 0.136+ |
| Frontend | Vue 3 + TypeScript + Vite |
| State Storage | SQLite (dev) / PostgreSQL (prod), SQLAlchemy 2.0 |
| LLM | claude-agent-sdk 0.2.88 + Claude Code CLI 2.1.150 |
| LLM Provider | Xiaomi mimo-v2.5-pro (Anthropic protocol) |
| Auth | JWT (PyJWT) + RBAC |
| i18n | vue-i18n 9.9+ (zh/en) |
| Markdown | marked + highlight.js |
| Icons | lucide-vue-next |

## Project Structure

```
dev-matrix/
├── app/                          # Backend (Python 3.10+)
│   ├── agents/                   # 7 AI Agents + BaseAgent
│   ├── api/                      # 25+ FastAPI endpoint modules
│   ├── memory/                   # 记忆系统 (user/soul/skill/mcp)
│   ├── llm/                      # LLM client + routing strategies
│   ├── skills/                   # Pluggable skill system
│   ├── state/                    # SQLAlchemy models + repository
│   ├── workflow/                 # Temporal workflow engine
│   ├── config.py                 # Pydantic Settings
│   └── main.py                   # FastAPI app entry
├── workspace/                    # 用户工作空间
│   └── users/                    # 按 user_id 隔离
│       ├── {user_id}/
│       │   ├── profile.md        # 用户偏好
│       │   ├── memory.md         # 用户记忆
│       │   ├── soul.md           # AI 人设 + 用户画像
│       │   ├── skill/            # 自定义技能
│       │   ├── mcp/              # MCP 服务器配置
│       │   └── projects/         # 项目记忆
│       └── _shared/              # Agent 共享记忆
├── frontend/                     # Vue 3 + TypeScript + Vite
│   └── src/
│       ├── api/                  # Unified API client
│       ├── components/           # 25+ Vue components
│       ├── pages/                # 25+ route pages
│       └── stores/               # Pinia stores
├── tests/                        # pytest test suite
├── docs/                         # 设计文档
└── CLAUDE.md                     # This file
```

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Backend API | **8000** | FastAPI REST server (uvicorn) |
| Frontend Dev | **3000** | Vite dev server |

### Port Configuration

- **Backend**: `app/config.py` → `app_port: int = 8000`
- **Frontend**: `frontend/vite.config.ts` → `port: 3000, strictPort: true`
- **API Proxy**: Vite proxies `/api` and `/health` to `http://localhost:8000`

## Key Modules

### Memory System (`app/memory/manager.py`)

文件系统级用户记忆，按 `workspace/users/{user_id}/` 隔离：

| 文件 | 作用 | 注入位置 |
|------|------|----------|
| `profile.md` | 用户偏好（语言、风格） | system prompt |
| `memory.md` | 纠正/反馈/学习记忆 | system prompt |
| `soul.md` | AI 人设 + 用户画像 | system prompt 最前面 |
| `skill/*.md` | 用户自定义技能指令 | system prompt |
| `mcp/*.md` | MCP 服务器配置 | ClaudeAgentOptions.mcp_servers |
| `projects/*.md` | 项目决策/反馈 | system prompt |

核心函数：
- `get_soul_prompt(user_id)` — 读取 soul.md
- `get_skills_prompt(user_id)` — 扫描 skill/*.md
- `build_memory_prompt(user_id, agent_role, project_id)` — 组装完整记忆上下文
- `build_mcp_options(user_id)` — 转换 MCP 配置为 SDK 格式

### User Workspace API (`app/api/user_workspace.py`)

| 端点 | 说明 |
|------|------|
| `GET /api/users/{id}/workspace` | 获取完整 workspace 数据 |
| `GET /api/users/{id}/workspace/soul` | 获取 soul.md |
| `GET /api/users/{id}/workspace/memory` | 获取记忆 |
| `GET /api/users/{id}/workspace/skills` | 获取技能列表 |
| `GET /api/users/{id}/workspace/mcp` | 获取 MCP 配置 |
| `GET /api/users/{id}/workspace/projects` | 获取项目记忆 |

### Memory API (`app/api/memory.py`)

| 端点 | 说明 |
|------|------|
| `GET /api/memory/memories` | 获取当前用户记忆 |
| `POST /api/memory/memories` | 添加记忆 |
| `DELETE /api/memory/memories/{key}` | 删除记忆 |
| `GET /api/memory/profile` | 获取用户画像 |
| `PUT /api/memory/profile` | 更新用户画像 |

### Workbench Chat (`app/api/workbench.py`)

| 端点 | 说明 |
|------|------|
| `POST /api/workbench/tasks/{id}/chat` | 与 Agent 对话（claude-agent-sdk） |
| `GET /api/workbench/tasks/{id}/chat` | 获取对话历史 |
| `POST /api/workbench/tasks/{id}/approve` | 审批通过 |
| `POST /api/workbench/tasks/{id}/reject` | 打回 |
| `POST /api/workbench/tasks/{id}/retry` | 重试 |

**关键配置**：
- `SDK_MAX_TURNS` — 最大工具调用轮次（默认 20）
- `ANTHROPIC_API_KEY` — 小米 API Key
- `ANTHROPIC_BASE_URL` — 小米 API 端点
- `claude_sdk_enabled` — 数据库配置，启用 SDK

### Frontend Components

| 组件 | 说明 |
|------|------|
| `ChatMessage.vue` | 消息气泡（Markdown 渲染、代码高亮、工具卡片、复制/重生成按钮） |
| `TaskDetailPage.vue` | 工作台任务详情（对话 + 操作面板） |
| `UserDetailPage.vue` | 用户详情页（workspace 内容展示） |
| `App.vue` | 根组件（侧边栏 + 顶部导航 + 用户头像下拉菜单） |

## Quick Start

```bash
# 1. Backend setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Initialize database
python -c "from app.state.models import init_db; init_db()"
python app/scripts/init_rbac.py

# 3. Configure .env
# ANTHROPIC_API_KEY=your-xiaomi-api-key
# ANTHROPIC_BASE_URL=https://token-plan-cn.xiaomimimo.com/anthropic/v1
# DEFAULT_LLM_MODEL=mimo-v2.5-pro

# 4. Start API Server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. Frontend
cd frontend && npm install && npx vite --host 0.0.0.0 --port 3000
```

Login: `admin` / `admin123`

## Environment Variables

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite:///./devmatrix.db` | 数据库连接 |
| `ANTHROPIC_API_KEY` | — | 小米 API Key |
| `ANTHROPIC_BASE_URL` | `https://api.anthropic.com/v1` | API 端点 |
| `DEFAULT_LLM_MODEL` | `mimo-v2.5-pro` | 默认模型 |
| `SDK_MAX_TURNS` | `20` | SDK 最大轮次 |
| `DEBUG` | `false` | 调试模式 |
| `DEFAULT_LOCALE` | `zh` | 默认语言 |

## Known Pitfalls

1. **FastAPI trailing slash**: 后端路由用 `""` 不用 `"/"`，否则 307 重定向会丢失 Authorization header。

2. **Vite HMR on NTFS**: Windows 文件系统 (NTFS) 上 Vite HMR 不可靠，CSS 修改需重启 dev server。

3. **claude-agent-sdk 超时**: SDK 调用 Claude Code CLI 可能需要 10-30 秒，前端 chat 请求超时设为 5 分钟，不重试。

4. **重复请求**: 不要同时使用 `session_id` 复用 + 历史消息拼接，会导致 SDK 重复执行。

5. **代理**: 异步 httpx 客户端默认使用系统代理，小米 API 可能需要 `trust_env=False`。

## Development Guidelines

1. **Think Before Coding** — 明确假设，不确定就问
2. **Simplicity First** — 最少代码解决问题，不做推测性功能
3. **Surgical Changes** — 只改必要部分，不碰无关代码
4. **Goal-Driven Execution** — 定义可验证的成功标准
