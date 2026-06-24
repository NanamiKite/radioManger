import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import type { QSOLog, Station } from '@/types'
import { logsApi } from '@/api/logs'
import { stationsApi } from '@/api/stations'
import { locationsApi } from '@/api/locations'

export const useLogsStore = defineStore('logs', () => {
  const logs = ref<QSOLog[]>([])
  const stations = ref<Station[]>([])
  const activeStation = ref<Station | null>(null)
  const pagination = reactive({
    page: 1, page_size: 20, total: 0, pages: 0
  })
  const sortBy = ref('qso_date')
  const sortOrder = ref('desc')
  const filters = reactive({
    start_date: '', end_date: '', band: '', mode: '', call_sign: '', grid_square: '',
    dxcc: '',
    station_id: null as number | null,
  })
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const buildParams = () => {
    const params: Record<string, any> = {
      page: pagination.page, page_size: pagination.page_size,
      sort_by: sortBy.value, sort_order: sortOrder.value,
    }
    for (const [key, val] of Object.entries(filters)) {
      if (val !== '' && val !== null && val !== undefined) params[key] = val
    }
    return params
  }

  const fetchLogs = async () => {
    isLoading.value = true
    error.value = null
    try {
      const response = await logsApi.list(buildParams())
      logs.value = response.items
      pagination.total = response.total
      pagination.pages = response.pages
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch logs'
    } finally {
      isLoading.value = false
    }
  }

  const fetchStations = async () => {
    try {
      stations.value = await stationsApi.list()
      // 通过激活的位置找到激活的台站
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
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch stations'
    }
  }

  const refreshActiveStation = async () => {
    try {
      const activeLoc = await locationsApi.getActive()
      const match = stations.value.find(s => s.id === activeLoc.station_id)
      if (match) activeStation.value = match
    } catch { /* no active location */ }
  }

  const createLog = async (data: any) => {
    try {
      const log = await logsApi.create(data)
      logs.value.unshift(log)
      return log
    } catch (err: any) {
      error.value = err.message || 'Failed to create log'
      throw err
    }
  }

  const updateLog = async (id: number, data: any) => {
    try {
      const updated = await logsApi.update(id, data)
      const index = logs.value.findIndex(log => log.id === id)
      if (index > -1) logs.value[index] = updated
      return updated
    } catch (err: any) {
      error.value = err.message || 'Failed to update log'
      throw err
    }
  }

  const deleteLog = async (id: number) => {
    try {
      await logsApi.delete(id)
      logs.value = logs.value.filter(log => log.id !== id)
    } catch (err: any) {
      error.value = err.message || 'Failed to delete log'
      throw err
    }
  }

  const createStation = async (data: any) => {
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
