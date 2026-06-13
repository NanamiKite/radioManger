<template>
  <div class="not-found">
    <div class="not-found-content">
      <h1>404</h1>
      <p>Page Not Found</p>
      <el-button type="primary" @click="goHome">Go Home</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<style scoped lang="scss">
.not-found {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);

  .not-found-content {
    text-align: center;
    color: white;

    h1 {
      font-size: 80px;
      margin-bottom: 20px;
    }

    p {
      font-size: 24px;
      margin-bottom: 30px;
    }
  }
}
</style>
