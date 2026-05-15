<template>
  <div class="task-card" :class="{ 'task-card--retrying': task.status === 'retrying' }">
    <div class="task-card__header">
      <div class="task-card__info">
        <span class="task-card__project">{{ task.project_id }}</span>
        <span class="task-card__separator">·</span>
        <span class="task-card__stage">{{ task.stage_name }}</span>
      </div>
      <div class="task-card__right">
        <span v-if="task.status === 'pending'" class="task-status pending">{{ t('workbench.pending') }}</span>
        <span v-else-if="task.status === 'retrying'" class="task-status retrying">{{ t('workbench.retry') }}</span>
        <span class="task-card__time">{{ relativeTime }}</span>
      </div>
    </div>

    <div class="task-card__output-toggle" @click="outputExpanded = !outputExpanded">
      <span class="task-card__output-label">{{ t('workbench.output') }}</span>
      <ChevronDown class="task-card__expand-icon" :class="{ expanded: outputExpanded }" :size="14" />
    </div>
    <div v-if="outputExpanded" class="task-card__output-content">
      <pre>{{ formattedOutput }}</pre>
    </div>

    <div class="task-card__actions">
      <button class="task-card__btn task-card__btn--approve" @click="emit('approve', task.id)">
        <CheckCircle :size="14" /> {{ t('workbench.approve') }}
      </button>
      <button class="task-card__btn task-card__btn--reject" @click="showRejectInput = !showRejectInput">
        <Undo2 :size="14" /> {{ t('workbench.reject') }}
      </button>
      <button class="task-card__btn task-card__btn--retry" @click="showRetryInput = !showRetryInput">
        <RefreshCw :size="14" /> {{ t('workbench.retry') }}
      </button>
    </div>

    <div v-if="showRejectInput" class="task-card__input-area">
      <label class="task-card__input-label">{{ t('workbench.rejectReason') }}</label>
      <textarea v-model="rejectComment" class="task-card__textarea" rows="3" />
      <div class="task-card__input-actions">
        <button class="task-card__btn task-card__btn--submit" @click="emit('reject', task.id, rejectComment); showRejectInput = false; rejectComment = ''">{{ t('workbench.submit') }}</button>
        <button class="task-card__btn task-card__btn--cancel" @click="showRejectInput = false; rejectComment = ''">{{ t('workbench.cancel') }}</button>
      </div>
    </div>

    <div v-if="showRetryInput" class="task-card__input-area">
      <label class="task-card__input-label">{{ t('workbench.retryFeedback') }}</label>
      <textarea v-model="retryFeedback" class="task-card__textarea" rows="3" />
      <div class="task-card__input-actions">
        <button class="task-card__btn task-card__btn--submit" @click="emit('retry', task.id, retryFeedback); showRetryInput = false; retryFeedback = ''">{{ t('workbench.submit') }}</button>
        <button class="task-card__btn task-card__btn--cancel" @click="showRetryInput = false; retryFeedback = ''">{{ t('workbench.cancel') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ChevronDown, CheckCircle, Undo2, RefreshCw } from 'lucide-vue-next'

const { t } = useI18n()

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
}

const props = defineProps<{ task: Task }>()
const emit = defineEmits<{
  approve: [taskId: number]
  reject: [taskId: number, comment?: string]
  retry: [taskId: number, feedback?: string]
}>()

const outputExpanded = ref(false)
const showRejectInput = ref(false)
const showRetryInput = ref(false)
const rejectComment = ref('')
const retryFeedback = ref('')

const formattedOutput = computed(() => {
  try {
    return JSON.stringify(JSON.parse(props.task.output_json), null, 2)
  } catch {
    return props.task.output_json
  }
})

const relativeTime = computed(() => {
  const now = Date.now()
  const arrived = new Date(props.task.arrived_at).getTime()
  const diff = Math.max(0, now - arrived)
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return t('workbench.timeJustNow')
  if (minutes < 60) return t('workbench.timeMinutesAgo', { n: minutes })
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return t('workbench.timeHoursAgo', { n: hours })
  const days = Math.floor(hours / 24)
  return t('workbench.timeDaysAgo', { n: days })
})
</script>

<style scoped>
.task-card {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  transition: border-color 0.15s ease;
}

.task-card:hover {
  border-color: var(--border-hover);
}

.task-card--retrying {
  border-color: var(--accent-blue);
  animation: pulse-border 2s ease-in-out infinite;
}

@keyframes pulse-border {
  0%, 100% { border-color: var(--accent-blue); }
  50% { border-color: transparent; }
}

.task-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.task-card__info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.task-card__project {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-card__separator {
  color: var(--text-muted);
  font-size: 13px;
}

.task-card__stage {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-card__right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.task-card__time {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}

.task-status.retrying {
  background-color: rgba(59, 130, 246, 0.15);
  color: var(--accent-blue);
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  animation: blink 1.5s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.task-card__output-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 0;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 13px;
  transition: color 0.15s ease;
}

.task-card__output-toggle:hover {
  color: var(--text-primary);
}

.task-card__output-label {
  font-weight: 500;
}

.task-card__expand-icon {
  transition: transform 0.2s ease;
}

.task-card__expand-icon.expanded {
  transform: rotate(180deg);
}

.task-card__output-content {
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 12px;
  margin-bottom: 12px;
  overflow-x: auto;
}

.task-card__output-content pre {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

.task-card__actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.task-card__btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.task-card__btn:hover {
  border-color: var(--border-hover);
}

.task-card__btn--approve:hover {
  background-color: rgba(34, 197, 94, 0.15);
  border-color: var(--accent-green);
  color: var(--accent-green);
}

.task-card__btn--reject:hover {
  background-color: rgba(234, 179, 8, 0.15);
  border-color: var(--accent-yellow);
  color: var(--accent-yellow);
}

.task-card__btn--retry:hover {
  background-color: rgba(59, 130, 246, 0.15);
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.task-card__btn--submit {
  background-color: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.task-card__btn--submit:hover {
  opacity: 0.9;
}

.task-card__btn--cancel {
  color: var(--text-secondary);
}

.task-card__btn--cancel:hover {
  color: var(--text-primary);
}

.task-card__input-area {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.task-card__input-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.task-card__textarea {
  width: 100%;
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  padding: 8px 12px;
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s ease;
}

.task-card__textarea:focus {
  border-color: var(--accent-blue);
}

.task-card__input-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
</style>
