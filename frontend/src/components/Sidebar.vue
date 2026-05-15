<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useTabs } from '../composables/useTabs'
import {
  LayoutDashboard,
  Bot,
  Wrench,
  GitBranch,
  Workflow,
  List,
  Layers,
  ClipboardCheck,
  Settings,
  ChevronDown,
} from 'lucide-vue-next'

const { t } = useI18n()

const router = useRouter()
const route = useRoute()
const { addTab, activeTabId } = useTabs()

interface NavItem {
  id: string
  path: string
  title: string
  icon: any
  children?: NavItem[]
}

const workflowExpanded = ref(true)

const navItems: NavItem[] = [
  { id: 'dashboard', path: '/', title: 'sidebar.dashboard', icon: LayoutDashboard },
  { id: 'agents', path: '/agents', title: 'sidebar.agents', icon: Bot },
  { id: 'skills', path: '/skills', title: 'sidebar.skills', icon: Wrench },
  {
    id: 'workflow',
    path: '/workflow',
    title: 'sidebar.workflow',
    icon: GitBranch,
    children: [
      { id: 'workflow-editor', path: '/workflow/editor', title: 'sidebar.workflowEditor', icon: Workflow },
      { id: 'workflow-list', path: '/workflow/list', title: 'sidebar.workflowList', icon: List },
      { id: 'workflow-instances', path: '/workflow/instances', title: 'sidebar.workflowInstances', icon: Layers },
    ],
  },
  { id: 'workbench', path: '/workbench', title: 'sidebar.workbench', icon: ClipboardCheck },
  { id: 'settings', path: '/settings', title: 'sidebar.settings', icon: Settings },
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
          <component :is="item.icon" class="nav-icon-lucide" :size="18" />
          <span class="nav-label">{{ t(item.title) }}</span>
          <ChevronDown v-if="item.children" class="nav-expand" :class="{ expanded: workflowExpanded }" :size="14" />
        </div>
        <div v-if="item.children && workflowExpanded" class="nav-children">
          <div
            v-for="child in item.children"
            :key="child.id"
            class="nav-item nav-child"
            :class="{ active: isActive(child.path) }"
            @click="navigateToChild(child)"
          >
            <component :is="child.icon" class="nav-icon-lucide" :size="16" />
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

.nav-icon-lucide {
  flex-shrink: 0;
}

.nav-label {
  font-size: 0.875rem;
  font-weight: 500;
  flex: 1;
}

.nav-expand {
  transition: transform 0.2s ease;
  flex-shrink: 0;
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
