import api from './index'
import type { Station } from '@/types'

export const stationsApi = {
  create(data: { callsign: string }): Promise<Station> {
    return api.post('/stations', data)
  },

  list(): Promise<Station[]> {
    return api.get('/stations')
  },

  get(id: number): Promise<Station> {
    return api.get(`/stations/${id}`)
  },

  update(id: number, data: { callsign?: string }): Promise<Station> {
    return api.patch(`/stations/${id}`, data)
  },

  delete(id: number): Promise<any> {
    return api.delete(`/stations/${id}`)
  },
}
