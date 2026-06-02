# DevMatrix

**Multi-role Collaborative Software Development Agent Operating System**

DevMatrix is an enterprise-grade AI software development platform that orchestrates multiple specialized AI agents through state-driven workflows with human-in-the-loop approval. Powered by Temporal workflow engine, it combines LLM intelligence with robust orchestration, code analysis, and human oversight to automate and enhance the software development lifecycle.

## Key Features

- **Multi-Agent Collaboration** — 6 specialized agents: Business Analyst, Product Manager, Architect, Developer, QA, Code Reviewer
- **State-Driven Workflow** — Each agent reads state, generates proposals, awaits human approval, then commits
- **Human-in-the-Loop** — Approval checkpoints between every workflow phase
- **AI Code Review** — Automated code review with severity scoring, issue detection, and improvement suggestions
- **RBAC & User Management** — Role-based access control with menu/agent permissions
- **Workflow Visualization** — Visual workflow editor powered by Vue Flow with drag-and-drop node design
- **Code Intelligence** — AST-based code indexing with context retrieval and Neo4j graph backend
- **Sandbox Execution** — Docker containers (dev) + Firecracker microVMs (production)
- **Task Management** — Jira-like task system with Kanban board and assignment tracking
- **Scheduled Tasks** — Cron-based task scheduling with execution history
- **Real-time Events** — SSE event stream for live workflow updates
- **Audit Logging** — Complete traceability of all user actions and system events
- **i18n** — Full Chinese/English support for both backend and frontend
- **Dark/Light Theme** — CSS variable-based theming with one-click toggle

## Architecture

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

## Tech Stack

| Category | Technology |
|----------|-----------|
| **Backend** | Python 3.10+, FastAPI, SQLAlchemy 2.0, Pydantic |
| **Frontend** | Vue 3.4+, TypeScript 5.3+, Vite 5.1+, Pinia 3.0 |
| **Workflow** | Temporal, APScheduler |
| **Database** | SQLite (dev) / PostgreSQL (prod), Alembic migrations |
| **LLM** | OpenAI, Anthropic, Claude Agent SDK |
| **Auth** | JWT (PyJWT), RBAC, bcrypt password hashing |
| **Visualization** | @vue-flow/core (workflow editor), lucide-vue-next (icons) |
| **i18n** | vue-i18n 9.9+ (frontend), JSON locales (backend) |
| **Infrastructure** | Docker Compose (Temporal, PostgreSQL, Redis) |
| **Code Quality** | Ruff, Black, MyPy, vue-tsc |

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

Each phase requires human approval before proceeding, ensuring quality control throughout the automated process.

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (optional, for Temporal/PostgreSQL/Redis)

### 1. Start Infrastructure (Optional)

```bash
docker-compose up -d temporal-server postgres redis
```

### 2. Backend Setup

```bash
pip install -r requirements.txt
python -c "from app.state.models import init_db; init_db()"
python app/scripts/init_rbac.py   # Create default admin user, roles, and menus
```

### 3. Start Temporal Worker (Optional)

```bash
python app/worker.py
```

### 4. Start API Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** and login with `admin` / `admin123`.

## Project Structure

```
dev-matrix/
├── app/                          # Backend (Python 3.10+)
│   ├── agents/                   # 6 AI Agents + BaseAgent
│   ├── api/                      # 20+ FastAPI endpoint modules
│   ├── code_intelligence/        # AST indexing + code graph
│   ├── core/                     # Registry, security, rate limiting
│   ├── events/                   # EventBus + handlers
│   ├── i18n/                     # Backend i18n (zh/en)
│   ├── llm/                      # LLM client + routing strategies
│   ├── prompts/                  # Jinja2 prompt template engine
│   ├── skills/                   # Pluggable skill system
│   ├── state/                    # SQLAlchemy models + repository
│   ├── workflow/                 # Temporal workflow engine
│   ├── config.py                 # Pydantic Settings
│   └── main.py                   # FastAPI app entry
├── config/                       # YAML configs (LLM routing, workflows)
├── frontend/                     # Vue 3 + TypeScript + Vite
│   └── src/
│       ├── api/                  # Unified API client
│       ├── components/           # 20+ Vue components
│       ├── composables/          # Vue composables (tabs, dialog, etc.)
│       ├── pages/                # 20+ route pages
│       ├── stores/               # Pinia stores
│       └── i18n/                 # Frontend i18n (zh/en)
├── tests/                        # pytest test suite
├── alembic/                      # Database migrations
├── docker-compose.yml            # Infrastructure services
└── Dockerfile                    # Application container
```

## API Overview

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login (returns JWT) |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Get current user info |
| POST | `/api/auth/refresh` | Refresh access token |
| POST | `/api/auth/password` | Change password |

### Core Resources

| Resource | Endpoints | Description |
|----------|-----------|-------------|
| Projects | `/api/projects` | Project CRUD + pagination |
| Tasks | `/api/tasks` | Jira-like task management |
| Workbench | `/api/workbench/tasks` | Agent task queue + chat |
| Workflows | `/api/workflow-config` | Workflow template CRUD |
| Instances | `/api/workflow-instances` | Running workflow instances |
| Code Reviews | `/api/code-reviews` | AI code review + re-run |
| Settings | `/api/settings` | System configuration |
| Scheduled | `/api/scheduled-tasks` | Cron task management |
| Users | `/api/users` | User CRUD |
| Roles | `/api/roles` | Role CRUD |
| Menus | `/api/menus` | Menu tree CRUD |
| Audit | `/api/audit/logs` | Audit log query |

### Example API Calls

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Start a workflow
curl -X POST http://localhost:8000/api/workflow/{project_id}/start \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/repo", "raw_input": "Add user authentication"}'

# Submit approval
curl -X POST "http://localhost:8000/api/approvals/{project_id}?status=approved&comment=Looks+good" \
  -H "Authorization: Bearer <token>"

# Create code review
curl -X POST http://localhost:8000/api/code-reviews \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "diff": "diff --git a/..."}'
```

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Overview with stats, activity, tasks |
| Projects | `/projects` | Project list + detail |
| Agents | `/agents` | Agent registry |
| Skills | `/skills` | Skill registry |
| Workbench | `/workbench` | Task queue with chat |
| Workflows | `/workflow/list` | Workflow templates |
| Workflow Editor | `/workflow/editor/:id?` | Visual flow editor |
| Workflow Instances | `/workflow/instances` | Running instances |
| Tasks | `/tasks/my`, `/tasks/board` | My tasks + Kanban |
| Code Reviews | `/code-reviews` | Review list + detail |
| Scheduled Tasks | `/scheduled-tasks` | Cron management |
| Settings | `/settings/system` | System/LLM/DB/Security/About |
| Users | `/users` | User management |
| Roles | `/roles` | Role management |
| Menus | `/menus` | Menu management |

## Design Patterns

| Pattern | Application |
|---------|------------|
| **Registry** | Agent, LLM Provider, Skill, Prompt registration |
| **Strategy** | LLM routing (quality_first / cost_first / config_driven) |
| **Template Method** | BaseAgent with abstract generate_proposal / validate_output |
| **Observer** | EventBus for decoupled module communication |
| **Repository** | StateRepository with snapshot/rollback |
| **Pipeline** | Configurable workflow stages via YAML |
| **Factory** | Sandbox provider selection |

## Agent System

### Built-in Agents

| Agent | Role | Description |
|-------|------|-------------|
| BusinessAnalyst | Requirement Analysis | Analyzes raw requirements, extracts acceptance criteria |
| ProductManager | PRD Generation | Generates Product Requirements Document |
| Architect | Code Impact Analysis | Analyzes codebase, identifies affected components |
| Developer | Patch Generation | Generates code patches for approved proposals |
| QA | Test Generation | Creates and executes test cases |
| CodeReviewer | Code Review | AI-powered code review with scoring and issue detection |
| ProjectManager | Project Management | Tracks project progress and coordinates agents |

### Skill System

Skills are independent, reusable capability units that can be composed with Agents:

```python
from app.agents.architect import ArchitectAgent
from app.skills.code_search import CodeSearchSkill

agent = ArchitectAgent(llm_router, state_repo)
agent.use_skill(CodeSearchSkill())

proposal = await agent.generate_proposal("proj_1", {"prd": "..."})
```

Register custom skills:

```python
from app.skills.base import BaseSkill, SkillResult
from app.skills.registry import register_skill

@register_skill("my_skill")
class MySkill(BaseSkill):
    name = "my_skill"
    description = "My custom skill"

    async def execute(self, context):
        return SkillResult(output="done")
```

## Environment Variables

Copy `.env.example` to `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `DATABASE_URL` | `sqlite:///./devmatrix.db` | Database connection |
| `TEMPORAL_HOST` | `localhost:7233` | Temporal server address |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `APP_HOST` | `0.0.0.0` | API server host |
| `APP_PORT` | `8000` | API server port |
| `DEBUG` | `false` | Debug mode |
| `DEFAULT_LOCALE` | `zh` | Default language (zh/en) |
| `LLM_STRATEGY` | `quality_first` | LLM routing strategy |
| `GITHUB_TOKEN` | — | GitHub token for PR automation |
| `NEO4J_URI` | — | Neo4j connection for code graph |

## Development

### Run Tests

```bash
# Backend
pytest tests/ -v

# Frontend type check
cd frontend && npx vue-tsc --noEmit

# Frontend build
cd frontend && npm run build
```

### Code Quality

```bash
# Python linting
ruff check app/ tests/

# Python formatting
ruff format app/ tests/
# or
black app/ tests/ --line-length 100
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop all services
docker-compose down
```

## License

MIT License — See [LICENSE](LICENSE) for details.
