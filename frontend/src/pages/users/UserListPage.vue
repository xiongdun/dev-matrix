<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>用户管理</h1>
        <p>管理系统用户、角色分配和权限控制</p>
      </div>
      <button class="btn-create" @click="showCreateModal">
        新建用户
      </button>
    </div>

    <div class="filters-bar">
      <input v-model="keyword" placeholder="搜索用户名或昵称" @input="loadUsers" class="filter-input" />
      <select v-model="statusFilter" @change="loadUsers" class="filter-select">
        <option value="">全部状态</option>
        <option value="active">启用</option>
        <option value="disabled">禁用</option>
      </select>
    </div>

    <div v-if="loading" class="empty-state">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="empty-state" style="color: var(--accent-red)">
      {{ t('common.error') }}: {{ error }}
    </div>
    <div v-else class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>用户名</th>
            <th>昵称</th>
            <th>角色</th>
            <th>状态</th>
            <th>最后登录</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td class="user-name">{{ user.username }}</td>
            <td class="user-nickname">{{ user.nickname || '—' }}</td>
            <td>
              <span v-for="role in user.roles" :key="role.id" class="role-badge">
                {{ role.display_name }}
              </span>
            </td>
            <td>
              <span class="user-status" :class="user.status">{{ statusLabel(user.status) }}</span>
            </td>
            <td class="user-time">{{ user.last_login_at ? formatDate(user.last_login_at) : '—' }}</td>
            <td class="user-actions">
              <button class="btn-action btn-view" @click="router.push(`/users/${user.id}`)">查看</button>
              <button class="btn-action" @click="editUser(user)">编辑</button>
              <button class="btn-action" :class="user.status === 'active' ? 'btn-archive' : 'btn-enable'" @click="toggleStatus(user)">
                {{ user.status === 'active' ? '禁用' : '启用' }}
              </button>
              <button class="btn-action btn-delete" @click="deleteUser(user)">删除</button>
            </td>
          </tr>
          <EmptyTableRow v-if="users.length === 0" :colspan="6" message="暂无用户数据" />
        </tbody>
      </table>
    </div>

    <UserFormModal
      v-if="modalVisible"
      :user="editingUser"
      @close="modalVisible = false"
      @saved="loadUsers"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { api } from '../../api'
import UserFormModal from './UserFormModal.vue'
import EmptyTableRow from '../../components/EmptyTableRow.vue'

const { t } = useI18n()
const router = useRouter()

const users = ref<any[]>([])
const keyword = ref('')
const statusFilter = ref('')
const modalVisible = ref(false)
const editingUser = ref<any>(null)
const loading = ref(true)
const error = ref('')

async function loadUsers() {
  loading.value = true
  error.value = ''
  try {
    const params: any = {}
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value
    const res = await api.get('/users', { params })
    users.value = res
  } catch (e: any) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

function showCreateModal() {
  editingUser.value = null
  modalVisible.value = true
}

function editUser(user: any) {
  editingUser.value = user
  modalVisible.value = true
}

async function toggleStatus(user: any) {
  const newStatus = user.status === 'active' ? 'disabled' : 'active'
  try {
    await api.put('/users/' + user.id + '/status?status=' + newStatus)
    loadUsers()
  } catch (e: any) {
    error.value = e.message || String(e)
  }
}

async function deleteUser(user: any) {
  if (!confirm(`确认删除用户「${user.username}」？`)) return
  try {
    await api.delete('/users/' + user.id)
    loadUsers()
  } catch (e: any) {
    error.value = e.message || String(e)
  }
}

function statusLabel(status: string) {
  const map: Record<string, string> = { active: '启用', disabled: '禁用' }
  return map[status] || status
}

function formatDate(date: string) {
  const d = new Date(date)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

onMounted(loadUsers)
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

.filters-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.filter-input,
.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
}

.filter-input {
  width: 240px;
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

.user-name {
  font-weight: 600;
  font-size: 13px;
}

.user-nickname {
  color: var(--text-secondary);
  font-size: 13px;
}

.role-badge {
  display: inline-block;
  margin-right: 6px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 9999px;
  background-color: rgba(99, 102, 241, 0.15);
  color: #6366f1;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.user-status {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.user-status.active {
  background-color: rgba(34, 197, 94, 0.15);
  color: var(--accent-green);
}

.user-status.disabled {
  background-color: rgba(239, 68, 68, 0.15);
  color: var(--accent-red);
}

.user-time {
  font-size: 13px;
  color: var(--text-secondary);
}

.user-actions {
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

.btn-view {
  border-color: #6366f1;
  color: #6366f1;
}

.btn-view:hover {
  background: rgba(99, 102, 241, 0.1);
}

.btn-delete:hover {
  border-color: var(--accent-red);
  color: var(--accent-red);
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

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
  font-size: 14px;
}
</style>
