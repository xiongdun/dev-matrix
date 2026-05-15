<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>{{ t('workbench.title') }}</h1>
        <p>{{ t('workbench.subtitle') }}</p>
      </div>
    </div>

    <div v-if="loading" class="empty-state">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="empty-state" style="color: var(--accent-red)">
      {{ t('common.error') }}: {{ error }}
    </div>
    <div v-else-if="tasks.length === 0" class="empty-state">
      {{ t('workbench.noTasks') }}
    </div>
    <div v-else class="task-table-wrapper">
      <table class="task-table">
        <thead>
          <tr>
            <th>{{ t('workbench.colProject') }}</th>
            <th>{{ t('workbench.colStage') }}</th>
            <th>{{ t('workbench.colAgent') }}</th>
            <th>{{ t('workbench.colStatus') }}</th>
            <th>{{ t('workbench.colArrived') }}</th>
            <th>{{ t('workbench.colAction') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="task in tasks"
            :key="task.id"
            class="task-row"
            @click="goToDetail(task.id)"
          >
            <td class="cell-project">{{ task.project_id }}</td>
            <td class="cell-stage">{{ task.stage_name }}</td>
            <td class="cell-agent">
              <span class="agent-tag">{{ task.agent_role }}</span>
            </td>
            <td>
              <span class="status-badge" :class="task.status">{{ statusLabel(task.status) }}</span>
            </td>
            <td class="cell-time">{{ formatTime(task.arrived_at) }}</td>
            <td>
              <button class="btn-enter" @click.stop="goToDetail(task.id)">
                <ArrowRight :size="14" />
                {{ t('workbench.enter') }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ArrowRight } from 'lucide-vue-next'
import { api } from '../api'

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

const mockTasks: Task[] = [
  {
    id: 1,
    project_id: 'dev-matrix-001',
    stage_id: 'analyze_requirement',
    stage_name: '需求分析',
    agent_role: 'business_analyst',
    status: 'pending',
    output_json: JSON.stringify({ content: '需求分析内容...', metadata: {} }, null, 2),
    feedback: null,
    arrived_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    processed_at: null,
  },
  {
    id: 2,
    project_id: 'dev-matrix-002',
    stage_id: 'generate_prd',
    stage_name: 'PRD 生成',
    agent_role: 'product_manager',
    status: 'pending',
    output_json: JSON.stringify({ content: 'PRD 内容...', metadata: {} }, null, 2),
    feedback: null,
    arrived_at: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    processed_at: null,
  },
  {
    id: 3,
    project_id: 'dev-matrix-003',
    stage_id: 'analyze_code_impact',
    stage_name: '代码影响分析',
    agent_role: 'architect',
    status: 'retrying',
    output_json: JSON.stringify({ content: '影响分析内容...', metadata: {} }, null, 2),
    feedback: '请补充数据库迁移脚本的影响分析',
    arrived_at: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    processed_at: null,
  },
  {
    id: 4,
    project_id: 'dev-matrix-004',
    stage_id: 'generate_patch',
    stage_name: '补丁生成',
    agent_role: 'developer',
    status: 'approved',
    output_json: JSON.stringify({ content: '补丁内容...', metadata: {} }, null, 2),
    feedback: null,
    arrived_at: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(),
    processed_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
  },
  {
    id: 5,
    project_id: 'hotfix-2026-001',
    stage_id: 'execute_tests',
    stage_name: '测试执行',
    agent_role: 'qa',
    status: 'rejected',
    output_json: JSON.stringify({ content: '测试结果...', metadata: {} }, null, 2),
    feedback: '集成测试失败，请修复后再提交',
    arrived_at: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
    processed_at: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString(),
  },
]

const tasks = ref<Task[]>(mockTasks)
const loading = ref(false)
const error = ref('')

let closeSSE: (() => void) | null = null

function goToDetail(taskId: number) {
  router.push(`/workbench/task/${taskId}`)
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: t('workbench.pending'),
    retrying: t('workbench.retry'),
    approved: t('workbench.approved'),
    rejected: t('workbench.rejected'),
    completed: t('workbench.completed'),
  }
  return map[status] || status
}

function formatTime(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  closeSSE = api.subscribeToEvents(undefined, (data) => {
    if (data.type === 'approval.required') {
      // refresh
    }
  })
})

onUnmounted(() => {
  closeSSE?.()
  closeSSE = null
})
</script>

<style scoped>
.task-table-wrapper {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.task-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.task-table thead {
  background-color: var(--bg-tertiary);
}

.task-table th {
  text-align: left;
  padding: 10px 16px;
  font-weight: 600;
  color: var(--text-tertiary);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border-color);
}

.task-table td {
  padding: 12px 16px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}

.task-row {
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.task-row:hover {
  background-color: var(--bg-hover);
}

.task-row:last-child td {
  border-bottom: none;
}

.cell-project {
  font-weight: 600;
  color: var(--text-primary);
}

.cell-stage {
  color: var(--text-secondary);
}

.cell-agent {
  color: var(--text-secondary);
}

.agent-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 9999px;
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
}

.cell-time {
  font-size: 12px;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-badge.pending {
  background-color: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.status-badge.retrying {
  background-color: rgba(234, 179, 8, 0.15);
  color: var(--accent-yellow);
}

.status-badge.approved {
  background-color: rgba(34, 197, 94, 0.15);
  color: var(--accent-green);
}

.status-badge.rejected {
  background-color: rgba(239, 68, 68, 0.15);
  color: var(--accent-red);
}

.status-badge.completed {
  background-color: rgba(113, 113, 122, 0.15);
  color: var(--text-tertiary);
}

.btn-enter {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-enter:hover {
  border-color: #6366f1;
  color: #6366f1;
  background-color: rgba(99, 102, 241, 0.08);
}
</style>
