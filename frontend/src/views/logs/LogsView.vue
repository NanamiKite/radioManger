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
        <el-form-item :label="$t('logs.band')">
          <el-select v-model="logsStore.filters.band" clearable :placeholder="$t('logs.allBands')">
            <el-option label="160m" value="160m" /><el-option label="80m" value="80m" />
            <el-option label="40m" value="40m" /><el-option label="20m" value="20m" />
            <el-option label="15m" value="15m" /><el-option label="10m" value="10m" />
            <el-option label="6m" value="6m" /><el-option label="2m" value="2m" /><el-option label="70cm" value="70cm" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('logs.mode')">
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
      </el-form>
    </el-card>

    <!-- 日志表格 -->
    <el-card class="table-card">
      <el-table :data="logsStore.logs" v-loading="logsStore.isLoading" stripe style="width:100%"
        @sort-change="handleSortChange"
        :default-sort="{ prop: logsStore.sortBy, order: logsStore.sortOrder === 'asc' ? 'ascending' : 'descending' }">
        <el-table-column prop="qso_date" :label="$t('logs.qsoDate')" width="120" sortable="custom" />
        <el-table-column prop="station_callsign" label="De Call" width="120">
          <template #default="scope">
            <el-tag size="small" type="info">{{ scope.row.station_callsign || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="call_sign" :label="$t('logs.callSign')" width="130" sortable="custom" />
        <el-table-column prop="dxcc" label="DXCC" width="110" sortable="custom">
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
        <el-table-column prop="qsl_sent" :label="$t('logs.qslSent')" width="80" sortable="custom" />
        <el-table-column prop="qsl_rcvd" :label="$t('logs.qslReceived')" width="80" sortable="custom" />
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
          :title="`Imported: ${importResult.imported} | Duplicates skipped: ${importResult.duplicates || 0} | Errors: ${importResult.skipped}`"
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
          <el-select v-model="exportStationId" clearable placeholder="All Stations" style="width:100%">
            <el-option label="All Stations" :value="null" />
            <el-option v-for="s in logsStore.stations" :key="s.id" :label="s.callsign" :value="s.id" />
          </el-select>
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
          No station selected — will export <strong>all stations</strong>
        </p>
        <p v-else-if="exportStationId" style="font-size:12px;color:#409eff;text-align:center;">
          Exporting station: <strong>{{ logsStore.stations.find(s=>s.id===exportStationId)?.callsign }}</strong>
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
          <el-input v-model="createForm.call_sign" :placeholder="$t('logs.callSign')" @input="v => createForm.call_sign = v.toUpperCase()" />
        </el-form-item>
        <el-form-item :label="$t('logs.qsoDate')" prop="qso_date">
          <el-date-picker v-model="createForm.qso_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item :label="$t('logs.band')" prop="band">
          <el-select v-model="createForm.band" style="width:100%">
            <el-option label="160m" value="160m" /><el-option label="80m" value="80m" />
            <el-option label="40m" value="40m" /><el-option label="20m" value="20m" />
            <el-option label="15m" value="15m" /><el-option label="10m" value="10m" /><el-option label="6m" value="6m" /><el-option label="2m" value="2m" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('logs.mode')" prop="mode">
          <el-select v-model="createForm.mode" style="width:100%">
            <el-option label="FT8" value="FT8" /><el-option label="SSB" value="SSB" />
            <el-option label="CW" value="CW" /><el-option label="FM" value="FM" /><el-option label="RTTY" value="RTTY" /><el-option label="SAT" value="SAT" />
          </el-select>
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
import { useRouter } from 'vue-router'
import { useLogsStore } from '@/stores/logs'
import { logsApi } from '@/api/logs'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import type { FormInstance } from 'element-plus'

const router = useRouter()
const { t: $t } = useI18n()
const logsStore = useLogsStore()

// 新建
const showCreateDialog = ref(false)
const submitting = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  station_id: 0, call_sign: '', qso_date: '',
  band: '20m', mode: 'FT8', qsl_sent: 'N', qsl_rcvd: 'N', comment: ''
})
const logRules = {
  call_sign: [{ required: true, message: 'Please enter callsign', trigger: 'blur' }],
  qso_date: [{ required: true, message: 'Please select date', trigger: 'change' }],
  band: [{ required: true, message: 'Please select band', trigger: 'change' }],
  mode: [{ required: true, message: 'Please select mode', trigger: 'change' }]
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
const exportRange = ref<any>(null)
const exportBand = ref('')
const exportFormat = ref('adi')
const handleExport = () => {
  exporting.value = true
  try {
    logsApi.exportLogs({
      format: exportFormat.value,
      start_date: exportRange.value?.[0] || undefined,
      end_date: exportRange.value?.[1] || undefined,
      band: exportBand.value || undefined,
      station_id: exportStationId.value,
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

onMounted(async () => {
  await logsStore.fetchStations()
  applyActiveStationFilter()
  await logsStore.fetchLogs()
  if (logsStore.activeStation) createForm.station_id = logsStore.activeStation.id
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
    // 检查是否有激活台站
    if (!logsStore.activeStation || !logsStore.activeStation.id) {
      ElMessage.warning('No active station with a configured location. Please create a station and location first.')
      showCreateDialog.value = false
      router.push({ name: 'Stations' })
      return
    }
    await createFormRef.value?.validate()
    submitting.value = true
    createForm.station_id = logsStore.activeStation.id
    await logsStore.createLog(createForm)
    ElMessage.success($t('common.success')); showCreateDialog.value = false
    Object.assign(createForm, { call_sign: '', qso_date: '', band: '20m', mode: 'FT8', qsl_sent: 'N', qsl_rcvd: 'N', comment: '' })
  } catch (err: any) { ElMessage.error(err?.response?.data?.detail || err.message || $t('errors.serverError')) }
  finally { submitting.value = false }
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
