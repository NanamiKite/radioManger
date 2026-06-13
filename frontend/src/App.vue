<template>
  <div id="app">
    <el-container class="app-container">
      <el-header v-if="isAuthenticated" class="app-header">
        <div class="header-content">
          <div class="logo">
            <h1>📻 RadioManager</h1>
          </div>
          <div class="header-right">
            <el-select v-model="currentLanguage" @change="handleLanguageChange" style="width: 120px; margin-right: 20px">
              <el-option label="中文" value="zh-CN" />
              <el-option label="English" value="en-US" />
            </el-select>
            <el-dropdown>
              <span class="el-dropdown-link">
                {{ currentUser?.username }}
                <el-icon class="el-icon--right">
                  <arrow-down />
                </el-icon>
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
              <span>Dashboard</span>
            </el-menu-item>
            <el-menu-item index="/logs">
              <span>QSO Logs</span>
            </el-menu-item>
            <el-menu-item index="/stations">
              <span>Stations</span>
            </el-menu-item>
            <el-menu-item index="/analysis">
              <span>Analysis</span>
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
import { computed, ref, watch, type Ref } from 'vue'
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
const activeMenu: Ref<string> = ref(route.path)
const currentLanguage: Ref<string> = ref(getLanguage())

watch(() => route.path, (newPath: string) => {
  activeMenu.value = newPath
})

const handleLanguageChange = (language: string): void => {
  setLanguage(language)
  locale.value = language as any
}

const handleLogout = (): void => {
  authStore.logout()
  ElMessage.success($t('auth.logoutSuccess'))
  router.push({ name: 'Login' })
}

const goToSettings = (): void => {
  router.push({ name: 'Settings' })
}
</script>

<style scoped lang="scss">
#app {
  height: 100vh;
}

.app-container {
  height: 100%;
}

.app-header {
  background-color: #409eff;
  border-bottom: 1px solid #dcdfe6;
  padding: 0 20px;

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 100%;
    color: white;

    .logo h1 {
      margin: 0;
      font-size: 24px;
    }

    .header-right {
      .el-dropdown-link {
        cursor: pointer;
        display: flex;
        align-items: center;
        color: white;

        &:hover {
          opacity: 0.8;
        }
      }
    }
  }
}

.main-container {
  height: calc(100% - 60px);
}

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
