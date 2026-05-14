<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>{{ t('skills.title') }}</h1>
        <p>{{ t('skills.subtitle') }}</p>
      </div>
    </div>

    <div class="upload-section">
      <div
        class="upload-area"
        :class="{ dragging: isDragging }"
        @dragenter.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @dragover.prevent
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".json"
          style="display: none"
          @change="handleFileChange"
        />
        <div class="upload-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
        </div>
        <p class="upload-text">{{ t('skills.uploadText') }}</p>
        <p class="upload-hint">{{ t('skills.uploadHint') }}</p>
      </div>
    </div>

    <div v-if="uploadError" class="upload-error">{{ uploadError }}</div>
    <div v-if="uploadSuccess" class="upload-success">{{ uploadSuccess }}</div>

    <div v-if="loading" class="empty-state">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="empty-state" style="color: var(--accent-red)">
      {{ t('common.error') }}: {{ error }}
    </div>
    <div v-else class="skills-table-wrapper">
      <table class="skills-table">
        <thead>
          <tr>
            <th>{{ t('skills.name') }}</th>
            <th>{{ t('skills.description') }}</th>
            <th>{{ t('skills.usedBy') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="skill in skills" :key="skill.name">
            <td class="skill-name">{{ skill.name }}</td>
            <td class="skill-desc">{{ skill.description }}</td>
            <td>
              <div v-if="skill.used_by && skill.used_by.length" class="used-by-tags">
                <span v-for="agent in skill.used_by" :key="agent" class="used-by-tag">{{ agent }}</span>
              </div>
              <span v-else class="used-by-empty">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../api'

const { t } = useI18n()

interface Skill {
  name: string
  description: string
  used_by: string[]
}

const skills = ref<Skill[]>([])
const loading = ref(true)
const error = ref('')
const isDragging = ref(false)
const uploadError = ref('')
const uploadSuccess = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

async function fetchSkills() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.getSkills()
    skills.value = res.skills || []
  } catch (e: any) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) processFile(file)
}

function handleDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files[0]
  if (file && file.type === 'application/json') {
    processFile(file)
  } else {
    uploadError.value = t('skills.errorInvalidFile')
  }
}

function processFile(file: File) {
  uploadError.value = ''
  uploadSuccess.value = ''
  const reader = new FileReader()
  reader.onload = async (e) => {
    try {
      const text = e.target?.result as string
      const payload = JSON.parse(text)
      await api.uploadSkill(payload)
      uploadSuccess.value = t('skills.uploadSuccess', { name: payload.name })
      await fetchSkills()
    } catch (err: any) {
      uploadError.value = err.message || String(err)
    }
  }
  reader.readAsText(file)
}

onMounted(fetchSkills)
</script>

<style scoped>
.upload-section {
  margin-bottom: 24px;
}

.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-lg);
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: var(--bg-secondary);
}

.upload-area:hover,
.upload-area.dragging {
  border-color: var(--accent-blue);
  background-color: var(--bg-hover);
}

.upload-icon {
  color: var(--text-muted);
  margin-bottom: 12px;
}

.upload-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.upload-hint {
  font-size: 13px;
  color: var(--text-muted);
}

.upload-error {
  margin-bottom: 16px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
  font-size: 13px;
}

.upload-success {
  margin-bottom: 16px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  background-color: rgba(34, 197, 94, 0.1);
  color: var(--accent-green);
  font-size: 13px;
}

.skills-table-wrapper {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.skills-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.skills-table th {
  text-align: left;
  padding: 12px 16px;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-tertiary);
}

.skills-table td {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}

.skills-table tr:last-child td {
  border-bottom: none;
}

.skills-table tr:hover td {
  background-color: var(--bg-hover);
}

.skill-name {
  font-weight: 600;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 13px;
}

.skill-desc {
  color: var(--text-secondary);
  font-size: 13px;
}

.used-by-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.used-by-tag {
  font-size: 11px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: 9999px;
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.used-by-empty {
  color: var(--text-muted);
  font-size: 13px;
}
</style>
