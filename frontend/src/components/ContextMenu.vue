<!--
  @file 右键菜单组件
  @description 自定义右键上下文菜单
  @component ContextMenu
  @props
    - items: 菜单项数组
    - position: 菜单位置 { x, y }
  @emits
    - close: 关闭菜单时触发

  @example
  ```vue
  <template>
    <ContextMenu
      :items="[{ label: '关闭', action: closeTab }]"
      :position="{ x: 100, y: 200 }"
      @close="hideMenu"
    />
  </template>
  ```
-->

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

interface MenuItem {
  label: string
  action: () => void
  disabled?: boolean
}

interface Props {
  items: MenuItem[]
  position: { x: number; y: number }
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const menuRef = ref<HTMLElement | null>(null)

const handleClickOutside = (event: MouseEvent) => {
  if (menuRef.value && !menuRef.value.contains(event.target as Node)) {
    emit('close')
  }
}

const handleItemClick = (item: MenuItem) => {
  if (!item.disabled) {
    item.action()
    emit('close')
  }
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div
    ref="menuRef"
    class="context-menu"
    :style="{ left: position.x + 'px', top: position.y + 'px' }"
  >
    <div
      v-for="(item, index) in items"
      :key="index"
      class="context-menu-item"
      :class="{ disabled: item.disabled }"
      @click="handleItemClick(item)"
    >
      {{ item.label }}
    </div>
  </div>
</template>

<style scoped>
.context-menu {
  position: fixed;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 4px 0;
  min-width: 120px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 1000;
}

.context-menu-item {
  padding: 8px 16px;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.context-menu-item:hover:not(.disabled) {
  background-color: var(--bg-hover);
}

.context-menu-item.disabled {
  color: var(--text-muted);
  cursor: not-allowed;
}
</style>
