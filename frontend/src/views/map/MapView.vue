<template>
  <div class="map-page">
    <div ref="mapContainer" class="map-container"></div>
    <div class="map-toolbar">
      <div class="toolbar-title">{{ $t('map.title') }}</div>
      <div class="toolbar-section">
        <div class="toolbar-label">{{ $t('map.displayMode') }}</div>
        <el-radio-group v-model="displayMode" size="small" @change="redraw">
          <el-radio-button value="grid">{{ $t('map.gridMode') }}</el-radio-button>
          <el-radio-button value="radial">{{ $t('map.radialMode') }}</el-radio-button>
        </el-radio-group>
      </div>
      <div class="toolbar-section">
        <el-checkbox v-model="showGreyline" @change="toggleGreyline">{{ $t('map.greyline') }}</el-checkbox>
      </div>
      <div class="toolbar-section" v-if="myGrid">
        <div class="toolbar-label">{{ $t('map.myStation') }}</div>
        <div class="toolbar-value">{{ myGrid }}</div>
      </div>
      <div class="toolbar-section" v-if="selectedGrid">
        <div class="toolbar-label">{{ $t('map.selectedGrid') }}</div>
        <div class="toolbar-value">{{ selectedGrid.grid }}</div>
        <div class="toolbar-stat">{{ $t('map.qsoCount') }}: <strong>{{ selectedGrid.count }}</strong></div>
        <div class="toolbar-stat">{{ $t('map.confirmed') }}: <strong>{{ selectedGrid.confirmed }}</strong></div>
        <el-button size="small" type="primary" @click="goToLogs" style="margin-top:8px">{{ $t('map.viewLogs') }}</el-button>
      </div>
      <div class="toolbar-section">
        <div class="toolbar-label">{{ $t('map.legend') }}</div>
        <div class="legend">
          <div class="legend-item"><span class="legend-color" style="background:rgba(100,100,100,0.15);border:1px solid #ccc"></span> {{ $t('map.noQso') }}</div>
          <div class="legend-item"><span class="legend-color" style="background:#3b82f6"></span> 1-5</div>
          <div class="legend-item"><span class="legend-color" style="background:#22c55e"></span> 6-20</div>
          <div class="legend-item"><span class="legend-color" style="background:#eab308"></span> 21-50</div>
          <div class="legend-item"><span class="legend-color" style="background:#ef4444"></span> 50+</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { getPosition as getSunPosition } from 'suncalc'
import { mapApi, type GridData, type MapGridsResponse } from '@/api/map'
import { gridBounds, gridToLatLon } from '@/utils/grid'

const router = useRouter()
const { t } = useI18n()

const mapContainer = ref<HTMLElement>()
const displayMode = ref<'grid' | 'radial'>('grid')
const selectedGrid = ref<GridData | null>(null)
const myGrid = ref<string | null>(null)
const showGreyline = ref(false)

let map: L.Map | null = null
let overlayGroup = L.layerGroup()
let greylineLayer: L.LayerGroup | null = null
let gridData: MapGridsResponse | null = null
let gridLabels: L.Marker[] = []

// ── 自定义缩放滑块控件 ──
const ZoomSliderControl = L.Control.extend({
  onAdd: function () {
    const container = L.DomUtil.create('div', 'zoom-slider-control')
    container.innerHTML = `
      <div class="zs-track">
        <div class="zs-fill"></div>
        <div class="zs-thumb"></div>
      </div>
      <div class="zs-label">3</div>
    `
    L.DomEvent.disableClickPropagation(container)
    const track = container.querySelector('.zs-track') as HTMLElement
    const fill = container.querySelector('.zs-fill') as HTMLElement
    const thumb = container.querySelector('.zs-thumb') as HTMLElement
    const label = container.querySelector('.zs-label') as HTMLElement
    let dragging = false
    const MIN_Z = 2, MAX_Z = 12

    const posToZoom = (y: number) => {
      const rect = track.getBoundingClientRect()
      const ratio = 1 - Math.max(0, Math.min(1, (y - rect.top) / rect.height))
      return Math.round(MIN_Z + ratio * (MAX_Z - MIN_Z))
    }
    const updateVisual = (zoom: number) => {
      const ratio = (zoom - MIN_Z) / (MAX_Z - MIN_Z)
      const pct = ratio * 100
      fill.style.height = pct + '%'
      thumb.style.bottom = 'calc(' + pct + '% - 7px)'
      label.textContent = String(zoom)
    }

    track.addEventListener('mousedown', (e: MouseEvent) => {
      dragging = true
      const z = posToZoom(e.clientY)
      if (map) map.setZoom(z)
      updateVisual(z)
      e.preventDefault()
    })
    const onMouseMove = (e: MouseEvent) => {
      if (!dragging) return
      const z = posToZoom(e.clientY)
      if (map) map.setZoom(z)
      updateVisual(z)
    }
    const onMouseUp = () => { dragging = false }
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)

    // 暴露更新方法和清理用的监听器引用
    ;(this as any)._updateVisual = updateVisual
    ;(this as any)._onMouseMove = onMouseMove
    ;(this as any)._onMouseUp = onMouseUp
    return container
  },
  _update: function (zoom: number) {
    const fn = (this as any)._updateVisual
    if (fn) fn(zoom)
  }
})

let zoomSliderControl: any = null

function allGrid4(): string[] {
  const g: string[] = []
  for (let a = 0; a < 18; a++)
    for (let b = 0; b < 18; b++)
      for (let c = 0; c < 10; c++)
        for (let d = 0; d < 10; d++)
          g.push(String.fromCharCode(65 + a) + String.fromCharCode(65 + b) + c + d)
  return g
}

function gridColor(count: number): string {
  if (count >= 50) return '#ef4444'
  if (count >= 21) return '#eab308'
  if (count >= 6) return '#22c55e'
  return '#3b82f6'
}

// ── 灰线 ──
function nightPolygon(): [number, number][] {
  const now = new Date()
  const pts: [number, number][] = []
  for (let lon = -180; lon <= 180; lon += 2) {
    let found = false
    for (let lat = -89; lat <= 89; lat++) {
      const a = getSunPosition(now, lat, lon).altitude
      const b = getSunPosition(now, lat + 1, lon).altitude
      if (a < 0 && b >= 0) { pts.push([lat + Math.abs(a) / (Math.abs(a) + b), lon]); found = true; break }
    }
    if (!found) pts.push([getSunPosition(now, 0, lon).altitude < 0 ? 90 : -90, lon])
  }
  const n = getSunPosition(now, 89, 0).altitude < 0
  const edge = n ? pts : [...pts].reverse()
  return [n ? [90, -180] : [-90, -180], ...edge, n ? [90, 180] : [-90, 180], n ? [90, -180] : [-90, -180]]
}

function terminatorLine(): [number, number][] {
  const now = new Date()
  const pts: [number, number][] = []
  for (let lon = -180; lon <= 180; lon += 2) {
    for (let lat = -89; lat <= 89; lat++) {
      const a = getSunPosition(now, lat, lon).altitude
      const b = getSunPosition(now, lat + 1, lon).altitude
      if (a < 0 && b >= 0) { pts.push([lat + Math.abs(a) / (Math.abs(a) + b), lon]); break }
    }
  }
  return pts
}

function toggleGreyline(on: boolean) {
  if (!map) return
  if (greylineLayer) { map.removeLayer(greylineLayer); greylineLayer = null }
  if (!on) return
  greylineLayer = L.layerGroup()
  L.polygon(nightPolygon(), { color: 'transparent', fillColor: '#1a1a2e', fillOpacity: 0.25, interactive: false }).addTo(greylineLayer)
  const line = terminatorLine()
  if (line.length > 1) L.polyline(line, { color: '#f59e0b', weight: 2, opacity: 0.8, interactive: false }).addTo(greylineLayer)
  greylineLayer.addTo(map)
}

function drawMyStation() {
  if (!map || !gridData?.my_lat || !gridData?.my_lon) return
  const icon = L.divIcon({
    className: 'my-icon',
    html: '<div style="background:#409eff;width:14px;height:14px;border-radius:50%;border:3px solid white;box-shadow:0 0 6px rgba(0,0,0,0.4)"></div>',
    iconSize: [14, 14], iconAnchor: [7, 7],
  })
  L.marker([gridData.my_lat, gridData.my_lon], { icon })
    .bindTooltip(myGrid.value || 'My QTH', { permanent: true, direction: 'top', offset: [0, -10] })
    .addTo(overlayGroup)
}

function drawGridLabels() {
  for (const m of gridLabels) m.remove()
  gridLabels = []
  if (!map) return
  const zoom = map.getZoom()
  if (zoom < 5) return
  const active = new Map<string, GridData>()
  if (gridData) for (const g of gridData.grids) active.set(g.grid, g)
  const bounds = map.getBounds()
  for (const g4 of allGrid4()) {
    const center = gridToLatLon(g4)
    if (!center) continue
    if (!bounds.contains(L.latLng(center[0], center[1]))) continue
    const data = active.get(g4)
    const label = data ? g4 + ' (' + data.count + ')' : g4
    const color = data ? gridColor(data.count) : '#999'
    const fontSize = zoom >= 7 ? 11 : zoom >= 5 ? 9 : 0
    if (fontSize === 0) continue
    const icon = L.divIcon({
      className: 'grid-label',
      html: '<div style="font-size:' + fontSize + 'px;color:' + color + ';opacity:0.7;white-space:nowrap;text-align:center;pointer-events:none;font-weight:' + (data ? '600' : '400') + '">' + label + '</div>',
      iconSize: [60, 14], iconAnchor: [30, 7],
    })
    const marker = L.marker(center, { icon, interactive: false }).addTo(overlayGroup)
    gridLabels.push(marker)
  }
}

function drawAllGrids() {
  if (!map) return
  const active = new Map<string, GridData>()
  if (gridData) for (const g of gridData.grids) active.set(g.grid, g)
  const mapBounds = map.getBounds()
  for (const g4 of allGrid4()) {
    const bounds = gridBounds(g4)
    if (!bounds) continue
    // 视口过滤：跳过不在当前视口内的网格
    if (!mapBounds.intersects(bounds)) continue
    const data = active.get(g4)
    const rect = L.rectangle(bounds, {
      color: data ? gridColor(data.count) : '#ccc',
      weight: data ? 1.5 : 0.5,
      fillColor: data ? gridColor(data.count) : 'rgba(100,100,100,0.05)',
      fillOpacity: data ? 0.35 : 0.05,
    })
    if (data) {
      rect.on('click', () => { selectedGrid.value = data })
      rect.bindTooltip(g4 + '<br>QSO: ' + data.count + ' | Confirmed: ' + data.confirmed)
    }
    rect.addTo(overlayGroup)
  }
}

function drawRadials() {
  if (!map || !gridData?.my_lat || !gridData?.my_lon) return
  const from: [number, number] = [gridData.my_lat, gridData.my_lon]
  for (const g of gridData.grids) {
    const center = gridToLatLon(g.grid)
    if (!center) continue
    const confirmed = g.confirmed > 0
    const line = L.polyline([from, center], {
      color: confirmed ? '#22c55e' : '#3b82f6',
      weight: Math.min(1 + g.count * 0.3, 5),
      opacity: 0.7,
      dashArray: confirmed ? undefined : '6 4',
    })
    line.on('click', () => { selectedGrid.value = g })
    line.bindTooltip(g.grid + ' - QSO: ' + g.count)
    line.addTo(overlayGroup)
  }
}

function redraw() {
  if (!map) return
  overlayGroup.clearLayers()
  gridLabels = []
  selectedGrid.value = null
  drawMyStation()
  drawAllGrids()
  drawGridLabels()
  if (displayMode.value === 'radial') drawRadials()
}

function goToLogs() {
  if (selectedGrid.value) router.push({ name: 'Logs', query: { grid: selectedGrid.value.grid } })
}

onMounted(async () => {
  if (!mapContainer.value) return
  map = L.map(mapContainer.value, {
    center: [30, 0], zoom: 3, minZoom: 2, maxZoom: 12,
    maxBounds: [[-90, -180], [90, 180]], maxBoundsViscosity: 1.0, worldCopyJump: false,
    zoomControl: true,
  })
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap', maxZoom: 19,
  }).addTo(map)
  overlayGroup.addTo(map)

  // 添加自定义缩放滑块（左侧，+/- 按钮下方）
  zoomSliderControl = new (ZoomSliderControl as any)({ position: 'topleft' })
  zoomSliderControl.addTo(map)

  map.on('zoomend', () => {
    if (map && zoomSliderControl) {
      zoomSliderControl._update(map.getZoom())
      drawGridLabels()
    }
  })

  try {
    gridData = await mapApi.getGrids()
    myGrid.value = gridData.my_grid
  } catch { gridData = { my_grid: null, my_lat: null, my_lon: null, grids: [] } }
  redraw()
})

onUnmounted(() => {
  // 清理缩放滑块的 document 级事件监听器
  if (zoomSliderControl) {
    const onMouseMove = (zoomSliderControl as any)._onMouseMove
    const onMouseUp = (zoomSliderControl as any)._onMouseUp
    if (onMouseMove) document.removeEventListener('mousemove', onMouseMove)
    if (onMouseUp) document.removeEventListener('mouseup', onMouseUp)
  }
  if (map) { map.remove(); map = null }
})
</script>

<style scoped lang="scss">
.map-page { position: relative; width: 100%; height: calc(100vh - 120px); overflow: hidden; }
.map-container { width: 100%; height: 100%; z-index: 0; }
.map-toolbar {
  position: absolute; top: 16px; right: 16px; z-index: 1000;
  background: rgba(255,255,255,0.92); backdrop-filter: blur(8px);
  border-radius: 10px; padding: 16px; width: 220px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  .toolbar-title { font-size: 15px; font-weight: 700; color: #303133; margin-bottom: 12px; }
  .toolbar-section { margin-bottom: 12px; &:last-child { margin-bottom: 0; } }
  .toolbar-label { font-size: 11px; color: #909399; margin-bottom: 4px; text-transform: uppercase; }
  .toolbar-value { font-size: 18px; font-weight: 700; color: #409eff; font-family: monospace; }
  .toolbar-stat { font-size: 13px; color: #606266; margin-top: 2px; strong { color: #409eff; } }
}
.legend {
  .legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #606266; margin-bottom: 3px; }
  .legend-color { width: 14px; height: 14px; border-radius: 3px; display: inline-block; }
}
:deep(.my-icon) { background: none !important; border: none !important; }
:deep(.grid-label) { background: none !important; border: none !important; }

// 缩放滑块样式（音量条风格）
:deep(.zoom-slider-control) {
  display: flex; flex-direction: column; align-items: center;
  background: white; border-radius: 8px; padding: 8px 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  .zs-track {
    position: relative; width: 8px; height: 160px;
    background: #e4e7ed; border-radius: 4px; cursor: pointer;
  }
  .zs-fill {
    position: absolute; bottom: 0; left: 0; width: 100%;
    background: linear-gradient(to top, #409eff, #79bbff);
    border-radius: 4px; pointer-events: none;
  }
  .zs-thumb {
    position: absolute; left: 50%; transform: translateX(-50%);
    width: 18px; height: 18px; border-radius: 50%;
    background: white; border: 3px solid #409eff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    cursor: grab; z-index: 2; pointer-events: none;
    transition: box-shadow 0.15s;
    &:active { cursor: grabbing; box-shadow: 0 0 0 4px rgba(64,158,255,0.2); }
  }
  .zs-label {
    font-size: 11px; font-weight: 700; color: #409eff;
    margin-top: 6px; font-family: monospace;
  }
}
</style>
