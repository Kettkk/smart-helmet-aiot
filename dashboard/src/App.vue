<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import {
  Activity,
  CheckCircle2,
  CloudCog,
  Database,
  ExternalLink,
  Gauge,
  HeartPulse,
  MapPin,
  Radio,
  RefreshCw,
  ServerCog,
  ShieldCheck,
  Thermometer,
  Wifi,
  Wind,
} from '@lucide/vue'

echarts.use([LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

const devices = ref([])
const selectedDevice = ref('')
const latest = ref(null)
const history = ref([])
const apiHealthy = ref(false)
const loading = ref(true)
const error = ref('')
const lastRefresh = ref(null)
const trendChart = ref(null)
let chart
let pollTimer

function displayNumber(value, digits = 1) {
  return Number.isFinite(value) ? value.toFixed(digits) : '—'
}

function formatTime(value, includeSeconds = true) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    second: includeSeconds ? '2-digit' : undefined,
    hour12: false,
  }).format(new Date(value))
}

const freshnessSeconds = computed(() => {
  if (!latest.value?.timestamp) return null
  return Math.max(0, Math.round((Date.now() - new Date(latest.value.timestamp).getTime()) / 1000))
})

const streamStatus = computed(() => {
  if (!apiHealthy.value) return { label: 'API offline', tone: 'danger' }
  if (freshnessSeconds.value === null) return { label: 'Awaiting telemetry', tone: 'warning' }
  if (freshnessSeconds.value > 10) return { label: 'Telemetry stale', tone: 'warning' }
  return { label: 'Live stream', tone: 'success' }
})

const prototypeAssessment = computed(() => {
  if (!latest.value) return { label: 'No assessment', detail: 'Waiting for the first sample', tone: 'neutral' }
  const heartRateInRange = latest.value.heartRateBpm >= 50 && latest.value.heartRateBpm <= 120
  const temperatureInRange = latest.value.bodyTemperatureC >= 35 && latest.value.bodyTemperatureC <= 38
  if (!latest.value.wearing) return { label: 'Helmet removed', detail: 'Wear state requires attention', tone: 'warning' }
  if (!heartRateInRange || !temperatureInRange) {
    return { label: 'Review signal', detail: 'A prototype threshold was crossed', tone: 'danger' }
  }
  return { label: 'Signals nominal', detail: 'Within prototype display thresholds', tone: 'success' }
})

const metricCards = computed(() => {
  const value = latest.value
  return [
    {
      label: 'Heart rate',
      value: value?.heartRateBpm ?? '—',
      unit: 'BPM',
      detail: value ? 'Prototype range 50–120 BPM' : 'Wearable sensor',
      icon: HeartPulse,
      accent: 'coral',
    },
    {
      label: 'Body temperature',
      value: displayNumber(value?.bodyTemperatureC, 2),
      unit: '°C',
      detail: value?.wearing ? 'Helmet detected' : 'Helmet not worn',
      icon: Thermometer,
      accent: 'amber',
    },
    {
      label: 'Ambient conditions',
      value: displayNumber(value?.ambientTemperatureC),
      unit: '°C',
      detail: value ? `${displayNumber(value.ambientHumidityPct)}% humidity` : 'Humidity unavailable',
      icon: Wind,
      accent: 'cyan',
    },
    {
      label: 'Movement speed',
      value: displayNumber(value?.speedMps, 2),
      unit: 'm/s',
      detail: 'Derived motion signal',
      icon: Gauge,
      accent: 'blue',
    },
  ]
})

const systemStages = computed(() => [
  { label: 'Simulator', detail: latest.value ? 'Publishing' : 'Waiting', icon: Radio, active: Boolean(latest.value) },
  { label: 'MQTT stream', detail: freshnessSeconds.value !== null && freshnessSeconds.value < 10 ? 'Recent sample' : 'No recent sample', icon: Wifi, active: freshnessSeconds.value !== null && freshnessSeconds.value < 10 },
  { label: 'Application API', detail: apiHealthy.value ? 'Healthy' : 'Unavailable', icon: ServerCog, active: apiHealthy.value },
  { label: 'Telemetry store', detail: history.value.length ? `${history.value.length} samples loaded` : 'No records', icon: Database, active: history.value.length > 0 },
])

const mapUrl = computed(() => {
  if (!latest.value) return '#'
  return `https://www.openstreetmap.org/?mlat=${latest.value.latitude}&mlon=${latest.value.longitude}#map=16/${latest.value.latitude}/${latest.value.longitude}`
})

async function fetchJson(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`)
  return response.json()
}

function renderChart() {
  if (!trendChart.value || !history.value.length) return
  if (!chart) chart = echarts.init(trendChart.value, null, { renderer: 'canvas' })
  const records = [...history.value].reverse()
  chart.setOption({
    animationDuration: 500,
    backgroundColor: 'transparent',
    color: ['#ff7b73', '#f4bd61', '#55d7e8'],
    textStyle: { color: '#87a0b5', fontFamily: 'Avenir Next, Segoe UI, sans-serif' },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#102033',
      borderColor: 'rgba(155,185,210,.24)',
      textStyle: { color: '#e8f0f8', fontSize: 11 },
    },
    legend: {
      right: 0,
      top: 0,
      itemWidth: 10,
      itemHeight: 3,
      textStyle: { color: '#87a0b5', fontSize: 10 },
      data: ['Heart rate', 'Body temp.', 'Ambient temp.'],
    },
    grid: { left: 10, right: 12, top: 44, bottom: 8, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: records.map((record) => formatTime(record.timestamp)),
      axisLine: { lineStyle: { color: 'rgba(155,185,210,.16)' } },
      axisTick: { show: false },
      axisLabel: { color: '#688298', fontSize: 9, interval: Math.max(0, Math.floor(records.length / 6)) },
    },
    yAxis: [
      {
        type: 'value',
        name: 'BPM',
        min: (value) => Math.floor(value.min - 4),
        max: (value) => Math.ceil(value.max + 4),
        splitLine: { lineStyle: { color: 'rgba(155,185,210,.08)' } },
        axisLabel: { color: '#688298', fontSize: 9 },
        nameTextStyle: { color: '#688298', fontSize: 9 },
      },
      {
        type: 'value',
        name: '°C',
        splitLine: { show: false },
        axisLabel: { color: '#688298', fontSize: 9 },
        nameTextStyle: { color: '#688298', fontSize: 9 },
      },
    ],
    series: [
      {
        name: 'Heart rate',
        type: 'line',
        smooth: 0.35,
        symbol: 'none',
        lineStyle: { width: 2 },
        areaStyle: { opacity: 0.06 },
        data: records.map((record) => record.heartRateBpm),
      },
      {
        name: 'Body temp.',
        type: 'line',
        yAxisIndex: 1,
        smooth: 0.35,
        symbol: 'none',
        lineStyle: { width: 1.5 },
        data: records.map((record) => record.bodyTemperatureC),
      },
      {
        name: 'Ambient temp.',
        type: 'line',
        yAxisIndex: 1,
        smooth: 0.35,
        symbol: 'none',
        lineStyle: { width: 1.5 },
        data: records.map((record) => record.ambientTemperatureC),
      },
    ],
  }, true)
}

async function refresh() {
  if (loading.value && lastRefresh.value) return
  loading.value = true
  try {
    const [health, deviceList] = await Promise.all([
      fetchJson('/actuator/health'),
      fetchJson('/api/v1/devices'),
    ])
    apiHealthy.value = health.status === 'UP'
    devices.value = deviceList
    if (!selectedDevice.value && deviceList.length) selectedDevice.value = deviceList[0].deviceId
    if (selectedDevice.value) {
      const deviceId = encodeURIComponent(selectedDevice.value)
      const [latestSample, recentSamples] = await Promise.all([
        fetchJson(`/api/v1/devices/${deviceId}/latest`),
        fetchJson(`/api/v1/devices/${deviceId}/telemetry?limit=30`),
      ])
      latest.value = latestSample
      history.value = recentSamples
      await nextTick()
      renderChart()
    }
    error.value = ''
    lastRefresh.value = new Date()
  } catch (requestError) {
    apiHealthy.value = false
    error.value = 'Live services are unavailable. Start the local Compose stack and retry.'
  } finally {
    loading.value = false
  }
}

async function chooseDevice(event) {
  selectedDevice.value = event.target.value
  history.value = []
  await refresh()
}

function resizeChart() {
  chart?.resize()
}

onMounted(() => {
  refresh()
  pollTimer = window.setInterval(refresh, 2000)
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  window.clearInterval(pollTimer)
  window.removeEventListener('resize', resizeChart)
  chart?.dispose()
})
</script>

<template>
  <main class="dashboard-shell">
    <header class="topbar">
      <a class="brand" href="#overview" aria-label="HELM telemetry overview">
        <span class="brand-mark"><Activity :size="20" /></span>
        <span><strong>HELM</strong><small>FIELD TELEMETRY</small></span>
      </a>

      <div class="topbar-actions">
        <label class="device-select">
          <span>Active device</span>
          <select :value="selectedDevice" :disabled="!devices.length" @change="chooseDevice">
            <option v-if="!devices.length" value="">No devices found</option>
            <option v-for="device in devices" :key="device.deviceId" :value="device.deviceId">{{ device.deviceId }}</option>
          </select>
        </label>
        <button class="icon-button" type="button" aria-label="Refresh telemetry" @click="refresh">
          <RefreshCw :size="18" :class="{ spinning: loading }" />
        </button>
      </div>
    </header>

    <section id="overview" class="hero-row">
      <div>
        <p class="eyebrow">SMART HELMET / LIVE OPERATIONS</p>
        <h1>Field telemetry overview</h1>
        <p class="lede">A real-time view of synthetic wearable, environmental, and location signals.</p>
      </div>
      <div class="stream-pill" :class="`is-${streamStatus.tone}`">
        <span class="pulse-dot"></span>
        <div>
          <strong>{{ streamStatus.label }}</strong>
          <small v-if="lastRefresh">Updated {{ lastRefresh.toLocaleTimeString() }}</small>
          <small v-else>Connecting to local services</small>
        </div>
      </div>
    </section>

    <section v-if="error" class="notice" role="alert">
      <CloudCog :size="20" />
      <span>{{ error }}</span>
      <button type="button" @click="refresh">Retry</button>
    </section>

    <section class="metric-grid" aria-label="Latest telemetry">
      <article v-for="metric in metricCards" :key="metric.label" class="metric-card" :class="`accent-${metric.accent}`">
        <div class="metric-icon"><component :is="metric.icon" :size="21" /></div>
        <div class="metric-heading"><span>{{ metric.label }}</span><Radio v-if="latest" :size="14" /></div>
        <div class="metric-value"><strong>{{ metric.value }}</strong><span>{{ metric.unit }}</span></div>
        <p>{{ metric.detail }}</p>
      </article>
    </section>

    <section class="analysis-grid">
      <article class="panel trend-panel">
        <div class="panel-heading">
          <div><p class="eyebrow">LAST 30 SAMPLES</p><h2>Physiology &amp; environment</h2></div>
          <Activity :size="22" />
        </div>
        <div v-if="history.length" ref="trendChart" class="trend-chart" role="img" aria-label="Heart rate and temperature trend chart"></div>
        <div v-else class="empty-state">Waiting for telemetry history</div>
      </article>

      <article class="panel status-panel">
        <div class="panel-heading">
          <div><p class="eyebrow">OBSERVED PATH</p><h2>System integrity</h2></div>
          <ShieldCheck :size="22" />
        </div>
        <div class="stage-list">
          <div v-for="stage in systemStages" :key="stage.label" class="stage-row">
            <span class="stage-icon" :class="{ active: stage.active }"><component :is="stage.icon" :size="16" /></span>
            <div><strong>{{ stage.label }}</strong><small>{{ stage.detail }}</small></div>
            <CheckCircle2 v-if="stage.active" :size="16" class="stage-check" />
          </div>
        </div>
        <div class="assessment" :class="`is-${prototypeAssessment.tone}`">
          <strong>{{ prototypeAssessment.label }}</strong>
          <span>{{ prototypeAssessment.detail }}</span>
        </div>
      </article>
    </section>

    <section class="lower-grid">
      <article class="panel position-panel">
        <div class="panel-heading">
          <div><p class="eyebrow">LAST KNOWN POSITION</p><h2>Location fix</h2></div>
          <MapPin :size="22" />
        </div>
        <div class="coordinates">
          <div><span>LATITUDE</span><strong>{{ displayNumber(latest?.latitude, 6) }}</strong></div>
          <div><span>LONGITUDE</span><strong>{{ displayNumber(latest?.longitude, 6) }}</strong></div>
          <div><span>PRESSURE</span><strong>{{ displayNumber(latest?.impactPressurePa, 2) }} Pa</strong></div>
        </div>
        <a v-if="latest" class="map-link" :href="mapUrl" target="_blank" rel="noreferrer">
          Inspect coordinate <ExternalLink :size="13" />
        </a>
        <p class="position-note">Synthetic coordinates · no personal location data</p>
      </article>

      <article class="panel records-panel">
        <div class="panel-heading records-heading">
          <div><p class="eyebrow">RECENT RECORDS</p><h2>Telemetry log</h2></div>
          <span>{{ history.length }} samples</span>
        </div>
        <div class="table-scroll">
          <table>
            <thead><tr><th>Time</th><th>Heart</th><th>Body</th><th>Ambient</th><th>Humidity</th><th>Speed</th></tr></thead>
            <tbody>
              <tr v-for="record in history.slice(0, 8)" :key="record.timestamp">
                <td>{{ formatTime(record.timestamp) }}</td>
                <td>{{ record.heartRateBpm }} BPM</td>
                <td>{{ displayNumber(record.bodyTemperatureC, 2) }}°</td>
                <td>{{ displayNumber(record.ambientTemperatureC) }}°</td>
                <td>{{ displayNumber(record.ambientHumidityPct) }}%</td>
                <td>{{ displayNumber(record.speedMps, 2) }} m/s</td>
              </tr>
              <tr v-if="!history.length"><td colspan="6" class="table-empty">No samples available</td></tr>
            </tbody>
          </table>
        </div>
      </article>
    </section>

    <footer>
      <span>SMART HELMET AIoT / LOCAL RESEARCH PROTOTYPE</span>
      <span>Not a certified medical or safety device</span>
    </footer>
  </main>
</template>
