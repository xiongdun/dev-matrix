# Settings Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated `/settings` route with grouped configuration sections (Appearance, LLM, Workflow, Notifications, About).

**Architecture:** Vue 3 single-file components with a settings store composable. Settings persisted to localStorage. Theme and language changes apply immediately; other settings require explicit save.

**Tech Stack:** Vue 3 + TypeScript + Vite + vue-i18n + Vue Router

---

## File Structure

### New Files
- `frontend/src/pages/SettingsPage.vue` — Main settings page layout
- `frontend/src/components/settings/SettingsSection.vue` — Card container for each section
- `frontend/src/components/settings/SettingItem.vue` — Individual setting row (label + control)
- `frontend/src/composables/useSettings.ts` — Settings store with localStorage persistence
- `frontend/src/router.ts` — Vue Router configuration

### Modified Files
- `frontend/src/App.vue` — Add router-view
- `frontend/src/components/Sidebar.vue` — Add router-link for settings
- `frontend/src/i18n/locales/zh.json` — Add settings translations
- `frontend/src/i18n/locales/en.json` — Add settings translations
- `frontend/src/style.css` — Add form control styles

---

## Task 1: Add Vue Router

**Files:**
- Create: `frontend/src/router.ts`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/main.ts`

- [ ] **Step 1: Install vue-router**

```bash
cd /Users/Summer/Documents/works/codes/dev-matrix/frontend
npm install vue-router@4
```

- [ ] **Step 2: Create router configuration**

`frontend/src/router.ts`:
```typescript
import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from './components/Dashboard.vue'
import SettingsPage from './pages/SettingsPage.vue'

const routes = [
  { path: '/', component: Dashboard },
  { path: '/settings', component: SettingsPage },
]

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
})
```

- [ ] **Step 3: Register router in main.ts**

Modify `frontend/src/main.ts`:
```typescript
import { createApp } from 'vue'
import { createI18n } from 'vue-i18n'
import App from './App.vue'
import { router } from './router'
import en from './i18n/locales/en.json'
import zh from './i18n/locales/zh.json'

const i18n = createI18n({
  locale: localStorage.getItem('devmatrix-language') || 'zh',
  fallbackLocale: 'en',
  messages: { en, zh },
})

const app = createApp(App)
app.use(i18n)
app.use(router)
app.mount('#app')
```

- [ ] **Step 4: Update App.vue to use router-view**

Modify `frontend/src/App.vue`:
```vue
<template>
  <div id="app" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <Sidebar :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>
```

- [ ] **Step 5: Verify build**

Run: `cd /Users/Summer/Documents/works/codes/dev-matrix/frontend && npm run build`
Expected: No errors

---

## Task 2: Create Settings Store Composable

**Files:**
- Create: `frontend/src/composables/useSettings.ts`

- [ ] **Step 1: Implement useSettings composable**

`frontend/src/composables/useSettings.ts`:
```typescript
import { reactive, watch } from 'vue'

export interface Settings {
  appearance: {
    theme: 'dark' | 'light'
    language: 'zh' | 'en'
    sidebarCollapsed: boolean
  }
  llm: {
    provider: 'openai' | 'anthropic'
    apiKey: string
    model: string
    strategy: 'quality_first' | 'cost_first' | 'config_driven'
  }
  workflow: {
    approvalMode: 'manual' | 'auto'
    timeout: number
    retryCount: number
  }
  notifications: {
    workflowCompleted: boolean
    approvalRequired: boolean
    agentFailed: boolean
    webhookUrl: string
  }
}

const STORAGE_KEY = 'devmatrix-settings'

const defaultSettings: Settings = {
  appearance: {
    theme: 'dark',
    language: 'zh',
    sidebarCollapsed: false,
  },
  llm: {
    provider: 'openai',
    apiKey: '',
    model: 'gpt-4',
    strategy: 'quality_first',
  },
  workflow: {
    approvalMode: 'manual',
    timeout: 30,
    retryCount: 3,
  },
  notifications: {
    workflowCompleted: true,
    approvalRequired: true,
    agentFailed: false,
    webhookUrl: '',
  },
}

function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      return { ...defaultSettings, ...JSON.parse(raw) }
    }
  } catch {
    // ignore
  }
  return { ...defaultSettings }
}

export const settings = reactive<Settings>(loadSettings())

watch(
  () => settings,
  (val) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(val))
  },
  { deep: true }
)

export function useSettings() {
  return {
    settings,
    reset() {
      Object.assign(settings, defaultSettings)
    },
  }
}
```

---

## Task 3: Create Settings UI Components

**Files:**
- Create: `frontend/src/components/settings/SettingsSection.vue`
- Create: `frontend/src/components/settings/SettingItem.vue`

- [ ] **Step 1: Create SettingsSection component**

`frontend/src/components/settings/SettingsSection.vue`:
```vue
<template>
  <div class="panel settings-section">
    <div class="panel-header">
      <h2 class="panel-title">{{ title }}</h2>
      <p v-if="description" class="panel-description">{{ description }}</p>
    </div>
    <div class="panel-body">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<style scoped>
.settings-section {
  margin-bottom: 24px;
}

.panel-description {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}
</style>
```

- [ ] **Step 2: Create SettingItem component**

`frontend/src/components/settings/SettingItem.vue`:
```vue
<template>
  <div class="setting-item">
    <div class="setting-label">
      <label>{{ label }}</label>
      <p v-if="description" class="setting-description">{{ description }}</p>
    </div>
    <div class="setting-control">
      <select
        v-if="type === 'select'"
        :value="modelValue"
        @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
        class="setting-select"
      >
        <option v-for="opt in options" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>

      <input
        v-else-if="type === 'text' || type === 'password'"
        :type="type"
        :value="modelValue"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        class="setting-input"
        :placeholder="placeholder"
      />

      <input
        v-else-if="type === 'number'"
        type="number"
        :value="modelValue"
        @input="$emit('update:modelValue', Number(($event.target as HTMLInputElement).value))"
        class="setting-input"
        :min="min"
        :max="max"
      />

      <label v-else-if="type === 'toggle'" class="setting-toggle">
        <input
          type="checkbox"
          :checked="modelValue"
          @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
        />
        <span class="toggle-slider"></span>
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Option {
  value: string
  label: string
}

defineProps<{
  label: string
  type: 'select' | 'text' | 'password' | 'number' | 'toggle'
  modelValue: any
  description?: string
  options?: Option[]
  placeholder?: string
  min?: number
  max?: number
}>()

defineEmits<{
  'update:modelValue': [value: any]
}>()
</script>

<style scoped>
.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  flex: 1;
}

.setting-label label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.setting-description {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.setting-control {
  flex-shrink: 0;
  margin-left: 24px;
}

.setting-select,
.setting-input {
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  padding: 8px 12px;
  font-size: 14px;
  min-width: 200px;
  outline: none;
  transition: border-color 0.15s ease;
}

.setting-select:focus,
.setting-input:focus {
  border-color: var(--accent-blue);
}

.setting-select option {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

/* Toggle Switch */
.setting-toggle {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  cursor: pointer;
}

.setting-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--bg-tertiary);
  border-radius: 24px;
  transition: background-color 0.2s ease;
  border: 1px solid var(--border-color);
}

.toggle-slider::before {
  content: '';
  position: absolute;
  height: 18px;
  width: 18px;
  left: 2px;
  bottom: 2px;
  background-color: var(--text-primary);
  border-radius: 50%;
  transition: transform 0.2s ease;
}

.setting-toggle input:checked + .toggle-slider {
  background-color: var(--accent-blue);
  border-color: var(--accent-blue);
}

.setting-toggle input:checked + .toggle-slider::before {
  transform: translateX(20px);
}
</style>
```

---

## Task 4: Create SettingsPage

**Files:**
- Create: `frontend/src/pages/SettingsPage.vue`

- [ ] **Step 1: Implement SettingsPage**

`frontend/src/pages/SettingsPage.vue`:
```vue
<template>
  <div>
    <div class="dashboard-header">
      <div>
        <h1>{{ t('settings.title') }}</h1>
      </div>
      <button
        class="theme-toggle"
        @click="saveSettings"
        :disabled="!isDirty"
        :style="{ opacity: isDirty ? 1 : 0.5 }"
      >
        {{ t('settings.save') }}
      </button>
    </div>

    <SettingsSection :title="t('settings.appearance.title')">
      <SettingItem
        :label="t('settings.appearance.theme')"
        type="select"
        v-model="form.appearance.theme"
        :options="themeOptions"
      />
      <SettingItem
        :label="t('settings.appearance.language')"
        type="select"
        v-model="form.appearance.language"
        :options="languageOptions"
      />
      <SettingItem
        :label="t('settings.appearance.sidebar')"
        type="select"
        v-model="sidebarCollapsedValue"
        :options="sidebarOptions"
      />
    </SettingsSection>

    <SettingsSection :title="t('settings.llm.title')">
      <SettingItem
        :label="t('settings.llm.provider')"
        type="select"
        v-model="form.llm.provider"
        :options="providerOptions"
      />
      <SettingItem
        :label="t('settings.llm.apiKey')"
        type="password"
        v-model="form.llm.apiKey"
        :placeholder="'sk-...'"
      />
      <SettingItem
        :label="t('settings.llm.model')"
        type="select"
        v-model="form.llm.model"
        :options="modelOptions"
      />
      <SettingItem
        :label="t('settings.llm.strategy')"
        type="select"
        v-model="form.llm.strategy"
        :options="strategyOptions"
      />
    </SettingsSection>

    <SettingsSection :title="t('settings.workflow.title')">
      <SettingItem
        :label="t('settings.workflow.approvalMode')"
        type="select"
        v-model="form.workflow.approvalMode"
        :options="approvalOptions"
      />
      <SettingItem
        :label="t('settings.workflow.timeout')"
        type="number"
        v-model="form.workflow.timeout"
        :min="5"
        :max="300"
      />
      <SettingItem
        :label="t('settings.workflow.retryCount')"
        type="number"
        v-model="form.workflow.retryCount"
        :min="0"
        :max="10"
      />
    </SettingsSection>

    <SettingsSection :title="t('settings.notifications.title')">
      <SettingItem
        :label="t('settings.notifications.workflowCompleted')"
        type="toggle"
        v-model="form.notifications.workflowCompleted"
      />
      <SettingItem
        :label="t('settings.notifications.approvalRequired')"
        type="toggle"
        v-model="form.notifications.approvalRequired"
      />
      <SettingItem
        :label="t('settings.notifications.agentFailed')"
        type="toggle"
        v-model="form.notifications.agentFailed"
      />
      <SettingItem
        :label="t('settings.notifications.webhookUrl')"
        type="text"
        v-model="form.notifications.webhookUrl"
        :placeholder="'https://...'"
      />
    </SettingsSection>

    <SettingsSection :title="t('settings.about.title')">
      <SettingItem
        :label="t('settings.about.version')"
        type="text"
        v-model="version"
        :disabled="true"
      />
      <SettingItem
        :label="t('settings.about.backend')"
        type="text"
        :model-value="backendStatus"
        :disabled="true"
      />
    </SettingsSection>

    <div v-if="showToast" class="toast">{{ t('settings.saved') }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SettingsSection from '../components/settings/SettingsSection.vue'
import SettingItem from '../components/settings/SettingItem.vue'
import { useSettings, settings as globalSettings } from '../composables/useSettings'

const { t, locale } = useI18n()
const { settings } = useSettings()

const form = reactive(JSON.parse(JSON.stringify(settings)))
const showToast = ref(false)
const version = ref('1.0.0')
const backendStatus = ref(t('settings.about.connected'))

const isDirty = computed(() => {
  return JSON.stringify(form) !== JSON.stringify(settings)
})

const sidebarCollapsedValue = computed({
  get: () => (form.appearance.sidebarCollapsed ? 'collapsed' : 'expanded'),
  set: (val: string) => {
    form.appearance.sidebarCollapsed = val === 'collapsed'
  },
})

const themeOptions = [
  { value: 'dark', label: t('settings.appearance.themeDark') },
  { value: 'light', label: t('settings.appearance.themeLight') },
]

const languageOptions = [
  { value: 'zh', label: '中文' },
  { value: 'en', label: 'English' },
]

const sidebarOptions = [
  { value: 'expanded', label: t('settings.appearance.sidebarExpanded') },
  { value: 'collapsed', label: t('settings.appearance.sidebarCollapsed') },
]

const providerOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
]

const modelOptions = [
  { value: 'gpt-4', label: 'GPT-4' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  { value: 'claude-3-opus', label: 'Claude 3 Opus' },
  { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
]

const strategyOptions = [
  { value: 'quality_first', label: t('settings.llm.strategyQuality') },
  { value: 'cost_first', label: t('settings.llm.strategyCost') },
  { value: 'config_driven', label: t('settings.llm.strategyConfig') },
]

const approvalOptions = [
  { value: 'manual', label: t('settings.workflow.approvalManual') },
  { value: 'auto', label: t('settings.workflow.approvalAuto') },
]

function saveSettings() {
  Object.assign(globalSettings, JSON.parse(JSON.stringify(form)))
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 2000)
}

// Apply theme immediately
watch(() => form.appearance.theme, (theme) => {
  document.documentElement.setAttribute('data-theme', theme)
})

// Apply language immediately
watch(() => form.appearance.language, (lang) => {
  locale.value = lang
  localStorage.setItem('devmatrix-language', lang)
})
</script>

<style scoped>
.toast {
  position: fixed;
  bottom: 32px;
  right: 32px;
  background-color: var(--accent-green);
  color: white;
  padding: 12px 20px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
```

---

## Task 5: Update Sidebar for Routing

**Files:**
- Modify: `frontend/src/components/Sidebar.vue`

- [ ] **Step 1: Replace click with router-link**

Replace the nav items in Sidebar.vue template:
```vue
<router-link
  v-for="item in menuItems"
  :key="item.key"
  :to="item.path"
  :class="['nav-item', { active: $route.path === item.path }]"
>
```

Update menuItems:
```typescript
const menuItems = [
  { key: 'dashboard', icon: 'dashboard', labelKey: 'sidebar.dashboard', path: '/' },
  { key: 'requirements', icon: 'requirements', labelKey: 'sidebar.requirements', path: '/requirements' },
  { key: 'approvals', icon: 'approvals', labelKey: 'sidebar.approvals', path: '/approvals' },
  { key: 'workflow', icon: 'workflow', labelKey: 'sidebar.workflow', path: '/workflow' },
  { key: 'settings', icon: 'settings', labelKey: 'sidebar.settings', path: '/settings' },
]
```

---

## Task 6: Add i18n Translations

**Files:**
- Modify: `frontend/src/i18n/locales/zh.json`
- Modify: `frontend/src/i18n/locales/en.json`

- [ ] **Step 1: Add settings keys to zh.json**

Append to `frontend/src/i18n/locales/zh.json`:
```json
  "settings": {
    "title": "设置",
    "save": "保存更改",
    "saved": "设置已保存",
    "appearance": {
      "title": "外观",
      "theme": "主题",
      "themeDark": "深色",
      "themeLight": "浅色",
      "language": "语言",
      "sidebar": "侧边栏默认状态",
      "sidebarExpanded": "展开",
      "sidebarCollapsed": "收起"
    },
    "llm": {
      "title": "LLM 配置",
      "provider": "默认提供商",
      "apiKey": "API 密钥",
      "show": "显示",
      "hide": "隐藏",
      "model": "模型",
      "strategy": "路由策略",
      "strategyQuality": "质量优先",
      "strategyCost": "成本优先",
      "strategyConfig": "配置驱动"
    },
    "workflow": {
      "title": "工作流",
      "approvalMode": "审批模式",
      "approvalManual": "人工审批",
      "approvalAuto": "自动通过",
      "timeout": "活动超时（秒）",
      "retryCount": "重试次数"
    },
    "notifications": {
      "title": "通知",
      "workflowCompleted": "工作流完成",
      "approvalRequired": "需要审批",
      "agentFailed": "智能体失败",
      "webhookUrl": "Webhook 地址"
    },
    "about": {
      "title": "关于",
      "version": "版本",
      "backend": "后端状态",
      "connected": "已连接",
      "disconnected": "未连接",
      "github": "GitHub"
    }
  }
```

- [ ] **Step 2: Add settings keys to en.json**

Append corresponding English translations.

---

## Task 7: Add CSS Styles for Forms

**Files:**
- Modify: `frontend/src/style.css`

- [ ] **Step 1: Append form control styles**

Add to end of `frontend/src/style.css`:
```css
/* Form Controls */
.setting-select,
.setting-input {
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  padding: 8px 12px;
  font-size: 14px;
  min-width: 200px;
  outline: none;
  transition: border-color 0.15s ease;
}

.setting-select:focus,
.setting-input:focus {
  border-color: var(--accent-blue);
}

.setting-select option {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.setting-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

---

## Task 8: Build and Verify

- [ ] **Step 1: Build frontend**

```bash
cd /Users/Summer/Documents/works/codes/dev-matrix/frontend
npm run build
```

- [ ] **Step 2: Restart dev server**

```bash
npm run dev -- --port 3000
```

- [ ] **Step 3: Verify**

1. Navigate to http://localhost:3000/#/settings
2. Check all sections render correctly
3. Test theme switch applies immediately
4. Test language switch applies immediately
5. Test save button shows toast
6. Verify settings persist after refresh
