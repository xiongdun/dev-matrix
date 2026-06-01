<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <h3>{{ isEdit ? '编辑用户' : '新建用户' }}</h3>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>用户名 *</label>
          <input v-model="form.username" :disabled="isEdit" required />
        </div>

        <div v-if="!isEdit" class="form-group">
          <label>密码 *</label>
          <input v-model="form.password" type="password" required />
        </div>

        <div class="form-group">
          <label>昵称</label>
          <input v-model="form.nickname" />
        </div>

        <div class="form-group">
          <label>邮箱</label>
          <input v-model="form.email" type="email" />
        </div>

        <div class="form-group">
          <label>角色</label>
          <select v-model="form.role_ids" multiple>
            <option v-for="role in roles" :key="role.id" :value="role.id">
              {{ role.display_name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>数据权限</label>
          <select v-model="form.data_scope">
            <option value="self">仅自己</option>
            <option value="dept">本部门</option>
            <option value="all">全部</option>
          </select>
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

const props = defineProps<{ user: any }>()
const emit = defineEmits(['close', 'saved'])

const isEdit = computed(() => !!props.user)
const isSubmitting = ref(false)
const roles = ref<any[]>([])

const form = reactive({
  username: '',
  password: '',
  nickname: '',
  email: '',
  role_ids: [] as number[],
  data_scope: 'self',
})

onMounted(async () => {
  roles.value = await api.get('/roles')
  if (props.user) {
    form.username = props.user.username
    form.nickname = props.user.nickname || ''
    form.email = props.user.email || ''
    form.data_scope = props.user.data_scope
    form.role_ids = props.user.roles.map((r: any) => r.id)
  }
})

async function handleSubmit() {
  isSubmitting.value = true
  try {
    if (isEdit.value) {
      await api.put('/users/' + props.user.id, {
        nickname: form.nickname,
        email: form.email,
        data_scope: form.data_scope,
        role_ids: form.role_ids,
      })
    } else {
      await api.post('/users', {
        username: form.username,
        password: form.password,
        nickname: form.nickname,
        email: form.email,
        role_ids: form.role_ids,
        data_scope: form.data_scope,
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
  width: 500px;
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

.form-group select[multiple] {
  height: 120px;
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
