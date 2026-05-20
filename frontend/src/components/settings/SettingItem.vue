<script setup lang="ts">
import { computed } from 'vue'

interface Option {
  value: string
  label: string
}

interface Props {
  label: string
  description?: string
  type: 'text' | 'number' | 'select' | 'checkbox' | 'password'
  modelValue?: any
  options?: Option[]
  placeholder?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: any): void
}>()

const value = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})
</script>

<template>
  <div class="setting-item">
    <div class="setting-info">
      <label class="setting-label">{{ label }}</label>
      <p v-if="description" class="setting-desc">{{ description }}</p>
    </div>
    <div class="setting-control">
      <select
        v-if="type === 'select'"
        v-model="value"
        class="setting-select"
      >
        <option v-for="opt in options" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
      <input
        v-else-if="type === 'checkbox'"
        type="checkbox"
        v-model="value"
        class="setting-checkbox"
      />
      <input
        v-else-if="type === 'password'"
        type="password"
        v-model="value"
        class="setting-input"
        :placeholder="placeholder || ''"
      />
      <input
        v-else-if="type === 'number'"
        type="number"
        v-model.number="value"
        class="setting-input"
        :placeholder="placeholder || ''"
      />
      <input
        v-else
        type="text"
        v-model="value"
        class="setting-input"
        :placeholder="placeholder || ''"
      />
    </div>
  </div>
</template>

<style scoped>
.setting-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
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
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  display: block;
  margin-bottom: 0.25rem;
}

.setting-desc {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.4;
}

.setting-control {
  flex-shrink: 0;
  min-width: 200px;
}

.setting-input,
.setting-select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-color);
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
  width: 1.25rem;
  height: 1.25rem;
  accent-color: var(--primary-color);
  cursor: pointer;
}
</style>
