<template>
  <div class="bi-viewport" :class="{ 'is-maximized': isMaximized }">
    <!-- 背景流光特效 -->
    <div class="space-ambient">
      <div class="nebula blue"></div>
      <div class="nebula gold"></div>
      <div class="scan-grid"></div>
    </div>

    <el-button
      v-show="isMaximized"
      type="primary"
      size="small"
      class="restore-fab"
      @click="toggleMaximize"
    >
      还原
    </el-button>

    <div class="layout-wrapper">
      <!-- Header Section -->
      <header class="page-header entrance-slide-in">
        <div class="title-area">
          <h1 class="ios-title">PROGRAM CYCLE SYNC<span class="subtitle">程序周期同步视窗</span></h1>
        </div>
        <div class="header-actions">
          <el-button type="primary" size="small" class="maximize-btn" @click="toggleMaximize">
            {{ isMaximized ? '还原' : '放大' }}
          </el-button>
        </div>
      </header>

      <!-- Control Panel -->
      <div class="control-panel ios-glass entrance-scale-up">
        <div class="border-glow"></div>
        <div class="cell-header">
          <span class="accent-bar"></span>
          分析配置中心 (ANALYSIS CONFIGURATION)
        </div>
        <div class="control-content">
          <div class="control-row">
            <!-- 机器人搜索 -->
            <div class="control-item compact-item entrance-fade-right-1">
              <label><el-icon><Monitor /></el-icon> 机器人</label>
              <el-input
                v-model="robotQuery"
                placeholder="请输入机器人表名（PROGRAM CYCLE SYNC）"
                clearable
                :disabled="robotsLoading"
                :readonly="isLoading"
                @clear="handleRobotClear"
                @keyup.enter="handleRobotSearch"
                class="styled-select"
              />
            </div>

            <!-- 时间范围选择器 -->
            <div class="control-item compact-item time-range-control entrance-fade-right-2">
              <label><el-icon><Calendar /></el-icon> 时间范围</label>
              <el-date-picker
                v-model="timeRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                :shortcuts="shortcuts"
                :default-time="defaultTime"
                unlink-panels
                popper-class="trajectory-date-picker"
                @change="handleTimeRangeChange"
                class="styled-date-picker"
              />
            </div>

            <!-- 加载分析按钮 -->
            <el-button
              type="primary"
              class="action-btn btn-entrance-2 load-analysis-btn"
              :class="{ 'is-cancel': isLoading && isLoadHover }"
              :disabled="(!activeName && !robotQuery.trim()) && !isLoading"
              @mouseenter="handleLoadHover(true)"
              @mouseleave="handleLoadHover(false)"
              @click="handleLoadOrCancel"
            >
              <el-icon v-if="!isLoading"><Search /></el-icon>
              {{ isLoading ? (isLoadHover ? '取消' : '加载中...') : '加载分析' }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- Content Area -->
      <div class="bi-content entrance-delayed-fade">
        <div v-if="!shouldLoad" class="bi-empty-state ios-glass">
          <div class="empty-icon"><el-icon><PieChart /></el-icon></div>
          <div class="empty-text">请输入机器人表名后点击"加载分析"按钮</div>
        </div>

        <!-- BI图表容器 -->
        <div v-else class="bi-card ios-glass">
          <div class="border-glow"></div>
          <div class="bi-frame-wrapper">
            <iframe
              v-if="shouldLoad && primaryFrameUrl"
              ref="primaryFrame"
              class="bi-frame"
              :class="{ 'is-active': showPrimaryFrame }"
              :src="primaryFrameUrl"
              title="程序周期同步视窗"
              @load="handleFrameLoad('primary')"
            ></iframe>
            <iframe
              v-if="shouldLoad && secondaryFrameUrl"
              ref="secondaryFrame"
              class="bi-frame"
              :class="{ 'is-active': !showPrimaryFrame }"
              :src="secondaryFrameUrl"
              title="程序周期同步视窗"
              @load="handleFrameLoad('secondary')"
            ></iframe>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onActivated, onDeactivated, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Monitor, Search, PieChart, Calendar } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { API_BASE_URL } from '@/config/appConfig'

defineOptions({ name: 'Alerts' })

const route = useRoute()
const router = useRouter()

const robotQuery = ref('')
const activeName = ref('')
const currentRobotLabel = ref('')
const selectedProgram = ref('')
const selectedAxis = ref('')
const reloadToken = ref(0)
const shouldLoad = ref(false)  // 控制是否加载 iframe
const primaryFrameUrl = ref('')
const secondaryFrameUrl = ref('')
const showPrimaryFrame = ref(true)
const loadingTarget = ref(null) // 'primary' | 'secondary' | null
const loadingMode = ref('full') // 'full' | 'switch'

const robotsLoading = ref(false)
const isLoading = ref(false)
const isLoadHover = ref(false)
const primaryFrame = ref(null)
const secondaryFrame = ref(null)
const loadingJobId = ref('')
const biLogs = ref([])
const logPollingTimer = ref(null)
const logRotateTimer = ref(null)
const currentLogIndex = ref(0)
const lastStableFrameUrl = ref('')
const initInProgress = ref(false)
const lastInitSignature = ref('')
const isMaximized = ref(false)
const isActiveRoute = computed(() => route.path === '/alerts')

const LOG_LIMIT = 8
const LOG_POLL_INTERVAL = 30000
const LOG_ROTATE_INTERVAL = 1600
const LOG_LOAD_POLL_INTERVAL = 2000  // 加载时使用更短的轮询间隔

// 时间范围选择器状态（数组格式：[开始日期, 结束日期]）
const DEFAULT_TIME_SPAN_DAYS = 30
const toDayStart = (date) => {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  return d
}
const toDayEnd = (date) => {
  const d = new Date(date)
  d.setHours(23, 59, 59, 999)
  return d
}
const normalizeRangeToDayBounds = (range) => {
  if (!range || range.length !== 2 || !range[0] || !range[1]) return range
  return [toDayStart(range[0]), toDayEnd(range[1])]
}
const timeRange = ref(
  normalizeRangeToDayBounds([
    new Date(Date.now() - DEFAULT_TIME_SPAN_DAYS * 24 * 3600_000),
    new Date()
  ])
)

const defaultTime = [
  new Date(2000, 1, 1, 0, 0, 0),
  new Date(2000, 1, 1, 23, 59, 59)
]

// 快捷选项
const shortcuts = [
  {
    text: '最近一周',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return normalizeRangeToDayBounds([start, end])
    }
  },
  {
    text: '最近一个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
      return normalizeRangeToDayBounds([start, end])
    }
  },
  {
    text: '最近三个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 90)
      return normalizeRangeToDayBounds([start, end])
    }
  }
]

const formatDateParam = (date) => {
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const generateJobId = () => {
  try {
    const randomUUID = globalThis?.crypto?.randomUUID
    if (typeof randomUUID === 'function') return randomUUID()
  } catch {
    // ignore
  }
  return `${Date.now()}_${Math.random().toString(16).slice(2)}`
}

const toAbsoluteUrl = (raw) => {
  try {
    return new URL(raw, globalThis?.location?.origin || 'http://localhost')
  } catch {
    return null
  }
}

const stripBiJobId = (raw) => {
  const u = toAbsoluteUrl(raw)
  if (!u) return raw
  u.searchParams.delete('job_id')
  return u.toString()
}

const withBiJobId = (raw, jobId) => {
  const id = (jobId || '').trim()
  if (!id) return raw
  const u = toAbsoluteUrl(raw)
  if (!u) return raw
  if (!u.pathname.includes('/api/robots/bi/')) return raw
  u.searchParams.set('job_id', id)
  return u.toString()
}

const cancelBiJob = async (jobId) => {
  const id = (jobId || '').trim()
  if (!id) return
  try {
    await request.get('/robots/bi_cancel/', { params: { job_id: id }, silent: true })
  } catch {
    // ignore
  }
}

const syncRouteQuery = (patch) => {
  const next = { ...route.query, ...(patch || {}) }
  for (const key of Object.keys(next)) {
    if (next[key] === '' || next[key] == null) delete next[key]
  }
  router.replace({ query: next })
}

const biUrl = computed(() => {
  const name = activeName.value.trim()
  const tableName = name || ''
  const baseUrl = tableName ? `/api/robots/bi/?table=${encodeURIComponent(tableName)}&embed=1` : ''
  if (!baseUrl) return ''
  const url = new URL(baseUrl, API_BASE_URL)
  if (reloadToken.value) {
    url.searchParams.set('_t', String(reloadToken.value))
  }
  // 添加时间范围参数（从timeRange数组格式转换）
  if (timeRange.value && timeRange.value.length === 2) {
    url.searchParams.set('start_date', formatDateParam(timeRange.value[0]))
    url.searchParams.set('end_date', formatDateParam(timeRange.value[1]))
  }
  // 返回完整的URL，确保iframe正确加载
  return url.toString()
})

const visibleFrameUrl = computed(() => (showPrimaryFrame.value ? primaryFrameUrl.value : secondaryFrameUrl.value))

const getActiveFrameWindow = () => {
  const frameEl = showPrimaryFrame.value ? primaryFrame.value : secondaryFrame.value
  return frameEl?.contentWindow || null
}

const biStateStorageKey = computed(() => {
  const robot = activeName.value?.trim() || ''
  return robot ? `alerts:biState:${robot.toLowerCase()}` : 'alerts:biState:last'
})

const readStoredBiState = () => {
  try {
    const raw = sessionStorage.getItem(biStateStorageKey.value)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    const program = typeof parsed?.program === 'string' ? parsed.program.trim() : ''
    const axis = typeof parsed?.axis === 'string' ? parsed.axis.trim() : ''
    return { program, axis }
  } catch {
    return null
  }
}

const writeStoredBiState = (program, axis) => {
  try {
    sessionStorage.setItem(
      biStateStorageKey.value,
      JSON.stringify({ program: program || '', axis: axis || '' })
    )
  } catch {
    // ignore
  }
}

const syncIframeState = () => {
  const win = getActiveFrameWindow()
  if (!win) return
  win.postMessage(
    {
      type: 'setBIState',
      program: selectedProgram.value || '',
      axis: selectedAxis.value || ''
    },
    '*'
  )
}

const requestIframeState = () => {
  const win = getActiveFrameWindow()
  if (!win) return
  win.postMessage({ type: 'getBIState' }, '*')
}

const loadFrame = (url, options = {}) => {
  const nextUrl = typeof url === 'string' ? url.trim() : ''
  if (!nextUrl) return
  if (stripBiJobId(nextUrl) === stripBiJobId(visibleFrameUrl.value)) return

  const jobId = generateJobId()
  loadingJobId.value = jobId
  const nextUrlWithJob = withBiJobId(nextUrl, jobId)

  const target = showPrimaryFrame.value ? 'secondary' : 'primary'
  loadingTarget.value = target
  loadingMode.value = options?.mode === 'switch' ? 'switch' : 'full'

  if (visibleFrameUrl.value) {
    lastStableFrameUrl.value = visibleFrameUrl.value
  }

  if (target === 'primary') {
    primaryFrameUrl.value = nextUrlWithJob
  } else {
    secondaryFrameUrl.value = nextUrlWithJob
  }

  startLoading()
}

const handleRobotSearch = async () => {
  const query = robotQuery.value.trim()
  if (!query) {
    ElMessage.warning('请输入机器人表名')
    return
  }

  robotsLoading.value = true
  try {
    const response = await request.get('/robots/components/bi_robots/', {
      params: { keyword: query },
      silent: true
    })
    const result = response?.results?.[0]
    if (!result?.value) {
      throw new Error('EMPTY_RESULT')
    }

    activeName.value = String(result.value).trim()
    currentRobotLabel.value = String(result.label || result.value).trim()
  } catch (error) {
    activeName.value = ''
    currentRobotLabel.value = ''
    const detail = error?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' && detail.trim() ? detail : 'PROGRAM CYCLE SYNC 数据库中未找到该机器人表名')
  } finally {
    robotsLoading.value = false
  }
}

const toggleMaximize = () => {
  isMaximized.value = !isMaximized.value
}

const handleKeyDown = (e) => {
  if (e?.key === 'Escape' && isMaximized.value) {
    isMaximized.value = false
  }
}

// 开始加载动画
const startLoading = () => {
  isLoading.value = true
  isLoadHover.value = false
}

// iframe加载完成（双缓冲：先加载隐藏iframe，加载完再切换显示）
const handleFrameLoad = (slot) => {
  if (!loadingTarget.value) return
  if (slot !== loadingTarget.value) return

  if (slot === 'primary') {
    showPrimaryFrame.value = true
    lastStableFrameUrl.value = primaryFrameUrl.value
  } else if (slot === 'secondary') {
    showPrimaryFrame.value = false
    lastStableFrameUrl.value = secondaryFrameUrl.value
  }

  loadingTarget.value = null
  // 延迟一点关闭加载动画，确保内容已渲染
  setTimeout(() => {
    isLoading.value = false
    isLoadHover.value = false
    loadingJobId.value = ''
    // 停止日志轮询
    stopLogPolling()
    syncIframeState()
    requestIframeState()
  }, 500)
}

const handleLoad = () => {
  if (!activeName.value) {
    const manual = robotQuery.value.trim()
    if (!manual) return
    activeName.value = manual
    currentRobotLabel.value = manual
  }
  shouldLoad.value = true  // 设置为 true，触发 iframe 加载
  reloadToken.value = Date.now()
  if (timeRange.value && timeRange.value.length === 2) {
    syncRouteQuery({
      robot: activeName.value,
      start_date: formatDateParam(timeRange.value[0]),
      end_date: formatDateParam(timeRange.value[1]),
      program: selectedProgram.value || '',
      axis: selectedAxis.value || '',
    })
  } else {
    syncRouteQuery({
      robot: activeName.value,
      program: selectedProgram.value || '',
      axis: selectedAxis.value || '',
    })
  }
  // 启动日志轮询以追踪加载状态
  startLogPolling()
  loadFrame(biUrl.value, { mode: 'full' })
}

const handleLoadHover = (val) => {
  if (!isLoading.value) return
  isLoadHover.value = val
}

const handleCancel = async () => {
  const jobId = loadingJobId.value
  isLoading.value = false
  isLoadHover.value = false
  loadingMode.value = 'full'
  loadingJobId.value = ''
  cancelBiJob(jobId)
  // 停止日志轮询
  stopLogPolling()
  if (loadingTarget.value === 'primary') {
    primaryFrameUrl.value = ''
  } else if (loadingTarget.value === 'secondary') {
    secondaryFrameUrl.value = ''
  }
  loadingTarget.value = null
  if (!primaryFrameUrl.value && !secondaryFrameUrl.value) {
    shouldLoad.value = false
  }
}

const handleLoadOrCancel = async () => {
  if (isLoading.value) {
    await handleCancel()
    return
  }
  handleLoad()
}

const handleRobotClear = async () => {
  if (isLoading.value) {
    await handleCancel()
  }
  // 清空展示态，避免继续看到旧图
  activeName.value = ''
  currentRobotLabel.value = ''
  selectedProgram.value = ''
  selectedAxis.value = ''
  primaryFrameUrl.value = ''
  secondaryFrameUrl.value = ''
  shouldLoad.value = false
  syncRouteQuery({ robot: '', program: '', axis: '', start_date: '', end_date: '' })
}

// 时间范围变化处理
const handleTimeRangeChange = (range) => {
  if (range && range.length === 2) {
    timeRange.value = normalizeRangeToDayBounds(range)
  }
  // 不再自动加载，时间范围变化后需要手动点击"加载分析"按钮
}

// 初始化：检查URL参数
const initFromQuery = async () => {
  const queryRobot = route.query.robot
  const queryStartDate = route.query.start_date
  const queryEndDate = route.query.end_date
  const queryProgram = route.query.program
  const queryAxis = route.query.axis

  const normalizedQueryRobot = typeof queryRobot === 'string' ? queryRobot.trim() : ''

  if (!normalizedQueryRobot) return false

  robotQuery.value = normalizedQueryRobot
  await handleRobotSearch()
  if (!activeName.value) return false

  // 如果有时间范围参数，设置时间范围；无则沿用默认 timeRange
  if (queryStartDate && queryEndDate) {
    timeRange.value = normalizeRangeToDayBounds([new Date(queryStartDate), new Date(queryEndDate)])
  }
  selectedProgram.value = typeof queryProgram === 'string' ? queryProgram.trim() : ''
  selectedAxis.value = typeof queryAxis === 'string' ? queryAxis.trim() : ''

  // 只要带了 robot，就自动加载 BI
  shouldLoad.value = true
  loadFrame(biUrl.value, { mode: 'full' })

  return true
}

const runInitFromQuery = async () => {
  const robot = typeof route.query.robot === 'string' ? route.query.robot.trim() : ''
  if (!robot) return
  const signature = JSON.stringify({
    robot,
    start_date: route.query.start_date || '',
    end_date: route.query.end_date || '',
    program: route.query.program || '',
    axis: route.query.axis || ''
  })
  if (initInProgress.value || signature === lastInitSignature.value) return
  initInProgress.value = true
  lastInitSignature.value = signature
  try {
    await initFromQuery()
  } finally {
    initInProgress.value = false
  }
}

const handleBiMessage = (event) => {
  if (!event?.data || typeof event.data !== 'object') return
  if (event.data.type === 'updateBIUrl' && typeof event.data.url === 'string') {
    // 兼容旧逻辑：更新iframe的src来重新加载图表
    loadFrame(event.data.url, { mode: 'switch' })
    return
  }
  if (event.data.type === 'biState') {
    const program = typeof event.data.program === 'string' ? event.data.program.trim() : ''
    const axis = typeof event.data.axis === 'string' ? event.data.axis.trim() : ''
    selectedProgram.value = program
    selectedAxis.value = axis
    writeStoredBiState(program, axis)
    syncRouteQuery({ program, axis })
  }
}

const enterView = async () => {
  if (!isActiveRoute.value) return
  await runInitFromQuery()
  // route.query 可能为空（侧边栏返回 /alerts 不带 query），优先用 sessionStorage 还原 program/axis
  if (!selectedProgram.value && !selectedAxis.value) {
    const stored = readStoredBiState()
    if (stored) {
      selectedProgram.value = stored.program
      selectedAxis.value = stored.axis
    }
  }
  // keep-alive 场景：切走再回来时 iframe 可能仍在加载；恢复加载态的日志轮询/轮播
  if (isLoading.value && loadingMode.value === 'full') {
    startLogPolling()
    startLogRotation()
  }
  syncIframeState()
  requestIframeState()
}

const leaveView = () => {
  stopLogPolling()
  stopLogRotation()
  isLoadHover.value = false
}

onMounted(async () => {
  // 监听来自iframe的postMessage（用于日期范围更新）
  window.addEventListener('message', handleBiMessage)
  window.addEventListener('keydown', handleKeyDown)
})

onActivated(async () => {
  await enterView()
})

onDeactivated(() => {
  leaveView()
})

onUnmounted(() => {
  stopLogPolling()
  stopLogRotation()
  window.removeEventListener('message', handleBiMessage)
  window.removeEventListener('keydown', handleKeyDown)
})

watch(
  () => route.path,
  async (path, prevPath) => {
    if (path === prevPath) return
    if (path === '/alerts') {
      await enterView()
    } else if (prevPath === '/alerts') {
      leaveView()
    }
  }
)

// 组件在同一路由下会复用（仅 query 变化不会触发 onMounted）
watch(
  () => route.query.robot,
  async (robot, prevRobot) => {
    if (!robot || robot === prevRobot) return
    await runInitFromQuery()
  }
)

const fetchBiLogs = async () => {
  try {
    const response = await request.get('/robots/bi_logs/', {
      params: { limit: LOG_LIMIT }
    })
    biLogs.value = response?.lines || []
  } catch (error) {
    console.error('加载后端日志失败:', error)
  }
}

const startLogPolling = () => {
  fetchBiLogs()
  if (logPollingTimer.value) return
  // 根据加载状态使用不同的轮询间隔
  const interval = isLoading.value ? LOG_LOAD_POLL_INTERVAL : LOG_POLL_INTERVAL
  logPollingTimer.value = setInterval(fetchBiLogs, interval)
}

const stopLogPolling = () => {
  if (!logPollingTimer.value) return
  clearInterval(logPollingTimer.value)
  logPollingTimer.value = null
}

const startLogRotation = () => {
  if (logRotateTimer.value) return
  logRotateTimer.value = setInterval(() => {
    if (!displayLogs.value.length) return
    currentLogIndex.value = (currentLogIndex.value + 1) % displayLogs.value.length
  }, LOG_ROTATE_INTERVAL)
}

const stopLogRotation = () => {
  if (!logRotateTimer.value) return
  clearInterval(logRotateTimer.value)
  logRotateTimer.value = null
}

const displayLogs = computed(() => {
  const stripPrefix = (line) =>
    line.replace(/^INFO\\s+\\d{4}-\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}:\\d{2},\\d+\\s+/, '')
  return biLogs.value.map(stripPrefix)
})

// 解析 BI 加载状态
const biLoadStatus = computed(() => {
  const logs = displayLogs.value
  if (!logs.length) return { stage: 'idle', message: '' }

  // 从后往前查找最新的 BI LOAD 日志
  for (let i = logs.length - 1; i >= 0; i--) {
    const line = logs[i]
    if (line.includes('[BI LOAD COMPLETE]')) {
      return { stage: 'complete', message: 'BI 图加载完成' }
    }
    if (line.includes('[BI LOAD] Creating charts')) {
      return { stage: 'creating', message: '正在生成图表...' }
    }
    if (line.includes('[BI LOAD] Energy data fetched')) {
      return { stage: 'energy', message: '正在获取能耗数据...' }
    }
    if (line.includes('[BI LOAD] Aggregation computed')) {
      return { stage: 'aggregation', message: '正在生成图表...' }
    }
    if (line.includes('[BI LOAD] Computing aggregation')) {
      return { stage: 'aggregating', message: '正在计算聚合数据...' }
    }
    if (line.includes('[BI LOAD] Data preprocessed')) {
      return { stage: 'preprocessed', message: '正在计算聚合数据...' }
    }
    if (line.includes('[BI LOAD] Data fetched')) {
      return { stage: 'preprocessing', message: '正在处理数据...' }
    }
    if (line.includes('[BI LOAD] Fetching data')) {
      return { stage: 'fetching', message: '正在从数据库获取数据...' }
    }
    if (line.includes('[BI LOAD START]')) {
      return { stage: 'started', message: '正在开始加载...' }
    }
  }

  // 检查是否有错误
  for (let i = logs.length - 1; i >= 0; i--) {
    const line = logs[i]
    if (line.includes('[BI LOAD] No data found')) {
      return { stage: 'error', message: '未找到数据' }
    }
    if (line.includes('[BI LOAD] No program data')) {
      return { stage: 'error', message: '该 program 无数据' }
    }
  }

  return { stage: 'idle', message: '' }
})

const currentLogLine = computed(() => {
  if (!displayLogs.value.length) return ''
  if (currentLogIndex.value >= displayLogs.value.length) {
    currentLogIndex.value = 0
  }
  return displayLogs.value[currentLogIndex.value]
})

watch(displayLogs, () => {
  currentLogIndex.value = 0
})

watch(robotQuery, (val) => {
  if (typeof val === 'string' && !val.trim()) {
    activeName.value = ''
    currentRobotLabel.value = ''
    shouldLoad.value = false
    primaryFrameUrl.value = ''
    secondaryFrameUrl.value = ''
    showPrimaryFrame.value = true
    loadingTarget.value = null
    loadingMode.value = 'full'
    selectedProgram.value = ''
    selectedAxis.value = ''
    syncRouteQuery({ robot: '', program: '', axis: '' })
  }
})

watch(activeName, (val, prev) => {
  if (!val || val === prev) return
  // 换机器人时，program/axis 选项集会变化，避免带入旧值
  selectedProgram.value = ''
  selectedAxis.value = ''
  syncRouteQuery({ program: '', axis: '' })
})

// 监听加载状态变化，动态调整日志轮询间隔
watch(isLoading, (val, prev) => {
  if (val === prev) return
  // 如果正在切换加载状态（从无到有或从有到无），重启轮询以使用正确的间隔
  if (logPollingTimer.value) {
    stopLogPolling()
    if (val) {
      // 开始加载，使用快速轮询
      startLogPolling()
    }
  }
})
</script>

<style scoped>
/* === 入场动画系统 === */

/* 标题滑入淡入动画 */
.entrance-slide-in {
  animation: slideInFade 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  opacity: 0;
  transform: translateX(-40px);
}

@keyframes slideInFade {
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 卡片缩放淡入动画 */
.entrance-scale-up {
  animation: scaleUpFade 0.9s cubic-bezier(0.16, 1, 0.3, 1) 0.2s forwards;
  opacity: 0;
  transform: scale(0.96) translateY(25px);
}

@keyframes scaleUpFade {
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.btn-entrance-2 {
  animation: btnFadeIn 0.5s ease-out 0.7s forwards;
  opacity: 0;
  transform: translateY(-10px);
}

@keyframes btnFadeIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 控制元素从右侧淡入 */
.entrance-fade-right-1 {
  animation: fadeRightIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.4s forwards;
  opacity: 0;
  transform: translateX(30px);
}

.entrance-fade-right-2 {
  animation: fadeRightIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.5s forwards;
  opacity: 0;
  transform: translateX(30px);
}

.entrance-fade-right-3 {
  animation: fadeRightIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.6s forwards;
  opacity: 0;
  transform: translateX(30px);
}

@keyframes fadeRightIn {
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 主内容区域延迟淡入 */
.entrance-delayed-fade {
  animation: delayedFadeIn 0.8s ease-out 0.8s forwards;
  opacity: 0;
}

@keyframes delayedFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* === 基础布局与背景 === */
.bi-viewport {
  background: radial-gradient(circle at 50% 35%, #0d1a2d 0%, #030508 100%);
  height: 100svh;
  position: relative;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  color: #fff;
}

.bi-viewport.is-maximized .layout-wrapper {
  padding: 8px;
  grid-template-rows: minmax(0, 1fr);
}

.bi-viewport.is-maximized .page-header,
.bi-viewport.is-maximized .control-panel {
  display: none;
}

.restore-fab {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 5;
  border-radius: 999px;
  height: 32px;
  padding: 0 14px;
}

.maximize-btn {
  border-radius: 12px;
  height: 32px;
  padding: 0 14px;
}

/* === 背景流光元素 === */
.space-ambient {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.nebula {
  position: absolute;
  filter: blur(120px);
  opacity: 0.28;
  mix-blend-mode: screen;
}

.nebula.blue {
  width: 80vw;
  height: 70vh;
  background: radial-gradient(circle, #0066ff, transparent 75%);
  top: -10%;
  left: -5%;
}

.nebula.gold {
  width: 80vw;
  height: 70vh;
  background: radial-gradient(circle, #ffaa00, transparent 75%);
  bottom: -10%;
  right: -5%;
}

.scan-grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 50px 50px;
}

.layout-wrapper {
  position: relative;
  z-index: 1;
  padding: clamp(12px, 1.6vw, 20px) clamp(16px, 2.2vw, 32px);
  width: 100%;
  max-width: none;
  margin: 0 auto;
  height: 100%;
  min-height: 0;
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
}

/* === Header === */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px 16px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex: 0 0 auto;
}

.title-area {
  display: flex;
  flex-direction: column;
}

.ios-title {
  font-size: clamp(22px, 2.4vw, 32px);
  letter-spacing: -0.5px;
  background: linear-gradient(180deg, #fff 40%, rgba(255,255,255,0.6));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
}

.ios-title .subtitle {
  font-size: clamp(12px, 1.2vw, 14px);
  color: #ffaa00;
  margin-left: 0;
  font-weight: 300;
  letter-spacing: 2px;
  display: block;
  margin-top: 4px;
}

.action-btn {
  background: linear-gradient(135deg, #00c3ff 0%, #0080ff 100%);
  border: none;
  box-shadow: 0 4px 14px rgba(0, 195, 255, 0.3);
  transition: all 0.3s ease;
}

.action-btn:hover:not(:disabled) {
  box-shadow: 0 6px 20px rgba(0, 195, 255, 0.5);
  transform: translateY(-1px);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.load-analysis-btn {
  flex: 0 0 auto;
  padding: 0 24px;
  height: 40px;
  border-radius: 12px;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0;
}

.load-analysis-btn.is-cancel {
  background: linear-gradient(135deg, #ff6b6b 0%, #ff3b30 100%);
  box-shadow: 0 6px 20px rgba(255, 59, 48, 0.35);
}

.load-analysis-btn.is-cancel:hover {
  transform: translateY(-1px);
}

/* === iOS 超透明玻璃卡片 === */
.ios-glass {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(50px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
}

.border-glow {
  position: absolute;
  inset: 0;
  border-radius: 24px;
  padding: 1px;
  background: linear-gradient(135deg, rgba(255, 170, 0, 0.4), transparent 40%, rgba(255, 170, 0, 0.1));
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  animation: borderBreathe 6s infinite ease-in-out, borderGlowEnter 1.2s ease-out forwards;
  opacity: 0;
}

@keyframes borderBreathe {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.8; box-shadow: inset 0 0 15px rgba(255, 170, 0, 0.2); }
}

@keyframes borderGlowEnter {
  0% {
    opacity: 0;
    transform: scale(0.95);
  }
  50% {
    opacity: 0.6;
  }
  100% {
    opacity: 0.3;
    transform: scale(1);
  }
}

/* 卡片标题 */
.cell-header {
  padding: 10px 18px;
  font-size: 11px;
  color: #c0ccda;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
  z-index: 1;
}

.accent-bar {
  width: 4px;
  height: 16px;
  background: #ffaa00;
  border-radius: 10px;
  box-shadow: 0 0 10px #ffaa00;
}

/* === 控制面板 === */
.control-panel {
  margin-bottom: 12px;
  overflow: visible;
  flex: 0 0 auto;
}

.control-content {
  padding: 14px 18px 16px;
  position: relative;
  z-index: 1;
}

.control-row {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.control-item {
  display: contents;
}

.compact-item {
  min-width: 0;
}

.control-item label {
  font-size: 12px;
  font-weight: 600;
  color: #8899aa;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  justify-content: flex-start;
}

.styled-select {
  flex: 0 0 auto;
  width: clamp(180px, 20vw, 260px);
  max-width: none;
  min-width: 0;
}

.styled-select :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.03);
}

.styled-select :deep(.el-input__wrapper:hover) {
  border-color: rgba(0, 195, 255, 0.3);
}

.styled-select :deep(.el-input__wrapper.is-focus) {
  border-color: #00c3ff;
  box-shadow: 0 0 0 3px rgba(0, 195, 255, 0.1);
}

.styled-select :deep(.el-input__inner) {
  color: #fff;
}

.styled-select :deep(.el-input__inner::placeholder) {
  color: #6a7a8a;
}

/* === 内容区域 === */
.bi-content {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  width: 100%;
  overflow: hidden;
}

/* === 空状态 === */
.bi-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  width: 100%;
  height: 100%;
  min-height: 0;
  flex: 1 1 auto;
  padding: 40px;
  border-radius: 0;
}

.empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: rgba(0, 195, 255, 0.1);
  color: #00c3ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
}

.empty-text {
  font-size: 15px;
  color: #8899aa;
}

/* === BI卡片 === */
.bi-card {
  padding: 0;
  overflow: hidden;
  border-radius: 0;
  width: 100%;
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.bi-frame-wrapper {
  position: relative;
  width: 100%;
  flex: 1 1 auto;
  min-height: 0;
  border-radius: 0;
  overflow: hidden;
  background: #000;
}

.bi-frame {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: none;
  background: #000;
  opacity: 0;
  pointer-events: none;
  transition: opacity 160ms ease;
}

.bi-frame.is-active {
  opacity: 1;
  pointer-events: auto;
}

/* === 加载遮罩层 === */

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-100%);
}

/* === Select Dropdown 全局样式（参考关键轨迹检查界面） === */
:deep(.el-select__wrapper) {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
  transition: all 0.2s ease !important;
}

:deep(.el-select__wrapper:hover) {
  border-color: rgba(0, 195, 255, 0.3) !important;
}

:deep(.el-select__wrapper.is-focused) {
  border-color: #00c3ff !important;
  box-shadow: 0 0 0 3px rgba(0, 195, 255, 0.1) !important;
}

:deep(.el-select__selected-item) {
  color: #fff !important;
}

:deep(.el-select__placeholder) {
  color: #6a7a8a !important;
}

/* 下拉框弹出层样式 */
:deep(.el-select-dropdown) {
  background: rgba(6, 10, 18, 0.95) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  backdrop-filter: blur(20px) !important;
}

:deep(.el-select-dropdown__item) {
  color: #dbe6f5 !important;
  background: transparent !important;
}

:deep(.el-select-dropdown__item:hover) {
  background: rgba(0, 195, 255, 0.1) !important;
}

:deep(.el-select-dropdown__item.is-selected) {
  color: #00c3ff !important;
  background: rgba(0, 195, 255, 0.15) !important;
}

:deep(.el-select-dropdown__item.is-disabled) {
  color: #6a7a8a !important;
}

/* === 时间范围选择器样式（Element Plus日期选择器） === */
.time-range-control {
  min-width: 0;
}

.styled-date-picker {
  flex: 0 0 auto;
  width: clamp(180px, 18vw, 240px);
  max-width: none;
  min-width: 0;
}

.load-analysis-btn {
  margin-left: auto;
}

@media (max-width: 1200px) {
  .control-row {
    justify-content: flex-start;
  }

  .load-analysis-btn {
    margin-left: 0;
  }
}

@media (max-width: 760px) {
  .page-header {
    align-items: flex-start;
  }
  .control-row {
    gap: 12px;
  }
  .styled-select,
  .styled-date-picker {
    width: 100%;
  }
  .load-analysis-btn {
    width: 100%;
    justify-content: center;
  }
  .bi-frame-wrapper {
    min-height: clamp(420px, 70vh, 720px);
  }
}

/* 日期选择器样式 - 与下拉框一致（使用全局样式，参考关键轨迹检查界面） */
:deep(.el-date-editor) {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 12px !important;
}

:deep(.el-date-editor:hover) {
  border-color: rgba(0, 195, 255, 0.3) !important;
}

:deep(.el-date-editor.is-active) {
  border-color: #00c3ff !important;
  box-shadow: 0 0 0 3px rgba(0, 195, 255, 0.1) !important;
}

/* 强制限制时间范围输入框宽度 */
:deep(.el-date-editor.el-range-editor) {
  width: 260px !important;
  min-width: 260px !important;
  max-width: 260px !important;
}

:deep(.el-date-editor.el-range-editor .el-range-input) {
  width: 90px !important;
  min-width: 90px !important;
}

@media (max-width: 760px) {
  :deep(.el-date-editor.el-range-editor) {
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
  }
  :deep(.el-date-editor.el-range-editor .el-range-input) {
    width: 100% !important;
    min-width: 0 !important;
  }
}
</style>

<!-- 全局样式：日期选择器青色主题（与关键轨迹检查界面一致） -->
<style>
.trajectory-date-picker.el-picker__popper {
  --el-color-primary: #00c3ff !important;
}

.trajectory-date-picker .el-picker-panel__shortcut:hover {
  color: #00c3ff !important;
  background: rgba(0, 195, 255, 0.1) !important;
}

.trajectory-date-picker .el-picker-panel__icon-btn:hover {
  color: #00c3ff !important;
}

.trajectory-date-picker .el-date-picker__header-label:hover {
  color: #00c3ff !important;
}

.trajectory-date-picker .el-date-table td.today div {
  color: #00c3ff !important;
}

.trajectory-date-picker .el-date-table td.in-range div {
  background: rgba(0, 195, 255, 0.15) !important;
  color: #00c3ff !important;
}

.trajectory-date-picker .el-date-table td.start-date div,
.trajectory-date-picker .el-date-table td.end-date div {
  background: #00c3ff !important;
  color: #fff !important;
}

.trajectory-date-picker .el-month-table td.current div {
  background: #00c3ff !important;
  color: #fff !important;
}

.trajectory-date-picker .el-year-table td.current div {
  background: #00c3ff !important;
  color: #fff !important;
}

.trajectory-date-picker .el-month-table td:hover div,
.trajectory-date-picker .el-year-table td:hover div {
  color: #00c3ff !important;
}

.trajectory-date-picker .el-date-table td.available:hover div {
  background: rgba(0, 195, 255, 0.15) !important;
}

.trajectory-date-picker .el-button.is-confirm {
  color: #00c3ff !important;
}

.trajectory-date-picker .el-button.is-confirm:hover {
  background: rgba(0, 195, 255, 0.1) !important;
}
</style>
