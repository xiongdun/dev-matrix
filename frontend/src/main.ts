/**
 * @file DevMatrix 前端应用入口文件
 * @description 初始化 Vue 应用，配置全局插件（Vue Router、i18n），挂载根组件
 * @module main
 *
 * @example
 * ```ts
 * // 开发环境启动
 * npm run dev
 *
 * // 生产构建
 * npm run build
 * ```
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import { vPermission } from './directives/permission'
import './style.css'

;(function initTheme() {
  try {
    const raw = localStorage.getItem('devmatrix-settings')
    const theme = raw ? JSON.parse(raw).theme : 'auto'
    const resolved = theme === 'auto'
      ? window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
      : theme
    document.documentElement.setAttribute('data-theme', resolved)
  } catch {
    document.documentElement.setAttribute('data-theme', 'dark')
  }
})()

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(i18n)
app.directive('permission', vPermission)

app.mount('#app')
