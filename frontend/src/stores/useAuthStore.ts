import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'
import { authStorage } from '@/utils/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as any,
    token: authStorage.getToken(),
    refreshToken: authStorage.getRefreshToken()
  }),

  getters: {
    isAuthenticated: (state) => !!state.token
  },

  actions: {
    async login(data: any) {
      const res = await authApi.login(data)

      this.token = res.access_token
      this.refreshToken = res.refresh_token
      this.user = res.user

      authStorage.setToken(res.access_token)
      authStorage.setRefreshToken(res.refresh_token)

      router.push('/dashboard')
    },

    async fetchMe() {
      const user = await authApi.getMe()
      this.user = user
      return user
    },

    logout() {
      this.user = null
      this.token = null
      this.refreshToken = null

      authStorage.clear()

      router.push('/login')

      // 可选：强制刷新（避免旧状态残留）
      window.location.reload()
    }
  }
})