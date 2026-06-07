# DevMatrix 项目概览

## 定位

多角色 AI 协作软件开发平台，通过状态驱动的工作流编排多个专业 Agent 协作完成软件开发生命周期。

## 技术栈

- 后端：Python 3.10+, FastAPI, SQLAlchemy 2.0
- 前端：Vue 3, TypeScript, Vite
- AI：claude-agent-sdk, Claude Code CLI
- LLM：小米 mimo-v2.5-pro (Anthropic 协议)

## 核心模块

| 模块 | 说明 |
|------|------|
| `app/agents/` | 7 个 AI Agent |
| `app/api/` | 25+ FastAPI 端点 |
| `app/memory/` | 记忆系统 |
| `app/llm/` | LLM 客户端 |
| `app/skills/` | 技能系统 |
| `app/workflow/` | 工作流引擎 |

## 服务端口

- 后端：8000
- 前端：3000
- 登录：admin / admin123
