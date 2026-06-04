<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../api'
import EmptyTableRow from '../components/EmptyTableRow.vue'
import { Plus, Play, Pause, Trash2, Edit3, History, X, CheckCircle, XCircle, Loader } from 'lucide-vue-next'

const { t } = useI18n()

interface ScheduledTask {
  id: number
  name: string
  description: string
  task_type: string
  trigger_type: string
  cron_expression: string
  is_enabled: number
  config_json: string
  last_run_at: string | null
  next_run_at: string | null
  created_at: string
  updated_at: string
}

interface TaskLog {
  id: number
  task_id: number
  status: string
  output: string
  error: string
  started_at: string
  completed_at: string | null
}

const tasks = ref<ScheduledTask[]>([])
const loading = ref(false)
const error = ref('')

const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)

const form = ref({
  name: '',
  description: '',
  task_type: 'workflow_instance',
  trigger_type: 'cron',
  cron_expression: '0 9 * * 1-5',
  is_enabled: 1,
  config_json: '{}',
})

const showLogsModal = ref(false)
const logsTaskId = ref<number | null>(null)
const logs = ref<TaskLog[]>([])
const logsLoading = ref(false)

const configForm = ref({
  template_id: '',
  project_id: '',
  context: '{}',
})

const triggerOptions = [
  { label: 'Cron 表达式', value: 'cron' },
  { label: '固定间隔', value: 'interval' },
  { label: '一次性', value: 'date' },
]

const intervalUnits = ref({ minutes: 30 })

onMounted(() => {
  loadTasks()
})

async function loadTasks() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.getScheduledTasks()
    tasks.value = res.tasks
  } catch (err) {
    error.value = t('scheduledTasks.loadError')
    console.error('Failed to load scheduled tasks:', err)
  } finally {
    loading.value = false
  }
}

function openCreateModal() {
  isEditing.value = false
  editingId.value = null
  form.value = {
    name: '',
    description: '',
    task_type: 'workflow_instance',
    trigger_type: 'cron',
    cron_expression: '0 9 * * 1-5',
    is_enabled: 1,
    config_json: '{}',
  }
  configForm.value = { template_id: '', project_id: '', context: '{}' }
  showModal.value = true
}

function openEditModal(task: ScheduledTask) {
  isEditing.value = true
  editingId.value = task.id
  form.value = {
    name: task.name,
    description: task.description,
    task_type: task.task_type,
    trigger_type: task.trigger_type,
    cron_expression: task.cron_expression,
    is_enabled: task.is_enabled,
    config_json: task.config_json,
  }
  try {
    const cfg = JSON.parse(task.config_json)
    configForm.value = {
      template_id: String(cfg.template_id || ''),
      project_id: cfg.project_id || '',
      context: JSON.stringify(cfg.context || {}, null, 2),
    }
  } catch {
    configForm.value = { template_id: '', project_id: '', context: '{}' }
  }
  showModal.value = true
}

function buildConfigJson(): string {
  if (form.value.task_type === 'workflow_instance') {
    return JSON.stringify({
      template_id: Number(configForm.value.template_id) || undefined,
      project_id: configForm.value.project_id || undefined,
      context: JSON.parse(configForm.value.context || '{}'),
    })
  }
  return form.value.config_json
}

async function saveTask() {
  if (!form.value.name) return
  const data = { ...form.value, config_json: buildConfigJson() }
  try {
    if (isEditing.value && editingId.value) {
      await api.updateScheduledTask(editingId.value, data)
    } else {
      await api.createScheduledTask(data)
    }
    showModal.value = false
    loadTasks()
  } catch (err) {
    console.error('Failed to save scheduled task:', err)
  }
}

async function deleteTask(id: number) {
  if (!confirm(t('scheduledTasks.confirmDelete'))) return
  try {
    await api.deleteScheduledTask(id)
    loadTasks()
  } catch (err) {
    console.error('Failed to delete scheduled task:', err)
  }
}

async function toggleTask(id: number) {
  try {
    await api.toggleScheduledTask(id)
    loadTasks()
  } catch (err) {
    console.error('Failed to toggle scheduled task:', err)
  }
}

async function runTaskNow(id: number) {
  try {
    await api.runScheduledTask(id)
    loadTasks()
  } catch (err) {
    console.error('Failed to run scheduled task:', err)
  }
}

async function openLogs(taskId: number) {
  logsTaskId.value = taskId
  showLogsModal.value = true
  logsLoading.value = true
  try {
    const res = await api.getScheduledTaskLogs(taskId, 50)
    logs.value = res.logs
  } catch (err) {
    console.error('Failed to load logs:', err)
  } finally {
    logsLoading.value = false
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

function getTaskTypeLabel(type: string): string {
  return type === 'workflow_instance' ? t('scheduledTasks.typeWorkflow') : t('scheduledTasks.typeSystem')
}

function getTriggerLabel(type: string): string {
  const map: Record<string, string> = { cron: 'Cron', interval: 'Interval', date: 'Date' }
  return map[type] || type
}

const cronPresets = [
  { label: '每分钟', value: '* * * * *' },
  { label: '每小时', value: '0 * * * *' },
  { label: '每天 9:00', value: '0 9 * * *' },
  { label: '工作日 9:00', value: '0 9 * * 1-5' },
  { label: '每周一 9:00', value: '0 9 * * 1' },
  { label: '每月 1 日 9:00', value: '0 9 1 * *' },
]
</script>

<template>
  <div class="scheduled-tasks-page">
    <div class="page-header">
      <div>
        <h1>{{ t('scheduledTasks.title') }}</h1>
        <p class="subtitle">{{ t('scheduledTasks.subtitle') }}</p>
      </div>
      <button class="btn btn-primary" @click="openCreateModal">
        <Plus :size="16" />
        {{ t('scheduledTasks.newTask') }}
      </button>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t('scheduledTasks.name') }}</th>
            <th>{{ t('scheduledTasks.taskType') }}</th>
            <th>{{ t('scheduledTasks.triggerType') }}</th>
            <th>{{ t('scheduledTasks.cronExpression') }}</th>
            <th>{{ t('scheduledTasks.enabled') }}</th>
            <th>{{ t('scheduledTasks.lastRun') }}</th>
            <th>{{ t('common.edit') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in tasks" :key="task.id" :class="{ 'row-disabled': !task.is_enabled }">
            <td class="cell-name">
              {{ task.name }}
              <span v-if="task.description" class="cell-desc-inline">{{ task.description }}</span>
            </td>
            <td>
              <span class="type-badge">{{ getTaskTypeLabel(task.task_type) }}</span>
            </td>
            <td>
              <span class="trigger-badge">{{ getTriggerLabel(task.trigger_type) }}</span>
            </td>
            <td class="cell-cron">{{ task.cron_expression }}</td>
            <td>
              <span :class="['status-dot', task.is_enabled ? 'enabled' : 'disabled']" />
              <span>{{ task.is_enabled ? t('scheduledTasks.enabled') : t('scheduledTasks.disabled') }}</span>
            </td>
            <td class="cell-time">{{ formatDate(task.last_run_at) }}</td>
            <td class="cell-actions">
              <button class="icon-btn" :title="t('scheduledTasks.runNow')" @click="runTaskNow(task.id)">
                <Play :size="14" />
              </button>
              <button class="icon-btn" :title="task.is_enabled ? t('scheduledTasks.disable') : t('scheduledTasks.enable')" @click="toggleTask(task.id)">
                <Pause v-if="task.is_enabled" :size="14" />
                <Play v-else :size="14" />
              </button>
              <button class="icon-btn" :title="t('scheduledTasks.logs')" @click="openLogs(task.id)">
                <History :size="14" />
              </button>
              <button class="icon-btn" :title="t('common.edit')" @click="openEditModal(task)">
                <Edit3 :size="14" />
              </button>
              <button class="icon-btn danger" :title="t('common.delete')" @click="deleteTask(task.id)">
                <Trash2 :size="14" />
              </button>
            </td>
          </tr>
          <EmptyTableRow v-if="tasks.length === 0" :colspan="7" :message="t('scheduledTasks.empty')" />
        </tbody>
      </table>
    </div>

    <!-- Create/Edit Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
        <div class="modal">
          <div class="modal-header">
            <h3>{{ isEditing ? t('scheduledTasks.editTitle') : t('scheduledTasks.createTitle') }}</h3>
            <button class="icon-btn" @click="showModal = false">
              <X :size="18" />
            </button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>{{ t('scheduledTasks.name') }} *</label>
              <input v-model="form.name" type="text" :placeholder="t('scheduledTasks.namePlaceholder')" />
            </div>
            <div class="form-group">
              <label>{{ t('scheduledTasks.description') }}</label>
              <textarea v-model="form.description" rows="2" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>{{ t('scheduledTasks.taskType') }}</label>
                <select v-model="form.task_type">
                  <option value="workflow_instance">{{ t('scheduledTasks.typeWorkflow') }}</option>
                  <option value="system_task">{{ t('scheduledTasks.typeSystem') }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>{{ t('scheduledTasks.triggerType') }}</label>
                <select v-model="form.trigger_type">
                  <option v-for="opt in triggerOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
            </div>

            <!-- Cron Expression -->
            <div v-if="form.trigger_type === 'cron'" class="form-group">
              <label>{{ t('scheduledTasks.cronExpression') }}</label>
              <input v-model="form.cron_expression" type="text" placeholder="0 9 * * 1-5" />
              <div class="cron-presets">
                <button v-for="preset in cronPresets" :key="preset.value" class="preset-btn" @click="form.cron_expression = preset.value">
                  {{ preset.label }}
                </button>
              </div>
            </div>

            <!-- Interval -->
            <div v-if="form.trigger_type === 'interval'" class="form-row">
              <div class="form-group">
                <label>{{ t('scheduledTasks.intervalMinutes') }}</label>
                <input v-model.number="intervalUnits.minutes" type="number" min="1" />
              </div>
            </div>

            <!-- Date -->
            <div v-if="form.trigger_type === 'date'" class="form-group">
              <label>{{ t('scheduledTasks.runDate') }}</label>
              <input v-model="form.cron_expression" type="datetime-local" />
            </div>

            <!-- Workflow Config -->
            <template v-if="form.task_type === 'workflow_instance'">
              <div class="form-row">
                <div class="form-group">
                  <label>{{ t('scheduledTasks.templateId') }}</label>
                  <input v-model="configForm.template_id" type="number" />
                </div>
                <div class="form-group">
                  <label>{{ t('scheduledTasks.projectId') }}</label>
                  <input v-model="configForm.project_id" type="text" />
                </div>
              </div>
              <div class="form-group">
                <label>{{ t('scheduledTasks.context') }}</label>
                <textarea v-model="configForm.context" rows="3" />
              </div>
            </template>

            <div class="form-group">
              <label class="checkbox-label">
                <input v-model="form.is_enabled" type="checkbox" :true-value="1" :false-value="0" />
                {{ t('scheduledTasks.enabled') }}
              </label>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showModal = false">{{ t('common.cancel') }}</button>
            <button class="btn btn-primary" :disabled="!form.name" @click="saveTask">{{ t('common.save') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Logs Modal -->
    <Teleport to="body">
      <div v-if="showLogsModal" class="modal-overlay" @click.self="showLogsModal = false">
        <div class="modal modal-lg">
          <div class="modal-header">
            <h3>{{ t('scheduledTasks.logsTitle') }}</h3>
            <button class="icon-btn" @click="showLogsModal = false">
              <X :size="18" />
            </button>
          </div>
          <div class="modal-body">
            <div v-if="logsLoading" class="loading">{{ t('common.loading') }}...</div>
            <div v-else-if="logs.length === 0" class="empty">{{ t('scheduledTasks.noLogs') }}</div>
            <div v-else class="logs-list">
              <div v-for="log in logs" :key="log.id" class="log-item">
                <div class="log-header">
                  <span :class="['log-status', log.status]">
                    <CheckCircle v-if="log.status === 'success'" :size="14" />
                    <XCircle v-else-if="log.status === 'failed'" :size="14" />
                    <Loader v-else :size="14" />
                    {{ log.status }}
                  </span>
                  <span class="log-time">{{ formatDate(log.started_at) }}</span>
                </div>
                <pre v-if="log.output" class="log-output">{{ log.output }}</pre>
                <pre v-if="log.error" class="log-error">{{ log.error }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.scheduled-tasks-page {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
}

.page-header h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.subtitle {
  color: var(--text-secondary);
  margin: 4px 0 0;
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

.data-table tbody tr:hover td {
  background-color: var(--bg-hover);
}

.row-disabled td {
  opacity: 0.6;
}

.cell-name {
  font-weight: 600;
  font-size: 13px;
}

.cell-desc-inline {
  display: block;
  font-weight: 400;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.type-badge,
.trigger-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 12px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  display: inline-block;
}

.cell-cron {
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 12px;
  color: var(--text-secondary);
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}

.status-dot.enabled {
  background: #22c55e;
}

.status-dot.disabled {
  background: #9ca3af;
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

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.icon-btn.danger:hover {
  background: #fee2e2;
  color: #dc2626;
}

.loading,
.error {
  text-align: center;
  padding: 48px;
  color: var(--text-secondary);
}

.error {
  color: #dc2626;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: var(--surface-color);
  border-radius: 12px;
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-lg {
  max-width: 720px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 6px;
  color: var(--text-primary);
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary-color);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label input {
  width: auto;
}

.cron-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.preset-btn {
  font-size: 11px;
  padding: 4px 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: pointer;
}

.preset-btn:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

/* Logs */
.logs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-item {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.log-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.log-status.success {
  color: #22c55e;
}

.log-status.failed {
  color: #dc2626;
}

.log-status.running {
  color: #f59e0b;
}

.log-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.log-output,
.log-error {
  font-size: 12px;
  padding: 8px;
  border-radius: 6px;
  margin: 4px 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.log-output {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.log-error {
  background: #fee2e2;
  color: #dc2626;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--primary-color);
  color: #fff;
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
