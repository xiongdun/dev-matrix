<template>
  <div class="code-review-list-page">
    <div class="page-header">
      <h1>代码审查</h1>
      <p class="page-desc">查看和管理代码审查记录</p>
    </div>

    <div class="filters">
      <select v-model="filterStatus" @change="loadReviews">
        <option value="">全部状态</option>
        <option value="completed">已完成</option>
        <option value="running">审查中</option>
        <option value="failed">失败</option>
      </select>
    </div>

    <div v-if="isLoading" class="loading">加载中...</div>
    <div v-else-if="reviews.length === 0" class="empty">
      <FileSearch :size="48" />
      <p>暂无代码审查记录</p>
    </div>
    <div v-else class="review-list">
      <div
        v-for="review in reviews"
        :key="review.id"
        class="review-item"
        @click="goToDetail(review.id)"
      >
        <div class="review-main">
          <div class="review-id">#{{ review.id }}</div>
          <div class="review-project">{{ review.project_id }}</div>
          <div class="review-status" :class="`status-${review.status}`">
            {{ statusLabel(review.status) }}
          </div>
        </div>
        <div class="review-meta">
          <ScoreBadge v-if="review.score != null" :score="review.score" />
          <span v-else class="no-score">-</span>
          <span class="review-time">{{ formatTime(review.created_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { FileSearch } from 'lucide-vue-next'
import { api } from '../api'
import ScoreBadge from '../components/code-review/ScoreBadge.vue'

const router = useRouter()

const reviews = ref<any[]>([])
const isLoading = ref(false)
const filterStatus = ref('')

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '等待中',
    running: '审查中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

function formatTime(time: string): string {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

async function loadReviews() {
  isLoading.value = true
  try {
    const params: any = { limit: 50 }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    const res = await api.listCodeReviews(params)
    reviews.value = res
  } catch (e) {
    console.error('Failed to load reviews:', e)
  } finally {
    isLoading.value = false
  }
}

function goToDetail(id: number) {
  router.push(`/code-reviews/${id}`)
}

onMounted(loadReviews)
</script>

<style scoped>
.code-review-list-page {
  padding: 24px;
}
.page-header {
  margin-bottom: 24px;
}
.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}
.page-desc {
  color: #6b7280;
  margin: 4px 0 0 0;
}
.filters {
  margin-bottom: 16px;
}
.filters select {
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  font-size: 14px;
}
.review-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.review-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.review-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}
.review-main {
  display: flex;
  align-items: center;
  gap: 16px;
}
.review-id {
  font-weight: 600;
  color: #111827;
}
.review-project {
  color: #6b7280;
  font-size: 14px;
}
.review-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}
.review-status.status-completed {
  background: #dcfce7;
  color: #166534;
}
.review-status.status-running {
  background: #dbeafe;
  color: #1e40af;
}
.review-status.status-failed {
  background: #fee2e2;
  color: #991b1b;
}
.review-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}
.no-score {
  color: #9ca3af;
  font-size: 14px;
}
.review-time {
  font-size: 12px;
  color: #9ca3af;
}
.loading,
.empty {
  text-align: center;
  padding: 60px;
  color: #6b7280;
}
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
</style>
