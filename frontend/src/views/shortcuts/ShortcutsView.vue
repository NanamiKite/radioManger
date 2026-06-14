<template>
  <div class="shortcuts-container">
    <div class="page-header">
      <div>
        <h1>{{ $t('shortcuts.title') }}</h1>
        <p>{{ $t('shortcuts.subtitle') }}</p>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col v-for="s in shortcuts" :key="s.id" :xs="24" :sm="12" :md="8" :lg="6" class="shortcut-col">
        <el-card shadow="hover" class="shortcut-card" @click="openUrl(s.url)">
          <div class="shortcut-content">
            <div class="shortcut-name">{{ s.name }}</div>
            <div class="shortcut-url">{{ s.url }}</div>
            <div class="shortcut-desc" v-if="s.description">{{ s.description }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="shortcuts.length === 0" :description="$t('shortcuts.noShortcuts')" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { shortcutsApi } from '@/api/shortcuts'
import type { Shortcut } from '@/api/shortcuts'

const shortcuts = ref<Shortcut[]>([])

onMounted(async () => {
  try { shortcuts.value = await shortcutsApi.list() } catch { /* non-critical */ }
})

const openUrl = (url: string) => {
  window.open(url, '_blank', 'noopener')
}
</script>

<style scoped lang="scss">
.shortcuts-container {
  .page-header { margin-bottom: 20px; h1 { margin-bottom: 5px; } p { color: #909399; } }
  .shortcut-col { margin-bottom: 16px; }
  .shortcut-card {
    cursor: pointer; transition: transform 0.15s;
    &:hover { transform: translateY(-2px); }
    .shortcut-content {
      .shortcut-name { font-size: 16px; font-weight: bold; margin-bottom: 4px; }
      .shortcut-url { font-size: 12px; color: #409eff; word-break: break-all; margin-bottom: 4px; }
      .shortcut-desc { font-size: 13px; color: #909399; }
    }
  }
}
</style>
