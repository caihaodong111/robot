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
          <h1 class="ios-title">TRAJECTORY CHECK<span class="subtitle">关键轨迹检查</span></h1>
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
              <div class="robot-select-wrap">
                <el-select
                  v-model="selectedRobots"
                  placeholder="请先选择 Type 和 Tech"
                  multiple
                  collapse-tags
                  collapse-tags-tooltip
                  filterable
                  remote
                  reserve-keyword
                  :remote-method="searchRobots"
                  :loading="robotsLoading"
                  :disabled="!canSelectRobots"
                  @change="handleRobotsChange"
                >
                  <template #header>
                    <div class="select-header">
                      <el-checkbox
                        v-model="isAllRobotsSelected"
                        :indeterminate="isIndeterminate"
                        @change="handleSelectAllRobots"
                      >全选当前筛选结果</el-checkbox>
                    </div>
                  </template>
                  <el-option
                    v-for="robot in availableRobots"
                    :key="robot.value"
                    :label="robot.label"
                    :value="robot.value"
                  />
                </el-select>
                <button
                  v-if="!canSelectRobots"
                  type="button"
                  class="robot-select-guard"
                  @click="handleRobotSelectGuardClick"
                ></button>
              </div>
            </div>

            <!-- Time Range -->
            <div class="control-item time-selector entrance-fade-right-3">
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
                popper-class="trajectory-date-picker"
              />
            </div>

            <!-- Execute Button -->
            <div class="control-item button-wrapper entrance-fade-right-4">
              <el-button
                type="primary"
                class="pulse-btn"
                :class="{ 'is-cancel': checking && isCheckHover && !isCancelling }"
                :disabled="!canExecute && !checking"
                @mouseenter="handleCheckHover(true)"
                @mouseleave="handleCheckHover(false)"
                @click="handleExecuteOrCancel"
              >
                <el-icon v-if="!checking"><Search /></el-icon>
                {{ checking ? (isCancelling ? '正在取消...' : (isCheckHover ? '取消' : '正在诊断...')) : '执行诊断' }}
              </el-button>
              <el-button
                v-if="checkResult"
                @click="handleExport"
                class="pulse-btn export-btn"
              >
                <el-icon><Download /></el-icon>
                <span>导出数据</span>
              </el-button>
              <el-button
                @click="openCsvBrowser"
                class="pulse-btn export-btn"
              >
                <el-icon><FolderOpened /></el-icon>
                <span>CSV 文件</span>
                <span v-if="hasUnreadCsvFiles" class="csv-unread-dot"></span>
              </el-button>
            </div>
          </div>

          <!-- Advanced Config Row (Key Paths) -->
          <div class="control-row secondary-row">
            <div class="control-item filter-selector entrance-fade-up-1">
              <label><el-icon><Cpu /></el-icon> Type 筛选</label>
              <el-select
                v-model="selectedTypes"
                placeholder="按 Type 缩小机器人范围"
                multiple
                collapse-tags
                collapse-tags-tooltip
                clearable
                filterable
                :loading="robotFilterLoading"
                :disabled="!canFilterRobots"
                @visible-change="handleRobotFilterVisibleChange"
                @change="handleTypeFilterChange"
              >
                <template #header>
                  <div class="select-header">
                    <el-checkbox
                      v-model="isAllTypesSelected"
                      :indeterminate="isTypeIndeterminate"
                      @change="handleSelectAllTypes"
                    >全选当前 Type</el-checkbox>
                  </div>
                </template>
                <el-option
                  v-for="type in availableTypes"
                  :key="type"
                  :label="type"
                  :value="type"
                />
              </el-select>
            </div>

            <div class="control-item filter-selector entrance-fade-up-1">
              <label><el-icon><Cpu /></el-icon> Tech 筛选</label>
              <el-select
                v-model="selectedTechs"
                placeholder="按 Tech 缩小机器人范围"
                multiple
                collapse-tags
                collapse-tags-tooltip
                clearable
                filterable
                :loading="robotFilterLoading"
                :disabled="!canFilterRobots"
                @visible-change="handleRobotFilterVisibleChange"
                @change="handleTechFilterChange"
              >
                <template #header>
                  <div class="select-header">
                    <el-checkbox
                      v-model="isAllTechsSelected"
                      :indeterminate="isTechIndeterminate"
                      @change="handleSelectAllTechs"
                    >全选当前 Tech</el-checkbox>
                  </div>
                </template>
                <el-option
                  v-for="tech in availableTechs"
                  :key="tech"
                  :label="tech"
                  :value="tech"
                />
              </el-select>
            </div>

            <div class="control-item path-config entrance-fade-up-1">
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
              <el-input
                v-model="keywordFilter"
                placeholder="关键词筛选（robot/位置/程序路径等）"
                clearable
                class="keyword-filter"
                @keyup.enter="applyKeywordFilter"
                @clear="applyKeywordFilter"
              />
              <el-button class="filter-btn" @click="applyKeywordFilter">筛选</el-button>
              <div class="legend">
                <span class="dot ok"></span> 正常
                <span class="dot warning"></span> 偏差较大
                <span class="dot bad"></span> 严重异常
              </div>
            </div>
          </div>
          <div v-if="activeCsvServerPath" class="csv-path-bar">
            <span class="path-label">CSV 路径</span>
            <button type="button" class="path-link" @click="openCsvBrowser">
              {{ activeCsvServerPath }}
            </button>
          </div>

          <el-table
            :data="checkResult?.data || []"
            v-loading="checking"
            @sort-change="handleSortChange"
            class="custom-table"
            :default-sort="{ prop: 'robot', order: 'ascending' }"
            :height="tableHeight"
          >
            <!-- 固定列：基本信息 -->
            <el-table-column prop="robot" label="机器人" min-width="180" sortable fixed="left" class-name="fixed-left-col">
              <template #default="{ row }">
                <div class="robot-info">
                  <el-icon><Monitor /></el-icon>
                  <span class="robot-name">{{ row.robot }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="Name_C" label="位置" width="120" sortable align="center" />
            <el-table-column prop="SNR_C" label="SNR" width="70" sortable align="center" />
            <el-table-column prop="SUB" label="SUB" width="100" sortable align="center" />
            <el-table-column prop="P_name" label="程序路径" min-width="110" sortable />

            <!-- 分组：偏差值 -->
            <el-table-column label="偏差值" align="center">
              <el-table-column label="1" width="130" align="center">
                <el-table-column prop="QH1" label="QH" width="65" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QH1)">{{ formatValue(row.QH1) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="QL1" label="QL" width="65" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QL1)">{{ formatValue(row.QL1) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
              <el-table-column label="2" width="130" align="center">
                <el-table-column prop="QH2" label="QH" width="65" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QH2)">{{ formatValue(row.QH2) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="QL2" label="QL" width="65" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QL2)">{{ formatValue(row.QL2) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
              <el-table-column label="3" width="130" align="center">
                <el-table-column prop="QH3" label="QH" width="65" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QH3)">{{ formatValue(row.QH3) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="QL3" label="QL" width="65" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QL3)">{{ formatValue(row.QL3) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
              <el-table-column label="4" width="130" align="center">
                <el-table-column prop="QH4" label="QH" width="65" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QH4)">{{ formatValue(row.QH4) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="QL4" label="QL" width="65" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QL4)">{{ formatValue(row.QL4) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
              <el-table-column label="5" width="130" align="center">
                <el-table-column prop="QH5" label="QH" width="65" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QH5)">{{ formatValue(row.QH5) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="QL5" label="QL" width="65" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QL5)">{{ formatValue(row.QL5) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
              <el-table-column label="6" width="130" align="center">
                <el-table-column prop="QH6" label="QH" width="65" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QH6)">{{ formatValue(row.QH6) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="QL6" label="QL" width="65" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QL6)">{{ formatValue(row.QL6) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
              <el-table-column label="7" width="130" align="center">
                <el-table-column prop="QH7" label="QH" width="65" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QH7)">{{ formatValue(row.QH7) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="QL7" label="QL" width="65" sortable align="center">
                  <template #default="{ row }">
                    <span class="deviation-value" :class="getStatusClass(row.QL7)">{{ formatValue(row.QL7) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
            </el-table-column>

            <!-- 分组：LQ 电流值 -->
            <el-table-column label="LQ 电流" align="center">
              <el-table-column prop="Curr_A1_LQ" label="A1" width="68" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A1_LQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A2_LQ" label="A2" width="68" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A2_LQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A3_LQ" label="A3" width="68" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A3_LQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A4_LQ" label="A4" width="68" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A4_LQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A5_LQ" label="A5" width="68" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A5_LQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A6_LQ" label="A6" width="68" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A6_LQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_E1_LQ" label="E1" width="68" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_E1_LQ) }}</span></template>
              </el-table-column>
            </el-table-column>

            <!-- 分组：HQ 电流值 -->
            <el-table-column label="HQ 电流" align="center">
              <el-table-column prop="Curr_A1_HQ" label="A1" width="68" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A1_HQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A2_HQ" label="A2" width="68" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A2_HQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A3_HQ" label="A3" width="68" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A3_HQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A4_HQ" label="A4" width="68" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A4_HQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A5_HQ" label="A5" width="68" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A5_HQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_A6_HQ" label="A6" width="68" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_A6_HQ) }}</span></template>
              </el-table-column>
              <el-table-column prop="Curr_E1_HQ" label="E1" width="68" sortable align="right" class-name="mono-col">
                <template #default="{ row }"><span class="mono">{{ formatValue(row.Curr_E1_HQ) }}</span></template>
              </el-table-column>
            </el-table-column>

            <el-table-column prop="size" label="样本" width="60" sortable align="center" />
          </el-table>

          <footer class="table-footer">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="checkResult.count || 0"
              :page-sizes="[15, 30, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              background
              @current-change="(p) => loadCsvPage(p)"
              @size-change="() => loadCsvPage(1)"
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

        <!-- Loading Spinner -->
        <div v-else class="loading-state">
          <div class="loading-spinner">
            <svg class="spinner" viewBox="0 0 50 50">
              <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="4"></circle>
            </svg>
          </div>
          <div class="loading-message">
            <div class="loading-title">{{ isCancelling ? '正在取消任务' : '正在诊断中' }}</div>
            <div class="loading-tip">{{ isCancelling ? '后端正在结束当前任务，请稍候...' : '正在分析轨迹数据，请稍候...' }}</div>
          </div>
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

    <el-dialog
      v-model="csvDialogVisible"
      width="760px"
      title="CSV 文件浏览"
      class="csv-browser-dialog"
    >
      <div class="csv-browser-header">
        <div class="csv-dir-line">
          <span class="csv-dir-label">存放路径</span>
          <span class="csv-dir-value">{{ exportDir || '暂无' }}</span>
        </div>
        <el-button :loading="csvFilesLoading" @click="refreshCsvFiles">刷新</el-button>
      </div>

      <el-table
        :data="csvFiles"
        v-loading="csvFilesLoading"
        height="360"
        class="custom-table"
        empty-text="暂无可用 CSV 文件"
      >
        <el-table-column prop="filename" label="文件名" min-width="300">
          <template #default="{ row }">
            <button type="button" class="path-link file-link" @click="handleLoadCsvFile(row)">
              <span v-if="isCsvUnread(row.filename)" class="csv-file-dot"></span>
              {{ row.filename }}
            </button>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" min-width="190">
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column prop="size" label="大小" width="110" align="right">
          <template #default="{ row }">{{ formatFileSize(row.size) }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, onActivated, onDeactivated, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Download, Search, Location, Cpu, Calendar,
  Operation, Monitor, Warning, FolderOpened
} from '@element-plus/icons-vue'
import { DEMO_MODE, API_BASE_URL } from '@/config/appConfig'
import {
  getRobotGroups,
  getGripperRobotTables,
  getGripperRobotFilterOptions,
  executeGripperCheckCsv,
  cancelGripperCheck,
  downloadGripperCheckCsv,
  downloadGripperCheckCsvFile,
  getGripperCheckCsvFiles,
  getGripperCheckCsvFileRows,
  getGripperCheckStatus,
  getGripperCheckLatest,
  getGripperCheckCsvRows
} from '@/api/robots'
import { useLayoutStore } from '@/stores/layout'

defineOptions({ name: 'Monitoring' })

const layoutStore = useLayoutStore()

// 默认时间跨度
const DEFAULT_TIME_SPAN_DAYS = 7
const TASK_STORAGE_KEY = 'gripper_check_task_id'
const CSV_READ_STORAGE_KEY = 'gripper_check_seen_csv_files'
const ACTIVE_TASK_STATUSES = new Set(['queued', 'running', 'exporting', 'cancelling'])

// 表格高度随侧边栏状态动态变化
const tableHeight = computed(() => layoutStore.isCollapsed ? 680 : 620)

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
const availableTypes = ref([])
const availableTechs = ref([])
const selectedTypes = ref([])
const selectedTechs = ref([])
const robotFilterLoading = ref(false)
const robotsLoading = ref(false)

const timeRange = ref([new Date(Date.now() - DEFAULT_TIME_SPAN_DAYS * 24 * 3600_000), new Date()])

// Key Paths (Improved Dynamic tags)
const activePaths = ref([])
const inputVisible = ref(false)
const inputValue = ref('')
const InputRef = ref(null)

const showInput = () => {
  inputVisible.value = true
  nextTick(() => InputRef.value.input.focus())
}

const handleInputConfirm = () => {
  const nextValue = (inputValue.value || '').trim()
  if (nextValue && !activePaths.value.includes(nextValue)) {
    activePaths.value.push(nextValue)
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
const isAllTypesSelected = computed({
  get: () => selectedTypes.value.length === availableTypes.value.length && availableTypes.value.length > 0,
  set: (val) => {
    if (val) selectedTypes.value = [...availableTypes.value]
    else selectedTypes.value = []
  }
})
const isTypeIndeterminate = computed(() => selectedTypes.value.length > 0 && selectedTypes.value.length < availableTypes.value.length)
const isAllTechsSelected = computed({
  get: () => selectedTechs.value.length === availableTechs.value.length && availableTechs.value.length > 0,
  set: (val) => {
    if (val) selectedTechs.value = [...availableTechs.value]
    else selectedTechs.value = []
  }
})
const isTechIndeterminate = computed(() => selectedTechs.value.length > 0 && selectedTechs.value.length < availableTechs.value.length)

// Executive Logic
const checking = ref(false)
const isCancelling = ref(false)
const isCheckHover = ref(false)
const checkResult = ref(null)
const latestMeta = ref(null)
const errorMessage = ref('')
const currentPage = ref(1)
const pageSize = ref(15)
const sortState = ref({ prop: 'robot', order: 'ascending' })
const activeCheckId = ref(0)
const canceledCheckId = ref(0)
const activeTaskId = ref(localStorage.getItem(TASK_STORAGE_KEY) || '')
const sseConnection = ref(null)
const statusPollingTimer = ref(null)
const STATUS_POLL_INTERVAL = 30000
const CANCELLING_POLL_INTERVAL = 1000
const statusRequestInFlight = ref(false)
const keywordFilter = ref('')
const activeCsvFilename = ref('')
const activeCsvServerPath = ref('')
const exportDir = ref('')
const csvDialogVisible = ref(false)
const csvFilesLoading = ref(false)
const csvFiles = ref([])
const seenCsvFiles = ref([])
const hasUnreadCsvFiles = computed(() => {
  const currentFilename = (activeCsvFilename.value || '').trim()
  if (currentFilename && !seenCsvFiles.value.includes(currentFilename)) return true
  return csvFiles.value.some(file => !seenCsvFiles.value.includes(file.filename))
})
const canFilterRobots = computed(() => Boolean(selectedPlant.value))
const canSelectRobots = computed(() => Boolean(selectedPlant.value) && selectedTypes.value.length > 0 && selectedTechs.value.length > 0)

const canExecute = computed(() => selectedPlant.value && selectedRobots.value.length > 0 && timeRange.value?.length === 2)

const DEMO_ROBOT_CATALOG = [
  { value: 'as33_020rb_400', label: 'as33_020rb_400', group_key: 'plant_a', type: 'HANDLING', tech: 'SPOT' },
  { value: 'as33_020rb_401', label: 'as33_020rb_401', group_key: 'plant_a', type: 'HANDLING', tech: 'MIG' },
  { value: 'as33_020rb_402', label: 'as33_020rb_402', group_key: 'plant_a', type: 'SEALING', tech: 'SEAL' },
  { value: 'as34_020rb_400', label: 'as34_020rb_400', group_key: 'plant_b', type: 'WELDING', tech: 'SPOT' },
  { value: 'as34_020rb_401', label: 'as34_020rb_401', group_key: 'plant_b', type: 'WELDING', tech: 'MIG' },
  { value: 'as35_020rb_400', label: 'as35_020rb_400', group_key: 'plant_c', type: 'HANDLING', tech: 'LASER' },
]

const normalizeGroupName = (group) => {
  if (!group) return group
  if (group.name === 'SA1' || group.key === 'SA1') {
    return { ...group, name: 'AS1' }
  }
  return group
}

const setPersistedTaskId = (taskId) => {
  const normalized = (taskId || '').trim()
  activeTaskId.value = normalized
  if (normalized) {
    localStorage.setItem(TASK_STORAGE_KEY, normalized)
  } else {
    localStorage.removeItem(TASK_STORAGE_KEY)
  }
}

const loadSeenCsvFiles = () => {
  try {
    const raw = localStorage.getItem(CSV_READ_STORAGE_KEY)
    if (!raw) {
      seenCsvFiles.value = []
      return false
    }
    const parsed = JSON.parse(raw)
    seenCsvFiles.value = Array.isArray(parsed) ? parsed.filter(Boolean) : []
    return true
  } catch {
    seenCsvFiles.value = []
    return false
  }
}

const persistSeenCsvFiles = () => {
  localStorage.setItem(CSV_READ_STORAGE_KEY, JSON.stringify(seenCsvFiles.value))
}

const markCsvFileRead = (filename) => {
  const normalized = (filename || '').trim()
  if (!normalized) return
  if (!seenCsvFiles.value.includes(normalized)) {
    seenCsvFiles.value = [...seenCsvFiles.value, normalized]
    persistSeenCsvFiles()
  }
}

const markCsvFileUnread = (filename) => {
  const normalized = (filename || '').trim()
  if (!normalized) return
  seenCsvFiles.value = seenCsvFiles.value.filter(item => item !== normalized)
  persistSeenCsvFiles()
}

const isCsvUnread = (filename) => {
  const normalized = (filename || '').trim()
  return Boolean(normalized) && !seenCsvFiles.value.includes(normalized)
}

const setActiveCsvSource = ({ filename = '', serverPath = '' } = {}) => {
  activeCsvFilename.value = (filename || '').trim()
  activeCsvServerPath.value = (serverPath || '').trim()
}

const getRequestErrorMessage = (error, fallback) => {
  const errorCode = error?.response?.data?.error
  const details = error?.response?.data?.details
  if (errorCode === 'another-task-running') return '已有轨迹检查任务正在执行，请稍后再试'
  if (errorCode === 'enqueue-failed') return details || '任务入队失败，请检查 Celery/Redis'
  if (errorCode === 'task-not-found') return '任务状态已失效，请重新执行'
  if (errorCode === 'task-not-active') return '任务已经结束，无需重复取消'
  return errorCode || error?.message || fallback
}

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
      availablePlants.value = (response || []).map(normalizeGroupName)
    }
  } catch (e) {
    ElMessage.error('获取车间列表失败')
  } finally {
    plantsLoading.value = false
  }
}

const resetRobotSearchState = () => {
  lastRobotSearchKey.value = ''
  if (robotSearchTimer.value) {
    clearTimeout(robotSearchTimer.value)
    robotSearchTimer.value = null
  }
}

const syncSelectedRobotsWithAvailable = () => {
  const allowed = new Set(availableRobots.value.map(robot => robot.value))
  selectedRobots.value = selectedRobots.value.filter(robotId => allowed.has(robotId))
}

const syncRobotFiltersWithAvailable = () => {
  const allowedTypes = new Set(availableTypes.value)
  const allowedTechs = new Set(availableTechs.value)
  selectedTypes.value = selectedTypes.value.filter(type => allowedTypes.has(type))
  selectedTechs.value = selectedTechs.value.filter(tech => allowedTechs.has(tech))
}

const loadRobotFilterOptions = async ({ clearSelection = false } = {}) => {
  if (clearSelection || !selectedPlant.value) {
    selectedTypes.value = []
    selectedTechs.value = []
  }

  if (!selectedPlant.value) {
    availableTypes.value = []
    availableTechs.value = []
    return
  }

  try {
    robotFilterLoading.value = true
    if (DEMO_MODE) {
      const scopedRobots = DEMO_ROBOT_CATALOG.filter(robot => robot.group_key === selectedPlant.value)
      availableTypes.value = [...new Set(scopedRobots.map(robot => robot.type).filter(Boolean))].sort()
      availableTechs.value = [...new Set(scopedRobots.map(robot => robot.tech).filter(Boolean))].sort()
    } else {
      const resp = await getGripperRobotFilterOptions({ group: selectedPlant.value })
      availableTypes.value = Array.isArray(resp?.types) ? resp.types : []
      availableTechs.value = Array.isArray(resp?.techs) ? resp.techs : []
    }

    if (!clearSelection) {
      syncRobotFiltersWithAvailable()
    }
  } catch (e) {
    availableTypes.value = []
    availableTechs.value = []
    ElMessage.error('获取 Type/Tech 筛选项失败')
  } finally {
    robotFilterLoading.value = false
  }
}

const handleRobotFilterVisibleChange = async (visible) => {
  if (!visible || !selectedPlant.value || robotFilterLoading.value) return
  if (availableTypes.value.length || availableTechs.value.length) return
  await loadRobotFilterOptions()
}

const refreshRobotOptions = async ({ query = '', clearSelection = false } = {}) => {
  resetRobotSearchState()
  if (clearSelection) {
    selectedRobots.value = []
  }
  await doSearchRobots(query)
  if (!clearSelection) {
    syncSelectedRobotsWithAvailable()
  }
}

const handlePlantChange = async () => {
  availableRobots.value = []
  await loadRobotFilterOptions({ clearSelection: true })
  await refreshRobotOptions({ clearSelection: true })
}

const handleTypeFilterChange = async () => {
  await refreshRobotOptions()
}

const handleTechFilterChange = async () => {
  await refreshRobotOptions()
}

const handleSelectAllTypes = async (val) => {
  selectedTypes.value = val ? [...availableTypes.value] : []
  await refreshRobotOptions()
}

const handleSelectAllTechs = async (val) => {
  selectedTechs.value = val ? [...availableTechs.value] : []
  await refreshRobotOptions()
}

const handleRobotSelectGuardClick = () => {
  if (!selectedPlant.value) {
    ElMessage.warning('请先选择车间，再选择 Type 和 Tech')
    return
  }
  if (!selectedTypes.value.length || !selectedTechs.value.length) {
    ElMessage.warning('请先选择 Type 和 Tech')
  }
}

// 远程搜索机器人
const robotSearchTimer = ref(null)
const lastRobotSearchKey = ref('')

const doSearchRobots = async (query) => {
  robotsLoading.value = true
  try {
    const params = {}
    if (query) {
      params.keyword = query
    }
    if (selectedPlant.value) {
      params.group = selectedPlant.value
    }
    if (selectedTypes.value.length) {
      params.types = selectedTypes.value.join(',')
    }
    if (selectedTechs.value.length) {
      params.techs = selectedTechs.value.join(',')
    }

    if (DEMO_MODE) {
      let filtered = DEMO_ROBOT_CATALOG
      if (query) {
        const normalizedQuery = query.toLowerCase()
        filtered = filtered.filter(robot =>
          robot.value.toLowerCase().includes(normalizedQuery) ||
          robot.type.toLowerCase().includes(normalizedQuery) ||
          robot.tech.toLowerCase().includes(normalizedQuery)
        )
      }
      if (selectedPlant.value) {
        filtered = filtered.filter(r => r.group_key === selectedPlant.value)
      }
      if (selectedTypes.value.length) {
        const selectedTypeSet = new Set(selectedTypes.value)
        filtered = filtered.filter(robot => selectedTypeSet.has(robot.type))
      }
      if (selectedTechs.value.length) {
        const selectedTechSet = new Set(selectedTechs.value)
        filtered = filtered.filter(robot => selectedTechSet.has(robot.tech))
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

// el-select remote-method 触发频率很高：做防抖，避免大量请求
const searchRobots = (query) => {
  const paramsKey = JSON.stringify({
    q: (query || '').trim(),
    group: selectedPlant.value || '',
    types: [...selectedTypes.value].sort(),
    techs: [...selectedTechs.value].sort()
  })
  if (paramsKey === lastRobotSearchKey.value) return
  lastRobotSearchKey.value = paramsKey

  if (robotSearchTimer.value) clearTimeout(robotSearchTimer.value)
  robotSearchTimer.value = setTimeout(() => {
    doSearchRobots((query || '').trim())
  }, 250)
}

// 机器人选择变化，自动设置对应车间
const handleRobotsChange = async (value) => {
  if (value.length === 0) return

  const firstRobot = availableRobots.value.find(r => r.value === value[0])
  if (firstRobot && firstRobot.group_key && firstRobot.group_key !== selectedPlant.value) {
    selectedPlant.value = firstRobot.group_key
    await loadRobotFilterOptions({ clearSelection: true })
    await refreshRobotOptions()
  }
  syncSelectedRobotsWithAvailable()
}

const handleSelectAllRobots = (val) => {
  selectedRobots.value = val ? availableRobots.value.map(r => r.value) : []
}

const executeCheck = async () => {
  const myCheckId = activeCheckId.value + 1
  activeCheckId.value = myCheckId
  canceledCheckId.value = 0
  checking.value = true
  isCancelling.value = false
  isCheckHover.value = false
  stopStatusPolling()
  checkResult.value = null
  errorMessage.value = ''
  setPersistedTaskId('')
  setActiveCsvSource()

  try {
    const sanitizedKeyPaths = (activePaths.value || [])
      .map(p => (p || '').trim())
      .filter(Boolean)

    const payload = {
      start_time: timeRange.value[0].toISOString(),
      end_time: timeRange.value[1].toISOString(),
      gripper_list: selectedRobots.value,
      key_paths: sanitizedKeyPaths
    }

    if (DEMO_MODE) {
      await new Promise(r => setTimeout(r, 1200))
      checkResult.value = {
        success: true,
        count: 42,
        data: generateMockData(42),
        columns: ['robot', 'Name_C', 'P_name', 'Curr_A1_LQ', 'Curr_A1_HQ', 'QH1', 'QL1', 'size']
      }
      ElMessage.success('检查完成，发现 42 条记录（演示）')
      currentPage.value = 1
      checking.value = false
      stopStatusPolling()
      handleExport()
      return
    }

    const resp = await executeGripperCheckCsv(payload)
    const taskId = (resp?.task_id || '').trim()
    if (!taskId) throw new Error('未获取到任务ID')
    setPersistedTaskId(taskId)
    startSse(taskId)
    startStatusPolling()
    await fetchCheckStatus()
  } catch (e) {
    if (canceledCheckId.value !== myCheckId && activeCheckId.value === myCheckId) {
      errorMessage.value = getRequestErrorMessage(e, '执行异常')
      checking.value = false
      stopStatusPolling()
    }
  }
}

const handleCheckHover = (val) => {
  if (!checking.value || isCancelling.value) return
  isCheckHover.value = val
}

const handleCancelCheck = async () => {
  if (!checking.value) return
  const taskId = (activeTaskId.value || '').trim()
  if (!taskId) return

  const finalizeCancelledUi = () => {
    checking.value = false
    isCancelling.value = false
    isCheckHover.value = false
    checkResult.value = null
    latestMeta.value = null
    stopStatusPolling()
    stopSse()
    setPersistedTaskId('')
  }

  isCheckHover.value = false
  isCancelling.value = true
  try {
    const resp = await cancelGripperCheck(taskId)
    const statusValue = (resp?.status || '').toLowerCase()
    if (statusValue === 'cancelled') {
      finalizeCancelledUi()
      ElMessage.info('任务已取消')
      return
    }

    stopSse()
    ElMessage.info(statusValue === 'cancelling' ? '正在取消任务...' : '已提交取消请求')
    stopStatusPolling()
    startStatusPolling()
    await fetchCheckStatus()
  } catch (e) {
    isCancelling.value = false
    errorMessage.value = getRequestErrorMessage(e, '取消失败')
  }
}

const handleExecuteOrCancel = () => {
  if (checking.value) {
    handleCancelCheck()
    return
  }
  executeCheck()
}

const loadCsvPage = async (page) => {
  const taskId = (activeTaskId.value || '').trim()
  const filename = (activeCsvFilename.value || '').trim()
  if (!taskId && !filename) return
  const sortProp = sortState.value?.prop || ''
  const sortOrder = sortState.value?.order === 'descending' ? 'desc' : 'asc'
  const baseParams = {
    page,
    page_size: pageSize.value,
    sort: sortProp,
    order: sortOrder,
    keyword: (keywordFilter.value || '').trim()
  }
  const resp = filename
    ? await getGripperCheckCsvFileRows({
        filename,
        ...baseParams
      })
    : await getGripperCheckCsvRows({
        task_id: taskId,
        ...baseParams
      })
  if (!resp?.success) throw new Error(resp?.error || '读取CSV失败')
  checkResult.value = resp
  currentPage.value = page
}

const applyKeywordFilter = async () => {
  if (!checkResult.value?.success) return
  await loadCsvPage(1)
}

const fetchCheckStatus = async () => {
  const taskId = (activeTaskId.value || '').trim()
  if (!taskId) return
  if (!checking.value && !checkResult.value) return
  if (document.visibilityState === 'hidden') return
  if (statusRequestInFlight.value) return
  statusRequestInFlight.value = true
  try {
    const resp = await getGripperCheckStatus(taskId)
    const statusValue = (resp?.status || '').toLowerCase()
    if (ACTIVE_TASK_STATUSES.has(statusValue)) {
      checking.value = true
      isCancelling.value = statusValue === 'cancelling'
      if (statusValue === 'cancelling') {
        stopStatusPolling()
        startStatusPolling()
      }
      return
    }
    if (statusValue) {
      checking.value = false
      isCancelling.value = false
      isCheckHover.value = false
      stopStatusPolling()
      if (statusValue === 'failed') {
        errorMessage.value = resp?.error || '检查失败'
        setPersistedTaskId('')
        return
      }
      if (statusValue === 'cancelled') {
        checkResult.value = null
        latestMeta.value = null
        setPersistedTaskId('')
        ElMessage.info('诊断已取消')
        return
      }

      try {
        const latest = await getGripperCheckLatest(taskId)
        if (!latest?.success) throw new Error(latest?.error || '检查失败')
        latestMeta.value = latest
        setActiveCsvSource({ filename: latest.filename, serverPath: latest.server_path })
        markCsvFileUnread(latest.filename)

        await loadCsvPage(1)
      } finally {
        checking.value = false
      }
    }
  } catch (error) {
    if (error?.response?.data?.error === 'task-not-found') {
      checking.value = false
      stopStatusPolling()
      setPersistedTaskId('')
      return
    }
    console.error('获取轨迹检查状态失败:', error)
  } finally {
    statusRequestInFlight.value = false
  }
}

const stopSse = () => {
  if (sseConnection.value) {
    try { sseConnection.value.close() } catch {}
    sseConnection.value = null
  }
}

const startSse = (taskId) => {
  if (DEMO_MODE) return
  const id = (taskId || '').trim()
  if (!id) return
  stopSse()

  const url = `${API_BASE_URL}/api/robots/gripper-check/events/?task_id=${encodeURIComponent(id)}`
  const es = new EventSource(url)
  sseConnection.value = es

  es.addEventListener('status', (evt) => {
    try {
      const payload = JSON.parse(evt.data || '{}')
      const statusValue = (payload?.status || '').toLowerCase()
      if (statusValue === 'failed' && payload?.error) errorMessage.value = payload.error
      if (statusValue === 'cancelled') {
        checking.value = false
        isCancelling.value = false
        checkResult.value = null
        latestMeta.value = null
        setPersistedTaskId('')
        stopStatusPolling()
        stopSse()
        ElMessage.info('诊断已取消')
      }
      if (statusValue === 'cancelling') {
        checking.value = true
        isCancelling.value = true
      }
    } catch {}
  })

  es.addEventListener('result', (evt) => {
    try {
      const latest = JSON.parse(evt.data || '{}')
      if (!latest?.success) {
        if (latest?.error) errorMessage.value = latest.error
        return
      }
      latestMeta.value = latest
      setActiveCsvSource({ filename: latest.filename, serverPath: latest.server_path })
      markCsvFileUnread(latest.filename)
      loadCsvPage(1).catch((e) => {
        errorMessage.value = e?.message || '读取CSV失败'
      })
    } finally {
      checking.value = false
      isCancelling.value = false
      stopStatusPolling()
      stopSse()
    }
  })

  es.addEventListener('error', () => {
    // SSE 失败时回退到轮询
    stopSse()
    if (checking.value) startStatusPolling()
  })
}

const startStatusPolling = () => {
  if (statusPollingTimer.value) return
  const interval = isCancelling.value ? CANCELLING_POLL_INTERVAL : STATUS_POLL_INTERVAL
  statusPollingTimer.value = setInterval(fetchCheckStatus, interval)
}

const stopStatusPolling = () => {
  if (!statusPollingTimer.value) return
  clearInterval(statusPollingTimer.value)
  statusPollingTimer.value = null
}

const handleVisibilityChange = () => {
  if (!checking.value) return
  if (document.visibilityState === 'hidden') stopStatusPolling()
  else startStatusPolling()
}

// Helpers
const formatValue = (val) => {
  if (val === null || val === undefined || val === 'N') return '-'
  const n = parseFloat(val)
  return isNaN(n) ? val : n.toFixed(3)
}

const formatFileSize = (size) => {
  const value = Number(size)
  if (!Number.isFinite(value) || value < 1024) return `${value || 0} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}

const formatDateTime = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
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
  if (n >= 10) return 'dev-danger'
  if (n >= 3) return 'dev-warning'
  return 'dev-success'
}

const generateMockData = (count) => {
  // 使用真实的机器人表名（与availableRobots中的值一致）
  const mockRobotNames = DEMO_ROBOT_CATALOG.map(robot => robot.value)

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

const handleSortChange = ({ prop, order }) => {
  sortState.value = { prop, order }
  loadCsvPage(1).catch((e) => {
    errorMessage.value = e?.message || '排序失败'
  })
}

const triggerCsvDownload = (downloadResp, fallbackFilename) => {
  const blob = downloadResp?.data
  const headers = downloadResp?.headers || {}
  const serverPath = headers['x-server-file-path'] || headers['X-Server-File-Path'] || activeCsvServerPath.value || latestMeta.value?.server_path
  const contentDisposition = headers['content-disposition'] || ''
  const match = /filename\\*=UTF-8''([^;]+)|filename=\"?([^\";]+)\"?/i.exec(contentDisposition)
  const filename = decodeURIComponent(match?.[1] || match?.[2] || fallbackFilename || `trajectory_report_${Date.now()}.csv`)

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)

  const tips = serverPath ? `（服务器生成路径: ${serverPath}）` : ''
  ElMessage({
    type: 'success',
    message: `文件已下载${tips}`,
    duration: 0,
    showClose: true
  })
}

const handleExport = () => {
  const taskId = (activeTaskId.value || '').trim()
  const filename = (activeCsvFilename.value || '').trim()
  if (filename) {
    downloadGripperCheckCsvFile(filename)
      .then((downloadResp) => triggerCsvDownload(downloadResp, filename))
      .catch((e) => {
        errorMessage.value = e?.message || '下载失败'
      })
    return
  }
  if (!taskId) return
  downloadGripperCheckCsv(taskId)
    .then((downloadResp) => triggerCsvDownload(downloadResp, latestMeta.value?.filename))
    .catch((e) => {
      errorMessage.value = e?.message || '下载失败'
    })
}

const refreshCsvFiles = async () => {
  csvFilesLoading.value = true
  try {
    const hadSeenStorage = loadSeenCsvFiles()
    const resp = await getGripperCheckCsvFiles()
    exportDir.value = resp?.export_dir || ''
    csvFiles.value = resp?.files || []
    if (!hadSeenStorage) {
      seenCsvFiles.value = csvFiles.value.map(file => file.filename)
      persistSeenCsvFiles()
    }
  } catch (e) {
    errorMessage.value = e?.message || '读取 CSV 文件列表失败'
  } finally {
    csvFilesLoading.value = false
  }
}

const openCsvBrowser = async () => {
  csvDialogVisible.value = true
  await refreshCsvFiles()
}

const handleLoadCsvFile = async (file) => {
  const filename = (file?.filename || '').trim()
  if (!filename) return
  markCsvFileRead(filename)
  checking.value = false
  stopStatusPolling()
  stopSse()
  setPersistedTaskId('')
  setActiveCsvSource({ filename, serverPath: file?.server_path || '' })
  latestMeta.value = {
    ...(latestMeta.value || {}),
    filename,
    server_path: file?.server_path || '',
    updated_at: file?.updated_at || ''
  }
  try {
    await loadCsvPage(1)
    csvDialogVisible.value = false
    ElMessage.success(`已加载 ${filename}`)
  } catch (e) {
    errorMessage.value = e?.message || '加载 CSV 失败'
  }
}

const goToRobotBI = (robotName) => {
  // 从机器人名称中获取车间信息（如果可能）
  let group = ''
  const robot = availableRobots.value.find(r => r.value === robotName)
  if (robot && robot.group_key) {
    group = robot.group_key
  }

  // 使用完整的后端URL，确保开发环境下正确访问
  const biUrl = `${API_BASE_URL}/api/robots/bi/?robot=${encodeURIComponent(robotName)}&group=${encodeURIComponent(group)}&embed=1`
  window.open(biUrl, '_blank')
}

onMounted(async () => {
  loadSeenCsvFiles()
  await loadPlantGroups()
  if (selectedPlant.value) {
    await loadRobotFilterOptions()
  }
  document.addEventListener('visibilitychange', handleVisibilityChange)
  // 若上次诊断仍在运行/刚完成，恢复状态并在需要时拉取 latest
  if (!DEMO_MODE && activeTaskId.value) {
    checking.value = true
    startSse(activeTaskId.value)
    startStatusPolling()
    await fetchCheckStatus()
  }
})

onUnmounted(() => {
  stopStatusPolling()
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  stopSse()
  resetRobotSearchState()
})

onDeactivated(() => {
  stopStatusPolling()
  stopSse()
  resetRobotSearchState()
})

onActivated(() => {
  if (selectedPlant.value && !availableTypes.value.length && !availableTechs.value.length) {
    loadRobotFilterOptions()
  }
  if (!DEMO_MODE && activeTaskId.value) {
    checking.value = true
    startSse(activeTaskId.value)
    startStatusPolling()
    fetchCheckStatus()
    return
  }
  if (checking.value) startStatusPolling()
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

/* 控制元素从右侧淡入 - 时间选择器 */
.entrance-fade-right-3 {
  animation: fadeRightIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.6s forwards;
  opacity: 0;
  transform: translateX(30px);
}

/* 控制元素从右侧淡入 - 执行按钮 */
.entrance-fade-right-4 {
  animation: fadeRightIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.7s forwards;
  opacity: 0;
  transform: translateX(30px);
}

@keyframes fadeRightIn {
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 控制元素从下方淡入 - 轨迹配置 */
.entrance-fade-up-1 {
  animation: fadeUpIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.5s forwards;
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
  padding: 24px 24px;
  max-width: 2600px;
  margin: 0 auto;
}

/* === Header === */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.title-area {
  display: flex;
  flex-direction: column;
}

.ios-title {
  font-size: 32px;
  letter-spacing: -0.5px;
  background: linear-gradient(180deg, #fff 40%, rgba(255,255,255,0.6));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
}

.ios-title .subtitle {
  font-size: 14px;
  color: #ffaa00;
  margin-left: 0;
  font-weight: 300;
  letter-spacing: 2px;
  display: block;
  margin-top: 4px;
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
  margin: 24px 0;
  overflow: visible;
}

.control-content {
  padding: 16px;
  position: relative;
  z-index: 1;
}

/* Control Center */
.control-row {
  display: flex;
  align-items: flex-end;
  gap: 14px;
  flex-wrap: wrap;
}

.main-controls {
  flex-wrap: nowrap;
  align-items: flex-end;
}

.secondary-row {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  flex-wrap: nowrap;
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.robot-select-wrap {
  position: relative;
}

.robot-select-guard {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
  background: transparent;
  cursor: not-allowed;
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
.time-selector { width: 380px; flex-shrink: 0; }
.filter-selector { width: 240px; flex-shrink: 0; }
.path-config { flex: 1; min-width: 350px; }

.button-wrapper {
  margin-left: 40px;
  margin-right: -20px;
  flex-shrink: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
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
  color: #fff;
}

.pulse-btn:not(:disabled):hover,
.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 195, 255, 0.5);
}

.pulse-btn.is-cancel {
  background: linear-gradient(135deg, #ff6b6b 0%, #ff3b30 100%);
  box-shadow: 0 6px 20px rgba(255, 59, 48, 0.35);
}

.pulse-btn.is-cancel:hover {
  transform: translateY(-1px);
}

.export-btn {
  margin-left: 0;
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border: none;
  box-shadow: 0 4px 14px rgba(34, 197, 94, 0.3);
}

.export-btn:hover {
  box-shadow: 0 8px 24px rgba(34, 197, 94, 0.5);
}

.config-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #8899aa;
}

.config-btn:hover {
  background: #ffaa00;
  border-color: #ffaa00;
  color: #fff;
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
  gap: 10px;
  overflow: hidden;
}

.result-container > * {
  overflow: hidden;
}

.result-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: rgba(10, 10, 15, 0.85);
  backdrop-filter: blur(30px);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5), 0 0 1px rgba(0, 204, 255, 0.2);
  border: 1px solid rgba(0, 204, 255, 0.15);
}

.summary-left {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.summary-left .label { font-size: 13px; color: #8da0b7; font-weight: 500; }
.summary-left .val { font-size: 24px; font-weight: 800; color: #00ccff; text-shadow: 0 0 20px rgba(0, 204, 255, 0.5); }
.summary-left .unit { font-size: 12px; color: #8da0b7; }

.summary-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.keyword-filter {
  width: 320px;
}

.filter-btn {
  border-radius: 10px;
}

.legend {
  font-size: 12px;
  color: #8da0b7;
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
.dot.ok { background: #00ff88; box-shadow: 0 0 10px #00ff88; }
.dot.warning { background: #ffae00; box-shadow: 0 0 10px #ffae00; }
.dot.bad { background: #ff4444; box-shadow: 0 0 10px #ff4444; }

/* Table Styling - 赛博朋克风格 */
.custom-table {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.8), 0 0 1px rgba(0, 204, 255, 0.2);
  background: rgba(10, 10, 15, 0.85);
  backdrop-filter: blur(30px);
  border: 1px solid rgba(0, 204, 255, 0.15);
}

/* 表格 CSS 变量覆盖 - 赛博朋克风格 */
.custom-table :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(0, 204, 255, 0.12);
  --el-table-header-bg-color: rgba(0, 204, 255, 0.08);
  --el-table-border-color: rgba(0, 204, 255, 0.1);
  color: #e6f0ff;
}

.custom-table :deep(.el-table__inner-wrapper) {
  overflow-x: auto;
}

.custom-table :deep(.el-table__body-wrapper) {
  overflow-x: auto;
}

.custom-table :deep(.el-table__row) {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.custom-table :deep(.el-table__row td) {
  padding: 0;
}

.custom-table :deep(.el-table__header th) {
  background: rgba(0, 204, 255, 0.08) !important;
  color: #00ccff !important;
  font-weight: 700;
  font-size: 11px;
  padding: 0;
  border-color: rgba(0, 204, 255, 0.15) !important;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.custom-table :deep(.el-table__body tr) {
  background: transparent !important;
}

.custom-table :deep(.el-table__body tr.el-table__row--striped) {
  background: rgba(0, 102, 255, 0.05) !important;
}

.custom-table :deep(.el-table__body td) {
  border-bottom: 1px solid rgba(0, 204, 255, 0.08) !important;
  background-color: transparent !important;
  color: #e6f0ff !important;
}

.custom-table :deep(.el-table__row:hover td) {
  background: rgba(0, 204, 255, 0.12) !important;
  box-shadow: inset 0 0 20px rgba(0, 204, 255, 0.05);
}

.custom-table :deep(.el-table__header .cell) {
  padding: 10px 6px;
  line-height: 1.3;
}

.custom-table :deep(.el-table__body .cell) {
  padding: 10px 6px;
  line-height: 1.3;
}

/* Fixed column handling */
.custom-table :deep(.el-table__fixed) {
  box-shadow: 2px 0 16px rgba(0, 204, 255, 0.15);
}

.custom-table :deep(.el-table__fixed-column) {
  background: rgba(10, 10, 15, 0.95) !important;
}

.custom-table :deep(.fixed-left-col .cell) {
  padding-left: 14px;
}

.robot-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #8da0b7;
  font-size: 14px;
}

.robot-name {
  color: #8da0b7;
}

.robot-info .el-icon {
  font-size: 16px;
  color: #00ccff;
}

/* Mono font columns */
.custom-table :deep(.mono-col .cell) {
  font-family: 'Share Tech Mono', 'SF Mono', Consolas, monospace;
  font-size: 13px;
  color: #8da0b7;
}

.mono {
  font-family: 'Share Tech Mono', 'SF Mono', Consolas, monospace;
  font-size: 13px;
  color: #8da0b7;
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
  font-size: 12px;
  font-weight: 500;
  display: inline-block;
  min-width: 38px;
  padding: 3px 4px;
  border-radius: 3px;
  white-space: nowrap;
}

.deviation-value.dev-success {
  color: #00ff88;
  background: rgba(0, 255, 136, 0.12);
  border: 1px solid rgba(0, 255, 136, 0.25);
  box-shadow: 0 0 8px rgba(0, 255, 136, 0.2);
}

.deviation-value.dev-warning {
  color: #ffae00;
  background: rgba(255, 174, 0, 0.12);
  border: 1px solid rgba(255, 174, 0, 0.25);
  box-shadow: 0 0 8px rgba(255, 174, 0, 0.2);
}

.deviation-value.dev-danger {
  color: #ff4444;
  background: rgba(255, 68, 68, 0.12);
  border: 1px solid rgba(255, 68, 68, 0.25);
  text-shadow: 0 0 10px rgba(255, 68, 68, 0.5);
  box-shadow: 0 0 8px rgba(255, 68, 68, 0.2);
}

.deviation-value.dev-neutral {
  color: #8da0b7;
  background: rgba(0, 204, 255, 0.05);
  border: 1px solid rgba(0, 204, 255, 0.1);
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
  padding: 12px 0;
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
  padding: 48px 0;
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

/* === Loading Spinner === */
.loading-state {
  text-align: center;
  padding: 48px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
}

.spinner {
  width: 100%;
  height: 100%;
  animation: rotate 1.5s linear infinite;
}

.spinner .path {
  stroke: #00c3ff;
  stroke-linecap: round;
  animation: dash 1.5s ease-in-out infinite;
}

@keyframes rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}

.loading-message {
  text-align: center;
}

.loading-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 6px;
}

.loading-tip {
  font-size: 13px;
  color: #8899aa;
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
  .filter-selector { width: calc(50% - 8px); }
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

  .filter-selector,
  .plant-selector,
  .robot-selector,
  .time-selector {
    width: 100%;
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
  border-color: rgba(255, 170, 0, 0.3) !important;
}

:deep(.el-select__wrapper.is-focused) {
  border-color: #ffaa00 !important;
  box-shadow: 0 0 0 3px rgba(255, 170, 0, 0.1) !important;
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
  border-color: rgba(255, 170, 0, 0.3) !important;
}

:deep(.el-date-editor.is-active) {
  border-color: #ffaa00 !important;
}

:deep(.el-input__prefix),
:deep(.el-input__suffix) {
  color: #8899aa !important;
}

/* Pagination */
:deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) {
  background: #ffaa00;
}

:deep(.el-pagination.is-background .el-pager li) {
  background: rgba(255, 255, 255, 0.03);
  color: #8899aa;
}

:deep(.el-pagination.is-background .el-pager li:hover) {
  background: rgba(255, 170, 0, 0.1);
}

:deep(.el-pagination button) {
  background: rgba(255, 255, 255, 0.03) !important;
  color: #8899aa !important;
}

:deep(.el-pagination button:hover) {
  background: rgba(255, 170, 0, 0.1) !important;
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
  background: rgba(255, 170, 0, 0.1);
  border: 1px solid rgba(255, 170, 0, 0.3);
  color: #ffaa00;
}

:deep(.add-path-btn) {
  border-style: dashed;
  color: #8899aa;
  background: rgba(255, 255, 255, 0.03);
}

:deep(.add-path-btn:hover) {
  border-color: #ffaa00;
  color: #ffaa00;
}

:deep(.el-check-tag.is-checked) {
  background: #ffaa00;
  border-color: #ffaa00;
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

<!-- 页面专属：DatePicker 蓝色主题（覆盖全局金色主题） -->
<style>
/* 专属 class 样式 - 蓝色主题 */
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

.trajectory-date-picker .el-time-spinner__item:hover,
.trajectory-date-picker .el-time-spinner__item.active,
.trajectory-date-picker .el-time-panel__btn.confirm {
  color: #00c3ff !important;
}

.trajectory-date-picker .el-time-spinner__item:hover {
  background: rgba(0, 195, 255, 0.1) !important;
}

.csv-path-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 14px;
  padding: 10px 14px;
  border: 1px solid rgba(188, 153, 84, 0.22);
  border-radius: 14px;
  background: rgba(255, 250, 239, 0.72);
}

.path-label,
.csv-dir-label {
  flex: 0 0 auto;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #7b5a1f;
  text-transform: uppercase;
}

.path-link {
  padding: 0;
  border: 0;
  background: transparent;
  color: #20508f;
  cursor: pointer;
  text-align: left;
  word-break: break-all;
}

.path-link:hover {
  color: #0d3970;
  text-decoration: underline;
}

.csv-browser-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.csv-dir-line {
  display: flex;
  gap: 10px;
  min-width: 0;
}

.csv-dir-value {
  color: #41556f;
  word-break: break-all;
}

.file-link {
  font-weight: 600;
}

.csv-unread-dot,
.csv-file-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #ff4d4f;
  box-shadow: 0 0 0 3px rgba(255, 77, 79, 0.18);
}

.csv-unread-dot {
  margin-left: 8px;
  vertical-align: middle;
}

.csv-file-dot {
  margin-right: 8px;
  vertical-align: middle;
}
</style>

<!-- Tooltip 样式：亮白色文字 -->
<style>
.el-tooltip__popper.is-dark {
  background-color: rgba(30, 30, 30, 0.95) !important;
  border: 1px solid rgba(0, 204, 255, 0.2) !important;
}

.el-tooltip__popper.is-dark .el-tooltip__inner {
  color: #ffffff !important;
  background-color: transparent !important;
}
</style>

<!-- 全局样式：Checkbox Dark Theme（金色） -->
<style>
/* --- Checkbox Dark Theme（金色） --- */
.el-checkbox {
  color: #aaa !important;
}

.el-checkbox__input.is-checked .el-checkbox__inner {
  background-color: #ffaa00 !important;
  border-color: #ffaa00 !important;
  box-shadow: 0 0 10px rgba(255, 170, 0, 0.4) !important;
}

.el-checkbox__inner {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
}

.el-checkbox__inner:hover {
  border-color: rgba(255, 170, 0, 0.4) !important;
}

.el-checkbox__label {
  color: #aaa !important;
}

.el-select-dropdown__item .el-checkbox {
  color: #aaa !important;
}
</style>
