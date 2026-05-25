<template>
  <div class="review-report">
    <div class="report-header">
      <ScoreBadge :score="report.score" />
      <div class="report-meta">
        <div class="meta-item">
          <span class="meta-label">状态</span>
          <span class="meta-value" :class="`status-${report.status}`">{{ statusLabel }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">问题数</span>
          <span class="meta-value">{{ totalIssues }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">耗时</span>
          <span class="meta-value">{{ report.duration_ms ? `${report.duration_ms}ms` : '-' }}</span>
        </div>
      </div>
    </div>

    <div v-if="report.summary" class="report-summary">
      <p>{{ report.summary }}</p>
    </div>

    <div class="issues-stats">
      <div class="stat-item must-fix">
        <span class="stat-count">{{ mustFixCount }}</span>
        <span class="stat-label">必须修复</span>
      </div>
      <div class="stat-item should-fix">
        <span class="stat-count">{{ shouldFixCount }}</span>
        <span class="stat-label">建议修复</span>
      </div>
      <div class="stat-item nice-to-have">
        <span class="stat-count">{{ niceToHaveCount }}</span>
        <span class="stat-label">可选优化</span>
      </div>
    </div>

    <div v-if="issues.length > 0" class="issues-section">
      <h3>审查问题</h3>
      <IssueCard
        v-for="(issue, index) in issues"
        :key="index"
        :issue="issue"
      />
    </div>

    <div v-if="improvements.length > 0" class="improvements-section">
      <h3>改进建议</h3>
      <div
        v-for="(item, index) in improvements"
        :key="index"
        class="improvement-item"
      >
        <span class="improvement-category">{{ item.category }}</span>
        <p>{{ item.suggestion }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ScoreBadge from './ScoreBadge.vue'
import IssueCard from './IssueCard.vue'

interface ReviewReportData {
  score?: number | null
  status: string
  summary?: string
  issues?: any[]
  improvements?: any[]
  duration_ms?: number
}

const props = defineProps<{
  report: ReviewReportData
}>()

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    pending: '等待中',
    running: '审查中',
    completed: '已完成',
    failed: '失败',
  }
  return map[props.report.status] || props.report.status
})

const issues = computed(() => props.report.issues || [])
const improvements = computed(() => props.report.improvements || [])

const totalIssues = computed(() => issues.value.length)
const mustFixCount = computed(() => issues.value.filter(i => i.severity === 'must_fix').length)
const shouldFixCount = computed(() => issues.value.filter(i => i.severity === 'should_fix').length)
const niceToHaveCount = computed(() => issues.value.filter(i => i.severity === 'nice_to_have').length)
</script>

<style scoped>
.review-report {
  padding: 20px;
}
.report-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
}
.report-meta {
  display: flex;
  gap: 20px;
}
.meta-item {
  display: flex;
  flex-direction: column;
}
.meta-label {
  font-size: 12px;
  color: #6b7280;
}
.meta-value {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}
.meta-value.status-pending { color: #6b7280; }
.meta-value.status-running { color: #3b82f6; }
.meta-value.status-completed { color: #22c55e; }
.meta-value.status-failed { color: #dc2626; }
.report-summary {
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}
.report-summary p {
  margin: 0;
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
}
.issues-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}
.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  border-radius: 8px;
}
.stat-item.must-fix { background: #fef2f2; }
.stat-item.should-fix { background: #fffbeb; }
.stat-item.nice-to-have { background: #f0fdf4; }
.stat-count {
  font-size: 28px;
  font-weight: 700;
}
.must-fix .stat-count { color: #dc2626; }
.should-fix .stat-count { color: #f59e0b; }
.nice-to-have .stat-count { color: #22c55e; }
.stat-label {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}
.issues-section h3,
.improvements-section h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: #111827;
}
.improvement-item {
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 8px;
}
.improvement-category {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
}
.improvement-item p {
  margin: 4px 0 0 0;
  font-size: 14px;
  color: #374151;
}
</style>
