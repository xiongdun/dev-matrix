<template>
  <div class="activity-list">
    <div
      v-for="activity in activities"
      :key="activity.id"
      class="activity-item"
    >
      <div class="activity-icon" :style="{ backgroundColor: getActivityColor(activity.type) }">
      </div>
      <div class="activity-content">
        <div class="activity-title">{{ activity.title }}</div>
        <div class="activity-time">{{ activity.time }}</div>
      </div>
    </div>
    <div v-if="!activities.length" class="empty-state">
      {{ t('activity.empty') }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

function getActivityColor(type: string): string {
  const colors: Record<string, string> = {
    requirement_created: '#22c55e',
    workflow_started: '#3b82f6',
    approval_submitted: '#a855f7',
    agent_action: '#f59e0b',
    snapshot_created: '#06b6d4',
  }
  return colors[type] || '#71717a'
}

defineProps<{
  activities: Array<{
    id: string
    type: string
    title: string
    time: string
  }>
}>()
</script>
