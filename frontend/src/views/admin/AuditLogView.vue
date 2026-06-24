<template>
  <div class="admin-audit">
    <div class="page-header">
      <h1>{{ $t('admin.auditLog') }}</h1>
      <p>{{ $t('admin.auditLogDesc') }}</p>
    </div>

    <!-- 筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" size="small">
        <el-form-item>
          <el-input v-model="usernameFilter" placeholder="Username" clearable @keyup.enter="fetchLogs" />
        </el-form-item>
        <el-form-item>
          <el-select v-model="actionFilter" clearable placeholder="Action">
            <el-option v-for="a in actions" :key="a" :label="a" :value="a" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchLogs">{{ $t('common.search') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志列表 -->
    <el-card>
      <el-table :data="logs" v-loading="loading" stripe>
        <el-table-column prop="created_at" :label="$t('admin.time')" width="180" />
        <el-table-column prop="username" label="User" width="120" />
        <el-table-column prop="action" label="Action" width="160">
          <template #default="scope">
            <el-tag :type="getActionType(scope.row.action)" size="small">{{ scope.row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_type" label="Target" width="100" />
        <el-table-column prop="detail" :label="$t('admin.detail')" min-width="250" show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP" width="130" />
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total"
          :page-sizes="[50, 100, 200]" layout="total, sizes, prev, pager, next" @change="fetchLogs" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const logs = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)
const usernameFilter = ref('')
const actionFilter = ref('')

const actions = [
  'LOGIN', 'LOGOUT', 'REGISTER',
  'IMPORT_LOGS', 'EXPORT_LOGS', 'DELETE_LOGS', 'RESTORE_LOGS',
  'CHANGE_PASSWORD', 'UPDATE_PROFILE',
  'ADMIN_TOGGLE_USER', 'ADMIN_RESET_PASSWORD', 'ADMIN_DELETE_USER', 'ADMIN_UPDATE_CONFIG',
]

const getActionType = (action: string) => {
  if (action.includes('DELETE') || action.includes('DISABLE')) return 'danger'
  if (action.includes('LOGIN') || action.includes('REGISTER')) return 'success'
  if (action.includes('ADMIN')) return 'warning'
  return 'info'
}

const fetchLogs = async () => {
  loading.value = true
  try {
    const res = await adminApi.getAuditLogs({
      page: page.value,
      page_size: pageSize.value,
      action: actionFilter.value || undefined,
    })
    logs.value = res.items
    total.value = res.total
  } catch {
    ElMessage.error('Failed to load audit logs')
  } finally {
    loading.value = false
  }
}

onMounted(fetchLogs)
</script>

<style scoped lang="scss">
.admin-audit {
  .page-header {
    margin-bottom: 20px;
    h1 { margin-bottom: 4px; font-size: 20px; font-weight: 600; color: var(--text-color-primary); }
    p { color: var(--text-color-secondary); font-size: 14px; margin: 0; }
  }
  .filter-card { margin-bottom: 16px; }
  .pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
}
</style>
