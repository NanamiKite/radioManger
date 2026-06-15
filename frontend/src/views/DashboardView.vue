<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div class="welcome-section">
        <h1>{{ $t('dashboard.title') }}</h1>
        <p>{{ $t('auth.welcomeBack', { username: currentUser?.username || '' }) }}</p>
      </div>

      <!-- UTC + 本地时钟 -->
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

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.totalQSO') }}</div>
          <div class="stat-value">{{ statistics?.total_qso || 0 }}</div>
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
        <div class="stat-icon">🏆</div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.totalWaz') }}</div>
          <div class="stat-value">{{ statistics?.total_waz || 0 }}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">📮</div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.qslReceived') }}</div>
          <div class="stat-value">{{ statistics?.qsl_rcvd || 0 }}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">✉️</div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.qslSent') }}</div>
          <div class="stat-value">{{ statistics?.qsl_sent || 0 }}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.lotwConfirmed') }}</div>
          <div class="stat-value">{{ statistics?.lotw_confirmed || 0 }}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">🔄</div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.lastQso') }}</div>
          <div class="stat-value stat-date">{{ lastQsoDisplay }}</div>
        </div>
      </div>
    </div>

    <div class="actions">
      <el-button type="primary" @click="goToLogs">{{ $t('dashboard.viewLogs') }}</el-button>
      <el-button @click="goToStations">{{ $t('dashboard.manageStations') }}</el-button>
      <el-button @click="goToCallsigns">🔍 {{ $t('dashboard.queryCallsign') }}</el-button>
      <el-button @click="goToAnalysis">{{ $t('dashboard.viewAnalysis') }}</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useStatsStore } from '@/stores/stats'
import { useLogsStore } from '@/stores/logs'

const router = useRouter()
const authStore = useAuthStore()
const statsStore = useStatsStore()
const logsStore = useLogsStore()

const currentUser = computed(() => authStore.user)
const statistics = computed(() => statsStore.statistics)
const userTimezone = computed(() => currentUser.value?.timezone || 'UTC')
const activeStation = computed(() => logsStore.activeStation)

// 获取激活台站的最新通联日期显示
const lastQsoDisplay = computed(() => {
  if (!statistics.value?.last_qso_date) return 'N/A'
  // 如果是跨年同日期的特殊处理
  return statistics.value.last_qso_date
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

onMounted(async () => {
  await logsStore.fetchStations()
  // 按激活台站获取统计
  if (logsStore.activeStation) {
    await statsStore.fetchStats(logsStore.activeStation.id)
  } else {
    await statsStore.fetchStats()
  }
  updateClock()
  timer = window.setInterval(updateClock, 1000)
})

onUnmounted(() => { if (timer) clearInterval(timer) })

const goToLogs = () => router.push({ name: 'Logs' })
const goToStations = () => router.push({ name: 'Stations' })
const goToCallsigns = () => router.push({ name: 'Callsigns' })
const goToAnalysis = () => router.push({ name: 'Analysis' })
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
    display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px;
    .stat-card {
      background: white; border-radius: 8px; padding: 20px; display: flex; align-items: center; gap: 15px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);
      .stat-icon { font-size: 28px; }
      .stat-content {
        flex: 1;
        .stat-label { color: #909399; font-size: 13px; margin-bottom: 4px; }
        .stat-value { color: #409eff; font-size: 24px; font-weight: bold; }
        .stat-date { font-size: 16px; }
      }
    }
  }
  .actions { display: flex; gap: 10px; flex-wrap: wrap; }
}
</style>
