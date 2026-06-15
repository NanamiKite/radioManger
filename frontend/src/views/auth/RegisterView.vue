<template>
  <div class="register-container">
    <div class="register-box">
      <h1>{{ $t('auth.register') }}</h1>
      <p>{{ $t('common.appName') }}</p>

      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleRegister">
        <el-form-item :label="$t('common.username')" prop="username">
          <el-input v-model="form.username" :placeholder="$t('common.username')" />
        </el-form-item>

        <el-form-item :label="$t('common.email')" prop="email">
          <el-input v-model="form.email" type="email" :placeholder="$t('common.email')" />
        </el-form-item>

        <el-form-item :label="$t('common.password')" prop="password">
          <el-input v-model="form.password" type="password" :placeholder="$t('common.password')" />
        </el-form-item>

        <el-form-item :label="$t('auth.passwordConfirm')" prop="confirm_password">
          <el-input v-model="form.confirm_password" type="password" :placeholder="$t('auth.passwordConfirm')" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleRegister" :loading="loading" class="register-btn">
            {{ $t('auth.register') }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="register-footer">
        <p>{{ $t('auth.loginSuccess') }} <router-link to="/login">{{ $t('auth.login') }}</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, type Ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const { t } = useI18n()
const formRef = ref<FormInstance>()
const loading: Ref<boolean> = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirm_password: ''
})

const rules = {
  username: [
    { required: true, message: t('validation.required'), trigger: 'blur' }
  ],
  email: [
    { required: true, message: t('validation.required'), trigger: 'blur' },
    { type: 'email', message: t('validation.email'), trigger: 'blur' }
  ],
  password: [
    { required: true, message: t('validation.required'), trigger: 'blur' },
    { min: 8, message: t('validation.passwordTooShort'), trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: t('validation.required'), trigger: 'blur' }
  ]
}

const handleRegister = async (): Promise<void> => {
  try {
    await formRef.value?.validate()
    
    if (form.password !== form.confirm_password) {
      ElMessage.error(t('validation.passwordMismatch'))
      return
    }

    loading.value = true

    await authStore.register(form)
    ElMessage.success(t('auth.registerSuccess'))

    router.push({ name: 'Login' })
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
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  padding: 20px;

  .register-box {
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

    .register-btn {
      width: 100%;
    }

    .register-footer {
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
