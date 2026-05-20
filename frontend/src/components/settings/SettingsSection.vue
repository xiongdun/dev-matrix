<script setup lang="ts">
interface Props {
  title: string
  description?: string
}

defineProps<Props>()
</script>

<template>
  <div class="settings-section">
    <div class="section-header">
      <h2 class="section-title">{{ title }}</h2>
      <p v-if="description" class="section-desc">{{ description }}</p>
    </div>
    <div class="section-body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.settings-section {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.section-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-color);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.25rem;
}

.section-desc {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin: 0;
}

.section-body {
  padding: 1rem 1.5rem;
}
</style>
