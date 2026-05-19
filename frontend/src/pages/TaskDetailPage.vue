<template>
  <div class="task-detail-page">
    <!-- 左侧：任务列表边栏 -->
    <TaskSidebar :tasks="allTasks" :active-task-id="taskId" />

    <!-- 中间：主内容区 -->
    <div class="detail-main">
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

      <!-- 对话流内容区 -->
      <div class="chat-container">
        <div class="chat-messages" ref="messagesRef">
          <ChatMessage
            v-for="msg in messages"
            :key="msg.id"
            :message="msg"
          />
        </div>

        <!-- 底部输入框 -->
        <div class="chat-input-bar">
          <div class="chat-input-wrapper">
            <textarea
              v-model="inputMessage"
              rows="1"
              class="chat-input"
              :placeholder="t('workbench.inputPlaceholder')"
              @keydown.enter.prevent="sendMessage"
              @input="autoResize"
              ref="inputRef"
            />
            <button
              class="chat-send-btn"
              :disabled="!inputMessage.trim() || isSending"
              @click="sendMessage"
            >
              <Send :size="16" />
            </button>
          </div>
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

      <!-- 上下文面板 -->
      <TaskContextPanel v-if="task?.context" :context="task.context" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  ArrowLeft,
  CheckCircle,
  Undo2,
  RefreshCw,
  Send,
} from 'lucide-vue-next'
import { api } from '../api'
import { useDialog } from '../composables/useDialog'
import TaskSidebar from '../components/TaskSidebar.vue'
import TaskContextPanel from '../components/TaskContextPanel.vue'
import ChatMessage from '../components/ChatMessage.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { showConfirm } = useDialog()

interface TaskContext {
  skills: Array<{ name: string; description?: string }>
  files: Array<{ path: string; name?: string }>
  tools: Array<{ name: string; description?: string }>
  tokenUsage?: {
    percent: number
    used: number
    total: number
  }
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  previousContent?: string
  timestamp: string
}

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
  context?: TaskContext
  messages?: Message[]
}

const allMockTasks: Task[] = [
  {
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
    context: {
      skills: [
        { name: 'requirement_analysis', description: '需求分析技能' },
        { name: 'stakeholder_interview', description: '利益相关者访谈' },
      ],
      files: [
        { path: 'docs/requirements/v1.md', name: 'v1.md' },
        { path: 'docs/user_personas.md', name: 'user_personas.md' },
      ],
      tools: [
        { name: 'markdown_parser', description: 'Markdown解析器' },
        { name: 'sentiment_analysis', description: '情感分析' },
      ],
      tokenUsage: {
        percent: 32,
        used: 3200,
        total: 10000,
      },
    },
    messages: [
      {
        id: 'msg-1-1',
        role: 'assistant',
        content: '## 需求分析\n\n### 背景\n用户需要一个支持多角色协作的软件开发 Agent 操作系统。\n\n### 核心功能\n1. 需求输入与分析\n2. 多 Agent 协作流程\n3. 人工审批节点\n4. 自动化测试与部署\n\n### 用户画像\n- 技术负责人：关注架构设计和代码质量\n- 产品经理：关注需求完整性和 PRD 质量\n- 开发者：关注代码实现和测试覆盖',
        timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      },
    ],
  },
  {
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
    context: {
      skills: [
        { name: 'prd_writer', description: 'PRD撰写技能' },
        { name: 'user_story_generator', description: '用户故事生成' },
      ],
      files: [
        { path: 'docs/requirements/v1.md', name: 'v1.md' },
        { path: 'templates/prd_standard.md', name: 'prd_standard.md' },
      ],
      tools: [
        { name: 'jira_api', description: 'Jira API' },
        { name: 'figma_plugin', description: 'Figma插件' },
      ],
      tokenUsage: {
        percent: 48,
        used: 4800,
        total: 10000,
      },
    },
    messages: [
      {
        id: 'msg-2-1',
        role: 'assistant',
        content: '# PRD - 多角色协作开发平台\n\n## 1. 产品概述\n构建一个 AI 驱动的软件开发操作系统，支持 5 个专业角色协同工作。\n\n## 2. 用户故事\n- 作为产品经理，我希望输入需求后自动生成 PRD\n- 作为架构师，我希望分析代码影响范围\n- 作为开发者，我希望自动生成代码补丁\n\n## 3. 功能模块\n### 3.1 需求管理\n### 3.2 流程编排\n### 3.3 审批中心\n### 3.4 工作台',
        timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
      },
    ],
  },
  {
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
    context: {
      skills: [
        { name: 'code_search', description: '代码搜索技能' },
        { name: 'dependency_graph', description: '依赖关系分析' },
        { name: 'risk_assessor', description: '风险评估' },
      ],
      files: [
        { path: 'app/state/models.py', name: 'models.py' },
        { path: 'app/api/workflow_config.py', name: 'workflow_config.py' },
        { path: 'frontend/src/pages/WorkflowInstancePage.vue', name: 'WorkflowInstancePage.vue' },
        { path: 'alembic/versions/001_init.py', name: '001_init.py' },
      ],
      tools: [
        { name: 'ast_parser', description: 'AST解析器' },
        { name: 'git_diff', description: 'Git差异分析' },
      ],
      tokenUsage: {
        percent: 72,
        used: 7200,
        total: 10000,
      },
    },
    messages: [
      {
        id: 'msg-3-1',
        role: 'assistant',
        content: '## 影响分析\n\n### 变更范围\n- `app/state/models.py` - 新增 WorkflowInstanceModel\n- `app/api/workflow_config.py` - 模板管理 API\n- `frontend/src/pages/WorkflowInstancePage.vue` - 实例管理页面\n\n### 风险评估\n- 低风险：新增表结构，不影响现有数据\n- 中风险：API 变更需同步前端',
        timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
      },
      {
        id: 'msg-3-2',
        role: 'user',
        content: '请补充数据库迁移脚本的影响分析',
        timestamp: new Date(Date.now() - 1000 * 60 * 100).toISOString(),
      },
      {
        id: 'msg-3-3',
        role: 'assistant',
        content: '## 影响分析\n\n### 变更范围\n- `app/state/models.py` - 新增 WorkflowInstanceModel\n- `app/api/workflow_config.py` - 模板管理 API\n- `frontend/src/pages/WorkflowInstancePage.vue` - 实例管理页面\n- `alembic/versions/001_init.py` - 数据库迁移脚本\n\n### 风险评估\n- 低风险：新增表结构，不影响现有数据\n- 中风险：API 变更需同步前端\n- 低风险：迁移脚本使用 alembic，可回滚',
        previousContent: '## 影响分析\n\n### 变更范围\n- `app/state/models.py` - 新增 WorkflowInstanceModel\n- `app/api/workflow_config.py` - 模板管理 API\n- `frontend/src/pages/WorkflowInstancePage.vue` - 实例管理页面\n\n### 风险评估\n- 低风险：新增表结构，不影响现有数据\n- 中风险：API 变更需同步前端',
        timestamp: new Date(Date.now() - 1000 * 60 * 95).toISOString(),
      },
    ],
  },
  {
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
    context: {
      skills: [
        { name: 'code_generator', description: '代码生成技能' },
        { name: 'unit_test_writer', description: '单元测试编写' },
      ],
      files: [
        { path: 'app/state/models.py', name: 'models.py' },
        { path: 'app/state/repository.py', name: 'repository.py' },
        { path: 'tests/test_state.py', name: 'test_state.py' },
      ],
      tools: [
        { name: 'black', description: '代码格式化' },
        { name: 'mypy', description: '类型检查' },
        { name: 'pytest', description: '测试框架' },
      ],
      tokenUsage: {
        percent: 45,
        used: 4500,
        total: 10000,
      },
    },
    messages: [
      {
        id: 'msg-4-1',
        role: 'assistant',
        content: '```diff\n+ class WorkflowInstanceModel(Base):\n+     __tablename__ = "workflow_instances"\n+     id = Column(Integer, primary_key=True)\n+     instance_id = Column(String(32), unique=True)\n+     template_id = Column(Integer, nullable=True)\n```',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(),
      },
    ],
  },
  {
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
    context: {
      skills: [
        { name: 'code_search', description: '代码搜索技能' },
        { name: 'test_runner', description: '测试执行技能' },
      ],
      files: [
        { path: 'tests/integration/test_api.py', name: 'test_api.py' },
        { path: 'tests/unit/test_models.py', name: 'test_models.py' },
        { path: 'app/api/workflow.py', name: 'workflow.py' },
      ],
      tools: [
        { name: 'pytest', description: 'Python测试框架' },
        { name: 'coverage', description: '代码覆盖率工具' },
      ],
      tokenUsage: {
        percent: 56,
        used: 5600,
        total: 10000,
      },
    },
    messages: [
      {
        id: 'msg-5-1',
        role: 'assistant',
        content: '## 测试结果\n\n| 测试项 | 状态 | 耗时 |\n|--------|------|------|\n| unit_test | ✅ 通过 | 12s |\n| integration | ❌ 失败 | 45s |\n| e2e | ⏭️ 跳过 | - |',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
      },
      {
        id: 'msg-5-2',
        role: 'user',
        content: '修复集成测试中的 API 超时问题',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 4.5).toISOString(),
      },
      {
        id: 'msg-5-3',
        role: 'assistant',
        content: '## 测试结果\n\n| 测试项 | 状态 | 耗时 |\n|--------|------|------|\n| unit_test | ✅ 通过 | 12s |\n| integration | ✅ 通过 | 28s |\n| e2e | ⏭️ 跳过 | - |\n\n### 修复内容\n- 增加 API 超时时间从 5s 到 15s\n- 优化数据库连接池配置',
        previousContent: '## 测试结果\n\n| 测试项 | 状态 | 耗时 |\n|--------|------|------|\n| unit_test | ✅ 通过 | 12s |\n| integration | ❌ 失败 | 45s |\n| e2e | ⏭️ 跳过 | - |',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString(),
      },
    ],
  },
]

const allTasks = ref<Task[]>(allMockTasks)
const taskId = ref(0)
const task = ref<Task | null>(null)
const messages = ref<Message[]>([])
const inputMessage = ref('')
const isSending = ref(false)
const messagesRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)

function loadTask(id: number) {
  taskId.value = id
  task.value = allTasks.value.find((t) => t.id === id) || null
  messages.value = task.value?.messages || []
}

watch(
  () => route.params.id,
  (newId) => {
    const id = parseInt(newId as string, 10)
    loadTask(id)
  },
  { immediate: true }
)

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

function goBack() {
  router.push('/workbench')
}

function formatTime(dateStr: string | undefined) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function autoResize() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

async function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text || isSending.value) return

  // 添加用户消息
  const userMsg: Message = {
    id: `msg-${taskId.value}-${Date.now()}`,
    role: 'user',
    content: text,
    timestamp: new Date().toISOString(),
  }
  messages.value.push(userMsg)
  inputMessage.value = ''
  autoResize()
  scrollToBottom()

  // 模拟 AI 回复
  isSending.value = true
  await new Promise((resolve) => setTimeout(resolve, 1000))

  const lastAssistantMsg = messages.value
    .filter((m) => m.role === 'assistant')
    .pop()

  const aiMsg: Message = {
    id: `msg-${taskId.value}-${Date.now()}-ai`,
    role: 'assistant',
    content: text.includes('修复') || text.includes('修改')
      ? lastAssistantMsg
        ? lastAssistantMsg.content + '\n\n### 修改说明\n根据您的反馈已调整上述内容。'
        : '已根据您的反馈调整内容。'
      : '收到您的指令，正在处理中...',
    previousContent: lastAssistantMsg?.content,
    timestamp: new Date().toISOString(),
  }
  messages.value.push(aiMsg)
  isSending.value = false
  scrollToBottom()
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
  height: 100vh;
  overflow: hidden;
}

/* 中间主内容区 */
.detail-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
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

/* 对话流容器 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px;
}

/* 底部输入框 */
.chat-input-bar {
  padding: 12px 24px;
  background-color: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}

.chat-input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 8px 12px;
  transition: border-color 0.15s ease;
}

.chat-input-wrapper:focus-within {
  border-color: var(--accent-blue);
}

.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 13px;
  font-family: inherit;
  line-height: 1.5;
  resize: none;
  outline: none;
  max-height: 120px;
  min-height: 20px;
}

.chat-input::placeholder {
  color: var(--text-muted);
}

.chat-send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  border: none;
  background-color: var(--accent-blue);
  color: white;
  cursor: pointer;
  transition: opacity 0.15s ease;
  flex-shrink: 0;
}

.chat-send-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.chat-send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 右侧操作面板 */
.content-right {
  width: 320px;
  min-width: 280px;
  overflow-y: auto;
  padding: 20px;
  background-color: var(--bg-secondary);
  border-left: 1px solid var(--border-color);
  flex-shrink: 0;
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
