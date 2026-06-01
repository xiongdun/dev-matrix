# DevMatrix RBAC 用户管理系统设计文档

## 1. 概述

### 1.1 背景
DevMatrix 目前没有任何用户管理系统。所有操作无需登录即可执行，这在生产环境中存在严重的安全和权限控制问题。随着系统功能日益丰富（Agent 管理、工作流编排、代码审查、任务管理等），需要一套完整的 RBAC（基于角色的访问控制）用户管理系统。

### 1.2 目标
- 实现用户登录认证（用户名+密码，JWT Token，预留 SSO 扩展接口）
- 实现角色管理，角色可关联可用 Agent
- 实现菜单权限控制（按钮级 + 数据级）
- 现有所有菜单统一纳入权限控制

### 1.3 范围
| 包含 | 不包含 |
|------|--------|
| 用户管理（CRUD） | SSO/LDAP/OAuth2 具体实现（预留接口） |
| 角色管理（CRUD + Agent 关联） | 审计日志（后续迭代） |
| 菜单管理（动态菜单 + 按钮权限） | 多租户 |
| 数据权限（项目/任务范围控制） | 组织架构（部门树） |
| JWT 认证 + 登录/登出 | 短信/邮箱验证码 |

---

## 2. 术语定义

| 术语 | 定义 |
|------|------|
| **用户 (User)** | 系统的登录账号，可分配一个或多个角色 |
| **角色 (Role)** | 权限的集合，定义用户能做什么。角色关联可用 Agent |
| **菜单 (Menu)** | 系统导航菜单项，支持父子层级 |
| **权限 (Permission)** | 对菜单/按钮的访问许可，格式为 `资源:操作`，如 `project:create` |
| **Agent 权限** | 角色可使用的 Agent 列表，控制用户在流程编排和工作台中能调用哪些 Agent |
| **数据权限** | 控制用户能看到哪些数据（全部 / 本部门 / 仅自己） |

---

## 3. 数据库设计

### 3.1 实体关系图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    User     │◄───►│  UserRole   │◄───►│    Role     │
│  用户表      │  M:N │  用户角色关联 │  M:N │  角色表      │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                          ┌────────────────────┼────────────────────┐
                          │                    │                    │
                          ▼                    ▼                    ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │  RoleMenu   │    │  RoleAgent  │    │ RolePermission│
                   │ 角色菜单关联 │    │ 角色Agent关联│    │  角色权限关联  │
                   └─────────────┘    └─────────────┘    └─────────────┘
                          │                    │                    │
                          ▼                    ▼                    ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │    Menu     │    │    Agent    │    │  Permission │
                   │  菜单表      │    │  (已有注册表) │    │  权限表      │
                   └─────────────┘    └─────────────┘    └─────────────┘
```

### 3.2 表结构

#### 3.2.1 `users` — 用户表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| username | String(50) UNIQUE | 用户名 |
| password_hash | String(255) | 密码哈希（bcrypt） |
| nickname | String(50) | 昵称 |
| email | String(100) | 邮箱 |
| avatar | String(255) | 头像 URL |
| status | String(20) | 状态: active/disabled |
| data_scope | String(20) | 数据权限范围: all/dept/self |
| dept_id | Integer FK | 部门 ID（预留） |
| last_login_at | DateTime | 最后登录时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

#### 3.2.2 `roles` — 角色表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| name | String(50) UNIQUE | 角色标识（如 admin, pm, developer） |
| display_name | String(50) | 显示名称（如 管理员, 项目经理） |
| description | String(255) | 描述 |
| data_scope | String(20) | 默认数据权限: all/dept/self |
| is_system | Boolean | 是否系统内置角色（不可删除） |
| status | String(20) | 状态: active/disabled |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

#### 3.2.3 `user_roles` — 用户角色关联表

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | Integer FK | 用户 ID |
| role_id | Integer FK | 角色 ID |
| PK | (user_id, role_id) | 联合主键 |

#### 3.2.4 `menus` — 菜单表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| name | String(50) | 菜单标识（如 dashboard, projects） |
| title | String(50) | 显示标题（i18n key） |
| path | String(100) | 路由路径 |
| icon | String(50) | 图标名称 |
| parent_id | Integer FK | 父菜单 ID（NULL 表示顶级） |
| sort_order | Integer | 排序 |
| menu_type | String(20) | 类型: directory/page/button |
| permission | String(100) | 权限标识（如 project:create） |
| component | String(100) | 前端组件路径 |
| is_visible | Boolean | 是否显示在菜单中 |
| status | String(20) | 状态: active/disabled |

#### 3.2.5 `role_menus` — 角色菜单关联表

| 字段 | 类型 | 说明 |
|------|------|------|
| role_id | Integer FK | 角色 ID |
| menu_id | Integer FK | 菜单 ID |
| PK | (role_id, menu_id) | 联合主键 |

#### 3.2.6 `role_agents` — 角色 Agent 关联表

| 字段 | 类型 | 说明 |
|------|------|------|
| role_id | Integer FK | 角色 ID |
| agent_name | String(50) | Agent 注册名称 |
| PK | (role_id, agent_name) | 联合主键 |

### 3.3 预置数据

#### 预置角色

| 角色标识 | 显示名称 | 数据权限 | 说明 |
|----------|----------|----------|------|
| super_admin | 超级管理员 | all | 拥有所有权限，不可删除 |
| admin | 系统管理员 | all | 管理用户、角色、菜单，可使用所有 Agent |
| project_manager | 项目经理 | all | 管理项目、工作流，可使用所有 Agent |
| developer | 开发工程师 | self | 开发项目、查看代码审查，可使用 developer/qa/code_reviewer |
| tester | 测试工程师 | self | 查看项目、执行测试，可使用 qa/code_reviewer |
| viewer | 访客 | self | 只读权限，只能查看不能操作 |

#### 预置菜单（与现有菜单对齐）

| 菜单标识 | 标题 | 路径 | 父级 | 类型 | 权限标识 |
|----------|------|------|------|------|----------|
| dashboard | 仪表盘 | / | - | page | dashboard:view |
| workbench | 工作台 | /workbench | - | page | workbench:view |
| projects | 项目管理 | /projects | - | page | project:view |
| project:create | 新建项目 | - | projects | button | project:create |
| project:edit | 编辑项目 | - | projects | button | project:edit |
| project:delete | 删除项目 | - | projects | button | project:delete |
| task_management | 任务管理 | /tasks | - | directory | task:view |
| my_tasks | 我的任务 | /tasks/my | task_management | page | task:view |
| task_board | 任务看板 | /tasks/board | task_management | page | task:view |
| task:create | 新建任务 | - | task_management | button | task:create |
| task:edit | 编辑任务 | - | task_management | button | task:edit |
| task:delete | 删除任务 | - | task_management | button | task:delete |
| scheduled_tasks | 定时任务 | /scheduled-tasks | - | page | scheduled_task:view |
| scheduled_task:create | 新建定时任务 | - | scheduled_tasks | button | scheduled_task:create |
| scheduled_task:edit | 编辑定时任务 | - | scheduled_tasks | button | scheduled_task:edit |
| scheduled_task:delete | 删除定时任务 | - | scheduled_tasks | button | scheduled_task:delete |
| agents | 智能体管理 | /agents | - | page | agent:view |
| agent:mount | 挂载技能 | - | agents | button | agent:mount |
| agent:unmount | 卸载技能 | - | agents | button | agent:unmount |
| skills | 技能管理 | /skills | - | page | skill:view |
| skill:upload | 上传技能 | - | skills | button | skill:upload |
| code_reviews | 代码审查 | /code-reviews | - | page | code_review:view |
| code_review:create | 创建审查 | - | code_reviews | button | code_review:create |
| code_review:rerun | 重新审查 | - | code_reviews | button | code_review:rerun |
| workflow | 流程管理 | /workflow | - | directory | workflow:view |
| workflow_editor | 流程编排 | /workflow/editor | workflow | page | workflow:edit |
| workflow_list | 流程列表 | /workflow/list | workflow | page | workflow:view |
| workflow_instances | 流程实例 | /workflow/instances | workflow | page | workflow_instance:view |
| workflow:create | 新建流程 | - | workflow | button | workflow:create |
| workflow:enable | 启用流程 | - | workflow | button | workflow:enable |
| workflow:archive | 归档流程 | - | workflow | button | workflow:archive |
| settings | 设置 | /settings | - | directory | setting:view |
| settings_system | 系统设置 | /settings/system | settings | page | setting:system |
| settings_llm | LLM 设置 | /settings/llm | settings | page | setting:llm |
| settings_database | 数据库设置 | /settings/database | settings | page | setting:database |
| settings_security | 安全设置 | /settings/security | settings | page | setting:security |
| settings_about | 关于 | /settings/about | settings | page | setting:about |
| user_management | 用户管理 | /users | - | page | user:manage |
| role_management | 角色管理 | /roles | - | page | role:manage |
| menu_management | 菜单管理 | /menus | - | page | menu:manage |

---

## 4. 后端 API 设计

### 4.1 认证模块 (`/api/auth`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/auth/login` | 用户登录 | `{username, password}` | `{token, user, expires_at}` |
| POST | `/auth/logout` | 用户登出 | - | `{success}` |
| GET | `/auth/me` | 获取当前用户信息 | - | `{id, username, nickname, roles, permissions, agents}` |
| POST | `/auth/refresh` | 刷新 Token | - | `{token, expires_at}` |
| POST | `/auth/password` | 修改密码 | `{old_password, new_password}` | `{success}` |

### 4.2 用户管理 (`/api/users`)

| 方法 | 路径 | 说明 | 权限要求 |
|------|------|------|----------|
| GET | `/users` | 用户列表（分页 + 搜索） | user:manage |
| POST | `/users` | 创建用户 | user:manage |
| GET | `/users/{id}` | 用户详情 | user:manage 或 本人 |
| PUT | `/users/{id}` | 更新用户 | user:manage |
| DELETE | `/users/{id}` | 删除用户 | user:manage |
| PUT | `/users/{id}/status` | 启用/禁用用户 | user:manage |
| PUT | `/users/{id}/roles` | 分配角色 | user:manage |

### 4.3 角色管理 (`/api/roles`)

| 方法 | 路径 | 说明 | 权限要求 |
|------|------|------|----------|
| GET | `/roles` | 角色列表 | role:manage 或 任意（下拉选择） |
| POST | `/roles` | 创建角色 | role:manage |
| GET | `/roles/{id}` | 角色详情（含菜单、Agent） | role:manage |
| PUT | `/roles/{id}` | 更新角色 | role:manage |
| DELETE | `/roles/{id}` | 删除角色 | role:manage |
| GET | `/roles/{id}/menus` | 角色菜单 | role:manage |
| PUT | `/roles/{id}/menus` | 分配菜单 | role:manage |
| GET | `/roles/{id}/agents` | 角色 Agent | role:manage |
| PUT | `/roles/{id}/agents` | 分配 Agent | role:manage |

### 4.4 菜单管理 (`/api/menus`)

| 方法 | 路径 | 说明 | 权限要求 |
|------|------|------|----------|
| GET | `/menus` | 菜单树 | menu:manage |
| POST | `/menus` | 创建菜单 | menu:manage |
| GET | `/menus/{id}` | 菜单详情 | menu:manage |
| PUT | `/menus/{id}` | 更新菜单 | menu:manage |
| DELETE | `/menus/{id}` | 删除菜单 | menu:manage |
| GET | `/menus/tree` | 菜单树（前端用） | 登录即可 |
| GET | `/menus/my` | 当前用户菜单 | 登录即可 |

### 4.5 数据权限控制

数据权限通过 SQL 查询时动态添加过滤条件实现：

```python
# 数据权限范围
class DataScope:
    ALL = "all"      # 全部数据
    DEPT = "dept"    # 本部门数据（预留）
    SELF = "self"    # 仅自己的数据

def apply_data_scope(query, user, model):
    """根据用户数据权限范围过滤查询"""
    scope = user.get_effective_data_scope()
    
    if scope == DataScope.ALL:
        return query
    elif scope == DataScope.SELF:
        # 根据模型类型添加不同的过滤条件
        if hasattr(model, 'owner'):
            return query.filter(model.owner == user.username)
        elif hasattr(model, 'created_by'):
            return query.filter(model.created_by == user.id)
        elif hasattr(model, 'assignee_id'):
            return query.filter(model.assignee_id == user.id)
    
    return query
```

---

## 5. 前端设计

### 5.1 登录页面

- 路径：`/login`
- 布局：居中卡片，深色背景
- 元素：用户名输入框、密码输入框、登录按钮、记住我选项
- 交互：登录成功后跳转到原目标页或仪表盘，Token 存入 localStorage

### 5.2 用户管理页面 (`/users`)

- 表格：用户名、昵称、角色、状态、最后登录、操作
- 操作按钮：编辑、禁用/启用、重置密码、删除
- 弹窗表单：创建/编辑用户（用户名、昵称、邮箱、密码、角色选择、数据权限）

### 5.3 角色管理页面 (`/roles`)

- 表格：角色名、显示名、数据权限、状态、操作
- 操作按钮：编辑、分配菜单、分配 Agent、删除
- 弹窗表单：
  - 基本信息：角色名、显示名、描述、数据权限
  - 菜单权限：树形选择器，勾选菜单和按钮
  - Agent 权限：多选框，选择可用 Agent

### 5.4 菜单管理页面 (`/menus`)

- 树形表格：展示菜单层级
- 操作按钮：新增、编辑、删除
- 弹窗表单：菜单名称、标题、路径、图标、父级、类型、权限标识、排序

### 5.5 权限控制实现

#### 5.5.1 路由守卫

```typescript
// router.ts 添加全局守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.path === '/login') {
    token ? next('/') : next()
    return
  }
  
  if (!token) {
    next('/login')
    return
  }
  
  // 检查页面权限
  const userStore = useUserStore()
  if (!userStore.hasPermission(to.meta.permission as string)) {
    next('/403')
    return
  }
  
  next()
})
```

#### 5.5.2 按钮级权限指令

```typescript
// 自定义指令 v-permission
<button v-permission="'project:create'">新建项目</button>

// 实现：检查用户 permissions 数组是否包含该权限
```

#### 5.5.3 动态菜单

```typescript
// 登录后获取用户菜单树
const menus = await api.getMyMenus()
// 动态渲染 Sidebar，只显示有权限的菜单
```

#### 5.5.4 Agent 权限过滤

```typescript
// 智能体管理页面，只显示有权限的 Agent
const allowedAgents = computed(() => {
  return allAgents.value.filter(a => userStore.hasAgent(a.name))
})

// 流程编排页面，只显示有权限的 Agent 节点
const allowedAgentNodes = computed(() => {
  return allAgentNodes.value.filter(n => userStore.hasAgent(n.agentName))
})
```

---

## 6. 安全设计

### 6.1 密码安全
- 使用 bcrypt 哈希存储密码（cost factor = 12）
- 密码最小长度 8 位，要求包含字母和数字
- 登录失败 5 次后锁定账号 30 分钟

### 6.2 JWT Token
- Access Token：有效期 2 小时
- Refresh Token：有效期 7 天
- Token 包含：user_id, username, roles, permissions, agents
- 使用 HS256 签名

### 6.3 API 保护
- 所有管理 API（用户/角色/菜单）需要 `user:manage` / `role:manage` / `menu:manage` 权限
- 普通 API 需要登录（JWT 验证）
- 数据权限在 Service 层通过装饰器实现

---

## 7. 实现计划

### Phase 1：核心认证（高优先级）
1. 数据库模型（users, roles, user_roles, menus, role_menus, role_agents）
2. 密码哈希工具 + JWT 工具
3. 登录/登出 API
4. 登录页面
5. 路由守卫 + Token 拦截器

### Phase 2：用户管理
6. 用户 CRUD API
7. 用户管理页面
8. 当前用户信息接口（/auth/me）

### Phase 3：角色与权限
9. 角色 CRUD API
10. 角色-菜单关联 API
11. 角色-Agent 关联 API
12. 角色管理页面（含菜单树、Agent 多选）

### Phase 4：菜单管理
13. 菜单 CRUD API
14. 菜单管理页面（树形表格）
15. 动态菜单接口（/menus/my）
16. 前端动态菜单渲染

### Phase 5：数据权限与完善
17. 数据权限装饰器
18. 项目/任务列表添加数据权限过滤
19. 按钮级权限指令
20. 403 页面
21. 国际化

---

## 8. 与现有系统的集成

### 8.1 现有菜单改造
- `Sidebar.vue` 从静态 `navItems` 改为从后端 `/api/menus/my` 动态获取
- 保留当前菜单数据结构兼容（id, path, title, icon, children）
- 新增菜单管理页面可动态配置菜单

### 8.2 现有页面按钮改造
- 所有页面的"新增/编辑/删除"按钮添加 `v-permission` 指令
- 无权限时按钮隐藏或禁用

### 8.3 Agent 权限集成
- `AgentsPage.vue` 只显示当前用户有权限的 Agent
- `WorkflowEditorPage.vue` 的 Agent 节点选择器过滤无权限 Agent
- `WorkbenchPage.vue` 的任务列表按 Agent 权限过滤

### 8.4 数据权限集成
- `ProjectsPage.vue` 列表查询添加 `data_scope` 参数
- `MyTasksPage.vue` 已按用户过滤，保持现状
- `TaskBoardPage.vue` 按数据权限过滤可见任务

---

## 9. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 引入用户系统后现有功能需要大量改造 | 高 | 采用渐进式改造，先加认证层，再逐步加权限控制 |
| JWT Token 泄露 | 中 | Token 设置短有效期，支持后端强制失效 |
| 权限配置错误导致管理员无法登录 | 高 | 超级管理员角色不可编辑，预留数据库重置脚本 |
| 数据权限影响查询性能 | 中 | 数据权限过滤在 SQL 层实现，走索引 |

---

## 10. 附录

### 10.1 预置用户

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| admin | admin123 | super_admin | 超级管理员，首次登录后必须修改密码 |

### 10.2 现有菜单完整映射

```
仪表盘 (/)
工作台 (/workbench)
项目管理 (/projects)
  └── [按钮] 新建项目、编辑、删除、启动工作流
任务管理 (/tasks)
  ├── 我的任务 (/tasks/my)
  ├── 任务看板 (/tasks/board)
  └── [按钮] 新建任务、编辑、删除、移动
定时任务 (/scheduled-tasks)
  └── [按钮] 新建、编辑、删除、启用/禁用、立即执行
智能体管理 (/agents)
  └── [按钮] 挂载技能、卸载技能
技能管理 (/skills)
  └── [按钮] 上传技能
代码审查 (/code-reviews)
  └── [按钮] 创建审查、重新审查
流程管理 (/workflow)
  ├── 流程编排 (/workflow/editor)
  ├── 流程列表 (/workflow/list)
  │   └── [按钮] 新建、启用、归档、删除、创建实例
  └── 流程实例 (/workflow/instances)
设置 (/settings)
  ├── 系统设置 (/settings/system)
  ├── LLM 设置 (/settings/llm)
  ├── 数据库设置 (/settings/database)
  ├── 安全设置 (/settings/security)
  └── 关于 (/settings/about)
用户管理 (/users) [新增]
角色管理 (/roles) [新增]
菜单管理 (/menus) [新增]
```
