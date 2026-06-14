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
          <span class="callsign-display">{{ result.call_sign }}</span>
          <el-tag v-if="result.cached" type="warning" size="small">{{ $t('auth.cached') }}</el-tag>
          <el-tag v-else type="success" size="small">{{ $t('auth.live') }}</el-tag>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item :label="$t('common.fullName')">{{ result.full_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Country">{{ result.country || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('logs.gridSquare')">{{ result.grid_square || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Latitude">{{ result.latitude ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="Longitude">{{ result.longitude ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="Class">{{ result.class_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="License Date">{{ result.license_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="License Expiry">{{ result.license_exp || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div class="result-actions" v-if="result.qrz_url">
        <el-button link type="primary" @click="openQRZ(result.qrz_url!)">
          {{ $t('auth.opensOnQRZ') }}
        </el-button>
      </div>
    </el-card>

    <el-card v-else-if="searched && !result" class="result-card">
      <el-empty :description="$t('auth.notFoundOnQRZ')" />
    </el-card>
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
    if (err?.response?.status === 404) {
      searched.value = true
    } else {
      ElMessage.error(err?.response?.data?.detail || 'Query failed')
    }
  } finally {
    searching.value = false
    searched.value = true
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
      display: flex; align-items: center; gap: 12px;
      .callsign-display { font-size: 24px; font-weight: bold; letter-spacing: 2px; font-family: monospace; }
    }
    .result-actions { margin-top: 16px; }
  }
}
</style>
