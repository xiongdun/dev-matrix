<!--
  @file Tab 标签栏组件
  @description 多页面标签页切换组件，支持添加、关闭、切换 Tab
  @component TabBar
  @props
    - 无需 props，状态由 useTabs composable 管理
  @emits
    - tab-click: 点击 Tab 时触发
    - tab-close: 关闭 Tab 时触发

  @example
  ```vue
  <template>
    <TabBar />
  </template>
  ```
-->

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTabs, type Tab } from '../composables/useTabs'
import TabBarItem from './TabBarItem.vue'
import ContextMenu from './ContextMenu.vue'

const { t } = useI18n()
const { tabs, activeTabId, setActiveTab, closeTab, closeOtherTabs, closeAllTabs } = useTabs()

interface MenuItem {
  label: string
  action: () => void
  disabled?: boolean
}

const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })
const contextMenuTarget = ref<Tab | null>(null)

const showContextMenu = (event: MouseEvent, tab: Tab) => {
  event.preventDefault()
  contextMenuTarget.value = tab
  contextMenuPosition.value = { x: event.clientX, y: event.clientY }
  contextMenuVisible.value = true
}

const hideContextMenu = () => {
  contextMenuVisible.value = false
  contextMenuTarget.value = null
}

const menuItems = (tab: Tab): MenuItem[] => [
  {
    label: t('tabBar.close'),
    action: () => closeTab(tab.id),
    disabled: !tab.closable,
  },
  {
    label: t('tabBar.closeOthers'),
    action: () => closeOtherTabs(tab.id),
    disabled: !tab.closable && tabs.value.length <= 1,
  },
  {
    label: t('tabBar.closeAll'),
    action: closeAllTabs,
  },
]

const handleTabClick = (tab: Tab) => {
  setActiveTab(tab.id)
}

const handleTabClose = (tab: Tab) => {
  closeTab(tab.id)
}
</script>

<template>
  <div class="tabbar" @click="hideContextMenu">
    <div class="tabbar-tabs">
      <TabBarItem
        v-for="tab in tabs"
        :key="tab.id"
        :tab="tab"
        :active="activeTabId === tab.id"
        @click="handleTabClick(tab)"
        @close="handleTabClose(tab)"
        @contextmenu="showContextMenu($event, tab)"
      />
    </div>

    <ContextMenu
      v-if="contextMenuVisible"
      :items="menuItems(contextMenuTarget!)"
      :position="contextMenuPosition"
      @close="hideContextMenu"
    />
  </div>
</template>

<style scoped>
.tabbar {
  height: var(--tabbar-height);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  padding: 0 8px;
  overflow-x: auto;
  overflow-y: hidden;
}

.tabbar::-webkit-scrollbar {
  height: 4px;
}

.tabbar::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}

.tabbar-tabs {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 100%;
}
</style>
