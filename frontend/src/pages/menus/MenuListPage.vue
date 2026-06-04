<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>菜单管理</h1>
        <p>管理系统菜单、权限标识和菜单层级结构</p>
      </div>
      <button class="btn-create" @click="showCreateModal">
        新建菜单
      </button>
    </div>

    <div v-if="loading" class="empty-state">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="empty-state" style="color: var(--accent-red)">
      {{ t('common.error') }}: {{ error }}
    </div>
    <div v-else class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>标题</th>
            <th>路径</th>
            <th>类型</th>
            <th>权限标识</th>
            <th>排序</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="menu in menus" :key="menu.id">
            <tr>
              <td class="menu-name">{{ menu.name }}</td>
              <td class="menu-title">{{ menu.title }}</td>
              <td class="menu-path">{{ menu.path || '—' }}</td>
              <td>
                <span class="type-badge">{{ typeLabel(menu.menu_type) }}</span>
              </td>
              <td class="menu-perm">{{ menu.permission || '—' }}</td>
              <td class="menu-sort">{{ menu.sort_order }}</td>
              <td>
                <span class="menu-status" :class="menu.status">{{ statusLabel(menu.status) }}</span>
              </td>
              <td class="menu-actions">
                <button class="btn-action" @click="editMenu(menu)">编辑</button>
                <button class="btn-action btn-delete" @click="deleteMenu(menu)">删除</button>
              </td>
            </tr>
            <tr v-for="child in menu.children" :key="child.id" class="child-row">
              <td class="menu-name" style="padding-left: 2rem">└ {{ child.name }}</td>
              <td class="menu-title">{{ child.title }}</td>
              <td class="menu-path">{{ child.path || '—' }}</td>
              <td>
                <span class="type-badge">{{ typeLabel(child.menu_type) }}</span>
              </td>
              <td class="menu-perm">{{ child.permission || '—' }}</td>
              <td class="menu-sort">{{ child.sort_order }}</td>
              <td>
                <span class="menu-status" :class="child.status">{{ statusLabel(child.status) }}</span>
              </td>
              <td class="menu-actions">
                <button class="btn-action" @click="editMenu(child)">编辑</button>
                <button class="btn-action btn-delete" @click="deleteMenu(child)">删除</button>
              </td>
            </tr>
          </template>
          <EmptyTableRow v-if="menus.length === 0" :colspan="8" message="暂无菜单数据" />
        </tbody>
      </table>
    </div>

    <MenuFormModal
      v-if="modalVisible"
      :menu="editingMenu"
      :parent-menus="parentMenus"
      @close="modalVisible = false"
      @saved="loadMenus"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../../api'
import EmptyTableRow from '../../components/EmptyTableRow.vue'
import MenuFormModal from './MenuFormModal.vue'

const { t } = useI18n()

const menus = ref<any[]>([])
const modalVisible = ref(false)
const editingMenu = ref<any>(null)
const loading = ref(true)
const error = ref('')

const parentMenus = computed(() => menus.value.filter((m: any) => m.menu_type === 'directory'))

async function loadMenus() {
  loading.value = true
  error.value = ''
  try {
    menus.value = await api.get('/menus/tree')
  } catch (e: any) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

function showCreateModal() {
  editingMenu.value = null
  modalVisible.value = true
}

function editMenu(menu: any) {
  editingMenu.value = menu
  modalVisible.value = true
}

async function deleteMenu(menu: any) {
  if (!confirm(`确认删除菜单「${menu.title}」？`)) return
  try {
    await api.delete('/menus/' + menu.id)
    loadMenus()
  } catch (e: any) {
    error.value = e.message || String(e)
  }
}

function typeLabel(type: string) {
  const map: Record<string, string> = { page: '页面', directory: '目录', button: '按钮' }
  return map[type] || type
}

function statusLabel(status: string) {
  const map: Record<string, string> = { active: '启用', disabled: '禁用' }
  return map[status] || status
}

onMounted(loadMenus)
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

.child-row td {
  background-color: rgba(0, 0, 0, 0.02);
}

.menu-name {
  font-weight: 600;
  font-size: 13px;
}

.menu-title {
  font-size: 13px;
}

.menu-path {
  color: var(--text-secondary);
  font-size: 13px;
  font-family: 'SF Mono', Monaco, monospace;
}

.type-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background-color: rgba(99, 102, 241, 0.15);
  color: #6366f1;
}

.menu-perm {
  color: var(--text-secondary);
  font-size: 13px;
  font-family: 'SF Mono', Monaco, monospace;
}

.menu-sort {
  font-size: 13px;
  color: var(--text-tertiary);
}

.menu-status {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.menu-status.active {
  background-color: rgba(34, 197, 94, 0.15);
  color: var(--accent-green);
}

.menu-status.disabled {
  background-color: rgba(239, 68, 68, 0.15);
  color: var(--accent-red);
}

.menu-actions {
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
