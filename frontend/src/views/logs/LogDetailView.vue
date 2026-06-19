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
        <el-descriptions-item :label="$t('logs.band')">{{ log.band || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('logs.mode')">{{ log.mode || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('logs.freqMhz')">{{ log.freq ? Number(log.freq).toFixed(4) + ' MHz' : '-' }}</el-descriptions-item>
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

    <el-empty v-else-if="!loading" :description="'Log not found'" />

    <el-dialog v-model="editing" :title="$t('logs.editLogTitle')" width="600px">
      <el-form :model="editForm" label-width="120px">
        <el-form-item :label="$t('logs.callSign')">
          <el-input v-model="editForm.call_sign" @input="(v: string) => editForm.call_sign = v.toUpperCase()" />
        </el-form-item>
        <el-form-item :label="$t('logs.band')">
          <el-select v-model="editForm.band" @change="handleBandChange" style="width: 100%">
            <el-option label="160m" value="160m" />
            <el-option label="80m" value="80m" />
            <el-option label="40m" value="40m" />
            <el-option label="20m" value="20m" />
            <el-option label="15m" value="15m" />
            <el-option label="10m" value="10m" />
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
          <el-input v-model="editForm.grid_square" :placeholder="$t('logs.gridSquare')" />
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import type { QSOLog } from '@/types'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const logId = Number(route.params.id)

const log = ref<QSOLog | null>(null)
const loading = ref(false)
const editing = ref(false)
const submitting = ref(false)

const editForm = reactive({
  call_sign: '', band: '', mode: '', rst_sent: '', rst_rcvd: '',
  qsl_sent: 'N', freq: '', qsl_rcvd: 'N', comment: '', grid_square: ''
})

onMounted(async () => {
  loading.value = true
  try {
    log.value = await logsApi.get(logId)
    if (log.value) {
      Object.assign(editForm, {
        call_sign: log.value.call_sign, band: log.value.band || '', mode: log.value.mode || '',
        rst_sent: log.value.rst_sent || '', rst_rcvd: log.value.rst_rcvd || '',
        qsl_sent: log.value.qsl_sent || 'N', qsl_rcvd: log.value.qsl_rcvd || 'N', comment: log.value.comment || ''
      })
    }
  } catch { ElMessage.error(t('errors.serverError')) } finally { loading.value = false }
})

const bandFrequencyMap: Record<string, string> = {
  '160m': '1.800',
  '80m': '3.500',
  '40m': '7.000',
  '20m': '14.000',
  '15m': '21.000',
  '10m': '28.000',
  '6m': '50.000',
  '2m': '144.000'
}


const handleBandChange = (val: string) => {
  // 根据选中的波段获取默认频率，如果找不到则清空或保持原样
  if (bandFrequencyMap[val]) {
    editForm.freq = bandFrequencyMap[val]
  }
}

const goBack = () => router.push({ name: 'Logs' })

const handleUpdate = async () => {
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
