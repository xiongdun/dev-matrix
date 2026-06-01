# DevMatrix 生产级可用性优化设计文档

> **日期**: 2026-05-26
> **目标**: 将 DevMatrix 从开发阶段提升到生产级可用，提升安全性、鲁棒性、可靠性和可维护性。

---

## 1. 现状问题总览

### 🔴 Critical（必须修复）

| # | 问题 | 影响 | 涉及文件 |
|---|------|------|----------|
| 1 | JWT Secret 硬编码 fallback | 任何人都能伪造 Token | `app/core/security.py:21` |
| 2 | API 路由无统一认证保护 | 未登录可访问所有接口 | `app/api/*.py` |
| 3 | 无 API 限流 | 易受 DDoS / 暴力破解 | 全局 |
| 4 | 无数据库迁移工具 | 模型变更需删库重建 | 全局 |
| 5 | Docker 容器以 root 运行 | 安全风险 | `Dockerfile` |

### 🟠 High（严重影响）

| # | 问题 | 影响 | 涉及文件 |
|---|------|------|----------|
| 6 | 前端路由守卫无权限检查 | 无权限用户可访问管理页面 | `frontend/src/router.ts:201-215` |
| 7 | API 错误信息泄露内部细节 | 安全隐患 | `app/main.py:198-203` |
| 8 | 无健康检查端点 | 无法监控服务状态 | `docker-compose.yml` |
| 9 | CORS 允许所有来源 | 安全风险 | `app/main.py:261-267` |
| 10 | 审计日志未集成到 API | 无法追踪用户操作 | `app/utils/audit.py` |
| 11 | 前端 API 错误处理不完善 | 用户体验差 | `frontend/src/api/index.ts` |
| 12 | 无请求 ID 链路追踪 | 难以排查问题 | `app/main.py` |

### 🟡 Medium（建议优化）

| # | 问题 | 影响 | 涉及文件 |
|---|------|------|----------|
| 13 | 无 CI/CD 流水线 | 手动部署易出错 | `.github/workflows/` |
| 14 | 测试覆盖率不足 | 质量难以保证 | `tests/` |
| 15 | 前端无 XSS 防护 | 潜在安全风险 | `frontend/src/` |
| 16 | 无数据库连接池配置 | 高并发性能问题 | `app/state/models.py` |
| 17 | 配置缺少验证和默认值 | 启动失败风险 | `app/config.py` |

---

## 2. 优化方案

### 批次 1：安全加固（Security Hardening）

#### 1.1 JWT Secret 自动生成与持久化

**方案 B（已确认）**：首次启动自动生成随机密钥，保存到 SQLite 数据库，后续复用。

**实现**：
- 新增 `app/core/secrets.py` — 密钥管理模块
- 启动时检查数据库中是否存在 `jwt_secret_key`
- 不存在则生成 256 位随机密钥并保存
- `app/core/security.py` 从 secrets 模块获取密钥

#### 1.2 API 统一认证保护

**实现**：
- 新增 `app/api/deps.py` — `get_current_user` 依赖（已存在但需完善）
- 为所有非公开 API 路由添加 `Depends(get_current_user)`
- 公开路由（登录、健康检查）标记 `tags=["public"]`

#### 1.3 API 限流（Rate Limiting）

**实现**：
- 使用 `slowapi` 库（基于 Redis 或内存）
- 登录接口：5 次/分钟
- 普通 API：100 次/分钟
- 全局错误返回 429 Too Many Requests

#### 1.4 CORS 配置收紧

**实现**：
- 开发环境允许 `localhost:3000`
- 生产环境只允许配置的域名
- 从环境变量读取 `ALLOWED_ORIGINS`

### 批次 2：基础设施（Infrastructure）

#### 2.1 Alembic 数据库迁移

**实现**：
- 初始化 Alembic：`alembic init alembic`
- 配置 `alembic.ini` 指向 `DATABASE_URL`
- 创建初始迁移脚本
- 启动时自动执行 `alembic upgrade head`

#### 2.2 Docker 安全加固

**实现**：
- 多阶段构建（减小镜像体积）
- 创建非 root 用户运行
- 添加健康检查 `HEALTHCHECK`
- 使用 `.dockerignore`

#### 2.3 健康检查与监控

**实现**：
- `/health` 端点扩展：检查数据库、Redis、Temporal 连接
- `/health/ready` — 就绪探针
- `/health/live` — 存活探针
- docker-compose 添加 `healthcheck` 配置

### 批次 3：前端鲁棒性（Frontend Robustness）

#### 3.1 路由守卫权限检查

**实现**：
- `router.beforeEach` 中检查 `to.meta.permission`
- 调用 `userStore.hasPermission()` 验证
- 无权限则重定向到 403 页面或首页

#### 3.2 API 错误处理增强

**实现**：
- 统一错误提示组件（替代 `alert`）
- 网络错误自动重试（已实现但需完善）
- 500 错误显示友好提示，不暴露内部信息
- 请求超时处理

#### 3.3 状态持久化与恢复

**实现**：
- Pinia store 使用 `pinia-plugin-persistedstate`
- 刷新后自动恢复用户信息和菜单
- Token 过期前自动刷新

### 批次 4：可观测性（Observability）

#### 4.1 结构化日志

**实现**：
- 使用 `structlog` 替代标准 logging
- 所有日志包含 `request_id`、`user_id`、`path`
- 敏感字段自动脱敏（password、token、api_key）

#### 4.2 审计日志集成

**实现**：
- 所有写操作（POST/PUT/DELETE）自动记录审计日志
- 记录操作用户、IP、时间、变更内容
- 提供审计日志查询 API

#### 4.3 请求链路追踪

**实现**：
- 中间件生成 `request_id`（已实现）
- 所有下游调用传递 `request_id`
- 日志中统一包含 `request_id`

### 批次 5：测试与 CI/CD

#### 5.1 测试覆盖提升

**实现**：
- API 单元测试（使用 `TestClient`）
- 认证流程测试
- 权限控制测试
- 前端组件测试（Vitest + Vue Test Utils）

#### 5.2 GitHub Actions CI/CD

**实现**：
- `.github/workflows/ci.yml` — 代码检查、测试
- `.github/workflows/docker.yml` — 构建并推送镜像
- 代码质量检查（ruff、black、mypy）

---

## 3. 实施优先级

```
批次 1: 安全加固（Critical）
  ├── 1.1 JWT Secret 自动生成
  ├── 1.2 API 统一认证保护
  ├── 1.3 API 限流
  └── 1.4 CORS 收紧

批次 2: 基础设施（High）
  ├── 2.1 Alembic 迁移
  ├── 2.2 Docker 安全加固
  └── 2.3 健康检查扩展

批次 3: 前端鲁棒性（High）
  ├── 3.1 路由权限检查
  ├── 3.2 API 错误处理
  └── 3.3 状态持久化

批次 4: 可观测性（Medium）
  ├── 4.1 结构化日志
  ├── 4.2 审计日志集成
  └── 4.3 链路追踪完善

批次 5: 测试与 CI/CD（Medium）
  ├── 5.1 测试覆盖
  └── 5.2 CI/CD 流水线
```

---

## 4. 验收标准

- [ ] 所有 API（除公开路由）都需要有效 JWT Token
- [ ] 暴力破解登录会被限流（5 次/分钟）
- [ ] 数据库模型变更可通过 Alembic 迁移
- [ ] Docker 镜像以非 root 用户运行
- [ ] 前端无权限用户无法访问管理页面
- [ ] 所有错误都有友好提示，不暴露内部信息
- [ ] 日志包含 request_id，可追踪完整请求链路
- [ ] CI 流水线自动运行测试和代码检查
