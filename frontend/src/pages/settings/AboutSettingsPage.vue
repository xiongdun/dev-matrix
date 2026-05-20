<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const version = ref('1.0.0')
const buildDate = ref('2026-05-20')
const backendStatus = ref<'ok' | 'error' | 'checking'>('checking')

onMounted(async () => {
  try {
    const res = await fetch('/health')
    if (res.ok) {
      backendStatus.value = 'ok'
    } else {
      backendStatus.value = 'error'
    }
  } catch {
    backendStatus.value = 'error'
  }
})
</script>

<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>{{ t('settings.aboutTitle') }}</h1>
        <p>{{ t('settings.aboutSubtitle') }}</p>
      </div>
    </div>

    <div class="about-card">
      <div class="about-logo">
        <div class="logo-icon">DM</div>
        <div class="logo-info">
          <h2>DevMatrix</h2>
          <p>{{ t('settings.aboutDesc') }}</p>
        </div>
      </div>

      <div class="about-info">
        <div class="info-row">
          <span class="info-label">{{ t('settings.version') }}</span>
          <span class="info-value">{{ version }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{{ t('settings.buildDate') }}</span>
          <span class="info-value">{{ buildDate }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{{ t('settings.backendStatus') }}</span>
          <span class="info-value">
            <span class="status-badge" :class="backendStatus">
              {{ backendStatus === 'ok' ? t('settings.statusOk') : backendStatus === 'error' ? t('settings.statusError') : t('settings.statusChecking') }}
            </span>
          </span>
        </div>
      </div>
    </div>

    <div class="about-section">
      <h3>{{ t('settings.techStack') }}</h3>
      <div class="tech-grid">
        <div class="tech-item">
          <span class="tech-name">Frontend</span>
          <span class="tech-value">Vue 3 + TypeScript + Vite</span>
        </div>
        <div class="tech-item">
          <span class="tech-name">Backend</span>
          <span class="tech-value">FastAPI + Python 3.10+</span>
        </div>
        <div class="tech-item">
          <span class="tech-name">Workflow</span>
          <span class="tech-value">Temporal</span>
        </div>
        <div class="tech-item">
          <span class="tech-name">Database</span>
          <span class="tech-value">SQLite / PostgreSQL</span>
        </div>
        <div class="tech-item">
          <span class="tech-name">LLM</span>
          <span class="tech-value">OpenAI / Anthropic / Azure</span>
        </div>
        <div class="tech-item">
          <span class="tech-name">Sandbox</span>
          <span class="tech-value">Docker / Firecracker</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.about-card {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 1.5rem;
}

.about-logo {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.logo-icon {
  width: 64px;
  height: 64px;
  background: var(--primary-color);
  color: white;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
}

.logo-info h2 {
  margin: 0 0 0.25rem;
  font-size: 1.25rem;
  color: var(--text-primary);
}

.logo-info p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.about-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
}

.info-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.info-value {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-badge.ok {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.status-badge.error {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.status-badge.checking {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.about-section {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1.5rem;
}

.about-section h3 {
  margin: 0 0 1rem;
  font-size: 1rem;
  color: var(--text-primary);
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.tech-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem;
  background: var(--bg-color);
  border-radius: 6px;
}

.tech-name {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.tech-value {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}
</style>
