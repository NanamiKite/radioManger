import api from './index'
import type { Statistics, BandStatEntry, ModeStatEntry } from '@/types'

export const statsApi = {
  getOverview(station_id?: number): Promise<{
    data: Statistics
  }> {
    const params: any = {}
    if (station_id) params.station_id = station_id
    return api.get('/stats/overview', { params })
  },

  getBandMode(): Promise<{
    data: { bands: BandStatEntry[]; modes: ModeStatEntry[] }
  }> {
    return api.get('/stats/band-mode')
  }
}
