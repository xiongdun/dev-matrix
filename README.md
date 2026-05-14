# DevMatrix

AI Software Development Operating System

Multi-role Collaborative Software Development Agent Operating System powered by Temporal workflow engine, featuring state-driven design, human-in-the-loop approval, code intelligence, and sandbox execution.

## Overview

DevMatrix is an enterprise-grade AI software development platform that orchestrates multiple specialized AI agents through a state-driven workflow. It combines the power of Large Language Models with robust workflow orchestration, code intelligence, and human oversight to automate and enhance the software development lifecycle.

### Key Capabilities

- **Multi-Agent Collaboration**: Business Analyst, Product Manager, Architect, Developer, QA Agent working in sequence
- **State-Driven Workflow**: Each agent reads state, generates proposals, awaits human approval, then commits
- **Human-in-the-Loop**: Approval checkpoints between every workflow phase
- **Code Intelligence**: In-memory code graph + Neo4j backend for production-scale code analysis
- **Sandbox Execution**: Docker containers (default) + Firecracker microVMs (production)
- **Auto PR/Release**: GitHub/GitLab integration for automated pull requests and releases
- **Multi-Repository Support**: Manage and modify multiple repositories simultaneously
- **Audit Logging**: Complete traceability of all state changes and agent actions
- **Vue 3 Dashboard**: Linear/Vercel-style dark developer tool UI with real-time monitoring
- **Theme Switching**: One-click toggle between dark and light themes
- **Settings Page**: Dedicated configuration page for appearance, LLM, workflow, and notifications
- **Internationalization (i18n)**: Full Chinese/English support for both backend and frontend

## Architecture

### 6-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 6: Execution Layer (Docker/Firecracker Sandbox)     │
├─────────────────────────────────────────────────────────────┤
│  Layer 5: Human Approval (REST API + Web UI)               │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Multi-Agent Layer (5 Specialized Agents)         │
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
| Workflow Engine | Temporal |
| API Framework | FastAPI (port 8000) |
| Frontend | Vue 3 + TypeScript + Vite (port 3000) |
| State Storage | SQLite (dev) / PostgreSQL (prod) |
| Code Graph | In-memory (dev) / Neo4j (prod) |
| Sandbox | Docker (dev) / Firecracker (prod) |
| LLM Providers | OpenAI, Anthropic |
| i18n | Backend: JSON locales / Frontend: vue-i18n |

## Project Structure

```
dev-matrix/
├── app/                          # Core application
│   ├── agents/                   # AI Agent implementations
│   │   ├── base.py              # BaseAgent with registry pattern
│   │   ├── business_analyst.py  # Requirement analysis
│   │   ├── product_manager.py   # PRD generation
│   │   ├── architect.py         # Code impact analysis
│   │   ├── developer.py         # Patch generation
│   │   └── qa.py                # Test generation & execution
│   ├── api/                      # FastAPI REST endpoints
│   │   ├── requirements.py      # Requirement CRUD
│   │   ├── approvals.py         # Approval workflow
│   │   ├── workflow.py          # Workflow control
│   │   └── registry.py          # Registry introspection
│   ├── code_intelligence/        # Code analysis & graph
│   │   ├── indexer.py           # AST code indexing
│   │   ├── retriever.py         # Context retrieval with scoring
│   │   └── code_graph.py        # Graph builder + Neo4j backend
│   ├── core/registry/            # Component registration (Registry Pattern)
│   │   ├── base.py              # Generic Registry<T>
│   │   ├── agent_registry.py    # AgentRegistry
│   │   ├── llm_registry.py      # LLMProviderRegistry
│   │   └── discovery.py         # Auto-discovery utility
│   ├── events/                   # Event-driven architecture (EventBus)
│   │   ├── bus.py               # EventBus (pub-sub)
│   │   ├── types.py             # Event type definitions
│   │   └── handlers/            # Event handlers
│   │       ├── state_handlers.py
│   │       ├── workflow_handlers.py
│   │       ├── agent_handlers.py
│   │       └── approval_handlers.py
│   ├── i18n/                     # Internationalization
│   │   ├── core.py              # i18n utilities
│   │   └── locales/             # Translation files
│   │       ├── en.json
│   │       └── zh.json
│   ├── llm/                      # LLM abstraction layer
│   │   ├── client.py            # LLM client implementations
│   │   ├── router.py            # LLM routing with strategies
│   │   └── strategies/          # Routing strategies (Strategy Pattern)
│   │       ├── base.py          # Strategy ABC
│   │       ├── quality_first.py # Quality-first strategy
│   │       ├── cost_first.py    # Cost-first strategy
│   │       └── config_driven.py # Config-driven strategy
│   ├── prompts/                  # Prompt template engine (Jinja2)
│   │   ├── engine.py            # Jinja2PromptTemplate
│   │   ├── registry.py          # PromptRegistry
│   │   ├── loader.py            # Filesystem loader
│   │   └── templates/           # .j2 template files
│   │       ├── business_analyst.j2
│   │       ├── product_manager.j2
│   │       ├── architect.j2
│   │       ├── developer.j2
│   │       └── qa.j2
│   ├── skills/                   # Pluggable Skill system
│   │   ├── base.py              # BaseSkill, SkillResult, SkillConfig
│   │   ├── registry.py          # SkillRegistry with decorator registration
│   │   ├── code_search.py       # Code search skill
│   │   ├── prompt_enhance.py    # Prompt enhancement skill
│   │   └── validation.py        # Output validation skill
│   ├── state/                    # State management + snapshots
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   └── repository.py        # StateRepository + snapshots + rollback
│   ├── utils/                    # Utilities (retry, audit, sandbox, git)
│   │   ├── retry.py             # Retry decorators (backoff + immediate)
│   │   ├── audit.py             # Audit logging
│   │   ├── multi_repo.py        # Multi-repo manager
│   │   ├── git_provider.py      # GitHub/GitLab integration
│   │   └── sandbox.py           # Docker/Firecracker sandbox
│   ├── workflow/                 # Temporal workflows + configurable pipeline
│   │   ├── activities.py        # Activity implementations
│   │   ├── definitions.py       # DevWorkflow class
│   │   ├── pipeline/            # Configurable pipeline (Pipeline Pattern)
│   │   │   ├── models.py        # PipelineStage, PipelineConfig
│   │   │   ├── loader.py        # YAML/JSON loader
│   │   │   └── executor.py      # WorkflowPipeline executor
│   │   └── worker.py            # Temporal Worker entry
│   ├── config.py                # Pydantic Settings
│   └── main.py                  # FastAPI application entry
├── config/                       # Configuration files
│   ├── llm-routing.yaml         # LLM routing rules
│   └── workflow-pipeline.yaml   # Workflow stage definitions
├── frontend/                     # Vue 3 + TypeScript + Vite frontend
│   ├── src/
│   │   ├── main.ts              # Application entry
│   │   ├── App.vue              # Root component
│   │   ├── style.css            # Linear/Vercel dark developer tool styles
│   │   ├── api/                 # API service layer
│   │   ├── components/          # Vue components
│   │   │   ├── Sidebar.vue      # Collapsible sidebar
│   │   │   ├── Dashboard.vue    # Main dashboard
│   │   │   ├── StatCard.vue     # Statistics cards
│   │   │   ├── ActivityList.vue # Recent activity
│   │   │   ├── TaskList.vue     # Recent tasks
│   │   │   ├── ThemeToggle.vue  # Dark/light theme toggle
│   │   │   └── settings/        # Settings components
│   │   │       ├── SettingsSection.vue
│   │   │       └── SettingItem.vue
│   │   ├── pages/               # Route pages
│   │   │   └── SettingsPage.vue # Settings configuration page
│   │   ├── composables/         # Vue composables
│   │   │   └── useSettings.ts   # Settings state management
│   │   ├── router.ts            # Vue Router configuration
│   │   └── i18n/                # Frontend i18n
│   │       ├── index.ts
│   │       └── locales/
│   │           ├── en.json
│   │           └── zh.json
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts           # Vite + proxy to backend:8000
│   ├── tsconfig.json
│   └── tsconfig.node.json
├── tests/                        # Test suite
│   ├── test_registry.py         # Registry pattern tests
│   ├── test_events.py           # EventBus tests
│   └── test_state.py            # State repository tests
├── docs/                         # Documentation
│   └── architecture.md          # Architecture documentation
├── docker-compose.yml            # Infrastructure services (Temporal, Postgres, Redis)
├── Dockerfile                    # Application container
├── requirements.txt              # Python dependencies
├── pytest.ini                   # Test configuration
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── LICENSE                      # MIT License
├── CLAUDE.md                    # Project context for AI assistants
└── README.md                    # This file
```

## Design Patterns

The project implements several enterprise design patterns:

| Pattern | Application | Benefit |
|---------|------------|---------|
| **Registry Pattern** | Agent, LLM Provider, Prompt registration | Runtime discovery, plugin architecture |
| **Strategy Pattern** | LLM routing strategies | Flexible provider selection |
| **Template Method** | Agent base class + overrides | Consistent agent behavior |
| **Observer Pattern** | EventBus for state changes | Decoupled module communication |
| **Repository Pattern** | StateRepository | Abstracted data access |
| **Pipeline Pattern** | Configurable workflow stages | Dynamic workflow composition |
| **Factory Pattern** | Sandbox provider selection | Runtime environment switching |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (optional)

### 1. Start Infrastructure (Optional)

```bash
docker-compose up -d temporal-server postgres redis
```

### 2. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
python -c "from app.state.models import init_db; init_db()"
```

### 4. Start Temporal Worker

```bash
python app/workflow/worker.py
```

### 5. Start API Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 6. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:3000` (or next available port).

## API Usage

### Create Requirement

```bash
curl -X POST http://localhost:8000/requirements/ \
  -H "Content-Type: application/json" \
  -d '{"requirement_raw_input": "Add user authentication with OAuth2"}'
```

### Start Workflow

```bash
curl -X POST http://localhost:8000/workflow/{project_id}/start \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/repo", "raw_input": "Add user authentication"}'
```

### Submit Approval

```bash
curl -X POST "http://localhost:8000/approvals/{project_id}?status=approved&comment=Looks+good"
```

### Check State

```bash
curl http://localhost:8000/approvals/{project_id}/state
```

### List Snapshots (for rollback)

```bash
curl http://localhost:8000/approvals/{project_id}/snapshots
```

### Rollback to Snapshot

```bash
curl -X POST "http://localhost:8000/approvals/{project_id}/rollback?snapshot_id={id}"
```

## Using Skills

Skills are independent, reusable capability units that can be used standalone or composed with Agents.

### Standalone Usage

```python
from app.skills.code_search import CodeSearchSkill

skill = CodeSearchSkill()
result = await skill.execute({"query": "authentication", "repo_path": "./my-project"})
print(result.output)
```

### Compose with Agent

```python
from app.agents.architect import ArchitectAgent
from app.skills.code_search import CodeSearchSkill

agent = ArchitectAgent(llm_router, state_repo)
agent.use_skill(CodeSearchSkill())

# Agent will automatically use code_search skill during proposal generation
proposal = await agent.generate_proposal(project_id, context)
```

### Register Custom Skill

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

## Internationalization (i18n)

DevMatrix supports both Chinese (zh) and English (en) with full i18n coverage.

### Backend i18n

Backend translations are stored in `app/i18n/locales/`:

```python
from app.i18n.core import get_text

message = get_text("workflow.approval_required", locale="zh")
```

### Frontend i18n

Frontend uses `vue-i18n` with translations in `frontend/src/i18n/locales/`:

```vue
<template>
  <p>{{ $t('dashboard.title') }}</p>
</template>
```

Switch language via the locale selector in the UI or by setting `DEFAULT_LOCALE` in `.env`.

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` - LLM provider credentials
- `DATABASE_URL` - Database connection string (defaults to SQLite)
- `TEMPORAL_HOST` - Temporal server address (default: `localhost:7233`)
- `REDIS_URL` - Redis connection (default: `redis://localhost:6379/0`)
- `APP_HOST` / `APP_PORT` - API server bind address (default: `0.0.0.0:8000`)
- `DEFAULT_LOCALE` - Default language: `zh` or `en` (default: `zh`)
- `LLM_STRATEGY` - Routing strategy: `quality_first`, `cost_first`, or `config_driven`
- `GITHUB_TOKEN` - For PR automation (optional)
- `NEO4J_URI` - Neo4j connection (optional)

## Workflow Pipeline

The development workflow follows this configurable pipeline:

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
Auto PR / Release
```

Each phase requires human approval before proceeding, ensuring quality control throughout the automated process.

## Frontend Dashboard

The Vue 3 frontend provides:

- **Linear/Vercel Dark UI**: Clean, high-contrast developer tool aesthetic inspired by Linear, Vercel, and GitHub Dark Mode
- **Theme Switching**: One-click toggle between dark (`#0a0a0a`) and light (`#ffffff`) themes via CSS variables
- **Collapsible Sidebar**: Fixed sidebar with smooth width transition (240px ↔ 64px)
- **Real-time Stats**: 4-column stat cards with trend indicators
- **Activity Feed**: Recent agent actions with color-coded type indicators
- **Task List**: Status badges (pending/running/completed/failed) with agent attribution
- **Settings Page**: `/settings` route with grouped configuration sections:
  - **Appearance**: Theme, language (zh/en), sidebar default state
  - **LLM Configuration**: Provider, API key, model, routing strategy
  - **Workflow**: Approval mode, timeout, retry count
  - **Notifications**: Event toggles, webhook URL
  - **About**: Version, backend status

## License

MIT License - See LICENSE file for details.
