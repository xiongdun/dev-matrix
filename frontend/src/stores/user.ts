import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface UserInfo {
  id: number
  username: string
  nickname: string | null
  email: string | null
  avatar: string | null
  roles: Array<{ id: number; name: string; display_name: string }>
  permissions: string[]
  agents: string[]
}

export const useUserStore = defineStore(
  'user',
  () => {
    const token = ref<string>(localStorage.getItem('token') || '')
    const userInfo = ref<UserInfo | null>(null)
    const menus = ref<any[]>([])

    const isLoggedIn = computed(() => !!token.value)
    const hasPermission = computed(() => (perm: string) => {
      if (!userInfo.value) return false
      return userInfo.value.permissions.includes(perm)
    })
    const hasAgent = computed(() => (agentName: string) => {
      if (!userInfo.value) return false
      return userInfo.value.agents.includes(agentName)
    })

    function setToken(newToken: string) {
      token.value = newToken
      localStorage.setItem('token', newToken)
    }

    function clearToken() {
      token.value = ''
      userInfo.value = null
      menus.value = []
      localStorage.removeItem('token')
    }

    function setUserInfo(info: UserInfo) {
      userInfo.value = info
    }

    function setMenus(newMenus: any[]) {
      menus.value = newMenus
    }

    return {
      token,
      userInfo,
      menus,
      isLoggedIn,
      hasPermission,
      hasAgent,
      setToken,
      clearToken,
      setUserInfo,
      setMenus,
    }
  },
  {
    persist: {
      key: 'devmatrix-user',
      paths: ['userInfo', 'menus'],
      storage: localStorage,
    },
  }
)
