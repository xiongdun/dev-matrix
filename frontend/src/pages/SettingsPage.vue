<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>{{ t('settings.title') }}</h1>
      </div>
      <button
        class="theme-toggle"
        @click="saveSettings"
        :disabled="!isDirty"
        :style="{ opacity: isDirty ? 1 : 0.5 }"
      >
        {{ t('settings.save') }}
      </button>
    </div>

    <SettingsSection :title="t('settings.appearance.title')">
      <SettingItem
        :label="t('settings.appearance.theme')"
        type="select"
        v-model="form.appearance.theme"
        :options="themeOptions"
      />
      <SettingItem
        :label="t('settings.appearance.language')"
        type="select"
        v-model="form.appearance.language"
        :options="languageOptions"
      />
      <SettingItem
        :label="t('settings.appearance.sidebar')"
        type="select"
        v-model="sidebarCollapsedValue"
        :options="sidebarOptions"
      />
    </SettingsSection>

    <SettingsSection :title="t('settings.llm.title')">
      <SettingItem
        :label="t('settings.llm.provider')"
        type="select"
        v-model="form.llm.provider"
        :options="providerOptions"
      />
      <SettingItem
        :label="t('settings.llm.apiKey')"
        type="password"
        v-model="form.llm.apiKey"
        :placeholder="'sk-...'"
      />
      <SettingItem
        :label="t('settings.llm.model')"
        type="select"
        v-model="form.llm.model"
        :options="modelOptions"
      />
      <SettingItem
        :label="t('settings.llm.strategy')"
        type="select"
        v-model="form.llm.strategy"
        :options="strategyOptions"
      />
    </SettingsSection>

    <SettingsSection :title="t('settings.workflow.title')">
      <SettingItem
        :label="t('settings.workflow.approvalMode')"
        type="select"
        v-model="form.workflow.approvalMode"
        :options="approvalOptions"
      />
      <SettingItem
        :label="t('settings.workflow.timeout')"
        type="number"
        v-model="form.workflow.timeout"
        :min="5"
        :max="300"
      />
      <SettingItem
        :label="t('settings.workflow.retryCount')"
        type="number"
        v-model="form.workflow.retryCount"
        :min="0"
        :max="10"
      />
    </SettingsSection>

    <SettingsSection :title="t('settings.notifications.title')">
      <SettingItem
        :label="t('settings.notifications.workflowCompleted')"
        type="toggle"
        v-model="form.notifications.workflowCompleted"
      />
      <SettingItem
        :label="t('settings.notifications.approvalRequired')"
        type="toggle"
        v-model="form.notifications.approvalRequired"
      />
      <SettingItem
        :label="t('settings.notifications.agentFailed')"
        type="toggle"
        v-model="form.notifications.agentFailed"
      />
      <SettingItem
        :label="t('settings.notifications.webhookUrl')"
        type="text"
        v-model="form.notifications.webhookUrl"
        :placeholder="'https://...'"
      />
    </SettingsSection>

    <SettingsSection :title="t('settings.about.title')">
      <SettingItem
        :label="t('settings.about.version')"
        type="text"
        v-model="version"
        :disabled="true"
      />
      <SettingItem
        :label="t('settings.about.backend')"
        type="text"
        :model-value="backendStatus"
        :disabled="true"
      />
    </SettingsSection>

    <div v-if="showToast" class="toast">{{ t('settings.saved') }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SettingsSection from '../components/settings/SettingsSection.vue'
import SettingItem from '../components/settings/SettingItem.vue'
import { useSettings, settings as globalSettings } from '../composables/useSettings'

const { t, locale } = useI18n()
const { settings } = useSettings()

const form = reactive(JSON.parse(JSON.stringify(settings)))
const showToast = ref(false)
const version = ref('1.0.0')
const backendStatus = ref(t('settings.about.connected'))

const isDirty = computed(() => {
  return JSON.stringify(form) !== JSON.stringify(settings)
})

const sidebarCollapsedValue = computed({
  get: () => (form.appearance.sidebarCollapsed ? 'collapsed' : 'expanded'),
  set: (val: string) => {
    form.appearance.sidebarCollapsed = val === 'collapsed'
  },
})

const themeOptions = [
  { value: 'dark', label: t('settings.appearance.themeDark') },
  { value: 'light', label: t('settings.appearance.themeLight') },
]

const languageOptions = [
  { value: 'zh', label: '中文' },
  { value: 'en', label: 'English' },
]

const sidebarOptions = [
  { value: 'expanded', label: t('settings.appearance.sidebarExpanded') },
  { value: 'collapsed', label: t('settings.appearance.sidebarCollapsed') },
]

const providerOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
]

const modelOptions = [
  { value: 'gpt-4', label: 'GPT-4' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  { value: 'claude-3-opus', label: 'Claude 3 Opus' },
  { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
]

const strategyOptions = [
  { value: 'quality_first', label: t('settings.llm.strategyQuality') },
  { value: 'cost_first', label: t('settings.llm.strategyCost') },
  { value: 'config_driven', label: t('settings.llm.strategyConfig') },
]

const approvalOptions = [
  { value: 'manual', label: t('settings.workflow.approvalManual') },
  { value: 'auto', label: t('settings.workflow.approvalAuto') },
]

function saveSettings() {
  Object.assign(globalSettings, JSON.parse(JSON.stringify(form)))
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 2000)
}

// Apply theme immediately
watch(() => form.appearance.theme, (theme) => {
  document.documentElement.setAttribute('data-theme', theme)
})

// Apply language immediately
watch(() => form.appearance.language, (lang) => {
  locale.value = lang
  localStorage.setItem('devmatrix-language', lang)
})
</script>

<style scoped>
.toast {
  position: fixed;
  bottom: 32px;
  right: 32px;
  background-color: var(--accent-green);
  color: white;
  padding: 12px 20px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
