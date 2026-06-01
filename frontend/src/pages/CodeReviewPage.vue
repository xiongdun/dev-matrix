<template>
  <div class="code-review-page">
    <div class="page-header">
      <button class="btn-back" @click="goBack">
        <ArrowLeft :size="16" />
        返回
      </button>
      <h1>代码审查报告 #{{ reviewId }}</h1>
      <div class="header-actions">
        <button
          v-if="review?.status === 'failed' || review?.status === 'completed'"
          class="btn-rerun"
          @click="rerunReview"
          :disabled="isRerunning"
        >
          <RefreshCw :size="14" :class="{ spinning: isRerunning }" />
          {{ isRerunning ? '审查中...' : '重新审查' }}
        </button>
      </div>
    </div>

    <div v-if="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>加载审查报告中...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <AlertCircle :size="48" />
      <p>{{ error }}</p>
      <button class="btn-retry" @click="loadReview">重试</button>
    </div>

    <ReviewReport
      v-else-if="review"
      :report="reportData"
    />

    <div v-if="review?.raw_diff" class="raw-diff-section">
      <h3>审查代码</h3>
      <pre class="diff-content">{{ review.raw_diff }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, RefreshCw, AlertCircle } from 'lucide-vue-next'
import { api } from '../api'
import ReviewReport from '../components/code-review/ReviewReport.vue'

const route = useRoute()
const router = useRouter()

const reviewId = computed(() => Number(route.params.id))
const review = ref<any>(null)
const isLoading = ref(false)
const isRerunning = ref(false)
const error = ref('')

const reportData = computed(() => {
  if (!review.value) return null
  return {
    score: review.value.score,
    status: review.value.status,
    summary: review.value.summary,
    issues: review.value.issues_json ? JSON.parse(review.value.issues_json) : [],
    improvements: review.value.improvements_json ? JSON.parse(review.value.improvements_json) : [],
    duration_ms: review.value.duration_ms,
  }
})

async function loadReview() {
  isLoading.value = true
  error.value = ''
  try {
    const res = await api.getCodeReview(reviewId.value)
    review.value = res
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    isLoading.value = false
  }
}

async function rerunReview() {
  isRerunning.value = true
  try {
    const res = await api.rerunCodeReview(reviewId.value)
    review.value = res
  } catch (e: any) {
    error.value = e.message || '重新审查失败'
  } finally {
    isRerunning.value = false
  }
}

function goBack() {
  router.back()
}

onMounted(loadReview)
</script>

<style scoped>
.code-review-page {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  flex: 1;
}
.btn-back {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 14px;
}
.btn-back:hover {
  background: #f9fafb;
}
.btn-rerun {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #3b82f6;
  color: white;
  cursor: pointer;
  font-size: 14px;
}
.btn-rerun:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-rerun:hover:not(:disabled) {
  background: #2563eb;
}
.spinning {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  gap: 16px;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.btn-retry {
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}
.raw-diff-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}
.raw-diff-section h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px 0;
}
.diff-content {
  background: #1f2937;
  color: #e5e7eb;
  padding: 16px;
  border-radius: 8px;
  font-size: 13px;
  overflow-x: auto;
  line-height: 1.6;
}
</style>
