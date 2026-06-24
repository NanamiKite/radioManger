<template>
  <div id="app">
    <el-container class="app-container">
      <el-header v-if="isAuthenticated" class="app-header">
        <div class="header-content">
          <!-- 左侧：Logo -->
          <div class="header-left">
            <h1 class="logo-text">{{ $t('common.appName') }}</h1>
          </div>

          <!-- 中间：搜索框 -->
          <div class="header-center">
            <div class="search-bar">
              <span class="search-icon">S</span>
              <input
                v-model="searchQuery"
                type="text"
                :placeholder="$t('logs.callSign') + ' / DXCC / Grid'"
                class="search-input"
                @keydown.enter="handleGlobalSearch"
              />
              <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''">X</button>
            </div>
          </div>

          <!-- 右侧：操作 -->
          <div class="header-right">
            <el-tooltip :content="getThemeLabel(themeMode)" placement="bottom">
              <button class="icon-btn" @click="toggleTheme">
                <span>{{ getThemeIcon(themeMode) }}</span>
              </button>
            </el-tooltip>

            <el-select v-model="currentLanguage" @change="handleLanguageChange" size="small" style="width: 80px;">
              <el-option label="中文" value="zh-CN" />
              <el-option label="EN" value="en-US" />
            </el-select>

            <el-dropdown>
              <span class="user-btn">
                {{ currentUser?.username }}
                <span class="user-arrow">v</span>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="goToSettings">{{ $t('common.settings') }}</el-dropdown-item>
                  <el-dropdown-divider />
                  <el-dropdown-item @click="handleLogout">{{ $t('common.logout') }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <el-container class="main-container">
        <el-aside v-if="isAuthenticated" width="220px" class="app-aside">
          <el-menu :router="true" :default-active="activeMenu">
            <el-menu-item index="/dashboard">
              <span>{{ $t('nav.dashboard') }}</span>
            </el-menu-item>
            <el-menu-item index="/logs">
              <span>{{ $t('nav.logs') }}</span>
            </el-menu-item>
            <el-menu-item index="/stations">
              <span>{{ $t('nav.stations') }}</span>
            </el-menu-item>
            <el-menu-item index="/dxclusters">
              <span>{{ $t('nav.dxspots') }}</span>
            </el-menu-item>
            <el-menu-item index="/analysis">
              <span>{{ $t('nav.analysis') }}</span>
            </el-menu-item>
            <el-menu-item index="/tools">
              <span>{{ $t('nav.tools') }}</span>
            </el-menu-item>
            <el-menu-item index="/map">
              <span>{{ $t('nav.map') }}</span>
            </el-menu-item>
            <el-menu-item index="/callsigns">
              <span>{{ $t('nav.callsigns') }}</span>
            </el-menu-item>
            <el-menu-item index="/shortcuts">
              <span>{{ $t('nav.shortcuts') }}</span>
            </el-menu-item>
            <el-menu-item index="/recycle">
              <span>{{ $t('nav.recycle') }}</span>
            </el-menu-item>

            <!-- Admin 菜单组（仅服务器模式 + admin 角色） -->
            <template v-if="isAdminPanel">
              <div class="nav-divider"></div>
              <div class="nav-section-title">{{ $t('admin.section') }}</div>
              <el-menu-item index="/admin/users">
                <span>{{ $t('admin.userManagement') }}</span>
              </el-menu-item>
              <el-menu-item index="/admin/system">
                <span>{{ $t('admin.systemStatus') }}</span>
              </el-menu-item>
              <el-menu-item index="/admin/audit">
                <span>{{ $t('admin.auditLog') }}</span>
              </el-menu-item>
            </template>

            <el-menu-item index="/settings">
              <span>{{ $t('nav.settings') }}</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <el-main class="app-main">
          <router-view :key="$route.fullPath" />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useLogsStore } from '@/stores/logs'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { setLanguage, getLanguage } from '@/locales'
import { useTheme } from '@/utils/theme'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const logsStore = useLogsStore()
const { locale } = useI18n()

const { themeMode, isDark, toggleTheme, getThemeIcon, getThemeLabel } = useTheme()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const currentUser = computed(() => authStore.user)
// Admin 面板：仅服务器模式 + admin 角色
const isAdminPanel = computed(() => {
  return authStore.dbMode !== 'sqlite' && currentUser.value?.role === 'admin'
})
const activeMenu = ref(route.path)
const currentLanguage = ref(getLanguage())
const searchQuery = ref('')

watch(() => route.path, (newPath: string) => {
  activeMenu.value = newPath
})

// 获取数据库模式（判断是否为服务器部署）
onMounted(() => {
  if (isAuthenticated.value) {
    authStore.fetchDbMode()
  }
})

const handleLanguageChange = (language: string) => {
  setLanguage(language)
  locale.value = language as any
}

const handleLogout = () => {
  authStore.logout()
}

const goToSettings = () => {
  router.push({ name: 'Settings' })
}

// 全局搜索：跳转到日志页并填入搜索词
const handleGlobalSearch = () => {
  const q = searchQuery.value.trim()
  if (!q) return
  logsStore.filters.call_sign = q.toUpperCase()
  logsStore.pagination.page = 1
  if (route.name !== 'Logs') {
    router.push({ name: 'Logs' })
  } else {
    logsStore.fetchLogs()
  }
}
</script>

<style scoped lang="scss">
#app {
  height: 100vh;
  overflow: hidden;
  background-color: var(--bg-color-page);
}

.app-container {
  height: 100%;
}

// ── Gmail 风格顶部栏 ──
.app-header {
  background-color: var(--bg-color-card);
  border-bottom: 1px solid var(--border-color-lighter);
  padding: 0 16px;
  height: 56px;
  z-index: var(--z-index-top);

  .header-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 100%;

    // 左侧 Logo
    .header-left {
      flex-shrink: 0;

      .logo-text {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: var(--text-color-primary);
        white-space: nowrap;
      }
    }

    // 中间搜索框
    .header-center {
      flex: 0 1 360px;
      min-width: 200px;

      .search-bar {
        display: flex;
        align-items: center;
        background: var(--bg-color-hover);
        border-radius: 8px;
        padding: 0 12px;
        height: 36px;
        transition: background 0.2s, box-shadow 0.2s;

        &:focus-within {
          background: var(--bg-color-card);
          box-shadow: 0 1px 6px rgba(0, 0, 0, 0.12);
        }

        .search-icon {
          flex-shrink: 0;
          width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-color-secondary);
          font-size: 12px;
          margin-right: 8px;
        }

        .search-input {
          flex: 1;
          border: none;
          outline: none;
          background: transparent;
          font-size: 13px;
          color: var(--text-color-primary);
          font-family: inherit;
          min-width: 0;

          &::placeholder {
            color: var(--text-color-placeholder);
          }
        }

        .search-clear {
          flex-shrink: 0;
          width: 18px;
          height: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: none;
          background: none;
          cursor: pointer;
          color: var(--text-color-secondary);
          font-size: 11px;
          border-radius: 50%;
          margin-left: 4px;

          &:hover {
            background: var(--border-color-lighter);
          }
        }
      }
    }

    // 右侧操作
    .header-right {
      flex-shrink: 0;
      display: flex;
      align-items: center;
      gap: 8px;

      .icon-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border: none;
        background: transparent;
        border-radius: 50%;
        cursor: pointer;
        color: var(--text-color-secondary);
        font-size: 14px;
        transition: background 0.15s;

        &:hover {
          background: var(--bg-color-hover);
        }
      }

      .user-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 4px 8px;
        border-radius: 6px;
        cursor: pointer;
        color: var(--text-color-regular);
        font-size: 14px;
        font-weight: 500;
        transition: background 0.15s;

        &:hover {
          background: var(--bg-color-hover);
        }

        .user-arrow {
          font-size: 10px;
          color: var(--text-color-secondary);
        }
      }
    }
  }
}

.main-container {
  height: calc(100% - 56px);
}

// ── 侧边栏 — Gmail 风格 ──
.app-aside {
  background-color: var(--sidebar-bg);
  border-right: 1px solid var(--border-color-lighter);
  overflow-y: auto;
  overflow-x: hidden;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 2px; }

  .nav-divider {
    height: 1px;
    background: var(--border-color-lighter);
    margin: 8px 16px;
  }

  .nav-section-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-color-placeholder);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 4px 24px 4px;
  }

  :deep(.el-menu) {
    border-right: none;
    background: transparent;
    padding: 8px 6px;

    .el-menu-item {
      height: 36px;
      line-height: 36px;
      margin-bottom: 1px;
      border-radius: 0 20px 20px 0;
      color: var(--sidebar-text);
      font-size: 14px;
      transition: all 0.15s;
      padding-left: 24px !important;

      &:hover {
        background: var(--sidebar-hover);
        color: var(--sidebar-text-active);
      }

      &.is-active {
        background: var(--color-accent);
        color: #ffffff;
        font-weight: 600;
      }

      span {
        display: flex;
        align-items: center;
        font-size: 14px;
      }
    }
  }
}

// ── 主内容区 ──
.app-main {
  background-color: var(--bg-color-page);
  padding: 24px;
  overflow-y: auto;
  overflow-x: hidden;

  &::-webkit-scrollbar { width: 6px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 3px;
    &:hover { background: var(--text-color-placeholder); }
  }
}

// ── 响应式 ──
@media (max-width: 768px) {
  .app-header .header-content {
    .header-center { flex: 0 1 200px; min-width: 140px; }
  }

  .app-aside {
    width: 56px !important;
    :deep(.el-menu) {
      padding: 4px;
      .el-menu-item {
        padding-left: 0 !important;
        justify-content: center;
        span { font-size: 0; }
        span::before { font-size: 18px; }
      }
    }
  }

  .app-main { padding: 16px; }
}
</style>
