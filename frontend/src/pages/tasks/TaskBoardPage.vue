<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus, Calendar, Tag, User, MoreHorizontal, Trash2, Edit3 } from 'lucide-vue-next'
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
const showCreateModal = ref(false)
const editingTask = ref<Task | null>(null)

const columns = [
  { id: 'backlog', title: t('taskManagement.statusBacklog'), color: '#71717a' },
  { id: 'todo', title: t('taskManagement.statusTodo'), color: '#3b82f6' },
  { id: 'in_progress', title: t('taskManagement.statusInProgress'), color: '#eab308' },
  { id: 'in_review', title: t('taskManagement.statusInReview'), color: '#a855f7' },
  { id: 'done', title: t('taskManagement.statusDone'), color: '#22c55e' },
]

const tasksByColumn = computed(() => {
  const map: Record<string, Task[]> = {}
  columns.forEach(col => {
    map[col.id] = tasks.value.filter(t => t.status === col.id)
  })
  return map
})

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

const loadTasks = async () => {
  loading.value = true
  try {
    const res = await api.getTasks()
    tasks.value = res.items
  } catch (e) {
    console.error('Failed to load tasks', e)
  } finally {
    loading.value = false
  }
}

const openCreateModal = (status?: string) => {
  editingTask.value = null
  newTask.value = {
    title: '',
    description: '',
    status: status || 'backlog',
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
  newTask.value.tags = newTask.value.tags.filter(t => t !== tag)
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

// Drag and drop
const draggedTask = ref<Task | null>(null)

const onDragStart = (task: Task) => {
  draggedTask.value = task
}

const onDragOver = (e: DragEvent) => {
  e.preventDefault()
}

const onDrop = async (e: DragEvent, status: string) => {
  e.preventDefault()
  if (!draggedTask.value) return
  if (draggedTask.value.status === status) return
  try {
    await api.updateTaskStatus(draggedTask.value.id, status)
    draggedTask.value.status = status
    await loadTasks()
  } catch (err) {
    console.error('Failed to update status', err)
  }
  draggedTask.value = null
}

const getPriorityClass = (priority: string) => {
  switch (priority) {
    case 'high': return 'priority-high'
    case 'medium': return 'priority-medium'
    case 'low': return 'priority-low'
    default: return ''
  }
}

const getPriorityLabel = (priority: string) => {
  switch (priority) {
    case 'high': return t('taskManagement.priorityHigh')
    case 'medium': return t('taskManagement.priorityMedium')
    case 'low': return t('taskManagement.priorityLow')
    default: return priority
  }
}

onMounted(loadTasks)
</script>

<template>
  <div class="task-board-page">
    <div class="dashboard-header">
      <div>
        <h1>{{ t('taskManagement.boardTitle') }}</h1>
        <p>{{ t('taskManagement.boardSubtitle') }}</p>
      </div>
      <button class="btn-primary" @click="openCreateModal()">
        <Plus :size="16" />
        {{ t('taskManagement.newTask') }}
      </button>
    </div>

    <div v-if="loading" class="empty-state">{{ t('common.loading') }}</div>

    <div v-else class="board-container">
      <div
        v-for="col in columns"
        :key="col.id"
        class="board-column"
        @dragover="onDragOver"
        @drop="onDrop($event, col.id)"
      >
        <div class="column-header">
          <div class="column-title">
            <span class="column-dot" :style="{ background: col.color }"></span>
            <span>{{ col.title }}</span>
            <span class="column-count">{{ tasksByColumn[col.id]?.length || 0 }}</span>
          </div>
          <button class="btn-icon" @click="openCreateModal(col.id)">
            <Plus :size="14" />
          </button>
        </div>

        <div class="column-cards">
          <div
            v-for="task in tasksByColumn[col.id]"
            :key="task.id"
            class="task-card"
            draggable="true"
            @dragstart="onDragStart(task)"
          >
            <div class="card-header">
              <span class="priority-badge" :class="getPriorityClass(task.priority)">
                {{ getPriorityLabel(task.priority) }}
              </span>
              <div class="card-actions">
                <button class="btn-icon-sm" @click="openEditModal(task)">
                  <Edit3 :size="12" />
                </button>
                <button class="btn-icon-sm danger" @click="deleteTask(task)">
                  <Trash2 :size="12" />
                </button>
              </div>
            </div>

            <div class="card-title">{{ task.title }}</div>
            <div v-if="task.description" class="card-desc">{{ task.description }}</div>

            <div v-if="task.tags.length" class="card-tags">
              <span v-for="tag in task.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>

            <div class="card-footer">
              <div v-if="task.assignee_name" class="card-meta">
                <User :size="12" />
                <span>{{ task.assignee_name }}</span>
              </div>
              <div v-if="task.due_date" class="card-meta" :class="{ overdue: new Date(task.due_date) < new Date() }">
                <Calendar :size="12" />
                <span>{{ task.due_date.slice(0, 10) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ editingTask ? t('taskManagement.editTitle') : t('taskManagement.createTitle') }}</h3>
          <button class="btn-icon" @click="closeModal">
            <span style="font-size: 20px;">&times;</span>
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
              <input
                v-model="tagInput"
                class="setting-input"
                :placeholder="t('taskManagement.tagsPlaceholder')"
                @keydown.enter.prevent="addTag"
              />
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
.task-board-page {
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
  width: 22px;
  height: 22px;
  border-radius: 4px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.task-card:hover .btn-icon-sm {
  opacity: 1;
}

.btn-icon-sm:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-icon-sm.danger:hover {
  color: var(--accent-red);
}

.board-container {
  display: flex;
  gap: 16px;
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 8px;
}

.board-column {
  flex: 1;
  min-width: 260px;
  max-width: 320px;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.column-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.column-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.column-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.column-count {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  padding: 2px 8px;
  border-radius: 9999px;
}

.column-cards {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 12px;
  cursor: grab;
  transition: box-shadow 0.15s ease, transform 0.1s ease;
}

.task-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  border-color: var(--border-hover);
}

.task-card:active {
  cursor: grabbing;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
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

.card-actions {
  display: flex;
  gap: 2px;
}

.card-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 6px;
  line-height: 1.4;
}

.card-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 10px;
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

.card-footer {
  display: flex;
  gap: 12px;
  align-items: center;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.card-meta.overdue {
  color: var(--accent-red);
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

.empty-state {
  padding: 48px;
  text-align: center;
  color: var(--text-muted);
}
</style>
