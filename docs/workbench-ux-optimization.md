# DevMatrix 工作台体验优化需求文档

## 一、现状分析

### 当前架构
- **三栏布局**：左侧任务边栏 + 中间对话区 + 右侧操作面板
- **后端**：claude-agent-sdk（Claude Code CLI）+ FastAPI
- **前端**：Vue 3 + marked（Markdown 渲染）+ lucide 图标

### 核心痛点
1. **等待焦虑** — SDK 调用需要 10-30 秒才返回结果，期间只有"思考中"动画
2. **信息密度过高** — 工具调用卡片占大量空间，真正有用的回复被淹没
3. **交互生硬** — 缺少复制、重生成、换行等基础聊天功能
4. **代码体验差** — 代码块无语法高亮、无复制按钮
5. **操作反馈弱** — 审批/打回操作无确认、无成功提示

---

## 二、优化需求清单

### P0 — 核心体验（必须做）

#### 2.1 消息交互增强
| 编号 | 需求 | 描述 |
|------|------|------|
| UX-01 | Shift+Enter 换行 | 当前 Enter 直接发送，无法输入多行文本 |
| UX-02 | 消息复制按钮 | 每条 AI 回复右上角添加复制按钮，一键复制 Markdown 源码 |
| UX-03 | 重新生成按钮 | AI 回复不满意时，可点击重新生成（相同 prompt 重发） |
| UX-04 | 停止生成按钮 | 发送后显示停止按钮，允许中断长时间的 SDK 调用 |

#### 2.2 代码展示优化
| 编号 | 需求 | 描述 |
|------|------|------|
| UX-05 | 代码块语法高亮 | 使用 highlight.js 或 Shiki 对代码块进行语法高亮 |
| UX-06 | 代码块复制按钮 | 每个代码块右上角添加复制按钮 |
| UX-07 | 代码块语言标识 | 显示代码语言类型（python/javascript/bash 等） |

#### 2.3 工具调用折叠
| 编号 | 需求 | 描述 |
|------|------|------|
| UX-08 | 工具调用卡片折叠 | 默认折叠工具调用详情，只显示「🔧 Read config.py」摘要行 |
| UX-09 | 点击展开详情 | 点击工具卡片展开查看完整输入/输出/diff |
| UX-10 | 工具调用计数 | 当有多次工具调用时，显示「AI 使用了 5 个工具」摘要 |

---

### P1 — 流畅度提升（应该做）

#### 2.4 响应速度优化
| 编号 | 需求 | 描述 |
|------|------|------|
| UX-11 | 进度提示增强 | 思考中状态显示当前阶段：「正在分析代码库...」「正在读取文件...」 |
| UX-12 | 超时提示 | 超过 15 秒未响应时显示「AI 正在处理复杂任务，请耐心等待」 |
| UX-13 | 请求取消 | 点击停止按钮可取消正在进行的 HTTP 请求（AbortController） |

#### 2.5 对话管理
| 编号 | 需求 | 描述 |
|------|------|------|
| UX-14 | 清空对话 | 添加清空当前对话按钮（仅清前端，不删数据库） |
| UX-15 | 对话历史分页 | 加载历史消息时只加载最近 50 条，上拉加载更多 |
| UX-16 | 消息时间分组 | 相邻消息间隔 > 5 分钟时显示时间分隔线 |

#### 2.6 操作面板优化
| 编号 | 需求 | 描述 |
|------|------|------|
| UX-17 | 操作确认弹窗 | 审批/打回操作前显示确认弹窗，防止误操作 |
| UX-18 | 操作成功提示 | 操作完成后显示 Toast 提示「已通过」「已打回」 |
| UX-19 | 面板折叠 | 右侧操作面板可折叠，给对话区更多空间 |

---

### P2 — 体验打磨（可以做）

#### 2.7 边栏增强
| 编号 | 需求 | 描述 |
|------|------|------|
| UX-20 | 任务搜索 | 边栏顶部添加搜索框，按项目名/阶段过滤 |
| UX-21 | 状态筛选 | 按状态（待处理/已通过/已打回）筛选任务 |
| UX-22 | 未读标记 | 有新 AI 回复的任务显示未读圆点 |

#### 2.8 快捷键
| 编号 | 需求 | 描述 |
|------|------|------|
| UX-23 | Ctrl+Enter 发送 | 可选的发送快捷键（与 Enter 换行配合） |
| UX-24 | Esc 关闭弹窗 | Esc 关闭模型选择器、拒绝/重试输入框 |
| UX-25 | ↑ 编辑上一条 | 输入框为空时按 ↑ 编辑上一条发送的消息 |

#### 2.9 消息增强
| 编号 | 需求 | 描述 |
|------|------|------|
| UX-26 | 消息引用 | 右键消息可引用，输入框显示引用内容 |
| UX-27 | 图片预览 | 用户上传的图片可点击放大查看 |
| UX-28 | 链接可点击 | AI 回复中的 URL 自动转为可点击链接 |

---

## 三、技术方案要点

### 3.1 代码语法高亮（UX-05）
```typescript
// 安装 highlight.js
import hljs from 'highlight.js'

// marked 配置
marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  }
})
```

### 3.2 工具调用折叠（UX-08/09）
```vue
<template>
  <div class="tool-call-card" @click="expanded = !expanded">
    <div class="tool-summary">
      <span>🔧 {{ tc.name }}</span>
      <span class="tool-path">{{ tc.input.path }}</span>
      <ChevronDown v-if="!expanded" :size="14" />
      <ChevronUp v-else :size="14" />
    </div>
    <div v-if="expanded" class="tool-detail">
      <!-- 完整输入/输出/diff -->
    </div>
  </div>
</template>
```

### 3.3 停止生成（UX-04/13）
```typescript
// 使用 AbortController
const abortController = ref<AbortController | null>(null)

async function sendMessage() {
  abortController.value = new AbortController()
  try {
    const res = await api.sendTaskChatMessage(
      taskId.value, text, selectedModel.value,
      { signal: abortController.value.signal }
    )
  } catch (e) {
    if (e.name === 'AbortError') {
      aiMsg.content += '\n\n[已停止生成]'
    }
  }
}

function stopGeneration() {
  abortController.value?.abort()
}
```

### 3.4 消息复制（UX-02）
```typescript
function copyMessage(content: string) {
  // 复制 Markdown 源码而非渲染后的文本
  navigator.clipboard.writeText(content)
  showToast('已复制到剪贴板')
}
```

---

## 四、实施优先级

| 阶段 | 包含需求 | 预估工时 | 价值 |
|------|----------|----------|------|
| **Phase 1** | UX-01~04（消息交互） | 2h | 解决最痛的交互问题 |
| **Phase 2** | UX-05~10（代码+工具） | 3h | 提升代码阅读体验 |
| **Phase 3** | UX-11~19（流畅度） | 3h | 减少等待焦虑 |
| **Phase 4** | UX-20~28（打磨） | 2h | 锦上添花 |

---

## 五、验收标准

- [ ] 用户可以 Shift+Enter 输入多行文本
- [ ] 每条 AI 回复有复制按钮，点击后复制 Markdown 源码
- [ ] 代码块有语法高亮和复制按钮
- [ ] 工具调用卡片默认折叠，点击可展开
- [ ] 思考中状态显示具体进度信息
- [ ] 审批/打回操作有确认弹窗
- [ ] 右侧面板可折叠
