<!--
  @file 侧边栏组件
  @description 应用主导航侧边栏，包含路由链接和主题切换
  @component Sidebar
  @emits
    - toggle: 侧边栏展开/收起状态变化
  @slots
    - default: 导航内容区

  @example
  ```vue
  <template>
    <Sidebar />
  </template>
  ```
-->

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useTabs } from '../composables/useTabs'

const { t } = useI18n()

const router = useRouter()
const route = useRoute()
const { addTab, activeTabId } = useTabs()

interface NavItem {
  id: string
  path: string
  title: string
  icon: string
  children?: NavItem[]
}

const workflowExpanded = ref(true)

const navItems: NavItem[] = [
  { id: 'dashboard', path: '/', title: 'sidebar.dashboard', icon: '📊' },
  { id: 'agents', path: '/agents', title: 'sidebar.agents', icon: '🤖' },
  { id: 'skills', path: '/skills', title: 'sidebar.skills', icon: '🔧' },
  {
    id: 'workflow',
    path: '/workflow',
    title: 'sidebar.workflow',
    icon: '🔄',
    children: [
      { id: 'workflow-editor', path: '/workflow/editor', title: 'sidebar.workflowEditor', icon: '✏️' },
      { id: 'workflow-list', path: '/workflow/list', title: 'sidebar.workflowList', icon: '📋' },
    ],
  },
  { id: 'workbench', path: '/workbench', title: 'sidebar.workbench', icon: '📋' },
  { id: 'settings', path: '/settings', title: 'sidebar.settings', icon: '⚙️' },
]

const navigateTo = (item: NavItem) => {
  if (item.children) {
    workflowExpanded.value = !workflowExpanded.value
    return
  }
  const title = t(item.title)
  addTab(item.id, title, item.path)
}

const navigateToChild = (child: NavItem) => {
  const title = t(child.title)
  addTab(child.id, title, child.path)
}

const isActive = (path: string) => {
  return route.path === path || route.path.startsWith(path + '/')
}

const isParentActive = (item: NavItem) => {
  if (!item.children) return false
  return route.path.startsWith(item.path)
}
</script>

<template>
  <aside class="sidebar">
    <nav class="sidebar-nav">
      <template v-for="item in navItems" :key="item.id">
        <div
          class="nav-item"
          :class="{ active: item.children ? isParentActive(item) : isActive(item.path), 'parent-active': isParentActive(item) }"
          @click="navigateTo(item)"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ t(item.title) }}</span>
          <span v-if="item.children" class="nav-expand" :class="{ expanded: workflowExpanded }">▾</span>
        </div>
        <div v-if="item.children && workflowExpanded" class="nav-children">
          <div
            v-for="child in item.children"
            :key="child.id"
            class="nav-item nav-child"
            :class="{ active: isActive(child.path) }"
            @click="navigateToChild(child)"
          >
            <span class="nav-icon">{{ child.icon }}</span>
            <span class="nav-label">{{ t(child.title) }}</span>
          </div>
        </div>
      </template>
    </nav>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 240px;
  background: var(--surface-color);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.sidebar-nav {
  padding: 1rem 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1.5rem;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.2s ease;
  gap: 0.75rem;
  cursor: pointer;
}

.nav-item:hover {
  background: var(--hover-color);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--primary-color);
  color: white;
}

.nav-item.parent-active {
  background: transparent;
  color: var(--text-primary);
  font-weight: 600;
}

.nav-icon {
  font-size: 1.25rem;
}

.nav-label {
  font-size: 0.875rem;
  font-weight: 500;
  flex: 1;
}

.nav-expand {
  font-size: 0.75rem;
  transition: transform 0.2s ease;
}

.nav-expand.expanded {
  transform: rotate(180deg);
}

.nav-children {
  padding-left: 1rem;
}

.nav-child {
  padding: 0.5rem 1.5rem 0.5rem 2rem;
}
</style>
