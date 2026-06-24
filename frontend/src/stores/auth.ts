import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { storage } from '@/utils/storage'
import type { User } from '@/types'
import { authApi } from '@/api/auth'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(storage.getUser())
  const token = ref<string | null>(storage.getToken())
  const isAuthenticated = computed(() => !!token.value)
  const dbMode = ref<string>('sqlite')

  /** 获取数据库模式（用于判断是否为服务器部署） */
  const fetchDbMode = async () => {
    try {
      const res = await axios.get('/health')
      dbMode.value = res.data?.database || 'sqlite'
    } catch {
      dbMode.value = 'sqlite'
    }
  }

  const register = async (data: any) => {
    const response = await authApi.register(data)
    return response
  }

  const login = async (username: string, password: string) => {
    const response = await authApi.login({ username, password })
    token.value = response.access_token
    user.value = response.user
    storage.setToken(response.access_token)
    storage.setUser(response.user)
    return response
  }

  const logout = async () => {
    // 服务器模式下调用后端 logout 使 token 失效
    if (dbMode.value === 'mysql' && token.value) {
      try {
        await authApi.logout()
      } catch { /* 忽略错误，本地仍然清理 */ }
    }
    token.value = null
    user.value = null
    storage.clear()
    // 强制跳转登录页并刷新以清除所有Pinia状态
    window.location.href = '/login'
  }

  const getCurrentUser = async () => {
    try {
      const response = await authApi.getMe()
      user.value = response
      storage.setUser(response)
      return response
    } catch (error) {
      logout()
      throw error
    }
  }

  return {
    user, token, isAuthenticated, dbMode,
    register, login, logout, getCurrentUser, fetchDbMode,
  }
})
