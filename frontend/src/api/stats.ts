import api from './index'
import type { Statistics, BandStatEntry, ModeStatEntry } from '@/types'

export interface DxccChartBandData {
  count: number
  confirmed: boolean
}

export interface DxccChartEntity {
  entity: string
  total: number
  bands: Record<string, DxccChartBandData | null>
}

export interface DxccChartData {
  bands: string[]
  entities: DxccChartEntity[]
  band_confirmed: Record<string, number>
  band_worked: Record<string, number>
  total_entities: number
}

export interface BandModeMatrixEntry {
  band: string
  mode: string
  count: number
}

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
  },

  getDxcc(): Promise<{
    data: { total_dxcc: number; dxcc_list: { entity: string; count: number }[] }
  }> {
    return api.get('/stats/dxcc')
  },

  getDxccChart(): Promise<{
    data: DxccChartData
  }> {
    return api.get('/stats/dxcc-chart')
  },

  getBandModeMatrix(): Promise<{
    data: BandModeMatrixEntry[]
  }> {
    return api.get('/stats/band-mode-matrix')
  }
}
