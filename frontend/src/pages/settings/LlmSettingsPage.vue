<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../../api'
import SettingsSection from '../../components/settings/SettingsSection.vue'
import SettingItem from '../../components/settings/SettingItem.vue'

const { t } = useI18n()

interface ConfigItem {
  key: string
  value: string
  category: string
  description: string | null
  is_sensitive: boolean
}

const configs = reactive<Record<string, string>>({})
const originalConfigs = reactive<Record<string, string>>({})
const isLoading = ref(false)
const saving = ref(false)
const message = ref('')
const error = ref('')

onMounted(() => {
  loadConfigs()
})

const loadConfigs = async () => {
  isLoading.value = true
  error.value = ''
  try {
    const res = await api.getSettings('llm')
    for (const c of res.configs) {
      configs[c.key] = c.value
      originalConfigs[c.key] = c.value
    }
  } catch (e: any) {
    error.value = e.message || String(e)
  } finally {
    isLoading.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  message.value = ''
  error.value = ''

  const updates: Record<string, string> = {}
  for (const key of Object.keys(configs)) {
    if (configs[key] !== originalConfigs[key]) {
      updates[key] = configs[key]
    }
  }

  if (Object.keys(updates).length === 0) {
    message.value = t('settings.noChanges')
    saving.value = false
    setTimeout(() => message.value = '', 3000)
    return
  }

  try {
    await api.updateSettings(updates)
    for (const key of Object.keys(updates)) {
      originalConfigs[key] = configs[key]
    }
    message.value = t('settings.saveSuccess')
  } catch (e: any) {
    error.value = e.message || String(e)
  } finally {
    saving.value = false
    setTimeout(() => { message.value = ''; error.value = '' }, 3000)
  }
}

const handleReset = async () => {
  try {
    await api.initSettings()
    await loadConfigs()
    message.value = t('settings.resetSuccess')
    setTimeout(() => message.value = '', 3000)
  } catch (e: any) {
    error.value = e.message || String(e)
  }
}
</script>

<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>{{ t('settings.llmTitle') }}</h1>
        <p>{{ t('settings.llmSubtitle') }}</p>
      </div>
    </div>

    <div v-if="isLoading" class="loading">{{ t('common.loading') }}...</div>

    <template v-else>
      <SettingsSection :title="t('settings.llmProvider')" :description="t('settings.llmProviderDesc')">
        <SettingItem
          :label="t('settings.llmProvider')"
          :description="t('settings.llmProviderDesc')"
          type="select"
          v-model="configs.llm_provider"
          :options="[
            { value: 'openai', label: 'OpenAI' },
            { value: 'anthropic', label: 'Anthropic' },
            { value: 'azure', label: 'Azure OpenAI' },
          ]"
        />
        <SettingItem
          :label="t('settings.llmModel')"
          :description="t('settings.llmModelDesc')"
          type="text"
          v-model="configs.llm_model"
        />
        <SettingItem
          :label="t('settings.llmStrategy')"
          :description="t('settings.llmStrategyDesc')"
          type="select"
          v-model="configs.llm_strategy"
          :options="[
            { value: 'quality_first', label: t('settings.strategyQuality') },
            { value: 'cost_first', label: t('settings.strategyCost') },
            { value: 'config_driven', label: t('settings.strategyConfig') },
          ]"
        />
      </SettingsSection>

      <SettingsSection :title="t('settings.apiKeys')" :description="t('settings.apiKeysDesc')">
        <SettingItem
          :label="t('settings.openaiApiKey')"
          :description="t('settings.openaiApiKeyDesc')"
          type="password"
          v-model="configs.openai_api_key"
          :placeholder="t('settings.enterApiKey')"
        />
        <SettingItem
          :label="t('settings.anthropicApiKey')"
          :description="t('settings.anthropicApiKeyDesc')"
          type="password"
          v-model="configs.anthropic_api_key"
          :placeholder="t('settings.enterApiKey')"
        />
      </SettingsSection>

      <SettingsSection title="Claude Agent SDK" description="Claude Code 集成配置">
        <SettingItem
          :label="t('settings.claudeSdkEnabled')"
          :description="t('settings.claudeSdkEnabledDesc')"
          type="checkbox"
          v-model="configs.claude_sdk_enabled"
        />
        <SettingItem
          :label="t('settings.claudeSdkSessionId')"
          :description="t('settings.claudeSdkSessionIdDesc')"
          type="text"
          v-model="configs.claude_sdk_session_id"
          placeholder="可选"
        />
      </SettingsSection>

      <SettingsSection :title="t('settings.advanced')" :description="t('settings.advancedDesc')">
        <SettingItem
          :label="t('settings.openaiBaseUrl')"
          :description="t('settings.openaiBaseUrlDesc')"
          type="text"
          v-model="configs.openai_base_url"
        />
        <SettingItem
          :label="t('settings.anthropicBaseUrl')"
          :description="t('settings.anthropicBaseUrlDesc')"
          type="text"
          v-model="configs.anthropic_base_url"
        />
      </SettingsSection>

      <div class="settings-actions">
        <span v-if="message" class="save-message success">{{ message }}</span>
        <span v-if="error" class="save-message error">{{ error }}</span>
        <button class="btn btn-secondary" @click="handleReset" :disabled="saving">
          {{ t('settings.resetDefaults') }}
        </button>
        <button class="btn btn-primary" :disabled="saving" @click="handleSave">
          {{ saving ? t('common.saving') : t('common.save') }}
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.loading {
  padding: 2rem;
  text-align: center;
  color: var(--text-secondary);
}

.settings-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.save-message {
  font-size: 0.875rem;
}

.save-message.success {
  color: var(--accent-green);
}

.save-message.error {
  color: var(--accent-red);
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  font-size: 0.875rem;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-color-dark);
}

.btn-secondary {
  background: var(--surface-color);
  color: var(--text-primary);
  border-color: var(--border-color);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--hover-color);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
