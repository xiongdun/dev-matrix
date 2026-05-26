<template>
  <div class="forbidden-page">
    <div class="forbidden-content">
      <ShieldAlert :size="64" class="forbidden-icon" />
      <h1>{{ t('forbidden.title') }}</h1>
      <p>{{ t('forbidden.message') }}</p>
      <button class="btn-primary" @click="goHome">
        {{ t('forbidden.backHome') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ShieldAlert } from 'lucide-vue-next'

const router = useRouter()
const { t } = useI18n()

function goHome() {
  router.push('/')
}
</script>

<style scoped>
.forbidden-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: var(--bg-primary);
}

.forbidden-content {
  text-align: center;
  padding: 48px;
}

.forbidden-icon {
  color: var(--accent-orange);
  margin-bottom: 24px;
}

h1 {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

p {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.btn-primary {
  padding: 10px 24px;
  border-radius: var(--radius-md);
  background-color: var(--accent-blue);
  color: white;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.btn-primary:hover {
  opacity: 0.9;
}
</style>
