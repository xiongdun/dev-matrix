# DevMatrix - Claude Coding Context

## Project Overview

DevMatrix is a **Multi-role Collaborative Software Development Agent Operating System**.
It orchestrates multiple AI agents (Business Analyst, Product Manager, Architect, Developer, QA) through a state-driven workflow with human-in-the-loop approval checkpoints.

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

### Tech Stack & Frameworks

| Layer | Technology | Version |
|-------|-----------|---------|
| Workflow Engine | Temporal | Latest |
| API Framework | FastAPI | Python 3.10+ |
| Frontend Framework | Vue 3 + TypeScript + Vite | Vue 3.4+ |
| State Storage | SQLite (dev) / PostgreSQL (prod) | - |
| Code Graph | In-memory (dev) / Neo4j (prod) | - |
| Sandbox | Docker (dev) / Firecracker (prod) | - |
| LLM Providers | OpenAI, Anthropic, Azure | - |
| i18n | vue-i18n (frontend), JSON-based (backend) | vue-i18n 9.9+ |

### Design Patterns Used

- **Registry Pattern** - Agent, LLM Provider, Prompt registration
- **Strategy Pattern** - LLM routing strategies (quality_first / cost_first / config_driven)
- **Template Method** - Agent base class with overrides
- **Observer Pattern** - EventBus for decoupled module communication
- **Repository Pattern** - StateRepository with snapshot/rollback
- **Pipeline Pattern** - Configurable workflow stages via YAML
- **Factory Pattern** - Sandbox provider selection

## Project Structure

```
dev-matrix/
├── app/                          # Core application (Python)
│   ├── agents/                   # AI Agent implementations
│   ├── api/                      # FastAPI REST endpoints
│   ├── code_intelligence/        # Code analysis & graph
│   ├── core/registry/            # Component registration (Registry Pattern)
│   ├── events/                   # Event-driven architecture (EventBus)
│   ├── i18n/                     # Backend internationalization
│   ├── llm/                      # LLM abstraction layer + strategies
│   ├── prompts/                  # Prompt template engine (Jinja2)
│   ├── state/                    # State management + snapshots
│   ├── utils/                    # Utilities (retry, audit, sandbox, git)
│   ├── workflow/                 # Temporal workflows + configurable pipeline
│   ├── config.py                 # Pydantic Settings
│   └── main.py                   # FastAPI application entry
├── config/                       # YAML configurations
│   ├── llm-routing.yaml         # LLM routing rules
│   └── workflow-pipeline.yaml   # Workflow stage definitions
├── frontend/                     # Vue 3 + TypeScript frontend
│   ├── src/
│   │   ├── i18n/                # Frontend internationalization (vue-i18n)
│   │   ├── components/          # Vue components
│   │   ├── api/                 # API service layer
│   │   ├── App.vue              # Root component
│   │   └── main.ts              # Application entry
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts           # Vite + proxy config
│   └── tsconfig.json            # TypeScript config
├── tests/                        # Test suite (pytest)
├── docs/                         # Documentation
├── docker-compose.yml            # Infrastructure services
├── Dockerfile                    # Application container
├── requirements.txt              # Python dependencies
├── pytest.ini                   # Test configuration
└── README.md                     # Project documentation
```

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Backend API | **8000** | FastAPI REST server |
| Frontend Dev | **3000** | Vite dev server (falls back to 3001 if busy) |
| Temporal Server | 7233 | Temporal gRPC |
| Temporal UI | 8088 | Temporal Web UI |
| PostgreSQL | 5432 | Database (optional) |
| Redis | 6379 | Cache (optional) |

### Port Configuration

- **Backend**: Configured in `app/config.py` (`app_port: int = 8000`)
- **Frontend**: Configured in `frontend/vite.config.ts` (`port: 3000`)
- **API Proxy**: Frontend Vite proxies `/requirements`, `/approvals`, `/workflow`, `/health` to `http://localhost:8000`

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
Auto PR / Release
```

## Quick Start Commands

```bash
# 1. Start infrastructure (optional)
docker-compose up -d temporal-server postgres redis

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Initialize database
python -c "from app.state.models import init_db; init_db()"

# 4. Start Temporal Worker
python app/worker.py

# 5. Start API Server (port 8000)
uvicorn app.main:app --reload --port 8000

# 6. Start Frontend (port 3000)
cd frontend
npm install
npm run dev
```

## Key Files for Development

| File | Purpose |
|------|---------|
| `app/config.py` | Application settings (database, LLM, locale) |
| `app/main.py` | FastAPI app entry with lifespan |
| `app/worker.py` | Temporal worker entry |
| `frontend/vite.config.ts` | Vite config + API proxy |
| `frontend/src/i18n/index.ts` | i18n configuration |
| `config/llm-routing.yaml` | LLM provider routing rules |
| `config/workflow-pipeline.yaml` | Workflow stage config |

## Internationalization (i18n)

- **Backend**: `app/i18n/` - JSON-based translation with dot notation keys
- **Frontend**: `frontend/src/i18n/` - vue-i18n with JSON locale files
- **Default Locale**: `zh` (configurable via `default_locale` in `app/config.py`)
- **Supported Locales**: zh, en

## Environment Variables

Copy `.env.example` to `.env`:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=sqlite:///./devmatrix.db
TEMPORAL_HOST=localhost:7233
DEFAULT_LOCALE=zh
GITHUB_TOKEN=ghp_...  # Optional, for PR automation
NEO4J_URI=bolt://localhost:7687  # Optional
```

---

## Behavioral Guidelines

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

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

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
