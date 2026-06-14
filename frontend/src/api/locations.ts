import api from './index'
import type { Location } from '@/types'

export const locationsApi = {
  create(data: {
    station_id: number
    name: string
    grid_square?: string
    radio_model?: string
    antenna_model?: string
    antenna_height?: number
    qth?: string
  }): Promise<Location> {
    return api.post('/locations', data)
  },

  list(station_id?: number): Promise<Location[]> {
    const params: any = {}
    if (station_id) params.station_id = station_id
    return api.get('/locations', { params })
  },

  getActive(): Promise<Location> {
    return api.get('/locations/active/current')
  },

  activate(id: number): Promise<Location> {
    return api.post(`/locations/${id}/activate`)
  },

  update(id: number, data: any): Promise<Location> {
    return api.patch(`/locations/${id}`, data)
  },

  delete(id: number): Promise<any> {
    return api.delete(`/locations/${id}`)
  },
}
