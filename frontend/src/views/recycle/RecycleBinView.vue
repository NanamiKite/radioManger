<template>
  <div class="recycle-container">
    <div class="page-header">
      <div>
        <h1>{{ t('recycleBin.title') }}</h1>
        <p>{{ t('recycleBin.recycleBinTip') }}</p>
      </div>
      <div class="header-actions">
        <el-button type="danger" plain :disabled="selectedIds.length === 0" @click="handleBatchDelete">
          {{ t('common.delete') }} ({{ selectedIds.length }})
        </el-button>
        <el-button type="danger" :disabled="total === 0" @click="handleClearAll">
          {{ t('recycleBin.clearAll') }}
        </el-button>
      </div>
    </div>

    <el-card>
      <el-table :data="items" v-loading="loading" stripe style="width:100%"
        @selection-change="handleSelectionChange"
        :row-key="(row: DeletedLogItem) => row.id">
        <el-table-column type="selection" width="45" :reserve-selection="true" />
        <el-table-column prop="call_sign" :label="$t('logs.callSign')" width="120" />
        <el-table-column prop="qso_date" :label="$t('recycleBin.date')" width="120" />
        <el-table-column prop="band" :label="$t('logs.band')" width="70" />
        <el-table-column prop="mode" :label="$t('logs.mode')" width="80" />
        <el-table-column prop="dxcc" label="DXCC" width="120" />
        <el-table-column prop="delete_reason" :label="$t('recycleBin.reason')" width="150" />
        <el-table-column :label="$t('recycleBin.expires')" width="120">
          <template #default="scope">
            <el-tag v-if="scope.row.days_remaining && scope.row.days_remaining > 0"
              :type="scope.row.days_remaining <= 1 ? 'danger' : 'warning'" size="small">
              {{ $t('recycleBin.days', { count: scope.row.days_remaining }) }}
            </el-tag>
            <el-tag v-else type="danger" size="small">{{ $t('recycleBin.expired') }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operations')" width="120" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary"
              :disabled="!scope.row.days_remaining || scope.row.days_remaining <= 0"
              @click="handleRestore(scope.row)">{{ $t('recycleBin.restore') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="items.length === 0 && !loading" style="text-align:center;padding:40px">
        <el-empty :description="t('recycleBin.recycleBinEmpty')" />
      </div>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10,20,50]"
          layout="total, sizes, prev, pager, next"
          @change="fetchItems"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { recycleApi } from '@/api/deleted_logs'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { DeletedLogItem } from '@/api/deleted_logs'
import { useI18n } from 'vue-i18n'

const items = ref<DeletedLogItem[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selectedIds = ref<number[]>([])
const { t } = useI18n()

const fetchItems = async () => {
  loading.value = true
  try {
    const res = await recycleApi.list({ page: page.value, page_size: pageSize.value })
    items.value = res.items
    total.value = res.total
  } catch { ElMessage.error(t('recycleBin.loadFailed')) }
  finally { loading.value = false }
}

const handleSelectionChange = (selection: DeletedLogItem[]) => {
  selectedIds.value = selection.map(item => item.id)
}

const handleRestore = async (item: DeletedLogItem) => {
  try {
    await recycleApi.restore(item.id)
    ElMessage.success(t('recycleBin.restored', { callSign: item.call_sign }))
    await fetchItems()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || t('recycleBin.restoreFailed'))
  }
}

const handleBatchDelete = async () => {
  if (selectedIds.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      t('recycleBin.batchDeleteConfirm', { count: selectedIds.value.length }),
      t('common.confirmDelete'),
      { type: 'warning', confirmButtonText: t('common.delete'), cancelButtonText: t('common.cancel') }
    )

    const res = await recycleApi.batchDelete(selectedIds.value)
    ElMessage.success(t('recycleBin.batchDeleted', { count: res.deleted }))
    selectedIds.value = []
    await fetchItems()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err?.response?.data?.detail || t('recycleBin.deleteFailed'))
    }
  }
}

const handleClearAll = async () => {
  if (total.value === 0) return

  try {
    // 第一次确认
    await ElMessageBox.confirm(
      t('recycleBin.clearAllConfirm', { count: total.value }),
      t('recycleBin.clearAllTitle'),
      { type: 'error', confirmButtonText: t('recycleBin.continue'), cancelButtonText: t('common.cancel') }
    )

    // 第二次确认
    await ElMessageBox.confirm(
      t('recycleBin.finalConfirm', { count: total.value }),
      t('recycleBin.finalConfirmTitle'),
      { type: 'error', confirmButtonText: t('recycleBin.yesDeleteAll'), cancelButtonText: t('common.cancel') }
    )

    const res = await recycleApi.clearAll()
    ElMessage.success(t('recycleBin.cleared', { count: res.deleted }))
    selectedIds.value = []
    await fetchItems()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err?.response?.data?.detail || t('recycleBin.clearFailed'))
    }
  }
}

onMounted(fetchItems)
</script>

<style scoped lang="scss">
.recycle-container {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
    h1 { margin-bottom: 5px; font-size: 20px; font-weight: 600; color: var(--text-color-primary); }
    p { color: var(--text-color-secondary); font-size: 14px; margin: 0; }
    .header-actions { display: flex; gap: 8px; }
  }
  .pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
}
</style>
