<template>
  <div class="logs-container">
    <div class="page-header">
      <div>
        <h1>{{ $t('logs.title') }}</h1>
        <p>
          {{ $t('nav.logs') }}
          <span v-if="logsStore.activeStation" style="margin-left:12px;color:#409eff;">
             | Active: <strong>{{ logsStore.activeStation.callsign }}</strong>
          </span>
        </p>
      </div>
      <div class="header-actions">
        <el-button @click="showImportDialog = true">{{ $t('common.import') }}</el-button>
        <el-button @click="showExportDialog = true">{{ $t('common.export') }}</el-button>
        <el-button type="primary" @click="showCreateDialog = true">{{ $t('logs.newLog') }}</el-button>
      </div>
    </div>

    <!-- 过滤栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="logsStore.filters" size="small">
        <el-form-item :label="$t('logs.callSign')">
          <el-input v-model="logsStore.filters.call_sign" :placeholder="$t('logs.callSign')" clearable />
        </el-form-item>
        <el-form-item label="Grid">
          <el-input v-model="logsStore.filters.grid_square" placeholder="OL63" clearable
            @input="(v: string) => logsStore.filters.grid_square = v.toUpperCase()" style="width:80px" />
        </el-form-item>
        <el-form-item :label="$t('logs.band')" style="width:120px">
          <el-select v-model="logsStore.filters.band" clearable :placeholder="$t('logs.allBands')">
            <el-option label="160m" value="160m" /><el-option label="80m" value="80m" />
            <el-option label="40m" value="40m" /><el-option label="20m" value="20m" />
            <el-option label="15m" value="15m" /><el-option label="10m" value="10m" />
            <el-option label="6m" value="6m" /><el-option label="2m" value="2m" /><el-option label="70cm" value="70cm" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('logs.mode')" style="width:120px">
          <el-select v-model="logsStore.filters.mode" clearable :placeholder="$t('logs.allModes')">
            <el-option label="FT8" value="FT8" /><el-option label="SSB" value="SSB" />
            <el-option label="CW" value="CW" /><el-option label="FM" value="FM" /><el-option label="AM" value="AM" />
            <el-option label="RTTY" value="RTTY" /><el-option label="SAT" value="SAT" />
          </el-select>
        </el-form-item>
        <!-- 台站过滤 -->
        <el-form-item :label="$t('stations.title')">
          <el-select v-model="logsStore.filters.station_id" clearable placeholder="All Stations" style="width:140px">
            <el-option label="All Stations" :value="null" />
            <el-option v-for="s in logsStore.stations" :key="s.id" :label="s.callsign" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">{{ $t('common.search') }}</el-button>
          <el-button @click="handleReset">{{ $t('common.refresh') }}</el-button>
        </el-form-item>
        <el-form-item>
          <el-button :type="udpRunning ? 'success' : 'info'" @click="toggleUdp" size="small">
            {{ udpRunning ? '🟢 UDP ' + $t('udp.listening') + ' (' + udpCount + ')' : '⚪ UDP ' + $t('udp.stopped') }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志表格 -->
    <el-card class="table-card">
      <el-table :data="logsStore.logs" v-loading="logsStore.isLoading" stripe style="width:100%"
        @sort-change="handleSortChange"
        :default-sort="{ prop: logsStore.sortBy, order: logsStore.sortOrder === 'asc' ? 'ascending' : 'descending' }">
        <el-table-column prop="qso_date" :label="$t('logs.qsoDate')" width="120" sortable="custom" />
        <el-table-column prop="time_on" label="UTC" width="80">
          <template #default="scope">{{ scope.row.time_on ? scope.row.time_on.substring(0, 5) : '-' }}</template>
        </el-table-column>
        <el-table-column prop="station_callsign" label="De Call" width="120">
          <template #default="scope">
            <el-tag size="small" type="info">{{ scope.row.station_callsign || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="call_sign" :label="$t('logs.callSign')" width="130" sortable="custom" />
        <el-table-column prop="dxcc" label="DXCC" width="150" sortable="custom">
          <template #default="scope">
            <el-tag size="small" v-if="scope.row.dxcc" type="warning" effect="plain">{{ scope.row.dxcc }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="band" :label="$t('logs.band')" width="70" sortable="custom" />
        <el-table-column prop="mode" :label="$t('logs.mode')" width="80" sortable="custom" />
        <el-table-column prop="freq" :label="$t('logs.freqMhz')" width="110" sortable="custom">
          <template #default="scope">{{ scope.row.freq ? Number(scope.row.freq).toFixed(4) : '-' }}</template>
        </el-table-column>
        <el-table-column prop="rst_sent" :label="$t('logs.rstSent')" width="90" sortable="custom" />
        <el-table-column prop="rst_rcvd" :label="$t('logs.rstReceived')" width="90" sortable="custom" />
        <el-table-column prop="qsl_rcvd" :label="$t('logs.qslReceived')" width="80" sortable="custom" />
        <el-table-column prop="grid_square" :label="$t('logs.gridSquare')" width="100" sortable="custom" />
        <el-table-column prop="comment" :label="$t('logs.comment')" min-width="150" show-overflow-tooltip />
        <el-table-column :label="$t('common.operations')" width="160" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="viewLog(scope.row.id)">{{ $t('common.edit') }}</el-button>
            <el-button size="small" type="danger" @click="handleDelete(scope.row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="logsStore.pagination.page"
          v-model:page-size="logsStore.pagination.page_size"
          :total="logsStore.pagination.total"
          :page-sizes="[10,20,50,100]"
          layout="total, sizes, prev, pager, next"
          @change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 导入对话框 -->
    <el-dialog v-model="showImportDialog" :title="$t('logs.importLogs')" width="500px">
      <el-upload drag accept=".adi,.adif" :auto-upload="false" :limit="1"
        :on-change="handleFileChange" :file-list="importFileList"
        :on-remove="() => { importFile = null; importFileList = [] }">
        <el-icon style="font-size:48px;color:#c0c4cc"><UploadFilled /></el-icon>
        <div class="el-upload__text">Drop .adi/.adif file here or <em>click to browse</em></div>
      </el-upload>
      <div v-if="importResult" style="margin-top:12px">
        <el-alert
          :title="`Imported: ${importResult.imported} | Duplicates: ${importResult.duplicates || 0} | QSL Updated: ${importResult.updated || 0} | Errors: ${importResult.skipped}`"
          :type="importResult.errors?.length ? 'warning' : 'success'" show-icon />
        <el-table v-if="importResult.errors?.length" :data="importResult.errors" size="small" style="margin-top:8px" max-height="200">
          <el-table-column prop="line" label="Line" width="60" />
          <el-table-column prop="error" label="Error" />
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showImportDialog = false; importFile=null; importFileList=[]; importResult=null">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleImport" :loading="importing" :disabled="!importFile">{{ $t('common.import') }}</el-button>
      </template>
    </el-dialog>

    <!-- 导出对话框 -->
    <el-dialog v-model="showExportDialog" :title="$t('logs.exportLogs')" width="500px">
      <el-form label-width="120px">
        <el-form-item :label="$t('stations.title')">
          <el-select v-model="exportStationId" clearable :placeholder="$t('logs.allStations')" style="width:100%"
            @change="onExportStationChange">
            <el-option :label="$t('logs.allStations')" :value="null" />
            <el-option v-for="s in logsStore.stations" :key="s.id" :label="s.callsign" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('logs.location')" v-if="exportStationId">
          <el-select v-model="exportLocationId" clearable :placeholder="$t('logs.allLocations')" style="width:100%">
            <el-option :label="$t('logs.allLocations')" :value="null" />
            <el-option v-for="l in exportLocations" :key="l.id"
              :label="l.name + ' (' + (l.grid_square || '-') + ')'" :value="l.id" />
          </el-select>
          <div v-if="exportLocationId" style="font-size:12px;color:#909399;margin-top:4px">
            {{ $t('logs.exportGridFilter') }}
          </div>
        </el-form-item>
        <el-form-item :label="$t('logs.qsoDate')">
          <el-date-picker v-model="exportRange" type="daterange" range-separator="~"
            :start-placeholder="$t('logs.qsoDate')" :end-placeholder="$t('logs.qsoDate')"
            value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item :label="$t('logs.band')">
          <el-select v-model="exportBand" clearable :placeholder="$t('logs.allBands')" style="width:100%">
            <el-option label="160m" value="160m" /><el-option label="80m" value="80m" />
            <el-option label="40m" value="40m" /><el-option label="20m" value="20m" />
            <el-option label="15m" value="15m" /><el-option label="10m" value="10m" />
          </el-select>
        </el-form-item>
        <el-form-item label="Format">
          <el-radio-group v-model="exportFormat">
            <el-radio value="adi">ADI</el-radio>
            <el-radio value="adif">ADIF</el-radio>
          </el-radio-group>
        </el-form-item>
        <p v-if="logsStore.activeStation && !exportStationId" style="font-size:12px;color:#909399;text-align:center;">
          {{ $t('logs.exportNoStation') }}
        </p>
        <p v-else-if="exportStationId && !exportLocationId" style="font-size:12px;color:#409eff;text-align:center;">
          {{ $t('logs.exportStation') }}: <strong>{{ logsStore.stations.find(s=>s.id===exportStationId)?.callsign }}</strong>
        </p>
        <p v-else-if="exportLocationId" style="font-size:12px;color:#67c23a;text-align:center;">
          {{ $t('logs.exportLocation') }}: <strong>{{ exportLocations.find(l=>l.id===exportLocationId)?.name }}</strong>
          ({{ exportLocations.find(l=>l.id===exportLocationId)?.grid_square }})
        </p>
      </el-form>
      <template #footer>
        <el-button @click="showExportDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleExport" :loading="exporting">{{ $t('common.export') }}</el-button>
      </template>
    </el-dialog>

    <!-- 新建日志对话框 -->
    <el-dialog v-model="showCreateDialog" :title="$t('logs.newLog')" width="600px">
      <el-form ref="createFormRef" :model="createForm" :rules="logRules" label-width="120px">
        <el-form-item :label="$t('logs.stationId')">
          <el-tag type="info" style="font-size:14px;padding:8px 16px;">
            {{ logsStore.activeStation?.callsign || 'No active station' }}
          </el-tag>
        </el-form-item>
        <el-form-item :label="$t('logs.callSign')" prop="call_sign">
          <el-input v-model="createForm.call_sign" :placeholder="$t('logs.callSign')" @input="(v: string) => createForm.call_sign = v.toUpperCase()" />
        </el-form-item>
        <el-form-item :label="$t('logs.qsoDate')" prop="qso_date">
          <el-date-picker v-model="createForm.qso_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="Time (UTC)">
          <el-time-picker v-model="createForm.time_on" value-format="HH:mm:ss" placeholder="UTC+0" style="width:100%" />
        </el-form-item>
        <el-form-item :label="$t('logs.band')" prop="band">
          <el-select v-model="createForm.band" @change="handleBandChange" style="width:100%">
            <el-option label="2190m" value="2190m" />
            <el-option label="160m" value="160m" /><el-option label="80m" value="80m" />
            <el-option label="40m" value="40m" /><el-option label="20m" value="20m" />
            <el-option label="15m" value="15m" /><el-option label="10m" value="10m" />
            <el-option label="6m" value="6m" /><el-option label="2m" value="2m" />
            <el-option label="70cm" value="70cm" /><el-option label="23cm" value="23cm" />
            <el-option label="13cm" value="13cm" /><el-option label="5cm" value="5cm" />
            <el-option label="3cm" value="3cm" /><el-option label="1.2cm" value="1.2cm"/>
            <el-option label="6mm" value="6mm" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('logs.frequency')" prop="frequency">
          <el-input v-model="createForm.freq" :placeholder="$t('logs.frequency')" />
        </el-form-item>
        <el-form-item :label="$t('logs.mode')" prop="mode">
          <el-select v-model="createForm.mode" style="width:100%">
            <el-option label="FT8" value="FT8" /><el-option label="SSB" value="SSB" />
            <el-option label="CW" value="CW" /><el-option label="FM" value="FM" /><el-option label="RTTY" value="RTTY" /><el-option label="SAT" value="SAT" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('logs.gridSquare')">
          <el-input v-model="createForm.grid_square" :placeholder="$t('logs.gridSquare')" @input="(v: string) => createForm.grid_square = v.toUpperCase()" />
        </el-form-item>
        <el-form-item :label="$t('logs.qslSent')">
          <el-select v-model="createForm.qsl_sent" style="width:100%">
            <el-option :label="$t('logs.no')" value="N" /><el-option :label="$t('logs.yes')" value="Y" />
            <el-option :label="$t('logs.requested')" value="R" /><el-option :label="$t('logs.ignore')" value="I" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('logs.comment')">
          <el-input v-model="createForm.comment" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleCreate" :loading="submitting">{{ $t('common.submit') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useLogsStore } from '@/stores/logs'
import { logsApi } from '@/api/logs'
import { udpApi } from '@/api/udp'
import { locationsApi } from '@/api/locations'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import type { FormInstance } from 'element-plus'
import { el } from 'date-fns/locale'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { t: $t } = useI18n()
const logsStore = useLogsStore()

// UDP 监听状态
const udpRunning = ref(false)
const udpCount = ref(0)
let udpWs: WebSocket | null = null

// 新建
const showCreateDialog = ref(false)
const submitting = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  station_id: 0, call_sign: '', qso_date: '', time_on: '',
  band: '20m', freq: '14.0000', mode: 'FT8', qsl_sent: 'N', qsl_rcvd: 'N', comment: '', grid_square: ''
})
const logRules = {
  call_sign: [{ required: true, message: 'Please enter callsign', trigger: 'blur' }],
  qso_date: [{ required: true, message: 'Please select date', trigger: 'change' }],
  band: [{ required: true, message: 'Please select band', trigger: 'change' }],
  mode: [{ required: true, message: 'Please select mode', trigger: 'change' }]
}

const bandFrequencyMap: Record<string, string> = {
  '2190m': '0.1375',
  '160m': '1.800',
  '80m': '3.500',
  '40m': '7.000',
  '20m': '14.000',
  '15m': '21.000',
  '10m': '28.000',
  '6m': '50.000',
  '4m': '70.000',
  '2m': '144.000',
  '70cm': '430.000',
  '23cm': '1240.000',
  '13cm': '2300.000',
  '5cm': '5760.000',
  '3cm': '10000.000',
  '1.2cm': '24000.000',
  '6mm': '47000.000',
}

// 2. 切换波段时的联动处理函数
const handleBandChange = (val: string) => {
  // 根据选中的波段获取默认频率，如果找不到则清空或保持原样
  if (bandFrequencyMap[val]) {
    createForm.freq = bandFrequencyMap[val]
  }
}

// 导入
const showImportDialog = ref(false)
const importing = ref(false)
const importFile = ref<File | null>(null)
const importFileList = ref<any[]>([])
const importResult = ref<any>(null)

const handleFileChange = (uploadFile: any) => {
  if (uploadFile.raw) {
    importFile.value = uploadFile.raw
    importFileList.value = [uploadFile]
  }
  return false
}

const handleImport = async () => {
  if (!importFile.value) { ElMessage.warning($t('common.selectFile')); return }
  importing.value = true; importResult.value = null
  try {
    const res = await logsApi.importLogs(importFile.value, logsStore.activeStation?.id)
    importResult.value = res; ElMessage.success(`${$t('common.imported')} ${res.imported} ${$t('common.records')}`); logsStore.fetchLogs()
  } catch (err: any) { ElMessage.error(err?.response?.data?.detail || $t('common.importFailed')) }
  finally { importing.value = false }
}

// 导出
const showExportDialog = ref(false)
const exporting = ref(false)
const exportStationId = ref<number | null>(null)
const exportLocationId = ref<number | null>(null)
const exportLocations = ref<any[]>([])
const exportRange = ref<any>(null)
const exportBand = ref('')
const exportFormat = ref('adi')

const onExportStationChange = async (sid: number | null) => {
  exportLocationId.value = null
  exportLocations.value = []
  if (sid) {
    try {
      const res: any = await locationsApi.list(sid)
      exportLocations.value = Array.isArray(res) ? res : []
    } catch { exportLocations.value = [] }
  }
}
const handleExport = () => {
  exporting.value = true
  try {
    logsApi.exportLogs({
      format: exportFormat.value,
      start_date: exportRange.value?.[0] || undefined,
      end_date: exportRange.value?.[1] || undefined,
      band: exportBand.value || undefined,
      station_id: exportStationId.value,
      location_id: exportLocationId.value,
    })
    showExportDialog.value = false
  } catch { ElMessage.error($t('common.exportFailed')) }
  finally { exporting.value = false }
}

// 默认只展示激活台站的日志
const applyActiveStationFilter = () => {
  if (logsStore.activeStation) {
    logsStore.filters.station_id = logsStore.activeStation.id
  }
}

const updateUtcNow = () => {
  const now = new Date()
  createForm.qso_date = now.toISOString().substring(0, 10)
  createForm.time_on = now.toISOString().substring(11, 19)
}

// ── UDP 监听控制 ──
function toggleUdp() {
  if (udpRunning.value) {
    udpApi.stop().then(() => {
      udpRunning.value = false
      if (udpWs) { udpWs.close(); udpWs = null }
    })
  } else {
    udpApi.start().then(() => {
      udpRunning.value = true
      connectUdpWs()
    })
  }
}

function connectUdpWs() {
  const token = authStore.token
  if (!token) return
  udpWs = udpApi.createWebSocket(token)
  udpWs.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      if (msg.type === 'qso_received') {
        udpCount.value = msg.count || udpCount.value + 1
        logsStore.fetchLogs()
        ElMessage.success(`UDP QSO: ${msg.data.call_sign} ${msg.data.band || ''} ${msg.data.mode || ''}`)
      }
    } catch {}
  }
  udpWs.onclose = () => { udpRunning.value = false }
  udpWs.onerror = () => { udpRunning.value = false }
}

async function checkUdpStatus() {
  try {
    const res = await udpApi.getStatus()
    udpRunning.value = res.data.running
    udpCount.value = res.data.qso_count || 0
    if (udpRunning.value) connectUdpWs()
  } catch {}
}

onMounted(async () => {
  await logsStore.fetchStations()
  applyActiveStationFilter()
  // 从地图跳转时读取网格筛选参数
  const gridQuery = route.query.grid as string
  if (gridQuery) {
    logsStore.filters.grid_square = gridQuery.toUpperCase()
  }
  await logsStore.fetchLogs()
  if (logsStore.activeStation) createForm.station_id = logsStore.activeStation.id
  updateUtcNow()
  checkUdpStatus()
})

watch(() => logsStore.activeStation, (s) => {
  if (s) {
    createForm.station_id = s.id
    // 激活台站变化时自动切换日志过滤并刷新
    logsStore.filters.station_id = s.id
    logsStore.fetchLogs()
  }
})

const handleSortChange = (sort: { prop?: string; order?: string }) => {
  if (sort.prop && sort.order) {
    logsStore.sortBy = sort.prop
    logsStore.sortOrder = sort.order === 'ascending' ? 'asc' : 'desc'
  } else {
    logsStore.sortBy = 'qso_date'
    logsStore.sortOrder = 'desc'
  }
  logsStore.fetchLogs()
}

const handleSearch = () => { logsStore.pagination.page = 1; logsStore.fetchLogs() }
const handleReset = () => { logsStore.clearFilters(); logsStore.fetchLogs() }
const handlePageChange = () => { logsStore.fetchLogs() }
const viewLog = (id: number) => router.push({ name: 'LogDetail', params: { id } })

const handleCreate = async () => {
  try {
    if (!logsStore.activeStation || !logsStore.activeStation.id) {
      ElMessage.warning('No active station with a configured location. Please create a station and location first.')
      showCreateDialog.value = false
      router.push({ name: 'Stations' })
      return
    }
    await createFormRef.value?.validate()
    submitting.value = true
    createForm.station_id = logsStore.activeStation.id
    // 自动填入 UTC 时间（如果没有手动修改）
    if (!createForm.time_on) {
      const now = new Date()
      createForm.time_on = now.toISOString().substring(11, 19)
    }
    await logsStore.createLog(createForm)
    ElMessage.success($t('common.success')); showCreateDialog.value = false
    resetCreateForm()
  } catch (err: any) { ElMessage.error(err?.response?.data?.detail || err.message || $t('errors.serverError')) }
  finally { submitting.value = false }
}

const resetCreateForm = () => {
  const now = new Date()
  const utcDate = now.toISOString().substring(0, 10)
  const utcTime = now.toISOString().substring(11, 19)
  Object.assign(createForm, {
    call_sign: '', qso_date: utcDate, time_on: utcTime,
    band: '20m', freq: '', mode: 'FT8',
    qsl_sent: 'N', qsl_rcvd: 'N', comment: ''
  })
}

const handleDelete = async (log: any) => {
  try {
    await ElMessageBox.confirm($t('logs.confirmDeleteMsg'), $t('common.confirmDelete'), { type: 'warning' })
    await logsStore.deleteLog(log.id); ElMessage.success($t('common.success'))
  } catch { /* cancelled */ }
}
</script>

<style scoped lang="scss">
.logs-container {
  .page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;
    h1 { margin-bottom:5px; } p { color:#909399; } .header-actions { display:flex; gap:8px; } }
  .filter-card { margin-bottom:16px; }
  .table-card { margin-bottom:16px; }
  .pagination-wrapper { margin-top:16px; display:flex; justify-content:flex-end; }
}
</style>
