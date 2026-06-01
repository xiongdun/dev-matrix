<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Tab } from '../composables/useTabs'
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
  Monitor,
  BrainCircuit,
  Database,
  Shield,
  Info,
  FolderKanban,
  Clock,
  KanbanSquare,
  ListTodo,
  GitPullRequest,
  Users,
  UserCog,
  Menu,
  X,
} from 'lucide-vue-next'

interface Props {
  tab: Tab
  active: boolean
}

const props = defineProps<Props>()
const { t } = useI18n()

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'close'): void
  (e: 'contextmenu', event: MouseEvent): void
}>()

const iconComponentMap: Record<string, any> = {
  LayoutDashboard,
  Bot,
  Wrench,
  GitBranch,
  Workflow,
  List,
  Layers,
  ClipboardCheck,
  Settings,
  Monitor,
  BrainCircuit,
  Database,
  Shield,
  Info,
  FolderKanban,
  Clock,
  KanbanSquare,
  ListTodo,
  GitPullRequest,
  Users,
  UserCog,
  Menu,
}

const tabIcon = computed(() => {
  if (props.tab.icon && iconComponentMap[props.tab.icon]) {
    return iconComponentMap[props.tab.icon]
  }
  return GitBranch
})

const displayTitle = computed(() => {
  const titleMap: Record<string, string> = {
    dashboard: t('sidebar.dashboard'),
    projects: t('sidebar.projects'),
    agents: t('sidebar.agents'),
    skills: t('sidebar.skills'),
    settings: t('sidebar.settings'),
    'settings-system': t('sidebar.settingsSystem'),
    'settings-llm': t('sidebar.settingsLlm'),
    'settings-database': t('sidebar.settingsDatabase'),
    'settings-security': t('sidebar.settingsSecurity'),
    'settings-about': t('sidebar.settingsAbout'),
    'workflow_list': t('sidebar.workflowList'),
    'workflow_editor': t('sidebar.workflowEditor'),
    'workflow_instances': t('sidebar.workflowInstances'),
    workbench: t('sidebar.workbench'),
    'scheduled-tasks': t('sidebar.scheduledTasks'),
    'my-tasks': t('sidebar.myTasks'),
    'task-board': t('sidebar.taskBoard'),
    user_management: t('sidebar.userManagement'),
    role_management: t('sidebar.roleManagement'),
    menu_management: t('sidebar.menuManagement'),
  }
  return titleMap[props.tab.id] || props.tab.title
})
</script>

<template>
  <div
    class="tabbar-item"
    :class="{ active }"
    @click="emit('click')"
    @contextmenu="emit('contextmenu', $event)"
  >
    <component :is="tabIcon" class="tab-icon" :size="14" />
    <span class="tab-title">{{ displayTitle }}</span>
    <button
      v-if="tab.closable"
      class="tab-close"
      @click.stop="emit('close')"
      :title="t('tabBar.closeTitle')"
    >
      <X :size="12" />
    </button>
  </div>
</template>

<style scoped>
.tabbar-item {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 13px;
  transition: all 0.15s ease;
  position: relative;
  border: 1px solid transparent;
  white-space: nowrap;
}

.tabbar-item:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

.tabbar-item.active {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  border-color: var(--border-color);
}

.tabbar-item.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background-color: var(--accent-blue);
}

.tab-icon {
  flex-shrink: 0;
  opacity: 0.7;
}

.tab-title {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tab-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: 3px;
  margin-left: 4px;
  padding: 0;
  line-height: 1;
  visibility: hidden;
  opacity: 0;
  transition: opacity 0.15s ease, visibility 0.15s ease;
}

.tabbar-item:hover .tab-close {
  visibility: visible;
  opacity: 1;
}

.tab-close:hover {
  background-color: var(--bg-active);
  color: var(--text-primary);
}
</style>
