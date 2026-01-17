<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card stat-primary">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Cpu /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">部件总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card stat-success">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.highRisk }}</div>
              <div class="stat-label">高风险（Level H）</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card stat-warning">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Bell /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.historyHighRisk }}</div>
              <div class="stat-label">历史高风险（有记录）</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card stat-info">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><DataLine /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.marked }}</div>
              <div class="stat-label">已标记（mark≠0）</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="24">
        <el-card v-loading="loading">
          <template #header>
            <span>组别风险占比</span>
          </template>
          <div v-if="groupRows.length" class="group-pie-grid">
            <div
              v-for="row in groupRows"
              :key="row.key || row.name"
              class="group-pie-item"
              :class="{ 'is-active': activeGroupKey && (row.key || row.name) === activeGroupKey }"
              @click="activateGroup(row.key || row.name)"
            >
              <div class="group-pie-title">{{ row.name }}</div>
              <div class="group-pie-chart" :ref="(el) => setGroupPieRef(row.key || row.name, el)"></div>
              <div class="group-pie-meta">
                高风险 {{ row.highRisk }} / {{ row.total }}
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无组别数据" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 各组高风险设备板块（与饼图联动） -->
    <el-row :gutter="20" class="data-row">
      <el-col :span="24">
        <el-card v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>高风险设备（按组）</span>
              <span class="card-header-hint">点击上方饼图或组卡片可联动定位</span>
            </div>
          </template>
          <div v-if="groupHighRiskRows.length" class="group-risk-board">
            <div
              v-for="row in groupHighRiskRows"
              :key="row.key || row.name"
              class="group-risk-card"
              :class="{ 'is-active': activeGroupKey && (row.key || row.name) === activeGroupKey }"
              :ref="(el) => setGroupCardRef(row.key || row.name, el)"
              @click="activateGroup(row.key || row.name)"
            >
              <div class="group-risk-card-header">
                <div class="group-risk-title">{{ row.name }}</div>
                <div class="group-risk-meta">
                  <span class="group-risk-meta-item">当前 {{ row.total ?? 0 }}</span>
                  <span class="group-risk-meta-item danger">高风险 {{ row.highRisk ?? 0 }}</span>
                </div>
              </div>
              <div class="group-risk-card-body">
                <el-empty v-if="!row.highRiskDevices?.length" description="暂无高风险设备" />
                <el-table v-else :data="row.highRiskDevices" stripe size="small" class="group-risk-table" height="260">
                  <el-table-column type="index" label="#" width="56" align="center" />
                  <el-table-column prop="name" label="设备名称" min-width="220" show-overflow-tooltip />
                </el-table>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无组别数据" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近更新部件 -->
    <el-row :gutter="20" class="data-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>最近更新部件</span>
          </template>
          <el-table :data="recentRows" stripe v-loading="loading" height="360">
            <el-table-column prop="partNo" label="Robot" width="190" show-overflow-tooltip />
            <el-table-column prop="referenceNo" label="Reference" width="170" />
            <el-table-column prop="number" label="Number" width="100" />
            <el-table-column prop="typeSpec" label="Type" min-width="160" show-overflow-tooltip />
            <el-table-column prop="level" label="Level" width="90" />
            <el-table-column prop="mark" label="Mark" width="90" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { DEMO_MODE } from '@/config/appConfig'
import { getRobotsDashboard } from '@/api/robots'
import { robotGroups, getAllRobots, getGroupStats, getRobotsByGroup } from '@/mock/robots'

const loading = ref(false)
const groupRows = ref([])
const recentRows = ref([])

let refreshTimer = null
const groupPieRefs = new Map()
const groupPieCharts = new Map()
const groupCardRefs = new Map()
const activeGroupKey = ref('')

const setGroupCardRef = (key, el) => {
  if (!key) return
  if (el) {
    groupCardRefs.set(key, el)
    return
  }
  groupCardRefs.delete(key)
}

const groupHighRiskRows = computed(() => {
  const rows = groupRows.value || []
  return [...rows]
    .map((row) => {
      const devices = Array.isArray(row.highRiskDevices) ? row.highRiskDevices : []
      const normalizedDevices = devices
        .map((d) => (typeof d === 'string' ? { name: d } : d))
        .map((d) => ({ ...d, name: d?.name || d?.robot_id || '' }))
        .filter((d) => d.name)
      return { ...row, highRiskDevices: normalizedDevices }
    })
    .sort((a, b) => Number(b.highRisk ?? 0) - Number(a.highRisk ?? 0))
})

const stats = reactive({
  total: 0,
  highRisk: 0,
  historyHighRisk: 0,
  marked: 0
})

const setGroupPieRef = (key, el) => {
  if (!key) return
  if (el) {
    groupPieRefs.set(key, el)
    return
  }
  groupPieRefs.delete(key)
}

const activateGroup = async (key) => {
  if (!key) return
  activeGroupKey.value = key
  await nextTick()
  const target = groupCardRefs.get(key)
  if (target?.scrollIntoView) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

const renderGroupPies = async () => {
  await nextTick()
  const rows = groupRows.value || []
  const keys = new Set(rows.map((row) => row.key || row.name).filter(Boolean))

  for (const [key, chart] of groupPieCharts.entries()) {
    if (!keys.has(key)) {
      chart.dispose()
      groupPieCharts.delete(key)
    }
  }

  for (const row of rows) {
    const key = row.key || row.name
    if (!key) continue

    const host = groupPieRefs.get(key)
    if (!host) continue

    const total = Number(row.total ?? 0)
    const highRisk = Number(row.highRisk ?? 0)
    const other = Math.max(0, total - highRisk)

    let chart = groupPieCharts.get(key)
    if (!chart) {
      chart = echarts.init(host)
      groupPieCharts.set(key, chart)
    }

    chart.off('click')
    chart.on('click', () => {
      activateGroup(key)
    })

    chart.setOption({
      tooltip: {
        trigger: 'item',
        formatter: '{b}<br/>{c} ({d}%)'
      },
      series: [
        {
          type: 'pie',
          radius: ['55%', '80%'],
          avoidLabelOverlap: true,
          label: { show: false },
          labelLine: { show: false },
          data: [
            { value: highRisk, name: '高风险设备', itemStyle: { color: '#F56C6C' } },
            { value: other, name: '其他设备', itemStyle: { color: '#409EFF' } }
          ]
        }
      ]
    })
  }
}

const resizeGroupPies = () => {
  for (const chart of groupPieCharts.values()) {
    chart.resize()
  }
}

const loadStats = async () => {
  loading.value = true
  try {
    if (DEMO_MODE) {
      const robots = getAllRobots()
      stats.total = robots.length
      stats.highRisk = robots.filter((r) => r.level === 'H').length
      stats.historyHighRisk = robots.filter((r) => r.riskHistory?.length).length
      stats.marked = robots.filter((r) => (r.mark ?? 0) !== 0).length

      groupRows.value = robotGroups.map((group) => {
        const groupKey = group.key
        const groupRobots = getRobotsByGroup(groupKey)
        const groupStat = getGroupStats(groupKey)
        const highRiskDevices = groupRobots
          .filter((r) => r.level === 'H')
          .sort((a, b) => Number(b.riskScore ?? 0) - Number(a.riskScore ?? 0))
          .slice(0, 12)
          .map((r) => ({
            id: r.id,
            robot_id: r.id,
            name: r.name || r.id
          }))
        return {
          key: groupKey,
          name: group.name,
          expected_total: group.total,
          total: groupStat.total,
          highRisk: groupStat.highRisk,
          historyHighRisk: groupStat.historyHighRisk,
          marked: groupRobots.filter((r) => (r.mark ?? 0) !== 0).length,
          highRiskDevices,
          highRiskDevicesPreviewLimit: 12
        }
      })
      recentRows.value = robots.slice(0, 18).map((r) => ({
        partNo: r.partNo,
        referenceNo: r.referenceNo,
        number: r.number ?? 0,
        typeSpec: r.typeSpec,
        level: r.level,
        mark: r.mark ?? 0
      }))

      await renderGroupPies()
      return
    }

    const data = await getRobotsDashboard()
    stats.total = data.summary?.total ?? 0
    stats.highRisk = data.summary?.highRisk ?? 0
    stats.historyHighRisk = data.summary?.historyHighRisk ?? 0
    stats.marked = data.summary?.marked ?? 0

    groupRows.value = data.groupStats || []
    recentRows.value = (data.recentUpdated || []).slice(0, 18)

    await renderGroupPies()
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error(error?.response?.data?.error || error?.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
  refreshTimer = setInterval(loadStats, 30000) // 每30秒刷新一次
  window.addEventListener('resize', resizeGroupPies)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  window.removeEventListener('resize', resizeGroupPies)

  for (const chart of groupPieCharts.values()) {
    chart.dispose()
  }
  groupPieCharts.clear()
  groupPieRefs.clear()
  groupCardRefs.clear()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.stat-card:hover {
  transform: translateY(-3px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.stat-primary .stat-icon {
  background-color: rgba(37, 99, 235, 0.1);
  color: var(--app-primary);
}

.stat-success .stat-icon {
  background-color: rgba(34, 197, 94, 0.12);
  color: #16a34a;
}

.stat-warning .stat-icon {
  background-color: rgba(245, 158, 11, 0.14);
  color: #b45309;
}

.stat-info .stat-icon {
  background-color: rgba(148, 163, 184, 0.16);
  color: rgba(15, 23, 42, 0.55);
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  color: var(--app-muted);
  font-size: 14px;
}

.charts-row {
  margin-bottom: 20px;
}

.group-pie-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: flex-start;
}

.group-pie-item {
  width: 200px;
  border: 1px solid var(--app-border);
  border-radius: 12px;
  padding: 14px 12px 10px;
  background: var(--app-surface);
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.group-pie-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.group-pie-item.is-active {
  border-color: rgba(239, 68, 68, 0.5);
  box-shadow: 0 10px 24px rgba(239, 68, 68, 0.12);
}

.group-pie-title {
  font-weight: 600;
  color: var(--app-text);
  margin-bottom: 8px;
}

.group-pie-chart {
  width: 176px;
  height: 176px;
  margin: 0 auto;
}

.group-pie-meta {
  margin-top: 8px;
  text-align: center;
  color: var(--app-muted);
  font-size: 12px;
}

.data-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.card-header-hint {
  color: var(--app-muted);
  font-size: 12px;
  font-weight: 400;
}

.group-risk-board {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.group-risk-card {
  border: 1px solid var(--app-border);
  border-radius: 14px;
  background: var(--app-surface);
  padding: 14px 14px 10px;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.group-risk-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
}

.group-risk-card.is-active {
  border-color: rgba(239, 68, 68, 0.5);
  box-shadow: 0 14px 28px rgba(239, 68, 68, 0.12);
}

.group-risk-card-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.group-risk-title {
  font-weight: 700;
  color: var(--app-text);
}

.group-risk-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--app-muted);
  flex-shrink: 0;
}

.group-risk-meta-item.danger {
  color: rgba(239, 68, 68, 0.9);
  font-weight: 600;
}

.group-risk-table :deep(.el-table__cell) {
  padding-top: 10px;
  padding-bottom: 10px;
}

.group-risk-card-body :deep(.el-empty) {
  padding: 28px 0;
}
</style>
