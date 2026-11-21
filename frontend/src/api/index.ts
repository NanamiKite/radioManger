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
  (error: AxiosError<{ detail?: unknown; message?: string }>) => {
    const url = error.config?.url || ''
    const body = error.response?.data
    if (body && typeof body === 'object') {
      if (Array.isArray(body.detail)) {
        body.detail = [...new Set(body.detail.map(item =>
          item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string' ? item.msg : ''
        ).filter(Boolean))].join('; ')
      } else if (body.message && body.detail === undefined) body.detail = body.message
    }

    // ECONNREFUSED / Network Error → 后端未启动
    if (!error.response && error.code === 'ERR_NETWORK') {
      Object.assign(error, { backend_down: true })
    }

    // 只在非认证接口的 401 时自动登出
    if (
      error.response?.status === 401 &&
      !url.startsWith('/auth/login') &&
      !url.startsWith('/auth/register') &&
      !url.startsWith('/auth/logout') &&
      !url.startsWith('/auth/change-password') &&
      !url.startsWith('/auth/delete-account')
    ) {
      const authStore = useAuthStore()
      authStore.clearSession()
    }
    return Promise.reject(error)
  }
)

export default api
