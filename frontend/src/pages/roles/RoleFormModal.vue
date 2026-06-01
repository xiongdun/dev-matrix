<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content wide" @click.stop>
      <h3>{{ isEdit ? '编辑角色' : '新建角色' }}</h3>

      <form @submit.prevent="handleSubmit">
        <div class="form-row">
          <div class="form-group">
            <label>角色标识 *</label>
            <input v-model="form.name" :disabled="isEdit" required />
          </div>
          <div class="form-group">
            <label>显示名称 *</label>
            <input v-model="form.display_name" required />
          </div>
        </div>

        <div class="form-group">
          <label>描述</label>
          <input v-model="form.description" />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>数据权限</label>
            <select v-model="form.data_scope">
              <option value="self">仅自己</option>
              <option value="dept">本部门</option>
              <option value="all">全部</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>菜单权限</label>
          <div class="menu-tree">
            <div v-for="menu in menuTree" :key="menu.id" class="menu-item">
              <label class="menu-label">
                <input
                  type="checkbox"
                  :checked="isMenuSelected(menu.id)"
                  @change="toggleMenu(menu.id)"
                />
                <span>{{ menu.title }}</span>
              </label>
              <div v-if="menu.children?.length" class="menu-children">
                <label v-for="child in menu.children" :key="child.id" class="menu-label child">
                  <input
                    type="checkbox"
                    :checked="isMenuSelected(child.id)"
                    @change="toggleMenu(child.id)"
                  />
                  <span>{{ child.title }}</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>Agent 权限</label>
          <div class="agent-checkboxes">
            <label v-for="agent in agents" :key="agent.name" class="agent-label">
              <input
                type="checkbox"
                :value="agent.name"
                v-model="form.agent_names"
              />
              <span>{{ agent.display_name || agent.name }}</span>
            </label>
          </div>
        </div>

        <div class="modal-actions">
          <button type="button" class="btn-secondary" @click="$emit('close')">取消</button>
          <button type="submit" class="btn-primary" :disabled="isSubmitting">
            {{ isSubmitting ? '保存中...' : '保存' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { api } from '../../api'

const props = defineProps<{ role: any }>()
const emit = defineEmits(['close', 'saved'])

const isEdit = computed(() => !!props.role)
const isSubmitting = ref(false)
const menuTree = ref<any[]>([])
const agents = ref<any[]>([])

const form = reactive({
  name: '',
  display_name: '',
  description: '',
  data_scope: 'self',
  menu_ids: [] as number[],
  agent_names: [] as string[],
})

onMounted(async () => {
  menuTree.value = await api.get('/menus/tree')
  agents.value = await api.get('/registry/agents/detail')

  if (props.role) {
    form.name = props.role.name
    form.display_name = props.role.display_name
    form.description = props.role.description || ''
    form.data_scope = props.role.data_scope
    form.menu_ids = props.role.menus.map((m: any) => m.id)
    form.agent_names = (props.role.agents || []).filter((a: any) => typeof a === 'string' && a.length > 0)
  }
})

function isMenuSelected(menuId: number) {
  return form.menu_ids.includes(menuId)
}

function toggleMenu(menuId: number) {
  const idx = form.menu_ids.indexOf(menuId)
  if (idx > -1) {
    form.menu_ids.splice(idx, 1)
  } else {
    form.menu_ids.push(menuId)
  }
}

async function handleSubmit() {
  isSubmitting.value = true
  try {
    if (isEdit.value) {
      await api.put('/roles/' + props.role.id, {
        display_name: form.display_name,
        description: form.description,
        data_scope: form.data_scope,
        menu_ids: form.menu_ids,
        agent_names: form.agent_names,
      })
    } else {
      await api.post('/roles', {
        name: form.name,
        display_name: form.display_name,
        description: form.description,
        data_scope: form.data_scope,
        menu_ids: form.menu_ids,
        agent_names: form.agent_names,
      })
    }
    emit('saved')
    emit('close')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  padding: 24px;
  background: var(--surface-color);
  border-radius: 12px;
}

.modal-content h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-row .form-group {
  flex: 1;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
  color: var(--text-primary);
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  box-sizing: border-box;
}

.menu-tree {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 12px;
}

.menu-item {
  margin-bottom: 8px;
}

.menu-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.menu-label.child {
  padding-left: 24px;
}

.menu-children {
  margin-top: 4px;
}

.agent-checkboxes {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 12px;
}

.agent-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.btn-secondary {
  padding: 8px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  cursor: pointer;
}

.btn-primary {
  padding: 8px 16px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
