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
    component: () => import('./pages/SettingsPage.vue'),
    meta: { title: 'Settings', icon: 'settings' },
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
