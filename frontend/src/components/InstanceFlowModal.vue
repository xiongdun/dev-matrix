<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { VueFlow, type Node, type Edge, Position, Handle } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { X, GitBranch } from 'lucide-vue-next'
import { api } from '../api'
import { useAgentI18n } from '../composables/useAgentI18n'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'

interface Props {
  visible: boolean
  instanceId: string
  templateId: number | null
  currentState: string
  instanceStatus: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
}>()

const { t } = useI18n()
const { getAgentDisplayName, getAgentDescription } = useAgentI18n()

const nodes = ref<Node[]>([])
const edges = ref<Edge[]>([])
const loading = ref(false)
const error = ref('')
const templateName = ref('')

const currentNodeId = computed(() => {
  const state = props.currentState.toLowerCase().replace(/_review$/, '')
  const node = nodes.value.find(n => {
    const nodeId = (n.id || '').toLowerCase()
    const nodeName = ((n.data?.name || n.data?.label || '') as string).toLowerCase()
    return nodeId === state || nodeName === state || nodeId === props.currentState.toLowerCase()
  })
  return node?.id || null
})

async function loadFlow() {
  if (!props.templateId) {
    error.value = t('instance.noTemplate')
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await api.getWorkflow(props.templateId)
    templateName.value = res.name
    if (res.flow_json) {
      const flow = JSON.parse(res.flow_json)
      const rawNodes = flow.nodes || []
      const rawEdges = flow.edges || []

      nodes.value = rawNodes.map((n: any) => {
        const isCurrent = n.id === currentNodeId.value
        const isCompleted = isNodeCompleted(n.id, rawEdges)
        const agentName = n.data?.name || n.data?.label || n.id
        return {
          ...n,
          type: 'agent',
          data: {
            ...n.data,
            label: getAgentDisplayName(agentName),
            name: agentName,
            description: getAgentDescription(agentName) || n.data?.agent || '',
            status: isCurrent ? 'current' : isCompleted ? 'completed' : 'pending',
          },
          style: {
            ...n.style,
            borderWidth: isCurrent ? '2px' : '1px',
            borderColor: isCurrent ? '#3b82f6' : isCompleted ? '#22c55e' : 'var(--border-color)',
            backgroundColor: isCurrent ? 'rgba(59, 130, 246, 0.1)' : isCompleted ? 'rgba(34, 197, 94, 0.08)' : 'var(--bg-secondary)',
            boxShadow: isCurrent ? '0 0 0 3px rgba(59, 130, 246, 0.2)' : undefined,
          },
        }
      })

      edges.value = rawEdges.map((e: any) => {
        const sourceCompleted = isNodeCompleted(e.source, rawEdges)
        return {
          ...e,
          animated: e.source === currentNodeId.value,
          style: {
            ...e.style,
            stroke: sourceCompleted ? '#22c55e' : 'var(--border-color)',
            strokeWidth: sourceCompleted ? 2 : 1,
          },
        }
      })
    } else {
      error.value = t('instance.noFlowData')
    }
  } catch (e: any) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

function isNodeCompleted(nodeId: string, allEdges: any[]) {
  if (props.instanceStatus === 'completed') return true
  if (props.instanceStatus === 'failed') {
    const current = currentNodeId.value
    if (!current) return false
    const edgeToCurrent = allEdges.find((e: any) => e.target === current)
    if (!edgeToCurrent) return false
    const visited = new Set<string>()
    const queue = [allEdges[0]?.source]
    while (queue.length) {
      const id = queue.shift()
      if (!id || visited.has(id)) continue
      visited.add(id)
      if (id === nodeId) return true
      if (id === current) break
      allEdges.filter((e: any) => e.source === id).forEach((e: any) => queue.push(e.target))
    }
    return visited.has(nodeId)
  }
  const current = currentNodeId.value
  if (!current) return false
  const visited = new Set<string>()
  const queue = [allEdges[0]?.source]
  while (queue.length) {
    const id = queue.shift()
    if (!id || visited.has(id)) continue
    visited.add(id)
    if (id === nodeId) return true
    if (id === current) break
    allEdges.filter((e: any) => e.source === id).forEach((e: any) => queue.push(e.target))
  }
  return visited.has(nodeId)
}

watch(() => props.visible, (v) => {
  if (v) loadFlow()
})

function handleClose() {
  emit('close')
}

function handleBackdropClick(e: MouseEvent) {
  if (e.target === e.currentTarget) handleClose()
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="modal-backdrop" @click="handleBackdropClick">
        <div class="modal-container">
          <div class="modal-header">
            <div class="modal-title">
              <GitBranch :size="18" />
              <span>{{ t('instance.flowTitle', { id: instanceId }) }}</span>
            </div>
            <div class="modal-subtitle">
              <span v-if="templateName" class="template-tag">{{ templateName }}</span>
              <span class="state-tag" :class="instanceStatus">{{ currentState }}</span>
            </div>
            <button class="modal-close" @click="handleClose">
              <X :size="18" />
            </button>
          </div>

          <div class="modal-body">
            <div v-if="loading" class="modal-loading">{{ t('common.loading') }}</div>
            <div v-else-if="error" class="modal-error">{{ error }}</div>
            <div v-else-if="nodes.length === 0" class="modal-empty">{{ t('instance.noFlowData') }}</div>
            <div v-else class="flow-canvas">
              <VueFlow
                :nodes="nodes"
                :edges="edges"
                :nodes-draggable="false"
                :nodes-connectable="false"
                :edges-updatable="false"
                :edges-focusable="false"
                :zoom-on-double-click="false"
                :min-zoom="0.2"
                :max-zoom="2"
                fit-view-on-init
              >
                <template #node-agent="nodeProps">
                  <div class="flow-node" :class="nodeProps.data.status">
                    <div class="flow-node__header">
                      <span class="flow-node__dot" :class="nodeProps.data.status"></span>
                      <span class="flow-node__title">{{ nodeProps.data.label }}</span>
                    </div>
                    <div v-if="nodeProps.data.description" class="flow-node__desc">
                      {{ nodeProps.data.description }}
                    </div>
                    <Handle type="target" :position="Position.Left" />
                    <Handle type="source" :position="Position.Right" />
                  </div>
                </template>
                <Background />
                <Controls />
              </VueFlow>
            </div>
          </div>

          <div class="modal-footer">
            <div class="legend">
              <span class="legend-item">
                <span class="legend-dot completed"></span>
                {{ t('instance.legendCompleted') }}
              </span>
              <span class="legend-item">
                <span class="legend-dot current"></span>
                {{ t('instance.legendCurrent') }}
              </span>
              <span class="legend-item">
                <span class="legend-dot pending"></span>
                {{ t('instance.legendPending') }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 20px;
}

.modal-container {
  background-color: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  width: 100%;
  max-width: 960px;
  height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
  flex-shrink: 0;
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-subtitle {
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 9999px;
  background-color: rgba(99, 102, 241, 0.12);
  color: #6366f1;
  font-weight: 500;
}

.state-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 9999px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.state-tag.running {
  background-color: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.state-tag.completed {
  background-color: rgba(34, 197, 94, 0.15);
  color: var(--accent-green);
}

.state-tag.failed {
  background-color: rgba(239, 68, 68, 0.15);
  color: var(--accent-red);
}

.state-tag.paused {
  background-color: rgba(234, 179, 8, 0.15);
  color: var(--accent-yellow);
}

.modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
}

.modal-close:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

.modal-body {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.modal-loading,
.modal-error,
.modal-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: 14px;
  color: var(--text-secondary);
}

.modal-error {
  color: var(--accent-red);
}

.flow-canvas {
  width: 100%;
  height: 100%;
}

.flow-canvas :deep(.vue-flow) {
  background-color: var(--bg-primary);
}

.flow-node {
  padding: 10px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
  min-width: 140px;
  transition: all 0.2s ease;
}

.flow-node.current {
  border-color: #3b82f6;
  background-color: rgba(59, 130, 246, 0.1);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.flow-node.completed {
  border-color: #22c55e;
  background-color: rgba(34, 197, 94, 0.08);
}

.flow-node__header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.flow-node__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.flow-node__dot.current {
  background-color: #3b82f6;
}

.flow-node__dot.completed {
  background-color: #22c55e;
}

.flow-node__dot.pending {
  background-color: var(--text-tertiary);
}

.flow-node__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.flow-node__desc {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.modal-footer {
  padding: 10px 20px;
  border-top: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
  flex-shrink: 0;
}

.legend {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-dot.completed {
  background-color: #22c55e;
}

.legend-dot.current {
  background-color: #3b82f6;
}

.legend-dot.pending {
  background-color: var(--text-tertiary);
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.96);
  opacity: 0;
}
</style>
