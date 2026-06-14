import api from './index'
import { useAuthStore } from '@/stores/auth'
import type { QSOLog } from '@/types'

export const logsApi = {
  create(data: any): Promise<QSOLog> {
    return api.post('/logs', data)
  },

  list(params: {
    page?: number
    page_size?: number
    sort_by?: string
    sort_order?: string
    start_date?: string
    end_date?: string
    band?: string
    mode?: string
    call_sign?: string
    station_id?: number | null
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
  },

  importLogs(file: File, station_id?: number): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    const params: any = {}
    if (station_id) params.station_id = station_id
    return api.post('/logs/import', formData, { params })
  },

  exportLogs(params: {
    format?: string
    start_date?: string
    end_date?: string
    band?: string
    station_id?: number | null
  }): void {
    const authStore = useAuthStore()
    const token = authStore.token
    const query = new URLSearchParams()
    query.set('format', params.format || 'adi')
    if (params.start_date) query.set('start_date', params.start_date)
    if (params.end_date) query.set('end_date', params.end_date)
    if (params.band) query.set('band', params.band)
    if (params.station_id) query.set('station_id', String(params.station_id))

    fetch(`/api/v1/logs/export?${query.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => {
        const disposition = res.headers.get('Content-Disposition') || ''
        const match = disposition.match(/filename="?(.+?)"?$/)
        const filename = match ? match[1] : 'logs_export.adi'
        return res.blob().then(blob => ({ blob, filename }))
      })
      .then(({ blob, filename }) => {
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
      })
  },
}
