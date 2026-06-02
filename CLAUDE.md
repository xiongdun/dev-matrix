# DevMatrix — Claude Coding Context

## Project Overview

DevMatrix is a **Multi-role Collaborative Software Development Agent Operating System**.
It orchestrates multiple AI agents (Business Analyst, Product Manager, Architect, Developer, QA, Code Reviewer) through state-driven workflows with human-in-the-loop approval checkpoints, powered by Temporal workflow engine.

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

| Layer | Technology | Version |
|-------|-----------|---------|
| Workflow Engine | Temporal | Latest |
| API Framework | FastAPI | 0.136+ |
| Frontend | Vue 3 + TypeScript + Vite | Vue 3.4+, Vite 5.1+ |
| State Storage | SQLite (dev) / PostgreSQL (prod) | SQLAlchemy 2.0 |
| Code Graph | In-memory (dev) / Neo4j (prod) | - |
| Sandbox | Docker (dev) / Firecracker (prod) | - |
| LLM Providers | OpenAI, Anthropic, Azure | openai 2.36+, claude-agent-sdk 0.2+ |
| Auth | JWT (PyJWT 2.12) + RBAC | - |
| i18n | vue-i18n 9.9+ (frontend), JSON-based (backend) | zh / en |
| State Management | Pinia 3.0 + persistedstate plugin | - |
| Workflow Visualization | @vue-flow/core 1.48+ | - |
| Icons | lucide-vue-next | 1.0+ |
| Task Scheduling | APScheduler 3.11 | - |
| Rate Limiting | slowapi (via core/limiter.py) | - |

### Design Patterns

| Pattern | Application |
|---------|------------|
| Registry | Agent, LLM Provider, Skill, Prompt registration |
| Strategy | LLM routing (quality_first / cost_first / config_driven) |
| Template Method | BaseAgent with abstract generate_proposal / validate_output |
| Observer | EventBus for decoupled module communication |
| Repository | StateRepository with snapshot/rollback |
| Pipeline | Configurable workflow stages via YAML |
| Factory | Sandbox provider selection |

## Project Structure

```
dev-matrix/
├── app/                          # Backend (Python 3.10+)
├── docker-compose.yml            # Infrastructure (Temporal, Postgres, Redis)
├── Dockerfile                    # Application container
├── alembic.ini                   # Alembic migration config
├── pyproject.toml                # Ruff + Black + MyPy config
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Dev dependencies
├── pytest.ini                    # Test configuration
├── .env.example                  # Environment variables template
├── CLAUDE.md                     # This file
└── README.md                     # Project documentation
```

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Backend API | **8000** | FastAPI REST server (uvicorn) |
| Frontend Dev | **3000** | Vite dev server (strictPort) |
| Temporal Server | 7233 | Temporal gRPC |
| Temporal UI | 8088 | Temporal Web UI |
| PostgreSQL | 5432 | Database (prod) |
| Redis | 6379 | Cache |

### Port Configuration

- **Backend**: `app/config.py` → `app_port: int = 8000`
- **Frontend**: `frontend/vite.config.ts` → `port: 3000, strictPort: true`
- **API Proxy**: Vite proxies `/api` and `/health` to `http://localhost:8000`

## Database Models (17 tables)

| Model | Table | Purpose |
|-------|-------|---------|
| ProjectModel | projects | Project management |
| ProjectStateModel | project_states | Project state JSON + version |
| StateSnapshotModel | state_snapshots | State history for rollback |
| WorkflowConfigModel | workflow_configs | Workflow templates (Vue Flow JSON) |
| WorkflowInstanceModel | workflow_instances | Running workflow instances |
| WorkflowTaskModel | workflow_tasks | Workbench tasks per stage |
| CodeReviewModel | code_reviews | AI code review results |
| TaskChatMessageModel | task_chat_messages | Agent chat messages |
| SystemConfigModel | system_configs | Key-value settings |
| SystemSecretModel | system_secrets | JWT secret etc. |
| TaskManagementModel | task_management | Jira-like task system |
| ScheduledTaskModel | scheduled_tasks | Cron-based task scheduling |
| ScheduledTaskLogModel | scheduled_task_logs | Task execution logs |
| UserModel | users | User accounts |
| RoleModel | roles | RBAC roles |
| UserRoleModel | user_roles | User-role mapping |
| MenuModel | menus | Sidebar menu tree |
| RoleMenuModel | role_menus | Role-menu permission mapping |
| RoleAgentModel | role_agents | Role-agent mapping |
| AuditLogModel | audit_logs | Audit trail |

## API Routes

### Public (no auth required)
- `POST /api/auth/login` — Login
- `GET /api/menus/tree` — Menu tree (for login page)
- `GET /health/live`, `GET /health/ready`, `GET /health` — Health checks

### Protected (JWT Bearer required)
- `/api/auth/me`, `/api/auth/refresh`, `/api/auth/logout`, `/api/auth/password`
- `/api/users` — User CRUD
- `/api/roles` — Role CRUD
- `/api/menus/my`, `/api/menus` — Menu CRUD
- `/api/projects` — Project CRUD + pagination
- `/api/tasks` — Task CRUD (Jira-like)
- `/api/workbench/tasks`, `/api/workbench/stats`, `/api/workbench/models`
- `/api/workflow/{project_id}/start`
- `/api/workflow-config`, `/api/workflow-config/templates`
- `/api/workflow-instances`
- `/api/code-reviews` — Code review CRUD + re-run
- `/api/registry/agents`, `/api/registry/skills`
- `/api/settings`, `/api/settings/categories`
- `/api/scheduled-tasks` — Scheduled task CRUD + toggle + run
- `/api/requirements`, `/api/approvals`
- `/api/events/stream` — SSE event stream
- `/api/audit/logs`
- `/api/lifecycle/{project_id}/pause|resume|cancel`

**Important**: All backend route decorators use `""` (empty string) for collection endpoints, not `"/"`. This avoids FastAPI 307 redirects that strip Authorization headers.

## Authentication & Authorization

- **JWT-based auth**: Access token (2h) + Refresh token (7d)
- **RBAC**: User → Roles → Menus (with permissions) + Agents
- **Route guard**: `get_current_user` dependency extracts Bearer token, validates JWT, loads user
- **Permission guard**: `require_permission("code_review:view")` checks role-menu-permission chain
- **Frontend guard**: `router.beforeEach` checks `localStorage.token`, redirects to `/login` if missing
- **Frontend directive**: `v-permission="'user:manage'"` conditionally renders elements
- **Default admin**: Created by `app/scripts/init_rbac.py` (admin/admin123)

## Development Workflow

```
Requirement Input
    ↓
Business Analyst → Requirement Analysis
    ↓ [Human Approval]
Product Manager → PRD Generation
    ↓ [Human Approval]
Architect → Code Impact Analysis
    ↓ [Human Approval]
Developer → Patch Generation
    ↓ [Human Approval]
QA Agent → Test Generation & Execution
    ↓ [Human Approval]
Code Reviewer → AI Code Review
    ↓
Auto PR / Release
```

## Quick Start

```bash
# 1. Start infrastructure (optional, for Temporal/Postgres/Redis)
docker-compose up -d

# 2. Backend setup
pip install -r requirements.txt
python -c "from app.state.models import init_db; init_db()"
python app/scripts/init_rbac.py  # Create default admin + roles + menus

# 3. Start Temporal Worker (optional, for workflow execution)
python app/worker.py

# 4. Start API Server (port 8000)
uvicorn app.main:app --reload --port 8000

# 5. Frontend setup
cd frontend
npm install
npm run dev  # port 3000
```

Open http://localhost:3000, login with admin/admin123.

## Key Files for Development

| File | Purpose |
|------|---------|
| `app/config.py` | Pydantic Settings (all env vars) |
| `app/main.py` | FastAPI app + lifespan + middleware + route registration |
| `app/worker.py` | Temporal worker entry |
| `app/state/models.py` | All SQLAlchemy models |
| `app/api/deps.py` | Dependency injection (auth, permissions) |
| `app/core/security.py` | JWT + password hashing |
| `app/core/secrets.py` | Auto-generated JWT secret storage |
| `app/agents/base.py` | BaseAgent + Claude Agent SDK integration |
| `app/llm/router.py` | LLM routing with strategy pattern |
| `app/workflow/engine.py` | Temporal-based workflow engine |
| `app/scripts/init_rbac.py` | Default RBAC data seeding |
| `frontend/src/main.ts` | Vue app entry (Pinia, Router, i18n, theme) |
| `frontend/src/router.ts` | Route definitions + auth/permission guards |
| `frontend/src/api/index.ts` | Unified API client (fetch + retry + 401 handling) |
| `frontend/src/stores/user.ts` | User store (Pinia + persistedstate) |
| `frontend/src/composables/useTabs.ts` | Tab state management |
| `frontend/vite.config.ts` | Vite + SPA fallback + API proxy |
| `config/llm-routing.yaml` | LLM provider routing rules |
| `config/workflow-pipeline.yaml` | Workflow stage config |

## Environment Variables

Copy `.env.example` to `.env`:

```env
OPENAI_API_KEY=sk-...
## Known Pitfalls

1. **FastAPI trailing slash redirects**: Backend routes use `""` (no trailing slash) for collection endpoints. If a route uses `"/"`, FastAPI returns 307 redirect which strips the `Authorization` header, causing 401 errors. Always use `""` for new routes.

2. **Pinia persist key**: User store persists to `localStorage` under key `devmatrix-user`, but the API client reads token from `localStorage.getItem('token')`. The `setToken()` method writes to both.

3. **Vite proxy**: Only `/api` and `/health` paths are proxied to backend. Other paths serve `index.html` (SPA fallback).

4. **SQLite WAL mode**: Dev mode uses SQLite with WAL journal mode for concurrent read/write support.

5. **Theme initialization**: Theme is resolved from `localStorage('devmatrix-settings')` before Vue mounts to prevent flash of wrong theme.

## Testing

```bash
# Backend tests
pytest tests/ -v

# Frontend build check
cd frontend && npm run build
```

## Linting & Formatting

```bash
# Python (Ruff)
ruff check app/ tests/
ruff format app/ tests/

# Python (Black)
black app/ tests/ --line-length 100

# TypeScript
cd frontend && npx vue-tsc --noEmit
```

---

## Behavioral Guidelines

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
