<template>
  <div class="task-list">
    <div
      v-for="task in tasks"
      :key="task.id"
      class="task-item"
    >
      <div :class="['task-status', task.status]">
        {{ t(`tasks.status.${task.status}`) }}
      </div>
      <div class="task-content">
        <div class="task-title">{{ task.title }}</div>
        <div class="task-meta">{{ task.agent }} · {{ task.time }}</div>
      </div>
    </div>
    <div v-if="!tasks.length" class="empty-state">
      {{ t('tasks.empty') }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps<{
  tasks: Array<{
    id: string
    title: string
    status: 'pending' | 'running' | 'completed' | 'failed' | 'approved' | 'rejected'
    agent: string
    time: string
  }>
}>()
</script>
