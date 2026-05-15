<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>{{ t('workflow.title') }}</h1>
        <p>{{ t('workflow.subtitle') }}</p>
      </div>
      <button class="btn-create" @click="handleCreate">
        {{ t('workflow.create') }}
      </button>
    </div>

    <div v-if="loading" class="empty-state">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="empty-state" style="color: var(--accent-red)">
      {{ t('common.error') }}: {{ error }}
    </div>
    <div v-else-if="workflows.length === 0" class="empty-state">
      {{ t('workflow.empty') }}
    </div>
    <div v-else class="table-wrapper">
      <table class="wf-table">
        <thead>
          <tr>
            <th>{{ t('workflow.name') }}</th>
            <th>{{ t('workflow.description') }}</th>
            <th>{{ t('workflow.version') }}</th>
            <th>{{ t('workflow.status') }}</th>
            <th>{{ t('workflow.createdAt') }}</th>
            <th>{{ t('workflow.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="wf in workflows" :key="wf.id">
            <td class="wf-name">{{ wf.name }}</td>
            <td class="wf-desc">{{ wf.description || '—' }}</td>
            <td class="wf-version">{{ wf.version }}</td>
            <td>
              <span class="wf-status" :class="statusClass(wf.status)">{{ statusLabel(wf.status) }}</span>
            </td>
            <td class="wf-time">{{ formatDate(wf.created_at) }}</td>
            <td class="wf-actions">
              <button class="btn-action btn-edit" @click="handleEdit(wf)">{{ t('common.edit') }}</button>
              <button class="btn-action btn-delete" @click="handleDelete(wf)">{{ t('common.delete') }}</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '../api'
import { useTabs } from '../composables/useTabs'

const { t } = useI18n()
const router = useRouter()
const { addTab } = useTabs()

interface Workflow {
  id: number
  name: string
  description: string
  version: string
  status: string
  created_at: string
  updated_at: string
}

const workflows = ref<Workflow[]>([])
const loading = ref(true)
const error = ref('')

async function fetchWorkflows() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.getWorkflows()
    workflows.value = res.workflows || []
  } catch (e: any) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

function handleCreate() {
  router.push('/workflow/editor')
  addTab('workflow-editor', t('workflow.newWorkflow'), '/workflow/editor')
}

function handleEdit(wf: Workflow) {
  router.push(`/workflow/editor/${wf.id}`)
  addTab(`workflow-editor-${wf.id}`, `${t('workflow.editor')} - ${wf.name}`, `/workflow/editor/${wf.id}`)
}

async function handleDelete(wf: Workflow) {
  if (!confirm(t('workflow.confirmDelete', { name: wf.name }))) return
  try {
    await api.deleteWorkflow(wf.id)
    await fetchWorkflows()
  } catch (e: any) {
    error.value = e.message || String(e)
  }
}

function statusClass(status: string) {
  const map: Record<string, string> = {
    draft: 'status-draft',
    active: 'status-active',
    archived: 'status-archived',
  }
  return map[status] || 'status-draft'
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    draft: t('workflow.statusDraft'),
    active: t('workflow.statusActive'),
    archived: t('workflow.statusArchived'),
  }
  return map[status] || status
}

function formatDate(dateStr: string) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

onMounted(fetchWorkflows)
</script>

<style scoped>
.btn-create {
  padding: 8px 20px;
  border-radius: var(--radius-md);
  border: none;
  background-color: var(--accent-blue);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.btn-create:hover {
  background-color: var(--primary-color-dark);
}

.table-wrapper {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.wf-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.wf-table th {
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

.wf-table td {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}

.wf-table tr:last-child td {
  border-bottom: none;
}

.wf-table tr:hover td {
  background-color: var(--bg-hover);
}

.wf-name {
  font-weight: 600;
  font-size: 13px;
}

.wf-desc {
  color: var(--text-secondary);
  font-size: 13px;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wf-version {
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 12px;
  color: var(--text-tertiary);
}

.wf-time {
  font-size: 13px;
  color: var(--text-secondary);
}

.wf-status {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-draft {
  background-color: rgba(234, 179, 8, 0.15);
  color: var(--accent-yellow);
}

.status-active {
  background-color: rgba(34, 197, 94, 0.15);
  color: var(--accent-green);
}

.status-archived {
  background-color: rgba(113, 113, 122, 0.15);
  color: var(--text-tertiary);
}

.wf-actions {
  display: flex;
  gap: 8px;
}

.btn-action {
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-action:hover {
  border-color: var(--border-hover);
  color: var(--text-primary);
}

.btn-delete:hover {
  border-color: var(--accent-red);
  color: var(--accent-red);
}
</style>
