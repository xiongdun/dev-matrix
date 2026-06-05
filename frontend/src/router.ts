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
import { useUserStore } from './stores/user'
import Dashboard from './components/Dashboard.vue'

/**
 * 路由配置数组
 * @type {Array<import('vue-router').RouteRecordRaw>}
 */
const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('./pages/LoginPage.vue'),
    meta: { public: true, fullscreen: true },
  },
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
    path: '/scheduled-tasks',
    name: 'scheduled-tasks',
    component: () => import('./pages/ScheduledTasksPage.vue'),
    meta: { title: 'Scheduled Tasks', icon: 'clock' },
  },
  {
    path: '/workbench/task/:id',
    name: 'task-detail',
    component: () => import('./pages/TaskDetailPage.vue'),
    meta: { title: 'Task Detail', icon: 'workbench', fullscreen: true },
  },
  {
    path: '/tasks',
    name: 'tasks',
    redirect: '/tasks/my',
    meta: { title: 'Task Management', icon: 'kanban-square' },
    children: [
      {
        path: 'my',
        name: 'my-tasks',
        component: () => import('./pages/tasks/MyTasksPage.vue'),
        meta: { title: 'My Tasks', icon: 'list-todo' },
      },
      {
        path: 'board',
        name: 'task-board',
        component: () => import('./pages/tasks/TaskBoardPage.vue'),
        meta: { title: 'Task Board', icon: 'kanban-square' },
      },
    ],
  },
  {
    path: '/code-reviews',
    name: 'CodeReviewList',
    component: () => import('./pages/CodeReviewListPage.vue'),
    meta: { title: '代码审查' }
  },
  {
    path: '/code-reviews/:id',
    name: 'CodeReviewDetail',
    component: () => import('./pages/CodeReviewPage.vue'),
    meta: { title: '审查详情' }
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
  {
    path: '/users',
    name: 'users',
    component: () => import('./pages/users/UserListPage.vue'),
    meta: { title: 'User Management', icon: 'users', permission: 'user:manage' },
  },
  {
    path: '/users/:id',
    name: 'user-detail',
    component: () => import('./pages/users/UserDetailPage.vue'),
    meta: { title: 'User Detail', icon: 'user', permission: 'user:manage' },
  },
  {
    path: '/roles',
    name: 'roles',
    component: () => import('./pages/roles/RoleListPage.vue'),
    meta: { title: 'Role Management', icon: 'user-cog', permission: 'role:manage' },
  },
  {
    path: '/menus',
    name: 'menus',
    component: () => import('./pages/menus/MenuListPage.vue'),
    meta: { title: 'Menu Management', icon: 'menu', permission: 'menu:manage' },
  },
  {
    path: '/forbidden',
    name: 'forbidden',
    component: () => import('./pages/ForbiddenPage.vue'),
    meta: { public: true, fullscreen: true },
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

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.public) {
    next()
    return
  }

  if (!token) {
    next('/login')
    return
  }

  // 权限检查
  const requiredPermission = to.meta.permission as string | undefined
  if (requiredPermission) {
    const userStore = useUserStore()
    // 确保用户信息已加载
    if (!userStore.userInfo) {
      // 异步获取用户信息后再检查权限
      import('./api/auth').then(({ authApi }) => {
        authApi.getMe()
          .then((userInfo) => {
            userStore.setUserInfo(userInfo)
            if (userStore.hasPermission(requiredPermission)) {
              next()
            } else {
              next('/forbidden')
            }
          })
          .catch(() => {
            userStore.clearToken()
            next('/login')
          })
      })
      return
    }

    if (!userStore.hasPermission(requiredPermission)) {
      next('/forbidden')
      return
    }
  }

  next()
})

export default router
