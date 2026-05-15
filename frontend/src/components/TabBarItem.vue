<!--
  @file Tab 标签项组件
  @description 单个标签页的显示组件，支持激活状态和关闭按钮
  @component TabBarItem
  @props
    - tab: Tab 对象
    - active: 是否为当前激活标签
  @emits
    - click: 点击标签时触发
    - close: 点击关闭按钮时触发
    - contextmenu: 右键点击时触发

  @example
  ```vue
  <template>
    <TabBarItem
      :tab="{ id: 'settings', title: 'Settings', path: '/settings', closable: true }"
      :active="true"
      @click="handleClick"
      @close="handleClose"
    />
  </template>
  ```
-->

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Tab } from '../composables/useTabs'

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

const getTabIcon = (id: string): string => {
  const icons: Record<string, string> = {
    dashboard: '⊞',
    agents: '◈',
    skills: '◇',
    settings: '⚙',
  }
  return icons[id] || '○'
}

const displayTitle = computed(() => {
  const titleMap: Record<string, string> = {
    dashboard: t('sidebar.dashboard'),
    agents: t('sidebar.agents'),
    skills: t('sidebar.skills'),
    settings: t('sidebar.settings'),
    'workflow-list': t('sidebar.workflowList'),
    'workflow-editor': t('sidebar.workflowEditor'),
    workbench: t('sidebar.workbench'),
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
    <span class="tab-icon">{{ getTabIcon(tab.id) }}</span>
    <span class="tab-title">{{ displayTitle }}</span>
    <button
      v-if="tab.closable"
      class="tab-close"
      @click.stop="emit('close')"
      :title="t('tabBar.closeTitle')"
    >
      ×
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
  font-size: 12px;
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
  font-size: 14px;
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
