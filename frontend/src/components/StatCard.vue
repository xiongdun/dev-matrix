<!--
  @file 统计卡片组件
  @description 展示单个统计数据的卡片组件
  @component StatCard
  @props
    - label: 统计项标签
    - value: 统计数值
    - icon: 图标字符
    - trend: 趋势百分比，可选

  @example
  ```vue
  <template>
    <StatCard label="Total Agents" :value="5" icon="🤖" :trend="12.5" />
  </template>
  ```
-->

<script setup lang="ts">
/**
 * 组件属性定义
 * @property {string} label - 统计项标签
 * @property {number} value - 统计数值
 * @property {string} icon - 图标字符
 * @property {number} [trend] - 趋势百分比
 */
interface Props {
  label: string
  value: number
  icon: string
  trend?: number
}

defineProps<Props>()
</script>

<template>
  <div class="stat-card">
    <!-- 图标 -->
    <div class="stat-icon">{{ icon }}</div>
    <div class="stat-content">
      <!-- 数值 -->
      <div class="stat-value">{{ value }}</div>
      <!-- 标签 -->
      <div class="stat-label">{{ label }}</div>
      <!-- 趋势指示器（可选） -->
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
  font-size: 2rem;
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
