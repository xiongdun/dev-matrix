<template>
  <div class="project-detail-page">
    <div class="detail-header">
      <button class="back-btn" @click="router.back()">
        <ArrowLeft :size="18" />
        {{ t('common.back') }}
      </button>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="!project" class="empty-state">
      <p>{{ t('projects.notFound') }}</p>
    </div>
    <div v-else class="detail-content">
      <div class="detail-main">
        <div class="detail-card">
          <div class="detail-title-row">
            <h1 class="detail-title">{{ project.name }}</h1>
            <div class="detail-badges">
              <span class="priority-badge" :class="project.priority">
                {{ t(`projects.priority${project.priority.charAt(0).toUpperCase() + project.priority.slice(1)}`) }}
              </span>
              <span class="status-badge" :class="project.status">
                {{ t(`projects.status${project.status.charAt(0).toUpperCase() + project.status.slice(1)}`) }}
              </span>
            </div>
          </div>
          <p class="detail-description">{{ project.description || t('projects.noDescription') }}</p>

          <div class="detail-meta-grid">
            <div class="meta-item">
              <User :size="16" />
              <div>
                <label>{{ t('projects.owner') }}</label>
                <span>{{ project.owner || t('projects.noOwner') }}</span>
              </div>
            </div>
            <div class="meta-item">
              <Calendar :size="16" />
              <div>
                <label>{{ t('projects.startDate') }}</label>
                <span>{{ formatDate(project.start_date) }}</span>
              </div>
            </div>
            <div class="meta-item">
              <CalendarCheck :size="16" />
              <div>
                <label>{{ t('projects.endDate') }}</label>
                <span>{{ formatDate(project.end_date) }}</span>
              </div>
            </div>
            <div class="meta-item">
              <Clock :size="16" />
              <div>
                <label>{{ t('projects.createdAt') }}</label>
                <span>{{ formatDate(project.created_at) }}</span>
              </div>
            </div>
          </div>

          <div class="detail-progress">
            <div class="progress-header">
              <span>{{ t('projects.progress') }}</span>
              <span class="progress-value">{{ project.progress }}%</span>
            </div>
            <div class="progress-bar-bg">
              <div
                class="progress-bar-fill"
                :style="{ width: `${project.progress}%` }"
                :class="project.status"
              />
            </div>
          </div>
        </div>

        <div class="detail-card">
          <h3>{{ t('projects.workflowInstances') }}</h3>
          <div v-if="instances.length === 0" class="empty-sub">
            <p>{{ t('projects.noInstances') }}</p>
          </div>
          <div v-else class="instance-list">
            <div
              v-for="inst in instances"
              :key="inst.id"
              class="instance-item"
            >
              <div class="instance-info">
                <span class="instance-id">{{ inst.instance_id }}</span>
                <span class="instance-state">{{ inst.current_state }}</span>
              </div>
              <span class="instance-status" :class="inst.status">{{ inst.status }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="detail-sidebar">
        <div class="detail-card">
          <h3>{{ t('projects.actions') }}</h3>
          <div class="action-buttons">
            <button class="btn btn-primary w-full" @click="editProject">
              <Pencil :size="14" />
              {{ t('common.edit') }}
            </button>
            <button class="btn btn-secondary w-full" @click="showStartWorkflow = true">
              <Play :size="14" />
              {{ t('projects.startWorkflow') }}
            </button>
            <button class="btn btn-danger w-full" @click="confirmDelete">
              <Trash2 :size="14" />
              {{ t('common.delete') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 启动工作流弹窗 -->
    <Teleport to="body">
      <div v-if="showStartWorkflow" class="modal-overlay" @click.self="showStartWorkflow = false">
        <div class="modal modal-sm">
          <div class="modal-header">
            <h3>{{ t('projects.startWorkflow') }}</h3>
            <button class="icon-btn" @click="showStartWorkflow = false">
              <X :size="18" />
            </button>
          </div>
          <div class="modal-body">
            <p>{{ t('projects.selectWorkflow') }}</p>
            <div v-if="workflows.length === 0" class="empty-sub">
              <p>{{ t('projects.noWorkflows') }}</p>
            </div>
            <div v-else class="workflow-select-list">
              <div
                v-for="wf in workflows"
                :key="wf.id"
                class="workflow-option"
                :class="{ selected: selectedWorkflow === wf.id }"
                @click="selectedWorkflow = wf.id"
              >
                <span class="wf-name">{{ wf.name }}</span>
                <span class="wf-desc">{{ wf.description }}</span>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showStartWorkflow = false">{{ t('common.cancel') }}</button>
            <button class="btn btn-primary" :disabled="!selectedWorkflow" @click="startWorkflow">{{ t('common.confirm') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 编辑项目弹窗 -->
    <Teleport to="body">
      <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
        <div class="modal">
          <div class="modal-header">
            <h3>{{ t('projects.editTitle') }}</h3>
            <button class="icon-btn" @click="showEditModal = false">
              <X :size="18" />
            </button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>{{ t('projects.name') }} *</label>
              <input v-model="editForm.name" type="text" :placeholder="t('projects.namePlaceholder')" />
            </div>
            <div class="form-group">
              <label>{{ t('projects.description') }}</label>
              <textarea v-model="editForm.description" rows="3" :placeholder="t('projects.descriptionPlaceholder')" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>{{ t('projects.owner') }}</label>
                <input v-model="editForm.owner" type="text" :placeholder="t('projects.ownerPlaceholder')" />
              </div>
              <div class="form-group">
                <label>{{ t('projects.priority') }}</label>
                <select v-model="editForm.priority">
                  <option value="high">{{ t('projects.priorityHigh') }}</option>
                  <option value="medium">{{ t('projects.priorityMedium') }}</option>
                  <option value="low">{{ t('projects.priorityLow') }}</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>{{ t('projects.status') }}</label>
                <select v-model="editForm.status">
                  <option value="planning">{{ t('projects.statusPlanning') }}</option>
                  <option value="in_progress">{{ t('projects.statusInProgress') }}</option>
                  <option value="completed">{{ t('projects.statusCompleted') }}</option>
                  <option value="on_hold">{{ t('projects.statusOnHold') }}</option>
                  <option value="cancelled">{{ t('projects.statusCancelled') }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>{{ t('projects.progress') }}</label>
                <input v-model.number="editForm.progress" type="number" min="0" max="100" />
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showEditModal = false">{{ t('common.cancel') }}</button>
            <button class="btn btn-primary" :disabled="!editForm.name" @click="doEdit">{{ t('common.save') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 删除确认 -->
    <Teleport to="body">
      <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
        <div class="modal modal-sm">
          <div class="modal-header">
            <h3>{{ t('projects.deleteTitle') }}</h3>
          </div>
          <div class="modal-body">
            <p>{{ t('projects.confirmDelete', { name: project?.name }) }}</p>
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
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  ArrowLeft,
  User,
  Calendar,
  CalendarCheck,
  Clock,
  Pencil,
  Trash2,
  Play,
  X,
} from 'lucide-vue-next'
import { api } from '../api'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()

const project = ref<any>(null)
const instances = ref<any[]>([])
const workflows = ref<any[]>([])
const loading = ref(false)
const showDeleteModal = ref(false)
const showStartWorkflow = ref(false)
const showEditModal = ref(false)
const selectedWorkflow = ref<number | null>(null)

const editForm = ref({
  name: '',
  description: '',
  owner: '',
  priority: 'medium',
  status: 'planning',
  progress: 0,
})

async function loadProject() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    project.value = await api.getProject(id)
    // 加载关联的工作流实例
    try {
      const instRes = await api.getWorkflowInstances()
      instances.value = instRes.instances.filter((i: any) => i.project_id === String(id))
    } catch {
      instances.value = []
    }
  } catch (err) {
    console.error('Failed to load project:', err)
  } finally {
    loading.value = false
  }
}

async function loadWorkflows() {
  try {
    const res = await api.getWorkflows()
    workflows.value = res.workflows
  } catch {
    workflows.value = []
  }
}

function editProject() {
  if (!project.value) return
  editForm.value = {
    name: project.value.name,
    description: project.value.description || '',
    owner: project.value.owner || '',
    priority: project.value.priority,
    status: project.value.status,
    progress: project.value.progress,
  }
  showEditModal.value = true
}

async function doEdit() {
  if (!project.value) return
  try {
    await api.updateProject(project.value.id, { ...editForm.value })
    showEditModal.value = false
    loadProject()
  } catch (err) {
    console.error('Failed to update project:', err)
  }
}

function confirmDelete() {
  showDeleteModal.value = true
}

async function doDelete() {
  if (!project.value) return
  try {
    await api.deleteProject(project.value.id)
    showDeleteModal.value = false
    router.push('/projects')
  } catch (err) {
    console.error('Failed to delete project:', err)
  }
}

async function startWorkflow() {
  if (!selectedWorkflow.value || !project.value) return
  try {
    await api.instantiateTemplate(selectedWorkflow.value, String(project.value.id))
    showStartWorkflow.value = false
    selectedWorkflow.value = null
    // 刷新实例列表
    const instRes = await api.getWorkflowInstances()
    instances.value = instRes.instances.filter((i: any) => i.project_id === String(project.value.id))
  } catch (err) {
    console.error('Failed to start workflow:', err)
  }
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(() => {
  loadProject()
  loadWorkflows()
})
</script>

<style scoped>
.project-detail-page {
  max-width: 1200px;
  margin: 0 auto;
}

.detail-header {
  margin-bottom: 20px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.back-btn:hover {
  background: var(--bg-tertiary);
}

.detail-content {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 20px;
}

.detail-main {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
}

.detail-card h3 {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.detail-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-title {
  font-size: 22px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.detail-badges {
  display: flex;
  gap: 8px;
}

.priority-badge {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 500;
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

.status-badge {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 12px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.detail-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 20px;
  line-height: 1.6;
}

.detail-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
}

.meta-item > div {
  display: flex;
  flex-direction: column;
}

.meta-item label {
  font-size: 11px;
  color: var(--text-secondary);
  opacity: 0.7;
}

.meta-item span {
  font-size: 13px;
  color: var(--text-primary);
}

.detail-progress {
  margin-top: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 6px;
  color: var(--text-primary);
}

.progress-value {
  font-weight: 600;
}

.progress-bar-bg {
  height: 8px;
  background: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}

.progress-bar-fill.planning { background: #9ca3af; }
.progress-bar-fill.in_progress { background: #3b82f6; }
.progress-bar-fill.completed { background: #10b981; }
.progress-bar-fill.on_hold { background: #f59e0b; }
.progress-bar-fill.cancelled { background: #ef4444; }

.instance-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.instance-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.instance-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.instance-id {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.instance-state {
  font-size: 11px;
  color: var(--text-secondary);
}

.instance-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.w-full {
  width: 100%;
  justify-content: center;
}

.empty-sub {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary);
  font-size: 13px;
}

.workflow-select-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
}

.workflow-option {
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.workflow-option:hover {
  border-color: var(--primary-color);
}

.workflow-option.selected {
  border-color: var(--primary-color);
  background: rgba(59, 130, 246, 0.08);
}

.wf-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.wf-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

.loading,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

/* Modal reuse styles from ProjectsPage */
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

@media (max-width: 768px) {
  .detail-content {
    grid-template-columns: 1fr;
  }
  .detail-meta-grid {
    grid-template-columns: 1fr;
  }
}
</style>
