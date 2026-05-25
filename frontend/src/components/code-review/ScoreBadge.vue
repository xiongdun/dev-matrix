<template>
  <div class="score-badge" :class="scoreClass">
    <span class="score-value">{{ score ?? '-' }}</span>
    <span class="score-label">{{ label }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  score?: number | null
}>()

const scoreClass = computed(() => {
  if (props.score == null) return 'unknown'
  if (props.score >= 80) return 'excellent'
  if (props.score >= 60) return 'good'
  if (props.score >= 40) return 'fair'
  return 'poor'
})

const label = computed(() => {
  if (props.score == null) return '未评分'
  if (props.score >= 80) return '优秀'
  if (props.score >= 60) return '良好'
  if (props.score >= 40) return '一般'
  return '需改进'
})
</script>

<style scoped>
.score-badge {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 20px;
  border-radius: 12px;
  min-width: 80px;
}
.score-badge.excellent { background: #dcfce7; color: #166534; }
.score-badge.good { background: #dbeafe; color: #1e40af; }
.score-badge.fair { background: #fef3c7; color: #92400e; }
.score-badge.poor { background: #fee2e2; color: #991b1b; }
.score-badge.unknown { background: #f3f4f6; color: #6b7280; }
.score-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}
.score-label {
  font-size: 12px;
  margin-top: 4px;
}
</style>
