<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <h1>{{ $t('dashboard.title') }}</h1>
      <p>{{ $t('auth.welcomeBack', { username: currentUser?.username || '' }) }}</p>
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
        <div class="stat-icon">📮</div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.qslReceived') }}</div>
          <div class="stat-value">{{ statistics?.qsl_rcvd || 0 }}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">🚀</div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('dashboard.lotwConfirmed') }}</div>
          <div class="stat-value">{{ statistics?.lotw_confirmed || 0 }}</div>
        </div>
      </div>
    </div>

    <div class="actions">
      <el-button type="primary" @click="goToLogs">{{ $t('dashboard.viewLogs') }}</el-button>
      <el-button @click="goToStations">{{ $t('dashboard.manageStations') }}</el-button>
      <el-button @click="goToAnalysis">{{ $t('dashboard.viewAnalysis') }}</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useStatsStore } from '@/stores/stats'

const router = useRouter()
const authStore = useAuthStore()
const statsStore = useStatsStore()

const currentUser = computed(() => authStore.user)
const statistics = computed(() => statsStore.statistics)

onMounted(() => {
  statsStore.fetchStats()
})

const goToLogs = () => {
  router.push({ name: 'Logs' })
}

const goToStations = () => {
  router.push({ name: 'Stations' })
}

const goToAnalysis = () => {
  router.push({ name: 'Analysis' })
}
</script>

<style scoped lang="scss">
.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;

  .dashboard-header {
    margin-bottom: 30px;

    h1 {
      margin-bottom: 10px;
      color: #303133;
    }

    p {
      color: #909399;
    }
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 30px;

    .stat-card {
      background: white;
      border-radius: 8px;
      padding: 20px;
      display: flex;
      align-items: center;
      gap: 15px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

      .stat-icon {
        font-size: 32px;
      }

      .stat-content {
        flex: 1;

        .stat-label {
          color: #909399;
          font-size: 14px;
          margin-bottom: 5px;
        }

        .stat-value {
          color: #409eff;
          font-size: 28px;
          font-weight: bold;
          }
        }
      }
    }

  .actions {
    display: flex;
    gap: 10px;
  }
}
</style>