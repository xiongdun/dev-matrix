<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSettings } from '../../composables/useSettings'
import SettingsSection from '../../components/settings/SettingsSection.vue'
import SettingItem from '../../components/settings/SettingItem.vue'

const { t, locale } = useI18n()
const { settings, updateSettings, refreshSettings, isLoading } = useSettings()

const saving = ref(false)
const message = ref('')

onMounted(() => {
  refreshSettings()
})

const handleLanguageChange = async (value: string) => {
  locale.value = value
  await updateSettings({ language: value })
}

const handleThemeChange = async (value: string) => {
  await updateSettings({ theme: value })
}

const handleNotificationsChange = async (value: boolean) => {
  await updateSettings({ notifications_enabled: String(value) })
}

const handleSave = async () => {
  saving.value = true
  message.value = ''
  try {
    await updateSettings({
      app_name: settings.value.app_name,
      auto_save_interval: String(settings.value.auto_save_interval),
    })
    message.value = t('settings.saveSuccess')
  } catch (e: any) {
    message.value = e.message || String(e)
  } finally {
    saving.value = false
    setTimeout(() => message.value = '', 3000)
  }
}
</script>

<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>{{ t('settings.systemTitle') }}</h1>
        <p>{{ t('settings.systemSubtitle') }}</p>
      </div>
    </div>

    <div v-if="isLoading" class="loading">{{ t('common.loading') }}...</div>

    <template v-else>
      <SettingsSection :title="t('settings.appearance')" :description="t('settings.appearanceDesc')">
        <SettingItem
          :label="t('settings.themeLabel')"
          :description="t('settings.themeDesc')"
          type="select"
          :modelValue="settings.theme"
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
          :options="[
            { value: 'zh', label: t('settings.languageZh') },
            { value: 'en', label: t('settings.languageEn') },
          ]"
          @update:modelValue="handleLanguageChange"
        />
      </SettingsSection>

      <SettingsSection :title="t('settings.notifications')" :description="t('settings.notificationsDesc')">
        <SettingItem
          :label="t('settings.notificationsLabel')"
          :description="t('settings.notificationsDesc')"
          type="checkbox"
          :modelValue="settings.notifications_enabled"
          @update:modelValue="handleNotificationsChange"
        />
      </SettingsSection>

      <SettingsSection :title="t('settings.general')" :description="t('settings.generalDesc')">
        <SettingItem
          :label="t('settings.appNameLabel')"
          :description="t('settings.appNameDesc')"
          type="text"
          v-model="settings.app_name"
        />
        <SettingItem
          :label="t('settings.autoSaveIntervalLabel')"
          :description="t('settings.autoSaveIntervalDesc')"
          type="number"
          v-model="settings.auto_save_interval"
        />
      </SettingsSection>

      <div class="settings-actions">
        <span v-if="message" class="save-message">{{ message }}</span>
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
  color: var(--accent-green);
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

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
