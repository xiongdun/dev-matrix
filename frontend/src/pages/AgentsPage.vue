<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>{{ t('agents.title') }}</h1>
        <p>{{ t('agents.subtitle') }}</p>
      </div>
    </div>

    <div v-if="loading" class="empty-state">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="empty-state" style="color: var(--accent-red)">
      {{ t('common.error') }}: {{ error }}
    </div>
    <div v-else class="agent-grid">
      <div v-for="agent in agents" :key="agent.name" class="agent-card">
        <div class="agent-card-header">
          <div class="agent-info">
            <h3 class="agent-name">{{ agent.name }}</h3>
            <span class="agent-status" :class="agent.status">{{ statusLabel(agent.status) }}</span>
          </div>
          <p class="agent-desc">{{ agent.description }}</p>
        </div>

        <div class="agent-skills">
          <div class="skills-header">
            <span class="skills-title">{{ t('agents.mountedSkills') }}</span>
            <span class="skills-count">{{ agent.skills.length }}</span>
          </div>
          <div v-if="agent.skills.length" class="skill-tags">
            <span v-for="skill in agent.skills" :key="skill" class="skill-tag">
              {{ skill }}
              <button class="skill-remove" @click="unmountSkill(agent.name, skill)" :title="t('agents.unmountTitle')">×</button>
            </span>
          </div>
          <div v-else class="skills-empty">{{ t('agents.noSkills') }}</div>
        </div>

        <div class="agent-actions">
          <select v-model="agent.selectedSkill" class="skill-select">
            <option value="">{{ t('agents.selectSkill') }}</option>
            <option v-for="s in availableSkillsFor(agent)" :key="s.name" :value="s.name">
              {{ s.name }}
            </option>
          </select>
          <button
            class="btn-primary"
            :disabled="!agent.selectedSkill"
            @click="mountSkill(agent.name, agent.selectedSkill)"
          >
            {{ t('agents.mount') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../api'

const { t } = useI18n()

interface Agent {
  name: string
  description: string
  status: string
  skills: string[]
  selectedSkill: string
}

interface Skill {
  name: string
  description: string
}

const agents = ref<Agent[]>([])
const allSkills = ref<Skill[]>([])
const loading = ref(true)
const error = ref('')

function statusLabel(status: string) {
  const map: Record<string, string> = {
    idle: t('agents.status.idle'),
    active: t('agents.status.active'),
    error: t('agents.status.error'),
  }
  return map[status] || status
}

function availableSkillsFor(agent: Agent) {
  return allSkills.value.filter(s => !agent.skills.includes(s.name))
}

async function fetchData() {
  loading.value = true
  error.value = ''
  try {
    const [agentsRes, skillsRes] = await Promise.all([
      api.getAgentDetails(),
      api.getSkills(),
    ])
    agents.value = (agentsRes.agents || []).map((a: any) => ({
      ...a,
      selectedSkill: '',
    }))
    allSkills.value = skillsRes.skills || []
  } catch (e: any) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

async function mountSkill(agentName: string, skillName: string) {
  if (!skillName) return
  try {
    await api.mountSkill(agentName, skillName)
    await fetchData()
  } catch (e: any) {
    alert(e.message || String(e))
  }
}

async function unmountSkill(agentName: string, skillName: string) {
  try {
    await api.unmountSkill(agentName, skillName)
    await fetchData()
  } catch (e: any) {
    alert(e.message || String(e))
  }
}

onMounted(fetchData)
</script>

<style scoped>
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}

.agent-card {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  transition: border-color 0.15s ease;
}

.agent-card:hover {
  border-color: var(--border-hover);
}

.agent-card-header {
  margin-bottom: 16px;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.agent-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.agent-status {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.agent-status.idle {
  background-color: rgba(161, 161, 170, 0.15);
  color: var(--text-secondary);
}

.agent-status.active {
  background-color: rgba(34, 197, 94, 0.15);
  color: var(--accent-green);
}

.agent-status.error {
  background-color: rgba(239, 68, 68, 0.15);
  color: var(--accent-red);
}

.agent-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.agent-skills {
  border-top: 1px solid var(--border-color);
  padding-top: 16px;
  margin-bottom: 16px;
}

.skills-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.skills-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.skills-count {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 9999px;
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skill-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.skill-remove {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  padding: 0 2px;
  margin-left: 2px;
}

.skill-remove:hover {
  color: var(--accent-red);
}

.skills-empty {
  font-size: 13px;
  color: var(--text-muted);
  font-style: italic;
}

.agent-actions {
  display: flex;
  gap: 8px;
  border-top: 1px solid var(--border-color);
  padding-top: 16px;
}

.skill-select {
  flex: 1;
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  padding: 8px 12px;
  font-size: 13px;
  outline: none;
}

.skill-select:focus {
  border-color: var(--accent-blue);
}

.skill-select option {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-primary {
  background-color: var(--accent-blue);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
