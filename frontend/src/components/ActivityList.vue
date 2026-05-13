<template>
  <div class="activity-list">
    <div
      v-for="activity in activities"
      :key="activity.id"
      class="activity-item"
    >
      <div class="activity-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>
        </svg>
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

defineProps<{
  activities: Array<{
    id: string
    type: string
    title: string
    time: string
  }>
}>()
</script>
