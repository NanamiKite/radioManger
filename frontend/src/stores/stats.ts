import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Statistics, BandStatEntry, ModeStatEntry } from '@/types'
import { statsApi, type DxccChartData, type BandModeMatrixEntry } from '@/api/stats'

export const useStatsStore = defineStore('stats', () => {
  const statistics = ref<Statistics | null>(null)
  const bandStats = ref<BandStatEntry[]>([])
  const modeStats = ref<ModeStatEntry[]>([])
  const dxccChart = ref<DxccChartData | null>(null)
  const bandModeMatrix = ref<BandModeMatrixEntry[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const fetchStats = async (station_id?: number) => {
    isLoading.value = true
    error.value = null
    try {
      const response = await statsApi.getOverview(station_id)
      statistics.value = response.data
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch statistics'
    } finally {
      isLoading.value = false
    }
  }

  const fetchBandMode = async () => {
    try {
      const response = await statsApi.getBandMode()
      bandStats.value = response.data.bands || []
      modeStats.value = response.data.modes || []
    } catch {
      bandStats.value = []
      modeStats.value = []
    }
  }

  const fetchDxccChart = async () => {
    try {
      const response = await statsApi.getDxccChart()
      dxccChart.value = response.data || null
    } catch {
      dxccChart.value = null
    }
  }

  const fetchBandModeMatrix = async () => {
    try {
      const response = await statsApi.getBandModeMatrix()
      bandModeMatrix.value = response.data || []
    } catch {
      bandModeMatrix.value = []
    }
  }

  return {
    statistics, bandStats, modeStats, dxccChart, bandModeMatrix, isLoading, error,
    fetchStats, fetchBandMode, fetchDxccChart, fetchBandModeMatrix
  }
})
