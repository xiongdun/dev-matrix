<template>
  <div class="chat-message" :class="message.role">
    <div class="message-avatar">
      <User v-if="message.role === 'user'" :size="16" />
      <Bot v-else :size="16" />
    </div>
    <div class="message-body">
      <div class="message-header">
        <span class="message-role">
          {{ message.role === 'user' ? t('workbench.userLabel') : t('workbench.aiLabel') }}
        </span>
        <span class="message-time">{{ formatTime(message.timestamp) }}</span>
      </div>

      <!-- 用户消息：纯文本 -->
      <div v-if="message.role === 'user'" class="message-content user-text">
        {{ message.content }}
      </div>

      <!-- AI消息：思考中 / 工具调用 / Diff对比 / Markdown渲染 -->
      <div v-else class="message-content">
        <!-- 思考中状态 -->
        <div v-if="message.isThinking" class="thinking-indicator">
          <div class="thinking-dots">
            <span class="thinking-dot"></span>
            <span class="thinking-dot"></span>
            <span class="thinking-dot"></span>
          </div>
          <div class="thinking-info">
            <span class="thinking-text">AI 正在思考...</span>
            <span class="thinking-hint" v-if="thinkingTime > 5">正在处理复杂任务，请耐心等待</span>
          </div>
          <span class="thinking-timer">{{ thinkingTime }}s</span>
        </div>

        <!-- 工具调用卡片 -->
        <div v-if="message.toolCalls?.length" class="tool-calls">
          <!-- 工具调用摘要 -->
          <div v-if="message.toolCalls.length > 1 && !showAllTools" class="tool-summary" @click="showAllTools = true">
            <span>🔧 AI 使用了 {{ message.toolCalls.length }} 个工具</span>
            <ChevronDown :size="14" />
          </div>
          <template v-for="(tc, idx) in message.toolCalls" :key="idx">
            <div v-if="showAllTools || idx === message.toolCalls!.length - 1" class="tool-call-card" @click="toggleToolExpand(idx)">
              <div class="tool-call-header">
                <span class="tool-call-icon">🔧</span>
                <span class="tool-call-name">{{ tc.name }}</span>
                <span class="tool-call-path" v-if="tc.input?.path">{{ tc.input.path }}</span>
                <span v-if="tc.result" class="tool-call-status" :class="tc.result.error ? 'error' : 'success'">
                  {{ tc.result.error ? '失败' : '成功' }}
                </span>
                <ChevronDown v-if="!expandedTools.has(idx)" :size="14" class="tool-toggle" />
                <ChevronUp v-else :size="14" class="tool-toggle" />
              </div>
              <div v-if="expandedTools.has(idx)" class="tool-detail">
                <div class="tool-call-input">
                  <code>{{ formatToolInput(tc.input) }}</code>
                </div>
            <!-- Write/Edit 工具显示 diff -->
            <div v-if="tc.name === 'Write' && tc.result?.success" class="tool-diff">
              <div class="diff-badge">📄 文件已写入</div>
              <code class="diff-path">{{ tc.input.path }}</code>
            </div>
            <div v-if="tc.name === 'Edit' && tc.result?.success" class="tool-diff">
              <div class="diff-badge">✏️ 文件已修改</div>
              <code class="diff-path">{{ tc.input.path }}</code>
              <div v-if="tc.input.old_string" class="diff-content">
                <div class="diff-old">
                  <span class="diff-label">- 删除</span>
                  <pre>{{ tc.input.old_string }}</pre>
                </div>
                <div class="diff-new">
                  <span class="diff-label">+ 新增</span>
                  <pre>{{ tc.input.new_string }}</pre>
                </div>
              </div>
            </div>
            <div v-if="tc.name === 'Bash' && tc.result" class="tool-result">
              <pre v-if="tc.result.stdout">{{ tc.result.stdout }}</pre>
              <pre v-if="tc.result.stderr" class="stderr">{{ tc.result.stderr }}</pre>
            </div>
              </div>
            </div>
          </template>
        </div>

        <!-- Diff对比 -->
        <div v-if="message.previousContent" class="diff-wrapper">
          <DiffViewer :old-content="message.previousContent" :new-content="message.content" />
        </div>

        <!-- Markdown渲染 -->
        <div v-if="message.content" class="ai-text markdown-body" :class="{ streaming: isStreaming }" v-html="renderedContent"></div>

        <!-- 操作按钮栏 -->
        <div v-if="message.role === 'assistant' && message.content && !isStreaming" class="message-actions">
          <button class="action-btn-sm" @click="copyContent" title="复制">
            <Copy :size="14" />
            <span>{{ copied ? '已复制' : '复制' }}</span>
          </button>
          <button class="action-btn-sm" @click="emit('regenerate', messageIndex ?? 0)" title="重新生成">
            <RefreshCw :size="14" />
            <span>重新生成</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { computed, ref, onMounted, onUnmounted, nextTick } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import { User, Bot, Wrench, Copy, RefreshCw, ChevronDown, ChevronUp } from 'lucide-vue-next'
import DiffViewer from './DiffViewer.vue'

const { t } = useI18n()

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  previousContent?: string
  timestamp: string
  images?: string[]
  toolCalls?: Array<{ name: string; input: Record<string, unknown>; result?: Record<string, unknown> }>
  isThinking?: boolean
}

const props = defineProps<{
  message: Message
  isStreaming?: boolean
  messageIndex?: number
}>()

const emit = defineEmits<{
  (e: 'regenerate', index: number): void
}>()

// 工具调用折叠状态
const showAllTools = ref(false)
const expandedTools = ref(new Set<number>())

function toggleToolExpand(idx: number) {
  if (expandedTools.value.has(idx)) {
    expandedTools.value.delete(idx)
  } else {
    expandedTools.value.add(idx)
  }
}

// UX-11: 思考计时器
const thinkingTime = ref(0)
let thinkingTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  if (props.message.isThinking) {
    thinkingTimer = setInterval(() => { thinkingTime.value++ }, 1000)
  }
})

onUnmounted(() => {
  if (thinkingTimer) clearInterval(thinkingTimer)
})

const renderedContent = computed(() => {
  if (props.message.role !== 'assistant') return ''
  const content = props.message.content || ''
  if (!content) return '<span class="typing-cursor"></span>'
  return marked.parse(content, {
    breaks: true,
    gfm: true,
    highlight: (code: string, lang: string) => {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang }).value
      }
      return hljs.highlightAuto(code).value
    },
  })
})

function formatTime(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatToolInput(input: Record<string, unknown>): string {
  const entries = Object.entries(input).map(([k, v]) => {
    const val = typeof v === 'string' ? v : JSON.stringify(v)
    const truncated = val.length > 80 ? val.slice(0, 80) + '...' : val
    return `${k}: ${truncated}`
  })
  return entries.join(', ')
}

// UX-02: 复制内容
const copied = ref(false)
function copyContent() {
  navigator.clipboard.writeText(props.message.content || '')
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 10px;
  padding: 12px 0;
}

/* 用户消息：右对齐，头像在右 */
.chat-message.user {
  flex-direction: row-reverse;
}

.chat-message.user .message-header {
  flex-direction: row-reverse;
}

.chat-message.user .message-body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.chat-message.user .message-avatar {
  background-color: rgba(99, 102, 241, 0.15);
  color: #6366f1;
}

.chat-message.assistant .message-avatar {
  background-color: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.message-body {
  flex: none;
  max-width: 80%;
  min-width: 0;
  width: fit-content;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.message-role {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.message-time {
  font-size: 11px;
  color: var(--text-muted);
}

.message-content {
  font-size: 13px;
  line-height: 1.6;
}

.user-text {
  color: var(--text-primary);
  background-color: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: var(--radius-md);
  padding: 10px 14px;
  width: fit-content;
  max-width: 100%;
}

/* AI Markdown 渲染样式 */
.markdown-body {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-primary);
  width: fit-content;
  max-width: 100%;
  overflow-x: auto;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin-top: 16px;
  margin-bottom: 8px;
  font-weight: 600;
  line-height: 1.4;
}

.markdown-body :deep(h1) { font-size: 1.3em; }
.markdown-body :deep(h2) { font-size: 1.15em; }
.markdown-body :deep(h3) { font-size: 1.05em; }

.markdown-body :deep(p) {
  margin: 8px 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

.markdown-body :deep(li) {
  margin: 4px 0;
}

.markdown-body :deep(code) {
  background-color: rgba(99, 102, 241, 0.08);
  border-radius: 4px;
  padding: 2px 6px;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 0.9em;
}

.markdown-body :deep(pre) {
  position: relative;
  background-color: #1e1e2e;
  border-radius: 8px;
  padding: 12px 16px;
  overflow-x: auto;
  margin: 10px 0;
}

/* 代码块语言标签 */
.markdown-body :deep(pre) {
  position: relative;
}

.markdown-body :deep(pre::before) {
  content: attr(data-lang);
  position: absolute;
  top: 0;
  right: 0;
  padding: 2px 8px;
  font-size: 10px;
  color: #888;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0 8px 0 4px;
}

/* 代码块复制按钮 */
.markdown-body :deep(.code-copy-btn) {
  position: absolute;
  top: 4px;
  right: 60px;
  padding: 2px 8px;
  font-size: 10px;
  color: #888;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 4px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
}

.markdown-body :deep(pre:hover .code-copy-btn) {
  opacity: 1;
}

.markdown-body :deep(.code-copy-btn:hover) {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 12px;
  color: #cdd6f4;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 10px 0;
  width: auto;
  font-size: 12px;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--border-color);
  padding: 6px 12px;
  text-align: left;
}

.markdown-body :deep(th) {
  background-color: var(--bg-secondary);
  font-weight: 600;
}

.markdown-body :deep(tr:nth-child(even)) {
  background-color: rgba(0, 0, 0, 0.02);
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid #6366f1;
  margin: 10px 0;
  padding: 4px 12px;
  color: var(--text-secondary);
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 16px 0;
}

.markdown-body :deep(a) {
  color: #6366f1;
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

/* 打字机光标动画 */
.markdown-body :deep(.typing-cursor) {
  display: inline-block;
  width: 2px;
  height: 1em;
  background-color: #6366f1;
  animation: blink 1s step-end infinite;
  vertical-align: text-bottom;
  margin-left: 2px;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 流式输出时最后一行闪烁光标 */
.markdown-body.streaming::after {
  content: '▌';
  color: #6366f1;
  animation: blink 1s step-end infinite;
}

.diff-wrapper {
  margin-top: 4px;
}

/* 思考中动画 */
.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.thinking-dots {
  display: flex;
  gap: 4px;
}

.thinking-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6366f1;
  animation: thinking-bounce 1.4s ease-in-out infinite;
}

.thinking-dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes thinking-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.thinking-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.thinking-text {
  font-size: 13px;
  color: var(--text-secondary);
}

.thinking-hint {
  font-size: 11px;
  color: var(--text-muted);
  font-style: italic;
}

.thinking-timer {
  font-size: 11px;
  color: var(--text-muted);
  font-family: 'SF Mono', Monaco, monospace;
  min-width: 30px;
  text-align: right;
}

/* 工具调用卡片 */
.tool-calls {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 8px;
}

.tool-call-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  font-size: 12px;
}

.tool-call-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(99, 102, 241, 0.05);
  border-bottom: 1px solid var(--border-color);
}

.tool-call-name {
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'SF Mono', Monaco, monospace;
}

.tool-call-status {
  margin-left: auto;
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 10px;
}

.tool-call-status.success {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.tool-call-status.error {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.tool-call-input {
  padding: 8px 12px;
}

.tool-call-input code {
  font-size: 11px;
  color: var(--text-secondary);
  background: none;
  padding: 0;
  word-break: break-all;
}

/* 工具摘要 */
.tool-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 12px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.tool-summary:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* 工具路径 */
.tool-call-path {
  font-size: 11px;
  color: #6366f1;
  background: rgba(99, 102, 241, 0.08);
  padding: 1px 6px;
  border-radius: 4px;
  margin-left: auto;
  margin-right: 8px;
  font-family: 'SF Mono', Monaco, monospace;
}

/* 工具展开按钮 */
.tool-toggle {
  color: var(--text-muted);
  flex-shrink: 0;
}

/* 工具详情 */
.tool-detail {
  border-top: 1px solid var(--border-color);
}

/* 工具 diff 展示 */
.tool-diff {
  padding: 8px 12px;
  border-top: 1px solid var(--border-color);
}

.diff-badge {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 4px;
}

.diff-path {
  font-size: 11px;
  color: #6366f1;
  background: rgba(99, 102, 241, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
}

.diff-content {
  margin-top: 8px;
  border-radius: 6px;
  overflow: hidden;
  font-size: 12px;
}

.diff-old {
  background: rgba(239, 68, 68, 0.06);
  padding: 8px 12px;
}

.diff-old pre {
  margin: 0;
  color: #dc2626;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 11px;
}

.diff-new {
  background: rgba(16, 185, 129, 0.06);
  padding: 8px 12px;
  border-top: 1px solid var(--border-color);
}

.diff-new pre {
  margin: 0;
  color: #059669;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 11px;
}

.diff-label {
  font-size: 11px;
  font-weight: 600;
  display: block;
  margin-bottom: 2px;
}

.diff-old .diff-label { color: #dc2626; }
.diff-new .diff-label { color: #059669; }

/* 工具结果 */
.tool-result {
  padding: 8px 12px;
  border-top: 1px solid var(--border-color);
  max-height: 200px;
  overflow-y: auto;
}

.tool-result pre {
  margin: 0;
  font-size: 11px;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

.tool-result pre.stderr {
  color: #ef4444;
}

/* 操作按钮栏 */
.message-actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.chat-message:hover .message-actions {
  opacity: 1;
}

.action-btn-sm {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text-muted);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn-sm:hover {
  color: var(--text-primary);
  border-color: var(--border-hover);
  background: var(--bg-hover);
}

/* 停止按钮 */
.stop-btn {
  background-color: #ef4444 !important;
  border-color: #ef4444 !important;
  color: white !important;
}

.stop-btn:hover {
  background-color: #dc2626 !important;
}
</style>
