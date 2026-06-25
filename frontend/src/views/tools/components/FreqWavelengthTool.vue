<template>
  <div class="tool-panel">
    <el-row :gutter="24">
      <el-col :span="11">
        <h3>{{ $t('tools.frequencyToWavelength') }}</h3>
        <el-form label-width="100px">
          <el-form-item :label="$t('tools.frequency')">
            <el-input v-model.number="freqInput" type="number" min="0" step="0.001">
              <template #append>
                <el-select v-model="freqUnit" style="width:80px">
                  <el-option label="MHz" value="MHz" /><el-option label="kHz" value="kHz" /><el-option label="GHz" value="GHz" />
                </el-select>
              </template>
            </el-input>
          </el-form-item>
        </el-form>
        <div class="result-box" v-if="freqInput > 0">
          <div class="result-row"><span>{{ $t('tools.wavelength') }}：</span><strong>{{ wlFull }} m</strong></div>
          <div class="result-row"><span>{{ $t('tools.halfWave') }}：</span><strong>{{ wlHalf }} m</strong></div>
          <div class="result-row"><span>{{ $t('tools.quarterWave') }}：</span><strong>{{ wlQuarter }} m</strong></div>
        </div>
      </el-col>
      <el-col :span="11" :offset="2">
        <h3>{{ $t('tools.wavelengthToFrequency') }}</h3>
        <el-form label-width="100px">
          <el-form-item :label="$t('tools.wavelength')">
            <el-input v-model.number="waveInput" type="number" min="0" step="0.001">
              <template #append>
                <el-select v-model="waveUnit" style="width:70px">
                  <el-option label="m" value="m" /><el-option label="cm" value="cm" /><el-option label="mm" value="mm" />
                </el-select>
              </template>
            </el-input>
          </el-form-item>
        </el-form>
        <div class="result-box" v-if="waveInput > 0">
          <div class="result-row"><span>{{ $t('tools.frequency') }}：</span><strong>{{ freqFromWave }} MHz</strong></div>
        </div>
      </el-col>
    </el-row>
    <h3 style="margin-top:24px">{{ $t('tools.hamBands') }}</h3>
    <el-table :data="hamBands" size="small" stripe border style="max-width:500px">
      <el-table-column prop="band" label="Band" width="70" />
      <el-table-column prop="freq" :label="$t('tools.frequency') + ' (MHz)'" width="160" />
      <el-table-column prop="wavelength" :label="$t('tools.wavelength') + ' (m)'" />
    </el-table>
    <div class="formula-note">
      <strong>{{ $t('tools.formula') }}：</strong> λ = c / f &nbsp; (c = 299,792,458 m/s, ITU-R standard)<br>
      <em>{{ $t('tools.source') }}：Maxwell's Equations / ITU-R Recommendations</em>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { SPEED_OF_LIGHT, HAM_BANDS } from '@/utils/constants'

const C = SPEED_OF_LIGHT
const hamBands = HAM_BANDS

const freqInput = ref(0)
const freqUnit = ref('MHz')
const waveInput = ref(0)
const waveUnit = ref('m')

const freqHz = computed(() => {
  const f = freqInput.value
  if (freqUnit.value === 'GHz') return f * 1e9
  if (freqUnit.value === 'kHz') return f * 1e3
  return f * 1e6
})
const wlFull = computed(() => freqInput.value > 0 ? (C / freqHz.value).toFixed(4) : '0')
const wlHalf = computed(() => freqInput.value > 0 ? (C / freqHz.value / 2).toFixed(4) : '0')
const wlQuarter = computed(() => freqInput.value > 0 ? (C / freqHz.value / 4).toFixed(4) : '0')

const waveM = computed(() => {
  const w = waveInput.value
  if (waveUnit.value === 'cm') return w / 100
  if (waveUnit.value === 'mm') return w / 1000
  return w
})
const freqFromWave = computed(() => waveInput.value > 0 ? (C / waveM.value / 1e6).toFixed(6) : '0')
</script>
