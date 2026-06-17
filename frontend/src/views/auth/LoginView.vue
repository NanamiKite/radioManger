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

//绑定当前选中的语言
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

//切换语言
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
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);

  //语言选择器的样式（右上角悬浮）
  .lang-selector-wrapper {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 10;
  }

  .login-box {
    background: white;
    border-radius: 8px;
    padding: 40px;
    width: 100%;
    max-width: 400px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);

    h1 {
      text-align: center;
      margin-bottom: 10px;
      color: #409eff;
    }

    p {
      text-align: center;
      color: #909399;
      margin-bottom: 30px;
    }

    .login-btn {
      width: 100%;
    }

    .login-footer {
      text-align: center;
      margin-top: 20px;
      color: #909399;

      a {
        color: #409eff;
        text-decoration: none;

        &:hover {
          text-decoration: underline;
        }
      }
    }
  }
}
</style>
