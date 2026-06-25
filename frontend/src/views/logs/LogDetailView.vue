<template>
  <div class="log-detail-container">
    <div class="page-header">
      <el-button @click="goBack">&larr; {{ $t('common.back') }}</el-button>
      <h1>{{ $t('logs.logDetail') }}</h1>
    </div>

    <el-card v-if="log" class="detail-card">
      <el-descriptions :column="2" border>
        <el-descriptions-item :label="$t('logs.callSign')" width="150">{{ log.call_sign }}</el-descriptions-item>
        <el-descriptions-item :label="$t('logs.qsoDate')">{{ log.qso_date }}</el-descriptions-item>
        <el-descriptions-item :label="$t('logs.timeUtc')">{{ log.time_on || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('logs.band')">{{ log.band || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('logs.mode')">{{ log.mode || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('logs.freqMhz')">{{ log.freq ? Number(log.freq).toFixed(4) + $t('logs.mhz') : '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('logs.rstSent')">{{ log.rst_sent || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('logs.rstReceived')">{{ log.rst_rcvd || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('logs.qslSent')">{{ log.qsl_sent || 'N' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('logs.qslReceived')">{{ log.qsl_rcvd || 'N' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('logs.gridSquare')">{{ log.grid_square || '-' }}</el-descriptions-item>
        <el-descriptions-item label="DXCC">{{ log.dxcc || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('logs.comment')" :span="2">{{ log.comment || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div class="detail-actions">
        <el-button type="primary" @click="editing = true">{{ $t('common.edit') }}</el-button>
        <el-button type="danger" @click="handleDelete">{{ $t('common.delete') }}</el-button>
      </div>
    </el-card>

    <el-empty v-else-if="!loading" :description="$t('logs.logNotFound')" />
<!-- 编辑日志表单 -->
    <el-dialog v-model="editing" :title="$t('logs.editLogTitle')" width="600px">
      <el-form ref="editFormRef" :model="editForm" :rules="logRules" label-width="120px">
        <el-form-item :label="$t('logs.callSign')">
          <el-input v-model="editForm.call_sign" @input="(v: string) => editForm.call_sign = v.toUpperCase()" />
        </el-form-item>
        <el-form-item :label="$t('logs.qsoDate')" prop="qso_date">
          <el-date-picker v-model="editForm.qso_date" @input="editForm.qso_date = $event" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item :label="$t('logs.timeUtc')" prop="time_on">
          <el-time-picker v-model="editForm.time_on" @input="editForm.time_on = $event" value-format="HH:mm:ss" :placeholder="$t('logs.utcHint')" style="width:100%" />
        </el-form-item>
        <el-form-item :label="$t('logs.band')">
          <el-select v-model="editForm.band" @change="handleBandChange" style="width: 100%">
            <el-option label="2190m" value="2190m" />
            <el-option label="160m" value="160m" />
            <el-option label="80m" value="80m" />
            <el-option label="40m" value="40m" />
            <el-option label="20m" value="20m" />
            <el-option label="15m" value="15m" />
            <el-option label="10m" value="10m" />
            <el-option label="6m" value="6m" />
            <el-option label="2m" value="2m" />
            <el-option label="70cm" value="70cm" />
            <el-option label="23cm" value="23cm" />
            <el-option label="13cm" value="13cm" />
            <el-option label="5cm" value="5cm" />
            <el-option label="3cm" value="3cm" />
            <el-option label="1.2cm" value="1.2cm" />
            <el-option label="6mm" value="6mm" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('logs.frequency')" prop="frequency">
          <el-input v-model="editForm.freq" :placeholder="$t('logs.frequency')" />
        </el-form-item>
        <el-form-item :label="$t('logs.mode')">
          <el-select v-model="editForm.mode" style="width: 100%">
            <el-option label="FT8" value="FT8" /><el-option label="SSB" value="SSB" />
            <el-option label="CW" value="CW" /><el-option label="FM" value="FM" /><el-option label="RTTY" value="RTTY" /><el-option label="SAT" value="SAT" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('logs.gridSquare')">
          <el-input v-model="editForm.grid_square" :placeholder="$t('logs.gridSquare')" @input="(v: string) => editForm.grid_square = v.toUpperCase()" />
        </el-form-item>
        <el-form-item :label="$t('logs.rstSent')">
          <el-input v-model="editForm.rst_sent" />
        </el-form-item>
        <el-form-item :label="$t('logs.rstReceived')">
          <el-input v-model="editForm.rst_rcvd" />
        </el-form-item>
        <el-form-item :label="$t('logs.qslSent')">
          <el-select v-model="editForm.qsl_sent" style="width: 100%">
            <el-option :label="$t('logs.no')" value="N" />
            <el-option :label="$t('logs.yes')" value="Y" />
            <el-option :label="$t('logs.requested')" value="R" />
            <el-option :label="$t('logs.ignore')" value="I" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('logs.qslReceived')">
          <el-select v-model="editForm.qsl_rcvd" style="width: 100%">
            <el-option :label="$t('logs.no')" value="N" />
            <el-option :label="$t('logs.yes')" value="Y" />
            <el-option :label="$t('logs.requested')" value="R" />
            <el-option :label="$t('logs.ignore')" value="I" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('logs.comment')">
          <el-input v-model="editForm.comment" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editing = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleUpdate" :loading="submitting">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { logsApi } from '@/api/logs'
import { ElFormItem, ElMessage, ElMessageBox, ElOption } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { getDefaultFrequency } from '@/utils/constants'
import type { QSOLog } from '@/types'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const logId = Number(route.params.id)

const log = ref<QSOLog | null>(null)
const loading = ref(false)
const editing = ref(false)
const submitting = ref(false)
const editFormRef = ref<FormInstance>()

const editForm = reactive({
  station_id: 0, call_sign: '', qso_date: '', time_on: '',rst_sent: '', rst_rcvd: '',
  band: '20m', freq: '14.0000', mode: 'FT8', qsl_sent: 'N', qsl_rcvd: 'N', comment: '', grid_square: ''
})

const logRules = {
  call_sign: [{ required: true, message: t('logs.pleaseEnterCallsign'), trigger: 'blur' }],
  qso_date: [{ required: true, message: t('logs.pleaseSelectDate'), trigger: 'change' }],
  band: [{ required: true, message: t('logs.pleaseSelectBand'), trigger: 'change' }],
  mode: [{ required: true, message: t('logs.pleaseSelectMode'), trigger: 'change' }]
}

onMounted(async () => {
  loading.value = true
  try {
    log.value = await logsApi.get(logId)
    if (log.value) {
      Object.assign(editForm, {
        station_id: log.value.station_id || 0,
        call_sign: log.value.call_sign, band: log.value.band || '', mode: log.value.mode || '',
        rst_sent: log.value.rst_sent || '', rst_rcvd: log.value.rst_rcvd || '',
        qsl_sent: log.value.qsl_sent || 'N', qsl_rcvd: log.value.qsl_rcvd || 'N',
        comment: log.value.comment || '', grid_square: log.value.grid_square || '',
        qso_date: log.value.qso_date || '', time_on: log.value.time_on || '',
        freq: log.value.freq ? String(log.value.freq) : '',
      })
    }
  } catch { ElMessage.error(t('errors.serverError')) } finally { loading.value = false }
})

const handleBandChange = (val: string) => {
  const freq = getDefaultFrequency(val)
  if (freq) {
    editForm.freq = freq
  }
}

const goBack = () => router.push({ name: 'Logs' })

const handleUpdate = async () => {
  await editFormRef.value?.validate()
  submitting.value = true
  try {
    await logsApi.update(logId, editForm)
    ElMessage.success(t('common.success'))
    editing.value = false
    log.value = await logsApi.get(logId)
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || t('errors.serverError'))
  } finally { submitting.value = false }
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(t('logs.confirmDeleteMsg'), t('common.confirmDelete'), { type: 'warning' })
    await logsApi.delete(logId)
    ElMessage.success(t('common.success'))
    router.push({ name: 'Logs' })
  } catch { /* cancelled */ }
}
</script>

<style scoped lang="scss">
.log-detail-container {
  .page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
  .detail-actions { margin-top: 20px; display: flex; gap: 10px; }
}
</style>
