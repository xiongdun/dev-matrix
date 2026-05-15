<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import StatCard from './StatCard.vue'
import ActivityList from './ActivityList.vue'
import TaskList from './TaskList.vue'
import { api } from '../api'
import { Bot, Wrench, Hourglass, CheckCircle } from 'lucide-vue-next'

const { t } = useI18n()

const loading = ref(false)

const stats = ref([
  { label: t('dashboard.stats.totalAgents'), value: 0, icon: Bot },
  { label: t('dashboard.stats.activeSkills'), value: 0, icon: Wrench },
  { label: t('dashboard.stats.pendingApprovals'), value: 0, icon: Hourglass },
  { label: t('dashboard.stats.completedWorkflows'), value: 0, icon: CheckCircle },
])

const now = new Date().toISOString()

const activities = ref([
  { id: '1', type: 'workflow', message: t('dashboard.mock.workflowCompleted'), timestamp: now },
  { id: '2', type: 'approval', message: t('dashboard.mock.approvalRequired'), timestamp: now },
  { id: '3', type: 'agent', message: t('dashboard.mock.agentProposal'), timestamp: now },
])

const tasks = ref([
  { id: '1', title: t('dashboard.mock.reviewPrd'), status: 'pending', priority: 'high' },
  { id: '2', title: t('dashboard.mock.mountSkill'), status: 'completed', priority: 'medium' },
  { id: '3', title: t('dashboard.mock.configureLlm'), status: 'in_progress', priority: 'low' },
])

const loadDashboard = async () => {
  loading.value = true
  try {
    const [agentRes, skillRes, statsRes] = await Promise.allSettled([
      api.getAgentDetails(),
      api.getSkills(),
      api.getWorkbenchStats(''),
    ])
    const agentCount = agentRes.status === 'fulfilled' ? (agentRes.value.agents?.length ?? 0) : 0
    const skillCount = skillRes.status === 'fulfilled' ? (skillRes.value.skills?.length ?? 0) : 0
    const pendingCount = statsRes.status === 'fulfilled' ? (statsRes.value.pending ?? 0) : 0
    stats.value = [
      { label: t('dashboard.stats.totalAgents'), value: agentCount, icon: Bot },
      { label: t('dashboard.stats.activeSkills'), value: skillCount, icon: Wrench },
      { label: t('dashboard.stats.pendingApprovals'), value: pendingCount, icon: Hourglass },
      { label: t('dashboard.stats.completedWorkflows'), value: 0, icon: CheckCircle },
    ]
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<template>
  <div class="dashboard">
    <h2>{{ t('dashboard.title') }}</h2>

    <div v-if="loading" class="loading">
      {{ t('common.loading') }}
    </div>

    <div v-else class="stats-grid">
      <StatCard
        v-for="stat in stats"
        :key="stat.label"
        :label="stat.label"
        :value="stat.value"
        :icon="stat.icon"
      />
    </div>

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
