<template>
  <div class="settings-container">
    <h1>{{ $t('settings.title') }}</h1>
    
    <p>Manage your account and application settings</p>

    <div class="settings-content">
      <el-tabs>
        <el-tab-pane :label="$t('settings.account')">
          <div class="setting-section">
            <p>Account settings here</p>
          </div>
        </el-tab-pane>
        
        <el-tab-pane :label="$t('settings.preferences')">
          <div class="setting-section">
            <p>Preference settings here</p>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped lang="scss">
.settings-container {
  h1 {
    margin-bottom: 10px;
  }

  p {
    color: #909399;
    margin-bottom: 20px;
  }

  .settings-content {
    background: white;
    border-radius: 8px;
    padding: 20px;
  }

  .setting-section {
    padding: 20px 0;
  }
}
</style>
