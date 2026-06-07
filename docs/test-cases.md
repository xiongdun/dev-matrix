# DevMatrix 功能性测试用例文档

## 概述

本文档定义了 DevMatrix 平台的 100 个功能性测试用例，覆盖所有核心模块。

## 测试环境

- **后端**: http://localhost:8000
- **前端**: http://localhost:3000
- **数据库**: SQLite (测试专用)
- **默认账号**: admin / admin123

---

## 一、认证与授权 (10 个)

| 编号 | 模块 | 测试用例 | 输入 | 预期结果 |
|------|------|----------|------|----------|
| TC-001 | 登录 | 正确用户名密码登录 | username=admin, password=admin123 | 返回 JWT token + 用户信息 |
| TC-002 | 登录 | 错误密码登录 | username=admin, password=wrong | 返回 401 错误 |
| TC-003 | 登录 | 不存在的用户登录 | username=nonexist, password=123 | 返回 401 错误 |
| TC-004 | 登录 | 缺少必填字段 | username=admin (无 password) | 返回 422 验证错误 |
| TC-005 | Token | 使用有效 token 访问受保护接口 | Authorization: Bearer {valid_token} | 返回 200 |
| TC-006 | Token | 使用过期 token | Authorization: Bearer {expired_token} | 返回 401 |
| TC-007 | Token | 无 token 访问受保护接口 | 无 Authorization header | 返回 401 |
| TC-008 | Token | 刷新 token | POST /api/auth/refresh | 返回新 token |
| TC-009 | 权限 | 无权限用户访问受限接口 | 普通用户访问 /api/users | 返回 403 |
| TC-010 | 登出 | 用户登出 | POST /api/auth/logout | 返回成功，token 失效 |

---

## 二、用户管理 (10 个)

| 编号 | 模块 | 测试用例 | 输入 | 预期结果 |
|------|------|----------|------|----------|
| TC-011 | 用户列表 | 获取用户列表 | GET /api/users | 返回用户数组 |
| TC-012 | 用户列表 | 按关键词搜索 | GET /api/users?keyword=admin | 返回匹配用户 |
| TC-013 | 用户列表 | 按状态筛选 | GET /api/users?status=active | 返回启用用户 |
| TC-014 | 创建用户 | 正常创建用户 | {username, password, nickname} | 返回新用户信息 |
| TC-015 | 创建用户 | 重复用户名创建 | username=已存在用户 | 返回 409 冲突 |
| TC-016 | 创建用户 | 密码太短 | password=123 | 返回 422 验证错误 |
| TC-017 | 用户详情 | 获取用户详情 | GET /api/users/{id} | 返回用户信息 |
| TC-018 | 更新用户 | 更新用户昵称 | PUT /api/users/{id} {nickname: "新昵称"} | 返回更新后用户 |
| TC-019 | 状态切换 | 禁用用户 | PUT /api/users/{id}/status?status=disabled | 用户状态变为 disabled |
| TC-020 | 删除用户 | 删除用户 | DELETE /api/users/{id} | 用户被删除 |

---

## 三、角色管理 (8 个)

| 编号 | 模块 | 测试用例 | 输入 | 预期结果 |
|------|------|----------|------|----------|
| TC-021 | 角色列表 | 获取角色列表 | GET /api/roles | 返回角色数组 |
| TC-022 | 创建角色 | 创建新角色 | {name, display_name} | 返回新角色 |
| TC-023 | 创建角色 | 重复角色名 | name=已存在角色 | 返回 409 冲突 |
| TC-024 | 角色详情 | 获取角色详情 | GET /api/roles/{id} | 返回角色信息 |
| TC-025 | 更新角色 | 修改角色名称 | PUT /api/roles/{id} | 返回更新后角色 |
| TC-026 | 删除角色 | 删除角色 | DELETE /api/roles/{id} | 角色被删除 |
| TC-027 | 角色权限 | 分配菜单权限 | POST /api/roles/{id}/menus | 权限生效 |
| TC-028 | 角色权限 | 分配 Agent 权限 | POST /api/roles/{id}/agents | Agent 可见 |

---

## 四、项目管理 (8 个)

| 编号 | 模块 | 测试用例 | 输入 | 预期结果 |
|------|------|----------|------|----------|
| TC-029 | 项目列表 | 获取项目列表 | GET /api/projects | 返回项目数组 |
| TC-030 | 项目列表 | 分页查询 | GET /api/projects?page=1&page_size=10 | 返回分页结果 |
| TC-031 | 创建项目 | 创建新项目 | {name, description, owner} | 返回新项目 |
| TC-032 | 项目详情 | 获取项目详情 | GET /api/projects/{id} | 返回项目信息 |
| TC-033 | 更新项目 | 更新项目状态 | PUT /api/projects/{id} {status: "in_progress"} | 状态更新 |
| TC-034 | 删除项目 | 删除项目 | DELETE /api/projects/{id} | 项目被删除 |
| TC-035 | 项目搜索 | 按名称搜索 | GET /api/projects?keyword=Alpha | 返回匹配项目 |
| TC-036 | 项目筛选 | 按优先级筛选 | GET /api/projects?priority=high | 返回高优先级项目 |

---

## 五、工作台对话 (12 个)

| 编号 | 模块 | 测试用例 | 输入 | 预期结果 |
|------|------|----------|------|----------|
| TC-037 | 任务列表 | 获取待办任务 | GET /api/workbench/tasks | 返回 pending 任务 |
| TC-038 | 任务列表 | 按角色筛选 | GET /api/workbench/tasks?role=business_analyst | 返回指定角色任务 |
| TC-039 | 任务详情 | 获取任务详情 | GET /api/workbench/tasks/{id} | 返回任务信息 |
| TC-040 | 对话 | 发送消息 (Direct LLM) | POST /chat {message, sdk: "direct_llm"} | 返回 AI 回复 |
| TC-041 | 对话 | 发送消息 (Claude Code) | POST /chat {message, sdk: "claude_code"} | 返回 AI 回复 |
| TC-042 | 对话 | 发送消息 (OpenAI Agents) | POST /chat {message, sdk: "openai_agents"} | 返回 AI 回复 |
| TC-043 | 对话 | 未选择 SDK | POST /chat {message} (无 sdk) | 默认使用 direct_llm |
| TC-044 | 对话 | 空消息 | POST /chat {message: ""} | 返回 422 验证错误 |
| TC-045 | 对话历史 | 获取对话历史 | GET /api/workbench/tasks/{id}/chat | 返回消息列表 |
| TC-046 | 审批 | 通过任务 | POST /tasks/{id}/approve | 状态变为 approved |
| TC-047 | 审批 | 打回任务 | POST /tasks/{id}/reject {comment} | 状态变为 rejected |
| TC-048 | 重试 | 重试任务 | POST /tasks/{id}/retry {feedback} | 状态变为 retrying |

---

## 六、SDK 管理 (6 个)

| 编号 | 模块 | 测试用例 | 输入 | 预期结果 |
|------|------|----------|------|----------|
| TC-049 | SDK 列表 | 获取可用 SDK | GET /api/workbench/sdks | 返回 SDK 列表 |
| TC-050 | SDK 可用性 | Claude Code SDK 可用性 | 检查 available 字段 | true (已安装) |
| TC-051 | SDK 可用性 | OpenAI Agents SDK 可用性 | 检查 available 字段 | true (已安装) |
| TC-052 | SDK 可用性 | Direct LLM 可用性 | 检查 available 字段 | true (始终可用) |
| TC-053 | SDK 切换 | 切换 SDK 后发消息 | 先选 Claude Code，再选 Direct LLM | 两种都能正常回复 |
| TC-054 | SDK 错误 | 未配置 API Key 时调用 OpenAI Agents | 无 OPENAI_API_KEY | 返回友好错误信息 |

---

## 七、记忆系统 (10 个)

| 编号 | 模块 | 测试用例 | 输入 | 预期结果 |
|------|------|----------|------|----------|
| TC-055 | 记忆列表 | 获取用户记忆 | GET /api/memory/memories | 返回记忆列表 |
| TC-056 | 添加记忆 | 添加一条记忆 | POST /api/memory/memories {type, key, value} | 记忆被保存 |
| TC-057 | 删除记忆 | 删除指定记忆 | DELETE /api/memory/memories/{key} | 记忆被删除 |
| TC-058 | 清空记忆 | 清空所有记忆 | DELETE /api/memory/memories | 所有记忆被清空 |
| TC-059 | 用户画像 | 获取用户画像 | GET /api/memory/profile | 返回 profile 数据 |
| TC-060 | 用户画像 | 更新用户偏好 | PUT /api/memory/profile {preferences} | 偏好被更新 |
| TC-061 | Agent 记忆 | 获取 Agent 共享记忆 | GET /api/memory/agents/{role}/memory | 返回 Agent 记忆 |
| TC-062 | Workspace | 获取完整 workspace | GET /api/users/{id}/workspace | 返回所有维度数据 |
| TC-063 | Workspace | 获取 soul.md | GET /api/users/{id}/workspace/soul | 返回 soul 内容 |
| TC-064 | Workspace | 获取技能列表 | GET /api/users/{id}/workspace/skills | 返回技能列表 |

---

## 八、系统设置 (8 个)

| 编号 | 模块 | 测试用例 | 输入 | 预期结果 |
|------|------|----------|------|----------|
| TC-065 | 设置列表 | 获取所有设置 | GET /api/settings | 返回配置列表 |
| TC-066 | 设置分类 | 按分类获取 | GET /api/settings?category=llm | 返回 LLM 配置 |
| TC-067 | 更新设置 | 更新单个配置 | PUT /api/settings {configs: {key: value}} | 配置被更新 |
| TC-068 | 初始化 | 初始化默认配置 | POST /api/settings/init | 缺失配置被创建 |
| TC-069 | LLM 设置 | 更新 LLM 提供商 | PUT /api/settings {llm_provider: "anthropic"} | 提供商更新 |
| TC-070 | LLM 设置 | 更新 API Key | PUT /api/settings {anthropic_api_key: "..."} | Key 被更新（脱敏存储） |
| TC-071 | SDK 设置 | 启用 Claude SDK | PUT /api/settings {claude_sdk_enabled: "true"} | SDK 启用 |
| TC-072 | 安全设置 | 获取安全配置 | GET /api/settings?category=security | 返回安全配置 |

---

## 九、工作流管理 (8 个)

| 编号 | 模块 | 测试用例 | 输入 | 预期结果 |
|------|------|----------|------|----------|
| TC-073 | 模板列表 | 获取工作流模板 | GET /api/workflow-config/templates | 返回模板列表 |
| TC-074 | 创建模板 | 创建工作流模板 | POST /api/workflow-config {name, flow_json} | 返回新模板 |
| TC-075 | 模板详情 | 获取模板详情 | GET /api/workflow-config/{id} | 返回模板信息 |
| TC-076 | 更新模板 | 更新模板描述 | PUT /api/workflow-config/{id} | 模板被更新 |
| TC-077 | 启动工作流 | 启动工作流实例 | POST /api/workflow/{project_id}/start | 返回实例 ID |
| TC-078 | 实例列表 | 获取运行中实例 | GET /api/workflow-instances | 返回实例列表 |
| TC-079 | 实例详情 | 获取实例详情 | GET /api/workflow-instances/{id} | 返回实例信息 |
| TC-080 | 删除模板 | 删除工作流模板 | DELETE /api/workflow-config/{id} | 模板被删除 |

---

## 十、代码审查 (5 个)

| 编号 | 模块 | 测试用例 | 输入 | 预期结果 |
|------|------|----------|------|----------|
| TC-081 | 审查列表 | 获取审查记录 | GET /api/code-reviews | 返回审查列表 |
| TC-082 | 创建审查 | 创建代码审查 | POST /api/code-reviews {task_id, diff} | 返回审查报告 |
| TC-083 | 审查详情 | 获取审查详情 | GET /api/code-reviews/{id} | 返回审查详情 |
| TC-084 | 重新审查 | 重新运行审查 | POST /api/code-reviews/{id}/rerun | 返回新审查结果 |
| TC-085 | 审查评分 | 验证评分范围 | 检查 score 字段 | 0-100 之间 |

---

## 十一、定时任务 (5 个)

| 编号 | 模块 | 测试用例 | 输入 | 预期结果 |
|------|------|----------|------|----------|
| TC-086 | 任务列表 | 获取定时任务 | GET /api/scheduled-tasks | 返回任务列表 |
| TC-087 | 创建任务 | 创建定时任务 | POST /api/scheduled-tasks {name, cron} | 返回新任务 |
| TC-088 | 启用/禁用 | 切换任务状态 | PUT /api/scheduled-tasks/{id}/toggle | 状态切换 |
| TC-089 | 立即执行 | 手动触发任务 | POST /api/scheduled-tasks/{id}/run | 任务被执行 |
| TC-090 | 执行历史 | 获取执行日志 | GET /api/scheduled-tasks/{id}/logs | 返回日志列表 |

---

## 十二、健康检查与审计 (5 个)

| 编号 | 模块 | 测试用例 | 输入 | 预期结果 |
|------|------|----------|------|----------|
| TC-091 | 健康检查 | 存活检查 | GET /health/live | 返回 {"status": "healthy"} |
| TC-092 | 健康检查 | 就绪检查 | GET /health/ready | 返回就绪状态 |
| TC-093 | 健康检查 | 详细健康信息 | GET /health | 返回各组件状态 |
| TC-094 | 审计日志 | 查询审计日志 | GET /api/audit/logs | 返回操作记录 |
| TC-095 | 审计日志 | 按操作类型筛选 | GET /api/audit/logs?action=login | 返回登录记录 |

---

## 十三、前端 UI (5 个)

| 编号 | 模块 | 测试用例 | 操作 | 预期结果 |
|------|------|----------|------|----------|
| TC-096 | 登录页 | 登录表单验证 | 空表单点击登录 | 显示必填提示 |
| TC-097 | 侧边栏 | 菜单导航 | 点击各菜单项 | 正确跳转到对应页面 |
| TC-098 | 工作台 | SDK 选择器 | 点击 SDK 下拉选择 | 显示可用 SDK 列表 |
| TC-099 | 用户详情 | 查看用户 workspace | 点击用户列表的"查看"按钮 | 显示用户详情页 |
| TC-100 | 主题切换 | 深色/浅色切换 | 点击主题切换按钮 | 界面主题正确切换 |

---

## 测试执行说明

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行指定模块
```bash
pytest tests/test_auth.py -v          # 认证测试
pytest tests/test_health.py -v        # 健康检查
pytest tests/test_workbench.py -v     # 工作台测试
```

### 生成覆盖率报告
```bash
pytest tests/ --cov=app --cov-report=html
```

---

## 优先级说明

| 优先级 | 用例范围 | 执行顺序 |
|--------|----------|----------|
| P0 | TC-001~010 (认证), TC-037~048 (工作台), TC-091~093 (健康检查) | 第一批 |
| P1 | TC-011~036 (用户/角色/项目), TC-049~064 (SDK/记忆) | 第二批 |
| P2 | TC-065~095 (设置/工作流/审查/定时/审计) | 第三批 |
| P3 | TC-096~100 (前端 UI) | 第四批 |
