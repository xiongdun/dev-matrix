# DevMatrix 用户记忆系统增强需求文档

## 一、目标

在现有 `user/{user_id}/` 目录下新增三个维度，形成完整的用户级 Agent 配置体系：

```
user/
├── 1/                              # user_id=1 (admin)
│   ├── profile.md                  # [已有] 用户画像（偏好设置）
│   ├── memory.md                   # [已有] 用户记忆（纠正/反馈/学习）
│   ├── soul.md                     # [新增] AI 人设 + 用户画像
│   ├── skill/                      # [新增] 用户自定义技能
│   │   ├── code-review.md          #   技能定义文件
│   │   └── pr-generator.md
│   ├── mcp/                        # [新增] 用户 MCP 服务器配置
│   │   ├── github.md               #   MCP 服务器定义
│   │   └── jira.md
│   └── projects/                   # [已有] 项目记忆
│       └── mock-proj-001.md
├── 2/                              # user_id=2
│   └── ...
└── _shared/                        # [已有] Agent 共享记忆
    └── business_analyst.md
```

---

## 二、soul.md — AI 人设 + 用户画像

### 2.1 定位

soul.md 是用户与 AI 交互的"灵魂文件"，包含两个部分：

| 部分 | 作用 | 示例 |
|------|------|------|
| **AI 人设** | 告诉 AI "你应该怎么为我工作" | 角色定位、沟通风格、输出偏好 |
| **用户画像** | 告诉 AI "我是谁" | 职位、技术栈、领域知识、编码风格 |

### 2.2 文件格式

```markdown
# Soul

## AI 人设

- **角色**: 全栈开发助手，专注于 Python/Vue 项目
- **风格**: 简洁直接，不要废话，直接给代码
- **输出偏好**: Markdown 格式，代码块带语言标识
- **禁止事项**: 不要重复已知信息，不要过度解释

## 用户画像

- **职位**: 高级全栈工程师
- **技术栈**: Python, FastAPI, Vue 3, TypeScript, PostgreSQL
- **领域**: 企业级 SaaS、AI 应用开发
- **编码风格**:
  - Python: PEP 8, type hints, Google docstring
  - Vue: Composition API, script setup
- **经验水平**: 高级（不需要解释基础概念）

## 项目上下文

- **当前项目**: DevMatrix — AI 多角色协作开发平台
- **技术选型**: FastAPI + Vue 3 + claude-agent-sdk
- **架构模式**: 六层架构（执行层→审批层→智能体层→代码智能层→状态层→工作流层）
```

### 2.3 注入方式

soul.md 的内容注入到 system prompt 的最前面：

```
{soul.md 内容}

---

You are a {agent_role} agent working on the '{stage_name}' stage.
{记忆上下文}
```

---

## 三、skill/ — 用户自定义技能

### 3.1 定位

用户可以定义自己的技能文件，这些技能会被 Agent 加载和使用。技能是 Markdown 格式的指令文件，告诉 Agent "遇到某种情况应该怎么做"。

### 3.2 文件格式

每个技能一个 .md 文件：

```markdown
# code-review

## 描述
对代码变更进行审查，关注安全性、性能和可维护性。

## 触发条件
- 用户提交代码 diff
- 用户请求代码审查

## 执行步骤

1. 读取 diff 内容
2. 检查以下维度：
   - 安全漏洞（SQL 注入、XSS、硬编码密钥）
   - 性能问题（N+1 查询、内存泄漏）
   - 代码风格（命名规范、函数长度）
   - 测试覆盖（是否有对应测试）
3. 生成审查报告，包含：
   - 评分（0-100）
   - 问题列表（严重程度 + 位置 + 建议）
   - 改进建议

## 输出格式

```json
{
  "score": 85,
  "issues": [
    {"severity": "high", "file": "app/api/auth.py", "line": 42, "message": "..."}
  ],
  "suggestions": ["..."]
}
```

## 约束
- 只审查用户指定的文件
- 不要修改代码，只提供建议
```

### 3.3 技能加载

Agent 启动时扫描 `user/{user_id}/skill/*.md`，将技能指令注入到 system prompt：

```
## 可用技能

### code-review
对代码变更进行审查...
（技能完整内容）
```

### 3.4 技能优先级

```
用户自定义技能 (user/{id}/skill/) > Agent 共享技能 (_shared/) > 系统内置技能 (app/skills/)
```

---

## 四、mcp/ — 用户 MCP 服务器配置

### 4.1 定位

MCP (Model Context Protocol) 服务器配置，让用户可以连接外部工具和服务（GitHub、Jira、数据库等）。

### 4.2 文件格式

每个 MCP 服务器一个 .md 文件：

```markdown
# github-mcp

## 服务器信息

- **类型**: stdio
- **命令**: npx -y @modelcontextprotocol/server-github
- **描述**: GitHub 仓库操作（issues、PR、文件读写）

## 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| GITHUB_TOKEN | GitHub Personal Access Token | 是 |
| GITHUB_OWNER | 默认仓库所有者 | 否 |

## 可用工具

| 工具 | 描述 |
|------|------|
| search_repositories | 搜索仓库 |
| create_issue | 创建 Issue |
| create_pull_request | 创建 PR |
| get_file_contents | 读取文件内容 |

## 使用场景

- 代码审查时自动获取 PR diff
- 创建 Issue 跟踪任务
- 读取远程仓库文件进行分析
```

### 4.3 配置注入

MCP 配置转换为 `ClaudeAgentOptions.mcp_servers` 参数：

```python
mcp_servers = [
    {
        "name": "github-mcp",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_TOKEN": "..."}
    }
]
```

### 4.4 环境变量安全

- 敏感变量（Token、密码）从环境变量或密钥管理系统读取
- 不在 .md 文件中存储实际值，只声明变量名
- 实际值通过 `.env` 或 `SystemSecretModel` 注入

---

## 五、实施计划

| 阶段 | 内容 | 预估 |
|------|------|------|
| Phase 1 | soul.md 解析 + 注入 system prompt | 1h |
| Phase 2 | skill/ 目录扫描 + 技能注入 | 1.5h |
| Phase 3 | mcp/ 配置解析 + SDK 注入 | 1.5h |
| Phase 4 | API 端点（CRUD） + 前端页面 | 2h |

---

## 六、验收标准

- [ ] soul.md 内容注入到 system prompt 最前面
- [ ] skill/ 下的 .md 文件被 Agent 自动加载
- [ ] mcp/ 下的配置被解析并传递给 claude-agent-sdk
- [ ] 不同用户登录看到各自的 soul/skill/mcp
- [ ] 敏感信息（Token）不在 .md 文件中明文存储
