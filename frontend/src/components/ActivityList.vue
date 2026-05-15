<!--
  @file 活动列表组件
  @description 展示最近活动记录的列表组件
  @component ActivityList
  @props
    - activities: 活动数据数组

  @example
  ```vue
  <template>
    <ActivityList :activities="recentActivities" />
  </template>
  ```
-->

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

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

/**
 * 根据活动类型获取图标
 * @param {string} type - 活动类型
 * @returns {string} 图标字符
 */
const getActivityIcon = (type: string): string => {
  const icons: Record<string, string> = {
    workflow: '⚡',
    approval: '✅',
    agent: '🤖',
    skill: '🔧',
    error: '❌',
  }
  return icons[type] || '📋'
}
</script>

<template>
  <div class="activity-list">
    <!-- 空状态提示 -->
    <div v-if="activities.length === 0" class="empty-state">
      {{ t('activity.empty') }}
    </div>
    <!-- 活动列表 -->
    <div
      v-for="activity in activities"
      :key="activity.id"
      class="activity-item"
    >
      <!-- 活动图标 -->
      <div class="activity-icon">{{ getActivityIcon(activity.type) }}</div>
      <div class="activity-content">
        <!-- 活动消息 -->
        <div class="activity-message">{{ activity.message }}</div>
        <!-- 相对时间 -->
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
  font-size: 1.25rem;
  flex-shrink: 0;
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
