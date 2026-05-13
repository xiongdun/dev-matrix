<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>{{ t('dashboard.title') }}</h1>
        <p>{{ t('app.subtitle') }}</p>
      </div>
      <ThemeToggle />
    </div>

    <div class="stats-grid">
      <StatCard
        :label="t('dashboard.stats.activeAgents')"
        :value="stats.activeAgents"
        change="+2"
      />
      <StatCard
        :label="t('dashboard.stats.pendingApprovals')"
        :value="stats.pendingApprovals"
        change="+5"
      />
      <StatCard
        :label="t('dashboard.stats.completedTasks')"
        :value="stats.completedTasks"
        change="+12"
      />
      <StatCard
        :label="t('dashboard.stats.workflowRuns')"
        :value="stats.workflowRuns"
        change="+3"
      />
    </div>

    <div class="dashboard-grid">
      <div class="panel">
        <div class="panel-header">
          <h2 class="panel-title">{{ t('dashboard.recentActivity') }}</h2>
        </div>
        <ActivityList :activities="activities" />
      </div>

      <div class="panel">
        <div class="panel-header">
          <h2 class="panel-title">{{ t('dashboard.recentTasks') }}</h2>
        </div>
        <TaskList :tasks="tasks" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import StatCard from './StatCard.vue'
import ActivityList from './ActivityList.vue'
import TaskList from './TaskList.vue'
import ThemeToggle from './ThemeToggle.vue'
import { api } from '../api'

const { t } = useI18n()

const stats = ref({
  activeAgents: 5,
  pendingApprovals: 3,
  completedTasks: 42,
  workflowRuns: 8,
})

const activities = ref<Array<{
  id: string
  type: string
  title: string
  time: string
}>>([
  { id: '1', type: 'requirement_created', title: '用户认证模块需求分析', time: '10 分钟前' },
  { id: '2', type: 'workflow_started', title: '工作流 #128 已启动', time: '25 分钟前' },
  { id: '3', type: 'approval_submitted', title: '架构设计审批已提交', time: '1 小时前' },
  { id: '4', type: 'agent_action', title: 'Developer 智能体生成补丁', time: '2 小时前' },
  { id: '5', type: 'snapshot_created', title: '状态快照 v1.2.0 已创建', time: '3 小时前' },
])

const tasks = ref<Array<{
  id: string
  title: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'approved' | 'rejected'
  agent: string
  time: string
}>>([
  { id: '1', title: '需求分析: OAuth2 认证', status: 'completed', agent: 'Business Analyst', time: '2 小时前' },
  { id: '2', title: 'PRD 生成: 用户系统', status: 'approved', agent: 'Product Manager', time: '4 小时前' },
  { id: '3', title: '代码影响分析', status: 'running', agent: 'Architect', time: '10 分钟前' },
  { id: '4', title: '测试用例生成', status: 'pending', agent: 'QA Agent', time: '等待中' },
])

onMounted(async () => {
  try {
    const health = await api.getHealth()
    console.log('Backend health:', health.status)
  } catch (e) {
    console.warn('Backend not available')
  }
})
</script>
