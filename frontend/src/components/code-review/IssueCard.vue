<template>
  <div class="issue-card" :class="`severity-${issue.severity}`">
    <div class="issue-header">
      <span class="severity-badge">{{ severityLabel }}</span>
      <span class="category-badge">{{ categoryLabel }}</span>
      <span v-if="issue.file" class="file-path">{{ issue.file }}:{{ issue.line ?? '?' }}</span>
    </div>
    <h4 class="issue-title">{{ issue.title }}</h4>
    <p class="issue-description">{{ issue.description }}</p>
    <div v-if="issue.suggestion" class="issue-suggestion">
      <div class="suggestion-label">修复建议</div>
      <pre class="suggestion-code">{{ issue.suggestion }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Issue {
  file: string
  line?: number | null
  severity: string
  category: string
  title: string
  description: string
  suggestion?: string
}

const props = defineProps<{
  issue: Issue
}>()

const severityLabel = computed(() => {
  const map: Record<string, string> = {
    must_fix: '必须修复',
    should_fix: '建议修复',
    nice_to_have: '可选优化',
  }
  return map[props.issue.severity] || props.issue.severity
})

const categoryLabel = computed(() => {
  const map: Record<string, string> = {
    security: '安全',
    performance: '性能',
    maintainability: '可维护性',
    style: '代码规范',
    testing: '测试',
    architecture: '架构',
  }
  return map[props.issue.category] || props.issue.category
})
</script>

<style scoped>
.issue-card {
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  border-left: 4px solid;
}
.issue-card.severity-must_fix {
  background: #fef2f2;
  border-left-color: #dc2626;
}
.issue-card.severity-should_fix {
  background: #fffbeb;
  border-left-color: #f59e0b;
}
.issue-card.severity-nice_to_have {
  background: #f0fdf4;
  border-left-color: #22c55e;
}
.issue-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.severity-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}
.severity-must_fix .severity-badge { background: #fecaca; color: #991b1b; }
.severity-should_fix .severity-badge { background: #fde68a; color: #92400e; }
.severity-nice_to_have .severity-badge { background: #bbf7d0; color: #166534; }
.category-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  background: #e5e7eb;
  color: #374151;
}
.file-path {
  font-size: 12px;
  color: #6b7280;
  font-family: monospace;
}
.issue-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #111827;
}
.issue-description {
  font-size: 14px;
  color: #4b5563;
  margin: 0 0 12px 0;
  line-height: 1.5;
}
.suggestion-label {
  font-size: 12px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 4px;
}
.suggestion-code {
  background: #1f2937;
  color: #e5e7eb;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  overflow-x: auto;
  margin: 0;
}
</style>
