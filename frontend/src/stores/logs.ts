import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import type { QSOLog, Station } from '@/types'
import { logsApi } from '@/api/logs'
import { stationsApi } from '@/api/stations'
import { locationsApi } from '@/api/locations'

interface LogQueryParams {
  page: number
  page_size: number
  sort_by: string
  sort_order: string
  start_date?: string
  end_date?: string
  band?: string
  mode?: string
  call_sign?: string
  grid_square?: string
  dxcc?: string
  station_id?: number
}

interface LogFilters {
  start_date: string
  end_date: string
  band: string
  mode: string
  call_sign: string
  grid_square: string
  dxcc: string
  station_id: number | null
}

function getErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message
  if (typeof err === 'object' && err !== null && 'message' in err) return String((err as { message: unknown }).message)
  return 'Unknown error'
}

export const useLogsStore = defineStore('logs', () => {
  const logs = ref<QSOLog[]>([])
  const stations = ref<Station[]>([])
  const activeStation = ref<Station | null>(null)
  const pagination = reactive({
    page: 1, page_size: 20, total: 0, pages: 0
  })
  const sortBy = ref('qso_date')
  const sortOrder = ref('desc')
  const filters = reactive<LogFilters>({
    start_date: '', end_date: '', band: '', mode: '', call_sign: '', grid_square: '',
    dxcc: '',
    station_id: null,
  })
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  let _fetchRequestId = 0  // 请求 ID 守卫，防止旧响应覆盖新数据

  const buildParams = (): LogQueryParams => {
    const params: LogQueryParams = {
      page: pagination.page, page_size: pagination.page_size,
      sort_by: sortBy.value, sort_order: sortOrder.value,
    }
    if (filters.start_date) params.start_date = filters.start_date
    if (filters.end_date) params.end_date = filters.end_date
    if (filters.band) params.band = filters.band
    if (filters.mode) params.mode = filters.mode
    if (filters.call_sign) params.call_sign = filters.call_sign
    if (filters.grid_square) params.grid_square = filters.grid_square
    if (filters.dxcc) params.dxcc = filters.dxcc
    if (filters.station_id !== null) params.station_id = filters.station_id
    return params
  }

  const fetchLogs = async () => {
    const requestId = ++_fetchRequestId
    isLoading.value = true
    error.value = null
    try {
      const response = await logsApi.list(buildParams())
      // 仅当本次请求是最新的才更新数据（防止旧响应覆盖新数据）
      if (requestId !== _fetchRequestId) return
      logs.value = response.items
      pagination.total = response.total
      pagination.pages = response.pages
    } catch (err: unknown) {
      if (requestId !== _fetchRequestId) return
      error.value = getErrorMessage(err)
    } finally {
      if (requestId === _fetchRequestId) isLoading.value = false
    }
  }

  const fetchStations = async () => {
    try {
      stations.value = await stationsApi.list()
      try {
        const activeLoc = await locationsApi.getActive()
        if (activeLoc.station_id) {
          const match = stations.value.find(s => s.id === activeLoc.station_id)
          if (match) activeStation.value = match
        }
      } catch {
        if (stations.value.length > 0 && !activeStation.value) {
          activeStation.value = stations.value[0]
        }
      }
    } catch (err: unknown) {
      error.value = getErrorMessage(err)
    }
  }

  const refreshActiveStation = async () => {
    try {
      const activeLoc = await locationsApi.getActive()
      const match = stations.value.find(s => s.id === activeLoc.station_id)
      if (match) activeStation.value = match
    } catch { /* no active location */ }
  }

  const createLog = async (data: Partial<QSOLog>) => {
    try {
      const log = await logsApi.create(data)
      logs.value.unshift(log)
      return log
    } catch (err: unknown) {
      error.value = getErrorMessage(err)
      throw err
    }
  }

  const updateLog = async (id: number, data: Partial<QSOLog>) => {
    try {
      const updated = await logsApi.update(id, data)
      const index = logs.value.findIndex(log => log.id === id)
      if (index > -1) logs.value[index] = updated
      return updated
    } catch (err: unknown) {
      error.value = getErrorMessage(err)
      throw err
    }
  }

  const deleteLog = async (id: number) => {
    try {
      await logsApi.delete(id)
      logs.value = logs.value.filter(log => log.id !== id)
    } catch (err: unknown) {
      error.value = getErrorMessage(err)
      throw err
    }
  }

  const createStation = async (data: { callsign: string }) => {
    const station = await stationsApi.create(data)
    stations.value.push(station)
    return station
  }

  const clearFilters = () => {
    filters.start_date = ''; filters.end_date = ''
    filters.band = ''; filters.mode = ''; filters.call_sign = ''; filters.grid_square = ''
    filters.dxcc = ''
    filters.station_id = null
    pagination.page = 1
  }

  return {
    logs, stations, activeStation, pagination, sortBy, sortOrder, filters, isLoading, error,
    fetchLogs, fetchStations, refreshActiveStation,
    createLog, updateLog, deleteLog, createStation, clearFilters,
  }
})
