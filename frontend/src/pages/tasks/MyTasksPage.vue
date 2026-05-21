<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus, Search, Calendar, User, Tag, Trash2, Edit3 } from 'lucide-vue-next'
import { api } from '../../api'
import { useDialog } from '../../composables/useDialog'

const { t } = useI18n()
const { confirm } = useDialog()

interface Task {
  id: number
  title: string
  description: string
  status: string
  priority: string
  assignee_id: string | null
  assignee_name: string | null
  reporter_id: string
  reporter_name: string
  project_id: number | null
  tags: string[]
  due_date: string | null
  created_at: string
  updated_at: string
}

const tasks = ref<Task[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const statusFilter = ref('')
const priorityFilter = ref('')
const showCreateModal = ref(false)
const editingTask = ref<Task | null>(null)

const statusOptions = [
  { value: '', label: t('taskManagement.allStatus') },
  { value: 'backlog', label: t('taskManagement.statusBacklog') },
  { value: 'todo', label: t('taskManagement.statusTodo') },
  { value: 'in_progress', label: t('taskManagement.statusInProgress') },
  { value: 'in_review', label: t('taskManagement.statusInReview') },
  { value: 'done', label: t('taskManagement.statusDone') },
]

const priorityOptions = [
  { value: '', label: t('taskManagement.allPriority') },
  { value: 'high', label: t('taskManagement.priorityHigh') },
  { value: 'medium', label: t('taskManagement.priorityMedium') },
  { value: 'low', label: t('taskManagement.priorityLow') },
]

const newTask = ref({
  title: '',
  description: '',
  status: 'backlog',
  priority: 'medium',
  assignee_name: '',
  tags: [] as string[],
  due_date: '',
})

const tagInput = ref('')

const filteredTasks = computed(() => {
  let result = tasks.value
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    result = result.filter(
      (task) =>
        task.title.toLowerCase().includes(kw) ||
        task.description.toLowerCase().includes(kw)
    )
  }
  if (statusFilter.value) {
    result = result.filter((task) => task.status === statusFilter.value)
  }
  if (priorityFilter.value) {
    result = result.filter((task) => task.priority === priorityFilter.value)
  }
  return result
})

const loadTasks = async () => {
  loading.value = true
  try {
    const res = await api.getMyTasks()
    tasks.value = res.items
  } catch (e) {
    console.error('Failed to load tasks', e)
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  editingTask.value = null
  newTask.value = {
    title: '',
    description: '',
    status: 'backlog',
    priority: 'medium',
    assignee_name: '',
    tags: [],
    due_date: '',
  }
  tagInput.value = ''
  showCreateModal.value = true
}

const openEditModal = (task: Task) => {
  editingTask.value = task
  newTask.value = {
    title: task.title,
    description: task.description,
    status: task.status,
    priority: task.priority,
    assignee_name: task.assignee_name || '',
    tags: [...task.tags],
    due_date: task.due_date ? task.due_date.slice(0, 10) : '',
  }
  tagInput.value = ''
  showCreateModal.value = true
}

const closeModal = () => {
  showCreateModal.value = false
  editingTask.value = null
}

const addTag = () => {
  const tag = tagInput.value.trim()
  if (tag && !newTask.value.tags.includes(tag)) {
    newTask.value.tags.push(tag)
  }
  tagInput.value = ''
}

const removeTag = (tag: string) => {
  newTask.value.tags = newTask.value.tags.filter((t) => t !== tag)
}

const saveTask = async () => {
  if (!newTask.value.title.trim()) return
  try {
    const payload = {
      ...newTask.value,
      assignee_id: newTask.value.assignee_name || null,
      due_date: newTask.value.due_date || null,
    }
    if (editingTask.value) {
      await api.updateTask(editingTask.value.id, payload)
    } else {
      await api.createTask(payload)
    }
    closeModal()
    await loadTasks()
  } catch (e) {
    console.error('Failed to save task', e)
  }
}

const deleteTask = async (task: Task) => {
  const ok = await confirm({
    title: t('taskManagement.deleteTitle'),
    message: t('taskManagement.confirmDelete', { title: task.title }),
    type: 'danger',
  })
  if (!ok) return
  try {
    await api.deleteTask(task.id)
    await loadTasks()
  } catch (e) {
    console.error('Failed to delete task', e)
  }
}

const getStatusClass = (status: string) => {
  switch (status) {
    case 'backlog':
      return 'status-backlog'
    case 'todo':
      return 'status-todo'
    case 'in_progress':
      return 'status-in-progress'
    case 'in_review':
      return 'status-in-review'
    case 'done':
      return 'status-done'
    default:
      return ''
  }
}

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'backlog':
      return t('taskManagement.statusBacklog')
    case 'todo':
      return t('taskManagement.statusTodo')
    case 'in_progress':
      return t('taskManagement.statusInProgress')
    case 'in_review':
      return t('taskManagement.statusInReview')
    case 'done':
      return t('taskManagement.statusDone')
    default:
      return status
  }
}

const getPriorityClass = (priority: string) => {
  switch (priority) {
    case 'high':
      return 'priority-high'
    case 'medium':
      return 'priority-medium'
    case 'low':
      return 'priority-low'
    default:
      return ''
  }
}

const getPriorityLabel = (priority: string) => {
  switch (priority) {
    case 'high':
      return t('taskManagement.priorityHigh')
    case 'medium':
      return t('taskManagement.priorityMedium')
    case 'low':
      return t('taskManagement.priorityLow')
    default:
      return priority
  }
}

onMounted(loadTasks)
</script>

<template>
  <div class="my-tasks-page">
    <div class="dashboard-header">
      <div>
        <h1>{{ t('taskManagement.myTasksTitle') }}</h1>
        <p>{{ t('taskManagement.myTasksSubtitle') }}</p>
      </div>
      <button class="btn-primary" @click="openCreateModal">
        <Plus :size="16" />
        {{ t('taskManagement.newTask') }}
      </button>
    </div>

    <div class="filter-bar">
      <div class="search-box">
        <Search :size="16" />
        <input
          v-model="searchKeyword"
          type="text"
          :placeholder="t('taskManagement.searchPlaceholder')"
        />
      </div>
      <select v-model="statusFilter" class="filter-select">
        <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
      <select v-model="priorityFilter" class="filter-select">
        <option v-for="opt in priorityOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </div>

    <div v-if="loading" class="empty-state">{{ t('common.loading') }}</div>
    <div v-else-if="filteredTasks.length === 0" class="empty-state">
      {{ t('taskManagement.empty') }}
    </div>
    <div v-else class="task-table-wrapper">
      <table class="task-table">
        <thead>
          <tr>
            <th>{{ t('taskManagement.title') }}</th>
            <th>{{ t('taskManagement.status') }}</th>
            <th>{{ t('taskManagement.priority') }}</th>
            <th>{{ t('taskManagement.assignee') }}</th>
            <th>{{ t('taskManagement.dueDate') }}</th>
            <th>{{ t('taskManagement.tags') }}</th>
            <th>{{ t('taskManagement.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in filteredTasks" :key="task.id">
            <td>
              <div class="task-title">{{ task.title }}</div>
              <div v-if="task.description" class="task-desc">{{ task.description }}</div>
            </td>
            <td>
              <span class="status-badge" :class="getStatusClass(task.status)">
                {{ getStatusLabel(task.status) }}
              </span>
            </td>
            <td>
              <span class="priority-badge" :class="getPriorityClass(task.priority)">
                {{ getPriorityLabel(task.priority) }}
              </span>
            </td>
            <td>
              <div v-if="task.assignee_name" class="task-meta">
                <User :size="12" />
                <span>{{ task.assignee_name }}</span>
              </div>
              <span v-else class="text-muted">{{ t('taskManagement.noAssignee') }}</span>
            </td>
            <td>
              <div v-if="task.due_date" class="task-meta" :class="{ overdue: new Date(task.due_date) < new Date() }">
                <Calendar :size="12" />
                <span>{{ task.due_date.slice(0, 10) }}</span>
              </div>
              <span v-else class="text-muted">-</span>
            </td>
            <td>
              <div v-if="task.tags.length" class="task-tags">
                <span v-for="tag in task.tags" :key="tag" class="tag">{{ tag }}</span>
              </div>
              <span v-else class="text-muted">-</span>
            </td>
            <td>
              <div class="task-actions">
                <button class="btn-icon-sm" @click="openEditModal(task)">
                  <Edit3 :size="14" />
                </button>
                <button class="btn-icon-sm danger" @click="deleteTask(task)">
                  <Trash2 :size="14" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ editingTask ? t('taskManagement.editTitle') : t('taskManagement.createTitle') }}</h3>
          <button class="btn-icon" @click="closeModal">
            <span style="font-size: 20px">&times;</span>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>{{ t('taskManagement.title') }}</label>
            <input v-model="newTask.title" class="setting-input" :placeholder="t('taskManagement.titlePlaceholder')" />
          </div>
          <div class="form-group">
            <label>{{ t('taskManagement.description') }}</label>
            <textarea v-model="newTask.description" class="setting-input" rows="3" :placeholder="t('taskManagement.descriptionPlaceholder')"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>{{ t('taskManagement.status') }}</label>
              <select v-model="newTask.status" class="setting-select">
                <option value="backlog">{{ t('taskManagement.statusBacklog') }}</option>
                <option value="todo">{{ t('taskManagement.statusTodo') }}</option>
                <option value="in_progress">{{ t('taskManagement.statusInProgress') }}</option>
                <option value="in_review">{{ t('taskManagement.statusInReview') }}</option>
                <option value="done">{{ t('taskManagement.statusDone') }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>{{ t('taskManagement.priority') }}</label>
              <select v-model="newTask.priority" class="setting-select">
                <option value="high">{{ t('taskManagement.priorityHigh') }}</option>
                <option value="medium">{{ t('taskManagement.priorityMedium') }}</option>
                <option value="low">{{ t('taskManagement.priorityLow') }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>{{ t('taskManagement.assignee') }}</label>
              <input v-model="newTask.assignee_name" class="setting-input" :placeholder="t('taskManagement.assigneePlaceholder')" />
            </div>
            <div class="form-group">
              <label>{{ t('taskManagement.dueDate') }}</label>
              <input v-model="newTask.due_date" type="date" class="setting-input" />
            </div>
          </div>
          <div class="form-group">
            <label>{{ t('taskManagement.tags') }}</label>
            <div class="tags-input">
              <input v-model="tagInput" class="setting-input" :placeholder="t('taskManagement.tagsPlaceholder')" @keydown.enter.prevent="addTag" />
            </div>
            <div v-if="newTask.tags.length" class="tags-list">
              <span v-for="tag in newTask.tags" :key="tag" class="tag removable" @click="removeTag(tag)">
                {{ tag }} &times;
              </span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeModal">{{ t('common.cancel') }}</button>
          <button class="btn-primary" @click="saveTask">{{ t('common.save') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.my-tasks-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.dashboard-header {
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.dashboard-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.dashboard-header p {
  font-size: 14px;
  color: var(--text-secondary);
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  padding: 8px 16px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 14px;
  cursor: pointer;
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}

.btn-icon:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-icon-sm {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
}

.btn-icon-sm:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-icon-sm.danger:hover {
  color: var(--accent-red);
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.search-box {
  flex: 1;
  max-width: 320px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.search-box input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
}

.search-box input::placeholder {
  color: var(--text-muted);
}

.filter-select {
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  min-width: 140px;
}

.task-table-wrapper {
  flex: 1;
  overflow: auto;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}

.task-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.task-table th {
  text-align: left;
  padding: 12px 16px;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
}

.task-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
  vertical-align: top;
}

.task-table tbody tr:hover {
  background: var(--bg-hover);
}

.task-title {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.task-desc {
  font-size: 12px;
  color: var(--text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.status-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 9999px;
  white-space: nowrap;
}

.status-backlog {
  background: rgba(113, 113, 122, 0.15);
  color: #a1a1aa;
}

.status-todo {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.status-in-progress {
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
}

.status-in-review {
  background: rgba(168, 85, 247, 0.15);
  color: #a855f7;
}

.status-done {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.priority-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  text-transform: uppercase;
}

.priority-high {
  background: var(--priority-high-bg);
  color: var(--priority-high-text);
}

.priority-medium {
  background: var(--priority-medium-bg);
  color: var(--priority-medium-text);
}

.priority-low {
  background: var(--priority-low-bg);
  color: var(--priority-low-text);
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.task-meta.overdue {
  color: var(--accent-red);
}

.task-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.tag.removable {
  cursor: pointer;
}

.tag.removable:hover {
  background: var(--accent-red);
  color: white;
}

.task-actions {
  display: flex;
  gap: 4px;
}

.text-muted {
  color: var(--text-muted);
  font-size: 12px;
}

.empty-state {
  padding: 48px;
  text-align: center;
  color: var(--text-muted);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 520px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-row {
  display: flex;
  gap: 16px;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
</style>
