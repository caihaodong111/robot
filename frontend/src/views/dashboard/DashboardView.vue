<template>
  <div class="dashboard-viewport">
    <!-- Header Section -->
    <header class="dashboard-header">
      <div class="title-area">
        <h1>平台概览 <small>Platform Overview</small></h1>
        <p class="subtitle">实时监控机器人集群健康态势与风险分布</p>
      </div>
      <div class="header-actions">
        <div class="last-update">最后更新: {{ lastUpdateTime }}</div>
        <el-button :icon="Refresh" circle @click="handleRefresh" class="refresh-btn"></el-button>
        <el-button type="primary" class="gradient-btn" @click="goTo('/portal')">管理控制台</el-button>
      </div>
    </header>

    <!-- KPI Metrics -->
    <div class="kpi-grid">
      <div class="kpi-card glass-card">
        <div class="kpi-icon total"><el-icon><Cpu /></el-icon></div>
        <div class="kpi-info">
          <label>机器人总数</label>
          <div class="value">{{ summary.total }}</div>
          <div class="trend positive">
            <span class="online-dot"></span> 在线 {{ summary.online }}
          </div>
        </div>
      </div>
      <div class="kpi-card glass-card warning">
        <div class="kpi-icon risk"><el-icon><Warning /></el-icon></div>
        <div class="kpi-info">
          <label>高风险设备</label>
          <div class="value">{{ summary.highRisk }}</div>
          <div class="trend negative">占比 {{ highRiskRate }}%</div>
        </div>
      </div>
      <div class="kpi-card glass-card muted">
        <div class="kpi-icon offline"><el-icon><CircleClose /></el-icon></div>
        <div class="kpi-info">
          <label>离线设备</label>
          <div class="value">{{ summary.offline }}</div>
          <div class="trend">离线率 {{ summary.offlineRate }}%</div>
        </div>
      </div>
      <div class="kpi-card glass-card primary">
        <div class="kpi-icon health"><el-icon><Odometer /></el-icon></div>
        <div class="kpi-info">
          <label>综合健康指数</label>
          <div class="value">{{ summary.healthIndex }}</div>
          <div class="trend-bar">
            <div class="fill" :style="{ width: summary.healthIndex + '%' }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Charts Layout -->
    <div class="chart-layout-grid">
      <!-- Section 1: Risk Ratio Pie Charts (User Requested) -->
      <div class="card-wrapper ratio-section">
        <el-card class="styled-card">
          <template #header>
            <div class="card-header-inner">
              <span class="title">各组高风险占比 <small>High-Risk Ratio per Group</small></span>
              <el-tooltip content="展示各车间组内，高风险机器人数量占该组总设备数的百分比">
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <div class="pie-grid-container">
            <div ref="chartRef" class="main-chart-item full-width-chart"></div>
          </div>
        </el-card>
      </div>

      <!-- Section 2: Pulse & Health -->
      <div class="card-wrapper pulse-section">
        <el-card class="styled-card">
          <template #header>
            <div class="card-header-inner">
              <span class="title">运行脉搏 <small>Operational Pulse</small></span>
            </div>
          </template>
          <div ref="statusChartRef" class="main-chart-item"></div>
        </el-card>
      </div>

      <!-- Section 3: Trend & Recent Alerts -->
      <div class="card-wrapper trend-section">
        <el-card class="styled-card">
          <template #header>
            <div class="card-header-inner">
              <span class="title">风险态势趋势 <small>Risk Trend (7D)</small></span>
            </div>
          </template>
          <div ref="trendChartRef" class="main-chart-item"></div>
        </el-card>
      </div>

      <div class="card-wrapper alerts-section">
        <el-card class="styled-card">
          <template #header>
            <div class="card-header-inner">
              <span class="title">实时风险预警 <small>Active Alerts</small></span>
              <el-link type="primary" @click="goTo('/alerts')">全部</el-link>
            </div>
          </template>
          <div class="alert-list-styled">
            <div v-if="alertLoading" class="loading-shimmer">加载中...</div>
            <template v-else-if="recentAlerts.length">
              <div v-for="alert in recentAlerts.slice(0, 5)" :key="alert.id" class="alert-item-mini">
                <div class="alert-badge" :class="alert.severity"></div>
                <div class="alert-content">
                  <div class="alert-top">
                    <span class="robot-name">{{ alert.robot_name }}</span>
                    <span class="alert-time">{{ formatTimeOnly(alert.triggered_at) }}</span>
                  </div>
                  <div class="alert-msg">{{ alert.message }}</div>
                </div>
              </div>
            </template>
            <el-empty v-else :image-size="60" description="暂无活动风险" />
          </div>
        </el-card>
      </div>
    </div>

    <!-- Quick Navigation -->
    <footer class="quick-nav">
      <div class="nav-item" @click="goTo('/devices')">
        <el-icon><Monitor /></el-icon> 状态监控
      </div>
      <div class="nav-item" @click="goTo('/monitoring')">
        <el-icon><LocationInformation /></el-icon> 轨迹分析
      </div>
      <div class="nav-item" @click="goTo('/alerts')">
        <el-icon><PieChart /></el-icon> 数据分析
      </div>
      <div class="nav-item" @click="handleRefresh">
        <el-icon><RefreshRight /></el-icon> 同步数据
      </div>
    </footer>

    <!-- Detail Dialog -->
    <el-dialog v-model="detailVisible" :title="detailTitle" width="850px" class="premium-dialog">
      <el-table :data="detailRows" stripe v-loading="detailLoading" height="400">
        <el-table-column prop="name" label="机器人" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
             <span class="status-indicator" :class="row.status">{{ row.status }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="level" label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag :type="row.level === 'H' ? 'danger' : row.level === 'M' ? 'warning' : 'success'" size="small">
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="riskScore" label="风险分" width="90" align="center" />
        <el-table-column prop="remark" label="风险描述" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Refresh, Cpu, Warning, CircleClose, Odometer,
  InfoFilled, Monitor, LocationInformation, PieChart, RefreshRight
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { DEMO_MODE } from '@/config/appConfig'
import { getRobotComponents, getRobotGroups, getRiskEventStatistics } from '@/api/robots'
import { createRiskEvents, getGroupStats, getRobotsByGroup, robotGroups as mockGroups } from '@/mock/robots'

const router = useRouter()

const loading = ref(false)
const alertLoading = ref(false)
const groupsData = ref([])
const recentAlerts = ref([])
const lastUpdateTime = ref(new Date().toLocaleTimeString())

const chartRef = ref(null)
const statusChartRef = ref(null)
const trendChartRef = ref(null)
const chartInstances = new Map()

const detailVisible = ref(false)
const detailTitle = ref('')
const detailRows = ref([])
const detailLoading = ref(false)

const groupRows = computed(() => {
  if (DEMO_MODE) {
    return mockGroups.map((group) => ({
      key: group.key,
      name: group.name,
      total: group.total,
      stats: getGroupStats(group.key)
    }))
  }
  return groupsData.value.map((group) => ({
    key: group.key,
    name: group.name,
    total: group.expected_total ?? group.stats?.total ?? 0,
    stats: {
      online: group.stats?.online ?? 0,
      offline: group.stats?.offline ?? 0,
      maintenance: group.stats?.maintenance ?? 0,
      highRisk: group.stats?.highRisk ?? 0,
      historyHighRisk: group.stats?.historyHighRisk ?? 0
    }
  }))
})

const summary = computed(() => {
  const rows = groupRows.value
  const total = rows.reduce((acc, r) => acc + (r.total || 0), 0)
  const online = rows.reduce((acc, r) => acc + (r.stats?.online || 0), 0)
  const offline = rows.reduce((acc, r) => acc + (r.stats?.offline || 0), 0)
  const maintenance = rows.reduce((acc, r) => acc + (r.stats?.maintenance || 0), 0)
  const highRisk = rows.reduce((acc, r) => acc + (r.stats?.highRisk || 0), 0)
  const historyHighRisk = rows.reduce((acc, r) => acc + (r.stats?.historyHighRisk || 0), 0)
  const offlineRate = total ? Math.round((offline / total) * 100) : 0
  const healthIndex = Math.max(0, Math.round(100 - offlineRate * 0.6 - (highRisk / (total || 1)) * 40))

  return { total, online, offline, maintenance, highRisk, historyHighRisk, offlineRate, healthIndex }
})

const highRiskRate = computed(() => (summary.value.total ? Math.round((summary.value.highRisk / summary.value.total) * 100) : 0))

const formatDateTime = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN')
}

const formatTimeOnly = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const loadGroups = async () => {
  if (DEMO_MODE) return
  loading.value = true
  try {
    groupsData.value = await getRobotGroups()
  } catch (error) {
    ElMessage.error(error?.message || '加载分组失败')
  } finally {
    loading.value = false
  }
}

const loadAlerts = async () => {
  if (DEMO_MODE) {
    recentAlerts.value = createRiskEvents(8).slice(0, 6)
    return
  }
  alertLoading.value = true
  try {
    const data = await getRiskEventStatistics()
    recentAlerts.value = data?.recent_alerts || []
  } catch (error) {
    ElMessage.error(error?.message || '加载风险事件失败')
  } finally {
    alertLoading.value = false
  }
}

const handleRefresh = () => {
  lastUpdateTime.value = new Date().toLocaleTimeString()
  loadGroups()
  loadAlerts()
}

const goTo = (path) => {
  router.push(path)
}

const initChart = (key, el) => {
  if (!el) return null
  if (!chartInstances.has(key)) {
    chartInstances.set(key, echarts.init(el))
  }
  return chartInstances.get(key)
}

const renderPieChart = () => {
  const chart = initChart('pie', chartRef.value)
  if (!chart) return
  
  const rows = groupRows.value
  const series = []
  const titles = []
  
  rows.forEach((row, index) => {
    const highRisk = row.stats?.highRisk || 0
    const total = row.total || 1
    const ratio = Math.round((highRisk / total) * 100)
    
    const centerX = (index * 25 + 12.5) + '%'
    const centerY = '50%'
    
    // Dynamic color based on risk ratio
    const riskColor = ratio > 40 ? '#ef4444' : ratio > 20 ? '#f59e0b' : '#3b82f6'

    series.push({
      type: 'pie',
      radius: ['55%', '75%'],
      center: [centerX, centerY],
      avoidLabelOverlap: false,
      label: { show: false },
      emphasis: { scale: true },
      data: [
        { value: highRisk, name: '高风险', itemStyle: { color: '#ef4444' } },
        { value: total - highRisk, name: '正常', itemStyle: { color: '#e2e8f0' } }
      ]
    })
    
    // Inner center text using graphic or label for custom look
    titles.push({
      text: ratio + '%',
      left: centerX,
      top: '48%',
      textAlign: 'center',
      textStyle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: ratio > 0 ? '#ef4444' : '#64748b'
      }
    }, {
      text: row.name,
      left: centerX,
      top: '85%',
      textAlign: 'center',
      textStyle: {
        fontSize: 12,
        color: '#64748b',
        fontWeight: 'normal'
      }
    })
  })

  chart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    title: titles,
    series: series
  })

  chart.off('click')
  chart.on('click', (params) => {
    const group = rows[params.seriesIndex]
    openDetail({
      seriesName: `${group.name} - 高风险详情`,
      data: { key: group.key, name: group.name }
    })
  })
}

const renderStatusChart = () => {
  const chart = initChart('status', statusChartRef.value)
  if (!chart) return
  const rows = groupRows.value
  const categories = rows.map((row) => row.name)
  const online = rows.map((row) => row.stats?.online || 0)
  const offline = rows.map((row) => row.stats?.offline || 0)
  
  chart.setOption({
    grid: { left: '3%', right: '4%', top: '15%', bottom: '10%', containLabel: true },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: {
      type: 'category',
      data: categories,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b' }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } },
      axisLabel: { color: '#64748b' }
    },
    series: [
      {
        name: '在线',
        type: 'bar',
        barWidth: '20%',
        data: online,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#10b981' },
            { offset: 1, color: '#34d399' }
          ])
        }
      },
      {
        name: '离线',
        type: 'bar',
        barWidth: '20%',
        data: offline,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#ef4444' },
            { offset: 1, color: '#f87171' }
          ])
        }
      }
    ]
  })
}

const renderTrendChart = () => {
  const chart = initChart('trend', trendChartRef.value)
  if (!chart) return
  
  const days = 7
  const labels = []
  const highRisk = []
  const baseHigh = summary.value.highRisk
  
  for (let i = days - 1; i >= 0; i -= 1) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    labels.push(`${date.getMonth() + 1}/${date.getDate()}`)
    highRisk.push(Math.max(0, Math.round(baseHigh * (0.8 + Math.random() * 0.4))))
  }

  chart.setOption({
    grid: { left: '3%', right: '4%', top: '15%', bottom: '10%', containLabel: true },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: labels,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b' }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#f1f5f9' } }
    },
    series: [{
      name: '风险数值',
      type: 'line',
      smooth: true,
      symbol: 'none',
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(239, 68, 68, 0.2)' },
          { offset: 1, color: 'rgba(239, 68, 68, 0)' }
        ])
      },
      lineStyle: { color: '#ef4444', width: 3 },
      data: highRisk
    }]
  })
}

const renderAllCharts = () => {
  renderPieChart()
  renderStatusChart()
  renderTrendChart()
}

const openDetail = async (payload) => {
  const groupKey = payload.data.key
  const groupName = payload.data.name
  detailTitle.value = `${groupName} - 高风险设备列表`
  detailVisible.value = true
  detailLoading.value = true
  
  try {
    if (DEMO_MODE) {
      const list = getRobotsByGroup(groupKey)
      detailRows.value = list.filter(r => r.isHighRisk)
    } else {
      const data = await getRobotComponents({ group: groupKey, tab: 'highRisk' })
      detailRows.value = data?.results || []
    }
  } catch (error) {
    ElMessage.error('加载详情失败')
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => {
  loadGroups()
  loadAlerts()
  renderAllCharts()
  window.addEventListener('resize', () => chartInstances.forEach(c => c.resize()))
})

onBeforeUnmount(() => {
  chartInstances.forEach(c => c.dispose())
})

watch(groupRows, renderAllCharts, { deep: true })
</script>

<style scoped>
.dashboard-viewport {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  background-color: #f8fafc;
  min-height: calc(100vh - 100px);
  color: #1e293b;
}

/* Header */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-header h1 {
  font-size: 28px;
  font-weight: 800;
  margin: 0;
  background: linear-gradient(135deg, #1e293b 0%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.dashboard-header h1 small {
  font-size: 14px;
  color: #64748b;
  font-weight: 400;
  margin-left: 8px;
  -webkit-text-fill-color: #64748b;
}

.subtitle {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 14px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.last-update {
  font-size: 12px;
  color: #94a3b8;
  background: #fff;
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid #e2e8f0;
}

.gradient-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

/* KPI Cards */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.glass-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 20px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.glass-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 30px -10px rgba(0, 0, 0, 0.1);
}

.kpi-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.kpi-icon.total { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
.kpi-icon.risk { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
.kpi-icon.offline { background: rgba(148, 163, 184, 0.1); color: #64748b; }
.kpi-icon.health { background: rgba(16, 185, 129, 0.1); color: #10b981; }

.kpi-info label {
  display: block;
  font-size: 13px;
  color: #64748b;
  margin-bottom: 4px;
}

.kpi-info .value {
  font-size: 24px;
  font-weight: 800;
  color: #1e293b;
}

.trend {
  font-size: 12px;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.trend.positive { color: #10b981; }
.trend.negative { color: #ef4444; }

.online-dot {
  width: 6px;
  height: 6px;
  background: #10b981;
  border-radius: 50%;
  box-shadow: 0 0 8px #10b981;
}

.trend-bar {
  height: 4px;
  width: 100px;
  background: #e2e8f0;
  border-radius: 2px;
  margin-top: 8px;
  overflow: hidden;
}

.trend-bar .fill {
  height: 100%;
  background: #10b981;
  transition: width 1s ease-out;
}

/* Charts Grid */
.chart-layout-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: auto auto;
  gap: 20px;
}

.ratio-section { grid-column: span 3; }
.pulse-section { grid-column: span 2; }
.trend-section { grid-column: span 1; }
.alerts-section { grid-column: span 1; }

.styled-card {
  border-radius: 20px;
  border: none;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
}

.card-header-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header-inner .title {
  font-size: 16px;
  font-weight: 700;
  color: #334155;
}

.card-header-inner .title small {
  color: #94a3b8;
  font-weight: 400;
  margin-left: 4px;
}

.main-chart-item {
  width: 100%;
  height: 300px;
}

.pie-grid-container {
  padding: 10px 0;
}

.full-width-chart {
  height: 240px;
}

/* Alert List */
.alert-list-styled {
  height: 300px;
  overflow-y: auto;
  padding-right: 8px;
}

.alert-item-mini {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 8px;
  background: #f8fafc;
  transition: background 0.2s;
}

.alert-item-mini:hover { background: #f1f5f9; }

.alert-badge {
  width: 4px;
  height: 40px;
  border-radius: 2px;
  flex-shrink: 0;
}

.alert-badge.critical { background: #ef4444; }
.alert-badge.high { background: #f97316; }
.alert-badge.medium { background: #f59e0b; }
.alert-badge.low { background: #3b82f6; }

.alert-content { flex: 1; overflow: hidden; }
.alert-top { display: flex; justify-content: space-between; margin-bottom: 2px; }
.robot-name { font-size: 13px; font-weight: 600; color: #334155; }
.alert-time { font-size: 11px; color: #94a3b8; }
.alert-msg { font-size: 12px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Quick Nav */
.quick-nav {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding-top: 10px;
}

.nav-item {
  background: #fff;
  padding: 12px 24px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #475569;
  cursor: pointer;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
}

.nav-item:hover {
  background: #3b82f6;
  color: #fff;
  border-color: #3b82f6;
  transform: translateY(-2px);
}

/* Custom Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

/* Dialog Styling */
.premium-dialog :deep(.el-dialog) {
  border-radius: 24px;
  overflow: hidden;
}

.status-indicator {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}
.status-indicator.online { background: #dcfce7; color: #166534; }
.status-indicator.offline { background: #fee2e2; color: #991b1b; }
.status-indicator.maintenance { background: #fef3c7; color: #92400e; }

@media (max-width: 1200px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .chart-layout-grid { grid-template-columns: 1fr; }
  .ratio-section, .pulse-section, .trend-section, .alerts-section { grid-column: span 1; }
}
</style>
