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
import { RouterView } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import TabBar from './components/TabBar.vue'
import AppConfirm from './components/AppConfirm.vue'
import AppPrompt from './components/AppPrompt.vue'
import { useI18n } from 'vue-i18n'
import { useDialog } from './composables/useDialog'

const { t } = useI18n()
const { confirmState, promptState, confirmResult, promptResult } = useDialog()
</script>

<template>
  <div class="app-container">
    <Sidebar />
    <div class="main-content">
      <header class="top-nav">
        <h1>{{ t('app.title') }}</h1>
      </header>
      <TabBar />
      <main class="content-area">
        <RouterView />
      </main>
    </div>

    <AppConfirm
      v-model:visible="confirmState.visible"
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
      v-model:visible="promptState.visible"
      :title="promptState.title"
      :message="promptState.message"
      :placeholder="promptState.placeholder"
      :default-value="promptState.defaultValue"
      :confirm-text="promptState.confirmText"
      :cancel-text="promptState.cancelText"
      @confirm="(v) => promptResult(v)"
      @cancel="promptResult(null)"
    />
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
}

.top-nav h1 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.content-area {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  width: 100%;
}
</style>
