<template>
  <div class="dashboard">
    <el-card class="hero-card">
      <template #header>
        <div class="card-header">
          <div class="title">
            <span class="title-text">平台概览</span>
            <span class="title-sub">机器人与关键轨迹检查的运行概览</span>
          </div>
          <el-button :icon="Refresh" @click="handleRefresh">刷新</el-button>
        </div>
      </template>

      <el-row :gutter="16">
        <el-col :xs="12" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-label">机器人总量</div>
            <div class="stat-value">{{ summary.total }}</div>
            <div class="stat-meta">在线 {{ summary.online }} · 维护 {{ summary.maintenance }}</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6">
          <div class="stat-card stat-warning">
            <div class="stat-label">高风险机器人</div>
            <div class="stat-value">{{ summary.highRisk }}</div>
            <div class="stat-meta">历史高风险 {{ summary.historyHighRisk }}</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6">
          <div class="stat-card stat-muted">
            <div class="stat-label">离线设备</div>
            <div class="stat-value">{{ summary.offline }}</div>
            <div class="stat-meta">离线率 {{ summary.offlineRate }}%</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6">
          <div class="stat-card stat-primary">
            <div class="stat-label">运行健康指数</div>
            <div class="stat-value">{{ summary.healthIndex }}</div>
            <div class="stat-meta">基于在线与风险状态</div>
          </div>
        </el-col>
      </el-row>

      <div class="quick-actions">
        <span class="quick-title">快速入口</span>
        <el-button type="primary" @click="goTo('/devices')">机器人状态</el-button>
        <el-button @click="goTo('/monitoring')">关键轨迹检查</el-button>
        <el-button @click="goTo('/alerts')">可视化BI</el-button>
        <el-button @click="goTo('/portal')">应用门户</el-button>
      </div>
    </el-card>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="14">
        <el-card>
          <template #header>
            <div class="table-header">
              <span>机器人分组状态</span>
              <span class="table-meta">共 {{ groupRows.length }} 组</span>
            </div>
          </template>

          <el-table :data="groupRows" stripe height="420" v-loading="loading">
            <el-table-column prop="name" label="分组" min-width="140" show-overflow-tooltip />
            <el-table-column prop="total" label="总量" width="90" align="center" />
            <el-table-column prop="stats.online" label="在线" width="90" align="center" />
            <el-table-column prop="stats.offline" label="离线" width="90" align="center" />
            <el-table-column prop="stats.maintenance" label="维护" width="90" align="center" />
            <el-table-column prop="stats.highRisk" label="高风险" width="90" align="center" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card>
          <template #header>
            <div class="table-header">
              <span>近期风险事件</span>
              <span class="table-meta">最新 {{ recentAlerts.length }} 条</span>
            </div>
          </template>

          <el-empty v-if="!recentAlerts.length && !alertLoading" description="暂无风险事件" />

          <el-table
            v-else
            :data="recentAlerts"
            stripe
            height="420"
            v-loading="alertLoading"
          >
            <el-table-column prop="triggered_at" label="时间" width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.triggered_at || row.time) }}
              </template>
            </el-table-column>
            <el-table-column prop="robot_name" label="机器人" min-width="140" show-overflow-tooltip />
            <el-table-column prop="severity" label="级别" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="severityType(row.severity)" effect="light">
                  {{ severityLabel(row.severity) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="事件描述" min-width="180" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { DEMO_MODE } from '@/config/appConfig'
import { getRobotGroups, getRiskEventStatistics } from '@/api/robots'
import { createRiskEvents, getGroupStats, robotGroups as mockGroups } from '@/mock/robots'

const router = useRouter()

const loading = ref(false)
const alertLoading = ref(false)
const groupsData = ref([])
const recentAlerts = ref([])

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

const formatDateTime = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN')
}

const severityLabel = (value) => {
  const map = { critical: '严重', high: '高', medium: '中', low: '低' }
  return map[value] || value || '-'
}

const severityType = (value) => {
  const map = { critical: 'danger', high: 'warning', medium: 'info', low: '' }
  return map[value] || 'info'
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
  loadGroups()
  loadAlerts()
}

const goTo = (path) => {
  router.push(path)
}

onMounted(() => {
  loadGroups()
  loadAlerts()
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-text {
  font-size: 16px;
  font-weight: 700;
}

.title-sub {
  font-size: 12px;
  color: var(--app-muted);
}

.stat-card {
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 14px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.85);
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 96px;
}

.stat-card.stat-warning {
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.25);
}

.stat-card.stat-muted {
  background: rgba(148, 163, 184, 0.12);
  border-color: rgba(148, 163, 184, 0.25);
}

.stat-card.stat-primary {
  background: rgba(37, 99, 235, 0.1);
  border-color: rgba(37, 99, 235, 0.2);
}

.stat-label {
  font-size: 12px;
  color: rgba(15, 23, 42, 0.6);
  font-weight: 600;
}

.stat-value {
  font-size: 24px;
  font-weight: 800;
  color: rgba(15, 23, 42, 0.9);
}

.stat-meta {
  font-size: 12px;
  color: rgba(15, 23, 42, 0.55);
}

.quick-actions {
  margin-top: 14px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.quick-title {
  font-size: 12px;
  color: rgba(15, 23, 42, 0.6);
  margin-right: 6px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.table-meta {
  font-size: 12px;
  color: rgba(15, 23, 42, 0.55);
}
</style>
