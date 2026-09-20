<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import {
  CheckCircle2,
  CloudCog,
  Database,
  ExternalLink,
  Radio,
  RefreshCw,
  ServerCog,
  Wifi,
} from '@lucide/vue'
import visionResults from './vision-results.json'

echarts.use([BarChart, LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

const devices = ref([])
const selectedDevice = ref('')
const latest = ref(null)
const history = ref([])
const apiHealthy = ref(false)
const loading = ref(true)
const error = ref('')
const lastRefresh = ref(null)
const trendChart = ref(null)
const visionChart = ref(null)
let chart
let benchmarkChart
let pollTimer

function displayNumber(value, digits = 1) {
  return Number.isFinite(value) ? value.toFixed(digits) : '--'
}

function formatTime(value) {
  if (!value) return '--'
  return new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
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
      value: value?.heartRateBpm ?? '--',
      unit: 'BPM',
      detail: value ? 'Prototype range 50-120 BPM' : 'Wearable sensor',
    },
    {
      label: 'Body temperature',
      value: displayNumber(value?.bodyTemperatureC, 2),
      unit: '°C',
      detail: value?.wearing ? 'Helmet detected' : 'Helmet not worn',
    },
    {
      label: 'Ambient conditions',
      value: displayNumber(value?.ambientTemperatureC),
      unit: '°C',
      detail: value ? `${displayNumber(value.ambientHumidityPct)}% humidity` : 'Humidity unavailable',
    },
    {
      label: 'Movement speed',
      value: displayNumber(value?.speedMps, 2),
      unit: 'm/s',
      detail: 'Derived motion signal',
    },
  ]
})

const systemStages = computed(() => [
  { label: 'Simulator', detail: latest.value ? 'Publishing' : 'Waiting', icon: Radio, active: Boolean(latest.value) },
  {
    label: 'MQTT stream',
    detail: freshnessSeconds.value !== null && freshnessSeconds.value < 10 ? 'Recent sample' : 'No recent sample',
    icon: Wifi,
    active: freshnessSeconds.value !== null && freshnessSeconds.value < 10,
  },
  { label: 'Application API', detail: apiHealthy.value ? 'Healthy' : 'Unavailable', icon: ServerCog, active: apiHealthy.value },
  {
    label: 'Telemetry store',
    detail: history.value.length ? `${history.value.length} samples loaded` : 'No records',
    icon: Database,
    active: history.value.length > 0,
  },
])

const mapUrl = computed(() => {
  if (!latest.value) return '#'
  return `https://www.openstreetmap.org/?mlat=${latest.value.latitude}&mlon=${latest.value.longitude}#map=16/${latest.value.latitude}/${latest.value.longitude}`
})

const visionRuns = computed(() => [...visionResults.runs].sort((a, b) => b.samplingFps - a.samplingFps))
const operatingPoint = computed(() => visionResults.runs.find(
  (run) => run.frameStride === visionResults.operatingPointStride,
))

function renderVisionChart() {
  if (!visionChart.value) return
  if (!benchmarkChart) benchmarkChart = echarts.init(visionChart.value, null, { renderer: 'canvas' })
  const rows = [...visionResults.runs].sort((a, b) => a.samplingFps - b.samplingFps)
  const styles = getComputedStyle(document.documentElement)
  const textMuted = styles.getPropertyValue('--text-muted').trim()
  const textPrimary = styles.getPropertyValue('--text-primary').trim()
  const borderColor = styles.getPropertyValue('--border').trim()
  const surface = styles.getPropertyValue('--surface').trim()
  const accent = styles.getPropertyValue('--accent').trim()

  benchmarkChart.setOption({
    animationDuration: 220,
    backgroundColor: 'transparent',
    textStyle: { color: textMuted, fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif' },
    tooltip: {
      trigger: 'axis',
      backgroundColor: surface,
      borderColor,
      extraCssText: 'box-shadow: none; border-radius: 6px;',
      textStyle: { color: textPrimary, fontSize: 11 },
      formatter: (items) => {
        const row = rows[items[0].dataIndex]
        return `<strong>${row.samplingFps} sampled FPS</strong><br/>Pipeline: ${row.pipelineFps.toFixed(1)} FPS<br/>Mean inference: ${row.meanLatencyMs.toFixed(1)} ms<br/>p95: ${row.p95LatencyMs.toFixed(1)} ms`
      },
    },
    grid: { left: 8, right: 10, top: 14, bottom: 8, containLabel: true },
    xAxis: {
      type: 'category',
      name: 'Sampled FPS',
      nameLocation: 'middle',
      nameGap: 28,
      data: rows.map((row) => row.samplingFps),
      axisLine: { lineStyle: { color: borderColor } },
      axisTick: { show: false },
      axisLabel: { color: textMuted, fontSize: 9 },
      nameTextStyle: { color: textMuted, fontSize: 9 },
    },
    yAxis: {
      type: 'value',
      name: 'Pipeline FPS',
      splitLine: { lineStyle: { color: borderColor } },
      axisLabel: { color: textMuted, fontSize: 9 },
      nameTextStyle: { color: textMuted, fontSize: 9 },
    },
    series: [{
      name: 'Pipeline FPS',
      type: 'bar',
      barMaxWidth: 44,
      itemStyle: { color: accent, borderRadius: [3, 3, 0, 0] },
      data: rows.map((row) => row.pipelineFps),
    }],
  }, true)
}

async function fetchJson(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`)
  return response.json()
}

function renderChart() {
  if (!trendChart.value || !history.value.length) return
  if (!chart) chart = echarts.init(trendChart.value, null, { renderer: 'canvas' })
  const records = [...history.value].reverse()
  const styles = getComputedStyle(document.documentElement)
  const chartColors = [
    styles.getPropertyValue('--accent').trim(),
    styles.getPropertyValue('--chart-secondary').trim(),
    styles.getPropertyValue('--chart-tertiary').trim(),
  ]
  const textMuted = styles.getPropertyValue('--text-muted').trim()
  const textPrimary = styles.getPropertyValue('--text-primary').trim()
  const borderColor = styles.getPropertyValue('--border').trim()
  const surface = styles.getPropertyValue('--surface').trim()
  chart.setOption({
    animationDuration: 220,
    backgroundColor: 'transparent',
    color: chartColors,
    textStyle: { color: textMuted, fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif' },
    tooltip: {
      trigger: 'axis',
      backgroundColor: surface,
      borderColor,
      extraCssText: 'box-shadow: none; border-radius: 6px;',
      textStyle: { color: textPrimary, fontSize: 11 },
    },
    legend: {
      right: 0,
      top: 0,
      itemWidth: 10,
      itemHeight: 3,
      textStyle: { color: textMuted, fontSize: 10 },
      data: ['Heart rate', 'Body temp.', 'Ambient temp.'],
    },
    grid: { left: 10, right: 12, top: 44, bottom: 8, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: records.map((record) => formatTime(record.timestamp)),
      axisLine: { lineStyle: { color: borderColor } },
      axisTick: { show: false },
      axisLabel: { color: textMuted, fontSize: 9, interval: Math.max(0, Math.floor(records.length / 6)) },
    },
    yAxis: [
      {
        type: 'value',
        name: 'BPM',
        min: (value) => Math.floor(value.min - 4),
        max: (value) => Math.ceil(value.max + 4),
        splitLine: { lineStyle: { color: borderColor } },
        axisLabel: { color: textMuted, fontSize: 9 },
        nameTextStyle: { color: textMuted, fontSize: 9 },
      },
      {
        type: 'value',
        name: '°C',
        splitLine: { show: false },
        axisLabel: { color: textMuted, fontSize: 9 },
        nameTextStyle: { color: textMuted, fontSize: 9 },
      },
    ],
    series: [
      {
        name: 'Heart rate',
        type: 'line',
        smooth: 0.2,
        symbol: 'none',
        lineStyle: { width: 2 },
        data: records.map((record) => record.heartRateBpm),
      },
      {
        name: 'Body temp.',
        type: 'line',
        yAxisIndex: 1,
        smooth: 0.2,
        symbol: 'none',
        lineStyle: { width: 1.5 },
        data: records.map((record) => record.bodyTemperatureC),
      },
      {
        name: 'Ambient temp.',
        type: 'line',
        yAxisIndex: 1,
        smooth: 0.2,
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
  } catch {
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
  benchmarkChart?.resize()
}

onMounted(async () => {
  await nextTick()
  renderVisionChart()
  refresh()
  pollTimer = window.setInterval(refresh, 2000)
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  window.clearInterval(pollTimer)
  window.removeEventListener('resize', resizeChart)
  chart?.dispose()
  benchmarkChart?.dispose()
})
</script>

<template>
  <main class="dashboard-shell">
    <header class="topbar">
      <a class="brand" href="#overview" aria-label="HELM telemetry overview">
        <span class="brand-mark" aria-hidden="true">H</span>
        <span><strong>HELM</strong><small>Research telemetry</small></span>
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

    <section id="overview" class="page-heading">
      <div>
        <h1>Telemetry overview</h1>
        <p class="lede">Live wearable, environmental, and location signals from the local research prototype.</p>
      </div>
      <div class="stream-state" :class="`is-${streamStatus.tone}`">
        <span class="status-dot" aria-hidden="true"></span>
        <div>
          <strong>{{ streamStatus.label }}</strong>
          <small v-if="lastRefresh">Updated at {{ lastRefresh.toLocaleTimeString() }}</small>
          <small v-else>Connecting to local services</small>
        </div>
      </div>
    </section>

    <section v-if="error" class="notice" role="alert">
      <CloudCog :size="20" />
      <span>{{ error }}</span>
      <button type="button" @click="refresh">Retry</button>
    </section>

    <section class="metric-grid" aria-label="Latest telemetry readings">
      <article v-for="metric in metricCards" :key="metric.label" class="metric-item">
        <div class="metric-heading">{{ metric.label }}</div>
        <div v-if="loading && !latest" class="metric-skeleton" aria-label="Loading reading"></div>
        <div v-else class="metric-value"><strong>{{ metric.value }}</strong><span>{{ metric.unit }}</span></div>
        <p>{{ metric.detail }}</p>
      </article>
    </section>

    <section class="workspace-grid">
      <article class="panel trend-panel">
        <div class="panel-heading">
          <div><h2>Signal trends</h2><p>Last 30 samples</p></div>
        </div>
        <div v-if="history.length" ref="trendChart" class="trend-chart" role="img" aria-label="Heart rate and temperature trend chart"></div>
        <div v-else-if="loading" class="chart-skeleton" aria-label="Loading chart"></div>
        <div v-else class="empty-state">No telemetry history is available for this device.</div>
      </article>

      <article class="panel status-panel">
        <div class="panel-heading">
          <div><h2>System path</h2><p>Observed local data flow</p></div>
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

    <section class="detail-grid">
      <article class="panel records-panel">
        <div class="panel-heading records-heading">
          <div><h2>Telemetry log</h2><p>Most recent readings</p></div>
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

      <article class="panel position-panel">
        <div class="panel-heading">
          <div><h2>Location fix</h2><p>Last reported position</p></div>
        </div>
        <dl class="coordinates">
          <div><dt>Latitude</dt><dd>{{ displayNumber(latest?.latitude, 6) }}</dd></div>
          <div><dt>Longitude</dt><dd>{{ displayNumber(latest?.longitude, 6) }}</dd></div>
          <div><dt>Impact pressure</dt><dd>{{ displayNumber(latest?.impactPressurePa, 2) }} Pa</dd></div>
        </dl>
        <a v-if="latest" class="map-link" :href="mapUrl" target="_blank" rel="noreferrer">
          Open coordinate <ExternalLink :size="13" />
        </a>
        <p class="position-note">Synthetic coordinates. No personal location data.</p>
      </article>
    </section>

    <section class="panel vision-panel" aria-labelledby="vision-heading">
      <div class="panel-heading vision-heading">
        <div>
          <div class="eyebrow-row">
            <span class="status-dot" aria-hidden="true"></span>
            <span>Measured benchmark</span>
          </div>
          <h2 id="vision-heading">Vision frame-sampling study</h2>
          <p>YOLO inference on a fixed 20-second hiking clip in a CPU-only Docker environment.</p>
        </div>
        <a class="map-link" href="https://github.com/Kettkk/smart-helmet-aiot/blob/main/docs/vision-demo.md" target="_blank" rel="noreferrer">
          Method and raw results <ExternalLink :size="13" />
        </a>
      </div>

      <div class="vision-summary" aria-label="Selected vision operating point">
        <div><span>Operating point</span><strong>Stride {{ operatingPoint.frameStride }}</strong></div>
        <div><span>Sampling rate</span><strong>{{ operatingPoint.samplingFps.toFixed(1) }} FPS</strong></div>
        <div><span>Mean inference</span><strong>{{ operatingPoint.meanLatencyMs.toFixed(1) }} ms</strong></div>
        <div><span>p95 inference</span><strong>{{ operatingPoint.p95LatencyMs.toFixed(1) }} ms</strong></div>
        <div><span>Pipeline throughput</span><strong>{{ operatingPoint.pipelineFps.toFixed(1) }} FPS</strong></div>
      </div>

      <div class="vision-content">
        <div>
          <div ref="visionChart" class="vision-chart" role="img" aria-label="Pipeline throughput by effective sampling rate"></div>
          <p class="chart-note">Lower sampling frequency reduces total work; inference latency per processed frame remains near 106–109 ms.</p>
        </div>
        <div class="table-scroll vision-table-scroll">
          <table class="vision-table">
            <thead><tr><th>Stride</th><th>Sampled FPS</th><th>Frames</th><th>Mean</th><th>p95</th><th>Pipeline</th></tr></thead>
            <tbody>
              <tr v-for="run in visionRuns" :key="run.frameStride" :class="{ 'is-operating-point': run.frameStride === visionResults.operatingPointStride }">
                <td>{{ run.frameStride }}<span v-if="run.frameStride === visionResults.operatingPointStride" class="table-badge">Selected</span></td>
                <td>{{ run.samplingFps.toFixed(1) }}</td>
                <td>{{ run.processedFrames }}</td>
                <td>{{ run.meanLatencyMs.toFixed(1) }} ms</td>
                <td>{{ run.p95LatencyMs.toFixed(1) }} ms</td>
                <td>{{ run.pipelineFps.toFixed(1) }} FPS</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="benchmark-meta">
        <span>{{ visionResults.configuration.model }}</span>
        <span>{{ visionResults.configuration.device }}</span>
        <span>{{ visionResults.configuration.imageSize }} px input</span>
        <span>Confidence {{ visionResults.configuration.confidence }}</span>
        <span>{{ visionResults.input.resolution }} source</span>
      </div>
    </section>

    <footer>
      <span>Smart Helmet AIoT local research prototype</span>
      <span>Not a certified medical or safety device</span>
    </footer>
  </main>
</template>
