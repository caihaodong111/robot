<template>
  <div class="dashboard-viewport">
    <div class="space-ambient">
      <div class="star-field"></div>
      <div class="nebula blue"></div> 
      <div class="nebula gold"></div>
      <div class="scan-grid"></div>
    </div>

    <div class="layout-wrapper">
      <header class="page-header">
        <h1 class="metallic-title">平台概览 <span>MONITORING PLATFORM</span></h1>
        <div class="system-status">
          <span class="pulse-line"></span>
          系统运行中 | {{ lastUpdateTime }}
        </div>
      </header>

      <section class="metrics-grid">
        <div class="data-cell glass-card main-chart-card">
          <div class="card-glow-track"></div>
          <div class="cell-header">
            <span class="decor-corner"></span>
            高风险机器人分布 (HIGH RISK DISTRIBUTION)
          </div>
          <div ref="chartRef" class="main-chart-box"></div>
        </div>

        <div class="data-cell glass-card dev-card" v-for="i in 3" :key="i">
          <div class="card-glow-track"></div>
          <div class="cell-header">
            <span class="decor-corner gray"></span>
            模块_0{{ i }}_数据流监控
          </div>
          <div class="dev-placeholder">
            <div class="dev-text">
              <div class="dev-icon">⚙</div>
              <div class="dev-label">开发中</div>
              <div class="dev-sub">MODULE UNDER DEVELOPMENT</div>
            </div>
            <div class="dev-grid"></div>
          </div>
        </div>
      </section>

      <footer class="footer-layout">
        <div class="glass-card trend-panel">
          <div class="cell-header">运行脉搏 (OPERATIONAL PULSE)</div>
          <div ref="statusChartRef" class="mini-chart"></div>
        </div>
        <div class="glass-card feed-panel">
          <div class="cell-header">实时预警日志 (LIVE ALERTS)</div>
          <div class="log-stream">
            <div v-if="alertLoading" class="loading-state">载入中...</div>
            <template v-else-if="recentAlerts.length">
              <div v-for="alert in recentAlerts.slice(0, 5)" :key="alert.id" class="log-row">
                <span class="log-tag" :class="alert.severity"></span>
                <p>{{ alert.message || alert.robot_name }}</p>
                <span class="log-time">{{ formatTimeOnly(alert.triggered_at) }}</span>
              </div>
            </template>
            <div v-else class="no-data">当前无风险事件</div>
          </div>
        </div>
      </footer>
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
          <div class="summary-metric">
            <div class="summary-label">记录数量</div>
            <div class="summary-value">{{ detailRows.length }}</div>
          </div>
          <div class="summary-divider"></div>
          <div class="summary-metric">
            <div class="summary-label">数据刷新</div>
            <div class="summary-value">{{ lastUpdateTime }}</div>
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
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { DEMO_MODE } from '@/config/appConfig'
import { getRobotComponents, getRobotGroups, getRiskEventStatistics } from '@/api/robots'
import { createRiskEvents, getGroupStats, getRobotsByGroup, robotGroups as mockGroups } from '@/mock/robots'

const loading = ref(false)
const alertLoading = ref(false)
const groupsData = ref([])
const recentAlerts = ref([])
const lastUpdateTime = ref(new Date().toLocaleTimeString())

// 加载机器人组数据
const loadGroupsData = async () => {
  loading.value = true
  try {
    if (DEMO_MODE) {
      // 演示模式使用 mock 数据
      groupsData.value = mockGroups.map(group => ({
        key: group.key,
        name: group.name,
        stats: getGroupStats(group.key)
      }))
    } else {
      // 生产模式调用真实 API
      const response = await getRobotGroups()
      groupsData.value = response || []
    }
  } catch (error) {
    console.error('加载机器人组数据失败:', error)
    ElMessage.error('加载数据失败')
    groupsData.value = []
  } finally {
    loading.value = false
    lastUpdateTime.value = new Date().toLocaleTimeString()
  }
}

const chartRef = ref(null)
const statusChartRef = ref(null)
const chartInstances = new Map()

const detailVisible = ref(false)
const detailTitle = ref('')
const detailRows = ref([])
const detailLoading = ref(false)

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

// 显示组详情弹窗
const showGroupDetail = async (groupKey, groupName) => {
  detailVisible.value = true
  detailTitle.value = `${groupName} - 高风险机器人列表`
  detailLoading.value = true
  detailRows.value = []

  try {
    if (DEMO_MODE) {
      // 演示模式使用 mock 数据，过滤高风险机器人
      const robots = getRobotsByGroup(groupKey)
      detailRows.value = robots
        .filter(r => r.isHighRisk)
        .map(r => ({
          name: r.name,
          level: r.level,
          referenceNo: r.referenceNo,
          remark: r.remark
        }))
    } else {
      // 生产模式调用真实 API
      const response = await getRobotComponents({ group: groupKey, tab: 'highRisk' })
      const data = response?.results || response || []
      detailRows.value = data.map(r => ({
        name: r.name || r.robot_id,
        level: r.level,
        referenceNo: r.referenceNo,
        remark: r.remark
      }))
    }
  } catch (error) {
    console.error('加载组详情失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    detailLoading.value = false
  }
}

// === 核心优化：渲染自然配色的饼图 ===
const renderMainPieChart = () => {
  const chart = initChart('main', chartRef.value)
  if (!chart) return

  const rows = groupRows.value.slice(0, 4)
  const totalHighRisk = rows.reduce((sum, row) => sum + (row.stats?.highRisk || 0), 0)

  // 提取自海报的流光配色：增加明度，使用渐变映射
  const colorSchemes = [
    { grad: ['#00f2ff', '#0066ff'], glow: 'rgba(0, 242, 255, 0.6)' }, // 科技蓝
    { grad: ['#ffcc00', '#ff6600'], glow: 'rgba(255, 204, 0, 0.6)' }, // 晨曦金
    { grad: ['#00ffa3', '#008a5c'], glow: 'rgba(0, 255, 163, 0.6)' }, // 运行绿
    { grad: ['#ffffff', '#636e72'], glow: 'rgba(255, 255, 255, 0.3)' } // 钛合金
  ]

  const pieData = rows.map((row, index) => {
    const scheme = colorSchemes[index % colorSchemes.length]
    return {
      value: row.stats?.highRisk || 0,
      name: row.name,
      itemStyle: {
        borderRadius: 12, // 圆角处理更自然
        color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
          { offset: 0, color: scheme.grad[0] },
          { offset: 1, color: scheme.grad[1] }
        ]),
        borderColor: 'rgba(255,255,255,0.2)',
        borderWidth: 2,
        shadowBlur: 20,
        shadowColor: scheme.glow
      }
    }
  })

  chart.setOption({
    series: [
      {
        type: 'pie',
        radius: ['45%', '78%'],
        roseType: 'radius', // 玫瑰图模式，错落感更强
        padAngle: 5, // 扇区间隔，增加空气感
        itemStyle: { borderRadius: 10 },
        label: { show: false },
        data: pieData
      },
      // 中心装饰
      {
        type: 'pie',
        radius: [0, '35%'],
        silent: true,
        label: {
          show: true,
          position: 'center',
          formatter: () => [`{v|${totalHighRisk}}`, `{l|高风险总数}`].join('\n'),
          rich: {
            v: { fontSize: 32, fontWeight: 900, color: '#ffcc00', textShadow: '0 0 20px rgba(255, 204, 0, 0.8)' },
            l: { fontSize: 11, color: '#8899aa', paddingTop: 5 }
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

  // 点击饼图板块弹出详情
  chart.off('click')
  chart.on('click', (params) => {
    if (params.componentType === 'series' && params.seriesIndex === 0) {
      const group = rows.find(r => r.name === params.name)
      if (group) {
        showGroupDetail(group.key, group.name)
      }
    }
  })
}

// 渲染状态条形图
const renderStatusChart = () => {
  const chart = initChart('status', statusChartRef.value)
  if (!chart) return
  const rows = groupRows.value
  
  chart.setOption({
    grid: { left: '3%', right: '4%', top: '15%', bottom: '5%', containLabel: true },
    xAxis: { 
      type: 'category', 
      data: rows.map(r => r.name),
      axisLabel: { color: '#8899aa', fontSize: 10 }
    },
    yAxis: { 
      type: 'value', 
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
      axisLabel: { color: '#8899aa' }
    },
    series: [{
      type: 'bar',
      barWidth: '35%',
      data: rows.map(r => r.stats?.online || 0),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#00ffcc' },
          { offset: 1, color: 'rgba(0, 255, 204, 0.1)' }
        ]),
        borderRadius: [4, 4, 0, 0]
      }
    }]
  })
}

const loadAlerts = async () => {
  alertLoading.value = true
  try {
    if (DEMO_MODE) {
      recentAlerts.value = createRiskEvents(8).slice(0, 5)
    } else {
      const data = await getRiskEventStatistics()
      recentAlerts.value = data?.recent_alerts || []
    }
  } finally { alertLoading.value = false }
}

onMounted(async () => {
  // 先加载数据，再渲染图表
  await Promise.all([loadGroupsData(), loadAlerts()])
  renderMainPieChart()
  renderStatusChart()
  window.addEventListener('resize', () => chartInstances.forEach(c => c.resize()))
})

onBeforeUnmount(() => chartInstances.forEach(c => c.dispose()))
watch(groupRows, () => {
  renderMainPieChart()
  renderStatusChart()
}, { deep: true })
</script>

<style scoped>
/* === 调亮全域环境 === */
.dashboard-viewport {
  background: radial-gradient(circle at 50% 35%, #0d1a2d 0%, #030508 100%);
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  color: #ffffff;
}

.space-ambient { position: absolute; inset: 0; pointer-events: none; }

/* 调亮星云，实现背景补光 */
.nebula {
  position: absolute; width: 80vw; height: 70vh;
  filter: blur(120px); opacity: 0.28; mix-blend-mode: screen;
}
.nebula.blue { background: radial-gradient(circle, #0066ff, transparent 75%); top: -10%; left: -5%; }
.nebula.gold { background: radial-gradient(circle, #ffaa00, transparent 75%); bottom: -10%; right: -5%; }

.layout-wrapper { position: relative; z-index: 1; padding: 40px; max-width: 1600px; margin: 0 auto; }

/* 标题：提升金属反光亮度 */
.metallic-title {
  font-size: 36px; font-weight: 900; letter-spacing: 5px;
  background: linear-gradient(180deg, #ffffff 30%, #a0a0a0 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  text-shadow: 0 0 40px rgba(0, 195, 255, 0.5);
  margin-bottom: 8px;
}
.metallic-title span { font-size: 14px; color: #636e72; margin-left: 15px; letter-spacing: 2px; }

/* 辅助文字调亮 */
.system-status { font-size: 11px; color: #a0aec0; letter-spacing: 2px; display: flex; align-items: center; gap: 15px; }
.pulse-line { width: 30px; height: 2px; background: #00ffcc; box-shadow: 0 0 10px #00ffcc; }

/* 面板：强化毛玻璃通透感 */
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(40px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 4px; padding: 0;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  transition: all 0.4s ease;
}
.glass-card:hover { transform: translateY(-5px); border-color: #00c3ff; background: rgba(255, 255, 255, 0.08); }

.cell-header {
  padding: 15px; font-size: 11px; color: #c0ccda; font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05); letter-spacing: 1px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(240px, 1fr));
  gap: 18px;
  margin-top: 24px;
}
.main-chart-box { height: 240px; width: 100%; }

/* 日志流文字调亮 */
.log-row p { color: #f5f6fa; flex: 1; margin: 0; font-size: 12px; }
.log-time { color: #8899aa; font-size: 10px; }

.footer-layout { display: grid; grid-template-columns: 2fr 1fr; gap: 30px; margin-top: 30px; }
.mini-chart { height: 200px; width: 100%; }

/* === 弹窗内部内容样式（scoped 可以作用） === */
.dialog-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
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

/* === 弹窗内部内容样式（赛博朋克科技风格） === */
.dialog-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 统计摘要区域 */
.dialog-summary {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  border-radius: 10px;
  background: rgba(0, 102, 255, 0.08);
  border: 1px solid rgba(0, 204, 255, 0.15);
  box-shadow: inset 0 1px 0 rgba(0, 204, 255, 0.1);
}

.summary-metric {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.summary-label {
  font-size: 10px;
  color: #00ccff;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  font-weight: 600;
}

.summary-value {
  font-size: 16px;
  font-weight: 800;
  color: #fff;
  text-shadow: 0 0 15px rgba(0, 204, 255, 0.3);
}

.summary-value.accent {
  color: #ffae00;
  text-shadow: 0 0 15px rgba(255, 174, 0, 0.4);
}

.summary-divider {
  width: 1px;
  height: 32px;
  background: linear-gradient(to bottom,
    transparent,
    rgba(0, 204, 255, 0.3),
    transparent
  );
}

/* 空状态样式 */
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
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.2);
  }
}

/* 星空背景 */
.star-field {
  position: absolute; inset: 0;
  background-image: radial-gradient(2px 2px at 20% 30%, rgba(255,255,255,0.3), transparent),
                    radial-gradient(2px 2px at 60% 70%, rgba(255,255,255,0.2), transparent),
                    radial-gradient(1px 1px at 50% 50%, rgba(255,255,255,0.4), transparent),
                    radial-gradient(1px 1px at 80% 10%, rgba(255,255,255,0.3), transparent);
  background-size: 200% 200%;
  animation: twinkle 8s ease-in-out infinite;
}
@keyframes twinkle { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }

/* 装饰角落 */
.decor-corner {
  display: inline-block; width: 8px; height: 8px;
  background: linear-gradient(135deg, #00c3ff, transparent);
  margin-right: 8px;
}
.decor-corner.gray { background: linear-gradient(135deg, #636e72, transparent); }

/* 卡片光晕轨道 */
.card-glow-track {
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 195, 255, 0.5), transparent);
}

/* 开发中卡片 */
.dev-card {
  grid-column: span 1;
  min-height: 280px;
  display: flex; flex-direction: column;
}
.dev-placeholder {
  flex: 1; display: flex; align-items: center; justify-content: center;
  position: relative;
}
.dev-text {
  text-align: center; z-index: 1;
}
.dev-icon {
  font-size: 32px; color: #636e72; margin-bottom: 12px;
  animation: rotate 8s linear infinite;
}
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.dev-label {
  font-size: 14px; color: #8899aa; font-weight: bold; margin-bottom: 4px;
}
.dev-sub {
  font-size: 10px; color: #5a6a7a; letter-spacing: 1px;
}
.dev-grid {
  position: absolute; inset: 0; opacity: 0.1;
  background-image: linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px);
  background-size: 20px 20px;
}

/* 底部面板 */
.trend-panel, .feed-panel { padding: 0; }
.log-stream { padding: 12px; max-height: 200px; overflow-y: auto; }
.loading-state {
  text-align: center; padding: 40px 0; color: #8899aa; font-size: 12px;
}
.no-data {
  text-align: center; padding: 40px 0; color: #5a6a7a; font-size: 12px;
}
.log-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; margin-bottom: 8px;
  background: rgba(0, 0, 0, 0.2); border-radius: 4px;
}
.log-tag {
  width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
}
.log-tag.critical { background: #ff4444; box-shadow: 0 0 8px #ff4444; }
.log-tag.high { background: #ffaa00; box-shadow: 0 0 8px #ffaa00; }
.log-tag.medium { background: #00c3ff; box-shadow: 0 0 8px #00c3ff; }
.log-tag.low { background: #00ffcc; }

/* 页面头部 */
.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px; padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

/* 扫描线动画 */
.scan-grid {
  position: absolute; inset: 0;
  background-image: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 50px 50px; mask-image: linear-gradient(to bottom, black, transparent);
  animation: gridMove 25s linear infinite;
}
@keyframes gridMove { from { background-position: 0 0; } to { background-position: 0 50px; } }

</style>

<!-- 非 scoped 样式：用于覆盖弹窗（挂载到 body 下）的 Element Plus 默认样式 -->
<style>
/* === 弹窗容器样式（赛博朋克科技发布会风格） === */
.el-dialog.premium-dialog {
  background: rgba(15, 20, 35, 0.88) !important;
  border: 1px solid rgba(0, 204, 255, 0.25) !important;
  box-shadow:
    0 0 40px rgba(0, 204, 255, 0.15),
    0 20px 50px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
  backdrop-filter: blur(30px) !important;
  border-radius: 16px !important;
}

/* 弹窗顶部青色光晕装饰 */
.el-dialog.premium-dialog::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 2px;
  background: linear-gradient(90deg,
    transparent,
    rgba(0, 204, 255, 0.6),
    rgba(0, 102, 255, 0.8),
    rgba(0, 204, 255, 0.6),
    transparent
  );
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

/* === 表格样式（科技风格，背景调亮） === */
.el-table.premium-table {
  --el-table-bg-color: transparent !important;
  --el-table-tr-bg-color: rgba(20, 30, 50, 0.4) !important;
  --el-table-row-hover-bg-color: rgba(0, 204, 255, 0.12) !important;
  --el-table-header-bg-color: rgba(0, 102, 255, 0.15) !important;
  --el-table-border-color: rgba(0, 204, 255, 0.1) !important;
  color: #e0e8f5 !important;
  background: transparent !important;
}

.el-table.premium-table .el-table__inner-wrapper {
  background: transparent !important;
}

/* 表头样式 */
.el-table.premium-table .el-table__header-wrapper {
  background: transparent !important;
}

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

.el-table.premium-table .el-table__header th .cell {
  padding: 0 12px;
}

/* 表格主体样式 */
.el-table.premium-table .el-table__body-wrapper {
  background: transparent !important;
}

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

.el-table.premium-table .el-table__body td .cell {
  padding: 0 12px;
}

/* 悬停效果 */
.el-table.premium-table .el-table__row:hover td {
  background: rgba(0, 204, 255, 0.12) !important;
  color: #fff !important;
}

.el-table.premium-table .el-table__row.current-row td {
  background: rgba(0, 204, 255, 0.18) !important;
}

/* 空状态样式 */
.el-table.premium-table .el-table__empty-block {
  background: transparent !important;
}

.el-table.premium-table .el-table__empty-text {
  color: #666 !important;
}

/* 加载遮罩 */
.el-table.premium-table .el-loading-mask {
  background: rgba(15, 20, 35, 0.7) !important;
}

/* 固定列样式 */
.el-table.premium-table .el-table-fixed-column--right,
.el-table.premium-table .el-table-fixed--right .el-table__fixed-body-wrapper {
  background: rgba(15, 20, 35, 0.88) !important;
}
</style>
