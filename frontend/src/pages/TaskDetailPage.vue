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
        <!-- 加载错误提示 -->
        <div v-if="loadError" class="load-error-overlay">
          <div class="load-error-content">
            <AlertCircle :size="48" class="error-icon" />
            <h3>{{ t('workbench.loadErrorTitle') }}</h3>
            <p>{{ loadError }}</p>
            <button class="btn-back" @click="goBack">
              <ArrowLeft :size="16" />
              {{ t('common.back') }}
            </button>
          </div>
        </div>

        <div v-else class="chat-messages" ref="messagesRef">
          <ChatMessage
            v-for="msg in messages"
            :key="msg.id"
            :message="msg"
          />
        </div>

        <!-- 底部输入框 -->
        <div class="chat-input-bar">
          <div class="chat-input-card">
            <!-- 已上传图片预览 -->
            <div v-if="uploadedImages.length" class="image-preview-row">
              <div v-for="(img, idx) in uploadedImages" :key="idx" class="image-preview-item">
                <img :src="img.preview" alt="preview" />
                <button class="image-remove-btn" @click="removeImage(idx)">
                  <X :size="12" />
                </button>
              </div>
            </div>

            <!-- 语音输入状态 -->
            <div v-if="isRecording" class="recording-indicator">
              <div class="recording-wave">
                <span v-for="i in 5" :key="i" class="wave-bar" :style="{ animationDelay: `${i * 0.1}s` }"></span>
              </div>
              <span class="recording-text">{{ t('workbench.recording') }} {{ recordingTime }}s</span>
              <button class="btn-icon-sm danger" @click="stopRecording">
                <Square :size="14" />
              </button>
            </div>

            <textarea
              v-model="inputMessage"
              rows="1"
              class="chat-input"
              :placeholder="t('workbench.inputPlaceholder')"
              @keydown.enter.prevent="sendMessage"
              @input="autoResize"
              ref="inputRef"
            />

            <!-- 底部工具栏 -->
            <div class="chat-toolbar">
              <div class="toolbar-left">
                <button class="toolbar-btn" :title="t('workbench.uploadImage')" @click="triggerImageUpload">
                  <ImageIcon :size="18" />
                </button>
                <button class="toolbar-btn" :title="t('workbench.codeBlock')" @click="insertCodeBlock">
                  <Code2 :size="18" />
                </button>
                <input
                  ref="imageInputRef"
                  type="file"
                  accept="image/*"
                  multiple
                  style="display: none"
                  @change="handleImageUpload"
                />
              </div>
              <div class="toolbar-right">
                <!-- 模型选择器 -->
                <div class="model-selector">
                  <button class="model-select-btn" @click="showModelDropdown = !showModelDropdown">
                    <span>{{ selectedModelLabel }}</span>
                    <ChevronDown :size="14" />
                  </button>
                  <div v-if="showModelDropdown" class="model-dropdown" v-click-outside="() => showModelDropdown = false">
                    <div
                      v-for="model in availableModels"
                      :key="model.id"
                      class="model-option"
                      :class="{ active: selectedModel === model.id }"
                      @click="selectModel(model.id)"
                    >
                      <span class="model-name">{{ model.name }}</span>
                      <span class="model-provider">{{ model.provider }}</span>
                    </div>
                  </div>
                </div>

                <!-- 语音输入按钮 -->
                <button
                  class="toolbar-btn"
                  :class="{ active: isRecording }"
                  :title="t('workbench.voiceInput')"
                  @click="toggleRecording"
                >
                  <Mic :size="18" />
                </button>

                <!-- 发送按钮 -->
                <button
                  class="chat-send-btn"
                  :disabled="!canSend || isSending"
                  @click="sendMessage"
                >
                  <ArrowUp :size="18" />
                </button>
              </div>
            </div>
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
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  ArrowLeft,
  CheckCircle,
  Undo2,
  RefreshCw,
  ArrowUp,
  ImageIcon,
  Code2,
  Mic,
  ChevronDown,
  X,
  Square,
  AlertCircle,
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
  images?: string[]
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

// ==================== 原有状态 ====================
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

// ==================== 图片上传 ====================
const uploadedImages = ref<Array<{ file: File; preview: string }>>([])
const imageInputRef = ref<HTMLInputElement | null>(null)

function triggerImageUpload() {
  imageInputRef.value?.click()
}

function handleImageUpload(e: Event) {
  const target = e.target as HTMLInputElement
  const files = target.files
  if (!files) return

  Array.from(files).forEach(file => {
    if (!file.type.startsWith('image/')) return
    const reader = new FileReader()
    reader.onload = () => {
      uploadedImages.value.push({
        file,
        preview: reader.result as string,
      })
    }
    reader.readAsDataURL(file)
  })

  target.value = ''
}

function removeImage(idx: number) {
  uploadedImages.value.splice(idx, 1)
}

// ==================== 代码块插入 ====================
function insertCodeBlock() {
  const codeBlock = '\n```\n\n```\n'
  inputMessage.value += codeBlock
  nextTick(() => {
    inputRef.value?.focus()
    autoResize()
  })
}

// ==================== LLM 模型选择器 ====================
interface LLMModel {
  id: string
  name: string
  provider: string
}

const availableModels = ref<LLMModel[]>([])
const selectedModel = ref('')
const showModelDropdown = ref(false)

const selectedModelLabel = computed(() => {
  const model = availableModels.value.find(m => m.id === selectedModel.value)
  return model?.name || t('workbench.selectModel')
})

async function loadAvailableModels() {
  try {
    const res = await api.getAvailableModels()
    availableModels.value = res.models
    if (availableModels.value.length && !selectedModel.value) {
      selectedModel.value = availableModels.value[0].id
    }
  } catch (e) {
    console.error('Failed to load models:', e)
    availableModels.value = [
      { id: 'gpt-4', name: 'GPT-4', provider: 'OpenAI' },
      { id: 'gpt-3.5-turbo', name: 'GPT-3.5', provider: 'OpenAI' },
      { id: 'claude-3-opus', name: 'Claude 3 Opus', provider: 'Anthropic' },
      { id: 'claude-3-sonnet', name: 'Claude 3 Sonnet', provider: 'Anthropic' },
    ]
    selectedModel.value = 'gpt-4'
  }
}

function selectModel(modelId: string) {
  selectedModel.value = modelId
  showModelDropdown.value = false
}

// ==================== 语音输入 ====================
const isRecording = ref(false)
const recordingTime = ref(0)
let mediaRecorder: MediaRecorder | null = null
let audioChunks: Blob[] = []
let recordingTimer: ReturnType<typeof setInterval> | null = null

async function toggleRecording() {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream)
    audioChunks = []

    mediaRecorder.ondataavailable = (e) => {
      audioChunks.push(e.data)
    }

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
      await transcribeAudio(audioBlob)
      stream.getTracks().forEach(t => t.stop())
    }

    mediaRecorder.start()
    isRecording.value = true
    recordingTime.value = 0
    recordingTimer = setInterval(() => {
      recordingTime.value++
    }, 1000)
  } catch (e) {
    console.error('Failed to start recording:', e)
    await showConfirm({
      title: t('common.error'),
      message: t('workbench.micPermissionDenied'),
      type: 'warning',
      showCancel: false,
      confirmText: t('common.confirm'),
    })
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  isRecording.value = false
  if (recordingTimer) {
    clearInterval(recordingTimer)
    recordingTimer = null
  }
}

async function transcribeAudio(audioBlob: Blob) {
  try {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'recording.webm')

    const res = await fetch('/api/workbench/transcribe', {
      method: 'POST',
      body: formData,
    })

    if (!res.ok) {
      throw new Error(`Transcription failed: ${res.status}`)
    }

    const data = await res.json()
    if (data.text) {
      inputMessage.value += (inputMessage.value ? ' ' : '') + data.text
      nextTick(() => {
        autoResize()
        inputRef.value?.focus()
      })
    }
  } catch (e: any) {
    console.error('Transcription error:', e)
    await showConfirm({
      title: t('common.error'),
      message: t('workbench.transcriptionFailed'),
      type: 'warning',
      showCancel: false,
      confirmText: t('common.confirm'),
    })
  }
}

// ==================== 原有方法 ====================
function safeParseOutputJson(outputJson: string | undefined): any {
  if (!outputJson || outputJson === '{}') return undefined
  try {
    const parsed = JSON.parse(outputJson)
    return parsed.context
  } catch (e) {
    console.warn('Failed to parse output_json:', e, 'Raw:', outputJson.slice(0, 200))
    return undefined
  }
}

async function loadAllTasks() {
  try {
    const res = await api.getWorkbenchTasks('')
    allTasks.value = res.tasks.map((t: any) => ({
      ...t,
      context: safeParseOutputJson(t.output_json),
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
    const taskRes = await api.getWorkbenchTask(id)
    task.value = {
      ...taskRes,
      context: safeParseOutputJson(taskRes.output_json),
      messages: [],
    }

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

loadAllTasks()
loadAvailableModels()

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

const canSend = computed(() => {
  return inputMessage.value.trim().length > 0 || uploadedImages.value.length > 0
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
  // 固定高度，由 CSS 控制，不需要动态调整
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
  if ((!text && uploadedImages.value.length === 0) || isSending.value || !taskId.value) return

  const imagePreviews = uploadedImages.value.map(img => img.preview)

  const userMsg: Message = {
    id: `msg-${taskId.value}-${Date.now()}`,
    role: 'user',
    content: text,
    timestamp: new Date().toISOString(),
    images: imagePreviews.length ? imagePreviews : undefined,
  }
  messages.value.push(userMsg)
  inputMessage.value = ''
  uploadedImages.value = []
  autoResize()
  scrollToBottom()

  isSending.value = true
  try {
    const res = await api.sendTaskChatMessage(taskId.value, text, selectedModel.value)

    const aiMsg: Message = {
      id: `msg-${res.message.id}`,
      role: 'assistant',
      content: res.message.content,
      timestamp: res.message.created_at || new Date().toISOString(),
    }
    messages.value.push(aiMsg)
  } catch (e: any) {
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

// ==================== 点击外部指令 ====================
const vClickOutside = {
  mounted(el: HTMLElement, binding: any) {
    el._clickOutside = (e: Event) => {
      if (!el.contains(e.target as Node)) {
        binding.value()
      }
    }
    document.addEventListener('click', el._clickOutside)
  },
  unmounted(el: HTMLElement) {
    document.removeEventListener('click', el._clickOutside)
  },
}

onUnmounted(() => {
  if (recordingTimer) clearInterval(recordingTimer)
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
})
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
  padding: 16px 24px;
  background-color: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}

.chat-input-card {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 16px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.chat-input-card:focus-within {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 图片预览 */
.image-preview-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.image-preview-item {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.image-preview-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

/* 录音指示器 */
.recording-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  margin-bottom: 8px;
}

.recording-wave {
  display: flex;
  align-items: center;
  gap: 3px;
  height: 24px;
}

.wave-bar {
  width: 3px;
  height: 100%;
  background: var(--accent-red);
  border-radius: 2px;
  animation: wave 1s ease-in-out infinite;
}

@keyframes wave {
  0%, 100% { height: 20%; }
  50% { height: 100%; }
}

.recording-text {
  font-size: 14px;
  color: var(--accent-red);
  font-weight: 500;
}

/* 输入框 */
.chat-input {
  width: 100%;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 15px;
  font-family: inherit;
  line-height: 1.6;
  resize: none;
  outline: none;
  height: 60px;
  max-height: 60px;
  padding: 0;
  margin-bottom: 12px;
  overflow-y: auto;
}

.chat-input::placeholder {
  color: var(--text-muted);
}

/* 底部工具栏 */
.chat-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 8px;
  border-top: 1px solid var(--border-color);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.toolbar-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.toolbar-btn.active {
  background: rgba(239, 68, 68, 0.15);
  color: var(--accent-red);
}

/* 模型选择器 */
.model-selector {
  position: relative;
}

.model-select-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  border: none;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.model-select-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.model-dropdown {
  position: absolute;
  bottom: calc(100% + 8px);
  right: 0;
  min-width: 200px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 6px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  z-index: 100;
}

.model-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.model-option:hover {
  background: var(--bg-hover);
}

.model-option.active {
  background: rgba(59, 130, 246, 0.1);
}

.model-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.model-provider {
  font-size: 11px;
  color: var(--text-muted);
}

/* 发送按钮 */
.chat-send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: none;
  background-color: var(--accent-green);
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.chat-send-btn:hover:not(:disabled) {
  opacity: 0.9;
  transform: scale(1.05);
}

.chat-send-btn:disabled {
  opacity: 0.3;
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

.btn-icon-sm {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
}

.btn-icon-sm.danger {
  color: var(--accent-red);
}

.btn-icon-sm:hover {
  background: var(--bg-hover);
}

/* 加载错误覆盖层 */
.load-error-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  padding: 40px;
}

.load-error-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  text-align: center;
  max-width: 400px;
}

.load-error-content .error-icon {
  color: var(--accent-red);
  opacity: 0.8;
}

.load-error-content h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.load-error-content p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}
</style>
