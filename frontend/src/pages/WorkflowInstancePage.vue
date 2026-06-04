<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>{{ t('instance.title') }}</h1>
        <p>{{ t('instance.subtitle') }}</p>
      </div>
      <div class="header-actions">
        <select v-model="statusFilter" class="status-filter" @change="fetchInstances">
          <option value="">{{ t('instance.allStatus') }}</option>
          <option value="running">{{ t('instance.statusRunning') }}</option>
          <option value="paused">{{ t('instance.statusPaused') }}</option>
          <option value="completed">{{ t('instance.statusCompleted') }}</option>
          <option value="failed">{{ t('instance.statusFailed') }}</option>
          <option value="cancelled">{{ t('instance.statusCancelled') }}</option>
        </select>
        <button class="btn-refresh" @click="fetchInstances">{{ t('instance.refresh') }}</button>
      </div>
    </div>

    <div v-if="loading" class="empty-state">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="empty-state" style="color: var(--accent-red)">
      {{ t('common.error') }}: {{ error }}
    </div>
    <div v-else class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t('instance.instanceId') }}</th>
            <th>{{ t('instance.project') }}</th>
            <th>{{ t('instance.currentState') }}</th>
            <th>{{ t('instance.status') }}</th>
            <th>{{ t('instance.startedAt') }}</th>
            <th>{{ t('instance.completedAt') }}</th>
            <th>{{ t('instance.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="inst in instances" :key="inst.id" class="instance-row" @click="toggleDetail(inst)">
            <td class="cell-id">
              <span class="instance-id">{{ inst.instance_id }}</span>
            </td>
            <td class="cell-project">{{ inst.project_id }}</td>
            <td>
              <span class="state-badge">{{ formatState(inst.current_state) }}</span>
            </td>
            <td>
              <span class="instance-status" :class="statusClass(inst.status)">{{ statusLabel(inst.status) }}</span>
            </td>
            <td class="cell-time">{{ formatDate(inst.started_at) }}</td>
            <td class="cell-time">{{ formatDate(inst.completed_at) }}</td>
            <td class="cell-actions" @click.stop>
              <button class="btn-flow" @click="openFlowModal(inst)" :title="t('instance.viewFlow')">
                <GitBranch :size="14" />
              </button>
            </td>
          </tr>
          <EmptyTableRow v-if="instances.length === 0" :colspan="7" :message="t('instance.empty')" />
        </tbody>
      </table>
    </div>

    <InstanceFlowModal
      :visible="modalVisible"
      :instance-id="selectedInstance?.instance_id || ''"
      :template-id="selectedInstance?.template_id || null"
      :current-state="selectedInstance?.current_state || ''"
      :instance-status="selectedInstance?.status || ''"
      @close="modalVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { GitBranch } from 'lucide-vue-next'
import { api } from '../api'
import EmptyTableRow from '../components/EmptyTableRow.vue'
import InstanceFlowModal from '../components/InstanceFlowModal.vue'

const { t } = useI18n()

interface Artifact {
  name: string
  stage: string
  agent?: string
  content?: string
}

interface WorkflowInstance {
  id: number
  instance_id: string
  template_id: number | null
  project_id: string
  current_state: string
  participants: string[]
  artifacts: Artifact[]
  status: string
  started_at: string | null
  completed_at: string | null
}

const instances = ref<WorkflowInstance[]>([])
const loading = ref(true)
const error = ref('')
const statusFilter = ref('')
const expandedId = ref<string | null>(null)
const modalVisible = ref(false)
const selectedInstance = ref<WorkflowInstance | null>(null)

async function fetchInstances() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.getWorkflowInstances(statusFilter.value || undefined)
    instances.value = res.instances || []
  } catch (e: any) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

function toggleDetail(inst: WorkflowInstance) {
  expandedId.value = expandedId.value === inst.instance_id ? null : inst.instance_id
}

function openFlowModal(inst: WorkflowInstance) {
  selectedInstance.value = inst
  modalVisible.value = true
}

function statusClass(status: string) {
  const map: Record<string, string> = {
    running: 'status-running',
    paused: 'status-paused',
    completed: 'status-completed',
    failed: 'status-failed',
    cancelled: 'status-cancelled',
  }
  return map[status] || 'status-running'
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    running: t('instance.statusRunning'),
    paused: t('instance.statusPaused'),
    completed: t('instance.statusCompleted'),
    failed: t('instance.statusFailed'),
    cancelled: t('instance.statusCancelled'),
  }
  return map[status] || status
}

function formatState(state: string) {
  if (!state) return '—'
  return state.replace(/_/g, ' ')
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

onMounted(fetchInstances)
</script>

<style scoped>
.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.status-filter {
  padding: 6px 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
}

.btn-refresh {
  padding: 6px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-refresh:hover {
  border-color: var(--border-hover);
  color: var(--text-primary);
}

.table-wrapper {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
}

.data-table td {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
  vertical-align: middle;
}

.data-table tr:last-child td {
  border-bottom: none;
}

.instance-row {
  cursor: pointer;
}

.instance-row:hover td {
  background-color: var(--bg-hover);
}

.cell-id {
  font-family: 'SF Mono', Monaco, monospace;
  font-weight: 700;
  font-size: 13px;
}

.cell-project {
  font-size: 13px;
  color: var(--text-secondary);
}

.state-badge {
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 12px;
  background-color: var(--bg-tertiary);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.instance-status {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: inline-block;
}

.status-running {
  background-color: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.status-paused {
  background-color: rgba(234, 179, 8, 0.15);
  color: var(--accent-yellow);
}

.status-completed {
  background-color: rgba(34, 197, 94, 0.15);
  color: var(--accent-green);
}

.status-failed {
  background-color: rgba(239, 68, 68, 0.15);
  color: var(--accent-red);
}

.status-cancelled {
  background-color: rgba(113, 113, 122, 0.15);
  color: var(--text-tertiary);
}

.cell-time {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.cell-actions {
  display: flex;
  gap: 4px;
}

.btn-flow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-flow:hover {
  border-color: #6366f1;
  color: #6366f1;
  background-color: rgba(99, 102, 241, 0.08);
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}
</style>
