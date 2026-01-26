<template>
  <div class="trajectory">
    <el-card class="filter-card">
      <template #header>
        <div class="card-header">
          <div class="title">
            <span class="title-text">关键轨迹检查</span>
            <span class="title-sub">配置车间、关键路径关键字和机器人列表，执行抓放点电流异常检查</span>
          </div>
          <el-button type="primary" :icon="Download" @click="handleExport" :disabled="!checkResult">
            导出CSV
          </el-button>
        </div>
      </template>

      <!-- 车间选择 -->
      <el-divider content-position="left">
        <span class="section-title">车间选择</span>
      </el-divider>
      <el-row :gutter="16" class="plant-row">
        <el-col :xs="24" :sm="12" :md="8">
          <el-select
            v-model="selectedPlant"
            placeholder="选择车间"
            clearable
            filterable
            :loading="plantsLoading"
            @change="handlePlantChange"
            style="width: 100%"
          >
            <el-option
              v-for="plant in availablePlants"
              :key="plant.key"
              :label="plant.name"
              :value="plant.key"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="16">
          <div class="plant-hint">
            <el-icon><InfoFilled /></el-icon>
            <span v-if="selectedPlant">已选择车间: {{ getPlantName(selectedPlant) }}</span>
            <span v-else>选择车间后可加载对应机器人表</span>
          </div>
        </el-col>
      </el-row>

      <!-- 关键路径配置 -->
      <el-divider content-position="left">
        <span class="section-title">关键路径配置</span>
      </el-divider>
      <el-row :gutter="16" class="key-paths-row">
        <el-col :xs="24" :sm="12" :md="6">
          <el-input v-model="keyPath1" placeholder="KeyPath1 (如: R1/CO)" clearable>
            <template #prepend>KeyPath1</template>
          </el-input>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-input v-model="keyPath2" placeholder="KeyPath2 (如: R1/DO)" clearable>
            <template #prepend>KeyPath2</template>
          </el-input>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-input v-model="keyPath3" placeholder="KeyPath3 (如: R1/CN)" clearable>
            <template #prepend>KeyPath3</template>
          </el-input>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-input v-model="keyPath4" placeholder="KeyPath4 (如: R1/DN)" clearable>
            <template #prepend>KeyPath4</template>
          </el-input>
        </el-col>
      </el-row>

      <!-- 时间范围配置 -->
      <el-divider content-position="left">
        <span class="section-title">时间范围</span>
      </el-divider>
      <el-row :gutter="16" class="time-row">
        <el-col :xs="24" :sm="24" :md="16">
          <el-date-picker
            v-model="timeRange"
            type="datetimerange"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            :default-time="defaultTime"
            unlink-panels
            style="width: 100%"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-select v-model="quickRange" placeholder="快速选择" clearable @change="handleQuickRangeChange">
            <el-option label="最近1小时" :value="1" />
            <el-option label="最近6小时" :value="6" />
            <el-option label="最近24小时" :value="24" />
            <el-option label="最近7天" :value="168" />
            <el-option label="最近30天" :value="720" />
          </el-select>
        </el-col>
      </el-row>

      <!-- 机器人选择 -->
      <el-divider content-position="left">
        <span class="section-title">机器人表选择</span>
      </el-divider>
      <el-row :gutter="16" class="robot-row">
        <el-col :xs="24" :sm="24" :md="24">
          <el-select
            v-model="selectedRobots"
            placeholder="请先选择车间，然后选择要检查的机器人表"
            clearable
            filterable
            multiple
            collapse-tags
            collapse-tags-tooltip
            :loading="robotsLoading"
            :disabled="!selectedPlant"
            style="width: 100%"
          >
            <el-option
              v-for="robot in availableRobots"
              :key="robot.value"
              :label="robot.label"
              :value="robot.value"
            />
            <template #footer>
              <el-button text @click="selectAllRobots" :disabled="!selectedPlant">全选</el-button>
              <el-button text @click="clearRobots">清空</el-button>
            </template>
          </el-select>
          <div class="robot-hint">
            <el-icon><InfoFilled /></el-icon>
            <span>已选择 {{ selectedRobots.length }} 个机器人表</span>
          </div>
        </el-col>
      </el-row>

      <!-- 执行按钮 -->
      <el-row :gutter="16" class="action-row">
        <el-col :xs="24" :sm="24" :md="24">
          <el-button
            type="primary"
            size="large"
            :icon="Search"
            :loading="checking"
            :disabled="selectedRobots.length === 0"
            @click="executeCheck"
            style="width: 100%"
          >
            执行检查
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 结果展示 -->
    <el-card v-if="checkResult">
      <template #header>
        <div class="table-header">
          <span>检查结果</span>
          <span class="table-meta">
            共 {{ checkResult.count || 0 }} 条记录
            <span v-if="checkResult.count > 0" class="success-badge">检查成功</span>
            <span v-else class="warning-badge">无数据</span>
          </span>
        </div>
      </template>

      <el-table
        :data="pagedRows"
        stripe
        height="560"
        v-loading="checking"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="robot" label="Robot" width="180" sortable show-overflow-tooltip />
        <el-table-column prop="Name_C" label="Name_C" width="120" sortable show-overflow-tooltip />
        <el-table-column prop="SNR_C" label="SNR_C" width="100" sortable />
        <el-table-column prop="SUB" label="SUB" width="100" sortable />
        <el-table-column prop="P_name" label="程序名称" width="200" sortable show-overflow-tooltip />

        <!-- 电流相关列 -->
        <el-table-column prop="Curr_A1_LQ" label="A1_LQ" width="90" sortable>
          <template #default="{ row }">
            <span class="mono">{{ formatValue(row.Curr_A1_LQ) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="Curr_A1_HQ" label="A1_HQ" width="90" sortable>
          <template #default="{ row }">
            <span class="mono">{{ formatValue(row.Curr_A1_HQ) }}</span>
          </template>
        </el-table-column>

        <!-- 偏差值 -->
        <el-table-column prop="QH1" label="QH1" width="90" sortable>
          <template #default="{ row }">
            <span :class="getValueClass(row.QH1)" class="mono">{{ formatValue(row.QH1) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="QL1" label="QL1" width="90" sortable>
          <template #default="{ row }">
            <span :class="getValueClass(row.QL1)" class="mono">{{ formatValue(row.QL1) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="size" label="样本数" width="90" sortable />
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="checkResult.count || 0"
        :page-sizes="[10, 20, 50, 100, 200]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pager"
      />
    </el-card>

    <!-- 错误提示 -->
    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      :closable="false"
      show-icon
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Search, InfoFilled } from '@element-plus/icons-vue'
import { DEMO_MODE } from '@/config/appConfig'
import { getRobotGroups, getGripperRobotTables, executeGripperCheck } from '@/api/robots'

const defaultTime = [new Date(2000, 1, 1, 8, 0, 0), new Date(2000, 1, 1, 18, 0, 0)]

// 车间相关
const availablePlants = ref([])
const selectedPlant = ref('')
const plantsLoading = ref(false)

// 关键路径配置
const keyPath1 = ref('XLHP')
const keyPath2 = ref('PWLD')
const keyPath3 = ref('')
const keyPath4 = ref('')

// 时间范围
const timeRange = ref([
  new Date(Date.now() - 7 * 24 * 3600_000),
  new Date()
])
const quickRange = ref(null)

// 机器人选择
const availableRobots = ref([])
const selectedRobots = ref([])
const robotsLoading = ref(false)

// 执行状态
const checking = ref(false)
const checkResult = ref(null)
const errorMessage = ref('')

// 分页和排序
const currentPage = ref(1)
const pageSize = ref(20)
const sortState = ref({ prop: 'robot', order: 'ascending' })

// 获取车间名称
const getPlantName = (key) => {
  const plant = availablePlants.value.find(p => p.key === key)
  return plant ? plant.name : key
}

// 加载车间列表
const loadPlantGroups = async () => {
  if (DEMO_MODE) {
    availablePlants.value = [
      { key: 'plant_a', name: '车间A' },
      { key: 'plant_b', name: '车间B' },
      { key: 'plant_c', name: '车间C' }
    ]
    return
  }

  plantsLoading.value = true
  try {
    const response = await getRobotGroups()
    availablePlants.value = response || []
  } catch (e) {
    ElMessage.error('获取车间列表失败: ' + (e?.message || '未知错误'))
  } finally {
    plantsLoading.value = false
  }
}

// 车间变化时重新加载机器人表
const handlePlantChange = () => {
  selectedRobots.value = []
  availableRobots.value = []
  loadRobotTables()
}

// 获取可用机器人表列表
const loadRobotTables = async () => {
  if (!selectedPlant.value) {
    availableRobots.value = []
    return
  }

  if (DEMO_MODE) {
    const mockRobots = {
      'plant_a': [
        { value: 'as33_020rb_400', label: 'as33_020rb_400' },
        { value: 'as33_020rb_401', label: 'as33_020rb_401' },
        { value: 'as33_020rb_402', label: 'as33_020rb_402' }
      ],
      'plant_b': [
        { value: 'as33_020rb_500', label: 'as33_020rb_500' },
        { value: 'as33_020rb_501', label: 'as33_020rb_501' }
      ],
      'plant_c': [
        { value: 'as33_020rb_600', label: 'as33_020rb_600' }
      ]
    }
    availableRobots.value = mockRobots[selectedPlant.value] || []
    return
  }

  robotsLoading.value = true
  try {
    const response = await getGripperRobotTables({ group: selectedPlant.value })
    availableRobots.value = response.results || []
  } catch (e) {
    ElMessage.error('获取机器人表列表失败: ' + (e?.message || '未知错误'))
  } finally {
    robotsLoading.value = false
  }
}

// 全选机器人
const selectAllRobots = () => {
  selectedRobots.value = availableRobots.value.map(r => r.value)
}

// 清空选择
const clearRobots = () => {
  selectedRobots.value = []
}

// 快速时间范围选择
const handleQuickRangeChange = (hours) => {
  if (!hours) return
  const now = new Date()
  const start = new Date(now.getTime() - hours * 3600_000)
  timeRange.value = [start, now]
}

// 构建关键路径列表
const getKeyPaths = () => {
  const paths = []
  if (keyPath1.value) paths.push(keyPath1.value)
  if (keyPath2.value) paths.push(keyPath2.value)
  if (keyPath3.value) paths.push(keyPath3.value)
  if (keyPath4.value) paths.push(keyPath4.value)
  return paths
}

// 执行检查
const executeCheck = async () => {
  if (selectedRobots.value.length === 0) {
    ElMessage.warning('请至少选择一个机器人表')
    return
  }

  if (!timeRange.value || timeRange.value.length !== 2) {
    ElMessage.warning('请选择有效的时间范围')
    return
  }

  checking.value = true
  checkResult.value = null
  errorMessage.value = ''

  try {
    const payload = {
      start_time: timeRange.value[0].toISOString(),
      end_time: timeRange.value[1].toISOString(),
      gripper_list: selectedRobots.value,
      key_paths: getKeyPaths()
    }

    if (DEMO_MODE) {
      // 演示模式：返回模拟数据
      await new Promise(resolve => setTimeout(resolve, 1500))
      checkResult.value = {
        success: true,
        count: 50,
        data: generateMockData(50),
        columns: ['robot', 'Name_C', 'SNR_C', 'SUB', 'P_name', 'Curr_A1_LQ', 'Curr_A1_HQ', 'QH1', 'QL1', 'size']
      }
    } else {
      checkResult.value = await executeGripperCheck(payload)
    }

    if (checkResult.value.success) {
      if (checkResult.value.count === 0) {
        ElMessage.warning('未找到匹配的数据')
      } else {
        ElMessage.success(`检查完成，共 ${checkResult.value.count} 条记录`)
      }
      currentPage.value = 1
    } else {
      errorMessage.value = checkResult.value.error || '检查失败'
      ElMessage.error(errorMessage.value)
    }
  } catch (e) {
    errorMessage.value = e?.message || '执行检查时发生错误'
    ElMessage.error(errorMessage.value)
  } finally {
    checking.value = false
  }
}

// 生成演示数据
const generateMockData = (count) => {
  const data = []
  for (let i = 0; i < count; i++) {
    data.push({
      robot: `as33_020rb_${400 + (i % 10)}`,
      Name_C: `R1/${['CO', 'DO', 'CN', 'DN'][i % 4]}`,
      SNR_C: Math.floor(Math.random() * 10000),
      SUB: `SUB_${i}`,
      P_name: `P_Program_${i % 20}`,
      Curr_A1_LQ: (Math.random() * 2).toFixed(3),
      Curr_A1_HQ: (Math.random() * 5 + 2).toFixed(3),
      QH1: (Math.random() * 0.5).toFixed(3),
      QL1: (Math.random() * 0.5).toFixed(3),
      size: Math.floor(Math.random() * 100) + 10
    })
  }
  return data
}

// 格式化值
const formatValue = (val) => {
  if (val === null || val === undefined || val === 'N') return '-'
  if (typeof val === 'number') return val.toFixed(3)
  return String(val)
}

// 获取值的样式类
const getValueClass = (val) => {
  const numVal = parseFloat(val)
  if (isNaN(numVal) || val === 'N') return ''
  return numVal > 0.1 ? 'bad' : 'ok'
}

// 分页数据
const pagedRows = computed(() => {
  if (!checkResult.value?.data) return []

  const start = (currentPage.value - 1) * pageSize.value
  return checkResult.value.data.slice(start, start + pageSize.value)
})

// 排序变化
const handleSortChange = ({ prop, order }) => {
  sortState.value = { prop, order }

  if (!checkResult.value?.data) return

  const dir = order === 'ascending' ? 1 : -1
  checkResult.value.data.sort((a, b) => {
    const av = a[prop]
    const bv = b[prop]
    if (av === bv) return 0

    // 数值比较
    const numA = parseFloat(av)
    const numB = parseFloat(bv)
    if (!isNaN(numA) && !isNaN(numB)) {
      return (numA - numB) * dir
    }

    // 字符串比较
    return String(av || '').localeCompare(String(bv || ''), 'zh-CN') * dir
  })
}

// 导出CSV
const handleExport = () => {
  if (!checkResult.value?.data || checkResult.value.data.length === 0) {
    ElMessage.warning('没有数据可导出')
    return
  }

  // 生成CSV内容
  const headers = checkResult.value.columns || Object.keys(checkResult.value.data[0])
  const csvContent = [
    headers.join(','),
    ...checkResult.value.data.map(row =>
      headers.map(h => {
        const val = row[h]
        return val === null || val === undefined ? '' : `"${String(val).replace(/"/g, '""')}"`
      }).join(',')
    )
  ].join('\n')

  // 下载文件
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `gripper_check_${selectedPlant.value}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`
  link.click()
  URL.revokeObjectURL(url)

  ElMessage.success('导出成功')
}

// 初始化
onMounted(() => {
  loadPlantGroups()
})
</script>

<style scoped>
.trajectory {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-card :deep(.el-input__wrapper),
.filter-card :deep(.el-select__wrapper),
.filter-card :deep(.el-date-editor.el-input__wrapper) {
  border-radius: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.plant-row,
.key-paths-row,
.time-row,
.robot-row,
.action-row {
  margin-bottom: 12px;
}

.plant-hint,
.robot-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
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
  font-weight: 800;
}

.title-sub {
  color: var(--app-muted);
  font-size: 12px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.table-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--app-muted);
  font-size: 12px;
}

.success-badge {
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
  font-size: 12px;
}

.warning-badge {
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
  font-size: 12px;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.ok {
  color: rgba(15, 23, 42, 0.7);
}

.bad {
  color: #b91c1c;
  font-weight: 800;
}

.pager {
  margin-top: 16px;
  justify-content: center;
}

:deep(.el-input-group__prepend) {
  background-color: var(--el-fill-color-light);
  color: var(--el-text-color-regular);
  font-weight: 500;
}
</style>
