import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from './components/Dashboard.vue'
import SettingsPage from './pages/SettingsPage.vue'
import AgentsPage from './pages/AgentsPage.vue'
import SkillsPage from './pages/SkillsPage.vue'

const routes = [
  { path: '/', component: Dashboard },
  { path: '/settings', component: SettingsPage },
  { path: '/agents', component: AgentsPage },
  { path: '/skills', component: SkillsPage },
]

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
})
