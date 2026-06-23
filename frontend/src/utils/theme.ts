import { ref, watch, onMounted } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'

const THEME_KEY = 'radiomanager-theme'

// 响应式的当前主题状态
const themeMode = ref<ThemeMode>('light')
const isDark = ref(false)

// 检测系统主题偏好
function getSystemTheme(): 'light' | 'dark' {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return 'light'
}

// 应用主题到 DOM
function applyTheme(dark: boolean) {
  const root = document.documentElement
  if (dark) {
    root.classList.add('dark')
    root.setAttribute('data-theme', 'dark')
  } else {
    root.classList.remove('dark')
    root.setAttribute('data-theme', 'light')
  }
  isDark.value = dark
}

// 切换主题
function toggleTheme() {
  const modes: ThemeMode[] = ['light', 'dark', 'system']
  const currentIndex = modes.indexOf(themeMode.value)
  const nextIndex = (currentIndex + 1) % modes.length
  themeMode.value = modes[nextIndex]
  saveTheme(themeMode.value)
  updateTheme()
}

// 设置特定主题
function setTheme(mode: ThemeMode) {
  themeMode.value = mode
  saveTheme(mode)
  updateTheme()
}

// 更新主题
function updateTheme() {
  let dark = false
  switch (themeMode.value) {
    case 'dark':
      dark = true
      break
    case 'system':
      dark = getSystemTheme() === 'dark'
      break
    case 'light':
    default:
      dark = false
      break
  }
  applyTheme(dark)
}

// 保存主题到本地存储
function saveTheme(mode: ThemeMode) {
  try {
    localStorage.setItem(THEME_KEY, mode)
  } catch (e) {
    console.warn('Failed to save theme preference:', e)
  }
}

// 从本地存储加载主题
function loadTheme(): ThemeMode {
  try {
    const saved = localStorage.getItem(THEME_KEY)
    if (saved && ['light', 'dark', 'system'].includes(saved)) {
      return saved as ThemeMode
    }
  } catch (e) {
    console.warn('Failed to load theme preference:', e)
  }
  return 'light'
}

// 监听系统主题变化
function watchSystemTheme() {
  if (typeof window !== 'undefined' && window.matchMedia) {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', () => {
      if (themeMode.value === 'system') {
        updateTheme()
      }
    })
  }
}

// 获取主题图标（Unicode 符号，非 emoji）
function getThemeIcon(mode: ThemeMode): string {
  switch (mode) {
    case 'light':
      return '\u25CB'   // ○ 空心圆（浅色）
    case 'dark':
      return '\u25CF'   // ● 实心圆（深色）
    case 'system':
      return '\u25D0'   // ◐ 半圆（跟随系统）
    default:
      return '\u25CB'
  }
}

// 获取主题标签
function getThemeLabel(mode: ThemeMode): string {
  switch (mode) {
    case 'light':
      return '浅色模式'
    case 'dark':
      return '深色模式'
    case 'system':
      return '跟随系统'
    default:
      return '浅色模式'
  }
}

// 组合式函数
export function useTheme() {
  onMounted(() => {
    themeMode.value = loadTheme()
    updateTheme()
    watchSystemTheme()
  })

  return {
    themeMode,
    isDark,
    toggleTheme,
    setTheme,
    getThemeIcon,
    getThemeLabel
  }
}
