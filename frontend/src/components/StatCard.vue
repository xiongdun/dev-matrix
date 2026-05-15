<script setup lang="ts">
interface Props {
  label: string
  value: number
  icon: any
  trend?: number
}

defineProps<Props>()
</script>

<template>
  <div class="stat-card">
    <div class="stat-icon">
      <component :is="icon" :size="28" />
    </div>
    <div class="stat-content">
      <div class="stat-value">{{ value }}</div>
      <div class="stat-label">{{ label }}</div>
      <div v-if="trend !== undefined" class="stat-trend" :class="{ positive: trend > 0, negative: trend < 0 }">
        {{ trend > 0 ? '+' : '' }}{{ trend }}%
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  background: var(--surface-color);
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.2s ease;
}

.stat-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.stat-trend {
  font-size: 0.75rem;
  font-weight: 600;
  margin-top: 0.25rem;
}

.stat-trend.positive {
  color: #22c55e;
}

.stat-trend.negative {
  color: #ef4444;
}
</style>
