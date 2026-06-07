import { ref } from 'vue'

interface ConfirmOptions {
  title?: string
  message: string
  type?: 'confirm' | 'warning' | 'info' | 'success'
  confirmText?: string
  cancelText?: string
  showCancel?: boolean
}

interface PromptOptions {
  title?: string
  message?: string
  placeholder?: string
  defaultValue?: string
  confirmText?: string
  cancelText?: string
}

const confirmState = ref({
  visible: false,
  title: '',
  message: '',
  type: 'confirm' as 'confirm' | 'warning' | 'info' | 'success',
  confirmText: '确认',
  cancelText: '取消',
  showCancel: true,
})

const promptState = ref({
  visible: false,
  title: '',
  message: '',
  placeholder: '',
  defaultValue: '',
  confirmText: '确认',
  cancelText: '取消',
})

let confirmResolve: ((value: boolean) => void) | null = null
let promptResolve: ((value: string | null) => void) | null = null

// 模块加载时强制重置，防止状态残留
confirmState.value.visible = false
promptState.value.visible = false

export function useDialog() {
  function showConfirm(options: ConfirmOptions): Promise<boolean> {
    confirmState.value = {
      visible: true,
      title: options.title || '确认',
      message: options.message,
      type: options.type || 'confirm',
      confirmText: options.confirmText || '确认',
      cancelText: options.cancelText || '取消',
      showCancel: options.showCancel !== false,
    }
    return new Promise((resolve) => {
      confirmResolve = resolve
    })
  }

  function showPrompt(options: PromptOptions): Promise<string | null> {
    promptState.value = {
      visible: true,
      title: options.title || '输入',
      message: options.message || '',
      placeholder: options.placeholder || '',
      defaultValue: options.defaultValue || '',
      confirmText: options.confirmText || '确认',
      cancelText: options.cancelText || '取消',
    }
    return new Promise((resolve) => {
      promptResolve = resolve
    })
  }

  function confirmResult(result: boolean) {
    confirmState.value.visible = false
    confirmResolve?.(result)
    confirmResolve = null
  }

  function promptResult(result: string | null) {
    promptState.value.visible = false
    promptResolve?.(result)
    promptResolve = null
  }

  // 强制关闭所有弹窗（紧急重置）
  function forceCloseAll() {
    confirmState.value.visible = false
    promptState.value.visible = false
    confirmResolve?.(false)
    promptResolve?.(null)
    confirmResolve = null
    promptResolve = null
  }

  return {
    confirmState,
    promptState,
    showConfirm,
    showPrompt,
    confirmResult,
    promptResult,
    forceCloseAll,
  }
}
