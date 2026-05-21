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
            <td class="wf-name">
              {{ wf.name }}
              <span v-if="wf.is_template" class="template-badge">{{ categoryLabel(wf.category) }}</span>
            </td>
            <td class="wf-desc">
              <span v-if="!editingDescription[wf.id]" @click="startEditDescription(wf)" class="desc-text">{{ wf.description || '—' }}</span>
              <input
                v-else
                v-model="editingDescription[wf.id]"
                class="desc-input"
                type="text"
                @blur="saveDescription(wf)"
                @keydown.enter="saveDescription(wf)"
                @keydown.esc="cancelEditDescription(wf)"
                ref="descInputRef"
              />
            </td>
            <td class="wf-version">{{ wf.version }}</td>
            <td>
              <span class="wf-status" :class="statusClass(wf.status)">{{ statusLabel(wf.status) }}</span>
            </td>
            <td class="wf-time">{{ formatDate(wf.created_at) }}</td>
            <td class="wf-actions">
              <button class="btn-action btn-edit" @click="handleEdit(wf)">{{ t('common.edit') }}</button>
              <button v-if="wf.status === 'draft'" class="btn-action btn-enable" @click="handleEnable(wf)">{{ t('workflow.enable') }}</button>
              <button v-if="wf.status === 'active'" class="btn-action btn-archive" @click="handleArchive(wf)">{{ t('workflow.archive') }}</button>
              <button v-if="wf.is_template" class="btn-action btn-instantiate" @click="handleInstantiate(wf)">{{ t('workflow.instantiate') }}</button>
              <button v-if="!wf.is_template" class="btn-action btn-delete" @click="handleDelete(wf)">{{ t('common.delete') }}</button>
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
import { useDialog } from '../composables/useDialog'

const { t } = useI18n()
const router = useRouter()
const { addTab } = useTabs()
const { showConfirm, showPrompt } = useDialog()

interface Workflow {
  id: number
  name: string
  description: string
  version: string
  status: string
  is_template: boolean
  category: string | null
  created_at: string
  updated_at: string
}

const workflows = ref<Workflow[]>([])
const loading = ref(true)
const error = ref('')
const editingDescription = ref<Record<number, string | undefined>>({})

function startEditDescription(wf: Workflow) {
  editingDescription.value[wf.id] = wf.description || ''
}

async function saveDescription(wf: Workflow) {
  const newDesc = editingDescription.value[wf.id]
  if (newDesc === undefined) return
  if (newDesc !== wf.description) {
    try {
      await api.saveWorkflow(wf.id, { description: newDesc })
      wf.description = newDesc
    } catch (e: any) {
      error.value = e.message || String(e)
    }
  }
  editingDescription.value[wf.id] = undefined
}

function cancelEditDescription(wf: Workflow) {
  editingDescription.value[wf.id] = undefined
}

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
  const confirmed = await showConfirm({
    title: t('common.confirm'),
    message: t('workflow.confirmDelete', { name: wf.name }),
    type: 'warning',
    confirmText: t('common.delete'),
    cancelText: t('common.cancel'),
  })
  if (!confirmed) return
  try {
    await api.deleteWorkflow(wf.id)
    await fetchWorkflows()
  } catch (e: any) {
    error.value = e.message || String(e)
  }
}

async function handleEnable(wf: Workflow) {
  const confirmed = await showConfirm({
    title: t('common.confirm'),
    message: t('workflow.confirmEnable', { name: wf.name }),
    type: 'confirm',
    confirmText: t('workflow.enable'),
    cancelText: t('common.cancel'),
  })
  if (!confirmed) return
  try {
    await api.saveWorkflow(wf.id, { status: 'active' })
    await fetchWorkflows()
  } catch (e: any) {
    error.value = e.message || String(e)
  }
}

async function handleArchive(wf: Workflow) {
  const confirmed = await showConfirm({
    title: t('common.confirm'),
    message: t('workflow.confirmArchive', { name: wf.name }),
    type: 'warning',
    confirmText: t('workflow.archive'),
    cancelText: t('common.cancel'),
  })
  if (!confirmed) return
  try {
    await api.saveWorkflow(wf.id, { status: 'archived' })
    await fetchWorkflows()
  } catch (e: any) {
    error.value = e.message || String(e)
  }
}

async function handleInstantiate(wf: Workflow) {
  const projectId = await showPrompt({
    title: t('workflow.instantiate'),
    message: t('workflow.enterProjectId'),
    placeholder: 'project-id',
  })
  if (!projectId) return
  try {
    const result = await api.instantiateTemplate(wf.id, projectId)
    await showConfirm({
      title: t('common.confirm'),
      message: t('workflow.instanceCreated', { instanceId: result.instance_id }),
      type: 'success',
      showCancel: false,
      confirmText: t('common.confirm'),
    })
  } catch (e: any) {
    error.value = e.message || String(e)
  }
}

function categoryLabel(category: string | null) {
  const map: Record<string, string> = {
    standard: t('workflow.categoryStandard'),
    hotfix: t('workflow.categoryHotfix'),
    db_change: t('workflow.categoryDbChange'),
    auto_fix: t('workflow.categoryAutoFix'),
  }
  return map[category || ''] || category || ''
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

.desc-text {
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: background-color 0.15s ease;
}

.desc-text:hover {
  background-color: var(--bg-hover);
}

.desc-input {
  width: 100%;
  background-color: var(--bg-primary);
  border: 1px solid var(--accent-blue);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  padding: 4px 8px;
  font-size: 13px;
  outline: none;
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

.template-badge {
  display: inline-block;
  margin-left: 8px;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 9999px;
  background-color: rgba(99, 102, 241, 0.15);
  color: #6366f1;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  vertical-align: middle;
}

.btn-instantiate {
  border-color: #6366f1;
  color: #6366f1;
}

.btn-instantiate:hover {
  background-color: rgba(99, 102, 241, 0.1);
}

.btn-enable {
  border-color: var(--accent-green);
  color: var(--accent-green);
}

.btn-enable:hover {
  background-color: rgba(34, 197, 94, 0.1);
}

.btn-archive {
  border-color: var(--text-tertiary);
  color: var(--text-tertiary);
}

.btn-archive:hover {
  background-color: rgba(113, 113, 122, 0.1);
}
</style>
