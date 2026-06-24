<template>
  <div class="settings-container">
    <div class="page-header">
      <h1>{{ $t('settings.title') }}</h1>
      <p>{{ $t('settings.manageAccount') }}</p>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane :label="$t('settings.account')" name="account">
        <el-card>
          <el-descriptions :column="1" border>
            <el-descriptions-item :label="$t('common.username')">{{ currentUser?.username }}</el-descriptions-item>
            <el-descriptions-item :label="$t('common.email')">{{ currentUser?.email }}</el-descriptions-item>
            <el-descriptions-item :label="$t('settings.role')">{{ currentUser?.role }}</el-descriptions-item>
            <el-descriptions-item :label="$t('settings.timezone')">{{ currentUser?.timezone || 'UTC' }}</el-descriptions-item>
            <el-descriptions-item :label="$t('settings.joined')">{{ currentUser?.created_at }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('settings.preferences')" name="preferences">
        <el-card>
          <el-form label-width="140px">
            <el-form-item :label="$t('settings.language')">
              <el-select v-model="language" @change="handleLanguageChange">
                <el-option label="中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('settings.timezone')">
              <el-select v-model="timezone" filterable>
                <el-option label="UTC (UTC+0)" value="UTC" />
                <el-option label="Asia/Shanghai (UTC+8)" value="Asia/Shanghai" />
                <el-option label="Asia/Tokyo (UTC+9)" value="Asia/Tokyo" />
                <el-option label="America/New_York (UTC-5)" value="America/New_York" />
                <el-option label="Europe/London (UTC+0)" value="Europe/London" />
                <el-option label="Europe/Berlin (UTC+1)" value="Europe/Berlin" />
                <el-option label="Australia/Sydney (UTC+10)" value="Australia/Sydney" />
                <el-option label="Pacific/Auckland (UTC+12)" value="Pacific/Auckland" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="savePreferences" :loading="savingPrefs">{{ $t('settings.saveSettings') }}</el-button>
            </el-form-item>
          </el-form>
          <div v-if="prefResult" style="margin-top:8px">
            <el-alert :title="prefResult" :type="prefResult.includes('Error') ? 'error' : 'success'" show-icon />
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('settings.security')" name="security">
        <el-card>
          <el-form label-width="140px">
            <el-form-item :label="$t('settings.currentPassword')">
              <el-input v-model="passwordForm.old_password" type="password" />
            </el-form-item>
            <el-form-item :label="$t('settings.newPassword')">
              <el-input v-model="passwordForm.new_password" type="password" />
            </el-form-item>
            <el-form-item :label="$t('settings.confirmPassword')">
              <el-input v-model="passwordForm.confirm_password" type="password" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="changePassword" :loading="changingPassword">{{ $t('settings.changePassword') }}</el-button>
            </el-form-item>
          </el-form>

          <!-- 账号注销（仅服务器模式） -->
          <template v-if="isServerMode">
            <el-divider />
            <div class="danger-zone">
              <h4>{{ $t('admin.deleteAccount') }}</h4>
              <p class="danger-desc">{{ $t('admin.deleteAccountDesc') }}</p>

              <!-- 已申请注销：显示倒计时 + 撤销按钮 -->
              <div v-if="deletionScheduled" class="deletion-pending">
                <el-alert type="warning" :closable="false" show-icon>
                  {{ $t('admin.deleteAccountCooldown') }}
                </el-alert>
                <div style="margin-top: 12px;">
                  <el-button type="primary" @click="cancelDeletion" :loading="cancellingDeletion">
                    {{ $t('admin.cancelDelete') }}
                  </el-button>
                </div>
              </div>

              <!-- 未申请：显示注销按钮 -->
              <div v-else>
                <el-button type="danger" @click="showDeleteDialog = true">
                  {{ $t('admin.deleteAccount') }}
                </el-button>
              </div>
            </div>
          </template>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('settings.udpSettings')" name="udp">
        <el-card>
          <el-form label-width="160px">
            <el-form-item :label="$t('udp.wsjtxPort')">
              <el-input v-model.number="udpForm.wsjtx_port" type="number" min="1024" max="65535" />
              <div class="field-hint">WSJT-X / JTDX / MSHV {{ $t('udp.defaultPort') }}: 2237</div>
            </el-form-item>
            <el-form-item :label="$t('udp.n1mmPort')">
              <el-input v-model.number="udpForm.n1mm_port" type="number" min="1024" max="65535" />
              <div class="field-hint">N1MM Logger+ {{ $t('udp.defaultPort') }}: 12060</div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveUdpSettings">{{ $t('settings.saveSettings') }}</el-button>
            </el-form-item>
          </el-form>
          <el-divider />
          <p style="font-size:13px;color:var(--text-color-secondary)">
            {{ $t('udp.settingsHint') }}
          </p>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('settings.about')" name="about">
        <el-card class="about-card">
          <div class="about-header">
            <h2>{{ $t('settings.appName') }}</h2>
            <p class="about-desc">{{ $t('settings.description') }}</p>
            <span class="version-badge">{{ $t('settings.version') }} 2.4.1</span>
          </div>

          <el-divider />

          <el-divider />

          <div class="about-info">
            <p>{{ $t('settings.dbMode') }}: <strong>{{ dbMode }}</strong></p>
            <p>{{ $t('settings.apiServer') }}: <strong>{{ apiBase }}</strong></p>
            <template v-if="dbPath">
              <p>{{ $t('settings.dbPath') }}: <code>{{ dbPath }}</code></p>
              <div style="margin-top:8px; display:flex; gap:8px;">
                <el-button size="small" @click="copyDbPath">{{ $t('settings.copyPath') }}</el-button>
                <el-button size="small" type="primary" @click="openDbFolder">{{ $t('settings.openFolder') }}</el-button>
              </div>
            </template>
          </div>

          <el-divider />

          <div class="about-footer">
            <p class="credit-line">
              DesignedBy: <strong>NanamiKite</strong>
            </p>
            <p class="copyright-line">
              &copy; 2026 {{ $t('settings.appName') }} &mdash; MIT License
            </p>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 注销确认弹窗 -->
    <el-dialog v-model="showDeleteDialog" :title="$t('admin.deleteAccount')" width="440px">
      <p style="margin-bottom:16px;color:var(--text-color-secondary)">
        {{ $t('admin.deleteAccountDesc') }}
      </p>
      <el-form label-width="100px">
        <el-form-item :label="$t('common.password')">
          <el-input v-model="deletePassword" type="password" placeholder="Enter password to confirm" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDeleteDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="danger" @click="requestDeletion" :loading="requestingDeletion">
          {{ $t('admin.confirmDelete') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { setLanguage, getLanguage } from '@/locales'
import { ElMessage } from 'element-plus'
import api from '@/api/index'
import { udpApi } from '@/api/udp'
import { authApi } from '@/api/auth'
import axios from 'axios'

const authStore = useAuthStore()
const { locale, t } = useI18n()

const activeTab = ref('account')
const currentUser = computed(() => authStore.user)
const language = ref(getLanguage())
const timezone = ref('UTC')
const savingPrefs = ref(false)
const prefResult = ref('')
const changingPassword = ref(false)
const dbMode = ref('loading...')
const dbPath = ref('')
const dbDir = ref('')
const apiBase = ref('/api/v1')

const udpForm = ref({ wsjtx_port: 2237, n1mm_port: 12060 })
const isServerMode = ref(false)
const deletionScheduled = ref(false)
const showDeleteDialog = ref(false)
const deletePassword = ref('')
const requestingDeletion = ref(false)
const cancellingDeletion = ref(false)

const saveUdpSettings = async () => {
  try {
    await udpApi.stop()
    ElMessage.success(t('settings.settingsSaved'))
  } catch { /* ignore */ }
}

const passwordForm = ref({ old_password: '', new_password: '', confirm_password: '' })

onMounted(async () => {
  // 从用户信息加载时区和语言
  if (authStore.user) {
    timezone.value = authStore.user.timezone || 'UTC'
    language.value = authStore.user.language || 'zh-CN'
  }
  try {
  const res: any = await axios.get('/health')   // api/v1
  dbMode.value = res.data.database || 'sqlite'   // 直接 axios 没有 response 拦截器，要取 .data
  isServerMode.value = dbMode.value === 'mysql'
  dbPath.value = res.data.db_path || ''
  dbDir.value = res.data.db_dir || ''
  } catch { dbMode.value = 'unknown' }
})

const copyDbPath = async () => {
  if (!dbPath.value) return
  try {
    await navigator.clipboard.writeText(dbPath.value)
    ElMessage.success(t('common.copy') + ' ✓')
  } catch {
    // fallback
    const ta = document.createElement('textarea')
    ta.value = dbPath.value
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    ElMessage.success(t('common.copy') + ' ✓')
  }
}

const openDbFolder = () => {
  if (!dbDir.value) return
  // Electron 环境：调用 shell.openPath
  if (window.electronAPI?.openPath) {
    window.electronAPI.openPath(dbDir.value)
    return
  }
  // Web 环境：复制路径让用户自己打开
  navigator.clipboard.writeText(dbDir.value).catch(() => {})
  ElMessage.info(t('settings.pathCopied') + '\n' + dbDir.value)
}

const handleLanguageChange = (lang: string) => {
  setLanguage(lang)
  locale.value = lang as any
}

const savePreferences = async () => {
  savingPrefs.value = true
  prefResult.value = ''
  try {
    await api.patch('/auth/me', {
      timezone: timezone.value,
      language: language.value,
    })
    // 同步更新 store 中的用户信息
    authStore.user = { ...authStore.user, timezone: timezone.value, language: language.value } as any
    // 同步到 storage
    localStorage.setItem('user', JSON.stringify(authStore.user))
    prefResult.value = t('settings.settingsSaved')
  } catch (err: any) {
    prefResult.value = t('errors.serverError') + ': ' + (err?.response?.data?.detail || '')
  } finally {
    savingPrefs.value = false
    setTimeout(() => { prefResult.value = '' }, 3000)
  }
}

const changePassword = async () => {
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    ElMessage.error(t('validation.passwordMismatch'))
    return
  }
  changingPassword.value = true
  try {
    await api.post('/auth/change-password', {
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password,
      confirm_password: passwordForm.value.confirm_password
    })
    ElMessage.success('Password changed')
    passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || 'Failed to change password')
  } finally { changingPassword.value = false }
}

const requestDeletion = async () => {
  if (!deletePassword.value) {
    ElMessage.error(t('validation.required'))
    return
  }
  requestingDeletion.value = true
  try {
    await authApi.deleteAccount(deletePassword.value)
    deletionScheduled.value = true
    showDeleteDialog.value = false
    deletePassword.value = ''
    ElMessage.success(t('admin.deleteAccountCooldown'))
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || 'Failed')
  } finally { requestingDeletion.value = false }
}

const cancelDeletion = async () => {
  cancellingDeletion.value = true
  try {
    await authApi.cancelDeleteAccount()
    deletionScheduled.value = false
    ElMessage.success(t('admin.cancelDelete') + ' - OK')
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || 'Failed')
  } finally { cancellingDeletion.value = false }
}
</script>

<style scoped lang="scss">
.settings-container {
  .page-header {
    margin-bottom: 20px;
    h1 {
      margin-bottom: 5px;
      color: var(--text-color-primary);
      font-size: var(--font-size-xxl);
      font-weight: var(--font-weight-semibold);
    }
    p { color: var(--text-color-secondary); }
  }

    .el-card { max-width: 600px; }

    .danger-zone {
      h4 {
        margin: 0 0 4px;
        font-size: 15px;
        font-weight: 600;
        color: var(--color-danger, #f56c6c);
      }
      .danger-desc {
        font-size: 13px;
        color: var(--text-color-secondary);
        margin: 0 0 12px;
      }
    }

    .field-hint {
    font-size: var(--font-size-small);
    color: var(--text-color-secondary);
    margin-top: 4px;
  }

  // ── 关于页面样式 ──
  .about-card {
    .about-header {
      text-align: center;

      h2 {
        margin: 0 0 4px;
        font-size: var(--font-size-extra-large);
        font-weight: var(--font-weight-semibold);
        color: var(--text-color-primary);
      }

      .about-desc {
        margin: 0 0 12px;
        color: var(--text-color-secondary);
        font-size: var(--font-size-base);
      }

      .version-badge {
        display: inline-block;
        padding: 2px 10px;
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius-round);
        font-size: var(--font-size-small);
        color: var(--text-color-secondary);
        font-weight: var(--font-weight-medium);
      }
    }

    .about-links {
      display: flex;
      flex-direction: column;
      gap: 2px;

      .about-link-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
        padding: var(--spacing-sm) var(--spacing-md);
        border-radius: var(--border-radius-base);
        text-decoration: none;
        color: var(--text-color-regular);
        transition: background var(--transition-duration) var(--transition-function);

        &:hover {
          background: var(--bg-color-hover);
          color: var(--text-color-primary);
        }

        .link-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          border: 1px solid var(--border-color);
          border-radius: var(--border-radius-base);
          font-size: var(--font-size-small);
          font-weight: var(--font-weight-semibold);
          color: var(--text-color-primary);
          flex-shrink: 0;
        }

        .link-label {
          font-size: var(--font-size-base);
          font-weight: var(--font-weight-medium);
        }
      }
    }

    .about-info {
      p {
        font-size: var(--font-size-base);
        color: var(--text-color-secondary);
        margin: 0 0 4px;

        strong {
          color: var(--text-color-primary);
          font-weight: var(--font-weight-regular);
        }

        code {
          font-size: 12px;
          background: var(--bg-color-hover);
          padding: 2px 6px;
          border-radius: 3px;
          font-family: 'JetBrains Mono', 'Fira Code', monospace;
          color: var(--text-color-primary);
          word-break: break-all;
        }
      }
    }

    .about-footer {
      text-align: center;

      .credit-line {
        font-size: var(--font-size-base);
        color: var(--text-color-secondary);
        margin: 0 0 4px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;

        strong {
          color: var(--text-color-primary);
          font-weight: var(--font-weight-semibold);
        }
      }

      .copyright-line {
        font-size: var(--font-size-small);
        color: var(--text-color-placeholder);
        margin: 0;
      }
    }
  }
}
</style>
