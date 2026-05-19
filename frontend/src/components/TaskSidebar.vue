<template>
  <div class="task-sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <button class="collapse-btn" @click="toggleCollapse" :title="isCollapsed ? t('workbench.expand') : t('workbench.collapse')">
        <PanelLeftClose v-if="!isCollapsed" :size="16" />
        <PanelRight v-else :size="16" />
      </button>
      <span v-if="!isCollapsed" class="sidebar-title">{{ t('workbench.taskList') }}</span>
    </div>

    <div v-if="!isCollapsed" class="task-list">
      <div
        v-for="task in tasks"
        :key="task.id"
        class="task-item"
        :class="{ active: task.id === activeTaskId }"
        @click="selectTask(task.id)"
      >
        <div class="task-item__top">
          <span class="task-item__project">{{ task.project_id }}</span>
          <span class="task-item__status" :class="task.status"></span>
        </div>
        <div class="task-item__stage">{{ task.stage_name }}</div>
        <div class="task-item__meta">
          <span class="task-item__agent">{{ task.agent_role }}</span>
          <span class="task-item__time">{{ formatTime(task.arrived_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { PanelLeftClose, PanelRight } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const { t } = useI18n()
const router = useRouter()

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

const props = defineProps<{
  tasks: Task[]
  activeTaskId: number
}>()

const isCollapsed = ref(false)

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

function selectTask(taskId: number) {
  if (taskId === props.activeTaskId) return
  router.push(`/workbench/task/${taskId}`)
}

function formatTime(dateStr: string) {
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (minutes < 1) return t('workbench.timeJustNow')
  if (minutes < 60) return t('workbench.timeMinutesAgo', { n: minutes })
  if (hours < 24) return t('workbench.timeHoursAgo', { n: hours })
  return t('workbench.timeDaysAgo', { n: days })
}
</script>

<style scoped>
.task-sidebar {
  width: 280px;
  min-width: 280px;
  background-color: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.25s ease, min-width 0.25s ease;
  overflow: hidden;
}

.task-sidebar.collapsed {
  width: 44px;
  min-width: 44px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.collapse-btn:hover {
  border-color: var(--border-hover);
  color: var(--text-primary);
}

.sidebar-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}

.task-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.task-item {
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.15s ease;
  margin-bottom: 4px;
}

.task-item:hover {
  background-color: var(--bg-hover);
}

.task-item.active {
  background-color: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.25);
}

.task-item__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.task-item__project {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'SF Mono', Monaco, monospace;
}

.task-item__status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.task-item__status.pending {
  background-color: #3b82f6;
}

.task-item__status.retrying {
  background-color: var(--accent-yellow);
}

.task-item__status.approved {
  background-color: var(--accent-green);
}

.task-item__status.rejected {
  background-color: var(--accent-red);
}

.task-item__status.completed {
  background-color: var(--text-muted);
}

.task-item__stage {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-item__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.task-item__agent {
  font-size: 11px;
  color: #6366f1;
  background-color: rgba(99, 102, 241, 0.1);
  padding: 1px 6px;
  border-radius: 9999px;
}

.task-item__time {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
}
</style>
