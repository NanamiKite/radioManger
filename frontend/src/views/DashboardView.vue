<template>
  <div class="dashboard-container">
    <!-- 区块 1: 头部 -->
    <div class="dashboard-header">
      <div class="welcome-section">
        <h1>{{ $t('dashboard.title') }}</h1>
        <p>{{ $t('auth.welcomeBack', { username: currentUser?.username || '' }) }}</p>
      </div>
      <div class="clock-section">
        <div class="clock-box">
          <div class="clock-label">{{ $t('dashboard.utcTime') }}</div>
          <div class="clock-time">{{ utcTime }}</div>
        </div>
        <div class="clock-box">
          <div class="clock-label">{{ $t('dashboard.localTime') }}</div>
          <div class="clock-time">{{ localTime }}</div>
        </div>
      </div>
    </div>

    <!-- 区块 2: 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.totalQSO') }}</div>
          <div class="stat-value">{{ statistics?.total_qso || 0 }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📅</div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.monthlyQSO') }}</div>
          <div class="stat-value">{{ statistics?.monthly_qso || 0 }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📆</div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.yearlyQSO') }}</div>
          <div class="stat-value">{{ statistics?.yearly_qso || 0 }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.confirmedQSO') }}</div>
          <div class="stat-value">{{ statistics?.confirmed_qso || 0 }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🌍</div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.dxcc') }}</div>
          <div class="stat-value">{{ statistics?.total_dxcc || 0 }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📻</div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.stationCount') }}</div>
          <div class="stat-value">{{ statistics?.station_count || 0 }}</div>
        </div>
      </div>
    </div>

    <!-- 区块 3: 左=最近日志+比赛日历 / 右=DXCC+波段+模式 -->
    <div class="two-col">
      <div class="col-left">
        <!-- 最近日志 -->
        <div class="panel panel-grow" style="margin-bottom:16px">
          <div class="panel-title">{{ $t('dashboard.recentLogs') }}</div>
          <el-table :data="recentLogs" size="default" stripe
            @row-click="(row: any) => router.push({ name: 'LogDetail', params: { id: row.id } })"
            style="cursor:pointer; font-size:15px" empty-text="-">
            <el-table-column prop="call_sign" :label="$t('logs.callSign')" width="130">
              <template #default="scope"><span style="font-size:15px;font-weight:600">{{ scope.row.call_sign }}</span></template>
            </el-table-column>
            <el-table-column prop="mode" label="Mode" width="90">
              <template #default="scope"><span style="font-size:14px">{{ scope.row.mode }}</span></template>
            </el-table-column>
            <el-table-column prop="band" label="Band" width="90">
              <template #default="scope"><span style="font-size:14px">{{ scope.row.band }}</span></template>
            </el-table-column>
            <el-table-column prop="qso_date" :label="$t('logs.qsoDate')" width="120">
              <template #default="scope"><span style="font-size:14px">{{ scope.row.qso_date }}</span></template>
            </el-table-column>
            <el-table-column prop="dxcc" label="DXCC">
              <template #default="scope"><span style="font-size:14px">{{ scope.row.dxcc || '-' }}</span></template>
            </el-table-column>
          </el-table>
        </div>
        <!-- 比赛日历 -->
        <div class="panel">
          <div class="panel-title">📅 {{ $t('dashboard.contestCalendar') }}</div>
          <div class="contest-list">
            <div v-for="c in upcomingContests" :key="c.name" class="contest-item"
              :class="{ 'contest-soon': c.daysUntil <= 14 }">
              <div class="contest-date">{{ c.dateStr }}</div>
              <div class="contest-info">
                <div class="contest-name">{{ c.name }}</div>
                <div class="contest-band">{{ c.bands }}</div>
              </div>
              <div class="contest-countdown" v-if="c.daysUntil >= 0">
                {{ c.daysUntil === 0 ? $t('dashboard.today') : c.daysUntil + 'd' }}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-right">
        <!-- DXCC 进度 -->
        <div class="panel" style="margin-bottom:16px">
          <div class="panel-title">{{ $t('dashboard.dxccProgress') }}</div>
          <div class="dxcc-progress">
            <div class="dxcc-big">{{ statistics?.total_dxcc || 0 }} / 340</div>
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" :style="{ width: dxccPercent + '%' }"></div>
            </div>
            <div class="dxcc-label">{{ dxccPercent }}%</div>
            <div class="dxcc-detail">
              <span>{{ $t('dashboard.worked') }}: <strong>{{ statistics?.total_dxcc || 0 }}</strong></span>
              <span>{{ $t('dashboard.confirmed') }}: <strong>{{ statistics?.confirmed_dxcc || 0 }}</strong></span>
            </div>
          </div>
        </div>
        <!-- Band 分布 -->
        <div class="panel" style="margin-bottom:16px">
          <div class="panel-title">{{ $t('dashboard.bandDistribution') }}</div>
          <div v-if="sortedBandStats.length" class="bar-chart">
            <div v-for="item in sortedBandStats" :key="item.band" class="bar-row">
              <span class="bar-label">{{ item.band }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: item.percentage + '%' }"></div>
              </div>
              <span class="bar-value">{{ item.qso_count }}</span>
            </div>
          </div>
          <div v-else class="empty-text">-</div>
        </div>
        <!-- Mode 分布 -->
        <div class="panel">
          <div class="panel-title">{{ $t('dashboard.modeDistribution') }}</div>
          <div v-if="modeStats.length" class="bar-chart">
            <div v-for="item in modeStats" :key="item.mode" class="bar-row">
              <span class="bar-label">{{ item.mode }}</span>
              <div class="bar-track">
                <div class="bar-fill mode-fill" :style="{ width: item.percentage + '%' }"></div>
              </div>
              <span class="bar-value">{{ item.qso_count }} ({{ item.percentage }}%)</span>
            </div>
          </div>
          <div v-else class="empty-text">-</div>
        </div>
      </div>
    </div>

    <!-- 区块 5: 操作按钮 -->
    <div class="actions">
      <el-button type="primary" @click="goToLogs">{{ $t('dashboard.viewLogs') }}</el-button>
      <el-button @click="goToStations">{{ $t('dashboard.manageStations') }}</el-button>
      <el-button @click="goToCallsigns">🔍 {{ $t('dashboard.queryCallsign') }}</el-button>
      <el-button @click="goToAnalysis">{{ $t('dashboard.viewAnalysis') }}</el-button>
      <el-button @click="goToTools">🔧 {{ $t('nav.tools') }}</el-button>
      <el-button @click="goToDxcluster">📡 {{ $t('dashboard.viewDxcluster') }}</el-button>
      <el-button @click="goToShortcuts">🔗 {{ $t('dashboard.viewShortcuts') }}</el-button>
      <el-button @click="goToRecycleBin">🗑️ {{ $t('dashboard.viewRecycleBin') }}</el-button>
      <el-button @click="goToSettings">⚙️ {{ $t('dashboard.viewSettings') }}</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useStatsStore } from '@/stores/stats'
import { useLogsStore } from '@/stores/logs'
import { logsApi } from '@/api/logs'
import type { QSOLog } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
const statsStore = useStatsStore()
const logsStore = useLogsStore()

const currentUser = computed(() => authStore.user)
const statistics = computed(() => statsStore.statistics)
const bandStats = computed(() => statsStore.bandStats)
const modeStats = computed(() => statsStore.modeStats)

// 波段按频率从低到高排序
const bandOrder: Record<string, number> = {
  '2190m': 0.137, '630m': 0.475, '160m': 1.8, '80m': 3.5, '60m': 5.3,
  '40m': 7.0, '30m': 10.1, '20m': 14.0, '17m': 18.068, '15m': 21.0,
  '12m': 24.89, '10m': 28.0, '6m': 50.0, '4m': 70.0, '2m': 144.0,
  '1.25m': 222.0, '70cm': 420.0, '33cm': 902.0, '23cm': 1240.0,
}
const sortedBandStats = computed(() => {
  return [...bandStats.value].sort((a, b) => {
    const fa = bandOrder[a.band] ?? 9999
    const fb = bandOrder[b.band] ?? 9999
    return fa - fb
  })
})

const recentLogs = ref<QSOLog[]>([])
const dxccPercent = computed(() => {
  const worked = statistics.value?.total_dxcc || 0
  return worked > 0 ? Math.round((worked / 340) * 100) : 0
})

// 时钟
const utcTime = ref('')
const localTime = ref('')
let timer: number | null = null

function updateClock() {
  const now = new Date()
  utcTime.value = now.toUTCString().split(' ')[4]
  try {
    localTime.value = now.toLocaleTimeString([], {
      timeZone: currentUser.value?.timezone || 'UTC',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    })
  } catch {
    localTime.value = now.toLocaleTimeString()
  }
}

// 业余无线电比赛日历（主要国际比赛，按月循环）
interface Contest { name: string; dateStr: string; bands: string; daysUntil: number }

const contests = [
  { name: 'ARRL RTTY Roundup', month: 1, day: 11, bands: '80-10m' },
  { name: 'CQ WW 160m CW', month: 1, day: 24, bands: '160m' },
  { name: 'ARRL DX CW', month: 2, day: 15, bands: '160-10m' },
  { name: 'ARRL DX SSB', month: 3, day: 1, bands: '160-10m' },
  { name: 'CQ WPX SSB', month: 3, day: 22, bands: '160-10m' },
  { name: 'CQ WPX CW', month: 5, day: 24, bands: '160-10m' },
  { name: 'ARRL Field Day', month: 6, day: 28, bands: 'All' },
  { name: 'IARU HF Championship', month: 7, day: 12, bands: '160-10m' },
  { name: 'WW Digi DX Contest', month: 8, day: 30, bands: '80-10m' },
  { name: 'ARRL September VHF', month: 9, day: 13, bands: '6m+' },
  { name: 'CQ WW SSB', month: 10, day: 25, bands: '160-10m' },
  { name: 'CQ WW CW', month: 11, day: 22, bands: '160-10m' },
  { name: 'ARRL 10m Contest', month: 12, day: 13, bands: '10m' },
  { name: 'RAC Winter Contest', month: 12, day: 20, bands: '160-10m' },
]

const upcomingContests = computed<Contest[]>(() => {
  const now = new Date()
  const year = now.getFullYear()
  const result: Contest[] = []
  for (const c of contests) {
    // 今年的日期
    let d = new Date(year, c.month - 1, c.day)
    let daysUntil = Math.ceil((d.getTime() - now.getTime()) / 86400000)
    // 如果已过，算明年的
    if (daysUntil < -1) {
      d = new Date(year + 1, c.month - 1, c.day)
      daysUntil = Math.ceil((d.getTime() - now.getTime()) / 86400000)
    }
    const dateStr = `${c.month}/${c.day}`
    result.push({ name: c.name, dateStr, bands: c.bands, daysUntil })
  }
  // 按距离天数排序，取最近 6 个
  return result.sort((a, b) => a.daysUntil - b.daysUntil).slice(0, 6)
})

onMounted(async () => {
  await logsStore.fetchStations()
  const stationId = logsStore.activeStation?.id
  await Promise.all([
    statsStore.fetchStats(stationId),
    statsStore.fetchBandMode(),
    loadRecentLogs(),
  ])
  updateClock()
  timer = window.setInterval(updateClock, 1000)
})

async function loadRecentLogs() {
  try {
    const res = await logsApi.list({ page: 1, page_size: 10, sort_by: 'qso_date', sort_order: 'desc' })
    recentLogs.value = res.items || []
  } catch {
    recentLogs.value = []
  }
}

onUnmounted(() => { if (timer) clearInterval(timer) })

const goToLogs = () => router.push({ name: 'Logs' })
const goToStations = () => router.push({ name: 'Stations' })
const goToCallsigns = () => router.push({ name: 'Callsigns' })
const goToAnalysis = () => router.push({ name: 'Analysis' })
const goToDxcluster = () => router.push({ name: 'DXClusters' })
const goToShortcuts = () => router.push({ name: 'Shortcuts' })
const goToRecycleBin = () => router.push({ name: 'RecycleBin' })
const goToSettings = () => router.push({ name: 'Settings' })
const goToTools = () => router.push({ name: 'Tools' })
</script>

<style scoped lang="scss">
.dashboard-container {
  max-width: 1200px; margin: 0 auto;

  .dashboard-header {
    display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px;
    .welcome-section {
      h1 { margin: 0 0 6px; color: #303133; }
      p { margin: 0; color: #909399; }
    }
    .clock-section {
      display: flex; gap: 16px;
      .clock-box {
        background: white; border-radius: 8px; padding: 12px 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        .clock-label { font-size: 11px; color: #909399; margin-bottom: 4px; }
        .clock-time { font-size: 22px; font-weight: bold; color: #409eff; font-family: monospace; }
      }
    }
  }

  .stats-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; margin-bottom: 20px;
    .stat-card {
      background: white; border-radius: 8px; padding: 16px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);
      .stat-icon { font-size: 26px; }
      .stat-content {
        flex: 1;
        .stat-label { color: #909399; font-size: 12px; margin-bottom: 2px; }
        .stat-value { color: #303133; font-size: 22px; font-weight: bold; }
      }
    }
  }

  .two-col { display: flex; gap: 16px; margin-bottom: 20px; }
  .col-left { flex: 3; display: flex; flex-direction: column; }
  .col-right { flex: 2; display: flex; flex-direction: column; }
  .panel-grow { flex: 1; display: flex; flex-direction: column; }
  .panel-grow :deep(.el-table) { flex: 1; }

  .panel {
    background: white; border-radius: 8px; padding: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    .panel-title { font-size: 14px; font-weight: 600; color: #303133; margin-bottom: 12px; }
    .empty-text { color: #c0c4cc; text-align: center; padding: 20px; }
  }

  .dxcc-progress {
    text-align: center; padding: 20px 0;
    .dxcc-big { font-size: 32px; font-weight: bold; color: #409eff; margin-bottom: 12px; }
    .progress-bar-bg { height: 20px; background: #ebeef5; border-radius: 10px; overflow: hidden; margin-bottom: 8px; }
    .progress-bar-fill { height: 100%; background: linear-gradient(90deg, #409eff, #67c23a); border-radius: 10px; transition: width 0.6s ease; }
    .dxcc-label { font-size: 14px; color: #909399; margin-bottom: 12px; }
    .dxcc-detail { display: flex; justify-content: center; gap: 24px; font-size: 13px; color: #606266; }
  }

  .contest-list {
    .contest-item {
      display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #f0f0f0;
      &:last-child { border-bottom: none; }
      &.contest-soon { .contest-countdown { color: #e6a23c; font-weight: bold; } }
      .contest-date { width: 44px; font-size: 12px; color: #909399; flex-shrink: 0; }
      .contest-info { flex: 1; min-width: 0;
        .contest-name { font-size: 13px; color: #303133; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .contest-band { font-size: 11px; color: #909399; }
      }
      .contest-countdown { width: 32px; text-align: right; font-size: 13px; color: #409eff; flex-shrink: 0; }
    }
  }

  .bar-chart {
    .bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
    .bar-label { width: 50px; font-size: 12px; color: #606266; text-align: right; flex-shrink: 0; }
    .bar-track { flex: 1; height: 18px; background: #ebeef5; border-radius: 4px; overflow: hidden; }
    .bar-fill { height: 100%; background: #409eff; border-radius: 4px; transition: width 0.6s ease; min-width: 2px; }
    .bar-fill.mode-fill { background: #67c23a; }
    .bar-value { width: 80px; font-size: 12px; color: #909399; flex-shrink: 0; }
  }

  .actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 4px; }
}
</style>
