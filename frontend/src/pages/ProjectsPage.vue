<template>
  <div class="projects-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ t('projects.title') }}</h1>
        <p class="page-subtitle">{{ t('projects.subtitle') }}</p>
      </div>
      <button class="btn btn-primary" @click="showCreateModal = true">
        <Plus :size="16" />
        {{ t('projects.create') }}
      </button>
    </div>

    <div class="toolbar">
      <div class="search-box">
        <Search :size="16" class="search-icon" />
        <input
          v-model="keyword"
          type="text"
          :placeholder="t('projects.searchPlaceholder')"
          @input="handleSearch"
        />
      </div>
      <select v-model="filterStatus" class="filter-select" @change="loadProjects">
        <option value="">{{ t('projects.allStatus') }}</option>
        <option value="planning">{{ t('projects.statusPlanning') }}</option>
        <option value="in_progress">{{ t('projects.statusInProgress') }}</option>
        <option value="completed">{{ t('projects.statusCompleted') }}</option>
        <option value="on_hold">{{ t('projects.statusOnHold') }}</option>
        <option value="cancelled">{{ t('projects.statusCancelled') }}</option>
      </select>
      <select v-model="filterPriority" class="filter-select" @change="loadProjects">
        <option value="">{{ t('projects.allPriority') }}</option>
        <option value="high">{{ t('projects.priorityHigh') }}</option>
        <option value="medium">{{ t('projects.priorityMedium') }}</option>
        <option value="low">{{ t('projects.priorityLow') }}</option>
      </select>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="projects.length === 0" class="empty-state">
      <FolderOpen :size="48" class="empty-icon" />
      <p>{{ t('projects.empty') }}</p>
    </div>
    <div v-else class="project-grid">
      <div
        v-for="project in projects"
        :key="project.id"
        class="project-card"
        @click="goToDetail(project.id)"
      >
        <div class="card-header">
          <h3 class="project-name">{{ project.name }}</h3>
          <span class="priority-badge" :class="project.priority">
            {{ t(`projects.priority${project.priority.charAt(0).toUpperCase() + project.priority.slice(1)}`) }}
          </span>
        </div>
        <p class="project-desc">{{ project.description || t('projects.noDescription') }}</p>
        <div class="project-meta">
          <span class="meta-item">
            <User :size="14" />
            {{ project.owner || t('projects.noOwner') }}
          </span>
          <span class="meta-item">
            <Calendar :size="14" />
            {{ formatDate(project.created_at) }}
          </span>
        </div>
        <div class="project-progress">
          <div class="progress-bar-bg">
            <div
              class="progress-bar-fill"
              :style="{ width: `${project.progress}%` }"
              :class="project.status"
            />
          </div>
          <span class="progress-text">{{ project.progress }}%</span>
        </div>
        <div class="project-footer">
          <span class="status-badge" :class="project.status">
            {{ t(`projects.status${project.status.charAt(0).toUpperCase() + project.status.slice(1)}`) }}
          </span>
          <div class="actions" @click.stop>
            <button class="icon-btn" @click="editProject(project)">
              <Pencil :size="14" />
            </button>
            <button class="icon-btn danger" @click="confirmDelete(project)">
              <Trash2 :size="14" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="total > pageSize" class="pagination">
      <button
        class="page-btn"
        :disabled="page === 1"
        @click="page--; loadProjects()"
      >
        <ChevronLeft :size="16" />
      </button>
      <span class="page-info">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button
        class="page-btn"
        :disabled="page >= Math.ceil(total / pageSize)"
        @click="page++; loadProjects()"
      >
        <ChevronRight :size="16" />
      </button>
    </div>

    <!-- 创建/编辑弹窗 -->
    <Teleport to="body">
      <div v-if="showCreateModal || showEditModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal">
          <div class="modal-header">
            <h3>{{ editingProject ? t('projects.editTitle') : t('projects.createTitle') }}</h3>
            <button class="icon-btn" @click="closeModal">
              <X :size="18" />
            </button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>{{ t('projects.name') }} *</label>
              <input v-model="form.name" type="text" :placeholder="t('projects.namePlaceholder')" />
            </div>
            <div class="form-group">
              <label>{{ t('projects.description') }}</label>
              <textarea v-model="form.description" rows="3" :placeholder="t('projects.descriptionPlaceholder')" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>{{ t('projects.owner') }}</label>
                <input v-model="form.owner" type="text" :placeholder="t('projects.ownerPlaceholder')" />
              </div>
              <div class="form-group">
                <label>{{ t('projects.priority') }}</label>
                <select v-model="form.priority">
                  <option value="high">{{ t('projects.priorityHigh') }}</option>
                  <option value="medium">{{ t('projects.priorityMedium') }}</option>
                  <option value="low">{{ t('projects.priorityLow') }}</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>{{ t('projects.status') }}</label>
                <select v-model="form.status">
                  <option value="planning">{{ t('projects.statusPlanning') }}</option>
                  <option value="in_progress">{{ t('projects.statusInProgress') }}</option>
                  <option value="completed">{{ t('projects.statusCompleted') }}</option>
                  <option value="on_hold">{{ t('projects.statusOnHold') }}</option>
                  <option value="cancelled">{{ t('projects.statusCancelled') }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>{{ t('projects.progress') }}</label>
                <input v-model.number="form.progress" type="number" min="0" max="100" />
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="closeModal">{{ t('common.cancel') }}</button>
            <button class="btn btn-primary" :disabled="!form.name" @click="saveProject">
              {{ t('common.save') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 删除确认弹窗 -->
    <Teleport to="body">
      <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
        <div class="modal modal-sm">
          <div class="modal-header">
            <h3>{{ t('projects.deleteTitle') }}</h3>
          </div>
          <div class="modal-body">
            <p>{{ t('projects.confirmDelete', { name: deletingProject?.name }) }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showDeleteModal = false">{{ t('common.cancel') }}</button>
            <button class="btn btn-danger" @click="doDelete">{{ t('common.delete') }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Plus,
  Search,
  FolderOpen,
  User,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Pencil,
  Trash2,
  X,
} from 'lucide-vue-next'
import { api } from '../api'

const { t } = useI18n()
const router = useRouter()

const projects = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)
const keyword = ref('')
const filterStatus = ref('')
const filterPriority = ref('')

const showCreateModal = ref(false)
const showEditModal = ref(false)
const showDeleteModal = ref(false)
const editingProject = ref<any>(null)
const deletingProject = ref<any>(null)

const form = reactive({
  name: '',
  description: '',
  owner: '',
  priority: 'medium',
  status: 'planning',
  progress: 0,
})

let searchTimer: ReturnType<typeof setTimeout> | null = null

function handleSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadProjects()
  }, 300)
}

async function loadProjects() {
  loading.value = true
  try {
    const res = await api.getProjects({
      page: page.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined,
      priority: filterPriority.value || undefined,
      keyword: keyword.value || undefined,
    })
    projects.value = res.items
    total.value = res.total
  } catch (err) {
    console.error('Failed to load projects:', err)
  } finally {
    loading.value = false
  }
}

function goToDetail(id: number) {
  router.push(`/projects/${id}`)
}

function editProject(project: any) {
  editingProject.value = project
  form.name = project.name
  form.description = project.description || ''
  form.owner = project.owner || ''
  form.priority = project.priority
  form.status = project.status
  form.progress = project.progress
  showEditModal.value = true
}

function confirmDelete(project: any) {
  deletingProject.value = project
  showDeleteModal.value = true
}

async function doDelete() {
  if (!deletingProject.value) return
  try {
    await api.deleteProject(deletingProject.value.id)
    showDeleteModal.value = false
    deletingProject.value = null
    loadProjects()
  } catch (err) {
    console.error('Failed to delete project:', err)
  }
}

async function saveProject() {
  try {
    const data = { ...form }
    if (editingProject.value) {
      await api.updateProject(editingProject.value.id, data)
    } else {
      await api.createProject(data)
    }
    closeModal()
    loadProjects()
  } catch (err) {
    console.error('Failed to save project:', err)
  }
}

function closeModal() {
  showCreateModal.value = false
  showEditModal.value = false
  editingProject.value = null
  form.name = ''
  form.description = ''
  form.owner = ''
  form.priority = 'medium'
  form.status = 'planning'
  form.progress = 0
}

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(loadProjects)
</script>

<style scoped>
.projects-page {
  padding: 24px;
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 4px;
  color: var(--text-primary);
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 200px;
  max-width: 360px;
}

.search-box input {
  width: 100%;
  padding: 8px 12px 8px 36px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.project-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
}

.project-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.project-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
  flex: 1;
  word-break: break-all;
}

.priority-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
  margin-left: 8px;
  flex-shrink: 0;
}

.priority-badge.high {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

.priority-badge.medium {
  background: rgba(245, 158, 11, 0.12);
  color: #f59e0b;
}

.priority-badge.low {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

.project-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 12px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.project-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.project-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.progress-bar-bg {
  flex: 1;
  height: 6px;
  background: var(--border-color);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s;
}

.progress-bar-fill.planning {
  background: #9ca3af;
}

.progress-bar-fill.in_progress {
  background: #3b82f6;
}

.progress-bar-fill.completed {
  background: #10b981;
}

.progress-bar-fill.on_hold {
  background: #f59e0b;
}

.progress-bar-fill.cancelled {
  background: #ef4444;
}

.progress-text {
  font-size: 12px;
  color: var(--text-secondary);
  min-width: 36px;
  text-align: right;
}

.project-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 12px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.actions {
  display: flex;
  gap: 4px;
}

.icon-btn {
  padding: 6px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.icon-btn.danger:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.loading,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.empty-icon {
  margin-bottom: 16px;
  opacity: 0.5;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 24px;
}

.page-btn {
  padding: 6px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: var(--text-secondary);
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
  background: var(--bg-primary);
  border-radius: 12px;
  width: 100%;
  max-width: 520px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal-sm {
  max-width: 400px;
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
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
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
  transition: opacity 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary-color);
  color: #fff;
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-danger {
  background: #ef4444;
  color: #fff;
}
</style>
