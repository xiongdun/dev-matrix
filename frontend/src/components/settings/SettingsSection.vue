<template>
  <div class="panel settings-section">
    <div class="panel-header">
      <h2 class="panel-title">{{ title }}</h2>
      <p v-if="description" class="panel-description">{{ description }}</p>
    </div>
    <div class="panel-body">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<style scoped>
.settings-section {
  margin-bottom: 24px;
}

.panel-description {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}
</style>
