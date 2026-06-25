<template>
  <div class="tools-container">
    <h1>{{ $t('tools.title') }}</h1>
    <p class="subtitle">{{ $t('tools.subtitle') }}</p>

    <el-tabs v-model="activeTab" type="border-card" tab-position="top">
      <el-tab-pane :label="$t('tools.freqWavelength')" name="freq">
        <FreqWavelengthTool />
      </el-tab-pane>
      <el-tab-pane :label="$t('tools.dipoleLength')" name="dipole">
        <DipoleTool />
      </el-tab-pane>
      <el-tab-pane :label="$t('tools.verticalLength')" name="vertical">
        <VerticalTool />
      </el-tab-pane>
      <el-tab-pane label="SWR" name="swr">
        <SwrTool />
      </el-tab-pane>
      <el-tab-pane :label="$t('tools.lcFilter')" name="filter">
        <LcFilterTool />
      </el-tab-pane>
      <el-tab-pane :label="$t('tools.general')" name="general">
        <GeneralTools />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FreqWavelengthTool from './components/FreqWavelengthTool.vue'
import DipoleTool from './components/DipoleTool.vue'
import VerticalTool from './components/VerticalTool.vue'
import SwrTool from './components/SwrTool.vue'
import LcFilterTool from './components/LcFilterTool.vue'
import GeneralTools from './components/GeneralTools.vue'

const activeTab = ref('freq')
</script>

<style scoped lang="scss">
.tools-container {
  max-width: 1100px; margin: 0 auto;
  h1 { margin-bottom: 4px; }
  .subtitle { color: var(--text-color-secondary); margin-bottom: 20px; }
}

// 子组件共享样式通过 :deep() 注入
:deep(.tool-panel) { padding: 16px 0; }
:deep(h3) { margin: 0 0 14px; color: var(--text-color-primary); font-size: 15px; }
:deep(.result-box) {
  background: var(--bg-color-hover); border-radius: 6px; padding: 14px 18px; margin-top: 12px;
  h4 { margin: 0 0 8px; font-size: 14px; color: var(--text-color-primary); }
  .result-row { margin-bottom: 8px; font-size: 14px; color: var(--text-color-regular);
    strong { color: var(--color-accent); font-size: 15px; margin-left: 8px; }
    .swr-good { color: var(--color-success); }
    .swr-ok { color: var(--color-warning); }
    .swr-bad { color: var(--color-danger); }
  }
}
:deep(.formula-note) {
  margin-top: 20px; padding: 12px 16px; background: var(--bg-color-page); border-radius: 6px;
  font-size: 13px; color: var(--text-color-secondary); line-height: 1.8;
  strong { color: var(--text-color-regular); }
  em { font-style: normal; color: var(--text-color-placeholder); }
}
:deep(.diagram-box) {
  text-align: center; margin-bottom: 16px; padding: 12px; background: var(--bg-color); border-radius: 6px; border: 1px solid var(--border-color-lighter);
  .antenna-svg { max-width: 500px; width: 100%; height: auto; }
}
:deep(.field-hint) { font-size: 12px; color: var(--text-color-secondary); margin-top: 4px; }
</style>
