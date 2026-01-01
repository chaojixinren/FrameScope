import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface User {
  id: string
  username: string
  email?: string
}

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const isAuthenticated = ref(false)

  const setUser = (userData: User) => {
    user.value = userData
    isAuthenticated.value = true
  }

  const setToken = (tokenValue: string) => {
    token.value = tokenValue
    // 持久化存储
    if (tokenValue) {
      localStorage.setItem('token', tokenValue)
    } else {
      localStorage.removeItem('token')
    }
  }

  const logout = () => {
    user.value = null
    token.value = null
    isAuthenticated.value = false
    localStorage.removeItem('token')
  }

  const initAuth = () => {
    // 从 localStorage 恢复 token
    const savedToken = localStorage.getItem('token')
    if (savedToken) {
      token.value = savedToken
      isAuthenticated.value = true
      // 这里可以调用 API 获取用户信息
      // 目前先模拟
      user.value = {
        id: '1',
        username: 'user'
      }
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    setUser,
    setToken,
    logout,
    initAuth
  }
})

