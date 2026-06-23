<template>
  <div id="app">
    <el-container class="app-container">
      <el-header v-if="isAuthenticated" class="app-header">
        <div class="header-content">
          <div class="logo">
            <h1>{{ $t('common.appName') }}</h1>
          </div>
          <div class="header-right">
            <!-- 主题切换按钮 -->
            <el-tooltip :content="getThemeLabel(themeMode)" placement="bottom">
              <button class="theme-toggle" @click="toggleTheme" :title="getThemeLabel(themeMode)">
                <span class="theme-icon">{{ getThemeIcon(themeMode) }}</span>
              </button>
            </el-tooltip>

            <el-select v-model="currentLanguage" @change="handleLanguageChange" style="width: 100px;">
              <el-option label="中文" value="zh-CN" />
              <el-option label="EN" value="en-US" />
            </el-select>
            <el-dropdown>
              <span class="el-dropdown-link">
                {{ currentUser?.username }}
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
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
import { computed, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { setLanguage, getLanguage } from '@/locales'
import { useTheme } from '@/utils/theme'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { locale } = useI18n()

// 主题切换
const { themeMode, isDark, toggleTheme, getThemeIcon, getThemeLabel } = useTheme()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const currentUser = computed(() => authStore.user)
const activeMenu = ref(route.path)
const currentLanguage = ref(getLanguage())

watch(() => route.path, (newPath: string) => {
  activeMenu.value = newPath
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

// ── 顶部导航栏 — 干净白底 ──
.app-header {
  background-color: var(--bg-color-card);
  border-bottom: 1px solid var(--border-color-lighter);
  padding: 0 var(--spacing-xl);
  height: 56px;
  z-index: var(--z-index-top);
  position: relative;

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 100%;

    .logo {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);

      h1 {
        margin: 0;
        font-size: var(--font-size-large);
        font-weight: var(--font-weight-semibold);
        color: var(--text-color-primary);
        letter-spacing: -0.01em;
      }
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);

      .theme-toggle {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border: 1px solid var(--border-color-lighter);
        background: transparent;
        border-radius: var(--border-radius-base);
        cursor: pointer;
        transition: background var(--transition-duration) var(--transition-function);
        padding: 0;

        &:hover {
          background: var(--bg-color-hover);
        }

        .theme-icon {
          font-size: 16px;
          line-height: 1;
        }
      }

      .el-dropdown-link {
        cursor: pointer;
        display: flex;
        align-items: center;
        color: var(--text-color-regular);
        padding: var(--spacing-xs) var(--spacing-sm);
        border-radius: var(--border-radius-base);
        transition: background var(--transition-duration) var(--transition-function);
        font-weight: var(--font-weight-medium);
        font-size: var(--font-size-base);

        &:hover {
          background: var(--bg-color-hover);
        }
      }
    }
  }
}

.main-container {
  height: calc(100% - 56px);
}

// ── 侧边栏 — Multica 浅灰风格 ──
.app-aside {
  background-color: var(--sidebar-bg);
  border-right: 1px solid var(--border-color-lighter);
  overflow-y: auto;
  overflow-x: hidden;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 2px;
  }

  :deep(.el-menu) {
    border-right: none;
    background: transparent;
    padding: var(--spacing-sm) var(--spacing-xs);

    .el-menu-item {
      height: 40px;
      line-height: 40px;
      margin-bottom: 2px;
      border-radius: var(--border-radius-base);
      color: var(--sidebar-text);
      font-size: var(--font-size-base);
      transition: all var(--transition-duration) var(--transition-function);

      &:hover {
        background: var(--sidebar-hover);
        color: var(--sidebar-text-active);
      }

      &.is-active {
        background: var(--color-accent);
        color: #ffffff;
        font-weight: var(--font-weight-medium);
      }

      span {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        font-size: var(--font-size-base);
      }
    }
  }
}

// ── 主内容区 ──
.app-main {
  background-color: var(--bg-color-page);
  padding: var(--spacing-xl);
  overflow-y: auto;
  overflow-x: hidden;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 3px;
    &:hover {
      background: var(--text-color-placeholder);
    }
  }
}

// ── 响应式 ──
@media (max-width: 768px) {
  .app-aside {
    width: 56px !important;

    :deep(.el-menu) {
      padding: var(--spacing-xs);

      .el-menu-item {
        span {
          font-size: 0;
          width: 100%;
          justify-content: center;
          gap: 0;
          &::before {
            font-size: 18px;
          }
        }
      }
    }
  }

  .app-main {
    padding: var(--spacing-base);
  }
}
</style>
