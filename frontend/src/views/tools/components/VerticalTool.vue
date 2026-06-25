<template>
  <div class="tool-panel">
    <div class="diagram-box">
      <svg viewBox="0 0 320 220" class="antenna-svg">
        <line x1="160" y1="20" x2="160" y2="150" stroke="#409eff" stroke-width="3" />
        <text x="175" y="90" font-size="11" fill="#409eff">λ/4 {{ $t('tools.vertical') }}</text>
        <circle cx="160" cy="150" r="5" fill="none" stroke="#e6a23c" stroke-width="2" />
        <text x="175" y="155" font-size="10" fill="#e6a23c">{{ $t('tools.feedpoint') }}</text>
        <line x1="160" y1="155" x2="160" y2="210" stroke="#909399" stroke-width="1.5" stroke-dasharray="4" />
        <line x1="160" y1="150" x2="60" y2="195" stroke="#67c23a" stroke-width="2" />
        <text x="85" y="180" font-size="10" fill="#67c23a">{{ $t('tools.radial') }}</text>
        <line x1="160" y1="150" x2="160" y2="200" stroke="#67c23a" stroke-width="2" />
        <line x1="160" y1="150" x2="260" y2="195" stroke="#67c23a" stroke-width="2" />
        <text x="215" y="180" font-size="10" fill="#67c23a">{{ $t('tools.radial') }}</text>
        <line x1="160" y1="150" x2="60" y2="150" stroke="#67c23a" stroke-width="2" />
        <line x1="160" y1="150" x2="260" y2="150" stroke="#67c23a" stroke-width="2" />
        <rect x="152" y="12" width="16" height="12" fill="none" stroke="#909399" stroke-width="1" rx="2" />
        <text x="160" y="9" font-size="9" fill="#909399" text-anchor="middle">{{ $t('tools.insulator') }}</text>
        <line x1="40" y1="200" x2="280" y2="200" stroke="#c0c4cc" stroke-width="1" stroke-dasharray="3" />
      </svg>
    </div>
    <el-form label-width="140px" style="max-width:460px">
      <el-form-item :label="$t('tools.frequency') + ' (MHz)'">
        <el-input v-model.number="vertFreq" type="number" min="0" step="0.01" placeholder="14.200" />
      </el-form-item>
      <el-form-item :label="$t('tools.wireType')">
        <el-select v-model="vertWireType" @change="onVertWireChange" style="width:100%">
          <el-option v-for="w in wireTypes" :key="w.label" :label="w.label" :value="w.label" />
        </el-select>
      </el-form-item>
      <el-form-item :label="$t('tools.velocityFactor')">
        <el-input v-model.number="vertVF" type="number" min="0.3" max="1" step="0.01" />
      </el-form-item>
      <el-form-item :label="$t('tools.radialType')">
        <el-select v-model="radialType" style="width:100%">
          <el-option :label="$t('tools.radialQuarter')" value="quarter" />
          <el-option :label="$t('tools.radialHalf')" value="half" />
        </el-select>
        <div class="field-hint">{{ $t('tools.radialHint') }}</div>
      </el-form-item>
      <el-form-item :label="$t('tools.numRadials')">
        <el-select v-model.number="numRadials" style="width:120px">
          <el-option v-for="n in [4, 8, 12, 16, 24, 32, 36]" :key="n" :label="n" :value="n" />
        </el-select>
      </el-form-item>
    </el-form>
    <div class="result-box" v-if="vertFreq > 0">
      <div class="result-row"><span>{{ $t('tools.verticalElement') }} (λ/4)：</span><strong>{{ vertFt }} ft / {{ vertM }} m</strong></div>
      <div class="result-row"><span>{{ $t('tools.radialLength') }} ({{ radialType === 'quarter' ? 'λ/4' : 'λ/2' }})：</span><strong>{{ radialFt }} ft / {{ radialM }} m</strong></div>
      <div class="result-row"><span>{{ $t('tools.radialsTotal') }} ({{ numRadials }}×)：</span><strong>{{ radialTotalM }} m / {{ radialTotalFt }} ft</strong></div>
    </div>
    <h3 style="margin-top:24px">GP {{ $t('tools.bandTable') }} (λ/4 {{ $t('tools.radials') }})</h3>
    <el-table :data="gpBandTable" size="small" stripe border style="max-width:600px">
      <el-table-column prop="band" label="Band" width="70" />
      <el-table-column prop="freq" label="Freq (MHz)" width="120" />
      <el-table-column prop="vertFt" :label="$t('tools.vertical') + ' (ft)'" width="110" />
      <el-table-column prop="vertM" :label="$t('tools.vertical') + ' (m)'" width="110" />
      <el-table-column prop="radFt" :label="$t('tools.radial') + ' (ft)'" />
    </el-table>
    <div class="formula-note">
      <strong>{{ $t('tools.vertical') }}：</strong> L(ft) = 234 × VF / f(MHz) &nbsp; {{ $t('tools.or') }} &nbsp; L(m) = 71.25 × VF / f(MHz)<br>
      <strong>{{ $t('tools.radials') }}：</strong> λ/4 = {{ $t('tools.sameAsVertical') }}; λ/2 = 468 × VF / f(MHz)<br>
      <em>{{ $t('tools.source') }}：ARRL Antenna Book — Ground Plane Antenna. Radials at 45° downward for ~50Ω impedance.</em>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { WIRE_TYPES, GP_BAND_TABLE } from '@/utils/constants'

const wireTypes = WIRE_TYPES
const gpBandTable = GP_BAND_TABLE

const vertFreq = ref(0)
const vertVF = ref(0.95)
const vertWireType = ref('裸铜线 (Bare Copper)')
const onVertWireChange = (label: string) => {
  const w = wireTypes.find(w => w.label === label)
  if (w) vertVF.value = w.vf
}

const radialType = ref('quarter')
const numRadials = ref(4)

const vertFt = computed(() => vertFreq.value > 0 ? (234 * vertVF.value / vertFreq.value).toFixed(2) : '0')
const vertM = computed(() => vertFreq.value > 0 ? (71.25 * vertVF.value / vertFreq.value).toFixed(2) : '0')

const radialFt = computed(() => {
  if (vertFreq.value <= 0) return '0'
  return radialType.value === 'quarter'
    ? (234 * vertVF.value / vertFreq.value).toFixed(2)
    : (468 * vertVF.value / vertFreq.value).toFixed(2)
})
const radialM = computed(() => {
  if (vertFreq.value <= 0) return '0'
  return radialType.value === 'quarter'
    ? (71.25 * vertVF.value / vertFreq.value).toFixed(2)
    : (142.5 * vertVF.value / vertFreq.value).toFixed(2)
})
const radialTotalFt = computed(() => vertFreq.value > 0 ? (parseFloat(radialFt.value) * numRadials.value).toFixed(1) : '0')
const radialTotalM = computed(() => vertFreq.value > 0 ? (parseFloat(radialM.value) * numRadials.value).toFixed(1) : '0')
</script>
