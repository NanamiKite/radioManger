<template>
  <div class="tool-panel">
    <div class="diagram-box">
      <svg viewBox="0 0 600 140" class="antenna-svg">
        <line x1="20" y1="70" x2="80" y2="70" stroke="#303133" stroke-width="1.5" />
        <path d="M80,70 Q90,40 100,70 Q110,40 120,70 Q130,40 140,70" fill="none" stroke="#409eff" stroke-width="2" />
        <text x="110" y="35" font-size="11" fill="#409eff" text-anchor="middle">L₁</text>
        <line x1="140" y1="70" x2="200" y2="70" stroke="#303133" stroke-width="1.5" />
        <line x1="200" y1="50" x2="200" y2="90" stroke="#e6a23c" stroke-width="2" />
        <line x1="210" y1="50" x2="210" y2="90" stroke="#e6a23c" stroke-width="2" />
        <line x1="200" y1="70" x2="200" y2="120" stroke="#303133" stroke-width="1" />
        <line x1="210" y1="70" x2="210" y2="120" stroke="#303133" stroke-width="1" />
        <line x1="180" y1="120" x2="230" y2="120" stroke="#303133" stroke-width="1.5" />
        <text x="205" y="110" font-size="11" fill="#e6a23c" text-anchor="middle">C₁</text>
        <line x1="210" y1="70" x2="270" y2="70" stroke="#303133" stroke-width="1.5" />
        <path d="M270,70 Q280,40 290,70 Q300,40 310,70 Q320,40 330,70" fill="none" stroke="#409eff" stroke-width="2" />
        <text x="300" y="35" font-size="11" fill="#409eff" text-anchor="middle">L₂</text>
        <line x1="330" y1="70" x2="390" y2="70" stroke="#303133" stroke-width="1.5" />
        <line x1="390" y1="50" x2="390" y2="90" stroke="#e6a23c" stroke-width="2" />
        <line x1="400" y1="50" x2="400" y2="90" stroke="#e6a23c" stroke-width="2" />
        <line x1="390" y1="70" x2="390" y2="120" stroke="#303133" stroke-width="1" />
        <line x1="400" y1="70" x2="400" y2="120" stroke="#303133" stroke-width="1" />
        <line x1="370" y1="120" x2="420" y2="120" stroke="#303133" stroke-width="1.5" />
        <text x="395" y="110" font-size="11" fill="#e6a23c" text-anchor="middle">C₂</text>
        <line x1="400" y1="70" x2="500" y2="70" stroke="#303133" stroke-width="1.5" />
        <rect x="500" y="55" width="40" height="30" fill="none" stroke="#909399" stroke-width="1.5" rx="3" />
        <text x="520" y="75" font-size="10" fill="#909399" text-anchor="middle">ZL</text>
        <line x1="20" y1="70" x2="20" y2="50" stroke="#303133" stroke-width="1" />
        <text x="20" y="42" font-size="10" fill="#909399" text-anchor="middle">Z₀</text>
      </svg>
    </div>
    <el-form label-width="160px" style="max-width:500px">
      <el-form-item :label="$t('tools.filterType')">
        <el-radio-group v-model="filtType">
          <el-radio value="lowpass">{{ $t('tools.lowpass') }}</el-radio>
          <el-radio value="highpass">{{ $t('tools.highpass') }}</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item :label="$t('tools.filterDesign')">
        <el-radio-group v-model="filtDesign">
          <el-radio value="butterworth">Butterworth</el-radio>
          <el-radio value="chebyshev">Chebyshev</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item :label="$t('tools.cutoffFreq')">
        <el-input v-model.number="filtFc" type="number" min="0" step="0.1">
          <template #append>
            <el-select v-model="filtFcUnit" style="width:80px">
              <el-option label="MHz" value="MHz" /><el-option label="kHz" value="kHz" /><el-option label="Hz" value="Hz" />
            </el-select>
          </template>
        </el-input>
      </el-form-item>
      <el-form-item :label="$t('tools.impedance') + ' (Ω)'">
        <el-input v-model.number="filtZ" type="number" min="1" step="1" placeholder="50" />
      </el-form-item>
      <el-form-item :label="$t('tools.numComponents')">
        <el-select v-model.number="filtN" style="width:120px">
          <el-option v-for="n in (filtDesign === 'chebyshev' ? [1,3,5,7,9] : [1,2,3,4,5,6,7,8,9])" :key="n" :label="n" :value="n" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="filtDesign === 'chebyshev'" :label="$t('tools.ripple') + ' (dB)'">
        <el-input v-model.number="filtRipple" type="number" min="0.01" max="3" step="0.01" placeholder="0.5" />
      </el-form-item>
    </el-form>
    <div class="result-box" v-if="filtFc > 0 && filtZ > 0">
      <h4>{{ $t('tools.componentValues') }}</h4>
      <div v-for="(val, idx) in filterValues" :key="idx" class="result-row">
        <span>{{ val.name }}：</span><strong>{{ val.value }}</strong>
      </div>
    </div>
    <div class="formula-note">
      <strong>Butterworth：</strong> g<sub>k</sub> = 2 × sin((2k-1)π / 2N), k = 1..N<br>
      <strong>Chebyshev：</strong> β = ln(coth(R<sub>dB</sub>/17.37)), γ = sinh(β/2N)<br>
      L<sub>k</sub> = g<sub>k</sub> × Z / (2π×f<sub>c</sub>) &nbsp;&nbsp; C<sub>k</sub> = g<sub>k</sub> / (2π×f<sub>c</sub>×Z)<br>
      <em>{{ $t('tools.source') }}：ARRL Handbook, LC Filter Design — Standard filter tables</em>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const filtType = ref('lowpass')
const filtDesign = ref('butterworth')
const filtFc = ref(0)
const filtFcUnit = ref('MHz')
const filtZ = ref(50)
const filtN = ref(5)
const filtRipple = ref(0.5)

const butterworthG = (n: number): number[] => {
  const g: number[] = []
  for (let k = 1; k <= n; k++) {
    g.push(2 * Math.sin((2 * k - 1) * Math.PI / (2 * n)))
  }
  return g
}

const chebyshevG = (n: number, rippleDb: number): number[] => {
  const beta = Math.log(1 / Math.tanh(rippleDb / 17.37))
  const gamma = Math.sinh(beta / (2 * n))
  const g: number[] = []
  for (let k = 1; k <= n; k++) {
    const ak = Math.sin((2 * k - 1) * Math.PI / (2 * n))
    const bk = gamma * gamma + Math.sin(k * Math.PI / n) * Math.sin(k * Math.PI / n)
    if (k === 1) {
      g.push(2 * ak / gamma)
    } else {
      const prev = g[k - 2]
      g.push(4 * ak * Math.sin((2 * k - 3) * Math.PI / (2 * n)) / (bk * prev))
    }
  }
  return g
}

const filterValues = computed(() => {
  if (filtFc.value <= 0 || filtZ.value <= 0) return []
  let fcHz = filtFc.value
  if (filtFcUnit.value === 'MHz') fcHz *= 1e6
  else if (filtFcUnit.value === 'kHz') fcHz *= 1e3
  const w = 2 * Math.PI * fcHz
  const z = filtZ.value
  const n = filtN.value

  const gVals = filtDesign.value === 'chebyshev'
    ? chebyshevG(n, filtRipple.value)
    : butterworthG(n)

  const result: { name: string; value: string }[] = []
  for (let i = 0; i < n; i++) {
    const isL = (i % 2 === 0)
    if (filtType.value === 'lowpass') {
      if (isL) {
        const uH = (gVals[i] * z / w) * 1e6
        result.push({ name: `L${i + 1}`, value: uH >= 1 ? `${uH.toFixed(2)} µH` : `${(uH * 1000).toFixed(1)} nH` })
      } else {
        const pF = (gVals[i] / (w * z)) * 1e12
        result.push({ name: `C${i + 1}`, value: pF >= 1000 ? `${(pF / 1000).toFixed(2)} nF` : `${pF.toFixed(1)} pF` })
      }
    } else {
      if (isL) {
        const uH = (z / (gVals[i] * w)) * 1e6
        result.push({ name: `C${i + 1}`, value: uH >= 1 ? `${uH.toFixed(2)} µF` : `${(uH * 1000).toFixed(1)} nF` })
      } else {
        const pF = (w * z / gVals[i]) * 1e6
        result.push({ name: `L${i + 1}`, value: `${pF.toFixed(2)} µH` })
      }
    }
  }
  return result
})
</script>
