<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSettings } from '../composables/useSettings'
import SettingsSection from '../components/settings/SettingsSection.vue'
import SettingItem from '../components/settings/SettingItem.vue'

const { t, locale } = useI18n()
const { settings, updateSettings, resetSettings } = useSettings()

const languageOptions = computed(() => [
  { value: 'zh', label: t('settings.languageZh') },
  { value: 'en', label: t('settings.languageEn') },
])

const llmProviderOptions = computed(() => [
  { value: 'openai', label: t('settings.providerOpenai') },
  { value: 'anthropic', label: t('settings.providerAnthropic') },
])

const llmModelOptions = computed(() => [
  { value: 'gpt-4', label: t('settings.modelGpt4') },
  { value: 'gpt-3.5-turbo', label: t('settings.modelGpt35Turbo') },
  { value: 'claude-3-opus-20240229', label: t('settings.modelClaude3Opus') },
  { value: 'claude-3-sonnet-20240229', label: t('settings.modelClaude3Sonnet') },
])

const handleLanguageChange = (value: string) => {
  locale.value = value
  updateSettings({ language: value })
}

const handleThemeChange = (value: string) => {
  updateSettings({ theme: value as 'light' | 'dark' | 'auto' })
}
</script>

<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>{{ t('settings.title') }}</h1>
        <p>{{ t('settings.subtitle') }}</p>
      </div>
    </div>

    <SettingsSection :title="t('settings.appearance')" :description="t('settings.appearanceDesc')">
      <SettingItem
        :label="t('settings.themeLabel')"
        :description="t('settings.themeDesc')"
        type="select"
        v-model="settings.theme"
        :options="[
          { value: 'light', label: t('settings.themeLight') },
          { value: 'dark', label: t('settings.themeDark') },
          { value: 'auto', label: t('settings.themeAuto') },
        ]"
        @update:modelValue="handleThemeChange"
      />
    </SettingsSection>

    <SettingsSection :title="t('settings.language')" :description="t('settings.languageDesc')">
      <SettingItem
        :label="t('settings.language')"
        :description="t('settings.languageDesc')"
        type="select"
        :modelValue="settings.language"
        :options="languageOptions"
        @update:modelValue="handleLanguageChange"
      />
    </SettingsSection>

    <SettingsSection :title="t('settings.notifications')" :description="t('settings.notificationsDesc')">
      <SettingItem
        :label="t('settings.notificationsLabel')"
        :description="t('settings.notificationsDesc')"
        type="checkbox"
        v-model="settings.notifications"
      />
    </SettingsSection>

    <SettingsSection :title="t('settings.llm')" :description="t('settings.defaultProviderDesc')">
      <SettingItem
        :label="t('settings.defaultProviderLabel')"
        :description="t('settings.defaultProviderDesc')"
        type="select"
        v-model="settings.defaultLLMProvider"
        :options="llmProviderOptions"
      />
      <SettingItem
        :label="t('settings.defaultModelLabel')"
        :description="t('settings.defaultModelDesc')"
        type="select"
        v-model="settings.defaultLLMModel"
        :options="llmModelOptions"
      />
    </SettingsSection>

    <div class="settings-actions">
      <button class="btn btn-secondary" @click="resetSettings">
        {{ t('common.cancel') }}
      </button>
      <button class="btn btn-primary" @click="updateSettings(settings)">
        {{ t('common.save') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.settings-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
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

.btn-primary:hover {
  background: var(--primary-color-dark);
}

.btn-secondary {
  background: var(--surface-color);
  color: var(--text-primary);
  border-color: var(--border-color);
}

.btn-secondary:hover {
  background: var(--hover-color);
}
</style>
