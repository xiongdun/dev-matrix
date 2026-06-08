# DevMatrix

**Multi-role Collaborative Software Development Agent Operating System**

DevMatrix 是一个企业级 AI 软件开发平台，通过状态驱动的工作流编排多个专业 AI Agent 协作完成软件开发生命周期，每个阶段都需人工审批后才能进入下一步。

## 核心特性

- **多 Agent 协作** — 7 个专业 Agent：业务分析师、产品经理、架构师、开发者、QA、代码审查员、项目经理
- **Claude Agent SDK 集成** — 通过 Claude Code CLI 实现工具调用（Read/Write/Edit/Bash）
- **用户记忆系统** — 按用户隔离的 workspace，包含 profile、memory、soul、skill、mcp
- **RBAC 权限管理** — 用户→角色→菜单→权限的完整链路
- **工作台对话** — 与 Agent 实时对话，支持 Markdown 渲染、代码高亮、工具调用展示
- **AI 代码审查** — 自动化代码审查，含评分、问题检测、改进建议
- **可视化工作流** — Vue Flow 拖拽式工作流编辑器
- **中英文双语** — 前后端完整 i18n 支持

## 架构

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

## 技术栈

| 类别 | 技术 |
|------|------|
| **后端** | Python 3.10+, FastAPI, SQLAlchemy 2.0, Pydantic |
| **前端** | Vue 3, TypeScript, Vite, Pinia |
| **AI** | claude-agent-sdk, Claude Code CLI, 小米 mimo-v2.5-pro |
| **认证** | JWT (PyJWT), RBAC |
| **数据库** | SQLite (开发) / PostgreSQL (生产), Alembic |
| **Markdown** | marked + highlight.js |

## 快速开始

### 1. 后端

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 初始化数据库
python -c "from app.state.models import init_db; init_db()"
python app/scripts/init_rbac.py

# 配置 .env
cp .env.example .env
# 编辑 .env，填入 API Key
```

### 2. 配置 .env

```env
DATABASE_URL=sqlite:///./devmatrix.db
ANTHROPIC_API_KEY=your-api-key
ANTHROPIC_BASE_URL=https://token-plan-cn.xiaomimimo.com/anthropic/v1
DEFAULT_LLM_MODEL=mimo-v2.5-pro
SDK_MAX_TURNS=20
DEBUG=true
DEFAULT_LOCALE=zh
```

### 3. 启动服务

```bash
# 后端 (端口 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端 (端口 3000)
cd frontend
npm install
npx vite --host 0.0.0.0 --port 3000
```

打开 http://localhost:3000，使用 `admin` / `admin123` 登录。

## 用户记忆系统

每个用户有独立的 workspace 目录，存储个性化配置和记忆：

```
workspace/users/{user_id}/
├── profile.md     # 用户偏好设置
├── memory.md      # 记忆（纠正/反馈/学习）
├── soul.md        # AI 人设 + 用户画像
├── skill/         # 自定义技能
│   └── *.md
├── mcp/           # MCP 服务器配置
│   └── *.md
└── projects/      # 项目记忆
    └── *.md
```

记忆内容会自动注入到 Agent 的 system prompt 中，实现个性化交互。

## API 概览

### 认证

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录（返回 JWT） |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 核心资源

| 资源 | 端点 | 说明 |
|------|------|------|
| 工作台 | `/api/workbench/tasks` | Agent 任务队列 |
| 对话 | `/api/workbench/tasks/{id}/chat` | 与 Agent 对话 |
| 项目 | `/api/projects` | 项目 CRUD |
| 用户 | `/api/users` | 用户管理 |
| 记忆 | `/api/memory` | 用户记忆管理 |
| Workspace | `/api/users/{id}/workspace` | 用户 workspace |
| 设置 | `/api/settings` | 系统配置 |
| 审计 | `/api/audit/logs` | 审计日志 |

## 开发工作流

```
需求输入
    ↓
业务分析师 → 需求分析
    ↓ [人工审批]
产品经理 → PRD 生成
    ↓ [人工审批]
架构师 → 代码影响分析
    ↓ [人工审批]
开发者 → 代码补丁生成
    ↓ [人工审批]
QA → 测试生成与执行
    ↓ [人工审批]
代码审查员 → AI 代码审查
    ↓
自动 PR / 发布
```

## 项目结构

```
dev-matrix/
├── app/                          # 后端 (Python)
│   ├── agents/                   # AI Agent 实现
│   ├── api/                      # FastAPI 端点
│   ├── memory/                   # 记忆系统
│   ├── llm/                      # LLM 客户端
│   ├── skills/                   # 技能系统
│   ├── state/                    # 数据模型
│   └── workflow/                 # 工作流引擎
├── workspace/users/              # 用户工作空间
├── frontend/                     # 前端 (Vue 3)
│   └── src/
│       ├── components/           # Vue 组件
│       ├── pages/                # 页面
│       └── api/                  # API 客户端
├── docs/                         # 设计文档
└── tests/                        # 测试
```

## 测试

```bash
# 后端测试
pytest tests/ -v

# 前端构建检查
cd frontend && npm run build
```

## 已知问题

### WSL + NTFS 下 Vite HMR 不可靠

项目在 WSL 中运行且源码位于 NTFS 挂载盘（如 `/mnt/d/`）时，Vite 的 HMR（Hot Module Replacement）文件监听不可靠，CSS/Vue 模板改动可能不触发热更新。

**解决方案**：修改前端代码后，手动重启 Vite dev server（`Ctrl+C` 后重新 `npx vite`）。

### WSL 系统代理干扰 API 请求

WSL 环境可能配置了 `HTTP_PROXY` 系统代理，导致 `httpx.AsyncClient` 请求小米 API 返回 503/404。后端所有 `httpx.AsyncClient` 已统一设置 `trust_env=False` 绕过。

## 许可证

MIT License

##TODO
- [1 ] 完善用户记忆系统
- [ ] 优化工作流引擎
- [ ] 增加更多技能
- [ ] 完善测试用例
- [ ] 部署到生产环境