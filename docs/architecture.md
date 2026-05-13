# DevMatrix Architecture

## 6-Layer Architecture

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

## Data Flow

1. **Requirement Input** → Workflow starts
2. **Agent reads state** → Generates proposal
3. **Human approves/rejects** → State commits or rolls back
4. **Next agent picks up** → Repeat until completion
5. **Auto PR/Release** → GitHub/GitLab integration

## Design Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| Registry | `core/registry/` | Runtime component discovery |
| Strategy | `llm/strategies/` | Flexible LLM provider selection |
| Observer | `events/` | Decoupled event communication |
| Repository | `state/repository.py` | Abstracted data access |
| Pipeline | `workflow/pipeline/` | Configurable workflow stages |
| Factory | `utils/sandbox.py`, `utils/git_provider.py` | Runtime provider creation |
