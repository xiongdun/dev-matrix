<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>{{ t('workbench.title') }}</h1>
        <p>{{ t('workbench.subtitle') }}</p>
      </div>
    </div>

    <div class="role-tabs">
      <button
        v-for="role in roles"
        :key="role.key"
        class="role-tab"
        :class="{ active: activeRole === role.key }"
        @click="switchRole(role.key)"
      >
        {{ t(role.labelKey) }}
      </button>
    </div>

    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-item__value">{{ stats.pending }}</span>
        <span class="stat-item__label">{{ t('workbench.pending') }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-item__value">{{ stats.completed }}</span>
        <span class="stat-item__label">{{ t('workbench.completed') }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-item__value">{{ stats.rejected }}</span>
        <span class="stat-item__label">{{ t('workbench.rejected') }}</span>
      </div>
    </div>

    <div v-if="loading" class="empty-state">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="empty-state" style="color: var(--accent-red)">
      {{ t('common.error') }}: {{ error }}
    </div>
    <div v-else-if="tasks.length === 0" class="empty-state">
      {{ t('workbench.noTasks') }}
    </div>
    <div v-else class="task-list">
      <TaskCard
        v-for="task in tasks"
        :key="task.id"
        :task="task"
        @approve="handleApprove"
        @reject="handleReject"
        @retry="handleRetry"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../api'
import TaskCard from '../components/workbench/TaskCard.vue'

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

const roles = [
  { key: 'business_analyst', labelKey: 'workbench.roleBA' },
  { key: 'product_manager', labelKey: 'workbench.rolePM' },
  { key: 'architect', labelKey: 'workbench.roleArchitect' },
  { key: 'developer', labelKey: 'workbench.roleDeveloper' },
  { key: 'qa', labelKey: 'workbench.roleQA' },
]

const activeRole = ref('business_analyst')
const tasks = ref<Task[]>([])
const loading = ref(true)
const error = ref('')
const stats = ref({ pending: 0, completed: 0, rejected: 0 })

let closeSSE: (() => void) | null = null

async function fetchTasks() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.getWorkbenchTasks(activeRole.value)
    tasks.value = res.tasks || []
  } catch (e: any) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  try {
    const res = await api.getWorkbenchStats(activeRole.value)
    stats.value = { pending: res.pending, completed: res.completed, rejected: res.rejected }
  } catch {
    // silently ignore stats errors
  }
}

function switchRole(roleKey: string) {
  activeRole.value = roleKey
  fetchTasks()
  fetchStats()
}

async function handleApprove(taskId: number) {
  try {
    await api.approveWorkbenchTask(taskId)
    await fetchTasks()
    await fetchStats()
  } catch (e: any) {
    error.value = e.message || String(e)
  }
}

async function handleReject(taskId: number, comment?: string) {
  try {
    await api.rejectWorkbenchTask(taskId, comment)
    await fetchTasks()
    await fetchStats()
  } catch (e: any) {
    error.value = e.message || String(e)
  }
}

async function handleRetry(taskId: number, feedback?: string) {
  try {
    await api.retryWorkbenchTask(taskId, feedback)
    await fetchTasks()
    await fetchStats()
  } catch (e: any) {
    error.value = e.message || String(e)
  }
}

onMounted(() => {
  fetchTasks()
  fetchStats()
  closeSSE = api.subscribeToEvents(undefined, (data) => {
    if (data.type === 'approval.required') {
      fetchTasks()
      fetchStats()
    }
  })
})

onUnmounted(() => {
  closeSSE?.()
  closeSSE = null
})
</script>

<style scoped>
.role-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 4px;
}

.role-tab {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: var(--radius-md);
  background-color: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.role-tab:hover {
  color: var(--text-primary);
  background-color: var(--bg-hover);
}

.role-tab.active {
  background-color: var(--bg-active);
  color: var(--text-primary);
}

.stats-bar {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-item__value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.stat-item__label {
  font-size: 13px;
  color: var(--text-secondary);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
