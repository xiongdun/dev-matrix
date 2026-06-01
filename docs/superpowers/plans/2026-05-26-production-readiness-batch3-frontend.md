# 批次 3：前端鲁棒性实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 提升前端安全性、错误处理能力和用户体验，包括路由权限检查、API 错误处理增强、状态持久化。

**Architecture:** 路由守卫中集成权限检查；API 层统一错误处理和友好提示；Pinia store 添加持久化插件自动保存用户状态。

**Tech Stack:** Vue 3, TypeScript, Vue Router, Pinia, pinia-plugin-persistedstate

---

## 文件变更总览

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/router.ts` | 修改 | 路由守卫添加权限检查 |
| `frontend/src/stores/user.ts` | 修改 | 添加状态持久化和 Token 刷新 |
| `frontend/src/api/index.ts` | 修改 | 增强错误处理，添加友好提示 |
| `frontend/src/composables/useErrorHandler.ts` | 创建 | 统一错误处理组合式函数 |
| `frontend/src/components/ErrorToast.vue` | 创建 | 错误提示组件 |
| `frontend/src/main.ts` | 修改 | 注册 Pinia 持久化插件 |
| `frontend/package.json` | 修改 | 添加 pinia-plugin-persistedstate |
| `frontend/src/pages/ForbiddenPage.vue` | 创建 | 403 无权限页面 |

---

## Task 1: 路由守卫权限检查

**Files:**
- Modify: `frontend/src/router.ts`
- Create: `frontend/src/pages/ForbiddenPage.vue`

**背景:** 当前路由守卫只检查登录状态，不检查用户是否有权限访问特定页面。

- [ ] **Step 1: 修改路由守卫添加权限检查**

修改 `frontend/src/router.ts`：

```typescript
import { useUserStore } from './stores/user'

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.public) {
    next()
    return
  }

  if (!token) {
    next('/login')
    return
  }

  // 权限检查
  const requiredPermission = to.meta.permission as string | undefined
  if (requiredPermission) {
    const userStore = useUserStore()
    // 确保用户信息已加载
    if (!userStore.userInfo) {
      // 异步获取用户信息后再检查权限
      import('./api/auth').then(({ authApi }) => {
        authApi.getMe()
          .then((userInfo) => {
            userStore.setUserInfo(userInfo)
            if (userStore.hasPermission.value(requiredPermission)) {
              next()
            } else {
              next('/forbidden')
            }
          })
          .catch(() => {
            userStore.clearToken()
            next('/login')
          })
      })
      return
    }

    if (!userStore.hasPermission.value(requiredPermission)) {
      next('/forbidden')
      return
    }
  }

  next()
})
```

- [ ] **Step 2: 创建 403 页面**

创建 `frontend/src/pages/ForbiddenPage.vue`：

```vue
<template>
  <div class="forbidden-page">
    <div class="forbidden-content">
      <ShieldAlert :size="64" class="forbidden-icon" />
      <h1>{{ t('forbidden.title') }}</h1>
      <p>{{ t('forbidden.message') }}</p>
      <button class="btn-primary" @click="goHome">
        {{ t('forbidden.backHome') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ShieldAlert } from 'lucide-vue-next'

const router = useRouter()
const { t } = useI18n()

function goHome() {
  router.push('/')
}
</script>

<style scoped>
.forbidden-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: var(--bg-primary);
}

.forbidden-content {
  text-align: center;
  padding: 48px;
}

.forbidden-icon {
  color: var(--accent-orange);
  margin-bottom: 24px;
}

h1 {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

p {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.btn-primary {
  padding: 10px 24px;
  border-radius: var(--radius-md);
  background-color: var(--accent-blue);
  color: white;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.btn-primary:hover {
  opacity: 0.9;
}
</style>
```

- [ ] **Step 3: 添加路由配置**

在 `frontend/src/router.ts` 的 `routes` 数组中添加：

```typescript
{
  path: '/forbidden',
  name: 'forbidden',
  component: () => import('./pages/ForbiddenPage.vue'),
  meta: { public: true, fullscreen: true },
},
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/router.ts frontend/src/pages/ForbiddenPage.vue
git commit -m "security: add route permission guard and 403 page"
```

---

## Task 2: API 错误处理增强

**Files:**
- Create: `frontend/src/composables/useErrorHandler.ts`
- Create: `frontend/src/components/ErrorToast.vue`
- Modify: `frontend/src/api/index.ts`

**背景:** 当前 API 错误直接抛出 Error，用户体验差，且 500 错误可能暴露内部信息。

- [ ] **Step 1: 创建统一错误处理组合式函数**

创建 `frontend/src/composables/useErrorHandler.ts`：

```typescript
import { ref } from 'vue'

export interface ErrorToast {
  id: number
  message: string
  type: 'error' | 'warning' | 'info'
  duration: number
}

const toasts = ref<ErrorToast[]>([])
let toastId = 0

export function useErrorHandler() {
  function showError(message: string, duration = 5000) {
    const id = ++toastId
    toasts.value.push({ id, message, type: 'error', duration })
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  function showWarning(message: string, duration = 4000) {
    const id = ++toastId
    toasts.value.push({ id, message, type: 'warning', duration })
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  function showInfo(message: string, duration = 3000) {
    const id = ++toastId
    toasts.value.push({ id, message, type: 'info', duration })
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  function removeToast(id: number) {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  function handleApiError(error: Error): string {
    const msg = error.message || String(error)

    // 网络错误
    if (msg.includes('timeout') || msg.includes('AbortError')) {
      return '请求超时，请检查网络连接后重试'
    }
    if (msg.includes('NetworkError') || msg.includes('fetch')) {
      return '网络连接失败，请检查网络后重试'
    }

    // HTTP 状态码错误
    if (msg.includes('API Error 401')) {
      return '登录已过期，请重新登录'
    }
    if (msg.includes('API Error 403')) {
      return '没有权限执行此操作'
    }
    if (msg.includes('API Error 404')) {
      return '请求的资源不存在'
    }
    if (msg.includes('API Error 429')) {
      return '请求过于频繁，请稍后再试'
    }
    if (msg.includes('API Error 5')) {
      return '服务器内部错误，请稍后再试'
    }

    // 默认错误
    return '操作失败，请稍后重试'
  }

  return {
    toasts,
    showError,
    showWarning,
    showInfo,
    removeToast,
    handleApiError,
  }
}
```

- [ ] **Step 2: 创建错误提示组件**

创建 `frontend/src/components/ErrorToast.vue`：

```vue
<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast-item"
          :class="`toast--${toast.type}`"
        >
          <component :is="getIcon(toast.type)" :size="18" />
          <span class="toast-message">{{ toast.message }}</span>
          <button class="toast-close" @click="removeToast(toast.id)">
            <X :size="14" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { X, AlertCircle, AlertTriangle, Info } from 'lucide-vue-next'
import { useErrorHandler } from '../composables/useErrorHandler'

const { toasts, removeToast } = useErrorHandler()

function getIcon(type: string) {
  switch (type) {
    case 'error': return AlertCircle
    case 'warning': return AlertTriangle
    case 'info': return Info
    default: return Info
  }
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.toast-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 280px;
  max-width: 400px;
}

.toast--error {
  border-left: 3px solid var(--accent-red);
}

.toast--warning {
  border-left: 3px solid var(--accent-orange);
}

.toast--info {
  border-left: 3px solid var(--accent-blue);
}

.toast-message {
  flex: 1;
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.4;
}

.toast-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: 3px;
  padding: 0;
}

.toast-close:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

/* Transition */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
```

- [ ] **Step 3: 修改 API 层使用错误处理**

修改 `frontend/src/api/index.ts`：

```typescript
import { useErrorHandler } from '../composables/useErrorHandler'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 30000)
  const { handleApiError } = useErrorHandler()

  try {
    // ... 现有请求逻辑 ...

    if (response.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
      throw new Error('Session expired, please login again')
    }

    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText)
      const error = new Error(`API Error ${response.status}: ${errorText}`)
      // 显示友好错误提示
      const friendlyMessage = handleApiError(error)
      useErrorHandler().showError(friendlyMessage)
      throw error
    }

    // ... 其余逻辑 ...
  } catch (error) {
    clearTimeout(timeoutId)
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        const msg = 'Request timeout after 30s'
        useErrorHandler().showError('请求超时，请检查网络连接后重试')
        throw new Error(msg)
      }
      throw error
    }
    throw new Error('Unknown network error')
  }
}
```

- [ ] **Step 4: 在 App.vue 中注册 Toast 组件**

修改 `frontend/src/App.vue`，添加 `<ErrorToast />` 组件。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/composables/useErrorHandler.ts frontend/src/components/ErrorToast.vue frontend/src/api/index.ts frontend/src/App.vue
git commit -m "feat: add unified error handling with toast notifications"
```

---

## Task 3: Pinia 状态持久化

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/main.ts`
- Modify: `frontend/src/stores/user.ts`

**背景:** 刷新页面后用户信息和菜单数据丢失，需要重新获取。

- [ ] **Step 1: 安装持久化插件**

修改 `frontend/package.json`，添加依赖：

```json
"pinia-plugin-persistedstate": "^3.2.1"
```

然后运行：

```bash
cd frontend
npm install pinia-plugin-persistedstate
```

- [ ] **Step 2: 修改 main.ts 注册插件**

修改 `frontend/src/main.ts`：

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import App from './App.vue'
import router from './router'
import i18n from './i18n'

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

createApp(App)
  .use(pinia)
  .use(router)
  .use(i18n)
  .mount('#app')
```

- [ ] **Step 3: 修改 user store 添加持久化配置**

修改 `frontend/src/stores/user.ts`：

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface UserInfo {
  id: number
  username: string
  nickname: string | null
  email: string | null
  avatar: string | null
  roles: Array<{ id: number; name: string; display_name: string }>
  permissions: string[]
  agents: string[]
}

export const useUserStore = defineStore(
  'user',
  () => {
    const token = ref<string>('')
    const userInfo = ref<UserInfo | null>(null)
    const menus = ref<any[]>([])

    const isLoggedIn = computed(() => !!token.value)
    const hasPermission = computed(() => (perm: string) => {
      if (!userInfo.value) return false
      return userInfo.value.permissions.includes(perm)
    })
    const hasAgent = computed(() => (agentName: string) => {
      if (!userInfo.value) return false
      return userInfo.value.agents.includes(agentName)
    })

    function setToken(newToken: string) {
      token.value = newToken
      localStorage.setItem('token', newToken)
    }

    function clearToken() {
      token.value = ''
      userInfo.value = null
      menus.value = []
      localStorage.removeItem('token')
    }

    function setUserInfo(info: UserInfo) {
      userInfo.value = info
    }

    function setMenus(newMenus: any[]) {
      menus.value = newMenus
    }

    return {
      token,
      userInfo,
      menus,
      isLoggedIn,
      hasPermission,
      hasAgent,
      setToken,
      clearToken,
      setUserInfo,
      setMenus,
    }
  },
  {
    persist: {
      key: 'devmatrix-user',
      paths: ['userInfo', 'menus'],
      storage: localStorage,
    },
  }
)
```

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/main.ts frontend/src/stores/user.ts
git commit -m "feat: add Pinia state persistence for user info and menus"
```

---

## 批次 3 验收检查

- [ ] 无权限用户访问 `/users` 等管理页面被重定向到 `/forbidden`
- [ ] API 错误显示友好 Toast 提示，不暴露内部信息
- [ ] 刷新页面后用户信息和菜单自动恢复
- [ ] 网络超时显示"请求超时"提示
- [ ] 401 错误自动跳转到登录页
