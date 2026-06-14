import api from './index'
import type { CallsignInfo } from '@/types'

export const callsignsApi = {
  lookup(call_sign: string): Promise<CallsignInfo> {
    return api.get(`/callsigns/${call_sign}`)
  },

  batchQuery(call_signs: string[]): Promise<{
    results: CallsignInfo[]
    found: number
    not_found: number
  }> {
    return api.post('/callsigns/batch-query', { call_signs })
  },

  search(prefix: string, country?: string): Promise<{ results: CallsignInfo[] }> {
    const params: any = {}
    if (country) params.country = country
    return api.get(`/callsigns/search/${prefix}`, { params })
  },

  clearCache(call_sign: string): Promise<void> {
    return api.delete(`/callsigns/cache/${call_sign}`)
  }
}
