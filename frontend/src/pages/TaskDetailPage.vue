<template>
  <div class="task-detail-page">
    <!-- 左侧：任务列表边栏 -->
    <TaskSidebar :tasks="allTasks" :active-task-id="taskId" />

    <!-- 中间：主内容区 -->
    <div class="detail-main">
      <!-- 顶部导航栏 -->
      <div class="detail-topbar">
        <button class="btn-back" @click="goBack">
          <ArrowLeft :size="16" />
          {{ t('workbench.back') }}
        </button>
        <div class="topbar-title">
          <span class="topbar-project">{{ task?.project_id }}</span>
          <span class="topbar-separator">·</span>
          <span class="topbar-stage">{{ task?.stage_name }}</span>
        </div>
        <div class="topbar-meta">
          <span class="tag tag--role">{{ task?.agent_role }}</span>
          <span class="tag" :class="`tag--${task?.status}`">{{ statusLabel }}</span>
        </div>
      </div>

      <!-- 对话流内容区 -->
      <div class="chat-container">
        <div class="chat-messages" ref="messagesRef">
          <ChatMessage
            v-for="msg in messages"
            :key="msg.id"
            :message="msg"
          />
        </div>

        <!-- 底部输入框 -->
        <div class="chat-input-bar">
          <div class="chat-input-wrapper">
            <textarea
              v-model="inputMessage"
              rows="1"
              class="chat-input"
              :placeholder="t('workbench.inputPlaceholder')"
              @keydown.enter.prevent="sendMessage"
              @input="autoResize"
              ref="inputRef"
            />
            <button
              class="chat-send-btn"
              :disabled="!inputMessage.trim() || isSending"
              @click="sendMessage"
            >
              <Send :size="16" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧：操作面板 -->
    <div class="content-right">
      <div class="action-panel">
        <h4>{{ t('workbench.actions') }}</h4>

        <button class="action-btn action-btn--approve" @click="handleApprove">
          <CheckCircle :size="18" />
          <div class="action-btn__text">
            <span class="action-btn__label">{{ t('workbench.approve') }}</span>
            <span class="action-btn__desc">{{ t('workbench.approveDesc') }}</span>
          </div>
        </button>

        <button class="action-btn action-btn--reject" @click="showReject = true; showRetry = false">
          <Undo2 :size="18" />
          <div class="action-btn__text">
            <span class="action-btn__label">{{ t('workbench.reject') }}</span>
            <span class="action-btn__desc">{{ t('workbench.rejectDesc') }}</span>
          </div>
        </button>

        <button class="action-btn action-btn--retry" @click="showRetry = true; showReject = false">
          <RefreshCw :size="18" />
          <div class="action-btn__text">
            <span class="action-btn__label">{{ t('workbench.retry') }}</span>
            <span class="action-btn__desc">{{ t('workbench.retryDesc') }}</span>
          </div>
        </button>
      </div>

      <!-- 拒绝输入 -->
      <div v-if="showReject" class="input-panel">
        <label>{{ t('workbench.rejectReason') }}</label>
        <textarea v-model="rejectComment" rows="5" :placeholder="t('workbench.rejectPlaceholder')" />
        <div class="input-actions">
          <button class="btn-submit" @click="handleReject">
            {{ t('workbench.submit') }}
          </button>
          <button class="btn-cancel" @click="showReject = false; rejectComment = ''">
            {{ t('workbench.cancel') }}
          </button>
        </div>
      </div>

      <!-- 重试输入 -->
      <div v-if="showRetry" class="input-panel">
        <label>{{ t('workbench.retryFeedback') }}</label>
        <textarea v-model="retryFeedback" rows="5" :placeholder="t('workbench.retryPlaceholder')" />
        <div class="input-actions">
          <button class="btn-submit" @click="handleRetry">
            {{ t('workbench.submit') }}
          </button>
          <button class="btn-cancel" @click="showRetry = false; retryFeedback = ''">
            {{ t('workbench.cancel') }}
          </button>
        </div>
      </div>

      <!-- 信息卡片 -->
      <div class="info-panel">
        <div class="info-item">
          <span class="info-label">{{ t('workbench.infoId') }}</span>
          <span class="info-value">#{{ task?.id }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">{{ t('workbench.infoStage') }}</span>
          <span class="info-value">{{ task?.stage_id }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">{{ t('workbench.infoArrived') }}</span>
          <span class="info-value">{{ formatTime(task?.arrived_at) }}</span>
        </div>
        <div v-if="task?.processed_at" class="info-item">
          <span class="info-label">{{ t('workbench.infoProcessed') }}</span>
          <span class="info-value">{{ formatTime(task?.processed_at) }}</span>
        </div>
      </div>

      <!-- 上下文面板 -->
      <TaskContextPanel v-if="task?.context" :context="task.context" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  ArrowLeft,
  CheckCircle,
  Undo2,
  RefreshCw,
  Send,
} from 'lucide-vue-next'
import { api } from '../api'
import { useDialog } from '../composables/useDialog'
import TaskSidebar from '../components/TaskSidebar.vue'
import TaskContextPanel from '../components/TaskContextPanel.vue'
import ChatMessage from '../components/ChatMessage.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { showConfirm } = useDialog()

interface TaskContext {
  skills: Array<{ name: string; description?: string }>
  files: Array<{ path: string; name?: string }>
  tools: Array<{ name: string; description?: string }>
  tokenUsage?: {
    percent: number
    used: number
    total: number
  }
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  previousContent?: string
  timestamp: string
}

interface Task {
  id: number
  project_id: string
  stage_id: string
  stage_name: string
  agent_role: string
  status: string
  output_json: string
  feedback: string | null
  arrived_at: string
  processed_at: string | null
  context?: TaskContext
  messages?: Message[]
}

const allTasks = ref<Task[]>([])
const taskId = ref(0)
const task = ref<Task | null>(null)
const messages = ref<Message[]>([])
const inputMessage = ref('')
const isSending = ref(false)
const messagesRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)
const isLoading = ref(false)
const loadError = ref('')

async function loadAllTasks() {
  try {
    const res = await api.getWorkbenchTasks('')
    allTasks.value = res.tasks.map((t: any) => ({
      ...t,
      context: t.output_json ? JSON.parse(t.output_json).context : undefined,
      messages: [],
    }))
  } catch (e: any) {
    console.error('Failed to load tasks:', e)
  }
}

async function loadTask(id: number) {
  taskId.value = id
  isLoading.value = true
  loadError.value = ''

  try {
    // 加载任务详情
    const taskRes = await api.getWorkbenchTask(id)
    task.value = {
      ...taskRes,
      context: taskRes.output_json ? JSON.parse(taskRes.output_json).context : undefined,
      messages: [],
    }

    // 加载对话历史
    const chatRes = await api.getTaskChatHistory(id)
    messages.value = chatRes.messages.map((m: any) => ({
      id: `msg-${m.id}`,
      role: m.role as 'user' | 'assistant',
      content: m.content,
      timestamp: m.created_at,
    }))
  } catch (e: any) {
    loadError.value = e.message || String(e)
    console.error('Failed to load task:', e)
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

watch(
  () => route.params.id,
  (newId) => {
    const id = parseInt(newId as string, 10)
    if (!isNaN(id)) {
      loadTask(id)
    }
  },
  { immediate: true }
)

// 初始加载任务列表
loadAllTasks()

const showReject = ref(false)
const showRetry = ref(false)
const rejectComment = ref('')
const retryFeedback = ref('')

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    pending: t('workbench.pending'),
    retrying: t('workbench.retry'),
    approved: t('workbench.approved'),
    rejected: t('workbench.rejected'),
    completed: t('workbench.completed'),
  }
  return map[task.value?.status || ''] || task.value?.status || ''
})

function goBack() {
  router.push('/workbench')
}

function formatTime(dateStr: string | undefined) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function autoResize() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

async function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text || isSending.value || !taskId.value) return

  // 添加用户消息到界面
  const userMsg: Message = {
    id: `msg-${taskId.value}-${Date.now()}`,
    role: 'user',
    content: text,
    timestamp: new Date().toISOString(),
  }
  messages.value.push(userMsg)
  inputMessage.value = ''
  autoResize()
  scrollToBottom()

  // 调用后端 API
  isSending.value = true
  try {
    const res = await api.sendTaskChatMessage(taskId.value, text)

    // 添加 AI 回复到界面
    const aiMsg: Message = {
      id: `msg-${res.message.id}`,
      role: 'assistant',
      content: res.message.content,
      timestamp: res.message.created_at || new Date().toISOString(),
    }
    messages.value.push(aiMsg)
  } catch (e: any) {
    // 显示错误消息
    const errorMsg: Message = {
      id: `msg-${taskId.value}-${Date.now()}-error`,
      role: 'assistant',
      content: `发送失败: ${e.message || String(e)}`,
      timestamp: new Date().toISOString(),
    }
    messages.value.push(errorMsg)
  } finally {
    isSending.value = false
    scrollToBottom()
  }
}

async function handleApprove() {
  try {
    await api.approveWorkbenchTask(task.value!.id)
    router.push('/workbench')
  } catch (e: any) {
    await showConfirm({
      title: t('common.error'),
      message: e.message || String(e),
      type: 'warning',
      showCancel: false,
      confirmText: t('common.confirm'),
    })
  }
}

async function handleReject() {
  try {
    await api.rejectWorkbenchTask(task.value!.id, rejectComment.value)
    router.push('/workbench')
  } catch (e: any) {
    await showConfirm({
      title: t('common.error'),
      message: e.message || String(e),
      type: 'warning',
      showCancel: false,
      confirmText: t('common.confirm'),
    })
  }
}

async function handleRetry() {
  try {
    await api.retryWorkbenchTask(task.value!.id, retryFeedback.value)
    router.push('/workbench')
  } catch (e: any) {
    await showConfirm({
      title: t('common.error'),
      message: e.message || String(e),
      type: 'warning',
      showCancel: false,
      confirmText: t('common.confirm'),
    })
  }
}
</script>

<style scoped>
.task-detail-page {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* 中间主内容区 */
.detail-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

/* 顶部导航栏 */
.detail-topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.btn-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-back:hover {
  border-color: var(--border-hover);
  color: var(--text-primary);
}

.topbar-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.topbar-project {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.topbar-separator {
  color: var(--text-muted);
}

.topbar-stage {
  font-size: 14px;
  color: var(--text-secondary);
}

.topbar-meta {
  display: flex;
  gap: 8px;
}

.tag {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tag--role {
  background-color: rgba(99, 102, 241, 0.12);
  color: #6366f1;
}

.tag--pending {
  background-color: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.tag--retrying {
  background-color: rgba(234, 179, 8, 0.15);
  color: var(--accent-yellow);
}

.tag--approved {
  background-color: rgba(34, 197, 94, 0.15);
  color: var(--accent-green);
}

.tag--rejected {
  background-color: rgba(239, 68, 68, 0.15);
  color: var(--accent-red);
}

.tag--completed {
  background-color: rgba(113, 113, 122, 0.15);
  color: var(--text-tertiary);
}

/* 对话流容器 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px;
}

/* 底部输入框 */
.chat-input-bar {
  padding: 12px 24px;
  background-color: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}

.chat-input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 8px 12px;
  transition: border-color 0.15s ease;
}

.chat-input-wrapper:focus-within {
  border-color: var(--accent-blue);
}

.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 13px;
  font-family: inherit;
  line-height: 1.5;
  resize: none;
  outline: none;
  max-height: 120px;
  min-height: 20px;
}

.chat-input::placeholder {
  color: var(--text-muted);
}

.chat-send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  border: none;
  background-color: var(--accent-blue);
  color: white;
  cursor: pointer;
  transition: opacity 0.15s ease;
  flex-shrink: 0;
}

.chat-send-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.chat-send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 右侧操作面板 */
.content-right {
  width: 320px;
  min-width: 280px;
  overflow-y: auto;
  padding: 20px;
  background-color: var(--bg-secondary);
  border-left: 1px solid var(--border-color);
  flex-shrink: 0;
}

.action-panel h4 {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 12px 0;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: 8px;
  text-align: left;
}

.action-btn:hover {
  border-color: var(--border-hover);
}

.action-btn--approve:hover {
  border-color: var(--accent-green);
  background-color: rgba(34, 197, 94, 0.08);
}

.action-btn--reject:hover {
  border-color: var(--accent-yellow);
  background-color: rgba(234, 179, 8, 0.08);
}

.action-btn--retry:hover {
  border-color: var(--accent-blue);
  background-color: rgba(59, 130, 246, 0.08);
}

.action-btn__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.action-btn__label {
  font-size: 13px;
  font-weight: 600;
}

.action-btn__desc {
  font-size: 11px;
  color: var(--text-tertiary);
}

.input-panel {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 14px;
  margin-bottom: 16px;
}

.input-panel label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.input-panel textarea {
  width: 100%;
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  padding: 10px 12px;
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s ease;
  margin-bottom: 10px;
}

.input-panel textarea:focus {
  border-color: var(--accent-blue);
}

.input-actions {
  display: flex;
  gap: 8px;
}

.btn-submit {
  flex: 1;
  padding: 7px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--accent-blue);
  background-color: var(--accent-blue);
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.btn-submit:hover {
  opacity: 0.9;
}

.btn-cancel {
  padding: 7px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-cancel:hover {
  color: var(--text-primary);
  border-color: var(--border-hover);
}

.info-panel {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  font-size: 12px;
}

.info-label {
  color: var(--text-tertiary);
}

.info-value {
  color: var(--text-secondary);
  font-family: 'SF Mono', Monaco, monospace;
}
</style>
