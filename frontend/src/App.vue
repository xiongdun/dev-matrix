<!--
  @file DevMatrix 根组件
  @description 应用布局容器，包含侧边栏、顶部导航和主内容区
  @component App
  @slots
    - default: 主内容区，由路由渲染

  @example
  ```vue
  <template>
    <App />
  </template>
  ```
-->

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import TabBar from './components/TabBar.vue'
import AppConfirm from './components/AppConfirm.vue'
import AppPrompt from './components/AppPrompt.vue'
import ErrorToast from './components/ErrorToast.vue'
import { useI18n } from 'vue-i18n'
import { useDialog } from './composables/useDialog'
import { useUserStore } from './stores/user'
import { authApi } from './api/auth'
import { api } from './api'
import { User, ChevronDown, LogOut, Home, Settings } from 'lucide-vue-next'

const { t } = useI18n()
const { confirmState, promptState, confirmResult, promptResult, forceCloseAll } = useDialog()
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isFullscreenRoute = computed(() => !!route.meta.fullscreen)
const showUserMenu = ref(false)

const userDisplayName = computed(() => {
  return userStore.userInfo?.nickname || userStore.userInfo?.username || 'User'
})

const userAvatarText = computed(() => {
  const name = userDisplayName.value
  return name.charAt(0).toUpperCase()
})

function goToProfile() {
  showUserMenu.value = false
  if (userStore.userInfo?.id) {
    router.push(`/users/${userStore.userInfo.id}`)
  }
}

function goToSettings() {
  showUserMenu.value = false
  router.push('/settings/system')
}

function handleLogout() {
  showUserMenu.value = false
  userStore.clearToken()
  router.push('/login')
}

// 点击外部关闭下拉菜单
function closeUserMenu(e: Event) {
  const target = e.target as HTMLElement
  if (!target.closest('.user-profile-btn')) {
    showUserMenu.value = false
  }
}

// 路由切换时自动关闭所有弹窗，防止遮罩层残留
watch(() => route.path, () => {
  forceCloseAll()
})

onMounted(async () => {
  // 强制关闭所有弹窗，防止遮罩层残留
  forceCloseAll()

  // 全局 Esc 键兜底
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && (confirmState.value.visible || promptState.value.visible)) {
      forceCloseAll()
    }
  })

  if (userStore.isLoggedIn && userStore.menus.length === 0) {
    try {
      const userInfo = await authApi.getMe()
      userStore.setUserInfo(userInfo)
      const menus = await api.get('/menus/my')
      userStore.setMenus(menus)
    } catch (e) {
      userStore.clearToken()
    }
  }
  document.addEventListener('click', closeUserMenu)
})
</script>

<template>
  <div class="app-container">
    <Sidebar v-if="!isFullscreenRoute" />
    <div class="main-content" :class="{ fullscreen: isFullscreenRoute }">
      <template v-if="!isFullscreenRoute">
        <header class="top-nav">
          <h1>{{ t('app.title') }}</h1>
          <div class="top-nav-right">
            <div class="user-profile-btn" @click.stop="showUserMenu = !showUserMenu">
              <div class="user-avatar">{{ userAvatarText }}</div>
              <span class="user-name">{{ userDisplayName }}</span>
              <ChevronDown :size="14" class="user-chevron" :class="{ open: showUserMenu }" />
              <!-- 下拉菜单 -->
              <div v-if="showUserMenu" class="user-dropdown">
                <div class="dropdown-header">
                  <div class="dropdown-avatar">{{ userAvatarText }}</div>
                  <div class="dropdown-info">
                    <div class="dropdown-name">{{ userDisplayName }}</div>
                    <div class="dropdown-email">{{ userStore.userInfo?.email || '' }}</div>
                  </div>
                </div>
                <div class="dropdown-divider"></div>
                <button class="dropdown-item" @click="goToProfile">
                  <Home :size="16" />
                  <span>{{ t("userMenu.homepage") }}</span>
                </button>
                <button class="dropdown-item" @click="goToSettings">
                  <Settings :size="16" />
                  <span>{{ t("userMenu.settings") }}</span>
                </button>
                <div class="dropdown-divider"></div>
                <button class="dropdown-item danger" @click="handleLogout">
                  <LogOut :size="16" />
                  <span>{{ t("userMenu.logout") }}</span>
                </button>
              </div>
            </div>
          </div>
        </header>
        <TabBar />
      </template>
      <main class="content-area" :class="{ 'fullscreen-content': isFullscreenRoute }">
        <RouterView />
      </main>
    </div>

    <AppConfirm
      v-if="confirmState.visible"
      :visible="confirmState.visible"
      :title="confirmState.title"
      :message="confirmState.message"
      :type="confirmState.type"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :show-cancel="confirmState.showCancel"
      @confirm="confirmResult(true)"
      @cancel="confirmResult(false)"
    />

    <AppPrompt
      v-if="promptState.visible"
      :visible="promptState.visible"
      :title="promptState.title"
      :message="promptState.message"
      :placeholder="promptState.placeholder"
      :default-value="promptState.defaultValue"
      :confirm-text="promptState.confirmText"
      :cancel-text="promptState.cancelText"
      @confirm="(v) => promptResult(v)"
      @cancel="promptResult(null)"
    />

    <!-- 全局 Esc 兜底：关闭所有弹窗 -->
    <Teleport to="body">
      <div
        v-if="confirmState.visible || promptState.visible"
        class="modal-esc-catcher"
        @keydown.esc="
          confirmState.visible = false;
          promptState.visible = false;
          confirmResult(false);
          promptResult(null);
        "
        tabindex="0"
        style="position:fixed;top:0;left:0;width:0;height:0;opacity:0;pointer-events:none;"
      ></div>
    </Teleport>

    <ErrorToast />
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
  width: 100%;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: var(--sidebar-width);
  min-height: 100vh;
  width: calc(100% - var(--sidebar-width));
}

.top-nav {
  padding: 1rem 2rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--surface-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.top-nav h1 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.top-nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 用户头像按钮 */
.user-profile-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.15s;
  user-select: none;
}

.user-profile-btn:hover {
  background: var(--bg-hover);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.user-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.user-chevron {
  color: var(--text-muted);
  transition: transform 0.2s;
}

.user-chevron.open {
  transform: rotate(180deg);
}

/* 下拉菜单 */
.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 220px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  overflow: hidden;
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--bg-secondary);
}

.dropdown-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 600;
  flex-shrink: 0;
}

.dropdown-info {
  flex: 1;
  min-width: 0;
}

.dropdown-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-email {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-divider {
  height: 1px;
  background: var(--border-color);
  margin: 4px 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 16px;
  border: none;
  background: none;
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
  text-align: left;
}

.dropdown-item:hover {
  background: var(--bg-hover);
}

.dropdown-item.danger {
  color: var(--accent-red);
}

.dropdown-item.danger:hover {
  background: rgba(239, 68, 68, 0.08);
}

.content-area {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  width: 100%;
}

.main-content.fullscreen {
  margin-left: 0;
  width: 100vw;
  height: 100vh;
}

.content-area.fullscreen-content {
  padding: 0;
  overflow: hidden;
}
</style>
