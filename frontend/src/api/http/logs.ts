import http from '../http'
import type { QSOLog } from '@/types'

export const logsApiHttp = {
  create(data: any): Promise<QSOLog> {
    return http.post('/logs', data)
  },

  list(params: any): Promise<any> {
    return http.get('/logs', { params })
  },

  get(id: number): Promise<QSOLog> {
    return http.get(`/logs/${id}`)
  },

  update(id: number, data: any): Promise<QSOLog> {
    return http.patch(`/logs/${id}`, data)
  },

  delete(id: number): Promise<any> {
    return http.delete(`/logs/${id}`)
  },

  getStats(): Promise<any> {
    return http.get('/logs/stats/overview')
  }
}