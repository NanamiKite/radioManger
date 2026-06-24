<template>
  <div class="admin-system">
    <div class="page-header">
      <h1>{{ $t('admin.systemStatus') }}</h1>
      <p>{{ $t('admin.systemStatusDesc') }}</p>
    </div>

    <!-- 系统状态卡片 -->
    <div class="status-grid">
      <div class="status-card">
        <div class="status-label">{{ $t('admin.dbMode') }}</div>
        <div class="status-value">{{ status?.database_mode || '-' }}</div>
      </div>
      <div class="status-card">
        <div class="status-label">{{ $t('admin.totalUsers') }}</div>
        <div class="status-value">{{ status?.total_users || 0 }}</div>
      </div>
      <div class="status-card">
        <div class="status-label">{{ $t('admin.activeUsers') }}</div>
        <div class="status-value">{{ status?.active_users || 0 }}</div>
      </div>
      <div class="status-card">
        <div class="status-label">{{ $t('dashboard.totalQSO') }}</div>
        <div class="status-value">{{ status?.total_qso || 0 }}</div>
      </div>
      <div class="status-card">
        <div class="status-label">{{ $t('dashboard.stationCount') }}</div>
        <div class="status-value">{{ status?.total_stations || 0 }}</div>
      </div>
      <div class="status-card">
        <div class="status-label">{{ $t('admin.onlineSessions') }}</div>
        <div class="status-value">{{ status?.online_sessions || 0 }}</div>
      </div>
    </div>

    <!-- 系统配置 -->
    <el-card class="config-card">
      <template #header>
        <span>{{ $t('admin.systemConfig') }}</span>
      </template>
      <el-table :data="configs" stripe>
        <el-table-column prop="key" :label="$t('admin.configKey')" width="200" />
        <el-table-column prop="description" :label="$t('admin.configDesc')" min-width="200" />
        <el-table-column prop="value" :label="$t('admin.configValue')" min-width="200">
          <template #default="scope">
            <el-input v-if="editingKey === scope.row.key" v-model="editValue" size="small"
              @keyup.enter="saveConfig(scope.row)" @keyup.escape="cancelEdit" />
            <span v-else @click="startEdit(scope.row)" class="config-value">{{ scope.row.value }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="value_type" label="Type" width="80" />
        <el-table-column label="" width="100">
          <template #default="scope">
            <el-button v-if="editingKey === scope.row.key" size="small" type="primary" @click="saveConfig(scope.row)">
              {{ $t('common.save') }}
            </el-button>
            <el-button v-else size="small" @click="startEdit(scope.row)">{{ $t('common.edit') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const status = ref<any>(null)
const configs = ref<any[]>([])
const editingKey = ref('')
const editValue = ref('')

const fetchStatus = async () => {
  try { status.value = await adminApi.getStatus() } catch {}
}

const fetchConfigs = async () => {
  try { configs.value = await adminApi.getConfigs() } catch {}
}

const startEdit = (row: any) => {
  editingKey.value = row.key
  editValue.value = row.value || ''
}

const cancelEdit = () => {
  editingKey.value = ''
  editValue.value = ''
}

const saveConfig = async (row: any) => {
  try {
    await adminApi.updateConfig(row.key, editValue.value)
    row.value = editValue.value
    editingKey.value = ''
    ElMessage.success('Config updated')
  } catch {
    ElMessage.error('Failed to update config')
  }
}

onMounted(() => {
  fetchStatus()
  fetchConfigs()
})
</script>

<style scoped lang="scss">
.admin-system {
  .page-header {
    margin-bottom: 20px;
    h1 { margin-bottom: 4px; font-size: 20px; font-weight: 600; color: var(--text-color-primary); }
    p { color: var(--text-color-secondary); font-size: 14px; margin: 0; }
  }

  .status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 20px;

    .status-card {
      background: var(--bg-color-card);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 16px;
      .status-label { font-size: 12px; color: var(--text-color-secondary); margin-bottom: 4px; }
      .status-value { font-size: 24px; font-weight: 600; color: var(--text-color-primary); }
    }
  }

  .config-card {
    .config-value {
      cursor: pointer;
      &:hover { color: var(--color-accent); }
    }
  }
}
</style>
