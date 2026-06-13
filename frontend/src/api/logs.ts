import api from './index'
import type { QSOLog } from '@/types'

export const logsApi = {
  create(data: any): Promise<QSOLog> {
    return api.post('/logs', data)
  },

  list(params: {
    page?: number
    page_size?: number
    start_date?: string
    end_date?: string
    band?: string
    mode?: string
    call_sign?: string
  }): Promise<{
    items: QSOLog[]
    total: number
    page: number
    page_size: number
    pages: number
  }> {
    return api.get('/logs', { params })
  },

  get(id: number): Promise<QSOLog> {
    return api.get(`/logs/${id}`)
  },

  update(id: number, data: any): Promise<QSOLog> {
    return api.patch(`/logs/${id}`, data)
  },

  delete(id: number): Promise<any> {
    return api.delete(`/logs/${id}`)
  },

  getStats(): Promise<any> {
    return api.get('/logs/stats/overview')
  }
}
