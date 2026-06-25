<template>
  <div class="tool-panel">
    <div class="diagram-box">
      <svg viewBox="0 0 600 160" class="antenna-svg">
        <line x1="80" y1="80" x2="260" y2="80" stroke="#409eff" stroke-width="3" />
        <line x1="340" y1="80" x2="520" y2="80" stroke="#409eff" stroke-width="3" />
        <circle cx="300" cy="80" r="8" fill="none" stroke="#303133" stroke-width="2" />
        <line x1="300" y1="88" x2="300" y2="140" stroke="#909399" stroke-width="2" />
        <rect x="60" y="65" width="16" height="30" fill="none" stroke="#909399" stroke-width="1.5" rx="2" />
        <rect x="524" y="65" width="16" height="30" fill="none" stroke="#909399" stroke-width="1.5" rx="2" />
        <text x="170" y="70" font-size="12" fill="#409eff" text-anchor="middle">← {{ $t('tools.eachLeg') }} →</text>
        <text x="300" y="155" font-size="11" fill="#909399" text-anchor="middle">{{ $t('tools.feedpoint') }}</text>
        <text x="68" y="55" font-size="10" fill="#909399" text-anchor="middle">{{ $t('tools.insulator') }}</text>
        <text x="532" y="55" font-size="10" fill="#909399" text-anchor="middle">{{ $t('tools.insulator') }}</text>
      </svg>
    </div>
    <el-form label-width="140px" style="max-width:460px">
      <el-form-item :label="$t('tools.frequency') + ' (MHz)'">
        <el-input v-model.number="dipFreq" type="number" min="0" step="0.01" placeholder="14.200" />
      </el-form-item>
      <el-form-item :label="$t('tools.wireType')">
        <el-select v-model="dipWireType" @change="onDipWireChange" style="width:100%">
          <el-option v-for="w in wireTypes" :key="w.label" :label="w.label" :value="w.label" />
        </el-select>
      </el-form-item>
      <el-form-item :label="$t('tools.velocityFactor')">
        <el-input v-model.number="dipVF" type="number" min="0.3" max="1" step="0.01" />
      </el-form-item>
    </el-form>
    <div class="result-box" v-if="dipFreq > 0">
      <div class="result-row"><span>{{ $t('tools.totalLength') }}：</span><strong>{{ dipTotalFt }} ft / {{ dipTotalM }} m</strong></div>
      <div class="result-row"><span>{{ $t('tools.eachLeg') }}：</span><strong>{{ dipLegFt }} ft / {{ dipLegM }} m</strong></div>
    </div>
    <h3 style="margin-top:24px">{{ $t('tools.dipoleBandTable') }}</h3>
    <el-table :data="dipoleBandTable" size="small" stripe border style="max-width:600px">
      <el-table-column prop="band" label="Band" width="70" />
      <el-table-column prop="freq" label="Freq (MHz)" width="130" />
      <el-table-column prop="totalFt" label="Total (ft)" width="100" />
      <el-table-column prop="totalM" label="Total (m)" width="100" />
      <el-table-column prop="legFt" label="Leg (ft)" />
    </el-table>
    <div class="formula-note">
      <strong>{{ $t('tools.formula') }}：</strong> L(ft) = 468 × VF / f(MHz) &nbsp; {{ $t('tools.or') }} &nbsp; L(m) = 142.5 × VF / f(MHz)<br>
      <em>{{ $t('tools.source') }}：ARRL Antenna Book — 468 factor accounts for ~5% end effect (VF ≈ 0.95 for bare copper)</em>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { WIRE_TYPES, DIPOLE_BAND_TABLE } from '@/utils/constants'

const wireTypes = WIRE_TYPES
const dipoleBandTable = DIPOLE_BAND_TABLE

const dipFreq = ref(0)
const dipVF = ref(0.95)
const dipWireType = ref('裸铜线 (Bare Copper)')
const onDipWireChange = (label: string) => {
  const w = wireTypes.find(w => w.label === label)
  if (w) dipVF.value = w.vf
}

const dipTotalFt = computed(() => dipFreq.value > 0 ? (468 * dipVF.value / dipFreq.value).toFixed(2) : '0')
const dipTotalM = computed(() => dipFreq.value > 0 ? (142.5 * dipVF.value / dipFreq.value).toFixed(2) : '0')
const dipLegFt = computed(() => dipFreq.value > 0 ? (468 * dipVF.value / dipFreq.value / 2).toFixed(2) : '0')
const dipLegM = computed(() => dipFreq.value > 0 ? (142.5 * dipVF.value / dipFreq.value / 2).toFixed(2) : '0')
</script>
