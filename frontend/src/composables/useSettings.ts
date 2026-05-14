import { reactive, watch } from 'vue'

export interface Settings {
  appearance: {
    theme: 'dark' | 'light'
    language: 'zh' | 'en'
    sidebarCollapsed: boolean
  }
  llm: {
    provider: 'openai' | 'anthropic'
    apiKey: string
    model: string
    strategy: 'quality_first' | 'cost_first' | 'config_driven'
  }
  workflow: {
    approvalMode: 'manual' | 'auto'
    timeout: number
    retryCount: number
  }
  notifications: {
    workflowCompleted: boolean
    approvalRequired: boolean
    agentFailed: boolean
    webhookUrl: string
  }
}

const STORAGE_KEY = 'devmatrix-settings'

const defaultSettings: Settings = {
  appearance: {
    theme: 'dark',
    language: 'zh',
    sidebarCollapsed: false,
  },
  llm: {
    provider: 'openai',
    apiKey: '',
    model: 'gpt-4',
    strategy: 'quality_first',
  },
  workflow: {
    approvalMode: 'manual',
    timeout: 30,
    retryCount: 3,
  },
  notifications: {
    workflowCompleted: true,
    approvalRequired: true,
    agentFailed: false,
    webhookUrl: '',
  },
}

function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      return { ...defaultSettings, ...JSON.parse(raw) }
    }
  } catch {
    // ignore
  }
  return { ...defaultSettings }
}

export const settings = reactive<Settings>(loadSettings())

watch(
  () => settings,
  (val) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(val))
  },
  { deep: true }
)

export function useSettings() {
  return {
    settings,
    reset() {
      Object.assign(settings, defaultSettings)
    },
  }
}
