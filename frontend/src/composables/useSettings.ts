/**
 * @file 设置组合式函数
 * @description 提供应用设置的响应式状态和持久化存储
 * @module useSettings
 *
 * @example
 * ```ts
 * import { useSettings } from './composables/useSettings'
 *
 * const { settings, updateSettings, resetSettings } = useSettings()
 * updateSettings({ theme: 'dark' })
 * ```
 */

import { ref, watch } from 'vue'

/**
 * 应用设置接口
 * @interface AppSettings
 */
export interface AppSettings {
  /** 主题模式 */
  theme: 'light' | 'dark' | 'auto'
  /** 语言代码 */
  language: string
  /** 是否启用通知 */
  notifications: boolean
  /** 自动保存间隔（毫秒） */
  autoSaveInterval: number
  /** 默认 LLM 提供商 */
  defaultLLMProvider: string
  /** 默认 LLM 模型 */
  defaultLLMModel: string
}

/**
 * 默认设置配置
 * @type {AppSettings}
 */
const DEFAULT_SETTINGS: AppSettings = {
  theme: 'auto',
  language: 'zh',
  notifications: true,
  autoSaveInterval: 30000,
  defaultLLMProvider: 'openai',
  defaultLLMModel: 'gpt-4',
}

/**
 * 存储键名
 * @type {string}
 */
const STORAGE_KEY = 'devmatrix-settings'

/**
 * 从本地存储加载设置
 * @returns {AppSettings} 加载的设置或默认值
 */
function loadSettings(): AppSettings {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) }
    }
  } catch (e) {
    console.error('Failed to load settings:', e)
  }
  return { ...DEFAULT_SETTINGS }
}

/**
 * 保存设置到本地存储
 * @param {AppSettings} settings - 要保存的设置
 */
function saveSettings(settings: AppSettings): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch (e) {
    console.error('Failed to save settings:', e)
  }
}

/**
 * 设置组合式函数
 * @returns {Object} 设置状态和操作方法
 * @property {import('vue').Ref<AppSettings>} settings - 响应式设置状态
 * @property {Function} updateSettings - 更新设置方法
 * @property {Function} resetSettings - 重置设置方法
 */
export function useSettings() {
  const settings = ref<AppSettings>(loadSettings())

  // 监听设置变化并自动保存
  watch(
    settings,
    (newSettings) => {
      saveSettings(newSettings)
    },
    { deep: true }
  )

  /**
   * 更新设置
   * @param {Partial<AppSettings>} partial - 部分设置对象
   */
  const updateSettings = (partial: Partial<AppSettings>) => {
    settings.value = { ...settings.value, ...partial }
  }

  /**
   * 重置设置为默认值
   */
  const resetSettings = () => {
    settings.value = { ...DEFAULT_SETTINGS }
  }

  return {
    settings,
    updateSettings,
    resetSettings,
  }
}
