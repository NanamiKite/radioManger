import { computed, type Ref } from 'vue'
import ALL_DXCC_ENTITIES from '@/data/dxcc-entities.json'
import type { DxccChartData, DxccChartBandData } from '@/api/stats'

export interface FullDxccEntity {
  name: string
  total: number
  bands: Record<string, DxccChartBandData | null>
}

/**
 * 将全量 DXCC 实体列表与用户通联数据合并，返回排序后的完整列表。
 * @param dxccChart - 响应式的 DXCC 图表数据（来自 statsStore）
 */
export function useDxccEntities(dxccChart: Ref<DxccChartData | null>) {
  const fullDxccEntities = computed<FullDxccEntity[]>(() => {
    const chartData = dxccChart.value
    const userMap: Record<string, { total: number; bands: Record<string, DxccChartBandData | null> }> = {}
    if (chartData) {
      for (const e of chartData.entities) {
        userMap[e.entity] = { total: e.total, bands: e.bands }
      }
    }

    return ALL_DXCC_ENTITIES.map(name => {
      const userData = userMap[name]
      if (userData) {
        return { name, total: userData.total, bands: userData.bands }
      }
      return { name, total: 0, bands: {} }
    }).sort((a, b) => a.name.localeCompare(b.name))
  })

  const workedCount = computed(() => fullDxccEntities.value.filter(e => e.total > 0).length)
  const confirmedCount = computed(() => fullDxccEntities.value.filter(e =>
    Object.values(e.bands).some(b => b?.confirmed && b.confirmed > 0)
  ).length)

  return { fullDxccEntities, workedCount, confirmedCount }
}
