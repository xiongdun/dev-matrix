<!--
  @file 设置项组件
  @description 单个设置项的表单控件，支持多种输入类型
  @component SettingItem
  @props
    - label: 设置项标签
    - description: 设置项描述
    - type: 输入类型 (text/select/checkbox/number)
    - modelValue: 当前值
    - options: 选项列表（select 类型使用）
  @emits
    - update:modelValue: 值变化事件

  @example
  ```vue
  <template>
    <SettingItem
      label="Theme"
      description="Choose your preferred theme"
      type="select"
      v-model="theme"
      :options="[{value: 'light', label: 'Light'}]"
    />
  </template>
  ```
-->

<script setup lang="ts">
/**
 * 选项接口
 * @interface Option
 */
interface Option {
  /** 选项值 */
  value: string
  /** 选项标签 */
  label: string
}

/**
 * 组件属性定义
 * @property {string} label - 设置项标签
 * @property {string} [description] - 设置项描述
 * @property {string} type - 输入类型
 * @property {string|number|boolean} modelValue - 当前值
 * @property {Option[]} [options] - 选项列表
 */
interface Props {
  label: string
  description?: string
  type: 'text' | 'select' | 'checkbox' | 'number'
  modelValue: string | number | boolean
  options?: Option[]
}

const props = defineProps<Props>()

/**
 * 组件事件定义
 * @emits update:modelValue - 值变化事件
 */
const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number | boolean): void
}>()

/**
 * 处理输入变化
 * @param {Event} event - 输入事件
 */
const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement | HTMLSelectElement
  let value: string | number | boolean

  if (props.type === 'checkbox') {
    value = (target as HTMLInputElement).checked
  } else if (props.type === 'number') {
    value = Number(target.value)
  } else {
    value = target.value
  }

  emit('update:modelValue', value)
}
</script>

<template>
  <div class="setting-item">
    <div class="setting-info">
      <!-- 设置项标签 -->
      <label class="setting-label">{{ label }}</label>
      <!-- 设置项描述 -->
      <p v-if="description" class="setting-description">{{ description }}</p>
    </div>
    <div class="setting-control">
      <!-- 文本输入 -->
      <input
        v-if="type === 'text'"
        type="text"
        :value="modelValue"
        @input="handleInput"
        class="setting-input"
      />
      <!-- 数字输入 -->
      <input
        v-else-if="type === 'number'"
        type="number"
        :value="modelValue"
        @input="handleInput"
        class="setting-input"
      />
      <!-- 下拉选择 -->
      <select
        v-else-if="type === 'select'"
        :value="modelValue"
        @change="handleInput"
        class="setting-select"
      >
        <option
          v-for="option in options"
          :key="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </option>
      </select>
      <!-- 复选框 -->
      <input
        v-else-if="type === 'checkbox'"
        type="checkbox"
        :checked="modelValue"
        @change="handleInput"
        class="setting-checkbox"
      />
    </div>
  </div>
</template>

<style scoped>
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1rem 0;
  border-bottom: 1px solid var(--border-color);
  gap: 1rem;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-info {
  flex: 1;
  min-width: 0;
}

.setting-label {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.875rem;
}

.setting-description {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.setting-control {
  flex-shrink: 0;
  min-width: 120px;
}

.setting-input,
.setting-select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--background-color);
  color: var(--text-primary);
  font-size: 0.875rem;
  transition: border-color 0.2s ease;
}

.setting-input:focus,
.setting-select:focus {
  outline: none;
  border-color: var(--primary-color);
}

.setting-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--primary-color);
}
</style>
