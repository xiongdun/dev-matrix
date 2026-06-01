/**
 * @file Tab 状态管理组合式函数
 * @description 管理多页面标签页的状态，包括添加、删除、切换 Tab
 * @module composables/useTabs
 *
 * @example
 * ```ts
 * const { tabs, activeTabId, addTab, closeTab, setActiveTab } = useTabs()
 * ```
 */

import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

/**
 * Tab 数据结构
 * @interface Tab
 */
export interface Tab {
  /** Tab 唯一标识（路由名称） */
  id: string
  /** Tab 显示标题 */
  title: string
  /** 路由路径 */
  path: string
  /** 是否可关闭 */
  closable: boolean
  /** 图标名称 */
  icon?: string
}

const tabs = ref<Tab[]>([
  {
    id: 'dashboard',
    title: 'Dashboard',
    path: '/',
    closable: false,
    icon: 'LayoutDashboard',
  },
])

const activeTabId = ref('dashboard')

/**
 * Tab 状态管理组合式函数
 * @returns {Object} Tab 状态和操作方法
 */
export function useTabs() {
  const router = useRouter()

  const findTabByName = (name: string): Tab | undefined => {
    return tabs.value.find((tab) => tab.id === name)
  }

  const addTab = (name: string, title: string, path: string, icon?: string) => {
    const existingTab = findTabByName(name)
    if (existingTab) {
      activeTabId.value = name
      router.push(path)
      return
    }

    tabs.value.push({
      id: name,
      title,
      path,
      closable: true,
      icon,
    })
    activeTabId.value = name
    router.push(path)
  }

  const closeTab = (tabId: string) => {
    const tabIndex = tabs.value.findIndex((tab) => tab.id === tabId)
    if (tabIndex === -1) return

    const closingTab = tabs.value[tabIndex]
    if (!closingTab.closable) return

    tabs.value.splice(tabIndex, 1)

    if (activeTabId.value === tabId) {
      if (tabs.value.length > 0) {
        const newIndex = Math.min(tabIndex, tabs.value.length - 1)
        const newTab = tabs.value[newIndex]
        activeTabId.value = newTab.id
        router.push(newTab.path)
      } else {
        addTab('dashboard', 'Dashboard', '/')
      }
    }
  }

  const closeOtherTabs = (tabId: string) => {
    const targetTab = findTabByName(tabId)
    if (!targetTab) return

    tabs.value = tabs.value.filter((tab) => !tab.closable || tab.id === tabId)
    activeTabId.value = tabId
    router.push(targetTab.path)
  }

  const closeAllTabs = () => {
    tabs.value = tabs.value.filter((tab) => !tab.closable)
    if (tabs.value.length > 0) {
      const firstTab = tabs.value[0]
      activeTabId.value = firstTab.id
      router.push(firstTab.path)
    } else {
      addTab('dashboard', 'Dashboard', '/')
    }
  }

  const setActiveTab = (tabId: string) => {
    const tab = findTabByName(tabId)
    if (tab) {
      activeTabId.value = tabId
      router.push(tab.path)
    }
  }

  const activeTab = computed(() => findTabByName(activeTabId.value))

  return {
    tabs,
    activeTabId,
    activeTab,
    addTab,
    closeTab,
    closeOtherTabs,
    closeAllTabs,
    setActiveTab,
    findTabByName,
  }
}
