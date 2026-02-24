<template>
  <div class="dashboard-viewport">
    <div class="ambient-background">
      <div class="nebula blue"></div>
      <div class="nebula gold"></div>
      <div class="breathing-line gold-1"></div>
      <div class="breathing-line gold-2"></div>
      <div class="scan-grid"></div>
    </div>

    <div class="layout-wrapper">
      <header class="page-header entrance-slide-in">
        <div class="title-group">
          <h1 class="ios-title">ROBOT OVERVIEW<span class="subtitle">机器人概览</span></h1>
          <div class="status-tag status-tag-entrance">
            <span class="dot pulse"></span> 最近更新时间：{{ lastUpdateTime }}
          </div>
        </div>
      </header>

      <div class="dashboard-content">

        <aside class="left-panel">
          <div class="data-cell ios-glass main-chart-card entrance-scale-up">
            <div class="border-glow entrance-border-glow"></div>
            <div class="cell-header">
              <span class="accent-bar"></span>
              高风险分布总览
            </div>
            <div ref="chartRef" class="main-chart-box entrance-chart-fade"></div>
          </div>

          <div class="data-cell ios-glass connection-panel entrance-scale-up-delay-1">
            <div class="border-glow purple-tint entrance-border-glow"></div>
            <div class="cell-header">
              <span class="accent-bar purple"></span>
              机器人连接状态
            </div>
            <div class="connection-stats entrance-content-fade" v-loading="connectionLoading">
              <div class="connection-details">
                <div class="connection-item total">
                  <div class="connection-indicator">
                    <span class="dot dot-total"></span>
                    <span class="connection-label">Total</span>
                  </div>
                  <span class="connection-count">{{ connectionStats.total }}</span>
                </div>
                <div class="connection-item high-risk">
                  <div class="connection-indicator">
                    <span class="dot dot-high-risk"></span>
                    <span class="connection-label">High Risk</span>
                  </div>
                  <span class="connection-count">{{ connectionStats.highRisk }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="data-cell ios-glass feed-panel entrance-scale-up-delay-2">
            <div class="border-glow blue-tint entrance-border-glow"></div>
            <div class="cell-header">
              <span class="accent-bar blue"></span>
              持续增大的关键轨迹预警
            </div>
            <div class="log-stream entrance-content-fade">
              <div v-if="alertLoading" class="loading-state">载入中...</div>
              <template v-else-if="recentAlerts.length">
                <div v-for="(alert, idx) in recentAlerts" :key="alert.id" class="log-row log-row-entrance" :style="{ animationDelay: `${0.9 + idx * 0.1}s` }">
                  <span class="log-tag" :class="alert.severity"></span>
                  <div class="log-info">
                    <p>{{ alert.message || alert.robot_name }}</p>
                    <span class="log-time">{{ formatTimeOnly(alert.triggered_at) }}</span>
                  </div>
                </div>
              </template>
              <div v-else class="no-data">当前无风险事件</div>
            </div>
          </div>
        </aside>

        <main class="right-panel">
          <div class="workshop-grid">
            <div
              class="data-cell ios-glass workshop-card entrance-scale-up-delay-1"
              v-for="(group, idx) in groupRows"
              :key="group.key"
              @click="goToWorkshop(group.key)"
              :style="{ animationDelay: `${0.3 + idx * 0.05}s` }"
            >
              <div class="border-glow slow entrance-border-glow"></div>

              <div class="cell-header compact">
                <span class="accent-bar small" :class="group.stats?.highRisk > 0 ? 'risk' : 'safe'"></span>
                {{ group.name }}
              </div>

              <div class="workshop-content">
                <div class="workshop-chart-wrapper">
                  <div :ref="el => setWorkshopChartRef(group.key, el)" class="workshop-mini-chart"></div>
                </div>

                <div class="workshop-data-col">
                  <div class="mini-stat-row">
                    <label>High Risk</label>
                    <span class="value" :class="{ 'has-risk': group.stats?.highRisk > 0 }">
                      {{ group.stats?.highRisk || 0 }}
                    </span>
                  </div>
                  <div class="mini-stat-row">
                    <label>Total</label>
                    <span class="value normal">{{ group.stats?.total || 0 }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>

    <el-dialog v-model="detailVisible" width="860px" class="premium-dialog">
       <template #header>
        <div class="dialog-header">
          <div class="dialog-title">
            <span class="dialog-chip"></span>
            {{ detailTitle || '高风险机器人列表' }}
          </div>
          <div class="dialog-subtitle">HIGH RISK ROBOT INSIGHTS</div>
        </div>
      </template>
      <div class="dialog-body">
        <div class="dialog-summary">
          <div class="summary-row">
            <div class="summary-item">
              <span class="summary-label">高风险机器人</span>
              <span class="summary-value primary">{{ detailTotal }}</span>
            </div>
            <div class="summary-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: getRiskPercentage() + '%' }"></div>
              </div>
              <span class="progress-text">{{ getRiskPercentage() }}%</span>
            </div>
          </div>
          <div class="summary-row">
            <div class="summary-item">
              <span class="summary-label">最后更新</span>
              <span class="summary-value time">{{ lastUpdateTime }}</span>
            </div>
          </div>
        </div>

        <el-table :data="detailRows" stripe v-loading="detailLoading" height="420" class="premium-table">
          <el-table-column prop="name" label="机器人" width="160" />
          <el-table-column prop="level" label="等级(level)" width="80" align="center">
            <template #default="{ row }">
               <el-tag :type="levelTagType(row.level)" effect="light">{{ row.level }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="referenceNo" label="参考编号(reference)" width="150" show-overflow-tooltip />
          <el-table-column prop="remark" label="风险描述" min-width="200" show-overflow-tooltip />
        </el-table>

        <div v-if="!detailLoading && !detailRows.length" class="dialog-empty">
          <div class="empty-dot"></div>
          当前暂无高风险记录
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { Monitor } from '@element-plus/icons-vue'
import { DEMO_MODE } from '@/config/appConfig'
import { getRobotComponents, getRobotGroups, getRiskEventStatistics, getRobotStatsSummary } from '@/api/robots'
import { createRiskEvents, getGroupStats, getRobotsByGroup, robotGroups as mockGroups } from '@/mock/robots'
import request from '@/utils/request'

const router = useRouter()

const loading = ref(false)
const alertLoading = ref(false)
const connectionLoading = ref(false)
const connectionStats = ref({
  total: 0,
  highRisk: 0
})
const overallTotal = ref(null)
const groupsData = ref([])
const recentAlerts = ref([])
const lastSyncTime = ref(null)
const lastUpdateTime = computed(() => {
  if (!lastSyncTime.value) return '暂无同步记录'
  const syncTime = new Date(lastSyncTime.value)
  const year = syncTime.getFullYear()
  const month = String(syncTime.getMonth() + 1).padStart(2, '0')
  const day = String(syncTime.getDate()).padStart(2, '0')
  const hour = String(syncTime.getHours()).padStart(2, '0')
  const minute = String(syncTime.getMinutes()).padStart(2, '0')
  const second = String(syncTime.getSeconds()).padStart(2, '0')
  return `${year}年${month}月${day}日${hour}时${minute}分${second}秒`
})

const normalizeGroupName = (group) => {
  if (!group) return group
  if (group.name === 'SA1' || group.key === 'SA1') {
    return { ...group, name: 'AS1' }
  }
  return group
}

// 加载机器人组数据
const loadGroupsData = async () => {
  loading.value = true
  try {
    if (DEMO_MODE) {
      groupsData.value = mockGroups.map(group => ({
        key: group.key,
        name: group.name,
        stats: getGroupStats(group.key)
      })).map(normalizeGroupName)
    } else {
      const response = await getRobotGroups()
      groupsData.value = (response || []).map(normalizeGroupName)
    }
  } catch (error) {
    console.error('加载机器人组数据失败:', error)
    ElMessage.error('加载数据失败')
    groupsData.value = []
  } finally {
    loading.value = false
  }
}

const chartRef = ref(null)
const chartInstances = new Map()
const workshopChartRefs = new Map()

const setWorkshopChartRef = (key, el) => {
  if (el) workshopChartRefs.set(key, el)
}

const detailVisible = ref(false)
const detailTitle = ref('')
const detailRows = ref([])
const detailTotal = ref(0)
const detailLoading = ref(false)
const currentGroupTotal = ref(0)

// 计算高风险占比
const getRiskPercentage = () => {
  if (!currentGroupTotal.value || currentGroupTotal.value === 0) return '0.0'
  const percentage = ((detailTotal.value / currentGroupTotal.value) * 100).toFixed(1)
  return percentage
}

const groupRows = computed(() => {
  if (DEMO_MODE) {
    return mockGroups.map(group => ({
      key: group.key,
      name: group.name,
      stats: getGroupStats(group.key)
    }))
  }
  return groupsData.value.map(group => ({
    key: group.key,
    name: group.name,
    stats: group.stats || {}
  }))
})

const formatTimeOnly = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const levelTagType = (level) => {
  const types = { H: 'danger', M: 'warning', L: 'info', T: 'success', C: '' }
  return types[level] || 'info'
}

const initChart = (key, el) => {
  if (!el) return null
  if (!chartInstances.has(key)) {
    chartInstances.set(key, echarts.init(el))
  }
  return chartInstances.get(key)
}

// 跳转到机器人状态界面对应车间
const goToWorkshop = (groupKey) => {
  router.push({
    path: '/devices',
    query: { group: groupKey }
  })
}

const showGroupDetail = async (groupKey, groupName) => {
  detailVisible.value = true
  detailTitle.value = `${groupName} - 高风险机器人列表`
  detailLoading.value = true
  detailRows.value = []
  detailTotal.value = 0
  currentGroupTotal.value = 0
  try {
    if (DEMO_MODE) {
      const robots = getRobotsByGroup(groupKey)
      const stats = getGroupStats(groupKey)
      currentGroupTotal.value = stats.total || 0
      const rows = robots.filter(r => r.isHighRisk).map(r => ({
        name: r.name,
        level: r.level,
        referenceNo: r.referenceNo,
        remark: r.remark
      }))
      detailRows.value = rows
      detailTotal.value = rows.length
    } else {
      const response = await getRobotComponents({ group: groupKey, tab: 'highRisk' })
      const groupStats = groupRows.value.find(g => g.key === groupKey)?.stats
      currentGroupTotal.value = groupStats?.total || 0
      const data = response?.results || response || []
      detailRows.value = data.map(r => ({
        name: r.name || r.robot_id,
        level: r.level,
        referenceNo: r.referenceNo,
        remark: r.remark
      }))
      detailTotal.value = typeof response?.count === 'number' ? response.count : detailRows.value.length
    }
  } catch (error) {
    console.error('加载组详情失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    detailLoading.value = false
  }
}

// 渲染主图（逻辑保持，仅容器变了）
const renderMainPieChart = () => {
  const chart = initChart('main', chartRef.value)
  if (!chart) return

  const mainBox = chartRef.value?.getBoundingClientRect()
  const baseSize = mainBox ? Math.min(mainBox.width, mainBox.height) : 240
  const ringInner = baseSize < 260 ? 58 : 54
  const ringOuter = baseSize < 260 ? 80 : 78
  const labelRadius = Math.max(34, ringInner - 10)
  const mainFontSize = Math.max(18, Math.round(baseSize * 0.11))
  const subFontSize = Math.max(9, Math.round(baseSize * 0.045))

  const rows = groupRows.value
    .filter(row => (row.stats?.highRisk || 0) > 0)
    .sort((a, b) => (b.stats?.highRisk || 0) - (a.stats?.highRisk || 0))

  const totalHighRisk = rows.reduce((sum, row) => sum + (row.stats?.highRisk || 0), 0)
  const groupTotal = groupRows.value.reduce((sum, row) => sum + (row.stats?.total || 0), 0)
  const totalRobots = Number.isFinite(overallTotal.value) ? overallTotal.value : groupTotal

  const colorSchemes = [
    { grad: ['#00f2ff', '#0066ff'], glow: 'rgba(0, 242, 255, 0.6)' },
    { grad: ['#ffcc00', '#ff6600'], glow: 'rgba(255, 204, 0, 0.6)' },
    { grad: ['#00ffa3', '#008a5c'], glow: 'rgba(0, 255, 163, 0.6)' },
    { grad: ['#ffffff', '#636e72'], glow: 'rgba(255, 255, 255, 0.3)' }
  ]

  const pieData = rows.map((row, index) => {
    const scheme = colorSchemes[index % colorSchemes.length]
    return {
      value: row.stats?.highRisk || 0,
      name: row.name,
      itemStyle: {
        borderRadius: 8,
        color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
          { offset: 0, color: scheme.grad[0] },
          { offset: 1, color: scheme.grad[1] }
        ]),
        borderColor: 'rgba(255,255,255,0.2)',
        borderWidth: 1,
        shadowBlur: 15,
        shadowColor: scheme.glow
      }
    }
  })

  chart.setOption({
    series: [
      {
        type: 'pie',
        radius: [`${ringInner}%`, `${ringOuter}%`], // 预留中心空间避免文字与扇区重叠
        center: ['50%', '50%'],
        roseType: 'radius',
        padAngle: 4,
        itemStyle: { borderRadius: 8 },
        label: { show: false },
        data: pieData
      },
      {
        type: 'pie',
        radius: [0, `${labelRadius}%`],
        silent: true,
        label: {
          show: true,
          position: 'center',
          formatter: () => [`{v|${totalHighRisk} / ${totalRobots}}`, `{l|High Risk / Total}`].join('\n'),
          rich: {
            v: { fontSize: mainFontSize, fontWeight: 900, color: '#ffcc00', textShadow: '0 0 20px rgba(255, 204, 0, 0.8)', lineHeight: Math.round(mainFontSize * 1.1) },
            l: { fontSize: subFontSize, color: '#8899aa', paddingTop: 4, lineHeight: Math.round(subFontSize * 1.2) }
          }
        },
        data: [{ value: 1, itemStyle: { color: 'transparent' } }]
      }
    ],
    tooltip: {
      backgroundColor: 'rgba(10, 20, 35, 0.9)',
      borderColor: '#00c3ff',
      textStyle: { color: '#fff' }
    }
  })

  chart.off('click')
  chart.on('click', (params) => {
    if (params.componentType === 'series' && params.seriesIndex === 0) {
      const group = rows.find(r => r.name === params.name)
      if (group) showGroupDetail(group.key, group.name)
    }
  })
}

// 渲染车间图表（优化为适合小卡片的样式）
const renderWorkshopCharts = () => {
  groupRows.value.forEach(group => {
    const el = workshopChartRefs.get(group.key)
    if (!el) return

    const chartKey = `workshop-${group.key}`
    if (!chartInstances.has(chartKey)) {
      chartInstances.set(chartKey, echarts.init(el))
    }
    const chart = chartInstances.get(chartKey)

    const highRisk = group.stats?.highRisk || 0
    const total = group.stats?.total || 0
    const normal = total - highRisk
    const hasHighRisk = highRisk > 0
    const percentage = total > 0 ? ((highRisk / total) * 100).toFixed(1) : '0.0'

    chart.setOption({
      series: [
        {
          type: 'pie',
          radius: ['60%', '85%'],
          center: ['50%', '50%'],
          silent: true,
          label: { show: false },
          data: [
            {
              value: highRisk,
              itemStyle: {
                color: hasHighRisk ? new echarts.graphic.LinearGradient(0,0,1,1,[{offset:0,color:'#ff6b6b'},{offset:1,color:'#cc0000'}]) : '#00d4ff',
                shadowBlur: hasHighRisk ? 10 : 0,
                shadowColor: '#ff4d4f'
              }
            },
            {
              value: normal || 1,
              itemStyle: { color: 'rgba(255, 255, 255, 0.08)' }
            }
          ]
        },
        {
          type: 'pie',
          radius: [0, '45%'],
          silent: true,
          label: {
            show: true,
            position: 'center',
            formatter: () => `{${hasHighRisk ? 'value' : 'valueSafe'}|${percentage}%}`,
            rich: {
              value: {
                fontSize: 16,
                fontWeight: 800,
                color: '#ff4d4f',
                textShadow: '0 0 8px rgba(255, 77, 79, 0.6)'
              },
              valueSafe: {
                fontSize: 16,
                fontWeight: 700,
                color: '#00c3ff',
                textShadow: '0 0 6px rgba(0, 195, 255, 0.5)'
              }
            }
          },
          data: [{ value: 1, itemStyle: { color: 'transparent' } }]
        }
      ]
    })
  })
}

const loadAlerts = async () => {
  alertLoading.value = true
  try {
    if (DEMO_MODE) {
      recentAlerts.value = createRiskEvents(8) // 稍微多加载几个以填充左侧
    } else {
      const data = await getRiskEventStatistics()
      recentAlerts.value = data?.recent_alerts || []
    }
  } finally { alertLoading.value = false }
}

const fetchLastSyncTime = async () => {
  if (DEMO_MODE) {
    lastSyncTime.value = new Date().toISOString()
    return
  }
  try {
    const response = await request.get('/robots/last_sync_time/')
    lastSyncTime.value = response?.last_sync_time || null
  } catch (error) {
    console.error('获取同步时间失败:', error)
    lastSyncTime.value = null
  }
}

// 加载机器人连接状态统计
const loadConnectionStats = async () => {
  connectionLoading.value = true
  try {
    if (DEMO_MODE) {
      // 模拟数据
      connectionStats.value = {
        total: 156,
        highRisk: 14
      }
      overallTotal.value = 156
    } else {
      // 使用专门的统计接口
      const data = await getRobotStatsSummary()
      connectionStats.value = {
        total: data.total || 0,
        highRisk: data.high_risk || 0
      }
      overallTotal.value = data?.total ?? null
    }
  } catch (error) {
    console.error('加载连接状态失败:', error)
    connectionStats.value = {
      total: 0,
      highRisk: 0
    }
  } finally {
    connectionLoading.value = false
  }
}

const handleRefresh = async () => {
  await Promise.all([loadGroupsData(), loadAlerts(), fetchLastSyncTime(), loadConnectionStats()])
  renderMainPieChart()
  renderWorkshopCharts()
}

onMounted(async () => {
  await Promise.all([loadGroupsData(), loadAlerts(), fetchLastSyncTime(), loadConnectionStats()])

  nextTick(() => {
    renderMainPieChart()
    renderWorkshopCharts()
  })
  window.addEventListener('resize', () => chartInstances.forEach(c => c.resize()))
})

onBeforeUnmount(() => chartInstances.forEach(c => c.dispose()))
watch(groupRows, () => {
  renderMainPieChart()
  renderWorkshopCharts()
}, { deep: true })
</script>

<style scoped>
/* === 核心布局重构 === */
.layout-wrapper {
  padding: 24px 32px;
  max-width: 1600px;
  margin: 0 auto;
  min-height: 100vh;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.page-header {
  flex-shrink: 0; /* 防止头部压缩 */
}

/* 主容器：Flex 布局，左侧固定宽，右侧自适应 */
.dashboard-content {
  flex: 1;
  display: flex;
  gap: 24px;
  min-height: 0; /* 关键：允许子元素滚动或收缩 */
  padding-bottom: 20px;
}

/* 左侧面板 */
.left-panel {
  width: 360px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.main-chart-card {
  flex: 0 0 240px;
  display: flex;
  flex-direction: column;
}

.main-chart-box {
  flex: 1;
  width: 100%;
  min-height: 0;
}

/* 连接状态面板 */
.connection-panel {
  flex: 0 0 180px;
  display: flex;
  flex-direction: column;
  min-height: 180px;
}

.connection-stats {
  flex: 1;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
}

.connection-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.connection-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.2);
}

.connection-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
}

.connection-label {
  font-size: 11px;
  color: #8899aa;
}

.connection-count {
  font-size: 14px;
  font-weight: 700;
  font-family: 'SF Mono', 'Monaco', monospace;
}

.connection-item.total .connection-count {
  color: #00c3ff;
  text-shadow: 0 0 8px rgba(0, 195, 255, 0.4);
}

.connection-item.high-risk .connection-count {
  color: #ef4444;
  text-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
}

.dot-total {
  background: #00c3ff;
  box-shadow: 0 0 6px #00c3ff;
}

.dot-high-risk {
  background: #ef4444;
  box-shadow: 0 0 6px #ef4444;
}

.feed-panel {
  flex: 1 1 auto;
  min-height: 200px;
  display: flex;
  flex-direction: column;
}

/* 右侧面板 */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 12宫格布局 */
.workshop-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr); /* 4 列 */
  grid-template-rows: repeat(3, 1fr);    /* 3 行 */
  gap: 16px;
  height: 100%;
}

/* 车间卡片优化 */
.workshop-card {
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: transform 0.2s;
}

.workshop-card:hover {
  transform: translateY(-4px);
  background: rgba(255, 255, 255, 0.06);
}

.workshop-content {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 0 16px 10px;
}

.workshop-chart-wrapper {
  width: 90px;
  height: 90px;
  flex-shrink: 0;
}

.workshop-mini-chart {
  width: 100%;
  height: 100%;
}

.workshop-data-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-left: 12px;
}

.mini-stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(0, 0, 0, 0.2);
  padding: 6px 10px;
  border-radius: 6px;
}

.mini-stat-row label {
  font-size: 10px;
  color: #8899aa;
}

.mini-stat-row .value {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  font-family: 'SF Mono', monospace;
}

.mini-stat-row .value.has-risk {
  color: #ff4d4f;
  text-shadow: 0 0 8px rgba(255, 77, 79, 0.6);
}

.mini-stat-row .value.normal {
  color: #00c3ff;
}

/* 头部样式微调 */
.cell-header.compact {
  padding: 12px 16px;
  font-size: 12px;
}

.accent-bar.small { width: 3px; height: 12px; }
.accent-bar.blue { background: #00c3ff; box-shadow: 0 0 10px #00c3ff; }
.accent-bar.risk { background: #ff4d4f; box-shadow: 0 0 10px #ff4d4f; }
.accent-bar.safe { background: #00c3ff; box-shadow: 0 0 10px #00c3ff; }
.accent-bar.purple { background: #a855f7; box-shadow: 0 0 10px #a855f7; }

/* 日志流样式优化 */
.log-stream {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.log-stream::-webkit-scrollbar {
  width: 4px;
}
.log-stream::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.log-row {
  align-items: flex-start;
  padding: 12px;
  background: rgba(0,0,0,0.15);
  margin-bottom: 8px;
}

.log-tag { margin-top: 5px; }

.log-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.log-info p {
  font-size: 12px;
  line-height: 1.4;
  color: #e0e6ed;
  margin: 0;
}

.log-time {
  font-size: 10px;
  color: #5c6b7f;
}

/* 媒体查询：适配小屏幕 */
@media (max-width: 1400px) {
  .left-panel { width: 300px; }
}

@media (max-width: 1200px) {
  .dashboard-content { flex-direction: column; overflow-y: auto; }
  .left-panel { width: 100%; height: 400px; flex-direction: row; }
  .right-panel { height: auto; }
  .workshop-grid {
    grid-template-columns: repeat(4, 1fr);
    height: auto;
    grid-auto-rows: 140px; /* 固定高度 */
  }
}

/* === 背景与环境样式 === */
.dashboard-viewport { background: #030508; min-height: 100vh; position: relative; overflow-y: auto; color: #fff; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
.ambient-background { position: absolute; inset: 0; pointer-events: none; }
.nebula { position: absolute; width: 80vw; height: 70vh; filter: blur(120px); opacity: 0.28; mix-blend-mode: screen; }
.nebula.blue { background: radial-gradient(circle, #0066ff, transparent 75%); top: -10%; left: -5%; }
.nebula.gold { background: radial-gradient(circle, #ffaa00, transparent 75%); bottom: -10%; right: -5%; }
.breathing-line { position: absolute; height: 1px; background: linear-gradient(90deg, transparent, #ffaa00, transparent); filter: blur(1px); opacity: 0.3; animation: breathe 8s infinite ease-in-out; }
.gold-1 { width: 100%; top: 30%; left: -50%; transform: rotate(-5deg); }
.gold-2 { width: 100%; bottom: 20%; right: -50%; transform: rotate(3deg); animation-delay: -4s; }
.scan-grid { position: absolute; inset: 0; background-image: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px); background-size: 50px 50px; mask-image: linear-gradient(to bottom, black, transparent); animation: gridMove 25s linear infinite; }
@keyframes gridMove { from { background-position: 0 0; } to { background-position: 0 50px; } }
@keyframes breathe { 0%, 100% { opacity: 0.1; transform: scaleX(0.8) translateY(0); } 50% { opacity: 0.5; transform: scaleX(1.2) translateY(-20px); } }

/* === iOS 玻璃卡片样式 === */
.ios-glass { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(50px) saturate(180%); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; position: relative; overflow: hidden; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8); }
.border-glow { position: absolute; inset: 0; border-radius: 20px; padding: 1px; background: linear-gradient(135deg, rgba(255, 170, 0, 0.4), transparent 40%, rgba(255, 170, 0, 0.1)); mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); mask-composite: exclude; animation: borderBreathe 6s infinite ease-in-out; }
.border-glow.blue-tint { background: linear-gradient(135deg, rgba(0, 195, 255, 0.55), transparent 45%, rgba(0, 195, 255, 0.15)); }
.border-glow.purple-tint { background: linear-gradient(135deg, rgba(168, 85, 247, 0.55), transparent 45%, rgba(168, 85, 247, 0.15)); }
@keyframes borderBreathe { 0%, 100% { opacity: 0.3; } 50% { opacity: 0.8; box-shadow: inset 0 0 15px rgba(255, 170, 0, 0.2); } }

/* === 标题与按钮样式 === */
.ios-title { font-size: 32px; letter-spacing: -0.5px; background: linear-gradient(180deg, #fff 40%, rgba(255,255,255,0.6)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
.ios-title .subtitle { font-size: 14px; color: #ffaa00; margin-left: 10px; font-weight: 300; letter-spacing: 2px; display: block; margin-top: 4px; }
.ios-title small { font-size: 14px; color: #ffaa00; margin-left: 10px; font-weight: 300; letter-spacing: 2px; }
.status-tag { background: rgba(255, 255, 255, 0.05); padding: 4px 12px; border-radius: 100px; display: inline-flex; align-items: center; gap: 8px; font-size: 11px; color: #a0aec0; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: #00ffcc; box-shadow: 0 0 10px rgba(0, 255, 204, 0.8); }
.pulse { animation: pulseDot 2s ease-in-out infinite; }
@keyframes pulseDot { 0%, 100% { transform: scale(1); opacity: 0.8; } 50% { transform: scale(1.5); opacity: 1; } }
.ios-btn { background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.12); color: #fff; border-radius: 999px; padding: 6px 14px; }
.ios-btn:hover { background: rgba(255, 255, 255, 0.12); }
.page-header { display: flex; justify-content: space-between; align-items: flex-end; padding-bottom: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 0; }
.title-group { display: flex; flex-direction: column; gap: 6px; }
.cell-header { padding: 12px 15px; font-size: 12px; color: #c0ccda; font-weight: bold; border-bottom: 1px solid rgba(255, 255, 255, 0.06); letter-spacing: 1px; display: flex; align-items: center; gap: 10px; }
.accent-bar { width: 4px; height: 16px; background: #ffaa00; border-radius: 10px; box-shadow: 0 0 10px #ffaa00; }

/* 覆盖通用 dot 的绿色，确保高风险点为红色 */
.connection-item.high-risk .dot {
  background: #ef4444;
  box-shadow: 0 0 6px #ef4444;
}

/* 日志流标签样式 */
.log-tag { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.log-tag.critical { background: #ff4444; box-shadow: 0 0 8px #ff4444; }
.log-tag.high { background: #ffaa00; box-shadow: 0 0 8px #ffaa00; }
.log-tag.medium { background: #00c3ff; box-shadow: 0 0 8px #00c3ff; }
.log-tag.low { background: #00ffcc; }
.loading-state, .no-data { text-align: center; padding: 40px 0; color: #8899aa; font-size: 12px; }

/* === 入场动画类 === */
.entrance-slide-in { animation: slideInFade 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards; opacity: 0; transform: translateX(-40px); }
@keyframes slideInFade { to { opacity: 1; transform: translateX(0); } }

.entrance-scale-up { animation: scaleUpFade 0.9s cubic-bezier(0.16, 1, 0.3, 1) 0.2s forwards; opacity: 0; transform: scale(0.92) translateY(30px); }
.entrance-scale-up-delay-1 { animation: scaleUpFade 0.9s cubic-bezier(0.16, 1, 0.3, 1) 0.35s forwards; opacity: 0; transform: scale(0.92) translateY(30px); }
.entrance-scale-up-delay-2 { animation: scaleUpFade 0.9s cubic-bezier(0.16, 1, 0.3, 1) 0.5s forwards; opacity: 0; transform: scale(0.92) translateY(30px); }
@keyframes scaleUpFade { to { opacity: 1; transform: scale(1) translateY(0); } }

.entrance-border-glow { animation: borderBreathe 6s infinite ease-in-out, borderGlowEnter 1.2s ease-out forwards; opacity: 0; }
@keyframes borderGlowEnter { 0% { opacity: 0; transform: scale(0.95); } 50% { opacity: 0.6; } 100% { opacity: 0.3; transform: scale(1); } }
.entrance-chart-fade { animation: chartFadeIn 1s cubic-bezier(0.16, 1, 0.3, 1) 0.6s forwards; opacity: 0; transform: scale(0.95); }
@keyframes chartFadeIn { to { opacity: 1; transform: scale(1); } }
.entrance-content-fade { animation: contentFadeIn 0.8s ease-out 0.8s forwards; opacity: 0; }
@keyframes contentFadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>

<!-- 非 scoped 样式：弹窗样式 -->
<style>
/* === 弹窗统计摘要样式（横条式） === */
.dialog-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 20px;
  border-radius: 12px;
  background: rgba(0, 102, 255, 0.06);
  border: 1px solid rgba(0, 204, 255, 0.12);
  margin-bottom: 16px;
}

.summary-row {
  display: flex;
  align-items: center;
  gap: 20px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 180px;
}

.summary-label {
  font-size: 11px;
  color: #8899aa;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.summary-value {
  font-size: 24px;
  font-weight: 800;
  color: #fff;
  font-family: 'SF Mono', 'Monaco', monospace;
}

.summary-value.primary {
  color: #ff4d4f;
  text-shadow: 0 0 15px rgba(255, 77, 79, 0.6);
}

.summary-value.time {
  font-size: 16px;
  color: #00ccff;
  text-shadow: 0 0 10px rgba(0, 204, 255, 0.4);
}

.summary-progress {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-bar::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  animation: progressShine 2s infinite;
}

@keyframes progressShine {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6b6b, #ff4d4f, #cc0000);
  border-radius: 4px;
  box-shadow: 0 0 10px rgba(255, 77, 79, 0.5);
  transition: width 0.5s ease-out;
  position: relative;
}

.progress-text {
  font-size: 14px;
  font-weight: 700;
  color: #ff4d4f;
  font-family: 'SF Mono', 'Monaco', monospace;
  min-width: 50px;
  text-align: right;
}

/* === 弹窗容器样式 === */
.el-dialog.premium-dialog {
  background: rgba(15, 20, 35, 0.88) !important;
  border: 1px solid rgba(0, 204, 255, 0.25) !important;
  box-shadow: 0 0 40px rgba(0, 204, 255, 0.15), 0 20px 50px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
  backdrop-filter: blur(30px) !important;
  border-radius: 16px !important;
}

/* === 弹窗标题样式 === */
.dialog-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dialog-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #e9f0ff;
}

.dialog-chip {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #6dd5ff, #1e66ff);
  box-shadow: 0 0 10px rgba(0, 195, 255, 0.35);
}

.dialog-subtitle {
  font-size: 10px;
  letter-spacing: 1.6px;
  color: #6f7f97;
}

/* === 弹窗空状态样式 === */
.dialog-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 30px 0;
  color: #666;
  font-size: 12px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}

.empty-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00ccff;
  box-shadow: 0 0 15px rgba(0, 204, 255, 0.6);
  animation: emptyPulse 2s ease-in-out infinite;
}

@keyframes emptyPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
}

.el-dialog.premium-dialog::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(0, 204, 255, 0.6), rgba(0, 102, 255, 0.8), rgba(0, 204, 255, 0.6), transparent);
  box-shadow: 0 0 15px rgba(0, 204, 255, 0.5);
}

.el-dialog.premium-dialog .el-dialog__header {
  margin-right: 0;
  padding: 20px 28px 16px;
  border-bottom: 1px solid rgba(0, 204, 255, 0.12);
}

.el-dialog.premium-dialog .el-dialog__title {
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 1px;
}

.el-dialog.premium-dialog .el-dialog__body {
  padding: 20px 28px 28px;
  color: #aaa;
}

.el-dialog.premium-dialog .el-dialog__close {
  color: #00ccff;
  font-size: 20px;
  transition: all 0.3s ease;
}

.el-dialog.premium-dialog .el-dialog__close:hover {
  color: #fff;
  text-shadow: 0 0 10px rgba(0, 204, 255, 0.8);
}

/* === 表格样式 === */
.el-table.premium-table {
  --el-table-bg-color: transparent !important;
  --el-table-tr-bg-color: rgba(20, 30, 50, 0.4) !important;
  --el-table-row-hover-bg-color: rgba(0, 204, 255, 0.12) !important;
  --el-table-header-bg-color: rgba(0, 102, 255, 0.15) !important;
  --el-table-border-color: rgba(0, 204, 255, 0.1) !important;
  color: #e0e8f5 !important;
  background: transparent !important;
}

.el-table.premium-table .el-table__inner-wrapper { background: transparent !important; }
.el-table.premium-table .el-table__header-wrapper { background: transparent !important; }

.el-table.premium-table .el-table__header th {
  background: rgba(0, 102, 255, 0.18) !important;
  border-color: rgba(0, 204, 255, 0.15) !important;
  color: #00ccff !important;
  font-size: 11px;
  letter-spacing: 1.5px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 14px 0;
}

.el-table.premium-table .el-table__header th .cell { padding: 0 12px; }
.el-table.premium-table .el-table__body-wrapper { background: transparent !important; }

.el-table.premium-table .el-table__body tr {
  background: rgba(20, 30, 50, 0.35) !important;
  transition: all 0.25s ease;
}

.el-table.premium-table .el-table__body tr.el-table__row--striped {
  background: rgba(30, 45, 70, 0.4) !important;
}

.el-table.premium-table .el-table__body td {
  border-bottom: 1px solid rgba(0, 204, 255, 0.08) !important;
  background-color: transparent !important;
  color: #d0d8e8 !important;
  padding: 12px 0;
}

.el-table.premium-table .el-table__body td .cell { padding: 0 12px; }
.el-table.premium-table .el-table__row:hover td { background: rgba(0, 204, 255, 0.12) !important; color: #fff !important; }
.el-table.premium-table .el-table__row.current-row td { background: rgba(0, 204, 255, 0.18) !important; }
.el-table.premium-table .el-table__empty-block { background: transparent !important; }
.el-table.premium-table .el-table__empty-text { color: #666 !important; }
.el-table.premium-table .el-loading-mask { background: rgba(15, 20, 35, 0.7) !important; }
</style>
