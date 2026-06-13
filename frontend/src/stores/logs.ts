import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'
import type { QSOLog, Station } from '@/types'
import { logsApi } from '@/api/logs'
import { stationsApi } from '@/api/stations'

export const useLogsStore = defineStore('logs', () => {
  const logs = ref<QSOLog[]>([])
  const stations = ref<Station[]>([])
  const currentStation = ref<Station | null>(null)
  const pagination = reactive({
    page: 1,
    page_size: 20,
    total: 0,
    pages: 0
  })

  const filters = reactive({
    start_date: '',
    end_date: '',
    band: '',
    mode: '',
    call_sign: ''
  })

  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // 获取日志列表
  const fetchLogs = async () => {
    isLoading.value = true
    error.value = null
    try {
      const response = await logsApi.list({
        page: pagination.page,
        page_size: pagination.page_size,
        ...filters
      })
      logs.value = response.items
      pagination.total = response.total
      pagination.pages = response.pages
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch logs'
    } finally {
      isLoading.value = false
    }
  }

  // 获取台站列表
  const fetchStations = async () => {
    try {
      stations.value = await stationsApi.list()
      if (stations.value.length > 0 && !currentStation.value) {
        currentStation.value = stations.value[0]
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch stations'
    }
  }

  // 创建日志
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

  // 更新日志
  const updateLog = async (id: number, data: any) => {
    try {
      const updated = await logsApi.update(id, data)
      const index = logs.value.findIndex(log => log.id === id)
      if (index > -1) {
        logs.value[index] = updated
      }
      return updated
    } catch (err: any) {
      error.value = err.message || 'Failed to update log'
      throw err
    }
  }

  // 删除日志
  const deleteLog = async (id: number) => {
    try {
      await logsApi.delete(id)
      logs.value = logs.value.filter(log => log.id !== id)
    } catch (err: any) {
      error.value = err.message || 'Failed to delete log'
      throw err
    }
  }

  // 创建台站
  const createStation = async (data: any) => {
    try {
      const station = await stationsApi.create(data)
      stations.value.push(station)
      return station
    } catch (err: any) {
      error.value = err.message || 'Failed to create station'
      throw err
    }
  }

  // 清空过滤条件
  const clearFilters = () => {
    filters.start_date = ''
    filters.end_date = ''
    filters.band = ''
    filters.mode = ''
    filters.call_sign = ''
    pagination.page = 1
  }

  return {
    logs,
    stations,
    currentStation,
    pagination,
    filters,
    isLoading,
    error,
    fetchLogs,
    fetchStations,
    createLog,
    updateLog,
    deleteLog,
    createStation,
    clearFilters
  }
})
