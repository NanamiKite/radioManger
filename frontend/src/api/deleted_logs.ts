import api from './index'
import type { QSOLog } from '@/types'

export interface DeletedLogItem {
  id: number
  log_id?: number
  call_sign?: string
  qso_date?: string
  band?: string
  mode?: string
  dxcc?: string
  delete_reason?: string
  deleted_at?: string
  expires_at?: string
  days_remaining?: number
}

export const recycleApi = {
  list(params: {
    page?: number
    page_size?: number
  }): Promise<{
    items: DeletedLogItem[]
    total: number
    page: number
    page_size: number
    pages: number
  }> {
    return api.get('/logs/recycle/list', { params })
  },

  restore(deleted_id: number): Promise<QSOLog> {
    return api.post(`/logs/recycle/${deleted_id}/restore`)
  }
}
