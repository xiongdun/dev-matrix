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

      <!-- AI消息：Diff对比或纯文本 -->
      <div v-else class="message-content">
        <div v-if="message.previousContent" class="diff-wrapper">
          <DiffViewer :old-content="message.previousContent" :new-content="message.content" />
        </div>
        <div v-else class="ai-text">
          <pre>{{ message.content }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { User, Bot } from 'lucide-vue-next'
import DiffViewer from './DiffViewer.vue'

const { t } = useI18n()

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  previousContent?: string
  timestamp: string
}

const props = defineProps<{
  message: Message
}>()

function formatTime(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 10px;
  padding: 12px 0;
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
  flex: 1;
  min-width: 0;
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
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 10px 14px;
  max-width: 90%;
}

.ai-text pre {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 12px;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 12px 14px;
}

.diff-wrapper {
  margin-top: 4px;
}
</style>
