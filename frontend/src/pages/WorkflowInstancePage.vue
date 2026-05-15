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
    <div v-else-if="instances.length === 0" class="empty-state">
      {{ t('instance.empty') }}
    </div>
    <div v-else class="instance-list">
      <div v-for="inst in instances" :key="inst.id" class="instance-card">
        <div class="instance-card__header" @click="toggleDetail(inst)">
          <div class="instance-card__left">
            <div class="instance-card__id">
              <span class="instance-id">{{ inst.instance_id }}</span>
              <span class="instance-status" :class="statusClass(inst.status)">{{ statusLabel(inst.status) }}</span>
            </div>
            <div class="instance-card__meta">
              <span class="meta-item">
                <span class="meta-label">{{ t('instance.project') }}</span>
                <span class="meta-value">{{ inst.project_id }}</span>
              </span>
              <span class="meta-item">
                <span class="meta-label">{{ t('instance.currentState') }}</span>
                <span class="meta-value state-badge">{{ formatState(inst.current_state) }}</span>
              </span>
              <span class="meta-item">
                <span class="meta-label">{{ t('instance.startedAt') }}</span>
                <span class="meta-value">{{ formatDate(inst.started_at) }}</span>
              </span>
            </div>
          </div>
          <div class="instance-card__right-actions">
            <button
              class="btn-flow"
              @click.stop="openFlowModal(inst)"
              :title="t('instance.viewFlow')"
            >
              <GitBranch :size="14" />
              <span>{{ t('instance.viewFlow') }}</span>
            </button>
          </div>
        </div>

        <div v-if="expandedId === inst.instance_id" class="instance-card__detail">
          <div class="detail-section">
            <h4>{{ t('instance.participants') }}</h4>
            <div class="participant-list">
              <span v-for="p in inst.participants" :key="p" class="participant-tag">{{ p }}</span>
              <span v-if="inst.participants.length === 0" class="empty-hint">—</span>
            </div>
          </div>
          <div class="detail-section">
            <h4>{{ t('instance.artifacts') }}</h4>
            <div v-if="inst.artifacts.length === 0" class="empty-hint">{{ t('instance.noArtifacts') }}</div>
            <table v-else class="artifact-table">
              <thead>
                <tr>
                  <th>{{ t('instance.artifactName') }}</th>
                  <th>{{ t('instance.artifactStage') }}</th>
                  <th>{{ t('instance.artifactAgent') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(art, idx) in inst.artifacts" :key="idx">
                  <td>{{ art.name }}</td>
                  <td>{{ art.stage }}</td>
                  <td>{{ art.agent }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="detail-section">
            <h4>{{ t('instance.template') }}</h4>
            <span>{{ inst.template_id ? `#${inst.template_id}` : '—' }}</span>
          </div>
          <div v-if="inst.completed_at" class="detail-section">
            <h4>{{ t('instance.completedAt') }}</h4>
            <span>{{ formatDate(inst.completed_at) }}</span>
          </div>
        </div>
      </div>
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

.instance-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.instance-card {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  transition: border-color 0.15s ease;
}

.instance-card:hover {
  border-color: var(--border-hover);
}

.instance-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  cursor: pointer;
}

.instance-card__left {
  flex: 1;
  min-width: 0;
}

.instance-card__right-actions {
  flex-shrink: 0;
  margin-left: 16px;
}

.btn-flow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.btn-flow:hover {
  border-color: #6366f1;
  color: #6366f1;
  background-color: rgba(99, 102, 241, 0.08);
}

.instance-card__id {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.instance-id {
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.instance-status {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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

.instance-card__meta {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  gap: 6px;
  align-items: center;
}

.meta-label {
  font-size: 12px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.meta-value {
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

.instance-card__detail {
  padding: 0 20px 16px;
  border-top: 1px solid var(--border-color);
  margin-top: 0;
  padding-top: 14px;
}

.detail-section {
  margin-bottom: 14px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h4 {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 8px 0;
}

.participant-list {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.participant-tag {
  display: inline-block;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 9999px;
  background-color: rgba(99, 102, 241, 0.12);
  color: #6366f1;
  font-weight: 500;
}

.empty-hint {
  font-size: 13px;
  color: var(--text-tertiary);
}

.artifact-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.artifact-table th {
  text-align: left;
  padding: 6px 10px;
  font-weight: 600;
  color: var(--text-tertiary);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border-color);
}

.artifact-table td {
  padding: 8px 10px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}

.artifact-table tr:last-child td {
  border-bottom: none;
}
</style>
