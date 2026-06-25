<template>
  <div class="tool-panel">
    <el-tabs v-model="generalTab" type="card">
      <!-- dB 转换 -->
      <el-tab-pane label="dB" name="db">
        <h3>{{ $t('tools.dbConverter') }}</h3>
        <el-form label-width="140px" style="max-width:460px">
          <el-form-item :label="$t('tools.powerIn') + ' (W)'">
            <el-input v-model.number="dbPwrIn" type="number" min="0" step="0.1" />
          </el-form-item>
          <el-form-item :label="$t('tools.powerOut') + ' (W)'">
            <el-input v-model.number="dbPwrOut" type="number" min="0" step="0.1" />
          </el-form-item>
        </el-form>
        <div class="result-box" v-if="dbPwrIn > 0 && dbPwrOut > 0">
          <div class="result-row"><span>dB：</span><strong>{{ dbResult }}</strong></div>
        </div>
        <div class="formula-note">
          <strong>{{ $t('tools.formula') }}：</strong> dB = 10 × log₁₀(P<sub>out</sub> / P<sub>in</sub>)<br>
          <em>{{ $t('tools.source') }}：Standard decibel definition (ITU-R)</em>
        </div>
      </el-tab-pane>
      <!-- 线规 -->
      <el-tab-pane :label="$t('tools.wireGauge')" name="wire">
        <h3>AWG {{ $t('tools.wireGauge') }}</h3>
        <el-form label-width="140px" style="max-width:460px">
          <el-form-item label="AWG">
            <el-select v-model.number="awgIdx" style="width:120px">
              <el-option v-for="g in awgTable" :key="g.awg" :label="g.awg" :value="g.awg" />
            </el-select>
          </el-form-item>
        </el-form>
        <div class="result-box" v-if="awgData">
          <div class="result-row"><span>{{ $t('tools.diameter') }}：</span><strong>{{ awgData.dia_mm }} mm / {{ awgData.dia_in }} in</strong></div>
          <div class="result-row"><span>{{ $t('tools.resistance') }}：</span><strong>{{ awgData.ohm_km }} Ω/km</strong></div>
          <div class="result-row"><span>{{ $t('tools.maxAmps') }}：</span><strong>{{ awgData.amps }} A</strong></div>
        </div>
        <div class="formula-note">
          <strong>{{ $t('tools.formula') }}：</strong> D(in) = 0.005 × 92^((36-AWG)/39)<br>
          <em>{{ $t('tools.source') }}：AWG standard (ASTM B258)</em>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { AWG_TABLE } from '@/utils/constants'

const generalTab = ref('db')
const awgTable = AWG_TABLE

// dB 转换
const dbPwrIn = ref(0)
const dbPwrOut = ref(0)
const dbResult = computed(() => dbPwrIn.value > 0 && dbPwrOut.value > 0 ? (10 * Math.log10(dbPwrOut.value / dbPwrIn.value)).toFixed(2) : '0')

// 线规
const awgIdx = ref(14)
const awgData = computed(() => awgTable.find(g => g.awg === awgIdx.value) || null)
</script>
