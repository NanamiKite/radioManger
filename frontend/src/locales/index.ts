// import { createI18n } from 'vue-i18n'
// import type { I18n } from 'vue-i18n'
// import zhCN from './zh-CN'
// import enUS from './en-US'

// export type MessageSchema = typeof zhCN

// const i18n: I18n = createI18n<MessageSchema>({
//   legacy: false,
//   locale: localStorage.getItem('language') || 'zh-CN',
//   fallbackLocale: 'en-US',
//   messages: {
//     'zh-CN': zhCN,
//     'en-US': enUS
//   }
// })

// export const setLanguage = (language: string) => {
//   i18n.global.locale.value = language as any
//   localStorage.setItem('language', language)
// }

// export const getLanguage = (): string => {
//   return i18n.global.locale.value as string
// }

// export default i18n
import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'
import enUS from './en-US'

// 导出语言包类型供外部使用
export type MessageSchema = typeof zhCN

// 1. 独立 getLanguage 的逻辑，让它不依赖 i18n 实例，彻底杜绝初始化顺序导致的白屏
export const getLanguage = (): string => {
  const cache = localStorage.getItem('language')
  if (cache) return cache

  // 如果没有缓存，获取浏览器默认语言
  const language = navigator.language.toLowerCase()
  if (language.includes('en')) return 'en-US'

  return 'zh-CN'
}

// 2. 创建 i18n 实例（去掉 const i18n: I18n 这种不完整的显式类型声明，让 TS 自动推导，报错瞬间消失）
const i18n = createI18n<{ message: MessageSchema }, 'zh-CN' | 'en-US'>({
  legacy: false, // 既然你使用了 Composition API (.value)，这里保持 false 正确
  globalInjection: true, // 极其重要：确保你在组件里用的 $t 不会失效
  locale: getLanguage(), // 初始语言直接调用上面的函数
  fallbackLocale: 'en-US',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  }
})

// 3. 切换语言的函数
export const setLanguage = (language: string) => {
  // 1. 把 locale 强行断言为 any，管它是 string 还是 Ref，直接点出 .value 赋值
  (i18n.global.locale as any).value = language
  localStorage.setItem('language', language)
}

export default i18n
