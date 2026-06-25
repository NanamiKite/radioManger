<template>
  <div class="stations-container">
    <div class="page-header">
      <div>
        <h1>{{ $t('stations.title') }}</h1>
        <p>{{ $t('stations.manageStations') }}</p>
      </div>
      <div class="header-actions">
        <el-button @click="showStationDialog = true">{{ $t('stations.newStation') }}</el-button>
        <el-button type="primary" @click="showLocationDialog = true" :disabled="stations.length === 0">
          + {{ $t('stations.newLocation') }}
        </el-button>
      </div>
    </div>

    <el-card>
      <el-tree v-loading="loading" :data="treeData" node-key="id" default-expand-all>
        <template #default="{ node, data }">
          <!-- Station 节点 -->
          <div v-if="data._type === 'station'" class="tree-station">
            <span class="station-callsign">{{ data.callsign }}</span>
            <span class="station-meta">({{ data.locationCount }} locations)</span>
            <div class="station-actions">
              <el-button size="small" text type="danger" @click="handleDeleteStation(data)">{{ $t('common.delete') }}</el-button>
            </div>
          </div>

          <!-- Location 节点 -->
          <div v-else class="tree-location">
            <el-radio
              v-model="activeLocationId"
              :value="data._lid"
              :label="data._lid"
              @change="handleActivate(data._lid)"
              class="location-radio"
            >
              <span class="location-name">{{ data.name }}</span>
            </el-radio>

            <div class="location-details">
              <el-tag size="small" v-if="data.grid_square">{{ data.grid_square }}</el-tag>
              <span class="detail-item" v-if="data.radio_model">{{ data.radio_model }}</span>
              <span class="detail-item" v-if="data.antenna_model">{{ data.antenna_model }}</span>
              <span class="detail-item" v-if="data.antenna_height">{{ data.antenna_height }}m</span>
              <span class="detail-item" v-if="data.qth">{{ data.qth }}</span>
            </div>

            <div class="location-actions">
              <el-button size="small" text @click="editLocation(data)">{{ $t('common.edit') }}</el-button>
              <el-button size="small" text type="danger" @click="handleDeleteLocation(data)">{{ $t('common.delete') }}</el-button>
            </div>
          </div>
        </template>
      </el-tree>

      <el-empty v-if="treeData.length === 0" :description="t('stations.noStations')" />
    </el-card>

    <!-- 新建 Station 对话框 -->
    <el-dialog v-model="showStationDialog" :title="$t('stations.newStation')" width="400px">
      <el-form ref="stationFormRef" :model="stationForm" :rules="stationRules" label-width="100px">
        <el-form-item :label="$t('stations.callSign')" prop="callsign">
          <el-input v-model="stationForm.callsign" placeholder="e.g. BA7ABC" @input="(v: string) => stationForm.callsign = v.toUpperCase()" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showStationDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleCreateStation" :loading="submitting">{{ $t('common.submit') }}</el-button>
      </template>
    </el-dialog>

    <!-- 新建/编辑 Location 对话框 -->
    <el-dialog v-model="showLocationDialog" :title="editingLocation ? $t('stations.editLocation') : $t('stations.newLocation')" width="500px">
      <el-form ref="locationFormRef" :model="locationForm" :rules="locationRules" label-width="120px">
        <el-form-item :label="$t('stations.title')" prop="station_id">
          <el-select v-model="locationForm.station_id" style="width:100%">
            <el-option v-for="s in stations" :key="s.id" :label="s.callsign" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('stations.name')" prop="name">
          <el-input v-model="locationForm.name" :placeholder="$t('stations.namePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('stations.gridSquare')" prop="grid_square">
          <el-input v-model="locationForm.grid_square" placeholder="e.g. OL63" @input="(v: string) => locationForm.grid_square = v.toUpperCase()" />
        </el-form-item>
        <el-form-item :label="$t('stations.radioModel')">
          <el-input v-model="locationForm.radio_model" />
        </el-form-item>
        <el-form-item :label="$t('stations.antennaModel')">
          <el-input v-model="locationForm.antenna_model" />
        </el-form-item>
        <el-form-item :label="$t('stations.antennaHeight')">
          <el-input-number v-model="locationForm.antenna_height" :min="0" :step="0.5" style="width:100%" />
        </el-form-item>
        <el-form-item :label="$t('stations.qth')">
          <el-input v-model="locationForm.qth" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showLocationDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmitLocation" :loading="submitting">{{ $t('common.submit') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { stationsApi } from '@/api/stations'
import { locationsApi } from '@/api/locations'
import { logsApi } from '@/api/logs'
import { useLogsStore } from '@/stores/logs'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import type { FormInstance } from 'element-plus'
import type { Station, Location } from '@/types'

const { t } = useI18n()
const logsStore = useLogsStore()

const loading = ref(false)
const submitting = ref(false)
const stations = ref<Station[]>([])
const locations = ref<Location[]>([])
const activeLocationId = ref<number | null>(null)

// 树数据
const treeData = computed(() => {
  return stations.value.map(st => ({
    _type: 'station' as const,
    _sid: st.id,
    id: `s-${st.id}`,
    callsign: st.callsign,
    locationCount: locations.value.filter(l => l.station_id === st.id).length,
    children: locations.value
      .filter(l => l.station_id === st.id)
      .map(l => ({ ...l, _type: 'location' as const, _lid: l.id, id: `loc-${l.id}` })),
  }))
})

// Station dialog
const showStationDialog = ref(false)
const stationFormRef = ref<FormInstance>()
const stationForm = reactive({ callsign: '' })
const stationRules = { callsign: [{ required: true, message: t('stations.required'), trigger: 'blur' }] }

// Location dialog
const showLocationDialog = ref(false)
const editingLocation = ref<Location | null>(null)
const locationFormRef = ref<FormInstance>()
const locationForm = reactive({
  station_id: 0, name: '', grid_square: '', radio_model: '',
  antenna_model: '', antenna_height: null as number | null, qth: ''
})
const locationRules = {
  station_id: [{ required: true, message: t('validation.required'), trigger: 'change' }],
  name: [{ required: true, message: t('validation.required'), trigger: 'blur' }],
  grid_square: [{ required: true, message: t('validation.gridSquare'), trigger: 'blur' }],
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    stations.value = await stationsApi.list()
    locations.value = await locationsApi.list()
    const active = locations.value.find(l => l.is_active)
    activeLocationId.value = active?.id ?? null
  } catch (err: any) { ElMessage.error(err?.response?.data?.detail || err.message || t('errors.serverError')) }
  finally { loading.value = false }
}

// 激活位置
const handleActivate = async (id: number) => {
  try {
    const loc = await locationsApi.activate(id)
    activeLocationId.value = loc.id
    ElMessage.success(`${t('common.activated')}: ${loc.station_callsign} / ${loc.name}`)
    await logsStore.refreshActiveStation()
  } catch (err: any) { ElMessage.error(err?.response?.data?.detail || t('errors.serverError')) }
}

// 删除台站（含导出提示）
const handleDeleteStation = async (station: any) => {
  const sid = station._sid
  const callsign = station.callsign

  try {
    // 先查询该台站有多少日志
    const logsResp = await logsApi.list({ station_id: sid, page_size: 1 })
    const logCount = logsResp.total

    let action = 'delete'
    if (logCount > 0) {
      const result = await ElMessageBox.confirm(
        `${t('common.stationLogs', { count: logCount })} ` +
        t('common.deleteWithoutExport'),
        t('common.deleteStationWarning', { callsign }),
        {
          confirmButtonText: t('stations.deleteAnyway'),
          cancelButtonText: t('stations.cancel'),
          distinguishCancelAndClose: true,
          type: 'warning',
        }
      ).catch((action_: any) => action_)

      if (result === 'cancel' || result === 'close' || !result) return

      // 如果确认直接删除
      await stationsApi.delete(sid)
      ElMessage.success(t('common.success'))
      await loadData()
      await logsStore.fetchStations()
    } else {
      await ElMessageBox.confirm(
        t('common.deleteStationWarning', { callsign }),
        t('common.confirmDelete'),
        { type: 'warning', confirmButtonText: t('common.delete') }
      )
      await stationsApi.delete(sid)
      ElMessage.success(t('common.success'))
      await loadData()
      await logsStore.fetchStations()
    }
  } catch (err: any) {
    if (err?.response?.status === 400) {
      ElMessage.error(err?.response?.data?.detail || t('stations.cannotDeleteStation'))
    } else if (err !== 'cancel' && err !== 'close') {
      ElMessage.error(err?.response?.data?.detail || err?.message || t('errors.serverError'))
    }
  }
}

// 创建台站
const handleCreateStation = async () => {
  try {
    await stationFormRef.value?.validate()
    submitting.value = true
    await stationsApi.create({ callsign: stationForm.callsign.toUpperCase() })
    ElMessage.success(t('common.success'))
    showStationDialog.value = false
    stationForm.callsign = ''
    await loadData()
    await logsStore.fetchStations()
  } catch (err: any) { ElMessage.error(err?.response?.data?.detail || t('errors.serverError')) }
  finally { submitting.value = false }
}

const editLocation = (loc: any) => {
  editingLocation.value = loc
  locationForm.station_id = loc.station_id
  locationForm.name = loc.name
  locationForm.grid_square = loc.grid_square || ''
  locationForm.radio_model = loc.radio_model || ''
  locationForm.antenna_model = loc.antenna_model || ''
  locationForm.antenna_height = loc.antenna_height ?? null
  locationForm.qth = loc.qth || ''
  showLocationDialog.value = true
}

const getLocationRealId = (loc: any): number => loc._lid || loc.id

const handleSubmitLocation = async () => {
  try {
    await locationFormRef.value?.validate()
    submitting.value = true
    if (editingLocation.value) {
      await locationsApi.update(getLocationRealId(editingLocation.value), locationForm)
      ElMessage.success(t('common.updateSuccess'))
    } else {
      await locationsApi.create({
        station_id: locationForm.station_id,
        name: locationForm.name,
        grid_square: locationForm.grid_square,
        radio_model: locationForm.radio_model || undefined,
        antenna_model: locationForm.antenna_model || undefined,
        antenna_height: locationForm.antenna_height ?? undefined,
        qth: locationForm.qth || undefined,
      })
      ElMessage.success(t('common.createSuccess'))
    }
    showLocationDialog.value = false
    editingLocation.value = null
    resetLocationForm()
    await loadData()
    await logsStore.refreshActiveStation()
  } catch (err: any) { ElMessage.error(err?.response?.data?.detail || t('errors.serverError')) }
  finally { submitting.value = false }
}

const handleDeleteLocation = async (loc: any) => {
  try {
    await ElMessageBox.confirm(t('stations.deleteLocation', { name: loc.name }), t('common.confirmDelete'), { type: 'warning' })
    await locationsApi.delete(getLocationRealId(loc))
    ElMessage.success(t('common.deleteSuccess'))
    await loadData()
    await logsStore.refreshActiveStation()
  } catch (err: any) {
    if (err !== 'cancel') ElMessage.error(err?.response?.data?.detail || t('errors.serverError'))
  }
}

const resetLocationForm = () => {
  locationForm.station_id = stations.value[0]?.id || 0
  locationForm.name = ''
  locationForm.grid_square = ''
  locationForm.radio_model = ''
  locationForm.antenna_model = ''
  locationForm.antenna_height = null
  locationForm.qth = ''
}

onMounted(async () => {
  await loadData()
  await logsStore.fetchStations()
  resetLocationForm()
})
</script>

<style scoped lang="scss">
.stations-container {
  .page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;
    h1 { margin-bottom:5px; } p { color:var(--text-color-secondary); } .header-actions { display:flex; gap:8px; } }
}
.tree-station {
  display:flex; align-items:center; gap:8px; padding:4px 0; width:100%;
  .station-callsign { font-size:16px; font-weight:bold; }
  .station-meta { font-size:12px; color:var(--text-color-secondary); }
  .station-actions { margin-left:auto; flex-shrink:0; }
}
.tree-location {
  display:flex; align-items:center; gap:12px; width:100%; padding:4px 0; flex-wrap:wrap;
  .location-radio { flex-shrink:0; .location-name { font-weight:600; margin-left:4px; } }
  .location-details { display:flex; align-items:center; gap:6px; flex-wrap:wrap;
    .detail-item { font-size:12px; color:var(--text-color-regular); }
  }
  .location-actions { margin-left:auto; flex-shrink:0; }
}
</style>
