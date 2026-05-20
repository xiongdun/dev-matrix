<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../../api'
import SettingsSection from '../../components/settings/SettingsSection.vue'
import SettingItem from '../../components/settings/SettingItem.vue'

const { t } = useI18n()

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
    const res = await api.getSettings('security')
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
</script>

<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>{{ t('settings.securityTitle') }}</h1>
        <p>{{ t('settings.securitySubtitle') }}</p>
      </div>
    </div>

    <div v-if="isLoading" class="loading">{{ t('common.loading') }}...</div>

    <template v-else>
      <SettingsSection :title="t('settings.sessionSettings')" :description="t('settings.sessionSettingsDesc')">
        <SettingItem
          :label="t('settings.sessionTimeout')"
          :description="t('settings.sessionTimeoutDesc')"
          type="number"
          v-model="configs.session_timeout"
        />
        <SettingItem
          :label="t('settings.maxLoginAttempts')"
          :description="t('settings.maxLoginAttemptsDesc')"
          type="number"
          v-model="configs.max_login_attempts"
        />
      </SettingsSection>

      <div class="settings-actions">
        <span v-if="message" class="save-message success">{{ message }}</span>
        <span v-if="error" class="save-message error">{{ error }}</span>
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

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
