<template>
  <div class="stat-card">
    <div class="stat-label">{{ label }}</div>
    <div class="stat-value">{{ value }}</div>
    <div v-if="change" class="stat-change">{{ change }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: number | string
  change?: string
}>()
</script>
