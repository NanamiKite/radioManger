<template>
  <div class="analysis-container">
    <h1>Analysis</h1>
    <p>View your amateur radio statistics and analysis</p>

    <div class="analysis-content">
      <el-button type="primary" @click="refreshStats">Refresh Stats</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useStatsStore } from '@/stores/stats'

const statsStore = useStatsStore()

const refreshStats = (): void => {
  statsStore.fetchStats()
}
</script>

<style scoped lang="scss">
.analysis-container {
  h1 {
    margin-bottom: 10px;
  }

  p {
    color: #909399;
    margin-bottom: 20px;
  }

  .analysis-content {
    background: white;
    border-radius: 8px;
    padding: 20px;
  }
}
</style>
