# 系统架构

## 六层架构

| 层级 | 功能 | 技术 |
|------|------|------|
| Layer 6 | 执行层 | Docker / Firecracker |
| Layer 5 | 人工审批层 | REST API + Vue 3 Web UI |
| Layer 4 | 多智能体层 | 6 个专业 Agent |
| Layer 3 | 代码智能层 | AST 索引 + Neo4j |
| Layer 2 | 状态记忆层 | SQLite/PostgreSQL + 快照 |
| Layer 1 | 工作流编排层 | Temporal + APScheduler |

## 目录结构

```
app/
├── agents/          # Agent 实现
├── api/             # FastAPI 端点
├── memory/          # 记忆系统
├── llm/             # LLM 客户端
├── skills/          # 技能系统
├── state/           # 数据模型
└── workflow/        # 工作流引擎

workspace/users/     # 用户记忆
frontend/            # Vue 3 前端
```

## 数据库

- 开发：SQLite (`devmatrix.db`)
- 生产：PostgreSQL
- ORM：SQLAlchemy 2.0
- 迁移：Alembic

## 认证

- JWT (PyJWT) + RBAC
- 用户 → 角色 → 菜单 → 权限
- 默认管理员：admin / admin123
