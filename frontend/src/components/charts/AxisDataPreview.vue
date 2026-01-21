<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import TimeSeriesChart from './TimeSeriesChart.vue'
import request from '@/utils/request'
import { DEMO_MODE } from '@/config/appConfig'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  robotPartNo: {
    type: String,
    default: ''
  },
  axisKey: {
    type: String,
    default: 'A1'
  }
})

const emit = defineEmits(['update:visible'])

const loading = ref(false)
const chartData = ref(null)
const selectedProgram = ref('')

// Axis configuration - same as bb project
const axisConfig = {
  A1: { min: 'MinCurr_A1', max: 'MAXCurr_A1', curr: 'Curr_A1', temp: 'Tem_1', pos: 'AxisP1', lq: 'Curr_A1_LQ', hq: 'Curr_A1_HQ', speed: 'Speed1', torque: 'Torque1', fol: 'Fol1' },
  A2: { min: 'MinCurr_A2', max: 'MAXCurr_A2', curr: 'Curr_A2', temp: 'Tem_2', pos: 'AxisP2', lq: 'Curr_A2_LQ', hq: 'Curr_A2_HQ', speed: 'Speed2', torque: 'Torque2', fol: 'Fol2' },
  A3: { min: 'MinCurr_A3', max: 'MAXCurr_A3', curr: 'Curr_A3', temp: 'Tem_3', pos: 'AxisP3', lq: 'Curr_A3_LQ', hq: 'Curr_A3_HQ', speed: 'Speed3', torque: 'Torque3', fol: 'Fol3' },
  A4: { min: 'MinCurr_A4', max: 'MAXCurr_A4', curr: 'Curr_A4', temp: 'Tem_4', pos: 'AxisP4', lq: 'Curr_A4_LQ', hq: 'Curr_A4_HQ', speed: 'Speed4', torque: 'Torque4', fol: 'Fol4' },
  A5: { min: 'MinCurr_A5', max: 'MAXCurr_A5', curr: 'Curr_A5', temp: 'Tem_5', pos: 'AxisP5', lq: 'Curr_A5_LQ', hq: 'Curr_A5_HQ', speed: 'Speed5', torque: 'Torque5', fol: 'Fol5' },
  A6: { min: 'MinCurr_A6', max: 'MAXCurr_A6', curr: 'Curr_A6', temp: 'Tem_6', pos: 'AxisP6', lq: 'Curr_A6_LQ', hq: 'Curr_A6_HQ', speed: 'Speed6', torque: 'Torque6', fol: 'Fol6' },
  A7: { min: 'MinCurr_E1', max: 'MAXCurr_E1', curr: 'Curr_E1', temp: 'Tem_7', pos: 'AxisP7', lq: 'Curr_E1_LQ', hq: 'Curr_E1_HQ', speed: 'Speed7', torque: 'Torque7', fol: 'Fol7' }
}

const currentConfig = computed(() => axisConfig[props.axisKey] || axisConfig.A1)

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const axisLabel = computed(() => {
  const labels = {
    A1: '供电/线束',
    A2: '温度/散热',
    A3: '通信/网络',
    A4: '传感器/对位',
    A5: '抓手/执行器',
    A6: '控制/程序',
    A7: '安全/急停'
  }
  return `${props.axisKey}（${labels[props.axisKey] || ''}）`
})

const programOptions = computed(() => {
  const list = chartData.value?.programs
  if (Array.isArray(list)) return list.map(String)

  const set = new Set()
  const rows = chartData.value?.data || []
  rows.forEach((r) => {
    if (r?.P_name) set.add(String(r.P_name))
  })
  return Array.from(set).sort()
})

// Load axis data - try API first, fallback to mock data
const loadAxisData = async () => {
  if (!props.robotPartNo || !props.axisKey) return

  loading.value = true
  try {
    if (DEMO_MODE) {
      await new Promise(resolve => setTimeout(resolve, 300))
      chartData.value = generateMockData()
      return
    }

    const response = await request.get('/robots/axis-data/', {
      params: {
        part_no: props.robotPartNo,
        axis: props.axisKey,
        program: selectedProgram.value || undefined,
      },
      silent: true,
    })
    if (response?.error) {
      throw new Error(response.error)
    }
    chartData.value = response
  } catch (error) {
    chartData.value = null
    const msg = error?.response?.data?.error || error?.response?.data?.detail || error?.message || '服务器错误'
    ElMessage.error(`加载轴数据失败：${msg}`)
  } finally {
    loading.value = false
  }
}

// Generate mock data for demo mode
const generateMockData = () => {
  const data = []
  const aggregated = []
  const now = Date.now()

  // Generate time series data
  for (let i = 0; i < 100; i++) {
    const sort = i
    const timestamp = new Date(now - (100 - i) * 60000).toISOString()
    const baseValue = 50 + Math.random() * 30
    data.push({
      sort,
      Timestamp: timestamp,
      MinCurr_A1: baseValue - 20,
      MAXCurr_A1: baseValue + 20,
      Curr_A1: baseValue + (Math.random() - 0.5) * 10,
      Tem_1: 25 + Math.random() * 30,
      AxisP1: -180 + Math.random() * 360,
      Speed1: Math.random() * 100,
      Torque1: Math.random() * 50,
      Fol1: Math.random() * 2,
      SNR_C: `SNR${1000 + i}`,
      P_name: `Program_${Math.floor(i / 10) + 1}`,
      // Add fields for all axes
      MinCurr_A2: baseValue - 20, MAXCurr_A2: baseValue + 20, Curr_A2: baseValue + (Math.random() - 0.5) * 10,
      Tem_2: 25 + Math.random() * 30, AxisP2: -180 + Math.random() * 360, Speed2: Math.random() * 100, Torque2: Math.random() * 50, Fol2: Math.random() * 2,
      Curr_A2_LQ: baseValue - 10, Curr_A2_HQ: baseValue + 10,
      MinCurr_A3: baseValue - 20, MAXCurr_A3: baseValue + 20, Curr_A3: baseValue + (Math.random() - 0.5) * 10,
      Tem_3: 25 + Math.random() * 30, AxisP3: -180 + Math.random() * 360, Speed3: Math.random() * 100, Torque3: Math.random() * 50, Fol3: Math.random() * 2,
      Curr_A3_LQ: baseValue - 10, Curr_A3_HQ: baseValue + 10,
      MinCurr_A4: baseValue - 20, MAXCurr_A4: baseValue + 20, Curr_A4: baseValue + (Math.random() - 0.5) * 10,
      Tem_4: 25 + Math.random() * 30, AxisP4: -180 + Math.random() * 360, Speed4: Math.random() * 100, Torque4: Math.random() * 50, Fol4: Math.random() * 2,
      Curr_A4_LQ: baseValue - 10, Curr_A4_HQ: baseValue + 10,
      MinCurr_A5: baseValue - 20, MAXCurr_A5: baseValue + 20, Curr_A5: baseValue + (Math.random() - 0.5) * 10,
      Tem_5: 25 + Math.random() * 30, AxisP5: -180 + Math.random() * 360, Speed5: Math.random() * 100, Torque5: Math.random() * 50, Fol5: Math.random() * 2,
      Curr_A5_LQ: baseValue - 10, Curr_A5_HQ: baseValue + 10,
      MinCurr_A6: baseValue - 20, MAXCurr_A6: baseValue + 20, Curr_A6: baseValue + (Math.random() - 0.5) * 10,
      Tem_6: 25 + Math.random() * 30, AxisP6: -180 + Math.random() * 360, Speed6: Math.random() * 100, Torque6: Math.random() * 50, Fol6: Math.random() * 2,
      Curr_A6_LQ: baseValue - 10, Curr_A6_HQ: baseValue + 10,
      MinCurr_E1: baseValue - 20, MAXCurr_E1: baseValue + 20, Curr_E1: baseValue + (Math.random() - 0.5) * 10,
      Tem_7: 25 + Math.random() * 30, AxisP7: -180 + Math.random() * 360, Speed7: Math.random() * 100, Torque7: Math.random() * 50, Fol7: Math.random() * 2,
      Curr_E1_LQ: baseValue - 10, Curr_E1_HQ: baseValue + 10
    })
  }

  // Generate aggregated data
  for (let i = 0; i < 20; i++) {
    const baseValue = 50 + Math.random() * 30
    aggregated.push({
      SNR_C: `SNR${1000 + i * 5}`,
      P_name: `Program_${i + 1}`,
      MinCurr_A1: baseValue - 20, MAXCurr_A1: baseValue + 20, Curr_A1_LQ: baseValue - 10, Curr_A1_HQ: baseValue + 10,
      MinCurr_A2: baseValue - 20, MAXCurr_A2: baseValue + 20, Curr_A2_LQ: baseValue - 10, Curr_A2_HQ: baseValue + 10,
      MinCurr_A3: baseValue - 20, MAXCurr_A3: baseValue + 20, Curr_A3_LQ: baseValue - 10, Curr_A3_HQ: baseValue + 10,
      MinCurr_A4: baseValue - 20, MAXCurr_A4: baseValue + 20, Curr_A4_LQ: baseValue - 10, Curr_A4_HQ: baseValue + 10,
      MinCurr_A5: baseValue - 20, MAXCurr_A5: baseValue + 20, Curr_A5_LQ: baseValue - 10, Curr_A5_HQ: baseValue + 10,
      MinCurr_A6: baseValue - 20, MAXCurr_A6: baseValue + 20, Curr_A6_LQ: baseValue - 10, Curr_A6_HQ: baseValue + 10,
      MinCurr_E1: baseValue - 20, MAXCurr_E1: baseValue + 20, Curr_E1_LQ: baseValue - 10, Curr_E1_HQ: baseValue + 10
    })
  }

  return { data, aggregated }
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    loadAxisData()
  }
})

watch(() => [props.robotPartNo, props.axisKey], () => {
  if (props.visible) {
    loadAxisData()
  }
})

watch(selectedProgram, () => {
  if (props.visible) loadAxisData()
})

watch(chartData, () => {
  if (selectedProgram.value && !programOptions.value.includes(selectedProgram.value)) {
    selectedProgram.value = ''
  }
})
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    :title="`${axisLabel} - 数据详情`"
    width="90%"
    top="5vh"
    destroy-on-close
  >
    <div v-loading="loading" class="axis-preview-content">
      <template v-if="chartData">
        <div class="chart-filters">
          <el-form label-position="top">
            <el-row :gutter="12">
              <el-col :xs="24" :sm="12" :md="8">
                <el-form-item label="应用程序（Name_C）">
                  <el-select v-model="selectedProgram" placeholder="全部应用程序" clearable filterable>
                    <el-option v-for="p in programOptions" :key="p" :label="p" :value="p" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
        <div class="chart-wrapper" v-if="chartData.data && chartData.data.length > 0">
          <TimeSeriesChart
            :data="chartData.data || []"
            :config="currentConfig"
            :axis="axisKey"
          />
        </div>
        <el-empty v-else description="暂无时间序列数据" />
      </template>
      <el-empty v-else-if="!loading" description="加载数据失败" />
    </div>

    <template #footer>
      <el-button @click="dialogVisible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.axis-preview-content {
  min-height: 920px;
}

.chart-filters :deep(.el-form-item) {
  margin-bottom: 8px;
}

.chart-filters :deep(.el-select) {
  width: 100%;
}

.chart-wrapper {
  width: 100%;
  height: 860px;
}
</style>
