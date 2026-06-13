import api from './index'
import type { Statistics } from '@/types'

export const statsApi = {
  getOverview(): Promise<{
    data: Statistics
  }> {
    return api.get('/stats/overview')
  }
}
