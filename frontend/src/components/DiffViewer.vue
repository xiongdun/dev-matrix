<template>
  <div class="diff-viewer">
    <div class="diff-toolbar">
      <div class="diff-tabs">
        <button
          class="diff-tab"
          :class="{ active: viewMode === 'diff' }"
          @click="viewMode = 'diff'"
        >
          <GitCompare :size="14" />
          {{ t('workbench.diffView') }}
        </button>
        <button
          class="diff-tab"
          :class="{ active: viewMode === 'full' }"
          @click="viewMode = 'full'"
        >
          <FileText :size="14" />
          {{ t('workbench.fullView') }}
        </button>
      </div>
      <span class="diff-stats" v-if="viewMode === 'diff'">
        <span class="stat-add">+{{ addCount }}</span>
        <span class="stat-del">−{{ delCount }}</span>
      </span>
    </div>

    <!-- Diff 视图 -->
    <div v-if="viewMode === 'diff'" class="diff-content">
      <div v-if="diffLines.length === 0" class="diff-empty">
        {{ t('workbench.noChanges') }}
      </div>
      <div
        v-for="(line, idx) in diffLines"
        :key="idx"
        class="diff-line"
        :class="line.type"
      >
        <span class="diff-marker">{{ line.marker }}</span>
        <span class="diff-line-num" v-if="line.oldNum !== undefined">{{ line.oldNum }}</span>
        <span class="diff-line-num" v-if="line.newNum !== undefined">{{ line.newNum }}</span>
        <span class="diff-line-content">{{ line.content }}</span>
      </div>
    </div>

    <!-- 完整内容视图 -->
    <div v-else class="full-content">
      <pre>{{ newContent }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { GitCompare, FileText } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps<{
  oldContent: string
  newContent: string
}>()

const viewMode = ref<'diff' | 'full'>('diff')

interface DiffLine {
  type: 'add' | 'del' | 'context'
  marker: string
  content: string
  oldNum?: number
  newNum?: number
}

// 简单的行级diff算法
const diffLines = computed((): DiffLine[] => {
  const oldLines = props.oldContent.split('\n')
  const newLines = props.newContent.split('\n')
  const result: DiffLine[] = []

  let oldIdx = 0
  let newIdx = 0
  let oldNum = 1
  let newNum = 1

  while (oldIdx < oldLines.length || newIdx < newLines.length) {
    const oldLine = oldIdx < oldLines.length ? oldLines[oldIdx] : null
    const newLine = newIdx < newLines.length ? newLines[newIdx] : null

    if (oldLine === newLine && oldLine !== null) {
      // 相同行
      result.push({
        type: 'context',
        marker: ' ',
        content: oldLine,
        oldNum: oldNum++,
        newNum: newNum++,
      })
      oldIdx++
      newIdx++
    } else if (newLine !== null && (oldLine === null || oldIdx >= oldLines.length)) {
      // 新增行
      result.push({
        type: 'add',
        marker: '+',
        content: newLine,
        newNum: newNum++,
      })
      newIdx++
    } else if (oldLine !== null && (newLine === null || newIdx >= newLines.length)) {
      // 删除行
      result.push({
        type: 'del',
        marker: '−',
        content: oldLine,
        oldNum: oldNum++,
      })
      oldIdx++
    } else {
      // 不同行，先删除旧行，再新增新行
      result.push({
        type: 'del',
        marker: '−',
        content: oldLine!,
        oldNum: oldNum++,
      })
      oldIdx++
      result.push({
        type: 'add',
        marker: '+',
        content: newLine!,
        newNum: newNum++,
      })
      newIdx++
    }
  }

  return result
})

const addCount = computed(() => diffLines.value.filter((l) => l.type === 'add').length)
const delCount = computed(() => diffLines.value.filter((l) => l.type === 'del').length)
</script>

<style scoped>
.diff-viewer {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background-color: var(--bg-secondary);
}

.diff-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background-color: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
}

.diff-tabs {
  display: flex;
  gap: 4px;
}

.diff-tab {
  display: flex;
  align-items: center;
  gap: 4px;
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

.diff-tab:hover {
  color: var(--text-secondary);
  background-color: var(--bg-hover);
}

.diff-tab.active {
  color: var(--text-primary);
  background-color: var(--bg-primary);
}

.diff-stats {
  display: flex;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  font-family: 'SF Mono', Monaco, monospace;
}

.stat-add {
  color: #22c55e;
}

.stat-del {
  color: #ef4444;
}

.diff-content {
  max-height: 400px;
  overflow-y: auto;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 12px;
  line-height: 1.6;
}

.diff-line {
  display: flex;
  align-items: center;
  padding: 1px 8px;
  white-space: pre-wrap;
  word-break: break-all;
}

.diff-line.add {
  background-color: rgba(34, 197, 94, 0.1);
}

.diff-line.del {
  background-color: rgba(239, 68, 68, 0.1);
}

.diff-line.context:hover {
  background-color: var(--bg-hover);
}

.diff-marker {
  width: 16px;
  flex-shrink: 0;
  text-align: center;
  font-weight: 600;
  user-select: none;
}

.diff-line.add .diff-marker {
  color: #22c55e;
}

.diff-line.del .diff-marker {
  color: #ef4444;
}

.diff-line-num {
  width: 32px;
  text-align: right;
  color: var(--text-muted);
  padding-right: 8px;
  flex-shrink: 0;
  user-select: none;
}

.diff-line-content {
  flex: 1;
  color: var(--text-secondary);
  min-width: 0;
}

.diff-empty {
  padding: 24px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

.full-content {
  max-height: 400px;
  overflow-y: auto;
  padding: 12px;
}

.full-content pre {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 12px;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}
</style>
