<template>
  <div class="login-container">
    <div class="lang-selector-wrapper">
      <el-select v-model="currentLanguage" @change="handleLanguageChange" style="width: 100px;">
        <el-option label="中文" value="zh-CN" />
        <el-option label="EN" value="en-US" />
      </el-select>
    </div>

    <div class="login-box">
      <h1>{{ $t('common.appName') }}</h1>
      <p>{{ $t('auth.login') }}</p>

      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <el-form-item :label="$t('common.username')" prop="username">
          <el-input v-model="form.username" :placeholder="$t('common.username')" />
        </el-form-item>

        <el-form-item :label="$t('common.password')" prop="password">
          <el-input v-model="form.password" type="password" :placeholder="$t('common.password')" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" class="login-btn">
            {{ $t('auth.login') }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <p>{{ $t('auth.noAccount') }} <router-link to="/register">{{ $t('common.register') }}</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { setLanguage, getLanguage } from '@/locales'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { t, locale } = useI18n()
const formRef = ref<FormInstance>()
const loading = ref(false)

const currentLanguage = ref(getLanguage())

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: 'Please enter username', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'Please enter password', trigger: 'blur' }
  ]
}

const handleLanguageChange = (language: string) => {
  setLanguage(language)
  locale.value = language as any
}

const handleLogin = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    await authStore.login(form.username, form.password)
    ElMessage.success(t('auth.loginSuccess'))

    const redirect = route.query.redirect as string
    router.push(redirect || '/dashboard')
  } catch (error: any) {
    const detail = error?.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : detail?.[0]?.msg || error.message
    ElMessage.error(msg || t('errors.serverError'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: var(--bg-color-page, #fafafa);

  .lang-selector-wrapper {
    position: absolute;
    top: var(--spacing-lg, 20px);
    right: var(--spacing-lg, 20px);
    z-index: 10;
  }

  .login-box {
    background: var(--bg-color-card, #ffffff);
    border: 1px solid var(--border-color, #e4e4e7);
    border-radius: var(--border-radius-large, 8px);
    padding: var(--spacing-xxl, 32px);
    width: 100%;
    max-width: 380px;
    animation: fadeIn 0.2s ease-out;

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    h1 {
      text-align: center;
      margin-bottom: var(--spacing-xs, 4px);
      color: var(--text-color-primary, #09090b);
      font-size: var(--font-size-xxl, 20px);
      font-weight: var(--font-weight-semibold, 600);
    }

    p {
      text-align: center;
      color: var(--text-color-secondary, #71717a);
      margin-bottom: var(--spacing-xl, 24px);
      font-size: var(--font-size-base, 14px);
    }

    :deep(.el-form-item) {
      margin-bottom: var(--spacing-lg, 20px);

      .el-form-item__label {
        color: var(--text-color-regular, #3f3f46);
        font-weight: var(--font-weight-medium, 500);
        font-size: var(--font-size-base, 14px);
      }

      .el-input__wrapper {
        border-radius: var(--border-radius-base, 6px);
      }
    }

    .login-btn {
      width: 100%;
      height: 40px;
      font-size: var(--font-size-base, 14px);
      font-weight: var(--font-weight-medium, 500);
      border-radius: var(--border-radius-base, 6px);
    }
  }

  .login-footer {
    text-align: center;
    margin-top: var(--spacing-lg, 20px);
    color: var(--text-color-secondary, #71717a);
    font-size: var(--font-size-base, 14px);

    a {
      color: var(--text-color-primary, #09090b);
      text-decoration: none;
      font-weight: var(--font-weight-medium, 500);

      &:hover {
        text-decoration: underline;
      }
    }
  }
}

@media (max-width: 480px) {
  .login-container {
    .login-box {
      margin: var(--spacing-base, 16px);
      padding: var(--spacing-xl, 24px);
    }
  }
}
</style>
