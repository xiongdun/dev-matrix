<script setup lang="ts">
import { AlertTriangle, Info, CheckCircle } from 'lucide-vue-next'
import AppModal from './AppModal.vue'

export type ConfirmType = 'confirm' | 'warning' | 'info' | 'success'

const props = withDefaults(defineProps<{
  visible: boolean
  title: string
  message: string
  type?: ConfirmType
  confirmText?: string
  cancelText?: string
  showCancel?: boolean
}>(), {
  type: 'confirm',
  confirmText: '确认',
  cancelText: '取消',
  showCancel: true,
})

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

const iconMap: Record<ConfirmType, any> = {
  confirm: Info,
  warning: AlertTriangle,
  info: Info,
  success: CheckCircle,
}

const colorMap: Record<ConfirmType, string> = {
  confirm: 'var(--accent-blue)',
  warning: 'var(--accent-yellow)',
  info: 'var(--accent-blue)',
  success: 'var(--accent-green)',
}
</script>

<template>
  <AppModal :visible="visible" :title="title" width="400px" @close="emit('cancel')">
    <div class="confirm-content">
      <div class="confirm-icon" :style="{ color: colorMap[type] }">
        <component :is="iconMap[type]" :size="28" />
      </div>
      <p class="confirm-message">{{ message }}</p>
    </div>
    <template #footer>
      <button v-if="showCancel" class="btn btn--secondary" @click="emit('cancel')">
        {{ cancelText }}
      </button>
      <button
        class="btn"
        :class="`btn--${type}`"
        @click="emit('confirm')"
      >
        {{ confirmText }}
      </button>
    </template>
  </AppModal>
</template>

<style scoped>
.confirm-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
  padding: 8px 0;
}

.confirm-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: currentColor;
  opacity: 0.12;
}

.confirm-icon :deep(svg) {
  opacity: 1;
}

.confirm-message {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
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

.btn--confirm {
  background-color: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.btn--confirm:hover {
  opacity: 0.9;
}

.btn--warning {
  background-color: var(--accent-yellow);
  border-color: var(--accent-yellow);
  color: #18181b;
}

.btn--warning:hover {
  opacity: 0.9;
}

.btn--info {
  background-color: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.btn--info:hover {
  opacity: 0.9;
}

.btn--success {
  background-color: var(--accent-green);
  border-color: var(--accent-green);
  color: white;
}

.btn--success:hover {
  opacity: 0.9;
}
</style>
