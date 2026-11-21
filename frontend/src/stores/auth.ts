import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { storage } from '@/utils/storage'
import type { User } from '@/types'
import { authApi } from '@/api/auth'
import { fetchHealth } from '@/api/health'
import { isAxiosError } from 'axios'

interface RegisterData {
  username: string
  email: string
  password: string
  confirm_password: string
  full_name?: string
  timezone?: string
  language?: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(storage.getUser())
  const token = ref<string | null>(storage.getToken())
  const isAuthenticated = computed(() => !!token.value)
  const dbMode = ref<string>('unknown')

  /** 获取数据库模式（用于判断是否为服务器部署） */
  const fetchDbMode = async () => {
    try {
      const res = await fetchHealth()
      dbMode.value = res.database
    } catch {
      dbMode.value = 'unknown'
    }
  }

  const register = async (data: RegisterData) => {
    const response = await authApi.register(data)
    return response
  }

  const login = async (username: string, password: string) => {
    const response = await authApi.login({ username, password })
    token.value = response.access_token
    user.value = response.user
    storage.setToken(response.access_token)
    storage.setUser(response.user)
    await fetchDbMode()
    return response
  }

  const clearSession = () => {
    token.value = null
    user.value = null
    storage.clear()
    window.location.replace('/login')
  }

  let loggingOut = false
  const logout = async () => {
    if (loggingOut) return
    loggingOut = true
    try {
      if (token.value) {
        try {
          await authApi.logout()
        } catch (error: unknown) {
          if (!isAxiosError(error) || error.response?.status !== 401) throw error
        }
      }
      clearSession()
    } finally {
      loggingOut = false
    }
  }

  const getCurrentUser = async () => {
    const response = await authApi.getMe()
    user.value = response
    storage.setUser(response)
    return response
  }

  return {
    user, token, isAuthenticated, dbMode,
    register, login, logout, clearSession, getCurrentUser, fetchDbMode,
  }
})
