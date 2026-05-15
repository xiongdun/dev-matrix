<!--
  @file 任务列表组件
  @description 展示任务列表，支持状态筛选和操作
  @component TaskList
  @props
    - tasks: 任务数据数组
  @emits
    - update:status: 更新任务状态
    - delete: 删除任务

  @example
  ```vue
  <template>
    <TaskList :tasks="taskList" @update:status="handleStatusUpdate" />
  </template>
  ```
-->

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

interface TaskItem {
  id: string
  title: string
  status: string
  priority: string
}

interface Props {
  tasks: TaskItem[]
}

defineProps<Props>()

const { t } = useI18n()

const emit = defineEmits<{
  (e: 'update:status', taskId: string, status: string): void
  (e: 'delete', taskId: string): void
}>()

const getStatusClass = (status: string): string => {
  const classes: Record<string, string> = {
    pending: 'status-pending',
    'in_progress': 'status-in-progress',
    completed: 'status-completed',
    failed: 'status-failed',
  }
  return classes[status] || 'status-pending'
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: t('tasks.status.pending'),
    'in_progress': t('tasks.status.in_progress'),
    completed: t('tasks.status.completed'),
    failed: t('tasks.status.failed'),
  }
  return labels[status] || status
}

const getPriorityClass = (priority: string): string => {
  const classes: Record<string, string> = {
    high: 'priority-high',
    medium: 'priority-medium',
    low: 'priority-low',
  }
  return classes[priority] || 'priority-medium'
}

const getPriorityLabel = (priority: string): string => {
  const labels: Record<string, string> = {
    high: t('tasks.priority.high'),
    medium: t('tasks.priority.medium'),
    low: t('tasks.priority.low'),
  }
  return labels[priority] || priority
}

/**
 * 处理状态变更
 * @param {string} taskId - 任务 ID
 * @param {string} status - 新状态
 */
const handleStatusChange = (taskId: string, status: string) => {
  emit('update:status', taskId, status)
}

/**
 * 处理删除任务
 * @param {string} taskId - 任务 ID
 */
const handleDelete = (taskId: string) => {
  emit('delete', taskId)
}
</script>

<template>
  <div class="task-list">
    <!-- 空状态提示 -->
    <div v-if="tasks.length === 0" class="empty-state">
      {{ t('tasks.empty') }}
    </div>
    <!-- 任务列表 -->
    <div
      v-for="task in tasks"
      :key="task.id"
      class="task-item"
    >
      <div class="task-header">
        <!-- 任务标题 -->
        <div class="task-title">{{ task.title }}</div>
        <!-- 删除按钮 -->
        <button
          class="task-delete"
          @click="handleDelete(task.id)"
          :title="t('tasks.deleteTitle')"
        >
          ×
        </button>
      </div>
      <div class="task-meta">
        <!-- 状态标签 -->
        <span :class="['task-status', getStatusClass(task.status)]">
          {{ getStatusLabel(task.status) }}
        </span>
        <!-- 优先级标签 -->
        <span :class="['task-priority', getPriorityClass(task.priority)]">
          {{ getPriorityLabel(task.priority) }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.task-list {
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

.task-item {
  padding: 1rem;
  border-radius: 6px;
  background: var(--background-color);
  border: 1px solid var(--border-color);
  transition: all 0.2s ease;
}

.task-item:hover {
  border-color: var(--primary-color);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.task-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.task-delete {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 1.25rem;
  line-height: 1;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.task-delete:hover {
  background: var(--error-color);
  color: white;
}

.task-meta {
  display: flex;
  gap: 0.5rem;
}

.task-status,
.task-priority {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.status-in-progress {
  background: #dbeafe;
  color: #1e40af;
}

.status-completed {
  background: #d1fae5;
  color: #065f46;
}

.status-failed {
  background: #fee2e2;
  color: #991b1b;
}

.priority-high {
  background: #fee2e2;
  color: #991b1b;
}

.priority-medium {
  background: #fef3c7;
  color: #92400e;
}

.priority-low {
  background: #d1fae5;
  color: #065f46;
}
</style>
