<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Sun, Moon, Monitor } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const { t } = useI18n()

const theme = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const themes = [
  { value: 'light', label: t('settings.theme.light'), icon: Sun },
  { value: 'dark', label: t('settings.theme.dark'), icon: Moon },
  { value: 'auto', label: t('settings.theme.auto'), icon: Monitor },
]

const setTheme = (value: string) => {
  theme.value = value
}
</script>

<template>
  <div class="theme-toggle">
    <button
      v-for="t in themes"
      :key="t.value"
      :class="['theme-btn', { active: theme === t.value }]"
      @click="setTheme(t.value)"
      :title="t.label"
    >
      <component :is="t.icon" class="theme-icon" :size="16" />
      <span class="theme-label">{{ t.label }}</span>
    </button>
  </div>
</template>

<style scoped>
.theme-toggle {
  display: flex;
  gap: 0.5rem;
  background: var(--surface-color);
  border-radius: 8px;
  padding: 0.25rem;
  border: 1px solid var(--border-color);
}

.theme-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s ease;
  font-size: 0.875rem;
}

.theme-btn:hover {
  background: var(--hover-color);
  color: var(--text-primary);
}

.theme-btn.active {
  background: var(--primary-color);
  color: white;
}

.theme-icon {
  flex-shrink: 0;
}

.theme-label {
  font-weight: 500;
}
</style>
