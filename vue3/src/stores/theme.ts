import { defineStore } from 'pinia'
import { ref } from 'vue'

export type Theme = 'light' | 'dark'

export const useThemeStore = defineStore('theme', () => {
  const theme = ref<Theme>('light')

  const initTheme = () => {
    // 检查 localStorage 或系统偏好
    const savedTheme = localStorage.getItem('theme') as Theme | null
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches

    if (savedTheme) {
      theme.value = savedTheme
    } else if (systemPrefersDark) {
      theme.value = 'dark'
    } else {
      // 默认使用深色模式
      theme.value = 'dark'
    }

    applyTheme(theme.value)
  }

  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme
    localStorage.setItem('theme', newTheme)
    applyTheme(newTheme)
  }

  const toggleTheme = () => {
    setTheme(theme.value === 'light' ? 'dark' : 'light')
  }

  const applyTheme = (themeValue: Theme) => {
    document.documentElement.setAttribute('data-theme', themeValue)
  }

  // 监听系统主题变化
  const watchSystemTheme = () => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', (e) => {
      if (!localStorage.getItem('theme')) {
        setTheme(e.matches ? 'dark' : 'light')
      }
    })
  }

  return {
    theme,
    initTheme,
    setTheme,
    toggleTheme,
    watchSystemTheme
  }
})

