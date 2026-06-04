<template>
  <tr>
    <td :colspan="colspan" class="empty-row">
      <div class="empty-row-content">
        <slot>{{ message }}</slot>
      </div>
    </td>
  </tr>
</template>

<script setup lang="ts">
defineProps<{
  colspan: number
  message?: string
}>()
</script>

<style scoped>
.empty-row {
  padding: 0;
}

.empty-row-content {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  color: var(--text-tertiary);
  font-size: 14px;
}
</style>
