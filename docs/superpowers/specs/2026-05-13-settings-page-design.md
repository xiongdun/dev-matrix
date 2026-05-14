# Settings Page Design Spec

## Overview

A dedicated `/settings` route providing comprehensive configuration management for the DevMatrix frontend. The page follows the existing Linear/Vercel dark developer tool aesthetic with grouped setting sections.

## Design Principles

- **Consistency**: Match existing dashboard styling (dark theme, CSS variables, card-based layout)
- **Clarity**: Group related settings with clear section headers
- **Feedback**: Save states with visual confirmation (toast/success indicator)
- **Safety**: Sensitive fields (API keys) are masked by default

## Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Settings                                    [Save Changes] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ Appearance ──────────────────────────────────────────┐  │
│  │  Theme: [Dark ○] [Light ○]                           │  │
│  │  Language: [中文 ▼]                                   │  │
│  │  Sidebar Default: [Expanded ○] [Collapsed ○]         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ LLM Configuration ───────────────────────────────────┐  │
│  │  Default Provider: [OpenAI ▼]                         │  │
│  │  API Key: [••••••••••••••••] [Show]                  │  │
│  │  Model: [gpt-4 ▼]                                     │  │
│  │  Routing Strategy: [Quality First ▼]                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Workflow ────────────────────────────────────────────┐  │
│  │  Approval Mode: [Manual ○] [Auto ○]                   │  │
│  │  Activity Timeout: [30] seconds                       │  │
│  │  Retry Count: [3]                                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Notifications ───────────────────────────────────────┐  │
│  │  [✓] Workflow Completed                               │  │
│  │  [✓] Approval Required                                │  │
│  │  [ ] Agent Failed                                     │  │
│  │  Webhook URL: [https://...]                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ About ───────────────────────────────────────────────┐  │
│  │  Version: v1.0.0                                      │  │
│  │  Backend: ● Connected                                 │  │
│  │  GitHub: github.com/.../dev-matrix                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Components

### SettingsSection
- Card container with title header
- Props: `title: string`, `description?: string`

### SettingItem
- Label + control row
- Supports: toggle, select, text input, number input
- Props: `label: string`, `type: 'toggle' | 'select' | 'text' | 'number'`, `modelValue`, `options?`

### SettingsPage
- Main page layout with save bar
- Manages form state and dirty tracking
- Save button enabled only when changes exist

## Data Model

```typescript
interface Settings {
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
```

## Storage Strategy

- All settings persisted to `localStorage` under key `devmatrix-settings`
- Loaded on app initialization
- Some settings (theme, language) applied immediately without save
- LLM/Workflow settings require explicit save with confirmation

## API Integration

- `GET /api/settings` — Load server-side defaults
- `POST /api/settings` — Save to server (optional, fallback to localStorage)

## Routes

- `/settings` — Main settings page
- Sidebar "Settings" nav item navigates to this route

## i18n Keys

```json
{
  "settings": {
    "title": "Settings",
    "save": "Save Changes",
    "saved": "Settings saved",
    "appearance": {
      "title": "Appearance",
      "theme": "Theme",
      "themeDark": "Dark",
      "themeLight": "Light",
      "language": "Language",
      "sidebar": "Sidebar Default",
      "sidebarExpanded": "Expanded",
      "sidebarCollapsed": "Collapsed"
    },
    "llm": {
      "title": "LLM Configuration",
      "provider": "Default Provider",
      "apiKey": "API Key",
      "show": "Show",
      "hide": "Hide",
      "model": "Model",
      "strategy": "Routing Strategy",
      "strategyQuality": "Quality First",
      "strategyCost": "Cost First",
      "strategyConfig": "Config Driven"
    },
    "workflow": {
      "title": "Workflow",
      "approvalMode": "Approval Mode",
      "approvalManual": "Manual",
      "approvalAuto": "Auto",
      "timeout": "Activity Timeout",
      "retryCount": "Retry Count"
    },
    "notifications": {
      "title": "Notifications",
      "workflowCompleted": "Workflow Completed",
      "approvalRequired": "Approval Required",
      "agentFailed": "Agent Failed",
      "webhookUrl": "Webhook URL"
    },
    "about": {
      "title": "About",
      "version": "Version",
      "backend": "Backend Status",
      "connected": "Connected",
      "disconnected": "Disconnected",
      "github": "GitHub"
    }
  }
}
```

## Implementation Notes

1. Use existing CSS variables for theming
2. Form controls styled to match dashboard cards
3. Save button fixed at top-right of page
4. Toast notification on successful save
5. API key field uses `type="password"` toggle
