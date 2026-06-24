<template>
  <div class="tools-container">
    <h1>{{ $t('tools.title') }}</h1>
    <p class="subtitle">{{ $t('tools.subtitle') }}</p>

    <el-tabs v-model="activeTab" type="border-card" tab-position="top">

      <!-- ═══════════════════════ 频率/波长 ═══════════════════════ -->
      <el-tab-pane :label="$t('tools.freqWavelength')" name="freq">
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
          <!-- 频段表 -->
          <h3 style="margin-top:24px">{{ $t('tools.hamBands') }}</h3>
          <el-table :data="hamBands" size="small" stripe border style="max-width:500px">
            <el-table-column prop="band" label="Band" width="70" />
            <el-table-column prop="freq" :label="$t('tools.frequency') + ' (MHz)'" width="160" />
            <el-table-column prop="wavelength" :label="$t('tools.wavelength') + ' (m)'" />
          </el-table>
          <!-- 公式 -->
          <div class="formula-note">
            <strong>{{ $t('tools.formula') }}：</strong> λ = c / f &nbsp; (c = 299,792,458 m/s, ITU-R standard)<br>
            <em>{{ $t('tools.source') }}：Maxwell's Equations / ITU-R Recommendations</em>
          </div>
        </div>
      </el-tab-pane>

      <!-- ═══════════════════════ 偶极天线 ═══════════════════════ -->
      <el-tab-pane :label="$t('tools.dipoleLength')" name="dipole">
        <div class="tool-panel">
          <!-- 示意图 -->
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
          <!-- 波段速查表 -->
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
      </el-tab-pane>

      <!-- ═══════════════════════ GP 垂直天线 ═══════════════════════ -->
      <el-tab-pane :label="$t('tools.verticalLength')" name="vertical">
        <div class="tool-panel">
          <!-- 示意图 -->
          <div class="diagram-box">
            <svg viewBox="0 0 320 220" class="antenna-svg">
              <!-- 垂直振子 -->
              <line x1="160" y1="20" x2="160" y2="150" stroke="#409eff" stroke-width="3" />
              <text x="175" y="90" font-size="11" fill="#409eff">λ/4 {{ $t('tools.vertical') }}</text>
              <!-- 馈电点 -->
              <circle cx="160" cy="150" r="5" fill="none" stroke="#e6a23c" stroke-width="2" />
              <text x="175" y="155" font-size="10" fill="#e6a23c">{{ $t('tools.feedpoint') }}</text>
              <!-- 同轴馈线 -->
              <line x1="160" y1="155" x2="160" y2="210" stroke="#909399" stroke-width="1.5" stroke-dasharray="4" />
              <!-- 地网 radial 1 (45度左下) -->
              <line x1="160" y1="150" x2="60" y2="195" stroke="#67c23a" stroke-width="2" />
              <text x="85" y="180" font-size="10" fill="#67c23a">{{ $t('tools.radial') }}</text>
              <!-- 地网 radial 2 (垂直向下) -->
              <line x1="160" y1="150" x2="160" y2="200" stroke="#67c23a" stroke-width="2" />
              <!-- 地网 radial 3 (45度右下) -->
              <line x1="160" y1="150" x2="260" y2="195" stroke="#67c23a" stroke-width="2" />
              <text x="215" y="180" font-size="10" fill="#67c23a">{{ $t('tools.radial') }}</text>
              <!-- 地网 radial 4 (水平左) -->
              <line x1="160" y1="150" x2="60" y2="150" stroke="#67c23a" stroke-width="2" />
              <!-- 地网 radial 5 (水平右) -->
              <line x1="160" y1="150" x2="260" y2="150" stroke="#67c23a" stroke-width="2" />
              <!-- 绝缘子 -->
              <rect x="152" y="12" width="16" height="12" fill="none" stroke="#909399" stroke-width="1" rx="2" />
              <text x="160" y="9" font-size="9" fill="#909399" text-anchor="middle">{{ $t('tools.insulator') }}</text>
              <!-- 地面 -->
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
          <!-- 波段速查表 -->
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
      </el-tab-pane>

      <!-- ═══════════════════════ SWR ═══════════════════════ -->
      <el-tab-pane label="SWR" name="swr">
        <div class="tool-panel">
          <!-- 示意图 -->
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
          <!-- SWR 参考表 -->
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
      </el-tab-pane>

      <!-- ═══════════════════════ LC 滤波器设计 ═══════════════════════ -->
      <el-tab-pane :label="$t('tools.lcFilter')" name="filter">
        <div class="tool-panel">
          <!-- 示意图：LC 梯形网络 -->
          <div class="diagram-box">
            <svg viewBox="0 0 600 140" class="antenna-svg">
              <line x1="20" y1="70" x2="80" y2="70" stroke="#303133" stroke-width="1.5" />
              <!-- L1 -->
              <path d="M80,70 Q90,40 100,70 Q110,40 120,70 Q130,40 140,70" fill="none" stroke="#409eff" stroke-width="2" />
              <text x="110" y="35" font-size="11" fill="#409eff" text-anchor="middle">L₁</text>
              <line x1="140" y1="70" x2="200" y2="70" stroke="#303133" stroke-width="1.5" />
              <!-- C1 -->
              <line x1="200" y1="50" x2="200" y2="90" stroke="#e6a23c" stroke-width="2" />
              <line x1="210" y1="50" x2="210" y2="90" stroke="#e6a23c" stroke-width="2" />
              <line x1="200" y1="70" x2="200" y2="120" stroke="#303133" stroke-width="1" />
              <line x1="210" y1="70" x2="210" y2="120" stroke="#303133" stroke-width="1" />
              <line x1="180" y1="120" x2="230" y2="120" stroke="#303133" stroke-width="1.5" />
              <text x="205" y="110" font-size="11" fill="#e6a23c" text-anchor="middle">C₁</text>
              <line x1="210" y1="70" x2="270" y2="70" stroke="#303133" stroke-width="1.5" />
              <!-- L2 -->
              <path d="M270,70 Q280,40 290,70 Q300,40 310,70 Q320,40 330,70" fill="none" stroke="#409eff" stroke-width="2" />
              <text x="300" y="35" font-size="11" fill="#409eff" text-anchor="middle">L₂</text>
              <line x1="330" y1="70" x2="390" y2="70" stroke="#303133" stroke-width="1.5" />
              <!-- C2 -->
              <line x1="390" y1="50" x2="390" y2="90" stroke="#e6a23c" stroke-width="2" />
              <line x1="400" y1="50" x2="400" y2="90" stroke="#e6a23c" stroke-width="2" />
              <line x1="390" y1="70" x2="390" y2="120" stroke="#303133" stroke-width="1" />
              <line x1="400" y1="70" x2="400" y2="120" stroke="#303133" stroke-width="1" />
              <line x1="370" y1="120" x2="420" y2="120" stroke="#303133" stroke-width="1.5" />
              <text x="395" y="110" font-size="11" fill="#e6a23c" text-anchor="middle">C₂</text>
              <line x1="400" y1="70" x2="500" y2="70" stroke="#303133" stroke-width="1.5" />
              <!-- 终端 -->
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
      </el-tab-pane>

      <!-- ═══════════════════════ 通用工具 ═══════════════════════ -->
      <el-tab-pane :label="$t('tools.general')" name="general">
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
      </el-tab-pane>

    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const activeTab = ref('freq')
const generalTab = ref('db')

const C = 299792458 // m/s

// ═══ 频率/波长 ═══
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

const hamBands = [
  { band: '160m', freq: '1.800 – 2.000', wavelength: '166.6 – 150.0' },
  { band: '80m', freq: '3.500 – 3.800', wavelength: '85.7 – 78.9' },
  { band: '40m', freq: '7.000 – 7.300', wavelength: '42.8 – 41.1' },
  { band: '30m', freq: '10.100 – 10.150', wavelength: '29.7 – 29.5' },
  { band: '20m', freq: '14.000 – 14.350', wavelength: '21.4 – 20.9' },
  { band: '17m', freq: '18.068 – 18.168', wavelength: '16.6 – 16.5' },
  { band: '15m', freq: '21.000 – 21.450', wavelength: '14.3 – 14.0' },
  { band: '12m', freq: '24.890 – 24.990', wavelength: '12.0 – 12.0' },
  { band: '10m', freq: '28.000 – 29.700', wavelength: '10.7 – 10.1' },
  { band: '6m', freq: '50.000 – 54.000', wavelength: '6.0 – 5.6' },
  { band: '2m', freq: '144.000 – 148.000', wavelength: '2.08 – 2.03' },
]

// ═══ 线材类型与缩短系数 ═══
// Source: ARRL Antenna Book, various wire manufacturer specs
const wireTypes = [
  { label: '裸铜线 (Bare Copper)', vf: 0.95 },
  { label: 'PVC 绝缘线 (PVC Insulated)', vf: 0.66 },
  { label: 'PE 绝缘线 (PE Insulated)', vf: 0.78 },
  { label: '特氟龙绝缘线 (Teflon/PTFE)', vf: 0.84 },
  { label: '铝管 (Aluminum Tubing)', vf: 0.95 },
  { label: '铜管 (Copper Tubing)', vf: 0.95 },
  { label: '镀铜钢线 (Copper-Clad Steel)', vf: 0.90 },
  { label: '不锈钢线 (Stainless Steel)', vf: 0.92 },
  { label: '自定义 (Custom)', vf: 0.95 },
]

// ═══ 偶极天线 ═══
const dipFreq = ref(0)
const dipVF = ref(0.95)
const dipWireType = ref('裸铜线 (Bare Copper)')
const onDipWireChange = (label: string) => {
  const w = wireTypes.find(w => w.label === label)
  if (w) dipVF.value = w.vf
}

// ═══ 垂直天线 ═══
const vertFreq = ref(0)
const vertVF = ref(0.95)
const vertWireType = ref('裸铜线 (Bare Copper)')
const onVertWireChange = (label: string) => {
  const w = wireTypes.find(w => w.label === label)
  if (w) vertVF.value = w.vf
}
const dipTotalFt = computed(() => dipFreq.value > 0 ? (468 * dipVF.value / dipFreq.value).toFixed(2) : '0')
const dipTotalM = computed(() => dipFreq.value > 0 ? (142.5 * dipVF.value / dipFreq.value).toFixed(2) : '0')
const dipLegFt = computed(() => dipFreq.value > 0 ? (468 * dipVF.value / dipFreq.value / 2).toFixed(2) : '0')
const dipLegM = computed(() => dipFreq.value > 0 ? (142.5 * dipVF.value / dipFreq.value / 2).toFixed(2) : '0')

const dipoleBandTable = [
  { band: '160m', freq: '1.830', totalFt: '255.7', totalM: '77.9', legFt: '127.9' },
  { band: '80m', freq: '3.550', totalFt: '131.8', totalM: '40.2', legFt: '65.9' },
  { band: '40m', freq: '7.150', totalFt: '65.5', totalM: '20.0', legFt: '32.7' },
  { band: '30m', freq: '10.125', totalFt: '46.2', totalM: '14.1', legFt: '23.1' },
  { band: '20m', freq: '14.175', totalFt: '33.0', totalM: '10.1', legFt: '16.5' },
  { band: '17m', freq: '18.118', totalFt: '25.8', totalM: '7.9', legFt: '12.9' },
  { band: '15m', freq: '21.225', totalFt: '22.0', totalM: '6.7', legFt: '11.0' },
  { band: '12m', freq: '24.940', totalFt: '18.8', totalM: '5.7', legFt: '9.4' },
  { band: '10m', freq: '28.850', totalFt: '16.2', totalM: '4.9', legFt: '8.1' },
  { band: '6m', freq: '52.000', totalFt: '9.0', totalM: '2.7', legFt: '4.5' },
]

// ═══ 垂直天线计算 ═══
const vertFt = computed(() => vertFreq.value > 0 ? (234 * vertVF.value / vertFreq.value).toFixed(2) : '0')
const vertM = computed(() => vertFreq.value > 0 ? (71.25 * vertVF.value / vertFreq.value).toFixed(2) : '0')

// 地网参数
const radialType = ref('quarter')
const numRadials = ref(4)
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

const gpBandTable = [
  { band: '160m', freq: '1.830', vertFt: '127.9', vertM: '39.0', radFt: '127.9' },
  { band: '80m', freq: '3.550', vertFt: '65.9', vertM: '20.1', radFt: '65.9' },
  { band: '40m', freq: '7.150', vertFt: '32.7', vertM: '10.0', radFt: '32.7' },
  { band: '30m', freq: '10.125', vertFt: '23.1', vertM: '7.0', radFt: '23.1' },
  { band: '20m', freq: '14.175', vertFt: '16.5', vertM: '5.0', radFt: '16.5' },
  { band: '17m', freq: '18.118', vertFt: '12.9', vertM: '3.9', radFt: '12.9' },
  { band: '15m', freq: '21.225', vertFt: '11.0', vertM: '3.4', radFt: '11.0' },
  { band: '12m', freq: '24.940', vertFt: '9.4', vertM: '2.9', radFt: '9.4' },
  { band: '10m', freq: '28.850', vertFt: '8.1', vertM: '2.5', radFt: '8.1' },
  { band: '6m', freq: '52.000', vertFt: '4.5', vertM: '1.4', radFt: '4.5' },
]

// ═══ SWR ═══
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

const swrRefTable = [
  { swr: '1.0', refl: '0.00', rl: '∞', status: 'Ideal' },
  { swr: '1.5', refl: '4.00', rl: '14.0', status: 'Good' },
  { swr: '2.0', refl: '11.1', rl: '9.5', status: 'OK' },
  { swr: '3.0', refl: '25.0', rl: '6.0', status: 'Fair' },
  { swr: '5.0', refl: '44.4', rl: '3.5', status: 'Poor' },
  { swr: '10.0', refl: '66.9', rl: '1.7', status: 'Bad' },
]

// ═══ LC 滤波器 ═══
const filtType = ref('lowpass')
const filtDesign = ref('butterworth')
const filtFc = ref(0)
const filtFcUnit = ref('MHz')
const filtZ = ref(50)
const filtN = ref(5)
const filtRipple = ref(0.5)

// Butterworth normalized g-values: g_k = 2*sin((2k-1)*π/(2N))
const butterworthG = (n: number): number[] => {
  const g: number[] = []
  for (let k = 1; k <= n; k++) {
    g.push(2 * Math.sin((2 * k - 1) * Math.PI / (2 * n)))
  }
  return g
}

// Chebyshev normalized g-values (0.5dB ripple default)
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
    const isL = (i % 2 === 0) // L starts first for lowpass L-input
    if (filtType.value === 'lowpass') {
      if (isL) {
        const uH = (gVals[i] * z / w) * 1e6
        result.push({ name: `L${i + 1}`, value: uH >= 1 ? `${uH.toFixed(2)} µH` : `${(uH * 1000).toFixed(1)} nH` })
      } else {
        const pF = (gVals[i] / (w * z)) * 1e12
        result.push({ name: `C${i + 1}`, value: pF >= 1000 ? `${(pF / 1000).toFixed(2)} nF` : `${pF.toFixed(1)} pF` })
      }
    } else {
      // High-pass: L and C are swapped
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

// ═══ dB 转换 ═══
const dbPwrIn = ref(0)
const dbPwrOut = ref(0)
const dbResult = computed(() => dbPwrIn.value > 0 && dbPwrOut.value > 0 ? (10 * Math.log10(dbPwrOut.value / dbPwrIn.value)).toFixed(2) : '0')

// ═══ 线规 ═══
const awgIdx = ref(14)
const awgTable = [
  { awg: 4, dia_mm: '5.19', dia_in: '0.204', ohm_km: '0.815', amps: '60' },
  { awg: 6, dia_mm: '4.11', dia_in: '0.162', ohm_km: '1.30', amps: '37' },
  { awg: 8, dia_mm: '3.26', dia_in: '0.129', ohm_km: '2.06', amps: '24' },
  { awg: 10, dia_mm: '2.59', dia_in: '0.102', ohm_km: '3.28', amps: '15' },
  { awg: 12, dia_mm: '2.05', dia_in: '0.081', ohm_km: '5.21', amps: '9.3' },
  { awg: 14, dia_mm: '1.63', dia_in: '0.064', ohm_km: '8.28', amps: '5.9' },
  { awg: 16, dia_mm: '1.29', dia_in: '0.051', ohm_km: '13.2', amps: '3.7' },
  { awg: 18, dia_mm: '1.02', dia_in: '0.040', ohm_km: '20.9', amps: '2.3' },
  { awg: 20, dia_mm: '0.81', dia_in: '0.032', ohm_km: '33.3', amps: '1.5' },
  { awg: 22, dia_mm: '0.64', dia_in: '0.025', ohm_km: '52.9', amps: '0.92' },
  { awg: 24, dia_mm: '0.51', dia_in: '0.020', ohm_km: '84.2', amps: '0.58' },
  { awg: 26, dia_mm: '0.40', dia_in: '0.016', ohm_km: '134', amps: '0.36' },
]
const awgData = computed(() => awgTable.find(g => g.awg === awgIdx.value) || null)
</script>

<style scoped lang="scss">
.tools-container {
  max-width: 1100px; margin: 0 auto;
  h1 { margin-bottom: 4px; }
  .subtitle { color: #909399; margin-bottom: 20px; }
  .tool-panel { padding: 16px 0; }
  h3 { margin: 0 0 14px; color: #303133; font-size: 15px; }
  .result-box {
    background: #f5f7fa; border-radius: 6px; padding: 14px 18px; margin-top: 12px;
    h4 { margin: 0 0 8px; font-size: 14px; color: #303133; }
    .result-row { margin-bottom: 8px; font-size: 14px; color: #606266;
      strong { color: #409eff; font-size: 15px; margin-left: 8px; }
      .swr-good { color: #67c23a; }
      .swr-ok { color: #e6a23c; }
      .swr-bad { color: #f56c6c; }
    }
  }
  .formula-note {
    margin-top: 20px; padding: 12px 16px; background: #fdf6ec; border-radius: 6px;
    font-size: 13px; color: #909399; line-height: 1.8;
    strong { color: #606266; }
    em { font-style: normal; color: #b0b3b8; }
  }
  .diagram-box {
    text-align: center; margin-bottom: 16px; padding: 12px; background: #fafafa; border-radius: 6px; border: 1px solid #ebeef5;
    .antenna-svg { max-width: 500px; width: 100%; height: auto; }
  }
  .field-hint { font-size: 12px; color: #909399; margin-top: 4px; }
}
</style>
