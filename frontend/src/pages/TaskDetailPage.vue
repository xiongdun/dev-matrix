<template>
  <div class="task-detail-page">
    <!-- 顶部导航栏 -->
    <div class="detail-topbar">
      <button class="btn-back" @click="goBack">
        <ArrowLeft :size="16" />
        {{ t('workbench.back') }}
      </button>
      <div class="topbar-title">
        <span class="topbar-project">{{ task?.project_id }}</span>
        <span class="topbar-separator">·</span>
        <span class="topbar-stage">{{ task?.stage_name }}</span>
      </div>
      <div class="topbar-meta">
        <span class="tag tag--role">{{ task?.agent_role }}</span>
        <span class="tag" :class="`tag--${task?.status}`">{{ statusLabel }}</span>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="detail-content">
      <!-- 左侧：产出物 -->
      <div class="content-left">
        <div class="content-section">
          <div class="section-header">
            <FileText :size="16" />
            <h3>{{ t('workbench.output') }}</h3>
          </div>
          <div class="output-panel">
            <pre>{{ formattedOutput }}</pre>
          </div>
        </div>

        <div v-if="task?.feedback" class="content-section">
          <div class="section-header">
            <MessageSquare :size="16" />
            <h3>{{ t('workbench.feedback') }}</h3>
          </div>
          <div class="feedback-panel">
            {{ task.feedback }}
          </div>
        </div>
      </div>

      <!-- 右侧：操作面板 -->
      <div class="content-right">
        <div class="action-panel">
          <h4>{{ t('workbench.actions') }}</h4>

          <button class="action-btn action-btn--approve" @click="handleApprove">
            <CheckCircle :size="18" />
            <div class="action-btn__text">
              <span class="action-btn__label">{{ t('workbench.approve') }}</span>
              <span class="action-btn__desc">{{ t('workbench.approveDesc') }}</span>
            </div>
          </button>

          <button class="action-btn action-btn--reject" @click="showReject = true; showRetry = false">
            <Undo2 :size="18" />
            <div class="action-btn__text">
              <span class="action-btn__label">{{ t('workbench.reject') }}</span>
              <span class="action-btn__desc">{{ t('workbench.rejectDesc') }}</span>
            </div>
          </button>

          <button class="action-btn action-btn--retry" @click="showRetry = true; showReject = false">
            <RefreshCw :size="18" />
            <div class="action-btn__text">
              <span class="action-btn__label">{{ t('workbench.retry') }}</span>
              <span class="action-btn__desc">{{ t('workbench.retryDesc') }}</span>
            </div>
          </button>
        </div>

        <!-- 拒绝输入 -->
        <div v-if="showReject" class="input-panel">
          <label>{{ t('workbench.rejectReason') }}</label>
          <textarea v-model="rejectComment" rows="5" :placeholder="t('workbench.rejectPlaceholder')" />
          <div class="input-actions">
            <button class="btn-submit" @click="handleReject">
              {{ t('workbench.submit') }}
            </button>
            <button class="btn-cancel" @click="showReject = false; rejectComment = ''">
              {{ t('workbench.cancel') }}
            </button>
          </div>
        </div>

        <!-- 重试输入 -->
        <div v-if="showRetry" class="input-panel">
          <label>{{ t('workbench.retryFeedback') }}</label>
          <textarea v-model="retryFeedback" rows="5" :placeholder="t('workbench.retryPlaceholder')" />
          <div class="input-actions">
            <button class="btn-submit" @click="handleRetry">
              {{ t('workbench.submit') }}
            </button>
            <button class="btn-cancel" @click="showRetry = false; retryFeedback = ''">
              {{ t('workbench.cancel') }}
            </button>
          </div>
        </div>

        <!-- 信息卡片 -->
        <div class="info-panel">
          <div class="info-item">
            <span class="info-label">{{ t('workbench.infoId') }}</span>
            <span class="info-value">#{{ task?.id }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('workbench.infoStage') }}</span>
            <span class="info-value">{{ task?.stage_id }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('workbench.infoArrived') }}</span>
            <span class="info-value">{{ formatTime(task?.arrived_at) }}</span>
          </div>
          <div v-if="task?.processed_at" class="info-item">
            <span class="info-label">{{ t('workbench.infoProcessed') }}</span>
            <span class="info-value">{{ formatTime(task?.processed_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  ArrowLeft,
  FileText,
  MessageSquare,
  CheckCircle,
  Undo2,
  RefreshCw,
} from 'lucide-vue-next'
import { api } from '../api'
import { useDialog } from '../composables/useDialog'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { showConfirm } = useDialog()

interface Task {
  id: number
  project_id: string
  stage_id: string
  stage_name: string
  agent_role: string
  status: string
  output_json: string
  feedback: string | null
  arrived_at: string
  processed_at: string | null
}

const mockTasks: Record<number, Task> = {
  1: {
    id: 1,
    project_id: 'dev-matrix-001',
    stage_id: 'analyze_requirement',
    stage_name: '需求分析',
    agent_role: 'business_analyst',
    status: 'pending',
    output_json: JSON.stringify({
      content: '## 需求分析\n\n### 背景\n用户需要一个支持多角色协作的软件开发 Agent 操作系统。\n\n### 核心功能\n1. 需求输入与分析\n2. 多 Agent 协作流程\n3. 人工审批节点\n4. 自动化测试与部署\n\n### 用户画像\n- 技术负责人：关注架构设计和代码质量\n- 产品经理：关注需求完整性和 PRD 质量\n- 开发者：关注代码实现和测试覆盖',
      metadata: { confidence: 0.92, tokens: 2048 }
    }, null, 2),
    feedback: null,
    arrived_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    processed_at: null,
  },
  2: {
    id: 2,
    project_id: 'dev-matrix-002',
    stage_id: 'generate_prd',
    stage_name: 'PRD 生成',
    agent_role: 'product_manager',
    status: 'pending',
    output_json: JSON.stringify({
      content: '# PRD - 多角色协作开发平台\n\n## 1. 产品概述\n构建一个 AI 驱动的软件开发操作系统，支持 5 个专业角色协同工作。\n\n## 2. 用户故事\n- 作为产品经理，我希望输入需求后自动生成 PRD\n- 作为架构师，我希望分析代码影响范围\n- 作为开发者，我希望自动生成代码补丁\n\n## 3. 功能模块\n### 3.1 需求管理\n### 3.2 流程编排\n### 3.3 审批中心\n### 3.4 工作台',
      metadata: { version: 'v1.0', pages: 12 }
    }, null, 2),
    feedback: null,
    arrived_at: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    processed_at: null,
  },
  3: {
    id: 3,
    project_id: 'dev-matrix-003',
    stage_id: 'analyze_code_impact',
    stage_name: '代码影响分析',
    agent_role: 'architect',
    status: 'retrying',
    output_json: JSON.stringify({
      content: '## 影响分析\n\n### 变更范围\n- `app/state/models.py` - 新增 WorkflowInstanceModel\n- `app/api/workflow_config.py` - 模板管理 API\n- `frontend/src/pages/WorkflowInstancePage.vue` - 实例管理页面\n\n### 风险评估\n- 低风险：新增表结构，不影响现有数据\n- 中风险：API 变更需同步前端',
      metadata: { files_changed: 3, risk_level: 'low' }
    }, null, 2),
    feedback: '请补充数据库迁移脚本的影响分析',
    arrived_at: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    processed_at: null,
  },
  4: {
    id: 4,
    project_id: 'dev-matrix-004',
    stage_id: 'generate_patch',
    stage_name: '补丁生成',
    agent_role: 'developer',
    status: 'approved',
    output_json: JSON.stringify({
      content: '```diff\n+ class WorkflowInstanceModel(Base):\n+     __tablename__ = "workflow_instances"\n+     id = Column(Integer, primary_key=True)\n+     instance_id = Column(String(32), unique=True)\n+     template_id = Column(Integer, nullable=True)\n```',
      metadata: { lines_added: 45, lines_removed: 0 }
    }, null, 2),
    feedback: null,
    arrived_at: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(),
    processed_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
  },
  5: {
    id: 5,
    project_id: 'hotfix-2026-001',
    stage_id: 'execute_tests',
    stage_name: '测试执行',
    agent_role: 'qa',
    status: 'rejected',
    output_json: JSON.stringify({
      content: '## 测试结果\n\n| 测试项 | 状态 | 耗时 |\n|--------|------|------|\n| unit_test | ✅ 通过 | 12s |\n| integration | ❌ 失败 | 45s |\n| e2e | ⏭️ 跳过 | - |',
      metadata: { total: 3, passed: 1, failed: 1, skipped: 1 }
    }, null, 2),
    feedback: '集成测试失败，请修复后再提交',
    arrived_at: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
    processed_at: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString(),
  },
}

const taskId = parseInt(route.params.id as string, 10)
const task = ref<Task | null>(mockTasks[taskId] || null)

const showReject = ref(false)
const showRetry = ref(false)
const rejectComment = ref('')
const retryFeedback = ref('')

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    pending: t('workbench.pending'),
    retrying: t('workbench.retry'),
    approved: t('workbench.approved'),
    rejected: t('workbench.rejected'),
    completed: t('workbench.completed'),
  }
  return map[task.value?.status || ''] || task.value?.status || ''
})

const formattedOutput = computed(() => {
  if (!task.value) return ''
  try {
    return JSON.stringify(JSON.parse(task.value.output_json), null, 2)
  } catch {
    return task.value.output_json
  }
})

function goBack() {
  router.push('/workbench')
}

function formatTime(dateStr: string | undefined) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

async function handleApprove() {
  try {
    await api.approveWorkbenchTask(task.value!.id)
    router.push('/workbench')
  } catch (e: any) {
    await showConfirm({
      title: t('common.error'),
      message: e.message || String(e),
      type: 'warning',
      showCancel: false,
      confirmText: t('common.confirm'),
    })
  }
}

async function handleReject() {
  try {
    await api.rejectWorkbenchTask(task.value!.id, rejectComment.value)
    router.push('/workbench')
  } catch (e: any) {
    await showConfirm({
      title: t('common.error'),
      message: e.message || String(e),
      type: 'warning',
      showCancel: false,
      confirmText: t('common.confirm'),
    })
  }
}

async function handleRetry() {
  try {
    await api.retryWorkbenchTask(task.value!.id, retryFeedback.value)
    router.push('/workbench')
  } catch (e: any) {
    await showConfirm({
      title: t('common.error'),
      message: e.message || String(e),
      type: 'warning',
      showCancel: false,
      confirmText: t('common.confirm'),
    })
  }
}
</script>

<style scoped>
.task-detail-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 64px - 40px);
  overflow: hidden;
}

/* 顶部导航栏 */
.detail-topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.btn-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-back:hover {
  border-color: var(--border-hover);
  color: var(--text-primary);
}

.topbar-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.topbar-project {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.topbar-separator {
  color: var(--text-muted);
}

.topbar-stage {
  font-size: 14px;
  color: var(--text-secondary);
}

.topbar-meta {
  display: flex;
  gap: 8px;
}

.tag {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tag--role {
  background-color: rgba(99, 102, 241, 0.12);
  color: #6366f1;
}

.tag--pending {
  background-color: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.tag--retrying {
  background-color: rgba(234, 179, 8, 0.15);
  color: var(--accent-yellow);
}

.tag--approved {
  background-color: rgba(34, 197, 94, 0.15);
  color: var(--accent-green);
}

.tag--rejected {
  background-color: rgba(239, 68, 68, 0.15);
  color: var(--accent-red);
}

.tag--completed {
  background-color: rgba(113, 113, 122, 0.15);
  color: var(--text-tertiary);
}

/* 主内容区 */
.detail-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 左侧产出物 */
.content-left {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  border-right: 1px solid var(--border-color);
}

.content-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.section-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.output-panel {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
  overflow-x: auto;
}

.output-panel pre {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.feedback-panel {
  background-color: rgba(234, 179, 8, 0.08);
  border: 1px solid rgba(234, 179, 8, 0.2);
  border-radius: var(--radius-lg);
  padding: 14px 16px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* 右侧操作面板 */
.content-right {
  width: 320px;
  min-width: 280px;
  overflow-y: auto;
  padding: 20px;
  background-color: var(--bg-secondary);
}

.action-panel h4 {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 12px 0;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: 8px;
  text-align: left;
}

.action-btn:hover {
  border-color: var(--border-hover);
}

.action-btn--approve:hover {
  border-color: var(--accent-green);
  background-color: rgba(34, 197, 94, 0.08);
}

.action-btn--reject:hover {
  border-color: var(--accent-yellow);
  background-color: rgba(234, 179, 8, 0.08);
}

.action-btn--retry:hover {
  border-color: var(--accent-blue);
  background-color: rgba(59, 130, 246, 0.08);
}

.action-btn__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.action-btn__label {
  font-size: 13px;
  font-weight: 600;
}

.action-btn__desc {
  font-size: 11px;
  color: var(--text-tertiary);
}

.input-panel {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 14px;
  margin-bottom: 16px;
}

.input-panel label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.input-panel textarea {
  width: 100%;
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  padding: 10px 12px;
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s ease;
  margin-bottom: 10px;
}

.input-panel textarea:focus {
  border-color: var(--accent-blue);
}

.input-actions {
  display: flex;
  gap: 8px;
}

.btn-submit {
  flex: 1;
  padding: 7px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--accent-blue);
  background-color: var(--accent-blue);
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.btn-submit:hover {
  opacity: 0.9;
}

.btn-cancel {
  padding: 7px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-cancel:hover {
  color: var(--text-primary);
  border-color: var(--border-hover);
}

.info-panel {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  font-size: 12px;
}

.info-label {
  color: var(--text-tertiary);
}

.info-value {
  color: var(--text-secondary);
  font-family: 'SF Mono', Monaco, monospace;
}
</style>
