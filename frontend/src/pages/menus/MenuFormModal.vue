<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <h3>{{ isEdit ? '编辑菜单' : '新建菜单' }}</h3>

      <form @submit.prevent="handleSubmit">
        <div class="form-row">
          <div class="form-group">
            <label>名称 *</label>
            <input v-model="form.name" :disabled="isEdit" required />
          </div>
          <div class="form-group">
            <label>标题 *</label>
            <input v-model="form.title" required />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>路径</label>
            <input v-model="form.path" />
          </div>
          <div class="form-group">
            <label>图标</label>
            <input v-model="form.icon" placeholder="如: Settings" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>父菜单</label>
            <select v-model="form.parent_id">
              <option :value="null">无（顶级菜单）</option>
              <option v-for="menu in parentMenus" :key="menu.id" :value="menu.id">
                {{ menu.title }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>类型</label>
            <select v-model="form.menu_type">
              <option value="page">页面</option>
              <option value="directory">目录</option>
              <option value="button">按钮</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>权限标识</label>
            <input v-model="form.permission" placeholder="如: user:manage" />
          </div>
          <div class="form-group">
            <label>排序</label>
            <input v-model.number="form.sort_order" type="number" />
          </div>
        </div>

        <div class="form-group">
          <label>组件路径</label>
          <input v-model="form.component" placeholder="Vue 组件路径" />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>
              <input v-model="form.is_visible" type="checkbox" :true-value="1" :false-value="0" />
              显示在菜单
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

const props = defineProps<{ menu: any; parentMenus: any[] }>()
const emit = defineEmits(['close', 'saved'])

const isEdit = computed(() => !!props.menu)
const isSubmitting = ref(false)

const form = reactive({
  name: '',
  title: '',
  path: '',
  icon: '',
  parent_id: null as number | null,
  menu_type: 'page',
  permission: '',
  sort_order: 0,
  component: '',
  is_visible: 1,
})

onMounted(() => {
  if (props.menu) {
    form.name = props.menu.name
    form.title = props.menu.title
    form.path = props.menu.path || ''
    form.icon = props.menu.icon || ''
    form.parent_id = props.menu.parent_id
    form.menu_type = props.menu.menu_type
    form.permission = props.menu.permission || ''
    form.sort_order = props.menu.sort_order
    form.component = props.menu.component || ''
    form.is_visible = props.menu.is_visible
  }
})

async function handleSubmit() {
  isSubmitting.value = true
  try {
    const payload = {
      name: form.name,
      title: form.title,
      path: form.path || null,
      icon: form.icon || null,
      parent_id: form.parent_id,
      menu_type: form.menu_type,
      permission: form.permission || null,
      sort_order: form.sort_order,
      component: form.component || null,
      is_visible: form.is_visible,
    }
    if (isEdit.value) {
      await api.put('/menus/' + props.menu.id, payload)
    } else {
      await api.post('/menus', payload)
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
  width: 560px;
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
