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
  program: {
    type: String,
    default: ''
  }
})

const chartRef = ref(null)
let chartInstance = null
let resizeObserver = null

// Prepare chart data - use computed for reactivity
const chartData = computed(() => {
  if (!props.data || props.data.length === 0) {
    return { x: [], lq: [], hq: [], min: [], max: [], labels: [] }
  }

  return {
    x: props.data.map(d => String(d.SNR_C || '')),
    lq: props.data.map(d => Number(d[props.config.lq]) || 0),
    hq: props.data.map(d => Number(d[props.config.hq]) || 0),
    min: props.data.map(d => Number(d[props.config.min]) || 0),
    max: props.data.map(d => Number(d[props.config.max]) || 0),
    labels: props.data.map(d => d.P_name || '')
  }
})

// Chart option
const getChartOption = () => {
  const data = chartData.value

  // Calculate Y-axis range based on actual data
  const allValues = [...data.lq, ...data.hq, ...data.min, ...data.max].filter(v => v !== null && v !== undefined)
  const hasData = allValues.length > 0 && allValues.some(v => v !== 0)

  let yAxisMin, yAxisMax
  if (hasData) {
    const minValue = Math.min(...allValues)
    const maxValue = Math.max(...allValues)
    const range = maxValue - minValue
    yAxisMin = minValue - (range * 0.1 || 1)
    yAxisMax = maxValue + (range * 0.1 || 1)
  } else {
    yAxisMin = -10
    yAxisMax = 10
  }

  return {
    title: {
      text: props.program || '聚合数据',
      left: 'center',
      top: 12,
      textStyle: { fontSize: 18, fontWeight: 600 }
    },
    grid: {
      left: 56,
      right: 28,
      top: 88,
      bottom: 86,
      containLabel: true
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      confine: true,
      formatter: (params) => {
        const idx = params[0].dataIndex
        let result = `SNR: ${data.x[idx]}<br/>`
        if (data.labels[idx]) {
          result += `程序: ${data.labels[idx]}<br/>`
        }
        params.forEach(param => {
          result += `${param.seriesName}: ${param.value}<br/>`
        })
        return result
      },
      textStyle: { fontSize: 13 }
    },
    legend: {
      data: ['1%分位数', '99%分位数', '参考范围'],
      top: 44,
      textStyle: { fontSize: 13 },
      itemWidth: 25,
      itemHeight: 14
    },
    xAxis: {
      type: 'category',
      data: data.x,
      name: 'SNR_C',
      nameLocation: 'middle',
      nameGap: 46,
      nameTextStyle: { fontSize: 13, fontWeight: 600 },
      axisLabel: {
        rotate: 35,
        fontSize: 11,
        margin: 14,
        interval: 'auto',
        hideOverlap: true
      },
      axisTick: { alignWithLabel: true },
      axisLine: { lineStyle: { width: 2 } }
    },
    yAxis: {
      type: 'value',
      name: 'Current %',
      nameLocation: 'middle',
      nameGap: 58,
      nameTextStyle: { fontSize: 13, fontWeight: 600 },
      min: yAxisMin,
      max: yAxisMax,
      axisLabel: {
        fontSize: 11,
        margin: 12,
        formatter: '{value}'
      },
      axisLine: { lineStyle: { width: 2 } },
      splitLine: { lineStyle: { color: '#e0e0e0' } }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        height: 28,
        bottom: 18,
        textStyle: { fontSize: 11 }
      }
    ],
    series: [
      {
        name: '1%分位数',
        type: 'line',
        data: data.lq,
        smooth: true,
        lineStyle: { color: '#5470c6', width: 3 },
        symbol: 'circle',
        symbolSize: 8,
        connectNulls: false
      },
      {
        name: '99%分位数',
        type: 'line',
        data: data.hq,
        smooth: true,
        lineStyle: { color: '#ee6666', width: 3 },
        symbol: 'circle',
        symbolSize: 8,
        connectNulls: false
      },
      {
        name: '参考范围',
        type: 'line',
        data: data.max,
        lineStyle: { opacity: 0 },
        areaStyle: {
          color: 'rgba(46, 204, 113, 0.25)'
        },
        stack: 'area',
        symbol: 'none',
        markArea: {
          silent: true,
          label: {
            show: false
          },
          itemStyle: {
            color: 'rgba(46, 204, 113, 0.1)'
          },
          data: [[
            {
              yAxis: Math.min(...data.min.filter(v => v !== null && v !== undefined)) || yAxisMin
            },
            {
              yAxis: Math.max(...data.max.filter(v => v !== null && v !== undefined)) || yAxisMax
            }
          ]]
        }
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

watch(() => chartData.value, () => {
  if (chartInstance) {
    chartInstance.setOption(getChartOption(), { notMerge: true, lazyUpdate: true })
    chartInstance.resize()
  }
}, { deep: true })
</script>

<template>
  <div class="aggregated-chart">
    <div ref="chartRef" class="chart-container"></div>
    <div v-if="chartData.x.length === 0" class="no-data">
      暂无聚合数据
    </div>
  </div>
</template>

<style scoped>
.aggregated-chart {
  width: 100%;
  height: 100%;
  position: relative;
}

.chart-container {
  width: 100%;
  height: 100%;
  min-height: 500px;
}

.no-data {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 16px;
  color: #999;
}
</style>
