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

export interface AppSettings {
  theme: 'light' | 'dark' | 'auto'
  language: string
  notifications: boolean
  autoSaveInterval: number
  defaultLLMProvider: string
  defaultLLMModel: string
}

const DEFAULT_SETTINGS: AppSettings = {
  theme: 'auto',
  language: 'zh',
  notifications: true,
  autoSaveInterval: 30000,
  defaultLLMProvider: 'openai',
  defaultLLMModel: 'gpt-4',
}

const STORAGE_KEY = 'devmatrix-settings'

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

function saveSettings(settings: AppSettings): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch (e) {
    console.error('Failed to save settings:', e)
  }
}

function applyTheme(theme: 'light' | 'dark' | 'auto') {
  let resolved: string
  if (theme === 'auto') {
    resolved = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
  } else {
    resolved = theme
  }
  document.documentElement.setAttribute('data-theme', resolved)
}

export function useSettings() {
  const settings = ref<AppSettings>(loadSettings())

  applyTheme(settings.value.theme)

  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => {
    if (settings.value.theme === 'auto') {
      applyTheme('auto')
    }
  })

  watch(
    settings,
    (newSettings) => {
      saveSettings(newSettings)
      applyTheme(newSettings.theme)
    },
    { deep: true }
  )

  const updateSettings = (partial: Partial<AppSettings>) => {
    settings.value = { ...settings.value, ...partial }
  }

  const resetSettings = () => {
    settings.value = { ...DEFAULT_SETTINGS }
  }

  return {
    settings,
    updateSettings,
    resetSettings,
  }
}
