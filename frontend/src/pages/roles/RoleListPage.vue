<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>角色管理</h1>
        <p>管理系统角色、权限分配和数据范围</p>
      </div>
      <button class="btn-create" @click="showCreateModal">
        新建角色
      </button>
    </div>

    <div v-if="loading" class="empty-state">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="empty-state" style="color: var(--accent-red)">
      {{ t('common.error') }}: {{ error }}
    </div>
    <div v-else-if="roles.length === 0" class="empty-state">
      暂无角色数据
    </div>
    <div v-else class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>角色标识</th>
            <th>显示名称</th>
            <th>描述</th>
            <th>数据权限</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="role in roles" :key="role.id">
            <td class="role-name">{{ role.name }}</td>
            <td class="role-display">{{ role.display_name }}</td>
            <td class="role-desc">{{ role.description || '—' }}</td>
            <td>
              <span class="scope-badge">{{ scopeLabel(role.data_scope) }}</span>
            </td>
            <td>
              <span class="role-status" :class="role.status">{{ statusLabel(role.status) }}</span>
            </td>
            <td class="role-actions">
              <button class="btn-action" @click="editRole(role)">编辑</button>
              <button v-if="!role.is_system" class="btn-action btn-delete" @click="deleteRole(role)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <RoleFormModal
      v-if="modalVisible"
      :role="editingRole"
      @close="modalVisible = false"
      @saved="loadRoles"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../../api'
import RoleFormModal from './RoleFormModal.vue'

const { t } = useI18n()

const roles = ref<any[]>([])
const modalVisible = ref(false)
const editingRole = ref<any>(null)
const loading = ref(true)
const error = ref('')

async function loadRoles() {
  loading.value = true
  error.value = ''
  try {
    roles.value = await api.get('/roles')
  } catch (e: any) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

function showCreateModal() {
  editingRole.value = null
  modalVisible.value = true
}

function editRole(role: any) {
  editingRole.value = role
  modalVisible.value = true
}

async function deleteRole(role: any) {
  if (!confirm(`确认删除角色「${role.display_name}」？`)) return
  try {
    await api.delete('/roles/' + role.id)
    loadRoles()
  } catch (e: any) {
    error.value = e.message || String(e)
  }
}

function scopeLabel(scope: string) {
  const map: Record<string, string> = { all: '全部', dept: '本部门', self: '仅自己' }
  return map[scope] || scope
}

function statusLabel(status: string) {
  const map: Record<string, string> = { active: '启用', disabled: '禁用' }
  return map[status] || status
}

onMounted(loadRoles)
</script>

<style scoped>
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.dashboard-header h1 {
  margin: 0;
  font-size: 1.5rem;
  color: var(--text-primary);
}

.dashboard-header p {
  margin: 0.25rem 0 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

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
}

.data-table tr:last-child td {
  border-bottom: none;
}

.data-table tr:hover td {
  background-color: var(--bg-hover);
}

.role-name {
  font-weight: 600;
  font-size: 13px;
}

.role-display {
  font-weight: 500;
  font-size: 13px;
}

.role-desc {
  color: var(--text-secondary);
  font-size: 13px;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scope-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background-color: rgba(99, 102, 241, 0.15);
  color: #6366f1;
}

.role-status {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.role-status.active {
  background-color: rgba(34, 197, 94, 0.15);
  color: var(--accent-green);
}

.role-status.disabled {
  background-color: rgba(239, 68, 68, 0.15);
  color: var(--accent-red);
}

.role-actions {
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

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
  font-size: 14px;
}
</style>
