<template>
  <div class="tool-panel">
    <div class="diagram-box">
      <svg viewBox="0 0 500 100" class="antenna-svg">
        <rect x="10" y="30" width="80" height="40" fill="none" stroke="#409eff" stroke-width="1.5" rx="4" />
        <text x="50" y="55" font-size="11" fill="#409eff" text-anchor="middle">TX/RX</text>
        <line x1="90" y1="50" x2="200" y2="50" stroke="#909399" stroke-width="2" />
        <text x="145" y="42" font-size="10" fill="#909399" text-anchor="middle">Z₀</text>
        <rect x="200" y="30" width="60" height="40" fill="none" stroke="#e6a23c" stroke-width="1.5" rx="4" />
        <text x="230" y="55" font-size="10" fill="#e6a23c" text-anchor="middle">SWR</text>
        <line x1="260" y1="50" x2="370" y2="50" stroke="#909399" stroke-width="2" />
        <text x="315" y="42" font-size="10" fill="#909399" text-anchor="middle">Z₀</text>
        <polygon points="370,30 430,50 370,70" fill="none" stroke="#67c23a" stroke-width="1.5" />
        <text x="400" y="55" font-size="10" fill="#67c23a" text-anchor="middle">ZL</text>
        <text x="460" y="55" font-size="10" fill="#909399">Ant</text>
      </svg>
    </div>
    <el-row :gutter="24">
      <el-col :span="11">
        <h3>{{ $t('tools.fromImpedance') }}</h3>
        <el-form label-width="140px">
          <el-form-item :label="$t('tools.feedpointImpedance') + ' (Ω)'">
            <el-input v-model.number="swrZL" type="number" min="0" step="1" placeholder="50" />
          </el-form-item>
          <el-form-item :label="$t('tools.feedlineImpedance') + ' (Ω)'">
            <el-input v-model.number="swrZ0" type="number" min="1" step="1" placeholder="50" />
          </el-form-item>
        </el-form>
        <div class="result-box" v-if="swrZL > 0 && swrZ0 > 0">
          <div class="result-row"><span>SWR：</span><strong :class="swrClass(swrFromZNum)">{{ swrFromZ }}</strong></div>
          <div class="result-row"><span>|Γ|：</span><strong>{{ gammaFromZ }}</strong></div>
          <div class="result-row"><span>{{ $t('tools.reflectedPower') }}：</span><strong>{{ reflFromZ }}%</strong></div>
          <div class="result-row"><span>{{ $t('tools.returnLoss') }}：</span><strong>{{ rlFromZ }} dB</strong></div>
          <div class="result-row"><span>{{ $t('tools.mismatchLoss') }}：</span><strong>{{ mlFromZ }} dB</strong></div>
        </div>
      </el-col>
      <el-col :span="11" :offset="2">
        <h3>{{ $t('tools.fromSWR') }}</h3>
        <el-form label-width="140px">
          <el-form-item label="SWR">
            <el-input v-model.number="swrVal" type="number" min="1" step="0.1" placeholder="1.5" />
          </el-form-item>
        </el-form>
        <div class="result-box" v-if="swrVal >= 1">
          <div class="result-row"><span>|Γ|：</span><strong>{{ gammaFromSWR }}</strong></div>
          <div class="result-row"><span>{{ $t('tools.reflectedPower') }}：</span><strong>{{ reflFromSWR }}%</strong></div>
          <div class="result-row"><span>{{ $t('tools.returnLoss') }}：</span><strong>{{ rlFromSWR }} dB</strong></div>
          <div class="result-row"><span>{{ $t('tools.mismatchLoss') }}：</span><strong>{{ mlFromSWR }} dB</strong></div>
        </div>
      </el-col>
    </el-row>
    <h3 style="margin-top:24px">SWR {{ $t('tools.referenceTable') }}</h3>
    <el-table :data="swrRefTable" size="small" stripe border style="max-width:500px">
      <el-table-column prop="swr" label="SWR" width="70" />
      <el-table-column prop="refl" :label="$t('tools.reflectedPower') + ' (%)'" width="130" />
      <el-table-column prop="rl" :label="$t('tools.returnLoss') + ' (dB)'" />
      <el-table-column prop="status" :label="$t('tools.status')" />
    </el-table>
    <div class="formula-note">
      <strong>{{ $t('tools.formula') }}：</strong><br>
      Γ = (Z<sub>L</sub> - Z<sub>0</sub>) / (Z<sub>L</sub> + Z<sub>0</sub>)<br>
      SWR = (1 + |Γ|) / (1 - |Γ|) &nbsp;&nbsp; P<sub>ref</sub> = |Γ|² × 100%<br>
      RL = -20 × log₁₀(|Γ|) dB &nbsp;&nbsp; ML = -10 × log₁₀(1 - |Γ|²) dB<br>
      <em>{{ $t('tools.source') }}：ARRL Handbook, Transmission Line Theory</em>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { SWR_REF_TABLE } from '@/utils/constants'

const swrRefTable = SWR_REF_TABLE

const swrZL = ref(0)
const swrZ0 = ref(50)
const swrVal = ref(0)

const gamma = (zl: number, z0: number) => Math.abs((zl - z0) / (zl + z0))
const gammaFromZ = computed(() => swrZL.value > 0 ? gamma(swrZL.value, swrZ0.value).toFixed(4) : '0')
const swrFromZNum = computed(() => { if (swrZL.value <= 0) return 0; const g = gamma(swrZL.value, swrZ0.value); return g >= 1 ? Infinity : (1 + g) / (1 - g) })
const swrFromZ = computed(() => isFinite(swrFromZNum.value) ? swrFromZNum.value.toFixed(2) : '∞')
const reflFromZ = computed(() => swrZL.value > 0 ? (Math.pow(gamma(swrZL.value, swrZ0.value), 2) * 100).toFixed(2) : '0')
const rlFromZ = computed(() => { if (swrZL.value <= 0) return '0'; const g = gamma(swrZL.value, swrZ0.value); return g === 0 ? '∞' : (-20 * Math.log10(g)).toFixed(2) })
const mlFromZ = computed(() => { if (swrZL.value <= 0) return '0'; const g = gamma(swrZL.value, swrZ0.value); return (-10 * Math.log10(1 - g * g)).toFixed(3) })

const gammaFromSWR = computed(() => swrVal.value >= 1 ? ((swrVal.value - 1) / (swrVal.value + 1)).toFixed(4) : '0')
const reflFromSWR = computed(() => { if (swrVal.value < 1) return '0'; const g = (swrVal.value - 1) / (swrVal.value + 1); return (g * g * 100).toFixed(2) })
const rlFromSWR = computed(() => { if (swrVal.value < 1) return '0'; const g = (swrVal.value - 1) / (swrVal.value + 1); return g === 0 ? '∞' : (-20 * Math.log10(g)).toFixed(2) })
const mlFromSWR = computed(() => { if (swrVal.value < 1) return '0'; const g = (swrVal.value - 1) / (swrVal.value + 1); return (-10 * Math.log10(1 - g * g)).toFixed(3) })

const swrClass = (v: number) => v <= 1.5 ? 'swr-good' : v <= 3 ? 'swr-ok' : 'swr-bad'
</script>
