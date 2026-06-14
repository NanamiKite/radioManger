<template>
  <div class="analysis-container">
    <div class="page-header">
      <div>
        <h1>{{ $t('analysis.title') }}</h1>
        <p>{{ $t('analysis.statistics') }}</p>
      </div>
      <el-button @click="refreshStats" :loading="loading">{{ $t('analysis.refreshStats') }}</el-button>
    </div>

    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ stats?.total_qso || 0 }}</div>
            <div class="stat-label">{{ $t('dashboard.totalQSO') }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ stats?.total_dxcc || 0 }}</div>
            <div class="stat-label">{{ $t('dashboard.dxcc') }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ stats?.qsl_sent || 0 }}</div>
            <div class="stat-label">{{ $t('dashboard.qslSent') }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ stats?.lotw_confirmed || 0 }}</div>
            <div class="stat-label">{{ $t('dashboard.lotwConfirmed') }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="stats-row">
      <el-col :span="12">
        <el-card>
          <template #header>{{ $t('analysis.qslStats') }}</template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item :label="$t('dashboard.qslSent')">{{ stats?.qsl_sent || 0 }}</el-descriptions-item>
            <el-descriptions-item :label="$t('dashboard.qslReceived')">{{ stats?.qsl_rcvd || 0 }}</el-descriptions-item>
            <el-descriptions-item label="eQSL Sent">{{ stats?.eqsl_sent || 0 }}</el-descriptions-item>
            <el-descriptions-item label="eQSL Received">{{ stats?.eqsl_rcvd || 0 }}</el-descriptions-item>
            <el-descriptions-item :label="$t('dashboard.lotwConfirmed')">{{ stats?.lotw_confirmed || 0 }}</el-descriptions-item>
            <el-descriptions-item :label="$t('dashboard.totalDistance')">{{ stats?.total_distance || 0 }} {{ $t('analysis.km') }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>{{ $t('analysis.activity') }}</template>
          <div v-if="stats" class="activity-info">
            <p>{{ $t('analysis.totalQso') }}: <strong>{{ stats.total_qso }}</strong></p>
            <p>{{ $t('analysis.dxccEntities') }}: <strong>{{ stats.total_dxcc }}</strong></p>
            <p>{{ $t('analysis.lastQso') }}: <strong>{{ stats.last_qso_date || 'N/A' }}</strong></p>
            <p>{{ $t('analysis.avgDistance') }}: <strong>{{ stats.average_distance || 0 }} {{ $t('analysis.km') }}</strong></p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useStatsStore } from '@/stores/stats'

const statsStore = useStatsStore()
const stats = computed(() => statsStore.statistics)
const loading = computed(() => statsStore.isLoading)

const refreshStats = () => statsStore.fetchStats()
onMounted(() => statsStore.fetchStats())
</script>

<style scoped lang="scss">
.analysis-container {
  .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; h1 { margin-bottom: 5px; } p { color: #909399; } }
  .stats-row { margin-bottom: 16px; }
  .stat-item { text-align: center; padding: 10px 0;
    .stat-value { font-size: 32px; font-weight: bold; color: #409eff; }
    .stat-label { color: #909399; margin-top: 5px; }
  }
  .activity-info p { margin: 8px 0; font-size: 14px; }
}
</style>
