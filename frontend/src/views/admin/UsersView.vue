<template>
  <div class="admin-users">
    <div class="page-header">
      <h1>{{ $t('admin.userManagement') }}</h1>
      <p>{{ $t('admin.userManagementDesc') }}</p>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" size="small">
        <el-form-item>
          <el-input v-model="keyword" :placeholder="$t('admin.searchUser')" clearable @keyup.enter="fetchUsers" />
        </el-form-item>
        <el-form-item>
          <el-select v-model="roleFilter" clearable :placeholder="$t('admin.role')">
            <el-option :label="$t('admin.roleUser')" value="user" />
            <el-option :label="$t('admin.roleAdmin')" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select v-model="activeFilter" clearable :placeholder="$t('admin.status')">
            <el-option :label="$t('admin.active')" :value="true" />
            <el-option :label="$t('admin.disabled')" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchUsers">{{ $t('common.search') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户列表 -->
    <el-card>
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" :label="$t('admin.id')" width="60" />
        <el-table-column prop="username" :label="$t('common.username')" width="120" />
        <el-table-column prop="email" :label="$t('common.email')" min-width="180" />
        <el-table-column prop="role" :label="$t('admin.role')" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'info'" size="small">
              {{ scope.row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('admin.status')" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'danger'" size="small">
              {{ scope.row.is_active ? $t('admin.active') : $t('admin.disabled') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" :label="$t('settings.joined')" width="160" />
        <el-table-column :label="$t('common.operations')" width="240" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="viewStats(scope.row)">{{ $t('admin.stats') }}</el-button>
            <el-button size="small" :type="scope.row.is_active ? 'warning' : 'success'" @click="toggleUser(scope.row)">
              {{ scope.row.is_active ? $t('admin.disable') : $t('admin.enable') }}
            </el-button>
            <el-button size="small" type="danger" @click="deleteUser(scope.row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total"
          :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next" @change="fetchUsers" />
      </div>
    </el-card>

    <!-- 统计弹窗 -->
    <el-dialog v-model="showStats" :title="$t('admin.userStats')" width="400px">
      <div v-if="userStats" class="stats-dialog">
        <p>{{ $t('dashboard.totalQSO') }}: <strong>{{ userStats.qso_count }}</strong></p>
        <p>{{ $t('dashboard.stationCount') }}: <strong>{{ userStats.station_count }}</strong></p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const users = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')
const roleFilter = ref('')
const activeFilter = ref<boolean | null>(null)
const showStats = ref(false)
const userStats = ref<any>(null)

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await adminApi.getUsers({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      role: roleFilter.value || undefined,
      is_active: activeFilter.value !== null ? activeFilter.value : undefined,
    })
    users.value = res.items
    total.value = res.total
  } catch {
    ElMessage.error(t('admin.loadFailed'))
  } finally {
    loading.value = false
  }
}

const toggleUser = async (user: any) => {
  try {
    await adminApi.toggleUser(user.id)
    ElMessage.success(t('admin.toggleSuccess', { username: user.username, action: user.is_active ? t('admin.actionDisable') : t('admin.actionEnable') }))
    await fetchUsers()
  } catch {
    ElMessage.error(t('admin.toggleFailed'))
  }
}

const deleteUser = async (user: any) => {
  try {
    await ElMessageBox.confirm(t('admin.deleteConfirm', { username: user.username }), t('common.confirm'), { type: 'warning' })
    await adminApi.deleteUser(user.id)
    ElMessage.success(t('admin.deleteSuccess', { username: user.username }))
    await fetchUsers()
  } catch (err: any) {
    if (err !== 'cancel') ElMessage.error(t('admin.deleteFailed'))
  }
}

const viewStats = async (user: any) => {
  try {
    userStats.value = await adminApi.getUserStats(user.id)
    showStats.value = true
  } catch {
    ElMessage.error(t('admin.loadStatsFailed'))
  }
}

onMounted(fetchUsers)
</script>

<style scoped lang="scss">
.admin-users {
  .page-header {
    margin-bottom: 20px;
    h1 { margin-bottom: 4px; font-size: 20px; font-weight: 600; color: var(--text-color-primary); }
    p { color: var(--text-color-secondary); font-size: 14px; margin: 0; }
  }
  .filter-card { margin-bottom: 16px; }
  .pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
  .stats-dialog {
    p { font-size: 16px; margin: 12px 0; color: var(--text-color-secondary);
      strong { color: var(--text-color-primary); } }
  }
}
</style>
