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
import { useI18n } from 'vue-i18n'

/**
 * 国际化组合式函数
 * @returns {Object} i18n 实例
 */
const { t } = useI18n()
</script>

<template>
  <div class="app-container">
    <!-- 侧边栏导航 -->
    <Sidebar />
    <div class="main-content">
      <!-- 顶部导航栏 -->
      <header class="top-nav">
        <h1>{{ t('app.title') }}</h1>
      </header>
      <!-- Tab 标签栏 -->
      <TabBar />
      <!-- 主内容区，路由视图 -->
      <main class="content-area">
        <RouterView />
      </main>
    </div>
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
