# Workspace — 用户记忆系统

## 目录说明

此目录是 DevMatrix 的**用户级记忆系统**，按 `user_id` 隔离存储每个用户的个性化配置、记忆和 Agent 上下文。

## 目录结构

```
workspace/
└── users/
    ├── {user_id}/                # 按用户 ID 隔离
    │   ├── profile.md            # 用户偏好设置
    │   ├── memory.md             # 用户记忆（纠正/反馈/学习）
    │   ├── soul.md               # AI 人设 + 用户画像
    │   ├── skill/                # 用户自定义技能
    │   │   └── *.md
    │   ├── mcp/                  # MCP 服务器配置
    │   │   └── *.md
    │   └── projects/             # 项目记忆
    │       └── {project_id}.md
    └── _shared/                  # Agent 共享记忆（跨用户）
        └── {agent_role}.md
```

## 文件格式规范

所有文件均为 **Markdown** 格式。

### profile.md — 用户偏好

```markdown
# 用户画像

- **用户名**: admin
- **昵称**: 管理员

## 偏好设置

| 项目 | 值 |
|------|-----|
| 语言 | zh |
| 沟通风格 | concise |
```

**解析规则**：
- `## 偏好设置` 下的表格解析为 `preferences` 字典
- `## 交互模式` 下的表格解析为 `patterns` 字典
- `- **key**: value` 解析为基础信息

### memory.md — 用户记忆

```markdown
# 用户记忆

## 纠正

- **不要重复发送请求** — 原因是 session_id 复用
  - 置信度: 1.0
  - 来源: user_feedback
  - 时间: 2026-06-04

## 偏好

- **输出格式** — 用户希望 Markdown 格式
```

**解析规则**：
- `## 纠正` / `## 偏好` / `## 反馈` 为分类标题
- `- **key** — value` 为记忆条目
- 子属性 `置信度` / `来源` / `时间` 附加到条目

### soul.md — AI 人设 + 用户画像

```markdown
# Soul

## AI 人设
- **角色**: 全栈开发助手
- **风格**: 简洁直接

## 用户画像
- **职位**: 高级全栈工程师
- **技术栈**: Python, FastAPI, Vue 3

## 项目上下文
- **当前项目**: DevMatrix
```

**注入位置**：system prompt 最前面

### skill/*.md — 自定义技能

```markdown
# code-review

## 描述
对代码变更进行审查

## 触发条件
- 用户提交代码 diff

## 执行步骤
1. 读取 diff 内容
2. 检查安全漏洞

## 约束
- 只审查用户指定的文件
```

**解析规则**：
- `## 描述` → description
- `## 触发条件` → triggers 列表
- `## 执行步骤` → steps 列表
- `## 约束` → constraints 列表

### mcp/*.md — MCP 服务器配置

```markdown
# github-mcp

## 服务器信息
- **类型**: stdio
- **命令**: npx -y @modelcontextprotocol/server-github

## 环境变量
| 变量 | 说明 | 必填 |
|------|------|------|
| GITHUB_TOKEN | GitHub Token | 是 |

## 可用工具
| 工具 | 描述 |
|------|------|
| search_repositories | 搜索仓库 |
```

**解析规则**：
- `## 服务器信息` 下的 `- **key**: value` 解析为服务器配置
- `## 环境变量` 表格解析为 `env_vars`
- `## 可用工具` 表格解析为 `tools`
- 实际环境变量值从 `os.environ` 读取，不在 .md 中存储

### projects/{project_id}.md — 项目记忆

```markdown
# 项目记忆 — mock-proj-001

## 项目上下文
- **描述**: 用户登录系统

## Agent 决策
- business_analyst: 确认需求范围
  - 审批人: admin

## 用户反馈
- 用户希望支持多因素认证
```

### _shared/{agent_role}.md — Agent 共享记忆

```markdown
# Agent 共享记忆 — business_analyst

## 角色知识
- **需求分析模板**: 标准需求分析应包含...
  - 来源: builtin

## 常见错误
- **过度分析**: 简单需求不需要过多分析
  - 频率: 3

## 成功模式
- **结构化输出**: 表格和分层标题更易被接受
  - 置信度: 0.9
```

## 记忆注入顺序

注入到 Agent 的 system prompt 中：

```
{soul.md}                    ← AI 人设 + 用户画像（最前面）
{agent_role 定义}             ← "You are a xxx agent..."
{memory.md 高置信度条目}       ← 用户纠正/偏好/反馈
{_shared/{agent_role}.md}    ← Agent 知识/避免错误/成功模式
{projects/{project_id}.md}   ← 项目决策/反馈
```

## 核心函数

| 函数 | 文件 | 说明 |
|------|------|------|
| `UserMemoryManager(user_id)` | manager.py | 用户记忆读写 |
| `AgentMemoryManager(agent_role)` | manager.py | Agent 共享记忆读写 |
| `build_memory_prompt(user_id, agent_role, project_id)` | manager.py | 组装完整记忆上下文 |
| `get_soul_prompt(user_id)` | manager.py | 读取 soul.md |
| `get_skills_prompt(user_id)` | manager.py | 扫描 skill/*.md |
| `build_mcp_options(user_id)` | manager.py | 转换 MCP 配置为 SDK 格式 |

## API 端点

| 端点 | 说明 |
|------|------|
| `GET /api/users/{id}/workspace` | 获取完整 workspace 数据 |
| `GET /api/users/{id}/workspace/soul` | 获取 soul.md |
| `GET /api/users/{id}/workspace/memory` | 获取记忆 |
| `GET /api/users/{id}/workspace/skills` | 获取技能列表 |
| `GET /api/users/{id}/workspace/mcp` | 获取 MCP 配置 |
| `GET /api/users/{id}/workspace/projects` | 获取项目记忆 |
| `GET /api/memory/memories` | 当前用户记忆 CRUD |
| `GET /api/memory/profile` | 当前用户画像 CRUD |

## 注意事项

1. **所有文件为 Markdown 格式**，不要使用 YAML/JSON
2. **MCP 环境变量**不在 .md 中存储实际值，从 `os.environ` 读取
3. **记忆置信度**低于 0.8 的条目不会注入到 system prompt
4. **_shared/** 目录下的记忆对所有用户生效
5. **解析器**使用正则匹配，格式必须严格遵循上述规范
