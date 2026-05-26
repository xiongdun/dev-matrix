import { ref } from 'vue'

export interface ErrorToast {
  id: number
  message: string
  type: 'error' | 'warning' | 'info'
  duration: number
}

const toasts = ref<ErrorToast[]>([])
let toastId = 0

export function useErrorHandler() {
  function showError(message: string, duration = 5000) {
    const id = ++toastId
    toasts.value.push({ id, message, type: 'error', duration })
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  function showWarning(message: string, duration = 4000) {
    const id = ++toastId
    toasts.value.push({ id, message, type: 'warning', duration })
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  function showInfo(message: string, duration = 3000) {
    const id = ++toastId
    toasts.value.push({ id, message, type: 'info', duration })
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  function removeToast(id: number) {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  function handleApiError(error: Error): string {
    const msg = error.message || String(error)

    // 网络错误
    if (msg.includes('timeout') || msg.includes('AbortError')) {
      return '请求超时，请检查网络连接后重试'
    }
    if (msg.includes('NetworkError') || msg.includes('fetch')) {
      return '网络连接失败，请检查网络后重试'
    }

    // HTTP 状态码错误
    if (msg.includes('API Error 401')) {
      return '登录已过期，请重新登录'
    }
    if (msg.includes('API Error 403')) {
      return '没有权限执行此操作'
    }
    if (msg.includes('API Error 404')) {
      return '请求的资源不存在'
    }
    if (msg.includes('API Error 429')) {
      return '请求过于频繁，请稍后再试'
    }
    if (msg.includes('API Error 5')) {
      return '服务器内部错误，请稍后再试'
    }

    // 默认错误
    return '操作失败，请稍后重试'
  }

  return {
    toasts,
    showError,
    showWarning,
    showInfo,
    removeToast,
    handleApiError,
  }
}
