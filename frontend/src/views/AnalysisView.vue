<template>
  <div class="analysis-container">
    <div class="page-header">
      <div>
        <h1>{{ $t('analysis.title') }}</h1>
        <p>{{ $t('analysis.statistics') }}</p>
      </div>
      <el-button @click="refreshAll" :loading="loading">{{ $t('analysis.refreshStats') }}</el-button>
    </div>

    <!-- 区块1：概览统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card stat-blue">
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.totalQSO') }}</div>
          <div class="stat-value">{{ stats?.total_qso || 0 }}</div>
        </div>
      </div>
      <div class="stat-card stat-green">
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.monthlyQSO') }}</div>
          <div class="stat-value">{{ stats?.monthly_qso || 0 }}</div>
        </div>
      </div>
      <div class="stat-card stat-orange">
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.yearlyQSO') }}</div>
          <div class="stat-value">{{ stats?.yearly_qso || 0 }}</div>
        </div>
      </div>
      <div class="stat-card stat-purple">
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.confirmedQSO') }}</div>
          <div class="stat-value">{{ stats?.confirmed_qso || 0 }}</div>
        </div>
      </div>
      <div class="stat-card stat-cyan">
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.dxcc') }}</div>
          <div class="stat-value">{{ stats?.total_dxcc || 0 }}</div>
        </div>
      </div>
      <div class="stat-card stat-red">
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.stationCount') }}</div>
          <div class="stat-value">{{ stats?.station_count || 0 }}</div>
        </div>
      </div>
    </div>

    <!-- 区块2：波段分布 + 模式分布 -->
    <div class="two-col">
      <div class="panel">
        <div class="panel-title">{{ $t('analysis.bands') }}</div>
        <div v-if="bandStats.length" class="bar-chart">
          <div v-for="item in sortedBandStats" :key="item.band" class="bar-row">
            <span class="bar-label">{{ item.band }}</span>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: item.percentage + '%' }"></div>
            </div>
            <span class="bar-value">{{ item.qso_count }}</span>
          </div>
        </div>
        <div v-else class="empty-text">{{ $t('analysis.noData') }}</div>
      </div>
      <div class="panel">
        <div class="panel-title">{{ $t('analysis.modes') }}</div>
        <div v-if="modeStats.length" class="bar-chart">
          <div v-for="item in modeStats" :key="item.mode" class="bar-row">
            <span class="bar-label">{{ item.mode }}</span>
            <div class="bar-track">
              <div class="bar-fill mode-fill" :style="{ width: item.percentage + '%' }"></div>
            </div>
            <span class="bar-value">{{ item.qso_count }}</span>
          </div>
        </div>
        <div v-else class="empty-text">{{ $t('analysis.noData') }}</div>
      </div>
    </div>

    <!-- 区块3：DXCC Chart -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">
          DXCC Chart
          <span class="panel-sub">({{ workedCount }} / 340)</span>
        </div>
        <div class="dxcc-filter">
          <input v-model="dxccFilter" type="text" :placeholder="$t('analysis.filterEntity')" class="filter-input" />
          <select v-model="dxccBandFilter" class="filter-select">
            <option value="">{{ $t('analysis.allBands') }}</option>
            <option v-for="band in allBands" :key="band" :value="band">{{ band }}</option>
          </select>
          <select v-model="dxccStatusFilter" class="filter-select">
            <option value="">{{ $t('analysis.all') }}</option>
            <option value="confirmed">{{ $t('analysis.confirmed') }}</option>
            <option value="worked">{{ $t('analysis.worked') }}</option>
            <option value="none">{{ $t('analysis.notWorked') }}</option>
          </select>
        </div>
      </div>

      <div class="dxcc-legend">
        <span class="legend-item"><span class="legend-box dxcc-confirmed"></span> {{ $t('analysis.confirmed') }}</span>
        <span class="legend-item"><span class="legend-box dxcc-worked"></span> {{ $t('analysis.worked') }}</span>
        <span class="legend-item"><span class="legend-box dxcc-empty"></span> {{ $t('analysis.notWorked') }}</span>
      </div>

      <div class="dxcc-band-summary" v-if="dxccChart">
        <span v-for="band in allBands" :key="band" class="band-stat">
          {{ band }}: {{ dxccChart.band_confirmed[band] || 0 }}C / {{ dxccChart.band_worked[band] || 0 }}W
        </span>
      </div>

      <div class="dxcc-chart-scroll">
        <table class="dxcc-chart-table">
          <thead>
            <tr>
              <th class="entity-col">Entity</th>
              <th v-for="band in allBands" :key="band" class="band-col">{{ band }}</th>
              <th class="total-col">Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entity in filteredDxccEntities" :key="entity.name"
                :class="{ 'row-clickable': entity.total > 0 }">
              <td class="entity-col" :class="{ 'entity-worked': entity.total > 0 }"
                  @click="entity.total > 0 && goToLogs(entity.name)">{{ entity.name }}</td>
              <td v-for="band in allBands" :key="band" class="band-col"
                  :class="[getCellClass(entity, band), { 'cell-clickable': entity.bands[band] }]"
                  @click="entity.bands[band] && goToLogs(entity.name, band)">
                {{ getCellText(entity, band) }}
              </td>
              <td class="total-col">{{ entity.total || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 区块4：波段×模式矩阵 + QSL统计 -->
    <div class="two-col">
      <div class="panel">
        <div class="panel-title">{{ $t('analysis.bandModeMatrix') }}</div>
        <div v-if="matrixData" class="matrix-wrapper">
          <table class="matrix-table">
            <thead>
              <tr>
                <th>{{ $t('analysis.band') }} \ {{ $t('analysis.mode') }}</th>
                <th v-for="m in matrixModes" :key="m">{{ m }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in matrixBands" :key="b">
                <td class="band-label">{{ b }}</td>
                <td v-for="m in matrixModes" :key="m"
                    :class="getMatrixCellClass(b, m)"
                    :title="b + ' / ' + m + ': ' + getCellValue(b, m)">
                  {{ getCellValue(b, m) || '-' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-text">{{ $t('analysis.noData') }}</div>
      </div>

      <div class="panel">
        <div class="panel-title">{{ $t('analysis.qslStats') }}</div>
        <table class="info-table">
          <tr>
            <td>{{ $t('dashboard.qslSent') }}</td>
            <td class="value">{{ stats?.qsl_sent || 0 }}</td>
            <td class="rate">{{ qslSentRate }}%</td>
          </tr>
          <tr>
            <td>{{ $t('dashboard.qslReceived') }}</td>
            <td class="value">{{ stats?.qsl_rcvd || 0 }}</td>
            <td class="rate">{{ qslRcvdRate }}%</td>
          </tr>
          <tr>
            <td>{{ $t('dashboard.lotwConfirmed') }}</td>
            <td class="value">{{ stats?.lotw_confirmed || 0 }}</td>
            <td class="rate">{{ lotwRate }}%</td>
          </tr>
        </table>
        <div class="panel-divider"></div>
        <div class="panel-title" style="border:none;padding:0;margin-top:8px;">{{ $t('analysis.activity') }}</div>
        <table class="info-table">
          <tr>
            <td>{{ $t('analysis.totalQso') }}</td>
            <td class="value">{{ stats?.total_qso || 0 }}</td>
          </tr>
          <tr>
            <td>{{ $t('analysis.dxccEntities') }}</td>
            <td class="value">{{ stats?.total_dxcc || 0 }}</td>
          </tr>
          <tr>
            <td>{{ $t('dashboard.confirmedQSO') }}</td>
            <td class="value">{{ stats?.confirmed_qso || 0 }}</td>
          </tr>
          <tr>
            <td>{{ $t('analysis.lastQso') }}</td>
            <td class="value">{{ stats?.last_qso_date || 'N/A' }}</td>
          </tr>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStatsStore } from '@/stores/stats'
import { useLogsStore } from '@/stores/logs'
import { useDxccEntities } from '@/composables/useDxccEntities'
import type { DxccChartBandData } from '@/api/stats'

const router = useRouter()
const statsStore = useStatsStore()
const logsStore = useLogsStore()

const stats = computed(() => statsStore.statistics)
const loading = computed(() => statsStore.isLoading)
const bandStats = computed(() => statsStore.bandStats)
const modeStats = computed(() => statsStore.modeStats)
const dxccChart = computed(() => statsStore.dxccChart)

const { fullDxccEntities, workedCount } = useDxccEntities(dxccChart)

const allBands = computed(() => {
  return dxccChart.value?.bands || ['160m','80m','60m','40m','30m','20m','17m','15m','12m','10m','6m']
})

const bandOrder: Record<string, number> = {
  '160m': 1.8, '80m': 3.5, '60m': 5.3, '40m': 7.0, '30m': 10.1,
  '20m': 14.0, '17m': 18.068, '15m': 21.0, '12m': 24.89, '10m': 28.0,
  '6m': 50.0, '4m': 70.0, '2m': 144.0, '1.25m': 222.0, '70cm': 420.0,
  '33cm': 902.0, '23cm': 1240.0,
}
const sortedBandStats = computed(() => {
  return [...bandStats.value].sort((a, b) => {
    const fa = bandOrder[a.band] ?? 9999
    const fb = bandOrder[b.band] ?? 9999
    return fa - fb
  })
})

const dxccFilter = ref('')
const dxccBandFilter = ref('')
const dxccStatusFilter = ref('')

const filteredDxccEntities = computed(() => {
  let entities = fullDxccEntities.value

  if (dxccFilter.value) {
    const q = dxccFilter.value.toLowerCase()
    entities = entities.filter(e => e.name.toLowerCase().includes(q))
  }

  if (dxccBandFilter.value) {
    const band = dxccBandFilter.value
    if (dxccStatusFilter.value === 'none') {
      entities = entities.filter(e => !e.bands[band])
    } else {
      entities = entities.filter(e => e.bands[band])
    }
  } else if (dxccStatusFilter.value) {
    if (dxccStatusFilter.value === 'confirmed') {
      entities = entities.filter(e => Object.values(e.bands).some(b => b && b.confirmed))
    } else if (dxccStatusFilter.value === 'worked') {
      entities = entities.filter(e => e.total > 0)
    } else if (dxccStatusFilter.value === 'none') {
      entities = entities.filter(e => e.total === 0)
    }
  }

  return entities
})

const getCellClass = (entity: FullDxccEntity, band: string) => {
  const data = entity.bands[band]
  if (!data) return 'dxcc-empty'
  if (data.confirmed) return 'dxcc-confirmed'
  return 'dxcc-worked'
}

const getCellText = (entity: FullDxccEntity, band: string) => {
  const data = entity.bands[band]
  if (!data) return ''
  if (data.confirmed) return 'C'
  return 'W'
}

const goToLogs = (entityName: string, band?: string) => {
  logsStore.filters.call_sign = ''
  logsStore.filters.grid_square = ''
  logsStore.filters.band = band || ''
  logsStore.filters.mode = ''
  const query: Record<string, string> = { dxcc: entityName }
  if (band) query.band = band
  router.push({ name: 'Logs', query })
}

const matrixData = computed(() => {
  const data = statsStore.bandModeMatrix
  if (!data || !data.length) return null
  return data
})

const matrixBands = computed(() => {
  if (!matrixData.value) return []
  const bands = [...new Set(matrixData.value.map(d => d.band))]
  return bands.sort((a, b) => (bandOrder[a] ?? 99) - (bandOrder[b] ?? 99))
})

const matrixModes = computed(() => {
  if (!matrixData.value) return []
  return [...new Set(matrixData.value.map(d => d.mode))].sort()
})

const matrixMap = computed(() => {
  const map: Record<string, number> = {}
  if (matrixData.value) {
    for (const d of matrixData.value) {
      map[d.band + '|' + d.mode] = d.count
    }
  }
  return map
})

const getCellValue = (band: string, mode: string) => matrixMap.value[band + '|' + mode] || 0

const getMatrixCellClass = (band: string, mode: string) => {
  const v = getCellValue(band, mode)
  if (v >= 50) return 'cell-high'
  if (v >= 20) return 'cell-mid'
  if (v > 0) return 'cell-low'
  return ''
}

const total = computed(() => stats.value?.total_qso || 0)
const qslSentRate = computed(() => total.value ? Math.round((stats.value?.qsl_sent || 0) / total.value * 100) : 0)
const qslRcvdRate = computed(() => total.value ? Math.round((stats.value?.qsl_rcvd || 0) / total.value * 100) : 0)
const lotwRate = computed(() => total.value ? Math.round((stats.value?.lotw_confirmed || 0) / total.value * 100) : 0)

const stationId = computed(() => logsStore.activeStation?.id)

const refreshAll = async () => {
  await Promise.all([
    statsStore.fetchStats(stationId.value),
    statsStore.fetchBandMode(),
    statsStore.fetchBandModeMatrix(),
    statsStore.fetchDxccChart(),
  ])
}

onMounted(async () => {
  await logsStore.fetchStations()
  await refreshAll()
})
</script>

<style scoped lang="scss">
.analysis-container {
  max-width: 1200px;
  margin: 0 auto;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    h1 { margin-bottom: 4px; font-size: 20px; font-weight: 600; color: var(--text-color-primary); }
    p { color: var(--text-color-secondary); font-size: 14px; margin: 0; }
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 20px;

    .stat-card {
      background: var(--bg-color-card);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 16px;
      border-left: 3px solid transparent;

      &.stat-blue   { border-left-color: var(--color-blue);   }
      &.stat-green  { border-left-color: var(--color-green);  }
      &.stat-orange { border-left-color: var(--color-orange); }
      &.stat-purple { border-left-color: var(--color-purple); }
      &.stat-cyan   { border-left-color: var(--color-cyan);   }
      &.stat-red    { border-left-color: var(--color-red);    }

      .stat-label { font-size: 12px; color: var(--text-color-secondary); margin-bottom: 4px; }
      .stat-value { font-size: 24px; font-weight: 600; color: var(--text-color-primary); }
    }
  }

  .two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 20px;
  }

  .panel {
    background: var(--bg-color-card);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 16px;

    .panel-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-color-primary);
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border-color);
    }

    .panel-sub {
      font-size: 12px;
      font-weight: 400;
      color: var(--text-color-secondary);
      margin-left: 4px;
    }

    .panel-divider {
      height: 1px;
      background: var(--border-color);
      margin: 12px 0;
    }

    .empty-text {
      color: var(--text-color-placeholder);
      text-align: center;
      padding: 20px;
    }
  }

  .bar-chart {
    .bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
    .bar-label { width: 50px; font-size: 12px; color: var(--text-color-secondary); text-align: right; flex-shrink: 0; }
    .bar-track { flex: 1; height: 8px; background: var(--bg-color-hover); border-radius: 9999px; overflow: hidden; }
    .bar-fill { height: 100%; background: var(--color-accent); border-radius: 9999px; transition: width 0.6s ease; min-width: 4px; }
    .bar-fill.mode-fill { background: var(--color-success); }
    .bar-value { width: 50px; font-size: 12px; color: var(--text-color-secondary); flex-shrink: 0; }
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    flex-wrap: wrap;
    gap: 8px;
  }

  .panel-header .panel-title {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
  }

  .dxcc-filter {
    display: flex;
    gap: 8px;
    align-items: center;

    .filter-input {
      width: 160px;
      height: 30px;
      padding: 0 8px;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      font-size: 13px;
      background: var(--bg-color-card);
      color: var(--text-color-primary);
      outline: none;
      &:focus { border-color: var(--color-accent); }
      &::placeholder { color: var(--text-color-placeholder); }
    }

    .filter-select {
      height: 30px;
      padding: 0 8px;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      font-size: 13px;
      background: var(--bg-color-card);
      color: var(--text-color-primary);
      outline: none;
      cursor: pointer;
      &:focus { border-color: var(--color-accent); }
    }
  }

  .dxcc-legend {
    display: flex;
    gap: 16px;
    margin-bottom: 8px;
    font-size: 12px;
    color: var(--text-color-secondary);

    .legend-item {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .legend-box {
      display: inline-block;
      width: 14px;
      height: 14px;
      border-radius: 2px;
      border: 1px solid var(--border-color-lighter);

      &.dxcc-confirmed { background: var(--color-success); border-color: var(--color-success); }
      &.dxcc-worked { background: var(--color-warning-bg, #fff7e6); border-color: var(--color-warning); }
      &.dxcc-empty { background: var(--bg-color-hover); }
    }
  }

  .dxcc-band-summary {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 10px;
    font-size: 11px;
    color: var(--text-color-secondary);

    .band-stat {
      padding: 2px 6px;
      background: var(--bg-color-hover);
      border-radius: 3px;
      font-family: monospace;
    }
  }

  .dxcc-chart-scroll {
    max-height: 500px;
    overflow-y: auto;
    overflow-x: auto;
    border: 1px solid var(--border-color-lighter);
    border-radius: 4px;

    &::-webkit-scrollbar { width: 6px; height: 6px; }
    &::-webkit-scrollbar-track { background: var(--bg-color-hover); }
    &::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }
    &::-webkit-scrollbar-thumb:hover { background: var(--text-color-placeholder); }
  }

  .dxcc-chart-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 13px;

    th, td {
      padding: 5px 8px;
      text-align: center;
      border: 1px solid var(--border-color-lighter);
      white-space: nowrap;
    }

    thead th {
      background: var(--bg-color-hover);
      color: var(--text-color-secondary);
      font-weight: 600;
      position: sticky;
      top: 0;
      z-index: 10;
    }

    .entity-col {
      text-align: left;
      font-weight: 500;
      color: var(--text-color-secondary);
      position: sticky;
      left: 0;
      background: var(--bg-color-card);
      z-index: 20;
      min-width: 160px;
    }

    thead .entity-col {
      background: var(--bg-color-hover);
      font-weight: 600;
      color: var(--text-color-secondary);
      z-index: 20;
    }

    .entity-worked {
      color: var(--text-color-primary);
      font-weight: 600;
      cursor: pointer;
    }

    .band-col {
      width: 44px;
      min-width: 44px;
      font-size: 12px;
      font-family: monospace;
    }

    .total-col {
      width: 50px;
      font-weight: 600;
      color: var(--text-color-secondary);
      position: sticky;
      right: 0;
      background: var(--bg-color-card);
      z-index: 5;
    }

    thead .total-col {
      background: var(--bg-color-hover);
      z-index: 15;
    }

    .row-clickable {
      cursor: pointer;
      &:hover td { background: var(--bg-color-hover); }
    }

    .dxcc-confirmed {
      background: var(--color-success);
      color: #fff;
      font-weight: 700;
    }

    .dxcc-worked {
      background: var(--color-warning-bg, #fff7e6);
      color: var(--color-warning);
      font-weight: 600;
    }

    .dxcc-empty {
      background: transparent;
      color: var(--text-color-placeholder);
    }

    .cell-clickable {
      cursor: pointer;
      &:hover { filter: brightness(0.85); }
    }
  }

  .matrix-wrapper { overflow-x: auto; }

  .matrix-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;

    th, td {
      padding: 6px 8px;
      text-align: center;
      border: 1px solid var(--border-color-lighter);
    }

    th {
      background: var(--bg-color-hover);
      color: var(--text-color-secondary);
      font-weight: 600;
      white-space: nowrap;
    }

    .band-label {
      font-weight: 600;
      color: var(--text-color-primary);
      text-align: left;
      white-space: nowrap;
    }

    .cell-high { background: var(--color-accent); color: #fff; font-weight: 600; }
    .cell-mid { background: var(--color-blue-bg); color: var(--color-accent); font-weight: 600; }
    .cell-low { background: var(--bg-color-hover); color: var(--text-color-secondary); }
  }

  .info-table {
    width: 100%;
    border-collapse: collapse;
    td {
      padding: 6px 0;
      font-size: 14px;
      color: var(--text-color-secondary);
      border-bottom: 1px solid var(--border-color-lighter);
    }
    tr:last-child td { border-bottom: none; }
    .value { color: var(--text-color-primary); font-weight: 600; text-align: right; }
    .rate { color: var(--color-accent); font-weight: 600; text-align: right; width: 60px; }
  }
}

@media (max-width: 768px) {
  .analysis-container {
    .two-col { grid-template-columns: 1fr; }
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
  }
}
</style>
