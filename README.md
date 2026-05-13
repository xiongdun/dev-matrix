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
- **Vue 3 Dashboard**: macOS glassmorphism UI with real-time monitoring

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
| API Framework | FastAPI |
| Frontend | Vue 3 + TypeScript + Vite |
| State Storage | SQLite (dev) / PostgreSQL (prod) |
| Code Graph | In-memory (dev) / Neo4j (prod) |
| Sandbox | Docker (dev) / Firecracker (prod) |
| LLM Providers | OpenAI, Anthropic, Azure |

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
│   │   ├── indexer.py           # Code indexing
│   │   ├── retriever.py         # Context retrieval
│   │   └── code_graph.py        # Graph builder + Neo4j
│   ├── core/registry/            # Component registration
│   │   ├── base.py              # Generic Registry
│   │   ├── agent_registry.py    # AgentRegistry
│   │   ├── llm_registry.py      # LLMProviderRegistry
│   │   └── discovery.py         # Auto-discovery
│   ├── events/                   # Event-driven architecture
│   │   ├── bus.py               # EventBus (pub-sub)
│   │   ├── types.py             # Event type definitions
│   │   └── handlers/            # Event handlers
│   ├── llm/                      # LLM abstraction layer
│   │   ├── client.py            # LLM client implementations
│   │   ├── router.py            # LLM routing with strategies
│   │   └── strategies/          # Routing strategies
│   │       ├── base.py          # Strategy ABC
│   │       ├── quality_first.py # Quality-first strategy
│   │       ├── cost_first.py    # Cost-first strategy
│   │       └── config_driven.py # Config-driven strategy
│   ├── prompts/                  # Prompt template engine
│   │   ├── engine.py            # Jinja2PromptTemplate
│   │   ├── registry.py          # PromptRegistry
│   │   ├── loader.py            # Filesystem loader
│   │   └── templates/           # .j2 template files
│   ├── state/                    # State management
│   │   ├── models.py            # SQLAlchemy models
│   │   └── repository.py        # StateRepository + snapshots
│   ├── utils/                    # Utilities
│   │   ├── retry.py             # Retry decorators
│   │   ├── audit.py             # Audit logging
│   │   ├── multi_repo.py        # Multi-repo manager
│   │   ├── git_provider.py      # GitHub/GitLab integration
│   │   └── sandbox.py           # Docker/Firecracker sandbox
│   ├── workflow/                 # Temporal workflows
│   │   ├── activities.py        # Activity implementations
│   │   ├── definitions.py       # DevWorkflow class
│   │   └── pipeline/            # Configurable pipeline
│   │       ├── models.py        # PipelineStage, PipelineConfig
│   │       ├── loader.py        # YAML loader
│   │       └── executor.py      # WorkflowPipeline executor
│   ├── config.py                # Application configuration
│   └── main.py                  # FastAPI application entry
├── config/                       # Configuration files
│   ├── llm-routing.yaml         # LLM routing rules
│   └── workflow-pipeline.yaml   # Workflow stage definitions
├── frontend/                     # Vue 3 + TypeScript frontend
│   ├── src/
│   │   ├── main.ts              # Application entry
│   │   ├── App.vue              # Root component
│   │   ├── style.css            # macOS glassmorphism styles
│   │   ├── api/                 # API service layer
│   │   └── components/          # Vue components
│   │       ├── Sidebar.vue      # Collapsible sidebar
│   │       ├── Dashboard.vue    # Main dashboard
│   │       ├── StatCard.vue     # Statistics cards
│   │       ├── ActivityList.vue # Recent activity
│   │       └── TaskList.vue     # Recent tasks
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts           # Vite + proxy config
│   └── tsconfig.json            # TypeScript config
├── tests/                        # Test suite
├── docs/                         # Documentation
├── docker-compose.yml            # Infrastructure services
├── Dockerfile                    # Application container
├── requirements.txt              # Python dependencies
└── pytest.ini                   # Test configuration
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
python app/worker.py
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

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` - LLM provider credentials
- `DATABASE_URL` - Database connection string (defaults to SQLite)
- `TEMPORAL_HOST` - Temporal server address
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

- **macOS Glassmorphism UI**: `backdrop-filter: blur(40px)` with semi-transparent surfaces
- **Collapsible Sidebar**: Click the DevMatrix logo to toggle sidebar width
- **Real-time Stats**: Agent status, task progress, budget tracking
- **Activity Feed**: Recent agent actions and workflow events
- **Task List**: Current development tasks with status indicators

## License

MIT License - See LICENSE file for details.
