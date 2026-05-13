<template>
  <div class="stat-card">
    <div class="stat-header">
      <div class="stat-label">{{ label }}</div>
      <div v-if="change" class="stat-change">{{ change }}</div>
    </div>
    <div class="stat-value">{{ value }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: number | string
  change?: string
}>()
</script>

<style scoped>
.stat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
</style>
