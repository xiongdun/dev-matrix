<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { Zap, CheckCircle, Bot, Wrench, XCircle, ClipboardList } from 'lucide-vue-next'

interface ActivityItem {
  id: string
  type: string
  message: string
  timestamp: string
}

interface Props {
  activities: ActivityItem[]
}

defineProps<Props>()

const { t } = useI18n()

const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return t('activity.justNow')
  if (minutes < 60) return t('activity.minutesAgo', { n: minutes })
  if (hours < 24) return t('activity.hoursAgo', { n: hours })
  return t('activity.daysAgo', { n: days })
}

const iconMap: Record<string, any> = {
  workflow: Zap,
  approval: CheckCircle,
  agent: Bot,
  skill: Wrench,
  error: XCircle,
}

const getActivityIcon = (type: string) => {
  return iconMap[type] || ClipboardList
}
</script>

<template>
  <div class="activity-list">
    <div v-if="activities.length === 0" class="empty-state">
      {{ t('activity.empty') }}
    </div>
    <div
      v-for="activity in activities"
      :key="activity.id"
      class="activity-item"
    >
      <div class="activity-icon">
        <component :is="getActivityIcon(activity.type)" :size="18" />
      </div>
      <div class="activity-content">
        <div class="activity-message">{{ activity.message }}</div>
        <div class="activity-time">{{ formatTime(activity.timestamp) }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
  font-style: italic;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 6px;
  background: var(--background-color);
  transition: background 0.2s ease;
}

.activity-item:hover {
  background: var(--hover-color);
}

.activity-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-message {
  font-size: 0.875rem;
  color: var(--text-primary);
  line-height: 1.4;
}

.activity-time {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}
</style>
