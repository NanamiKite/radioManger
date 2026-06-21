import api from './index'

export interface GridData {
  grid: string
  count: number
  confirmed: number
  lat: number
  lon: number
}

export interface MapGridsResponse {
  my_grid: string | null
  my_lat: number | null
  my_lon: number | null
  grids: GridData[]
}

export const mapApi = {
  getGrids(): Promise<MapGridsResponse> {
    return api.get('/map/grids')
  }
}
