/**
 * @file DevMatrix 前端路由配置
 * @description 定义应用路由表，包含页面路径、组件和元信息
 * @module router
 *
 * @example
 * ```ts
 * import router from './router'
 * app.use(router)
 * ```
 */

import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './components/Dashboard.vue'

/**
 * 路由配置数组
 * @type {Array<import('vue-router').RouteRecordRaw>}
 */
const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: Dashboard,
    meta: { title: 'Dashboard', icon: 'dashboard' },
  },
  {
    path: '/projects',
    name: 'projects',
    component: () => import('./pages/ProjectsPage.vue'),
    meta: { title: 'Projects', icon: 'projects' },
  },
  {
    path: '/projects/:id',
    name: 'project-detail',
    component: () => import('./pages/ProjectDetailPage.vue'),
    meta: { title: 'Project Detail', icon: 'projects' },
  },
  {
    path: '/agents',
    name: 'agents',
    component: () => import('./pages/AgentsPage.vue'),
    meta: { title: 'Agents', icon: 'agents' },
  },
  {
    path: '/skills',
    name: 'skills',
    component: () => import('./pages/SkillsPage.vue'),
    meta: { title: 'Skills', icon: 'skills' },
  },
  {
    path: '/workflow',
    name: 'workflow',
    redirect: '/workflow/list',
    meta: { title: 'Workflow', icon: 'workflow' },
    children: [
      {
        path: 'list',
        name: 'workflow-list',
        component: () => import('./pages/WorkflowListPage.vue'),
        meta: { title: 'Workflow List', icon: 'workflow-list' },
      },
      {
        path: 'editor/:id?',
        name: 'workflow-editor',
        component: () => import('./pages/WorkflowEditorPage.vue'),
        meta: { title: 'Workflow Editor', icon: 'workflow-editor' },
      },
      {
        path: 'instances',
        name: 'workflow-instances',
        component: () => import('./pages/WorkflowInstancePage.vue'),
        meta: { title: 'Workflow Instances', icon: 'workflow-instances' },
      },
    ],
  },
  {
    path: '/workbench',
    name: 'workbench',
    component: () => import('./pages/WorkbenchPage.vue'),
    meta: { title: 'Workbench', icon: 'workbench' },
  },
  {
    path: '/workbench/task/:id',
    name: 'task-detail',
    component: () => import('./pages/TaskDetailPage.vue'),
    meta: { title: 'Task Detail', icon: 'workbench', fullscreen: true },
  },
  {
    path: '/settings',
    name: 'settings',
    redirect: '/settings/system',
    meta: { title: 'Settings', icon: 'settings' },
    children: [
      {
        path: 'system',
        name: 'settings-system',
        component: () => import('./pages/settings/SystemSettingsPage.vue'),
        meta: { title: 'System Settings', icon: 'monitor' },
      },
      {
        path: 'llm',
        name: 'settings-llm',
        component: () => import('./pages/settings/LlmSettingsPage.vue'),
        meta: { title: 'LLM Settings', icon: 'brain-circuit' },
      },
      {
        path: 'database',
        name: 'settings-database',
        component: () => import('./pages/settings/DatabaseSettingsPage.vue'),
        meta: { title: 'Database Settings', icon: 'database' },
      },
      {
        path: 'security',
        name: 'settings-security',
        component: () => import('./pages/settings/SecuritySettingsPage.vue'),
        meta: { title: 'Security Settings', icon: 'shield' },
      },
      {
        path: 'about',
        name: 'settings-about',
        component: () => import('./pages/settings/AboutSettingsPage.vue'),
        meta: { title: 'About', icon: 'info' },
      },
    ],
  },
]

/**
 * Vue Router 实例
 * @type {import('vue-router').Router}
 */
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
