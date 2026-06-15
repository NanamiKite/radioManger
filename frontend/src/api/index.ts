import axios, { AxiosInstance, AxiosError } from 'axios'
import { useAuthStore } from '@/stores/auth'


const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
    }
    return Promise.reject(error)
  }
)

export default api

// import { logsApiLocal } from './local/logs'
// import { logsApiHttp } from './http/logs'

// const mode = import.meta.env.VITE_MODE

// function pickAPI() {
//   switch (mode) {
//     case 'local':
//       console.log('[RadioManager] LOCAL mode')
//       return {
//         logs: logsApiLocal
//       }

//     case 'lan':
//     case 'cloud':
//       console.log('[RadioManager] HTTP mode:', mode)
//       return {
//         logs: logsApiHttp
//       }

//     default:
//       throw new Error('Unknown VITE_MODE: ' + mode)
//   }
// }

// export const api = pickAPI()
