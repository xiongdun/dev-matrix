# DevMatrix + claude-agent-sdk 集成开发计划

## 现状分析

### 已有代码
- ✅ `app/agents/base.py` — BaseAgent 集成了 SDK (sdk_query / sdk_query_with_tools)
- ✅ `app/api/workbench.py` — Workbench 对话集成 SDK + ToolExecutor
- ✅ `app/tools/executor.py` — 工具注册表 (Read/Search/Write/Edit/Bash)
- ✅ `app/api/settings.py` — 配置项 (claude_sdk_enabled, claude_sdk_session_id)
- ✅ 前端 LLM 设置页面已有 SDK 开关

### SDK API 验证
- ✅ `query(prompt, options)` — 匹配现有代码
- ✅ `ClaudeAgentOptions(system_prompt, max_turns, session_id, allowed_tools)` — 匹配
- ✅ `AssistantMessage, TextBlock, ToolUseBlock, ToolResultBlock` — 全部可用

## 需要完成的工作

### Phase 1: 配置与启动 (30 min)
1. **配置 ANTHROPIC_API_KEY**
   - 在 `.env` 中设置真实的 Anthropic API Key
   - 或通过前端 LLM 设置页面配置

2. **启用 SDK**
   - 数据库中 `claude_sdk_enabled` 设为 `true`
   - 可通过前端设置页面或 API 直接修改

3. **启动服务**
   - 后端: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - 前端: `cd frontend && npx vite --host 0.0.0.0 --port 3000`

### Phase 2: 验证 Agent 工作流 (1 hr)
4. **验证 BaseAgent.sdk_query()**
   - 测试 BusinessAnalyst Agent 调用 SDK 生成需求分析
   - 验证 TextBlock / ToolUseBlock 消息处理
   - 检查 Proposal 生成和验证流程

5. **验证其他 Agent**
   - ArchitectAgent — 代码影响分析
   - DeveloperAgent — 代码补丁生成
   - CodeReviewerAgent — AI 代码审查

### Phase 3: 验证 Workbench 对话 (1 hr)
6. **验证 Workbench SDK 集成**
   - 测试对话消息发送和 AI 回复
   - 验证工具调用 (Read/Search/Write/Edit/Bash)
   - 检查 tool_calls_log 记录

7. **修复兼容性问题** (如有)
   - SDK API 变更适配
   - 工具结果反馈机制
   - 错误处理和 fallback

### Phase 4: 端到端测试 (30 min)
8. **完整工作流测试**
   - 创建项目 → 输入需求
   - Agent 工作流自动执行 (BA → PM → Architect → Developer → QA → Reviewer)
   - 人工审批流程
   - Workbench 对话交互

## 风险与依赖
- **必须**: 有效的 Anthropic API Key (claude-3-opus 或 claude-3-sonnet 访问权限)
- **可选**: Temporal 服务 (工作流引擎, Docker 启动)
- **可选**: Redis (缓存, 非必须)

## 产出物
- 可运行的 DevMatrix 服务 (后端 + 前端)
- 验证报告: SDK 集成状态、已知问题、改进建议
