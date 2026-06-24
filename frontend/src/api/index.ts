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
    const url = error.config?.url || ''

    // ECONNREFUSED / Network Error → 后端未启动
    if (!error.response && error.code === 'ERR_NETWORK') {
      (error as Record<string, unknown>).backend_down = true
    }

    // 只在非认证接口的 401 时自动登出
    if (
      error.response?.status === 401 &&
      !url.startsWith('/auth/login') &&
      !url.startsWith('/auth/register')
    ) {
      const authStore = useAuthStore()
      authStore.logout()
    }
    return Promise.reject(error)
  }
)

export default api
