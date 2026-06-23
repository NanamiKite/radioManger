<template>
  <div class="dxcluster-container">

    <!-- ================= HEADER ================= -->
    <div class="page-header">
      <div>
        <h1>🌐 {{ $t('dxcluster.title') }}</h1>
      </div>

      <div class="header-actions">
        <el-tag :type="statusTagType" effect="dark">
          {{ statusText }}
        </el-tag>
      </div>
    </div>

    <!-- ================= CONTROL ================= -->
    <el-card class="control-card" shadow="never">
      <el-row :gutter="16" align="middle">

        <el-col :span="10">
          <span class="control-label">{{ $t('dxcluster.nodes') }}:</span>
          <el-select
            v-model="store.selectedNode"
            value-key="host"
            placeholder="Select Node"
            :disabled="store.isConnected"
            style="width: 100%; margin-left: 8px"
          >
            <el-option
              v-for="n in store.nodes"
              :key="`${n.host}:${n.port}`"
              :label="`${n.name} (${n.country}) — ${n.remark || ''}`"
              :value="n"
            />
          </el-select>
        </el-col>

        <el-col :span="14" style="text-align: right">
          <el-button
            v-if="!store.isConnected"
            type="primary"
            :loading="connecting"
            :disabled="!store.selectedNode"
            @click="handleConnect"
          >
            {{ $t('dxcluster.connect') }}
          </el-button>

          <el-button
            v-else
            type="danger"
            plain
            @click="handleDisconnect"
          >
            {{ $t('dxcluster.disconnect') }}
          </el-button>
        </el-col>

      </el-row>

      <!-- ================= STATUS INFO ================= -->
      <div v-if="store.status" class="status-info">
        <span v-if="store.status.current_node">
          {{ $t('dxcluster.currentNode') }}:
          <strong>{{ store.status.current_node.name }}</strong>
        </span>

        <span v-if="store.status.callsign">
          {{ $t('dxcluster.callsign') }}:
          <strong>{{ store.status.callsign }}</strong>
        </span>

        <span v-if="store.status.connected">
          {{ $t('dxcluster.spotsAmount') }}:
          <strong>{{ store.status.spot_count }}</strong>
        </span>
      </div>
    </el-card>

    <!-- ================= TABLE ================= -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <span>{{ $t('dxcluster.recentSpots') }}</span>
      </template>

      <el-table
        :data="store.spots"
        stripe
        max-height="650"
        :default-sort="{
          prop: 'received_at',
          order: 'descending'
        }"
      >

        <el-table-column prop="freq" :label="$t('dxcluster.freq')" width="140" >
          <template #default="{ row }">
            <strong>{{ formatFreq(row.freq) }}</strong>
          </template>
        </el-table-column>

        <el-table-column prop="band" :label="$t('dxcluster.band')" width="80" >
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.band }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="dx_callsign" :label="$t('dxcluster.callsign')" width="170" >
          <template #default="{ row }">
            <span class="dx-callsign" @click="lookupCall(row.dx_callsign)">
              {{ row.dx_callsign }}
            </span>
          </template>
        </el-table-column>        
        <el-table-column prop="dxcc_entity" :label="$t('dxcluster.dxcc')" width="200" >
          <template #default="{ row }">
            <el-tag v-if="row.dxcc_entity" size="small">{{ row.dxcc_entity }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="mode" :label="$t('dxcluster.mode')" width="90" >
          <template #default="{ row }">
            <el-tag v-if="row.mode" size="small">{{ row.mode }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="spotter" :label="$t('dxcluster.spotter')" width="120" />

        <el-table-column prop="comment" :label="$t('dxcluster.comment')" show-overflow-tooltip />

        <el-table-column
          prop="received_at"
          :label="$t('dxcluster.time')"
          width="160"
          sortable
        >
          <template #default="{ row }">
            {{ formatTime(row.received_at) }}
          </template>
        </el-table-column>

      </el-table>

      <el-empty v-if="store.spots.length === 0" :description="$t('dxcluster.noSpots')" />
    </el-card>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useDxClusterStore } from '@/stores/dxcluster'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'


const store = useDxClusterStore()
const connecting = ref(false)
const { t } = useI18n()

/* ================= STATUS ================= */
const statusTagType = computed(() => {
  if (store.isConnecting) return 'warning'
  return store.isConnected ? 'success' : 'info'
})

const statusText = computed(() => {
  if (store.isConnecting) return 'Connecting'
  return store.isConnected ? 'Connected' : 'Disconnected'
})

/* ================= FORMAT ================= */
const formatFreq = (f: any) => {
  const n = Number(f)
  if (Number.isNaN(n)) return '-'
  return n.toFixed(3)
}

const formatTime = (iso: string) => {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString()
}

/* ================= ACTION ================= */
const lookupCall = (call: string) => {
  window.open(`https://www.qrz.com/db/${call}`, '_blank')
}

const handleConnect = async () => {
  connecting.value = true
  try {
    await store.connect()
    ElMessage.success('Connected')
  } catch (e: any) {
    ElMessage.error(e?.message || 'Connect failed')
  } finally {
    connecting.value = false
  }
}

const handleDisconnect = async () => {
  await store.disconnect()
  ElMessage.info('Disconnected')
}



/* ================= LIFECYCLE ================= */
onMounted(async () => {
  await store.fetchInit()
  if (store.isConnected) {
    store.connectWS()
  }
})

onUnmounted(() => {
  store.disconnectWS()
})
</script>

<style scoped lang="scss">
.dxcluster-container {

  /* ================= HEADER ================= */
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h1 {
      margin: 0 0 4px 0;
      font-size: 22px;
    }
  }
.status-info {
  display: flex;
  align-items: center;
  gap: 24px; /* 控制间距 */
}
  /* ================= CONTROL ================= */
  .control-card {
    margin-bottom: 16px;

    .control-label {
      color: #606266;
    }

    .status-info {
      margin-top: 12px;
      color: #909399;
      font-size: 13px;
    }
  }

  /* ================= TABLE ================= */
  .table-card {
    margin-bottom: 16px;
  }

  .dx-callsign {
    font-weight: 600;
    color: #409eff;
    font-family: monospace;
    cursor: pointer;
  }
}
</style>
