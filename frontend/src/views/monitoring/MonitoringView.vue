<template>
  <div class="trajectory-viewport">
    <!-- Header Area -->
    <header class="page-header">
      <div class="title-group">
        <div class="icon-orb">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="text-content">
          <h1>关键轨迹检查 Pulse <small>Trajectory Pulse</small></h1>
          <p class="description">基于实时电流数据的机器人重点抓放点位精准巡检</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button-group>
          <el-tooltip content="刷新数据" placement="bottom">
            <el-button :icon="Refresh" @click="loadPlantGroups" circle />
          </el-tooltip>
          <el-button 
            v-if="checkResult" 
            type="primary" 
            :icon="Download" 
            @click="handleExport"
            class="export-btn"
          >
            导出报告
          </el-button>
        </el-button-group>
      </div>
    </header>

    <!-- Control Center (Horizontal) -->
    <div class="control-center glass-panel">
      <div class="control-row">
        <!-- Plant Selection -->
        <div class="control-item plant-selector">
          <label><el-icon><Location /></el-icon> 目标车间</label>
          <el-select
            v-model="selectedPlant"
            placeholder="请选择车间"
            filterable
            :loading="plantsLoading"
            @change="handlePlantChange"
          >
            <el-option
              v-for="plant in availablePlants"
              :key="plant.key"
              :label="plant.name"
              :value="plant.key"
            />
          </el-select>
        </div>

        <!-- Robot Selection -->
        <div class="control-item robot-selector">
          <label>
            <el-icon><Cpu /></el-icon> 机器人列表
            <el-tag size="small" type="info" effect="plain" class="count-tag" v-if="selectedRobots.length">
              {{ selectedRobots.length }}
            </el-tag>
          </label>
          <el-select
            v-model="selectedRobots"
            placeholder="请选择或全选"
            multiple
            collapse-tags
            collapse-tags-tooltip
            filterable
            :disabled="!selectedPlant"
          >
            <template #header>
              <div class="select-header">
                <el-checkbox
                  v-model="isAllRobotsSelected"
                  :indeterminate="isIndeterminate"
                  @change="handleSelectAllRobots"
                >全选机器人</el-checkbox>
              </div>
            </template>
            <el-option
              v-for="robot in availableRobots"
              :key="robot.value"
              :label="robot.label"
              :value="robot.value"
            />
          </el-select>
        </div>

        <!-- Time Range -->
        <div class="control-item time-selector">
          <label><el-icon><Calendar /></el-icon> 时间跨度</label>
          <el-date-picker
            v-model="timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            :shortcuts="shortcuts"
            unlink-panels
          />
        </div>

        <!-- Execute Button -->
        <div class="control-footer">
          <el-button
            type="primary"
            class="pulse-btn"
            :loading="checking"
            :disabled="!canExecute"
            @click="executeCheck"
          >
            <el-icon v-if="!checking"><Search /></el-icon>
            {{ checking ? '正在诊断...' : '执行诊断' }}
          </el-button>
        </div>
      </div>

      <!-- Advanced Config Row (Key Paths) -->
      <div class="control-row secondary-row">
        <div class="control-item path-config">
          <label><el-icon><Operation /></el-icon> 轨迹关键特征 (Key Paths)</label>
          <div class="path-inputs">
            <el-tag
              v-for="tag in activePaths"
              :key="tag"
              closable
              :disable-transitions="false"
              @close="handleClosePath(tag)"
              class="path-tag"
            >
              {{ tag }}
            </el-tag>
            <el-input
              v-if="inputVisible"
              ref="InputRef"
              v-model="inputValue"
              class="new-path-input"
              size="small"
              @keyup.enter="handleInputConfirm"
              @blur="handleInputConfirm"
            />
            <el-button v-else class="add-path-btn" size="small" @click="showInput">
              + 新增路径
            </el-button>
            <div class="path-presets">
              <el-check-tag 
                v-for="p in ['XLHP', 'PWLD']" 
                :key="p"
                :checked="activePaths.includes(p)"
                @change="(checked) => handlePresetToggle(p, checked)"
              >
                {{ p }}
              </el-check-tag>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="main-content">
      <transition name="fade-slide" mode="out-in">
        <!-- Results Table -->
        <div v-if="checkResult" class="result-container animate-fade-in">
          <div class="result-summary">
            <div class="summary-left">
              <span class="label">检测完成:</span>
              <span class="val">{{ checkResult.count }}</span>
              <span class="unit">个点位</span>
            </div>
            <div class="summary-right">
              <div class="legend">
                <span class="dot ok"></span> 正常
                <span class="dot warning"></span> 偏差较大
                <span class="dot bad"></span> 严重异常
              </div>
            </div>
          </div>

          <el-table
            :data="pagedRows"
            v-loading="checking"
            @sort-change="handleSortChange"
            class="custom-table"
          >
            <el-table-column prop="robot" label="机器人" min-width="180" sortable fixed="left">
              <template #default="{ row }">
                <div class="robot-info">
                  <el-icon><Monitor /></el-icon>
                  <span>{{ row.robot }}</span>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="Name_C" label="位置" width="120" sortable />
            <el-table-column prop="P_name" label="程序路径" min-width="200" show-overflow-tooltip sortable />
            
            <el-table-column label="电流基准 (LQ/HQ)" width="180" align="center">
              <template #default="{ row }">
                <div class="val-group">
                  <span class="mono">{{ formatValue(row.Curr_A1_LQ) }}</span>
                  <span class="divider">/</span>
                  <span class="mono">{{ formatValue(row.Curr_A1_HQ) }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="QH1" label="偏差 QH1" width="120" sortable align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.QH1)" effect="light" class="mono-tag">
                  {{ formatValue(row.QH1) }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="QL1" label="偏差 QL1" width="120" sortable align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.QL1)" effect="light" class="mono-tag">
                  {{ formatValue(row.QL1) }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="size" label="样本数" width="100" sortable align="right" />
          </el-table>

          <footer class="table-footer">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="checkResult.count || 0"
              :page-sizes="[15, 30, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              background
            />
          </footer>
        </div>

        <!-- Empty State -->
        <div v-else-if="!checking" class="empty-state animate-fade-in">
          <div class="empty-illustration">
            <el-icon class="pulse-icon"><Search /></el-icon>
          </div>
          <h3>尚未执行检查</h3>
          <p>请在上方配置车间、机器人及时间跨度，点击“执行诊断”开始巡检</p>
        </div>

        <!-- Skeleton Loading -->
        <div v-else class="loading-state">
          <el-skeleton :rows="10" animated />
        </div>
      </transition>
    </div>

    <!-- Error Toast -->
    <transition name="el-fade-in">
      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        :closable="true"
        @close="errorMessage = ''"
        show-icon
        class="critical-alert"
      />
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Download, Search, Refresh, Location, Cpu, Calendar, 
  TrendCharts, Operation, Monitor, Warning 
} from '@element-plus/icons-vue'
import { DEMO_MODE } from '@/config/appConfig'
import { getRobotGroups, getGripperRobotTables, executeGripperCheck } from '@/api/robots'

// Shortcuts for Date Picker
const shortcuts = [
  { text: '最近 24 小时', value: () => [new Date(Date.now() - 24 * 3600 * 1000), new Date()] },
  { text: '最近 3 天', value: () => [new Date(Date.now() - 3 * 24 * 3600 * 1000), new Date()] },
  { text: '最近 7 天', value: () => [new Date(Date.now() - 7 * 24 * 3600 * 1000), new Date()] },
]

// State
const availablePlants = ref([])
const selectedPlant = ref('')
const plantsLoading = ref(false)

const availableRobots = ref([])
const selectedRobots = ref([])
const robotsLoading = ref(false)

const timeRange = ref([new Date(Date.now() - 7 * 24 * 3600_000), new Date()])

// Key Paths (Improved Dynamic tags)
const activePaths = ref(['XLHP', 'PWLD'])
const inputVisible = ref(false)
const inputValue = ref('')
const InputRef = ref(null)

const showInput = () => {
  inputVisible.value = true
  nextTick(() => InputRef.value.input.focus())
}

const handleInputConfirm = () => {
  if (inputValue.value && !activePaths.value.includes(inputValue.value)) {
    activePaths.value.push(inputValue.value)
  }
  inputVisible.value = false
  inputValue.value = ''
}

const handleClosePath = (tag) => {
  activePaths.value = activePaths.value.filter(t => t !== tag)
}

const handlePresetToggle = (path, checked) => {
  if (checked) {
    if (!activePaths.value.includes(path)) activePaths.value.push(path)
  } else {
    activePaths.value = activePaths.value.filter(p => p !== path)
  }
}

// Robot Selection Logic
const isAllRobotsSelected = computed({
  get: () => selectedRobots.value.length === availableRobots.value.length && availableRobots.value.length > 0,
  set: (val) => {
    if (val) selectedRobots.value = availableRobots.value.map(r => r.value)
    else selectedRobots.value = []
  }
})
const isIndeterminate = computed(() => selectedRobots.value.length > 0 && selectedRobots.value.length < availableRobots.value.length)

// Executive Logic
const checking = ref(false)
const checkResult = ref(null)
const errorMessage = ref('')
const currentPage = ref(1)
const pageSize = ref(15)
const sortState = ref({ prop: 'robot', order: 'ascending' })

const canExecute = computed(() => selectedPlant.value && selectedRobots.value.length > 0 && timeRange.value?.length === 2)

const loadPlantGroups = async () => {
  plantsLoading.value = true
  try {
    if (DEMO_MODE) {
      availablePlants.value = [
        { key: 'plant_a', name: '车间 A - 总装' },
        { key: 'plant_b', name: '车间 B - 喷漆' },
        { key: 'plant_c', name: '车间 C - 冲压' }
      ]
    } else {
      const response = await getRobotGroups()
      availablePlants.value = response || []
    }
  } catch (e) {
    ElMessage.error('获取车间列表失败')
  } finally {
    plantsLoading.value = false
  }
}

const handlePlantChange = async () => {
  selectedRobots.value = []
  availableRobots.value = []
  if (!selectedPlant.value) return

  robotsLoading.value = true
  try {
    if (DEMO_MODE) {
      const mock = { 
        plant_a: ['RB101', 'RB102', 'RB103', 'RB104'], 
        plant_b: ['RB201', 'RB202'], 
        plant_c: ['RB301'] 
      }
      availableRobots.value = (mock[selectedPlant.value] || []).map(r => ({ value: r, label: r }))
    } else {
      const resp = await getGripperRobotTables({ group: selectedPlant.value })
      availableRobots.value = (resp.results || []).map(r => ({ value: r.value, label: r.label }))
    }
  } catch (e) {
    ElMessage.error('获取机器人失败')
  } finally {
    robotsLoading.value = false
  }
}

const handleSelectAllRobots = (val) => {
  selectedRobots.value = val ? availableRobots.value.map(r => r.value) : []
}

const executeCheck = async () => {
  checking.value = true
  checkResult.value = null
  errorMessage.value = ''

  try {
    const payload = {
      start_time: timeRange.value[0].toISOString(),
      end_time: timeRange.value[1].toISOString(),
      gripper_list: selectedRobots.value,
      key_paths: activePaths.value
    }

    if (DEMO_MODE) {
      await new Promise(r => setTimeout(r, 1200))
      checkResult.value = {
        success: true,
        count: 42,
        data: generateMockData(42),
        columns: ['robot', 'Name_C', 'P_name', 'Curr_A1_LQ', 'Curr_A1_HQ', 'QH1', 'QL1', 'size']
      }
    } else {
      checkResult.value = await executeGripperCheck(payload)
    }

    if (checkResult.value.success) {
      ElMessage.success(`检查完成，发现 ${checkResult.value.count} 条记录`)
      currentPage.value = 1
    } else {
      errorMessage.value = checkResult.value.error || '检查失败'
    }
  } catch (e) {
    errorMessage.value = e?.message || '执行异常'
  } finally {
    checking.value = false
  }
}

// Helpers
const formatValue = (val) => {
  if (val === null || val === undefined || val === 'N') return '-'
  const n = parseFloat(val)
  return isNaN(n) ? val : n.toFixed(3)
}

const getStatusType = (val) => {
  const n = Math.abs(parseFloat(val))
  if (isNaN(n)) return 'info'
  if (n > 0.3) return 'danger'
  if (n > 0.1) return 'warning'
  return 'success'
}

const generateMockData = (count) => {
  return Array.from({ length: count }, (_, i) => ({
    robot: `RB_${100 + (i % 5)}`,
    Name_C: `R${i % 2 + 1}/${['PICK', 'PLACE'][i % 2]}`,
    P_name: `/home/robot/Programs/Main_Cycle_V2.mod#L${100 + i * 5}`,
    Curr_A1_LQ: (Math.random() * 1.5).toFixed(3),
    Curr_A1_HQ: (3 + Math.random() * 2).toFixed(3),
    QH1: (Math.random() * 0.5 - 0.1).toFixed(3),
    QL1: (Math.random() * 0.4 - 0.05).toFixed(3),
    size: Math.floor(Math.random() * 200) + 50
  }))
}

const pagedRows = computed(() => {
  if (!checkResult.value?.data) return []
  const start = (currentPage.value - 1) * pageSize.value
  return checkResult.value.data.slice(start, start + pageSize.value)
})

const handleSortChange = ({ prop, order }) => {
  if (!checkResult.value?.data) return
  const dir = order === 'ascending' ? 1 : -1
  checkResult.value.data.sort((a, b) => {
    const av = a[prop], bv = b[prop]
    if (av === bv) return 0
    const na = parseFloat(av), nb = parseFloat(bv)
    if (!isNaN(na) && !isNaN(nb)) return (na - nb) * dir
    return String(av || '').localeCompare(String(bv || '')) * dir
  })
}

const handleExport = () => {
  const headers = checkResult.value.columns || Object.keys(checkResult.value.data[0])
  const csv = [
    headers.join(','),
    ...checkResult.value.data.map(r => headers.map(h => `"${String(r[h]).replace(/"/g, '""')}"`).join(','))
  ].join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `trajectory_report_${Date.now()}.csv`
  link.click()
}

onMounted(loadPlantGroups)
</script>

<style scoped>
.trajectory-viewport {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  background: #f0f2f5;
  min-height: calc(100vh - 120px);
  color: #2c3e50;
  overflow-x: hidden;
}

/* Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-orb {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  box-shadow: 0 8px 16px rgba(79, 172, 254, 0.3);
}

.text-content h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.text-content small {
  font-weight: 400;
  color: #94a3b8;
  font-size: 14px;
  margin-left: 8px;
}

.description {
  margin: 4px 0 0;
  font-size: 13px;
  color: #64748b;
}

/* Glass Panel */
.glass-panel {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 18px;
  padding: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.04);
}

/* Control Center */
.control-row {
  display: flex;
  align-items: flex-end;
  gap: 24px;
  flex-wrap: wrap;
}

.secondary-row {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-item label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 6px;
}

.plant-selector { width: 180px; }
.robot-selector { width: 260px; }
.time-selector { width: 340px; }
.path-config { flex: 1; min-width: 400px; }

.count-tag { margin-left: 4px; }

/* Path Inputs */
.path-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.path-tag {
  height: 32px;
  padding: 0 12px;
  border-radius: 8px;
  font-weight: 500;
}

.new-path-input { width: 120px; }

.path-presets {
  margin-left: 12px;
  display: flex;
  gap: 8px;
  padding-left: 12px;
  border-left: 1px solid #e2e8f0;
}

/* Execute Button */
.pulse-btn {
  height: 42px;
  padding: 0 32px;
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.pulse-btn:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.3);
}

/* Results */
.main-content {
  flex: 1;
}

.result-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}

.summary-left {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.summary-left .label { font-size: 14px; color: #64748b; }
.summary-left .val { font-size: 22px; font-weight: 800; color: #2563eb; }
.summary-left .unit { font-size: 12px; color: #94a3b8; }

.legend {
  font-size: 12px;
  color: #64748b;
  display: flex;
  gap: 12px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 4px;
}
.dot.ok { background: #10b981; }
.dot.warning { background: #f59e0b; }
.dot.bad { background: #ef4444; }

/* Table Styling */
.custom-table {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 30px rgba(0,0,0,0.05);
}

.custom-table :deep(.el-table__row) {
  transition: background-color 0.2s;
}

.robot-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.val-group {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: 'Share Tech Mono', monospace;
  color: #64748b;
}

.mono { font-family: 'Share Tech Mono', monospace; }
.mono-tag { font-family: 'Share Tech Mono', monospace; min-width: 60px; }

.table-footer {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

/* State Transitions */
.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.empty-state {
  text-align: center;
  padding: 80px 0;
  color: #94a3b8;
}

.empty-illustration {
  font-size: 64px;
  margin-bottom: 24px;
  opacity: 0.2;
}

.pulse-icon {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 0.2; }
  50% { transform: scale(1.1); opacity: 0.4; }
  100% { transform: scale(1); opacity: 0.2; }
}

/* Critical Alert */
.critical-alert {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  width: 90%;
  max-width: 600px;
  box-shadow: 0 10px 30px rgba(239, 68, 68, 0.2);
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .control-row { gap: 16px; }
  .path-config { min-width: 100%; }
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  background: white !important;
  border: 1px solid rgba(0, 0, 0, 0.05) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}

:deep(.el-select__wrapper.is-focused) {
  border-color: #2563eb !important;
}
</style>
