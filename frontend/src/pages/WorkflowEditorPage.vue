<template>
  <div class="workflow-editor" :class="{ fullscreen: isFullscreen }">
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <input
          v-model="workflowName"
          class="wf-name-input"
          :placeholder="t('workflow.namePlaceholder')"
        />
      </div>
      <div class="toolbar-right">
        <button class="toolbar-btn" @click="handleSave" :disabled="saving">
          {{ saving ? t('workflow.saving') : t('common.save') }}
        </button>
        <button class="toolbar-btn" @click="toggleFullscreen">
          {{ isFullscreen ? t('workflow.exitFullscreen') : t('workflow.fullscreen') }}
        </button>
      </div>
    </div>

    <div class="editor-body">
      <div class="agent-panel">
        <div class="panel-title">{{ t('workflow.agents') }}</div>
        <div v-if="agentsLoading" class="panel-hint">{{ t('common.loading') }}</div>
        <div v-else-if="agentsError" class="panel-hint" style="color: var(--accent-red)">{{ agentsError }}</div>
        <div v-else class="agent-list">
          <div
            v-for="agent in agents"
            :key="agent.name"
            class="agent-item"
            draggable="true"
            @dragstart="(e: DragEvent) => onDragStart(e, agent)"
          >
            <span class="agent-dot" :class="agent.status === 'active' ? 'dot-active' : 'dot-idle'"></span>
            <div class="agent-info">
              <div class="agent-name">{{ agent.name }}</div>
              <div class="agent-desc">{{ agent.description }}</div>
            </div>
          </div>
        </div>
      </div>

      <div
        class="canvas-area"
        @drop="onDrop"
        @dragover="onDragOver"
      >
        <VueFlow
          v-model:nodes="nodes"
          v-model:edges="edges"
          :default-viewport="{ zoom: 1, x: 0, y: 0 }"
          :min-zoom="0.2"
          :max-zoom="2"
          fit-view-on-init
          @connect="onConnect"
        >
          <template #node-agent="agentNodeProps">
            <div class="custom-agent-node">
              <div class="node-header">
                <span class="node-dot" :class="agentNodeProps.data.status === 'active' ? 'dot-active' : 'dot-idle'"></span>
                <span class="node-title">{{ agentNodeProps.data.label || agentNodeProps.data.name || agentNodeProps.id }}</span>
              </div>
              <div class="node-desc">{{ agentNodeProps.data.description || agentNodeProps.data.agent || '' }}</div>
              <Handle type="target" :position="Position.Left" />
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>
          <Background />
          <Controls />
          <MiniMap />
        </VueFlow>
      </div>
    </div>

    <div v-if="saveError" class="save-error">{{ saveError }}</div>
    <div v-if="saveSuccess" class="save-success">{{ t('workflow.saveSuccess') }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { VueFlow, useVueFlow, type Connection, type Node, type Edge, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { Handle } from '@vue-flow/core'
import { api } from '../api'
import { useTabs } from '../composables/useTabs'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

const { t } = useI18n()
const route = useRoute()
const { addTab } = useTabs()
const { project } = useVueFlow()

const workflowName = ref('')
const nodes = ref<Node[]>([])
const edges = ref<Edge[]>([])
const isFullscreen = ref(false)
const saving = ref(false)
const saveError = ref('')
const saveSuccess = ref(false)

const agents = ref<Array<{ name: string; description: string; status: string; skills: string[] }>>([])
const agentsLoading = ref(true)
const agentsError = ref('')

const workflowId = ref<number | null>(null)

async function loadAgents() {
  agentsLoading.value = true
  agentsError.value = ''
  try {
    const res = await api.getAgentDetails()
    agents.value = res.agents || []
  } catch (e: any) {
    agentsError.value = e.message || String(e)
  } finally {
    agentsLoading.value = false
  }
}

async function loadWorkflow(id: number) {
  try {
    const res = await api.getWorkflow(id)
    workflowId.value = res.id
    workflowName.value = res.name
    if (res.flow_json) {
      try {
        const flow = JSON.parse(res.flow_json)
        nodes.value = (flow.nodes || []).map((n: any) => ({
          ...n,
          type: n.type || 'agent',
          data: {
            ...n.data,
            label: n.data?.label || n.data?.name || n.id,
            description: n.data?.description || n.data?.agent || '',
            status: n.data?.status || 'idle',
          },
        }))
        edges.value = flow.edges || []
      } catch {
        // invalid flow_json, start empty
      }
    }
    addTab(`workflow-editor-${id}`, `${t('workflow.editor')} - ${res.name}`, `/workflow/editor/${id}`)
  } catch (e: any) {
    saveError.value = e.message || String(e)
  }
}

function onDragStart(e: DragEvent, agent: { name: string; description: string; status: string; skills: string[] }) {
  e.dataTransfer?.setData('application/vueflow', JSON.stringify(agent))
  e.dataTransfer!.effectAllowed = 'move'
}

function onDragOver(e: DragEvent) {
  e.preventDefault()
  e.dataTransfer!.dropEffect = 'move'
}

function onDrop(e: DragEvent) {
  const data = e.dataTransfer?.getData('application/vueflow')
  if (!data) return

  const agent = JSON.parse(data)
  const { left, top } = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const position = project({ x: e.clientX - left, y: e.clientY - top })

  const newNode: Node = {
    id: `${agent.name}-${Date.now()}`,
    type: 'agent',
    position,
    data: {
      label: agent.name,
      description: agent.description,
      status: agent.status,
    },
  }
  nodes.value = [...nodes.value, newNode]
}

function onConnect(connection: Connection) {
  const newEdge: Edge = {
    id: `e-${connection.source}-${connection.target}-${Date.now()}`,
    source: connection.source,
    target: connection.target,
    sourceHandle: connection.sourceHandle,
    targetHandle: connection.targetHandle,
    animated: true,
  }
  edges.value = [...edges.value, newEdge]
}

async function handleSave() {
  if (!workflowName.value.trim()) {
    saveError.value = t('workflow.nameRequired')
    return
  }

  saving.value = true
  saveError.value = ''
  saveSuccess.value = false

  try {
    const flowJson = JSON.stringify({ nodes: nodes.value, edges: edges.value })

    if (workflowId.value) {
      await api.saveWorkflow(workflowId.value, {
        name: workflowName.value,
        flow_json: flowJson,
      })
    } else {
      const created = await api.createWorkflow({ name: workflowName.value, flow_json: flowJson })
      workflowId.value = created.id
      addTab(`workflow-editor-${workflowId.value}`, `${t('workflow.editor')} - ${workflowName.value}`, `/workflow/editor/${workflowId.value}`)
    }

    saveSuccess.value = true
    setTimeout(() => { saveSuccess.value = false }, 2000)
  } catch (e: any) {
    saveError.value = e.message || String(e)
  } finally {
    saving.value = false
  }
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
}

onMounted(async () => {
  const id = route.params.id
  if (id) {
    await loadWorkflow(Number(id))
  } else {
    addTab('workflow-editor', t('workflow.newWorkflow'), '/workflow/editor')
  }
  await loadAgents()
})
</script>

<style scoped>
.workflow-editor {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 64px - 40px);
}

.workflow-editor.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  height: 100vh;
  background: var(--bg-primary);
}

.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
  gap: 12px;
}

.toolbar-left {
  flex: 1;
}

.wf-name-input {
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  padding: 6px 12px;
  font-size: 14px;
  font-weight: 600;
  outline: none;
  width: 280px;
  transition: border-color 0.15s ease;
}

.wf-name-input:focus {
  border-color: var(--accent-blue);
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.toolbar-btn {
  padding: 6px 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.toolbar-btn:hover:not(:disabled) {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.toolbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.editor-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.agent-panel {
  width: 220px;
  background-color: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.panel-title {
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}

.panel-hint {
  padding: 16px;
  font-size: 13px;
  color: var(--text-muted);
}

.agent-list {
  padding: 8px;
  overflow-y: auto;
}

.agent-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px;
  border-radius: var(--radius-sm);
  cursor: grab;
  transition: background-color 0.15s ease;
}

.agent-item:hover {
  background-color: var(--bg-hover);
}

.agent-item:active {
  cursor: grabbing;
}

.agent-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
}

.dot-active {
  background-color: var(--accent-green);
}

.dot-idle {
  background-color: var(--text-muted);
}

.agent-info {
  min-width: 0;
}

.agent-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.agent-desc {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.canvas-area {
  flex: 1;
  background-color: var(--bg-primary);
}

.custom-agent-node {
  padding: 10px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
  min-width: 160px;
  position: relative;
  transition: all 0.2s ease;
}

.node-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.node-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.node-dot.dot-active {
  background-color: var(--accent-green);
}

.node-dot.dot-idle {
  background-color: var(--text-muted);
}

.node-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.node-desc {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.save-error {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 10px 16px;
  border-radius: var(--radius-md);
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
  font-size: 13px;
  z-index: 10000;
}

.save-success {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 10px 16px;
  border-radius: var(--radius-md);
  background-color: rgba(34, 197, 94, 0.1);
  color: var(--accent-green);
  font-size: 13px;
  z-index: 10000;
}
</style>
