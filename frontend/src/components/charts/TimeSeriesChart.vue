<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    required: true
  },
  config: {
    type: Object,
    required: true
  },
  axis: {
    type: String,
    required: true
  }
})

const chartRef = ref(null)
let chartInstance = null
let resizeObserver = null

// Prepare chart data
const chartData = computed(() => {
  if (!props.data || props.data.length === 0) return []

  return props.data.map(item => ({
    sort: item.sort,
    timestamp: item.Timestamp,
    minCurr: item[props.config.min],
    maxCurr: item[props.config.max],
    curr: item[props.config.curr],
    temp: item[props.config.temp],
    pos: item[props.config.pos],
    speed: item[props.config.speed],
    torque: item[props.config.torque],
    fol: item[props.config.fol],
    snr: item.SNR_C,
    pname: item.P_name
  }))
})

// Chart option
const getChartOption = () => {
  const data = chartData.value

  return {
    title: {
      text: `${props.axis} - 时间序列数据`,
      left: 'center',
      top: 8,
      textStyle: { fontSize: 14, fontWeight: 600 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      confine: true,
      formatter: (params) => {
        const idx = params[0].dataIndex
        const d = data[idx]
        let result = `时间: ${d?.timestamp || '-'}<br/>`
        result += `SNR: ${d?.snr || '-'}<br/>`
        result += `程序: ${d?.pname || '-'}<br/>`
        params.forEach(param => {
          result += `${param.seriesName}: ${param.value[1]}<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['最小电流', '最大电流', '电流', '温度', '位置', '速度', '扭矩', '跟随误差'],
      top: 34,
      textStyle: { fontSize: 11 }
    },
    grid: [
      { left: 60, right: 28, top: 78, height: 150 },
      { left: 60, right: 28, top: 240, height: 105 },
      { left: 60, right: 28, top: 355, height: 105 },
      { left: 60, right: 28, top: 470, height: 105 },
      { left: 60, right: 28, top: 585, height: 105 },
      { left: 60, right: 28, top: 700, height: 105 }
    ],
    xAxis: [
      {
        gridIndex: 0,
        type: 'value',
        name: 'Motion Time',
        nameTextStyle: { fontSize: 10, fontWeight: 600 },
        axisLabel: { show: false }
      },
      { gridIndex: 1, type: 'value', axisLabel: { show: false } },
      { gridIndex: 2, type: 'value', axisLabel: { show: false } },
      { gridIndex: 3, type: 'value', axisLabel: { show: false } },
      { gridIndex: 4, type: 'value', axisLabel: { show: false } },
      { gridIndex: 5, type: 'value' }
    ],
    yAxis: [
      {
        gridIndex: 0,
        type: 'value',
        name: 'Current %',
        position: 'left',
        nameTextStyle: { fontSize: 10, fontWeight: 600 }
      },
      {
        gridIndex: 1,
        type: 'value',
        name: 'Temperature',
        min: 15,
        max: 100,
        nameTextStyle: { fontSize: 10, fontWeight: 600 }
      },
      {
        gridIndex: 2,
        type: 'value',
        name: 'Position',
        nameTextStyle: { fontSize: 10, fontWeight: 600 }
      },
      {
        gridIndex: 3,
        type: 'value',
        name: 'Speed',
        nameTextStyle: { fontSize: 10, fontWeight: 600 }
      },
      {
        gridIndex: 4,
        type: 'value',
        name: 'Torque',
        nameTextStyle: { fontSize: 10, fontWeight: 600 }
      },
      {
        gridIndex: 5,
        type: 'value',
        name: 'Following error',
        nameTextStyle: { fontSize: 10, fontWeight: 600 }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1, 2, 3, 4, 5],
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1, 2, 3, 4, 5],
        start: 0,
        end: 100,
        height: 22,
        bottom: 18
      }
    ],
    series: [
      {
        name: '最小电流',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: data.map(d => [d.sort, d.minCurr]),
        lineStyle: { color: 'red', width: 2 },
        step: 'middle',
        symbol: 'none'
      },
      {
        name: '最大电流',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: data.map(d => [d.sort, d.maxCurr]),
        lineStyle: { color: 'red', width: 2 },
        step: 'middle',
        symbol: 'none'
      },
      {
        name: '电流',
        type: 'scatter',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: data.map(d => [d.sort, d.curr]),
        symbolSize: 4,
        itemStyle: { color: '#5470c6', opacity: 0.7 }
      },
      {
        name: '温度',
        type: 'scatter',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: data.map(d => [d.sort, d.temp]),
        symbolSize: 4,
        itemStyle: { color: 'orange' }
      },
      {
        name: '位置',
        type: 'scatter',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: data.map(d => [d.sort, d.pos]),
        symbolSize: 4,
        itemStyle: { color: 'green' }
      },
      {
        name: '速度',
        type: 'scatter',
        xAxisIndex: 3,
        yAxisIndex: 3,
        data: data.map(d => [d.sort, d.speed]),
        symbolSize: 4,
        itemStyle: { color: 'blue' }
      },
      {
        name: '扭矩',
        type: 'scatter',
        xAxisIndex: 4,
        yAxisIndex: 4,
        data: data.map(d => [d.sort, d.torque]),
        symbolSize: 4,
        itemStyle: { color: 'sienna' }
      },
      {
        name: '跟随误差',
        type: 'scatter',
        xAxisIndex: 5,
        yAxisIndex: 5,
        data: data.map(d => [d.sort, d.fol]),
        symbolSize: 4,
        itemStyle: { color: 'limegreen' }
      }
    ]
  }
}

const initChart = () => {
  if (!chartRef.value) return

  const existing = echarts.getInstanceByDom(chartRef.value)
  if (existing) existing.dispose()

  chartInstance = echarts.init(chartRef.value)
  chartInstance.setOption(getChartOption(), { notMerge: true, lazyUpdate: true })
  chartInstance.resize()
}

const resizeChart = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(() => {
  nextTick(() => initChart())
  window.addEventListener('resize', resizeChart)
  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => resizeChart())
    if (chartRef.value) resizeObserver.observe(chartRef.value)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

watch(() => [props.data, props.config, props.axis], () => {
  if (chartInstance) {
    chartInstance.setOption(getChartOption(), { notMerge: true, lazyUpdate: true })
    chartInstance.resize()
  }
}, { deep: true })
</script>

<template>
  <div class="time-series-chart">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<style scoped>
.time-series-chart {
  width: 100%;
  height: 100%;
}

.chart-container {
  width: 100%;
  height: 100%;
  min-height: 840px;
}
</style>
