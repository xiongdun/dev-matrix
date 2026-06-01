<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="login-title">DevMatrix</h1>
      <p class="login-subtitle">多角色协作软件开发 Agent 操作系统</p>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>用户名</label>
          <input
            v-model="form.username"
            type="text"
            placeholder="请输入用户名"
            required
          />
        </div>

        <div class="form-group">
          <label>密码</label>
          <input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            required
          />
        </div>

        <div v-if="error" class="error-message">{{ error }}</div>

        <button type="submit" class="login-btn" :disabled="isLoading">
          {{ isLoading ? '登录中...' : '登录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { authApi } from '../api/auth'
import { api } from '../api'

const router = useRouter()
const userStore = useUserStore()

const form = reactive({
  username: '',
  password: '',
})

const isLoading = ref(false)
const error = ref('')

async function handleLogin() {
  isLoading.value = true
  error.value = ''

  try {
    const res = await authApi.login(form)
    userStore.setToken(res.token)

    // 获取用户信息
    const userInfo = await authApi.getMe()
    userStore.setUserInfo(userInfo)

    // 获取菜单
    const menus = await api.get('/menus/my')
    userStore.setMenus(menus)

    router.push('/')
  } catch (e: any) {
    error.value = e.message || '登录失败'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: var(--surface-color, #ffffff);
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  text-align: center;
  margin: 0 0 8px 0;
  color: var(--text-primary, #111827);
}

.login-subtitle {
  font-size: 14px;
  text-align: center;
  color: var(--text-secondary, #6b7280);
  margin: 0 0 32px 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
  color: var(--text-primary, #111827);
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-secondary, #f9fafb);
  color: var(--text-primary, #111827);
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: var(--primary-color, #3b82f6);
}

.error-message {
  color: #ef4444;
  font-size: 14px;
  margin-bottom: 16px;
  text-align: center;
}

.login-btn {
  width: 100%;
  padding: 12px;
  background: var(--primary-color, #3b82f6);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.login-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
