import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Statistics } from '@/types'
import { statsApi } from '@/api/stats'

export const useStatsStore = defineStore('stats', () => {
  const statistics = ref<Statistics | null>(null)
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

  return {
    statistics,
    isLoading,
    error,
    fetchStats
  }
})
