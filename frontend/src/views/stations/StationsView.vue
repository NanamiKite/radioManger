<template>
  <div class="stations-container">
    <h1>Stations</h1>
    <p>Manage your amateur radio stations</p>

    <div class="stations-content">
      <el-button type="primary" @click="showCreateForm = true">New Station</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, type Ref } from 'vue'

const showCreateForm: Ref<boolean> = ref(false)
</script>

<style scoped lang="scss">
.stations-container {
  h1 {
    margin-bottom: 10px;
  }

  p {
    color: #909399;
    margin-bottom: 20px;
  }

  .stations-content {
    background: white;
    border-radius: 8px;
    padding: 20px;
  }
}
</style>
