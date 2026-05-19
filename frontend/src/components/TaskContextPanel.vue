<template>
  <div class="context-panel">
    <!-- 标题栏 -->
    <div class="context-header">
      <div class="context-title">
        <span>{{ t('workbench.contextTitle') }}</span>
        <Info :size="14" class="title-icon" />
      </div>
    </div>

    <!-- Token 进度条 -->
    <div v-if="context.tokenUsage" class="token-section">
      <div class="token-bar-wrapper">
        <div class="token-bar-bg">
          <div
            class="token-bar-fill"
            :style="{ width: `${Math.min(context.tokenUsage.percent, 100)}%` }"
          ></div>
        </div>
        <span class="token-percent">{{ context.tokenUsage.percent }}%</span>
      </div>
      <div class="token-legend">
        <span class="legend-item">
          <span class="legend-dot legend-skills"></span>
          {{ t('workbench.contextSkills') }}
        </span>
        <span class="legend-item">
          <span class="legend-dot legend-files"></span>
          {{ t('workbench.contextFiles') }}
        </span>
        <span class="legend-item">
          <span class="legend-dot legend-others"></span>
          {{ t('workbench.contextOthers') }}
        </span>
      </div>
    </div>

    <!-- 标签页切换 -->
    <div class="context-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="context-tab"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 技能列表 -->
    <div v-if="activeTab === 'skills'" class="context-list">
      <div
        v-for="skill in context.skills"
        :key="skill.name"
        class="context-item"
      >
        <Library :size="16" class="item-icon" />
        <span class="item-name">{{ skill.name }}</span>
      </div>
      <div v-if="!context.skills?.length" class="context-empty">
        {{ t('workbench.contextNoSkills') }}
      </div>
    </div>

    <!-- 文件列表 -->
    <div v-if="activeTab === 'files'" class="context-list">
      <div
        v-for="file in context.files"
        :key="file.path"
        class="context-item"
      >
        <FileCode :size="16" class="item-icon" />
        <span class="item-name">{{ file.name || file.path }}</span>
      </div>
      <div v-if="!context.files?.length" class="context-empty">
        {{ t('workbench.contextNoFiles') }}
      </div>
    </div>

    <!-- 工具列表 -->
    <div v-if="activeTab === 'tools'" class="context-list">
      <div
        v-for="tool in context.tools"
        :key="tool.name"
        class="context-item"
      >
        <Wrench :size="16" class="item-icon" />
        <span class="item-name">{{ tool.name }}</span>
      </div>
      <div v-if="!context.tools?.length" class="context-empty">
        {{ t('workbench.contextNoTools') }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Info, Library, FileCode, Wrench } from 'lucide-vue-next'

const { t } = useI18n()

interface Skill {
  name: string
  description?: string
}

interface FileRef {
  path: string
  name?: string
}

interface Tool {
  name: string
  description?: string
}

interface TokenUsage {
  percent: number
  used: number
  total: number
}

interface TaskContext {
  skills: Skill[]
  files: FileRef[]
  tools: Tool[]
  tokenUsage?: TokenUsage
}

const props = defineProps<{
  context: TaskContext
}>()

const activeTab = ref('skills')

const tabs = computed(() => [
  { key: 'skills', label: t('workbench.contextSkills') },
  { key: 'files', label: t('workbench.contextFiles') },
  { key: 'tools', label: t('workbench.contextTools') },
])
</script>

<style scoped>
.context-panel {
  padding: 16px;
  border-top: 1px solid var(--border-color);
}

.context-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.context-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.title-icon {
  color: var(--text-muted);
}

/* Token 进度条 */
.token-section {
  margin-bottom: 16px;
}

.token-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.token-bar-bg {
  flex: 1;
  height: 6px;
  background-color: var(--bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
}

.token-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #6366f1);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.token-percent {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  font-family: 'SF Mono', Monaco, monospace;
  white-space: nowrap;
}

.token-legend {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-tertiary);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.legend-skills {
  background-color: #3b82f6;
}

.legend-files {
  background-color: #10b981;
}

.legend-others {
  background-color: var(--text-muted);
}

/* 标签页 */
.context-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
}

.context-tab {
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.context-tab:hover {
  color: var(--text-secondary);
  background-color: var(--bg-hover);
}

.context-tab.active {
  color: var(--text-primary);
  background-color: var(--bg-tertiary);
}

/* 列表 */
.context-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.context-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.context-item:hover {
  background-color: var(--bg-hover);
}

.item-icon {
  color: #6366f1;
  flex-shrink: 0;
}

.item-name {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.context-empty {
  padding: 16px;
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
}
</style>
