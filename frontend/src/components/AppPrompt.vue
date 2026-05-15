<script setup lang="ts">
import { ref, watch } from 'vue'
import AppModal from './AppModal.vue'

const props = withDefaults(defineProps<{
  visible: boolean
  title: string
  message?: string
  placeholder?: string
  defaultValue?: string
  confirmText?: string
  cancelText?: string
}>(), {
  message: '',
  placeholder: '',
  defaultValue: '',
  confirmText: '确认',
  cancelText: '取消',
})

const emit = defineEmits<{
  (e: 'confirm', value: string): void
  (e: 'cancel'): void
}>()

const inputValue = ref('')

watch(() => props.visible, (v) => {
  if (v) {
    inputValue.value = props.defaultValue
  }
})

function handleConfirm() {
  emit('confirm', inputValue.value)
}
</script>

<template>
  <AppModal :visible="visible" :title="title" width="400px" @close="emit('cancel')">
    <div class="prompt-content">
      <p v-if="message" class="prompt-message">{{ message }}</p>
      <input
        v-model="inputValue"
        type="text"
        class="prompt-input"
        :placeholder="placeholder"
        @keydown.enter="handleConfirm"
      />
    </div>
    <template #footer>
      <button class="btn btn--secondary" @click="emit('cancel')">
        {{ cancelText }}
      </button>
      <button class="btn btn--primary" @click="handleConfirm">
        {{ confirmText }}
      </button>
    </template>
  </AppModal>
</template>

<style scoped>
.prompt-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.prompt-message {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0;
}

.prompt-input {
  width: 100%;
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  padding: 10px 14px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s ease;
}

.prompt-input:focus {
  border-color: var(--accent-blue);
}

.btn {
  padding: 7px 18px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn--secondary:hover {
  border-color: var(--border-hover);
  color: var(--text-primary);
}

.btn--primary {
  background-color: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.btn--primary:hover {
  opacity: 0.9;
}
</style>
