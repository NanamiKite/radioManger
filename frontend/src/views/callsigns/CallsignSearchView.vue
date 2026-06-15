<template>
  <div class="callsign-container">
    <div class="page-header">
      <div>
        <h1>{{ $t('auth.searchCallsign') }}</h1>
        <p>{{ $t('auth.searchCallsignHint') }}</p>
      </div>
    </div>

    <el-card class="search-card">
      <el-form :inline="true" @submit.prevent="handleSearch">
        <el-form-item :label="$t('logs.callSign')">
          <el-input
            v-model="callsign"
            :placeholder="$t('auth.enterCallsign')"
            style="width: 220px"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch" :loading="searching">{{ $t('auth.lookup') }}</el-button>
          <el-button @click="callsign = ''; result = null">{{ $t('auth.clear') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" class="result-card">
      <template #header>
        <div class="result-header">
          <div class="header-left">
            <span class="callsign-display">{{ result.call_sign }}</span>
            <el-tag v-if="result.offline" type="info" size="small">Offline</el-tag>
            <el-tag v-else-if="result.cached" type="warning" size="small">{{ $t('auth.cached') }}</el-tag>
            <el-tag v-else type="success" size="small">{{ $t('auth.live') }}</el-tag>
          </div>
          <el-button v-if="result.qrz_url" link type="primary" size="small" @click="openQRZ(result.qrz_url!)">
            QRZ.com →
          </el-button>
        </div>
        <div v-if="result.offline" style="margin-top: 6px; font-size: 12px; color: #909399;">
          {{ $t('auth.offlineHint') }}
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item :label="$t('callsign.fullName')" :span="2">{{ result.full_name || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('callsign.country')">{{ result.country || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('callsign.gridSquare')">{{ result.grid_square || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('callsign.address')" :span="2">{{ result.address || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('callsign.class')">{{ result.class_type || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('callsign.previousCalls')">{{ result.previous_call || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('callsign.licenseDate')">{{ result.license_date || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('callsign.licenseExp')">{{ result.license_exp || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('callsign.cqZone')">{{ result.cq_zone || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('callsign.ituZone')">{{ result.itu_zone || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('callsign.email')" :span="1">{{ result.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Phone">{{ result.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="URL" :span="2">{{ result.url || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div v-if="result.latitude && result.longitude" class="coordinates">
        {{ $t('callsign.coordinates') }}: {{ result.latitude }}, {{ result.longitude }}
      </div>
    </el-card>

    <el-empty v-else-if="searched" :description="$t('auth.notFoundOnQRZ')" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { callsignsApi } from '@/api/callsigns'
import { ElMessage } from 'element-plus'
import type { CallsignInfo } from '@/types'

const callsign = ref('')
const result = ref<CallsignInfo | null>(null)
const searching = ref(false)
const searched = ref(false)

const handleSearch = async () => {
  if (!callsign.value.trim()) return
  searching.value = true
  searched.value = false
  result.value = null
  try {
    const data = await callsignsApi.lookup(callsign.value.trim().toUpperCase())
    result.value = data
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || 'Query failed')
  } finally {
    searching.value = false
  }
}

const openQRZ = (url: string) => {
  window.open(url, '_blank')
}
</script>

<style scoped lang="scss">
.callsign-container {
  .page-header { margin-bottom: 20px; h1 { margin-bottom: 5px; } p { color: #909399; } }
  .search-card { margin-bottom: 16px; }
  .result-card {
    .result-header {
      display: flex; justify-content: space-between; align-items: center;
      .header-left { display: flex; align-items: center; gap: 12px; }
      .callsign-display { font-size: 24px; font-weight: bold; letter-spacing: 2px; font-family: monospace; }
    }
    .coordinates { margin-top: 12px; font-size: 13px; color: #606266; }
  }
}
</style>
