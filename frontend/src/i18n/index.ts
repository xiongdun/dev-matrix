import { createI18n } from 'vue-i18n'
import zh from './locales/zh.json'
import en from './locales/en.json'

const savedLang = (() => {
  try {
    const stored = localStorage.getItem('devmatrix-settings')
    if (stored) return JSON.parse(stored).language
  } catch {}
  return 'zh'
})()

const i18n = createI18n({
  legacy: false,
  locale: savedLang || 'zh',
  fallbackLocale: 'en',
  messages: { zh, en },
})

export default i18n
