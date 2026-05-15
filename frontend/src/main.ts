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
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import './style.css'

/**
 * 创建 Vue 应用实例
 * @returns {import('vue').App} Vue 应用实例
 */
const app = createApp(App)

// 注册路由
app.use(router)
// 注册国际化
app.use(i18n)

// 挂载到 DOM
app.mount('#app')
