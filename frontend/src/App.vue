<template>
  <div id="app">
    <el-container class="app-container">
      <el-header v-if="isAuthenticated" class="app-header">
        <div class="header-content">
          <div class="logo">
            <h1>{{ $t('common.appName') }}</h1>
          </div>
          <div class="header-right">
            <el-select v-model="currentLanguage" @change="handleLanguageChange" style="width: 100px; margin-right: 16px">
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
        <el-aside v-if="isAuthenticated" width="200px" class="app-aside">
          <el-menu :router="true" :default-active="activeMenu">
            <el-menu-item index="/dashboard">
              <span>📊 {{ $t('nav.dashboard') }}</span>
            </el-menu-item>
            <el-menu-item index="/logs">
              <span>📝 {{ $t('nav.logs') }}</span>
            </el-menu-item>
            <el-menu-item index="/stations">
              <span>📡 {{ $t('nav.stations') }}</span>
            </el-menu-item>
                        <el-menu-item index="/dxclusters">
              <span>📈 {{ $t('nav.dxspots') }}</span>
            </el-menu-item>
            <el-menu-item index="/analysis">
              <span>📈 {{ $t('nav.analysis') }}</span>
            </el-menu-item>
            <el-menu-item index="/callsigns">
              <span>🔍 {{ $t('nav.callsigns') }}</span>
            </el-menu-item>
            <el-menu-item index="/shortcuts">
              <span>🔗 {{ $t('nav.shortcuts') }}</span>
            </el-menu-item>
            <el-menu-item index="/recycle">
              <span>🗑️ {{ $t('nav.recycle') }}</span>
            </el-menu-item>
            <el-menu-item index="/settings">
              <span>⚙️ {{ $t('nav.settings') }}</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <el-main class="app-main">
          <router-view />
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

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { locale } = useI18n()

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
  // logout() 会通过 window.location.href 跳转到 /login
}

const goToSettings = () => {
  router.push({ name: 'Settings' })
}
</script>

<style scoped lang="scss">
#app { height: 100vh; }

.app-container { height: 100%; }

.app-header {
  background-color: #409eff;
  padding: 0 20px;
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 100%;
    color: white;
    .logo h1 { margin: 0; font-size: 22px; letter-spacing: 1px; }
    .header-right {
      display: flex;
      align-items: center;
      .el-dropdown-link {
        cursor: pointer;
        display: flex;
        align-items: center;
        color: white;
        &:hover { opacity: 0.8; }
      }
    }
  }
}

.main-container { height: calc(100% - 60px); }

.app-aside {
  background-color: #f5f7fa;
  border-right: 1px solid #dcdfe6;
}

.app-main {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
