/**
 * @file 设置组合式函数（后端持久化版）
 * @description 通过后端 API 读写应用设置，支持实时同步
 * @module useSettings
 *
 * @example
 * ```ts
 * import { useSettings } from './composables/useSettings'
 *
 * const { settings, updateSettings, refreshSettings } = useSettings()
 * await updateSettings({ theme: 'dark' })
 * ```
 */

import { ref, computed, watch } from 'vue'
import { api } from '../api'

export interface AppSettings {
  theme: 'light' | 'dark' | 'auto'
  language: string
  notifications_enabled: boolean
  auto_save_interval: number
  defaultLLMProvider: string
  defaultLLMModel: string
  llm_strategy: string
  app_name: string
  [key: string]: any
}

const DEFAULT_SETTINGS: AppSettings = {
  theme: 'auto',
  language: 'zh',
  notifications_enabled: true,
  auto_save_interval: 30000,
  defaultLLMProvider: 'openai',
  defaultLLMModel: 'gpt-4',
  llm_strategy: 'quality_first',
  app_name: 'DevMatrix',
}

const rawConfigs = ref<Record<string, string>>({})
const isLoading = ref(false)
const error = ref('')

function applyTheme(theme: 'light' | 'dark' | 'auto') {
  let resolved: string
  if (theme === 'auto') {
    resolved = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
  } else {
    resolved = theme
  }
  document.documentElement.setAttribute('data-theme', resolved)
}

function parseValue(key: string, value: string): any {
  if (key === 'notifications_enabled') return value === 'true'
  if (key === 'auto_save_interval') return parseInt(value, 10) || 30000
  return value
}

export function useSettings() {
  const settings = computed<AppSettings>(() => {
    const result: any = { ...DEFAULT_SETTINGS }
    for (const [key, value] of Object.entries(rawConfigs.value)) {
      const mappedKey = key === 'llm_provider' ? 'defaultLLMProvider'
        : key === 'llm_model' ? 'defaultLLMModel'
        : key
      result[mappedKey] = parseValue(key, value)
    }
    return result as AppSettings
  })

  const refreshSettings = async () => {
    isLoading.value = true
    error.value = ''
    try {
      const res = await api.getSettings()
      const configs: Record<string, string> = {}
      for (const c of res.configs) {
        configs[c.key] = c.value
      }
      rawConfigs.value = configs
      applyTheme(settings.value.theme)
    } catch (e: any) {
      error.value = e.message || String(e)
      console.error('Failed to load settings:', e)
    } finally {
      isLoading.value = false
    }
  }

  const updateSettings = async (partial: Partial<Record<string, any>>) => {
    const updates: Record<string, string> = {}
    for (const [key, value] of Object.entries(partial)) {
      const configKey = key === 'defaultLLMProvider' ? 'llm_provider'
        : key === 'defaultLLMModel' ? 'llm_model'
        : key
      updates[configKey] = String(value)
    }

    try {
      const res = await api.updateSettings(updates)
      for (const c of res.configs) {
        rawConfigs.value[c.key] = c.value
      }
      if (updates.theme !== undefined) {
        applyTheme(settings.value.theme)
      }
      return true
    } catch (e: any) {
      error.value = e.message || String(e)
      console.error('Failed to update settings:', e)
      return false
    }
  }

  const resetSettings = async () => {
    try {
      await api.initSettings()
      await refreshSettings()
      return true
    } catch (e: any) {
      error.value = e.message || String(e)
      return false
    }
  }

  // 监听系统主题变化
  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => {
    if (settings.value.theme === 'auto') {
      applyTheme('auto')
    }
  })

  return {
    settings,
    isLoading,
    error,
    refreshSettings,
    updateSettings,
    resetSettings,
  }
}
