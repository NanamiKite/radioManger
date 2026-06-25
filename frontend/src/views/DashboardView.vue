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
      <div class="stat-card stat-blue">
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.totalQSO') }}</div>
          <div class="stat-value">{{ statistics?.total_qso || 0 }}</div>
        </div>
      </div>
      <div class="stat-card stat-green">
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.monthlyQSO') }}</div>
          <div class="stat-value">{{ statistics?.monthly_qso || 0 }}</div>
        </div>
      </div>
      <div class="stat-card stat-orange">
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.yearlyQSO') }}</div>
          <div class="stat-value">{{ statistics?.yearly_qso || 0 }}</div>
        </div>
      </div>
      <div class="stat-card stat-purple">
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.confirmedQSO') }}</div>
          <div class="stat-value">{{ statistics?.confirmed_qso || 0 }}</div>
        </div>
      </div>
      <div class="stat-card stat-cyan">
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.dxcc') }}</div>
          <div class="stat-value">{{ statistics?.total_dxcc || 0 }}</div>
        </div>
      </div>
      <div class="stat-card stat-red">
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
              <template #default="scope">
                <span class="callsign-link" @click.stop="lookupCall(scope.row.call_sign)">
                  {{ scope.row.call_sign }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="mode" :label="$t('logs.mode')" width="90">
              <template #default="scope"><span style="font-size:14px">{{ scope.row.mode }}</span></template>
            </el-table-column>
            <el-table-column prop="band" :label="$t('logs.band')" width="90">
              <template #default="scope"><span style="font-size:14px">{{ scope.row.band }}</span></template>
            </el-table-column>
            <el-table-column prop="qso_date" :label="$t('logs.qsoDate')" width="120">
              <template #default="scope"><span style="font-size:14px">{{ scope.row.qso_date }}</span></template>
            </el-table-column>
            <el-table-column prop="dxcc" :label="'DXCC'">
              <template #default="scope"><span style="font-size:14px">{{ scope.row.dxcc || '-' }}</span></template>
            </el-table-column>
          </el-table>
        </div>
        <!-- 比赛日历 -->
        <div class="panel">
          <div class="panel-title">{{ $t('dashboard.contestCalendar') }}</div>
          <div class="contest-list">
            <div v-for="c in upcomingContests" :key="c.name" class="contest-item"
              :class="{ 'contest-soon': c.daysUntil <= 14 }">
              <div class="contest-date">{{ c.dateStr }}</div>
              <div class="contest-info">
                <a class="contest-name" :href="c.url" target="_blank" rel="noopener">{{ c.name }}</a>
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
      <el-button @click="goToCallsigns">{{ $t('dashboard.queryCallsign') }}</el-button>
      <el-button @click="goToAnalysis">{{ $t('dashboard.viewAnalysis') }}</el-button>
      <el-button @click="goToTools">{{ $t('nav.tools') }}</el-button>
      <el-button @click="goToDxcluster">{{ $t('dashboard.viewDxcluster') }}</el-button>
      <el-button @click="goToShortcuts">{{ $t('dashboard.viewShortcuts') }}</el-button>
      <el-button @click="goToRecycleBin">{{ $t('dashboard.viewRecycleBin') }}</el-button>
      <el-button @click="goToSettings">{{ $t('dashboard.viewSettings') }}</el-button>
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
interface Contest { name: string; dateStr: string; bands: string; daysUntil: number; url: string }

const contests = [
  { name: 'ARRL RTTY Roundup', month: 1, day: 11, bands: '80-10m', url: 'https://www.contestcalendar.com/weeklydetail.php?contest=arrl-rtty' },
  { name: 'CQ WW 160m CW', month: 1, day: 24, bands: '160m', url: 'https://www.contestcalendar.com/weeklydetail.php?contest=cq-ww-160' },
  { name: 'ARRL DX CW', month: 2, day: 15, bands: '160-10m', url: 'https://www.contestcalendar.com/weeklydetail.php?contest=arrl-dx-cw' },
  { name: 'ARRL DX SSB', month: 3, day: 1, bands: '160-10m', url: 'https://www.contestcalendar.com/weeklydetail.php?contest=arrl-dx-ssb' },
  { name: 'CQ WPX SSB', month: 3, day: 22, bands: '160-10m', url: 'https://www.contestcalendar.com/weeklydetail.php?contest=cq-wpx-ssb' },
  { name: 'CQ WPX CW', month: 5, day: 24, bands: '160-10m', url: 'https://www.contestcalendar.com/weeklydetail.php?contest=cq-wpx-cw' },
  { name: 'ARRL Field Day', month: 6, day: 28, bands: 'All', url: 'https://www.arrl.org/field-day' },
  { name: 'IARU HF Championship', month: 7, day: 12, bands: '160-10m', url: 'https://www.contestcalendar.com/weeklydetail.php?contest=iaru-hf' },
  { name: 'WW Digi DX Contest', month: 8, day: 30, bands: '80-10m', url: 'https://www.contestcalendar.com/weeklydetail.php?contest=ww-digi' },
  { name: 'ARRL September VHF', month: 9, day: 13, bands: '6m+', url: 'https://www.contestcalendar.com/weeklydetail.php?contest=arrl-sept-vhf' },
  { name: 'CQ WW SSB', month: 10, day: 25, bands: '160-10m', url: 'https://www.contestcalendar.com/weeklydetail.php?contest=cq-ww-ssb' },
  { name: 'CQ WW CW', month: 11, day: 22, bands: '160-10m', url: 'https://www.contestcalendar.com/weeklydetail.php?contest=cq-ww-cw' },
  { name: 'ARRL 10m Contest', month: 12, day: 13, bands: '10m', url: 'https://www.contestcalendar.com/weeklydetail.php?contest=arrl-10m' },
  { name: 'RAC Winter Contest', month: 12, day: 20, bands: '160-10m', url: 'https://www.contestcalendar.com/weeklydetail.php?contest=rac-winter' },
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
    result.push({ name: c.name, dateStr, bands: c.bands, daysUntil, url: c.url })
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
const lookupCall = (call: string) => {
  if (call) window.open(`https://www.qrz.com/db/${call}`, '_blank')
}
const goToTools = () => router.push({ name: 'Tools' })
</script>

<style scoped lang="scss">
.dashboard-container {
  max-width: 1400px;
  margin: 0 auto;
  animation: fadeIn 0.2s ease-out;

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .callsign-link {
    font-weight: 600;
    color: var(--color-accent);
    font-family: monospace;
    cursor: pointer;
    &:hover { text-decoration: underline; }
  }

  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--spacing-xl);
    padding-bottom: var(--spacing-lg);
    border-bottom: 1px solid var(--border-color);

    .welcome-section {
      h1 {
        margin: 0 0 var(--spacing-xs);
        color: var(--text-color-primary);
        font-size: var(--font-size-xxl);
        font-weight: var(--font-weight-semibold);
        letter-spacing: -0.02em;
      }
      p {
        margin: 0;
        color: var(--text-color-secondary);
        font-size: var(--font-size-base);
      }
    }

    .clock-section {
      display: flex;
      gap: var(--spacing-sm);
      .clock-box {
        background: var(--bg-color-card);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius-base);
        padding: var(--spacing-sm) var(--spacing-base);
        text-align: center;
        .clock-label {
          font-size: var(--font-size-extra-small);
          color: var(--text-color-secondary);
          margin-bottom: 2px;
          font-weight: var(--font-weight-medium);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .clock-time {
          font-size: var(--font-size-xxl);
          font-weight: var(--font-weight-semibold);
          color: var(--text-color-primary);
          font-family: 'JetBrains Mono', 'Fira Code', monospace;
        }
      }
    }
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: var(--spacing-base);
    margin-bottom: var(--spacing-xl);

    .stat-card {
      background: var(--bg-color-card);
      border: 1px solid var(--border-color);
      border-radius: var(--border-radius-base);
      padding: var(--spacing-lg);
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      cursor: default;
      border-left: 3px solid transparent;

      &.stat-blue   { border-left-color: var(--color-blue);   .stat-icon { background: var(--color-blue-bg);   } }
      &.stat-green  { border-left-color: var(--color-green);  .stat-icon { background: var(--color-green-bg);  } }
      &.stat-orange { border-left-color: var(--color-orange); .stat-icon { background: var(--color-orange-bg); } }
      &.stat-purple { border-left-color: var(--color-purple); .stat-icon { background: var(--color-purple-bg); } }
      &.stat-cyan   { border-left-color: var(--color-cyan);   .stat-icon { background: var(--color-cyan-bg);   } }
      &.stat-red    { border-left-color: var(--color-red);    .stat-icon { background: var(--color-red-bg);    } }

      .stat-icon {
        font-size: 22px;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--bg-color-hover);
        border-radius: var(--border-radius-base);
        flex-shrink: 0;
      }

      .stat-content {
        flex: 1;
        min-width: 0;
        .stat-label {
          color: var(--text-color-secondary);
          font-size: var(--font-size-small);
          margin-bottom: 2px;
          font-weight: var(--font-weight-medium);
        }
        .stat-value {
          color: var(--text-color-primary);
          font-size: var(--font-size-xxl);
          font-weight: var(--font-weight-semibold);
          line-height: 1.2;
        }
      }
    }
  }

  .two-col {
    display: flex;
    gap: var(--spacing-base);
    margin-bottom: var(--spacing-xl);
  }

  .col-left {
    flex: 3;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-base);
  }

  .col-right {
    flex: 2;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-base);
  }

  .panel-grow {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .panel-grow :deep(.el-table) {
    flex: 1;
  }

  // ── 面板 — 边框卡片 ──
  .panel {
    background: var(--bg-color-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-base);
    padding: var(--spacing-lg);

    .panel-title {
      font-size: var(--font-size-base);
      font-weight: var(--font-weight-semibold);
      color: var(--text-color-primary);
      margin-bottom: var(--spacing-base);
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding-bottom: var(--spacing-sm);
      border-bottom: 1px solid var(--border-color);
    }

    .empty-text {
      color: var(--text-color-placeholder);
      text-align: center;
      padding: var(--spacing-xl);
      font-size: var(--font-size-base);
    }
  }

  // ── DXCC 进度 ──
  .dxcc-progress {
    text-align: center;
    padding: var(--spacing-base) 0;

    .dxcc-big {
      font-size: 36px;
      font-weight: var(--font-weight-bold);
      color: var(--text-color-primary);
      margin-bottom: var(--spacing-md);
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
    }

    .progress-bar-bg {
      height: 8px;
      background: var(--bg-color-hover);
      border-radius: var(--border-radius-round);
      overflow: hidden;
      margin-bottom: var(--spacing-sm);
    }

    .progress-bar-fill {
      height: 100%;
      background: var(--color-accent);
      border-radius: var(--border-radius-round);
      transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .dxcc-label {
      font-size: var(--font-size-small);
      color: var(--text-color-secondary);
      margin-bottom: var(--spacing-md);
      font-weight: var(--font-weight-medium);
    }

    .dxcc-detail {
      display: flex;
      justify-content: center;
      gap: var(--spacing-xl);
      font-size: var(--font-size-small);
      color: var(--text-color-secondary);
      strong {
        color: var(--text-color-primary);
        font-weight: var(--font-weight-medium);
      }
    }
  }

  // ── 比赛日历 ──
  .contest-list {
    .contest-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-sm) 0;
      border-bottom: 1px solid var(--border-color-lighter);
      &:last-child { border-bottom: none; }
      &:hover { background: var(--bg-color-hover); border-radius: var(--border-radius-base); }

      &.contest-soon .contest-countdown {
        color: var(--color-warning);
        font-weight: var(--font-weight-semibold);
      }

      .contest-date {
        width: 50px;
        font-size: var(--font-size-small);
        color: var(--text-color-secondary);
        flex-shrink: 0;
        font-weight: var(--font-weight-medium);
      }

      .contest-info {
        flex: 1;
        min-width: 0;
        .contest-name {
          font-size: var(--font-size-small);
          color: var(--color-accent);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          font-weight: var(--font-weight-semibold);
          text-decoration: none;
          cursor: pointer;
          display: block;
          &:hover {
            text-decoration: underline;
          }
        }
        .contest-band {
          font-size: var(--font-size-extra-small);
          color: var(--text-color-secondary);
          margin-top: 2px;
        }
      }

      .contest-countdown {
        width: 40px;
        text-align: right;
        font-size: var(--font-size-small);
        color: var(--text-color-secondary);
        flex-shrink: 0;
        font-weight: var(--font-weight-medium);
      }
    }
  }

  // ── 柱状图 ──
  .bar-chart {
    .bar-row {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      margin-bottom: var(--spacing-sm);
    }

    .bar-label {
      width: 50px;
      font-size: var(--font-size-small);
      color: var(--text-color-secondary);
      text-align: right;
      flex-shrink: 0;
      font-weight: var(--font-weight-medium);
    }

    .bar-track {
      flex: 1;
      height: 8px;
      background: var(--bg-color-hover);
      border-radius: var(--border-radius-round);
      overflow: hidden;
    }

    .bar-fill {
      height: 100%;
      background: var(--color-accent);
      border-radius: var(--border-radius-round);
      transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
      min-width: 4px;
    }

    .bar-fill.mode-fill {
      background: var(--color-success);
    }

    .bar-value {
      width: 80px;
      font-size: var(--font-size-small);
      color: var(--text-color-secondary);
      flex-shrink: 0;
      font-weight: var(--font-weight-medium);
    }
  }

  // ── 操作按钮 ──
  .actions {
    display: flex;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
    margin-top: var(--spacing-sm);
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--border-color);
  }
}

@media (max-width: 1200px) {
  .dashboard-container {
    .two-col { flex-direction: column; }
    .col-left, .col-right { flex: 1; }
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    .dashboard-header {
      flex-direction: column;
      gap: var(--spacing-base);
    }
    .clock-section { width: 100%; }
    .clock-box { flex: 1; }
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
    .actions { justify-content: center; }
  }
}

@media (max-width: 480px) {
  .dashboard-container {
    .stats-grid { grid-template-columns: 1fr; }
  }
}
</style>
