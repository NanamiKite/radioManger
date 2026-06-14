// import { defineStore } from 'pinia'
// import { ref, computed } from 'vue'
// import { storage } from '@/utils/storage'
// import type { User } from '@/types'
// import { authApi } from '@/api/auth'

// export const useAuthStore = defineStore('auth', () => {
//   const user = ref<User | null>(storage.getUser())
//   const token = ref<string | null>(storage.getToken())
//   const isAuthenticated = computed(() => !!token.value)

//   const register = async (data: any) => {
//     const response = await authApi.register(data)
//     return response
//   }

//   const login = async (username: string, password: string) => {
//     const response = await authApi.login({
//       username,
//       password
//     })

//     token.value = response.access_token
//     user.value = response.user

//     storage.setToken(response.access_token)
//     storage.setUser(response.user)

//     return response
//   }

//   const logout = () => {
//     token.value = null
//     user.value = null
//     storage.clear()
//   }

//   const getCurrentUser = async () => {
//     try {
//       const response = await authApi.getMe()
//       user.value = response
//       storage.setUser(response)
//       return response
//     } catch (error) {
//       logout()
//       throw error
//     }
//   }

//   return {
//     user,
//     token,
//     isAuthenticated,
//     register,
//     login,
//     logout,
//     getCurrentUser
//   }
// })
import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as any,
    token: localStorage.getItem('access_token')
  }),

  getters: {
    isAuthenticated: (state) => !!state.token
  },

  actions: {
    async login(username: string, password: string) {
      const res = await authApi.login({ username, password })

      this.token = res.access_token
      this.user = res.user

      localStorage.setItem('access_token', res.access_token)
      localStorage.setItem('refresh_token', res.refresh_token)
    },

    async fetchMe() {
      try {
        const user = await authApi.getMe()
        this.user = user
      } catch (e) {
        this.logout()
      }
    },

    logout() {
      this.user = null
      this.token = null

      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')

      window.location.href = '/login'
    }
  }
})