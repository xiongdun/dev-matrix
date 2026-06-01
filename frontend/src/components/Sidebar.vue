<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useTabs } from '../composables/useTabs'
import { useUserStore } from '../stores/user'
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
  FolderKanban,
  Monitor,
  BrainCircuit,
  Database,
  Shield,
  Info,
  Clock,
  KanbanSquare,
  ListTodo,
  GitPullRequest,
  Users,
  UserCog,
  Menu,
} from 'lucide-vue-next'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const { addTab, activeTabId } = useTabs()
const userStore = useUserStore()

const iconMap: Record<string, any> = {
  LayoutDashboard,
  Bot,
  Wrench,
  GitBranch,
  Workflow,
  List,
  Layers,
  ClipboardCheck,
  Settings,
  FolderKanban,
  Monitor,
  BrainCircuit,
  Database,
  Shield,
  Info,
  Clock,
  KanbanSquare,
  ListTodo,
  GitPullRequest,
  Users,
  UserCog,
  Menu,
}

function transformMenuTree(menus: any[]): any[] {
  return menus.map((menu: any) => ({
    id: menu.name,
    path: menu.path || '',
    title: menu.title,
    icon: menu.icon || 'LayoutDashboard',
    iconComponent: iconMap[menu.icon || ''] || LayoutDashboard,
    permission: menu.permission,
    children: menu.children ? transformMenuTree(menu.children) : [],
  }))
}

const staticMenus = computed(() => {
  const menus = userStore.menus || []
  return transformMenuTree(menus)
})

const expandedIds = ref<Set<string>>(new Set())

const navigateTo = (item: any) => {
  if (item.children && item.children.length > 0) {
    if (expandedIds.value.has(item.id)) {
      expandedIds.value.delete(item.id)
    } else {
      expandedIds.value.add(item.id)
    }
    return
  }
  if (!item.path) return
  const title = t(item.title)
  addTab(item.id, title, item.path, item.icon)
}

const navigateToChild = (child: any) => {
  if (!child.path) return
  const title = t(child.title)
  addTab(child.id, title, child.path, child.icon)
}

const isActive = (path: string) => {
  return route.path === path || route.path.startsWith(path + '/')
}

const isParentActive = (item: any) => {
  if (!item.children) return false
  return item.children.some((child: any) => isActive(child.path))
}
</script>

<template>
  <aside class="sidebar">
    <nav class="sidebar-nav">
      <template v-for="item in staticMenus" :key="item.id">
        <div
          class="nav-item"
          :class="{ active: item.children ? isParentActive(item) : isActive(item.path), 'parent-active': isParentActive(item) }"
          @click="navigateTo(item)"
        >
          <component :is="item.iconComponent" class="nav-icon-lucide" :size="18" />
          <span class="nav-label">{{ t(item.title) }}</span>
          <ChevronDown
            v-if="item.children && item.children.length > 0"
            class="nav-expand"
            :class="{ expanded: expandedIds.has(item.id) }"
            :size="14"
          />
        </div>
        <div
          v-if="item.children && item.children.length > 0 && expandedIds.has(item.id)"
          class="nav-children"
        >
          <div
            v-for="child in item.children"
            :key="child.id"
            class="nav-item nav-child"
            :class="{ active: isActive(child.path) }"
            @click="navigateToChild(child)"
          >
            <component :is="child.iconComponent" class="nav-icon-lucide" :size="16" />
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
