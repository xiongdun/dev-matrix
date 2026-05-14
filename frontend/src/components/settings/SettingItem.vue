<template>
  <div class="setting-item">
    <div class="setting-label">
      <label>{{ label }}</label>
      <p v-if="description" class="setting-description">{{ description }}</p>
    </div>
    <div class="setting-control">
      <select
        v-if="type === 'select'"
        :value="modelValue"
        @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
        class="setting-select"
      >
        <option v-for="opt in options" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>

      <input
        v-else-if="type === 'text' || type === 'password'"
        :type="type"
        :value="modelValue"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        class="setting-input"
        :placeholder="placeholder"
      />

      <input
        v-else-if="type === 'number'"
        type="number"
        :value="modelValue"
        @input="$emit('update:modelValue', Number(($event.target as HTMLInputElement).value))"
        class="setting-input"
        :min="min"
        :max="max"
      />

      <label v-else-if="type === 'toggle'" class="setting-toggle">
        <input
          type="checkbox"
          :checked="modelValue"
          @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
        />
        <span class="toggle-slider"></span>
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Option {
  value: string
  label: string
}

defineProps<{
  label: string
  type: 'select' | 'text' | 'password' | 'number' | 'toggle'
  modelValue: any
  description?: string
  options?: Option[]
  placeholder?: string
  min?: number
  max?: number
}>()

defineEmits<{
  'update:modelValue': [value: any]
}>()
</script>

<style scoped>
.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  flex: 1;
}

.setting-label label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.setting-description {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.setting-control {
  flex-shrink: 0;
  margin-left: 24px;
}

.setting-select,
.setting-input {
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  padding: 8px 12px;
  font-size: 14px;
  min-width: 200px;
  outline: none;
  transition: border-color 0.15s ease;
}

.setting-select:focus,
.setting-input:focus {
  border-color: var(--accent-blue);
}

.setting-select option {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

/* Toggle Switch */
.setting-toggle {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  cursor: pointer;
}

.setting-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--bg-tertiary);
  border-radius: 24px;
  transition: background-color 0.2s ease;
  border: 1px solid var(--border-color);
}

.toggle-slider::before {
  content: '';
  position: absolute;
  height: 18px;
  width: 18px;
  left: 2px;
  bottom: 2px;
  background-color: var(--text-primary);
  border-radius: 50%;
  transition: transform 0.2s ease;
}

.setting-toggle input:checked + .toggle-slider {
  background-color: var(--accent-blue);
  border-color: var(--accent-blue);
}

.setting-toggle input:checked + .toggle-slider::before {
  transform: translateX(20px);
}
</style>
