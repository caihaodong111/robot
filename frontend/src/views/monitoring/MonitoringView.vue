<template>
  <div class="trajectory-viewport">
    <!-- 背景流光特效 -->
    <div class="space-ambient">
      <div class="nebula blue"></div>
      <div class="nebula gold"></div>
      <div class="scan-grid"></div>
    </div>

    <div class="layout-wrapper">
      <!-- Header Area -->
      <header class="page-header entrance-slide-in">
        <div class="title-area">
          <h1 class="metallic-title">关键轨迹检查 <span>TRAJECTORY PULSE</span></h1>
        </div>
        <div class="header-actions">
          <el-tooltip content="刷新数据" placement="bottom">
            <el-button :icon="Refresh" @click="loadPlantGroups" circle class="refresh-btn btn-entrance-1" />
          </el-tooltip>
          <el-button
            v-if="checkResult"
            @click="handleExport"
            class="action-btn btn-entrance-2"
          >
            <el-icon class="export-icon"><Download /></el-icon>
            <span>导出报告</span>
          </el-button>
        </div>
      </header>

      <!-- Control Center -->
      <div class="control-area ios-glass entrance-scale-up">
        <div class="border-glow"></div>
        <div class="cell-header">
          <span class="accent-bar"></span>
          诊断配置中心 (DIAGNOSTIC CONFIGURATION)
        </div>

        <div class="control-content">
          <!-- Main Controls Row -->
          <div class="control-row main-controls">
            <!-- Plant Selection -->
            <div class="control-item plant-selector entrance-fade-right-1">
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
            <div class="control-item robot-selector entrance-fade-right-2">
              <label>
                <el-icon><Cpu /></el-icon> 机器人列表
                <el-tag size="small" type="info" effect="plain" class="count-tag" v-if="selectedRobots.length">
                  {{ selectedRobots.length }}
                </el-tag>
              </label>
              <el-select
                v-model="selectedRobots"
                placeholder="请输入机器人名称搜索或全选"
                multiple
                collapse-tags
                collapse-tags-tooltip
                filterable
                remote
                reserve-keyword
                :remote-method="searchRobots"
                :loading="robotsLoading"
                @change="handleRobotsChange"
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

            <!-- Execute Button -->
            <div class="control-item button-wrapper entrance-fade-right-3">
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

          <!-- Time Range Row -->
          <div class="control-row secondary-row">
            <div class="control-item time-selector entrance-fade-up-1">
              <label><el-icon><Calendar /></el-icon> 时间跨度</label>
              <el-date-picker
                v-model="timeRange"
                type="datetimerange"
                range-separator="至"
                start-placeholder="开始"
                end-placeholder="结束"
                :shortcuts="shortcuts"
                :disabled-date="disabledDate"
                unlink-panels
              />
            </div>
          </div>

          <!-- Advanced Config Row (Key Paths) -->
          <div class="control-row secondary-row">
            <div class="control-item path-config entrance-fade-up-2">
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
      </div>

    <!-- Main Content Area -->
    <div class="main-content entrance-delayed-fade">
      <transition name="fade-slide" mode="out-in">
        <!-- Results Table -->
        <div v-if="checkResult" class="result-container animate-fade-in">
          <div class="result-summary">
            <div class="summary-left">
              <span class="label">检测完成:</span>
              <span class="val">{{ checkResult.count }}</span>
              <span class="unit">条记录</span>
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
            :default-sort="{ prop: 'robot', order: 'ascending' }"
            :height="tableHeight"
          >
            <!-- 固定列：基本信息 -->
            <el-table-column prop="robot" label="机器人" min-width="140" sortable fixed="left" class-name="fixed-left-col">
              <template #default="{ row }">
                <div class="robot-info" @click="goToRobotBI(row.robot)">
                  <el-icon><Monitor /></el-icon>
                  <span class="robot-link">{{ row.robot }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="Name_C" label="位置" width="110" sortable align="center" />
            <el-table-column prop="SNR_C" label="SNR" width="80" sortable align="center" />
            <el-table-column prop="SUB" label="SUB" width="70" sortable align="center" />
            <el-table-column prop="P_name" label="程序路径" min-width="120" show-overflow-tooltip sortable />

            <!-- 分组：LQ 电流值 -->
            <el-table-column label="LQ 电流" align="center">
              <el-table-column prop="Curr_A1_LQ" label="A1" width="80" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A1_LQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A2_LQ" label="A2" width="80" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A2_LQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A3_LQ" label="A3" width="80" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A3_LQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A4_LQ" label="A4" width="80" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A4_LQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A5_LQ" label="A5" width="80" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A5_LQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A6_LQ" label="A6" width="80" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A6_LQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_E1_LQ" label="E1" width="80" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_E1_LQ) }}</span></template>
              </el-table-column>
            </el-table-column>

            <!-- 分组：HQ 电流值 -->
            <el-table-column label="HQ 电流" align="center">
              <el-table-column prop="Curr_A1_HQ" label="A1" width="80" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A1_HQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A2_HQ" label="A2" width="80" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A2_HQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A3_HQ" label="A3" width="80" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A3_HQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A4_HQ" label="A4" width="80" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A4_HQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A5_HQ" label="A5" width="80" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A5_HQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A6_HQ" label="A6" width="80" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A6_HQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_E1_HQ" label="E1" width="80" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_E1_HQ) }}</span></template>
              </el-table-column>
            </el-table-column>

            <el-table-column prop="size" label="样本" width="70" sortable align="center" />

            <!-- 分组：偏差值 -->
            <el-table-column label="偏差值" align="center">
              <el-table-column label="1" width="120" align="center">
                <el-table-column prop="QH1" label="QH" width="60" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QH1)">{{ formatValue(row.QH1) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="QL1" label="QL" width="60" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QL1)">{{ formatValue(row.QL1) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
              <el-table-column label="2" width="120" align="center">
                <el-table-column prop="QH2" label="QH" width="60" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QH2)">{{ formatValue(row.QH2) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="QL2" label="QL" width="60" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QL2)">{{ formatValue(row.QL2) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
              <el-table-column label="3" width="120" align="center">
                <el-table-column prop="QH3" label="QH" width="60" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QH3)">{{ formatValue(row.QH3) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="QL3" label="QL" width="60" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QL3)">{{ formatValue(row.QL3) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
              <el-table-column label="4" width="120" align="center">
                <el-table-column prop="QH4" label="QH" width="60" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QH4)">{{ formatValue(row.QH4) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="QL4" label="QL" width="60" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QL4)">{{ formatValue(row.QL4) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
              <el-table-column label="5" width="120" align="center">
                <el-table-column prop="QH5" label="QH" width="60" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QH5)">{{ formatValue(row.QH5) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="QL5" label="QL" width="60" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QL5)">{{ formatValue(row.QL5) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
              <el-table-column label="6" width="120" align="center">
                <el-table-column prop="QH6" label="QH" width="60" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QH6)">{{ formatValue(row.QH6) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="QL6" label="QL" width="60" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QL6)">{{ formatValue(row.QL6) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
              <el-table-column label="7" width="120" align="center">
                <el-table-column prop="QH7" label="QH" width="60" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QH7)">{{ formatValue(row.QH7) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="QL7" label="QL" width="60" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QL7)">{{ formatValue(row.QL7) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
            </el-table-column>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Download, Search, Refresh, Location, Cpu, Calendar,
  Operation, Monitor, Warning
} from '@element-plus/icons-vue'
import { DEMO_MODE, API_BASE_URL } from '@/config/appConfig'
import { getRobotGroups, getGripperRobotTables, executeGripperCheck } from '@/api/robots'
import { useLayoutStore } from '@/stores/layout'

const layoutStore = useLayoutStore()

// 默认时间跨度
const DEFAULT_TIME_SPAN_DAYS = 7

// 表格高度随侧边栏状态动态变化
const tableHeight = computed(() => layoutStore.isCollapsed ? 600 : 500)

// Shortcuts for Date Picker
const shortcuts = [
  { text: '最近 24 小时', value: () => [new Date(Date.now() - 24 * 3600 * 1000), new Date()] },
  { text: '最近 3 天', value: () => [new Date(Date.now() - 3 * 24 * 3600 * 1000), new Date()] },
  { text: '最近 7 天', value: () => [new Date(Date.now() - 7 * 24 * 3600 * 1000), new Date()] },
  { text: '最近 10 天', value: () => [new Date(Date.now() - 10 * 24 * 3600 * 1000), new Date()] },
]

// 禁用未来日期
const disabledDate = (time) => {
  // 只禁用未来日期
  if (time.getTime() > Date.now()) return true
  return false
}

// State
const availablePlants = ref([])
const selectedPlant = ref('')
const plantsLoading = ref(false)

const availableRobots = ref([])
const selectedRobots = ref([])
const robotsLoading = ref(false)

const timeRange = ref([new Date(Date.now() - DEFAULT_TIME_SPAN_DAYS * 24 * 3600_000), new Date()])

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
  // 车间变化时重新搜索机器人
  await searchRobots('')
}

// 远程搜索机器人
const searchRobots = async (query) => {
  robotsLoading.value = true
  try {
    const params = {}
    if (query) {
      params.keyword = query
    }
    if (selectedPlant.value) {
      params.group = selectedPlant.value
    }

    if (DEMO_MODE) {
      // 模拟数据
      const allRobots = [
        { value: 'as33_020rb_400', label: 'as33_020rb_400', group_key: 'plant_a' },
        { value: 'as33_020rb_401', label: 'as33_020rb_401', group_key: 'plant_a' },
        { value: 'as33_020rb_402', label: 'as33_020rb_402', group_key: 'plant_a' },
        { value: 'as34_020rb_400', label: 'as34_020rb_400', group_key: 'plant_b' },
        { value: 'as34_020rb_401', label: 'as34_020rb_401', group_key: 'plant_b' },
        { value: 'as35_020rb_400', label: 'as35_020rb_400', group_key: 'plant_c' },
      ]
      let filtered = allRobots
      if (query) {
        filtered = allRobots.filter(r => r.value.toLowerCase().includes(query.toLowerCase()))
      }
      if (selectedPlant.value) {
        filtered = filtered.filter(r => r.group_key === selectedPlant.value)
      }
      availableRobots.value = filtered
    } else {
      const resp = await getGripperRobotTables(params)
      availableRobots.value = resp.results || []
    }
  } catch (e) {
    ElMessage.error('搜索机器人失败')
  } finally {
    robotsLoading.value = false
  }
}

// 机器人选择变化，自动设置对应车间
const handleRobotsChange = (value) => {
  if (value.length === 0) return

  // 获取第一个选中机器人的车间信息
  const firstRobot = availableRobots.value.find(r => r.value === value[0])
  if (firstRobot && firstRobot.group_key && firstRobot.group_key !== selectedPlant.value) {
    selectedPlant.value = firstRobot.group_key
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

const getStatusClass = (val) => {
  const n = Math.abs(parseFloat(val))
  if (isNaN(n)) return 'dev-neutral'
  if (n > 0.3) return 'dev-danger'
  if (n > 0.1) return 'dev-warning'
  return 'dev-success'
}

const generateMockData = (count) => {
  // 使用真实的机器人表名（与availableRobots中的值一致）
  const mockRobotNames = [
    'as33_020rb_400', 'as33_020rb_401', 'as33_020rb_402',
    'as34_020rb_400', 'as34_020rb_401', 'as35_020rb_400'
  ]

  return Array.from({ length: count }, (_, i) => {
    const robotIndex = i % mockRobotNames.length
    return {
      robot: mockRobotNames[robotIndex],
      Name_C: `R${i % 4 + 1}/${['PICK', 'PLACE', 'WELD', 'CHECK'][i % 4]}`,
      SNR_C: `SNR${100 + i}`,
      SUB: `S${i % 3}`,
      P_name: `/home/robot/Programs/Task_${i % 5}/Main_Cycle_V${i % 3 + 1}.mod#L${100 + i * 5}`,
      // LQ 电流值
      Curr_A1_LQ: (Math.random() * 1.5 + 0.3).toFixed(3),
      Curr_A2_LQ: (Math.random() * 1.8 + 0.4).toFixed(3),
      Curr_A3_LQ: (Math.random() * 2.0 + 0.5).toFixed(3),
      Curr_A4_LQ: (Math.random() * 1.6 + 0.3).toFixed(3),
      Curr_A5_LQ: (Math.random() * 1.4 + 0.2).toFixed(3),
      Curr_A6_LQ: (Math.random() * 1.3 + 0.3).toFixed(3),
      Curr_E1_LQ: (Math.random() * 0.8 + 0.1).toFixed(3),
      // HQ 电流值
      Curr_A1_HQ: (3 + Math.random() * 2).toFixed(3),
      Curr_A2_HQ: (3.5 + Math.random() * 2.5).toFixed(3),
      Curr_A3_HQ: (4 + Math.random() * 3).toFixed(3),
      Curr_A4_HQ: (3.2 + Math.random() * 2.2).toFixed(3),
      Curr_A5_HQ: (2.8 + Math.random() * 1.8).toFixed(3),
      Curr_A6_HQ: (2.5 + Math.random() * 1.5).toFixed(3),
      Curr_E1_HQ: (1.5 + Math.random() * 1).toFixed(3),
      size: Math.floor(Math.random() * 200) + 50,
      // 偏差值
      QH1: (Math.random() * 0.5 - 0.1).toFixed(3),
      QL1: (Math.random() * 0.4 - 0.05).toFixed(3),
      QH2: (Math.random() * 0.5 - 0.1).toFixed(3),
      QL2: (Math.random() * 0.4 - 0.05).toFixed(3),
      QH3: (Math.random() * 0.5 - 0.1).toFixed(3),
      QL3: (Math.random() * 0.4 - 0.05).toFixed(3),
      QH4: (Math.random() * 0.5 - 0.1).toFixed(3),
      QL4: (Math.random() * 0.4 - 0.05).toFixed(3),
      QH5: (Math.random() * 0.5 - 0.1).toFixed(3),
      QL5: (Math.random() * 0.4 - 0.05).toFixed(3),
      QH6: (Math.random() * 0.5 - 0.1).toFixed(3),
      QL6: (Math.random() * 0.4 - 0.05).toFixed(3),
      QH7: (Math.random() * 0.5 - 0.1).toFixed(3),
      QL7: (Math.random() * 0.4 - 0.05).toFixed(3)
    }
  })
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

const goToRobotBI = (robotName) => {
  // 从机器人名称中获取车间信息（如果可能）
  let group = ''
  const robot = availableRobots.value.find(r => r.value === robotName)
  if (robot && robot.group_key) {
    group = robot.group_key
  }
  
  const biUrl = `/api/robots/bi/?robot=${encodeURIComponent(robotName)}&group=${encodeURIComponent(group)}&embed=1`
  window.open(biUrl, '_blank')
}

onMounted(loadPlantGroups)
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

/* 按钮淡入效果 - 刷新按钮 */
.btn-entrance-1 {
  animation: btnFadeIn 0.5s ease-out 0.6s forwards;
  opacity: 0;
  transform: translateY(-10px) rotate(0deg);
}

/* 按钮淡入效果 - 导出按钮 */
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

/* 控制元素从右侧淡入 - 车间选择 */
.entrance-fade-right-1 {
  animation: fadeRightIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.4s forwards;
  opacity: 0;
  transform: translateX(30px);
}

/* 控制元素从右侧淡入 - 机器人选择 */
.entrance-fade-right-2 {
  animation: fadeRightIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.5s forwards;
  opacity: 0;
  transform: translateX(30px);
}

/* 控制元素从右侧淡入 - 执行按钮 */
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

/* 控制元素从下方淡入 - 时间选择器 */
.entrance-fade-up-1 {
  animation: fadeUpIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.5s forwards;
  opacity: 0;
  transform: translateY(20px);
}

/* 控制元素从下方淡入 - 轨迹配置 */
.entrance-fade-up-2 {
  animation: fadeUpIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.6s forwards;
  opacity: 0;
  transform: translateY(20px);
}

@keyframes fadeUpIn {
  to {
    opacity: 1;
    transform: translateY(0);
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
.trajectory-viewport {
  background: radial-gradient(circle at 50% 35%, #0d1a2d 0%, #030508 100%);
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  color: #fff;
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
  padding: 40px;
  max-width: 1600px;
  margin: 0 auto;
}

/* === Header === */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.title-area {
  display: flex;
  flex-direction: column;
}

.metallic-title {
  font-size: 36px;
  font-weight: 900;
  letter-spacing: 5px;
  background: linear-gradient(180deg, #ffffff 30%, #a0a0a0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 40px rgba(0, 195, 255, 0.5);
  margin: 0 0 8px 0;
  position: relative;
  animation: titleGlow 2s ease-out forwards;
}

@keyframes titleGlow {
  0% {
    text-shadow: 0 0 20px rgba(255, 170, 0, 0), 0 0 40px rgba(255, 170, 0, 0), 0 0 40px rgba(0, 195, 255, 0.5);
    filter: brightness(0.8);
  }
  50% {
    text-shadow: 0 0 20px rgba(255, 170, 0, 0.4), 0 0 40px rgba(255, 170, 0, 0.2), 0 0 40px rgba(0, 195, 255, 0.5);
    filter: brightness(1.2);
  }
  100% {
    text-shadow: 0 0 20px rgba(255, 170, 0, 0), 0 0 40px rgba(255, 170, 0, 0), 0 0 40px rgba(0, 195, 255, 0.5);
    filter: brightness(1);
  }
}

.metallic-title span {
  font-size: 14px;
  color: #636e72;
  margin-left: 15px;
  letter-spacing: 2px;
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

/* 卡片标题 */
.cell-header {
  padding: 15px 20px;
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

/* 控制区域 */
.control-area {
  margin: 40px 0;
  overflow: visible;
}

.control-content {
  padding: 20px;
  position: relative;
  z-index: 1;
}

/* Control Center */
.control-row {
  display: flex;
  align-items: flex-end;
  gap: 18px;
  flex-wrap: wrap;
}

.main-controls {
  flex-wrap: nowrap;
  align-items: flex-end;
}

.secondary-row {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  flex-wrap: nowrap;
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-item label {
  font-size: 12px;
  font-weight: 600;
  color: #8899aa;
  display: flex;
  align-items: center;
  gap: 5px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.plant-selector { width: 170px; flex-shrink: 0; }
.robot-selector { width: 240px; flex-shrink: 0; }
.time-selector { width: 100%; max-width: 480px; flex: 1; }
.path-config { flex: 1; min-width: 350px; }

.button-wrapper {
  margin-left: auto;
  flex-shrink: 0;
}

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
  border-left: 1px solid rgba(255, 255, 255, 0.1);
}

/* Execute Button */
.pulse-btn,
.action-btn {
  height: 40px;
  padding: 0 28px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 14px;
  background: linear-gradient(135deg, #00c3ff 0%, #0080ff 100%);
  border: none;
  box-shadow: 0 4px 14px rgba(0, 195, 255, 0.3);
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.pulse-btn:not(:disabled):hover,
.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 195, 255, 0.5);
}

.refresh-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #8899aa;
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  background: #00c3ff;
  border-color: #00c3ff;
  color: #fff;
  transform: rotate(180deg);
}

/* Results */
.main-content {
  flex: 1;
}

.result-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: hidden;
}

.result-container > * {
  overflow: hidden;
}

.result-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(40px);
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.summary-left {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.summary-left .label { font-size: 13px; color: #8899aa; font-weight: 500; }
.summary-left .val { font-size: 24px; font-weight: 800; color: #00c3ff; text-shadow: 0 0 20px rgba(0, 195, 255, 0.5); }
.summary-left .unit { font-size: 12px; color: #8899aa; }

.legend {
  font-size: 12px;
  color: #8899aa;
  display: flex;
  gap: 14px;
  align-items: center;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 4px;
}
.dot.ok { background: #22c55e; box-shadow: 0 0 8px #22c55e; }
.dot.warning { background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }
.dot.bad { background: #ef4444; box-shadow: 0 0 8px #ef4444; }

/* Table Styling */
.custom-table {
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  background: transparent;
}

/* 表格 CSS 变量覆盖 - 参考平台概览的半透明风格 */
.custom-table :deep(.el-table) {
  --el-table-bg-color: rgba(6, 10, 18, 0.9);
  --el-table-tr-bg-color: rgba(8, 12, 20, 0.45);
  --el-table-row-hover-bg-color: rgba(0, 195, 255, 0.06);
  --el-table-header-bg-color: rgba(255, 255, 255, 0.04);
  --el-table-border-color: rgba(255, 255, 255, 0.06);
  color: #dbe6f5;
}

.custom-table :deep(.el-table__inner-wrapper) {
  overflow-x: auto;
}

.custom-table :deep(.el-table__body-wrapper) {
  overflow-x: auto;
}

.custom-table :deep(.el-table__row) {
  transition: background-color 0.2s;
}

.custom-table :deep(.el-table__row td) {
  padding: 0;
}

.custom-table :deep(.el-table__header th) {
  background: rgba(255, 255, 255, 0.04) !important;
  color: #8da0b7 !important;
  font-weight: 600;
  font-size: 11px;
  padding: 0;
  border-color: rgba(255, 255, 255, 0.06) !important;
}

.custom-table :deep(.el-table__body tr) {
  background: rgba(8, 12, 20, 0.5) !important;
}

.custom-table :deep(.el-table__body tr.el-table__row--striped) {
  background: rgba(14, 20, 32, 0.65) !important;
}

.custom-table :deep(.el-table__body td) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.04) !important;
  background-color: transparent !important;
  color: #dbe6f5 !important;
}

.custom-table :deep(.el-table__row:hover td) {
  background: rgba(0, 195, 255, 0.06) !important;
}

.custom-table :deep(.el-table__header .cell) {
  padding: 12px 8px;
  line-height: 1.4;
}

.custom-table :deep(.el-table__body .cell) {
  padding: 12px 8px;
  line-height: 1.4;
}

/* Fixed column handling */
.custom-table :deep(.el-table__fixed) {
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.3);
}

.custom-table :deep(.el-table__fixed-column) {
  background: rgba(6, 10, 18, 0.92) !important;
}

.custom-table :deep(.fixed-left-col .cell) {
  padding-left: 14px;
}

.robot-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #00c3ff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.robot-info:hover {
  color: #00c3ff;
  text-shadow: 0 0 10px rgba(0, 195, 255, 0.5);
}

.robot-link {
  text-decoration: none;
  position: relative;
}

.robot-info:hover .robot-link {
  text-decoration: underline;
}

.robot-info .el-icon {
  font-size: 16px;
}

/* Mono font columns */
.custom-table :deep(.mono-col .cell) {
  font-family: 'Share Tech Mono', 'SF Mono', Consolas, monospace;
  font-size: 13px;
  color: #8899aa;
}

.mono {
  font-family: 'Share Tech Mono', 'SF Mono', Consolas, monospace;
  font-size: 13px;
  color: #8899aa;
}

/* Status tags */
.status-tag {
  font-family: 'Share Tech Mono', 'SF Mono', Consolas, monospace;
  font-size: 12px;
  min-width: 42px;
  border-radius: 6px;
  padding: 0 8px;
  height: 24px;
  line-height: 24px;
  display: inline-block;
  text-align: center;
}

/* Deviation value styles */
.deviation-value {
  font-family: 'Share Tech Mono', 'SF Mono', Consolas, monospace;
  font-size: 13px;
  font-weight: 500;
  display: inline-block;
  min-width: 44px;
  padding: 4px 6px;
  border-radius: 4px;
}

.deviation-value.dev-success {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.deviation-value.dev-warning {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.deviation-value.dev-danger {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  text-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
}

.deviation-value.dev-neutral {
  color: #8899aa;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.val-group {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: 'Share Tech Mono', monospace;
  color: #64748b;
}

.table-footer {
  display: flex;
  justify-content: center;
  padding: 16px 0;
  overflow: visible;
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
  padding: 70px 0;
  color: #8899aa;
}

.empty-state h3 {
  font-size: 18px;
  font-weight: 600;
  color: #8899aa;
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 14px;
  color: #6a7a8a;
}

.empty-illustration {
  font-size: 56px;
  margin-bottom: 20px;
  opacity: 0.2;
  color: #00c3ff;
}

.pulse-icon {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.1); opacity: 0.6; }
  100% { transform: scale(1); opacity: 0.3; }
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
  box-shadow: 0 10px 30px rgba(239, 68, 68, 0.3);
  border-radius: 16px;
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .main-controls { flex-wrap: wrap; }
  .secondary-row { flex-wrap: wrap; }
  .control-row { gap: 16px; }
  .path-config { min-width: 100%; }
  .button-wrapper { margin-left: 0; }
}

@media (max-width: 768px) {
  .trajectory-viewport {
    padding: 16px;
  }

  .custom-table {
    font-size: 12px;
  }

  .custom-table :deep(.el-table__header .cell),
  .custom-table :deep(.el-table__body .cell) {
    padding: 8px 6px;
  }
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
  transition: all 0.2s ease !important;
}

:deep(.el-input__wrapper:hover),
:deep(.el-select__wrapper:hover) {
  border-color: rgba(0, 195, 255, 0.3) !important;
}

:deep(.el-select__wrapper.is-focused) {
  border-color: #00c3ff !important;
  box-shadow: 0 0 0 3px rgba(0, 195, 255, 0.1) !important;
}

:deep(.el-input__inner) {
  color: #fff !important;
}

:deep(.el-select__selected-item) {
  color: #fff !important;
}

:deep(.el-input__inner::placeholder) {
  color: #6a7a8a !important;
}

/* Date Picker Dark Theme */
:deep(.el-date-editor) {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
}

:deep(.el-date-editor:hover) {
  border-color: rgba(0, 195, 255, 0.3) !important;
}

:deep(.el-date-editor.is-active) {
  border-color: #00c3ff !important;
}

:deep(.el-input__prefix),
:deep(.el-input__suffix) {
  color: #8899aa !important;
}

/* Pagination */
:deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) {
  background: #00c3ff;
}

:deep(.el-pagination.is-background .el-pager li) {
  background: rgba(255, 255, 255, 0.03);
  color: #8899aa;
}

:deep(.el-pagination.is-background .el-pager li:hover) {
  background: rgba(0, 195, 255, 0.1);
}

:deep(.el-pagination button) {
  background: rgba(255, 255, 255, 0.03) !important;
  color: #8899aa !important;
}

:deep(.el-pagination button:hover) {
  background: rgba(0, 195, 255, 0.1) !important;
}

:deep(.el-pagination) {
  --el-pagination-button-bg-color: transparent;
  --el-pagination-button-color: #8899aa;
}

:deep(.el-pagination__total),
:deep(.el-pagination__jump),
:deep(.el-pagination__sizes) {
  color: #8899aa !important;
}

/* Path Tags */
:deep(.path-tag) {
  background: rgba(0, 195, 255, 0.1);
  border: 1px solid rgba(0, 195, 255, 0.3);
  color: #00c3ff;
}

:deep(.add-path-btn) {
  border-style: dashed;
  color: #8899aa;
  background: rgba(255, 255, 255, 0.03);
}

:deep(.add-path-btn:hover) {
  border-color: #00c3ff;
  color: #00c3ff;
}

:deep(.el-check-tag.is-checked) {
  background: #00c3ff;
  border-color: #00c3ff;
  color: #fff;
}

:deep(.el-check-tag) {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.1);
  color: #8899aa;
}

/* Custom Scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }

/* Table scrollbar specifically */
.custom-table :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  height: 8px;
}

.custom-table :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.custom-table :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Ensure cells don't overflow */
.custom-table :deep(.el-table__cell) {
  overflow: hidden;
  text-overflow: ellipsis;
}

.custom-table :deep(.cell) {
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-word;
}

/* Tooltip dark theme */
:deep(.el-tooltip__popper) {
  background: rgba(6, 10, 18, 0.95) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

:deep(.el-tooltip__popper .el-tooltip__arrow::before) {
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

:deep(.el-tooltip__popper.is-dark) {
  background: rgba(6, 10, 18, 0.95) !important;
}

:deep(.el-tooltip__inner) {
  color: #fff !important;
}
</style>

<!-- 全局样式：下拉菜单深色主题 -->
<style>
/* Select Dropdown - 玻璃质感 */
.el-select-dropdown {
  background: rgba(10, 10, 15, 0.85) !important;
  backdrop-filter: blur(30px) !important;
  border: 1px solid rgba(0, 204, 255, 0.2) !important;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5) !important;
}

.el-select-dropdown__item {
  color: #aaa !important;
  background: transparent !important;
}

.el-select-dropdown__item.hover,
.el-select-dropdown__item:hover {
  background: rgba(0, 204, 255, 0.15) !important;
  color: #00ccff !important;
}

.el-select-dropdown__item.is-selected {
  color: #00ccff !important;
  background: rgba(0, 204, 255, 0.2) !important;
  font-weight: 600;
}

.el-select-dropdown__item.is-disabled {
  color: #666 !important;
}

.el-select-dropdown__empty-panel {
  color: #666 !important;
}

.el-select-dropdown__wrap {
  background: transparent !important;
}

.el-select-dropdown__list {
  background: transparent !important;
}

.el-popper.is-light .el-popper__arrow::before {
  background: rgba(10, 10, 15, 0.85) !important;
  border: 1px solid rgba(0, 204, 255, 0.2) !important;
}

.el-popper .el-popper__arrow::before {
  background: rgba(10, 10, 15, 0.85) !important;
  border: 1px solid rgba(0, 204, 255, 0.2) !important;
}

/* Date Picker Dropdown - 玻璃质感 */
.el-picker-panel {
  background: rgba(10, 10, 15, 0.85) !important;
  backdrop-filter: blur(30px) !important;
  border: 1px solid rgba(0, 204, 255, 0.2) !important;
  color: #aaa !important;
}

.el-picker-panel__content .cell {
  color: #aaa !important;
}

.el-picker-panel__content .cell:hover {
  background: rgba(0, 204, 255, 0.15) !important;
  color: #00ccff !important;
}

.el-picker-panel__content .cell.available:not(.disabled).in-range {
  background: rgba(0, 204, 255, 0.2) !important;
  color: #00ccff !important;
}

.el-picker-panel__content .cell.available:not(.disabled):hover {
  background: rgba(0, 204, 255, 0.25) !important;
}

.el-date-table th {
  color: #888 !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.el-picker-panel__header-label {
  color: #aaa !important;
}

.el-picker-panel__icon-btn {
  color: #888 !important;
}

.el-picker-panel__icon-btn:hover {
  color: #00ccff !important;
}

.el-picker-panel__footer {
  background: transparent !important;
  border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.el-picker-panel__shortcut {
  color: #888 !important;
}

.el-picker-panel__shortcut:hover {
  color: #00ccff !important;
}

.el-date-range-picker__content {
  border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.el-date-range-picker__header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* Checkbox Dark Theme */
.el-checkbox {
  color: #aaa !important;
}

.el-checkbox__input.is-checked .el-checkbox__inner {
  background-color: #00ccff !important;
  border-color: #00ccff !important;
}

.el-checkbox__inner {
  background: rgba(255, 255, 255, 0.03) !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
}

.el-checkbox__inner:hover {
  border-color: #00ccff !important;
}

.el-checkbox__label {
  color: #aaa !important;
}

.el-select-dropdown__item .el-checkbox {
  color: #aaa !important;
}
</style>
