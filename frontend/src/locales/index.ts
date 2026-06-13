import { createI18n } from 'vue-i18n'
import type { I18n } from 'vue-i18n'
import zhCN from './zh-CN'
import enUS from './en-US'

export type MessageSchema = typeof zhCN

const i18n: I18n = createI18n<MessageSchema>({
  legacy: false,
  locale: localStorage.getItem('language') || 'zh-CN',
  fallbackLocale: 'en-US',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  }
})

export const setLanguage = (language: string) => {
  i18n.global.locale.value = language as any
  localStorage.setItem('language', language)
}

export const getLanguage = (): string => {
  return i18n.global.locale.value as string
}

export default i18n
