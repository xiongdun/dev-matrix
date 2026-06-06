<template>
  <div class="user-detail-page">
    <div class="dashboard-header">
      <div class="header-left">
        <button class="btn-back" @click="router.push('/users')">
          <ArrowLeft :size="16" />
          {{ t("common.back") }}
        </button>
        <div>
          <h1>{{ td("title") }}</h1>
          <p v-if="user">{{ user.username }} · {{ user.nickname || '—' }}</p>
        </div>
      </div>
    </div>

    <div v-if="loading" class="empty-state">{{ td("loading") }}</div>
    <div v-else-if="error" class="empty-state" style="color: var(--accent-red)">{{ error }}</div>

    <template v-else-if="user">
      <!-- 用户基本信息 -->
      <div class="section">
        <h2 class="section-title">{{ td("basicInfo") }}</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">{{ td("username") }}</span>
            <span class="info-value">{{ user.username }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ td("nickname") }}</span>
            <span class="info-value">{{ user.nickname || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ td("email") }}</span>
            <span class="info-value">{{ user.email || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ td("status") }}</span>
            <span class="user-status" :class="user.status">{{ statusLabel(user.status) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ td("roles") }}</span>
            <div>
              <span v-for="role in user.roles" :key="role.id" class="role-badge">{{ role.display_name }}</span>
            </div>
          </div>
          <div class="info-item">
            <span class="info-label">{{ td("createdAt") }}</span>
            <span class="info-value">{{ formatDate(user.created_at) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ td("lastLogin") }}</span>
            <span class="info-value">{{ user.last_login_at ? formatDate(user.last_login_at) : '—' }}</span>
          </div>
        </div>
      </div>

      <!-- Soul -->
      <div class="section" v-if="workspace.soul">
        <h2 class="section-title">{{ td("soulTitle") }}</h2>
        <div class="markdown-body" v-html="renderMarkdown(workspace.soul)"></div>
      </div>

      <!-- Profile -->
      <div class="section" v-if="workspace.profile && Object.keys(workspace.profile).length">
        <h2 class="section-title">{{ td("preferencesTitle") }}</h2>
        <div class="info-grid">
          <template v-for="(val, key) in workspace.profile" :key="key">
            <div v-if="typeof val === 'string'" class="info-item">
              <span class="info-label">{{ key }}</span>
              <span class="info-value">{{ val }}</span>
            </div>
            <div v-else-if="typeof val === 'object'" class="info-item info-item--full">
              <span class="info-label">{{ key }}</span>
              <div class="info-table">
                <div v-for="(v, k) in val" :key="k" class="info-table-row">
                  <span class="info-table-key">{{ k }}</span>
                  <span class="info-table-val">{{ v }}</span>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- Memories -->
      <div class="section" v-if="workspace.memories?.length">
        <h2 class="section-title">{{ td("memoriesCount", { count: workspace.memories.length }) }}</h2>
        <div class="memory-list">
          <div v-for="(mem, idx) in workspace.memories" :key="idx" class="memory-item">
            <div class="memory-header">
              <span class="memory-type">{{ mem.type }}</span>
              <span class="memory-key">{{ mem.key }}</span>
            </div>
            <div class="memory-value">{{ mem.value }}</div>
            <div class="memory-meta">
              <span v-if="mem.source">{{ td("source") }}: {{ mem.source }}</span>
              <span v-if="mem.confidence">{{ td("confidence") }}: {{ mem.confidence }}</span>
              <span v-if="mem.created_at">{{ mem.created_at }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Skills -->
      <div class="section" v-if="workspace.skills?.length">
        <h2 class="section-title">{{ td("skillsCount", { count: workspace.skills.length }) }}</h2>
        <div class="skill-list">
          <div v-for="skill in workspace.skills" :key="skill.name" class="skill-card">
            <div class="skill-name">{{ skill.name }}</div>
            <div class="skill-desc" v-if="skill.description">{{ skill.description }}</div>
            <div class="skill-triggers" v-if="skill.triggers?.length">
              <span class="skill-label">{{ td("trigger") }}：</span>
              <span v-for="t in skill.triggers" :key="t" class="skill-tag">{{ t }}</span>
            </div>
            <div class="skill-constraints" v-if="skill.constraints?.length">
              <span class="skill-label">{{ td("constraint") }}：</span>
              <span v-for="c in skill.constraints" :key="c" class="skill-tag constraint">{{ c }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- MCP Servers -->
      <div class="section" v-if="workspace.mcp_servers?.length">
        <h2 class="section-title">{{ td("mcpCount", { count: workspace.mcp_servers.length }) }}</h2>
        <div class="mcp-list">
          <div v-for="mcp in workspace.mcp_servers" :key="mcp.name" class="mcp-card">
            <div class="mcp-header">
              <span class="mcp-name">{{ mcp.name }}</span>
              <span class="mcp-type" v-if="mcp.类型">{{ mcp.类型 }}</span>
            </div>
            <div class="mcp-command" v-if="mcp.命令">
              <code>{{ mcp.命令 }}</code>
            </div>
            <div class="mcp-tools" v-if="mcp.tools?.length">
              <div v-for="tool in mcp.tools" :key="tool.name" class="mcp-tool">
                <span class="tool-name">{{ tool.name }}</span>
                <span class="tool-desc">{{ tool.description }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Projects -->
      <div class="section" v-if="Object.keys(workspace.projects || {}).length">
        <h2 class="section-title">{{ td("projectsCount", { count: Object.keys(workspace.projects).length }) }}</h2>
        <div class="project-list">
          <div v-for="(proj, pid) in workspace.projects" :key="pid" class="project-card">
            <div class="project-name">{{ pid }}</div>
            <div class="project-decisions" v-if="proj.decisions?.length">
              <div v-for="(d, i) in proj.decisions" :key="i" class="decision-item">
                <span class="decision-agent">{{ d.agent }}:</span>
                <span class="decision-text">{{ d.decision }}</span>
              </div>
            </div>
            <div class="project-feedback" v-if="proj.feedback?.length">
              <div v-for="(f, i) in proj.feedback" :key="i" class="feedback-item">
                💬 {{ f.content }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ArrowLeft } from 'lucide-vue-next'
import { marked } from 'marked'
import { api } from '../../api'

const { t } = useI18n()
const td = (key: string, params?: Record<string, any>) => t(`userDetail.${key}`, params || {})
const route = useRoute()
const router = useRouter()

const user = ref<any>(null)
const workspace = ref<any>({})
const loading = ref(true)
const error = ref('')

async function loadData() {
  const userId = route.params.id
  loading.value = true
  error.value = ''
  try {
    // 并行加载用户信息和 workspace
    const [userRes, wsRes] = await Promise.all([
      api.get(`/users/${userId}`),
      api.get(`/users/${userId}/workspace`).catch(() => ({})),
    ])
    user.value = userRes
    workspace.value = wsRes
  } catch (e: any) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

function renderMarkdown(content: string): string {
  return marked.parse(content || '', { breaks: true })
}

function statusLabel(status: string) {
  const map: Record<string, string> = { active: td('statusActive'), disabled: td('statusDisabled') }
  return map[status] || status
}

function formatDate(date: string) {
  if (!date) return '—'
  const d = new Date(date)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

onMounted(loadData)
</script>

<style scoped>
.user-detail-page {
  max-width: 960px;
}

.dashboard-header {
  margin-bottom: 1.5rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h1 {
  margin: 0;
  font-size: 1.5rem;
}

.header-left p {
  margin: 0.25rem 0 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-back:hover {
  color: var(--text-primary);
  border-color: var(--border-hover);
}

.section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 16px;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 信息网格 */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item--full {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 14px;
  color: var(--text-primary);
}

.user-status {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 9999px;
}

.user-status.active {
  background: rgba(34, 197, 94, 0.15);
  color: var(--accent-green);
}

.user-status.disabled {
  background: rgba(239, 68, 68, 0.15);
  color: var(--accent-red);
}

.role-badge {
  display: inline-block;
  margin-right: 6px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 9999px;
  background: rgba(99, 102, 241, 0.15);
  color: #6366f1;
}

.info-table {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-table-row {
  display: flex;
  gap: 12px;
  font-size: 13px;
}

.info-table-key {
  color: var(--text-muted);
  min-width: 80px;
}

.info-table-val {
  color: var(--text-primary);
}

/* Markdown 渲染 */
.markdown-body {
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-primary);
}

.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) {
  margin-top: 12px;
  margin-bottom: 6px;
  font-weight: 600;
}

.markdown-body :deep(p) { margin: 6px 0; }

.markdown-body :deep(ul), .markdown-body :deep(ol) {
  padding-left: 20px;
  margin: 6px 0;
}

.markdown-body :deep(code) {
  background: rgba(99, 102, 241, 0.08);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 0.9em;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 12px;
}

.markdown-body :deep(th), .markdown-body :deep(td) {
  border: 1px solid var(--border-color);
  padding: 6px 10px;
  text-align: left;
}

.markdown-body :deep(th) {
  background: var(--bg-tertiary);
  font-weight: 600;
}

/* 记忆列表 */
.memory-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.memory-item {
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
}

.memory-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.memory-type {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

.memory-key {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.memory-value {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.memory-meta {
  display: flex;
  gap: 12px;
  margin-top: 6px;
  font-size: 11px;
  color: var(--text-muted);
}

/* 技能列表 */
.skill-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.skill-card {
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
}

.skill-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.skill-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.skill-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-right: 4px;
}

.skill-tag {
  display: inline-block;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(99, 102, 241, 0.08);
  color: #6366f1;
  margin-right: 4px;
}

.skill-tag.constraint {
  background: rgba(234, 179, 8, 0.1);
  color: var(--accent-yellow);
}

/* MCP 列表 */
.mcp-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mcp-card {
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
}

.mcp-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.mcp-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.mcp-type {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.mcp-command {
  margin-bottom: 8px;
}

.mcp-command code {
  font-size: 12px;
  background: var(--bg-tertiary);
  padding: 4px 8px;
  border-radius: 4px;
  color: var(--text-secondary);
}

.mcp-tool {
  display: flex;
  gap: 8px;
  font-size: 12px;
  padding: 4px 0;
}

.tool-name {
  font-weight: 600;
  color: var(--text-primary);
  min-width: 120px;
}

.tool-desc {
  color: var(--text-secondary);
}

/* 项目列表 */
.project-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.project-card {
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
}

.project-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  font-family: 'SF Mono', Monaco, monospace;
}

.decision-item {
  font-size: 13px;
  padding: 4px 0;
}

.decision-agent {
  font-weight: 600;
  color: #6366f1;
}

.decision-text {
  color: var(--text-secondary);
}

.feedback-item {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 4px 0;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
}
</style>
