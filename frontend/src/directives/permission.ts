import type { Directive } from 'vue'
import { useUserStore } from '../stores/user'

export const vPermission: Directive = {
  mounted(el, binding) {
    const userStore = useUserStore()
    const permission = binding.value as string

    if (!userStore.hasPermission(permission)) {
      el.style.display = 'none'
    }
  },
  updated(el, binding) {
    const userStore = useUserStore()
    const permission = binding.value as string

    if (userStore.hasPermission(permission)) {
      el.style.display = ''
    } else {
      el.style.display = 'none'
    }
  },
}
