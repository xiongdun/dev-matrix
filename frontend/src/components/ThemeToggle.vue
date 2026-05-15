<!--
  @file 主题切换组件
  @description 切换应用主题模式（浅色/深色/自动）
  @component ThemeToggle
  @emits
    - change: 主题变化事件，参数为新模式
  @props
    - modelValue: 当前主题值

  @example
  ```vue
  <template>
    <ThemeToggle v-model="currentTheme" />
  </template>
  ```
-->

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

/**
 * 组件属性定义
 * @property {string} modelValue - 当前主题值
 */
const props = defineProps<{
  modelValue: string
}>()

/**
 * 组件事件定义
 * @emits update:modelValue - 更新主题值
 */
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

/**
 * 国际化组合式函数
 * @returns {Object} i18n 实例
 */
const { t } = useI18n()

/**
 * 当前主题的计算属性
 * @type {import('vue').ComputedRef<string>}
 */
const theme = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

/**
 * 可用的主题选项
 * @type {Array<{value: string, label: string, icon: string}>}
 */
const themes = [
  { value: 'light', label: t('settings.theme.light'), icon: '☀️' },
  { value: 'dark', label: t('settings.theme.dark'), icon: '🌙' },
  { value: 'auto', label: t('settings.theme.auto'), icon: '🔄' },
]

/**
 * 设置主题
 * @param {string} value - 主题值
 */
const setTheme = (value: string) => {
  theme.value = value
}
</script>

<template>
  <div class="theme-toggle">
    <!-- 遍历渲染主题选项按钮 -->
    <button
      v-for="t in themes"
      :key="t.value"
      :class="['theme-btn', { active: theme === t.value }]"
      @click="setTheme(t.value)"
      :title="t.label"
    >
      <span class="theme-icon">{{ t.icon }}</span>
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
  font-size: 1rem;
}

.theme-label {
  font-weight: 500;
}
</style>
