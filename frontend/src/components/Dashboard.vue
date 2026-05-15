<!--
  @file 仪表盘组件
  @description 应用主仪表盘，展示统计数据、最近活动和任务列表
  @component Dashboard
  @emits
    - refresh: 用户请求刷新数据
  @slots
    - default: 主内容区

  @example
  ```vue
  <template>
    <Dashboard />
  </template>
  ```
-->

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import StatCard from './StatCard.vue'
import ActivityList from './ActivityList.vue'
import TaskList from './TaskList.vue'

/**
 * 国际化组合式函数
 * @returns {Object} i18n 实例
 */
const { t } = useI18n()

/**
 * 加载状态
 * @type {import('vue').Ref<boolean>}
 */
const loading = ref(false)

/**
 * 统计数据
 * @type {import('vue').Ref<Array<{label: string, value: number, icon: string}>>}
 */
const stats = ref([
  { label: t('dashboard.stats.totalAgents'), value: 0, icon: '🤖' },
  { label: t('dashboard.stats.activeSkills'), value: 0, icon: '🔧' },
  { label: t('dashboard.stats.pendingApprovals'), value: 0, icon: '⏳' },
  { label: t('dashboard.stats.completedWorkflows'), value: 0, icon: '✅' },
])

/**
 * 最近活动列表
 * @type {import('vue').Ref<Array<{id: string, type: string, message: string, timestamp: string}>>}
 */
const activities = ref([
  { id: '1', type: 'workflow', message: t('dashboard.mock.workflowCompleted'), timestamp: '2024-01-15T10:30:00Z' },
  { id: '2', type: 'approval', message: t('dashboard.mock.approvalRequired'), timestamp: '2024-01-15T09:15:00Z' },
  { id: '3', type: 'agent', message: t('dashboard.mock.agentProposal'), timestamp: '2024-01-15T08:45:00Z' },
])

/**
 * 任务列表
 * @type {import('vue').Ref<Array<{id: string, title: string, status: string, priority: string}>>}
 */
const tasks = ref([
  { id: '1', title: t('dashboard.mock.reviewPrd'), status: 'pending', priority: 'high' },
  { id: '2', title: t('dashboard.mock.mountSkill'), status: 'completed', priority: 'medium' },
  { id: '3', title: t('dashboard.mock.configureLlm'), status: 'in_progress', priority: 'low' },
])

/**
 * 加载仪表盘数据
 * @returns {Promise<void>}
 */
const loadDashboard = async () => {
  loading.value = true
  try {
    // 模拟 API 调用，实际应从后端获取
    await new Promise((resolve) => setTimeout(resolve, 500))
    stats.value = [
      { label: t('dashboard.stats.totalAgents'), value: 5, icon: '🤖' },
      { label: t('dashboard.stats.activeSkills'), value: 12, icon: '🔧' },
      { label: t('dashboard.stats.pendingApprovals'), value: 3, icon: '⏳' },
      { label: t('dashboard.stats.completedWorkflows'), value: 24, icon: '✅' },
    ]
  } finally {
    loading.value = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadDashboard()
})
</script>

<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <h2>{{ t('dashboard.title') }}</h2>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      {{ t('common.loading') }}
    </div>

    <!-- 统计数据卡片 -->
    <div v-else class="stats-grid">
      <StatCard
        v-for="stat in stats"
        :key="stat.label"
        :label="stat.label"
        :value="stat.value"
        :icon="stat.icon"
      />
    </div>

    <!-- 下方内容区：活动和任务 -->
    <div class="dashboard-content">
      <div class="section">
        <h3>{{ t('dashboard.recentActivity') }}</h3>
        <ActivityList :activities="activities" />
      </div>
      <div class="section">
        <h3>{{ t('dashboard.tasks') }}</h3>
        <TaskList :tasks="tasks" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 1rem 0;
}

.dashboard h2 {
  margin-bottom: 1.5rem;
  color: var(--text-primary);
}

.loading {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.dashboard-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.section {
  background: var(--surface-color);
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid var(--border-color);
}

.section h3 {
  margin-bottom: 1rem;
  color: var(--text-primary);
  font-size: 1.1rem;
}

@media (max-width: 768px) {
  .dashboard-content {
    grid-template-columns: 1fr;
  }
}
</style>
