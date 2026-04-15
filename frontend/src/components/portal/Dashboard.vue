<template>
  <section id="dashboard" ref="dashboardSection" class="relative z-30 -mt-[16vh] px-4 pb-12 sm:px-6 lg:px-10">
    <div class="mx-auto max-w-[1440px]">
      <div
        class="glass-panel relative overflow-hidden rounded-[40px] border border-benz-blue/16 px-6 py-12 sm:px-8 lg:px-10 lg:py-14"
      >
        <img
          :src="dashboardImageUrl"
          alt="Dashboard background"
          class="absolute inset-0 h-full w-full object-cover opacity-[0.18]"
        />
        <div
          class="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(0,255,255,0.12),transparent_28%),linear-gradient(180deg,rgba(0,0,0,0)_0%,rgba(11,11,12,0.72)_100%)]"
          aria-hidden="true"
        ></div>
        <div
          class="pointer-events-none absolute inset-x-[7%] -bottom-16 h-28 rounded-[999px] bg-[radial-gradient(circle,rgba(160,210,255,0.12)_0%,rgba(0,113,227,0.08)_38%,transparent_72%)] blur-3xl"
          aria-hidden="true"
        ></div>
        <div
          class="pointer-events-none absolute inset-x-10 bottom-0 h-24 bg-[linear-gradient(180deg,rgba(11,11,12,0)_0%,rgba(11,11,12,0.74)_75%,rgba(11,11,12,0.96)_100%)]"
          aria-hidden="true"
        ></div>

        <div class="relative z-10">
          <div ref="headerRef" class="mx-auto mb-14 max-w-3xl text-center">
            <p class="text-sm font-semibold uppercase tracking-[0.3em] text-benz-blue">Live Data Overview</p>
            <h2 class="mt-4 text-4xl font-semibold tracking-[-0.05em] text-white sm:text-5xl lg:text-6xl">
              核心数据看板
            </h2>
            <div class="mt-8 flex flex-wrap justify-center gap-3">
              <button
                type="button"
                :ref="bindGlow"
                class="interactive-glow portal-btn-secondary min-w-[132px]"
                :class="{
                  'border-benz-cyan/36 bg-benz-cyan/10 text-benz-cyan shadow-[0_0_0_1px_rgba(0,255,255,0.08),0_0_26px_rgba(0,255,255,0.12)]': refreshButtonState === 'success'
                }"
                :disabled="refreshLoading"
                @click="refreshOverviewData"
              >
                <span class="inline-flex items-center gap-2">
                  <svg
                    v-if="refreshButtonState === 'loading'"
                    class="h-4 w-4 animate-spin text-current"
                    viewBox="0 0 24 24"
                    fill="none"
                    aria-hidden="true"
                  >
                    <circle class="opacity-25" cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2.5"></circle>
                    <path
                      class="opacity-90"
                      d="M21 12a9 9 0 0 0-9-9"
                      stroke="currentColor"
                      stroke-width="2.5"
                      stroke-linecap="round"
                    ></path>
                  </svg>
                  <svg
                    v-else-if="refreshButtonState === 'success'"
                    class="h-4 w-4 text-current drop-shadow-[0_0_8px_rgba(0,255,255,0.5)]"
                    viewBox="0 0 20 20"
                    fill="none"
                    aria-hidden="true"
                  >
                    <circle cx="10" cy="10" r="7.2" stroke="currentColor" stroke-width="1.2" class="opacity-35"></circle>
                    <path
                      d="M4.5 10.5 8 14l7.5-8"
                      stroke="currentColor"
                      stroke-width="2.2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    ></path>
                  </svg>
                  <span :class="{ 'tracking-[0.08em]': refreshButtonState === 'success' }">
                    {{ refreshButtonState === 'loading' ? '刷新中' : '刷新数据' }}
                  </span>
                </span>
              </button>
              <button
                type="button"
                :ref="bindGlow"
                class="interactive-glow portal-btn-primary"
                @click="router.push('/dashboard')"
              >
                进入机器人总览
              </button>
              <button
                type="button"
                :ref="bindGlow"
                class="interactive-glow portal-btn-secondary"
                @click="router.push('/devices')"
              >
                查看设备状态
              </button>
            </div>
            <div class="mt-5 flex justify-center">
              <div class="inline-flex items-center gap-3 rounded-full border border-white/8 bg-white/[0.03] px-4 py-2.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
                <span class="h-2.5 w-2.5 rounded-full bg-benz-cyan shadow-[0_0_14px_rgba(0,255,255,0.55)]"></span>
                <span class="text-[11px] font-semibold uppercase tracking-[0.24em] text-white/48">Last Sync</span>
                <span class="text-sm font-medium text-white/80">{{ latestUpdatedAt }}</span>
              </div>
            </div>
          </div>

          <div class="grid gap-4 xl:grid-cols-12">
            <article
              ref="leftCardRef"
              class="interactive-glow cursor-pointer rounded-[32px] border border-benz-blue/16 bg-[linear-gradient(180deg,rgba(0,60,130,0.12),rgba(8,12,18,0.9)_26%,rgba(5,7,10,0.96))] p-6 backdrop-blur-xl transition-colors duration-300 hover:border-benz-cyan/24 xl:col-span-6"
              role="link"
              tabindex="0"
              aria-label="打开 WAM 外部看板"
              @click="openWamDashboard"
              @keydown.enter.prevent="openWamDashboard"
              @keydown.space.prevent="openWamDashboard"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-sm font-bold uppercase tracking-[0.24em] text-benz-cyan">WAM</p>
                  <h3 class="mt-3 text-2xl font-semibold tracking-tight text-white">设备状态总览</h3>
                </div>
              </div>
              <div class="mt-5 space-y-4">
                <div class="grid gap-4 sm:grid-cols-[152px_1fr]">
                  <div
                    class="relative mx-auto h-32 w-32 rounded-full border border-benz-blue/18 shadow-[0_0_40px_rgba(0,113,227,0.12)]"
                    :style="{ background: wamRingBackground }"
                  >
                    <div class="absolute inset-[12px] rounded-full bg-[#06080c]"></div>
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                      <span class="text-[34px] font-black text-white">{{ wamTotal }}</span>
                      <span class="text-[11px] uppercase tracking-[0.22em] text-benz-gray">devices</span>
                    </div>
                  </div>
                  <div class="grid gap-3">
                    <div
                      v-for="status in wamCard.stats"
                      :key="status.key"
                      class="rounded-[18px] border border-white/6 bg-black/18 px-3.5 py-2.5"
                    >
                      <div class="flex items-center justify-between gap-3 text-xs uppercase tracking-[0.22em] text-benz-gray">
                        <span>{{ status.label }}</span>
                        <span>{{ status.percent }}%</span>
                      </div>
                      <div class="mt-2.5 flex items-end justify-between gap-3">
                        <span class="text-xl font-black text-white">{{ status.value }}</span>
                        <span class="text-xs font-semibold" :class="status.textClass">{{ status.caption }}</span>
                      </div>
                      <div class="mt-2.5 h-1.5 overflow-hidden rounded-full bg-white/6">
                        <div class="h-full rounded-full" :class="status.barClass" :style="{ width: `${status.percent}%` }"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </article>

            <article
              ref="centerCardRef"
              class="interactive-glow cursor-pointer rounded-[32px] border border-benz-cyan/18 bg-[linear-gradient(180deg,rgba(0,113,227,0.26),rgba(8,16,26,0.92)_38%,rgba(5,7,10,0.98))] p-6 shadow-glow-blue backdrop-blur-xl transition-colors duration-300 hover:border-benz-cyan/32 xl:col-span-6"
              role="link"
              tabindex="0"
              aria-label="打开 Lenze 外部看板"
              @click="openLenzeDashboard"
              @keydown.enter.prevent="openLenzeDashboard"
              @keydown.space.prevent="openLenzeDashboard"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-sm font-bold uppercase tracking-[0.24em] text-white/82">Lenze</p>
                  <h3 class="mt-3 text-2xl font-semibold tracking-tight text-white">温度状态总览</h3>
                </div>
              </div>
              <div class="mt-5 grid gap-4 lg:grid-cols-[168px_1fr]">
                <div
                  class="relative mx-auto h-36 w-36 rounded-full border border-benz-blue/18 shadow-[0_0_46px_rgba(0,113,227,0.14)]"
                  :style="{ background: lenzeRingBackground }"
                >
                  <div class="absolute inset-[14px] rounded-full bg-[#06101a]"></div>
                  <div class="absolute inset-0 flex flex-col items-center justify-center">
                    <span class="text-[34px] font-black text-white">{{ lenzeTotal }}</span>
                    <span class="text-[11px] uppercase tracking-[0.24em] text-benz-gray">signals</span>
                  </div>
                </div>
                <div class="space-y-3">
                  <div
                    v-for="status in lenzeStats"
                    :key="status.key"
                    class="rounded-[18px] border border-benz-blue/18 bg-[linear-gradient(180deg,rgba(0,113,227,0.12),rgba(5,8,12,0.92))] px-3.5 py-3"
                  >
                    <div class="flex items-center justify-between gap-3 text-xs uppercase tracking-[0.2em] text-benz-gray">
                      <span>{{ status.label }}</span>
                      <span>{{ status.percent }}%</span>
                    </div>
                    <div class="mt-2.5 flex items-end justify-between gap-3">
                      <span class="text-xl font-black text-white">{{ status.value }}</span>
                      <span class="text-xs font-semibold" :class="status.textClass">{{ status.caption }}</span>
                    </div>
                    <div class="mt-2.5 h-1.5 overflow-hidden rounded-full bg-white/6">
                      <div class="h-full rounded-full" :class="status.barClass" :style="{ width: `${status.percent}%` }"></div>
                    </div>
                  </div>
                </div>
              </div>
            </article>

            <article
              ref="highRiskCardRef"
              class="interactive-glow cursor-pointer overflow-hidden rounded-[32px] border border-amber-300/16 bg-[linear-gradient(180deg,rgba(255,204,0,0.08),rgba(18,16,10,0.92)_26%,rgba(7,7,8,0.98))] p-6 backdrop-blur-xl transition-colors duration-300 hover:border-amber-300/28 xl:col-span-6"
              role="link"
              tabindex="0"
              aria-label="打开 Robot Overview"
              @click="openRobotOverview"
              @keydown.enter.prevent="openRobotOverview"
              @keydown.space.prevent="openRobotOverview"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-sm font-bold uppercase tracking-[0.24em] text-amber-300">High-Risk Distribution Overview</p>
                  <h3 class="mt-3 text-2xl font-semibold tracking-tight text-white">高风险分布总览</h3>
                </div>
              </div>
              <div class="mt-5 grid gap-4 lg:grid-cols-[1.25fr_0.75fr]">
                <div class="rounded-[24px] border border-amber-300/10 bg-black/16 p-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
                  <div ref="distributionChartRef" class="mx-auto h-[280px] w-full max-w-[320px]"></div>
                </div>
                <div class="space-y-3">
                  <div class="grid grid-cols-2 gap-3">
                    <div class="rounded-[18px] border border-white/6 bg-black/18 px-4 py-3">
                      <p class="text-[11px] uppercase tracking-[0.22em] text-benz-gray">高风险总数</p>
                      <p class="mt-2 text-2xl font-black text-white">{{ highRiskCard.total }}</p>
                    </div>
                    <div class="rounded-[18px] border border-white/6 bg-black/18 px-4 py-3">
                      <p class="text-[11px] uppercase tracking-[0.22em] text-benz-gray">机器人总数</p>
                      <p class="mt-2 text-2xl font-black text-white">{{ highRiskCard.overallTotal }}</p>
                    </div>
                  </div>
                  <div v-for="item in highRiskLegend" :key="item.label" class="rounded-[18px] border border-white/6 bg-black/18 px-3.5 py-2.5">
                    <div class="flex items-center justify-between gap-3">
                      <div class="flex min-w-0 items-center gap-3">
                        <span class="h-2.5 w-2.5 rounded-full" :style="{ background: item.color }"></span>
                        <span class="truncate text-[13px] font-medium text-white">{{ item.label }}</span>
                      </div>
                      <span class="text-[13px] font-semibold text-benz-gray">{{ item.value }}</span>
                    </div>
                    <div class="mt-2.5 h-1.5 overflow-hidden rounded-full bg-white/6">
                      <div class="h-full rounded-full" :style="{ width: `${item.percent}%`, background: item.color }"></div>
                    </div>
                  </div>
                </div>
              </div>
            </article>

            <article
              ref="rightCardRef"
              class="interactive-glow cursor-pointer rounded-[32px] border border-benz-blue/16 bg-[linear-gradient(180deg,rgba(0,60,130,0.12),rgba(8,12,18,0.9)_26%,rgba(5,7,10,0.96))] p-6 backdrop-blur-xl transition-colors duration-300 hover:border-benz-cyan/24 xl:col-span-6"
              role="link"
              tabindex="0"
              aria-label="打开 Filling 外部看板"
              @click="openFillingDashboard"
              @keydown.enter.prevent="openFillingDashboard"
              @keydown.space.prevent="openFillingDashboard"
            >
              <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p class="text-sm font-bold uppercase tracking-[0.24em] text-benz-cyan">Filling</p>
                  <h3 class="mt-3 text-2xl font-semibold tracking-tight text-white">灌注结果总览</h3>
                </div>
              </div>
              <div class="mt-5">
                <div class="grid gap-4 sm:grid-cols-[152px_1fr] items-start">
                  <div
                    class="relative mx-auto h-36 w-36 rounded-full border border-benz-blue/18 shadow-[0_0_44px_rgba(0,113,227,0.14)]"
                    :style="{ background: fillingRingBackground }"
                  >
                    <div class="absolute inset-[14px] rounded-full bg-[#070b10]"></div>
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                      <span class="text-[34px] font-black text-white">{{ fillingTotal }}</span>
                      <span class="text-[11px] uppercase tracking-[0.24em] text-benz-gray">records</span>
                    </div>
                  </div>
                  <div class="grid gap-3">
                    <div
                      v-for="status in fillingStats"
                      :key="status.key"
                      class="rounded-[18px] border border-white/6 bg-black/18 px-3.5 py-3"
                    >
                      <div class="flex items-center justify-between gap-3 text-xs uppercase tracking-[0.22em] text-benz-gray">
                        <span>{{ status.label }}</span>
                        <span>{{ status.percent }}%</span>
                      </div>
                      <div class="mt-2.5 flex items-end justify-between gap-3">
                        <span class="text-xl font-black text-white">{{ status.value }}</span>
                        <span class="text-xs font-semibold" :class="status.textClass">{{ status.caption }}</span>
                      </div>
                      <div class="mt-2.5 h-1.5 overflow-hidden rounded-full bg-white/6">
                        <div class="h-full rounded-full" :class="status.barClass" :style="{ width: `${status.percent}%` }"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </article>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { getPortalOverviewSnapshot, refreshPortalOverviewSnapshot } from '@/api/robots'
import { useMouseMoveGlow } from '@/utils/useMouseMoveGlow'

gsap.registerPlugin(ScrollTrigger)

const { bindGlow } = useMouseMoveGlow()
const router = useRouter()
const dashboardSection = ref(null)
const headerRef = ref(null)
const leftCardRef = ref(null)
const centerCardRef = ref(null)
const highRiskCardRef = ref(null)
const rightCardRef = ref(null)
const distributionChartRef = ref(null)
const dashboardImageUrl = `${import.meta.env.BASE_URL}portal-dashboard-bg.jpg`
const wamDashboardUrl = 'http://172.16.17.173:8050/'
const lenzeDashboardUrl = 'http://172.16.29.103:500/PS3lenze-alert'
const fillingDashboardUrl = 'https://apagepowerbi.cn/groups/4c00eble-18cd-4dd0-a41c-baceff07900e/reports/93f1e6ed-637841c3-8cb4-0372af3960a6/7713aa26f8e40c755d36'
const refreshLoading = ref(false)
const refreshButtonState = ref('idle')
const latestUpdatedAt = ref('暂无更新记录')
let ctx
let refreshSuccessTimer = null
let distributionChart = null

const handleResize = () => {
  distributionChart?.resize()
}

const formatSnapshotTime = (value) => {
  if (!value) return '暂无更新记录'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value)
  }

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const openWamDashboard = () => {
  window.open(wamDashboardUrl, '_blank', 'noopener,noreferrer')
}

const openLenzeDashboard = () => {
  window.open(lenzeDashboardUrl, '_blank', 'noopener,noreferrer')
}

const openFillingDashboard = () => {
  window.open(fillingDashboardUrl, '_blank', 'noopener,noreferrer')
}

const openRobotOverview = () => {
  router.push('/dashboard')
}

const fillingCard = ref({
  nokCount: 360,
  okCount: 213,
  note: '这一块更适合突出 NOK 占比，再用工位堆叠条补充 Filing1 到 Filing4 的分布差异。'
})

const highRiskCard = ref({
  total: 14,
  groupCount: 3,
  overallTotal: 156
})

const highRiskLegend = ref([
  { label: 'AS1', value: '6', percent: 43, color: '#00d8ff' },
  { label: 'MRA', value: '4', percent: 29, color: '#ffcc00' },
  { label: '其他车间', value: '4', percent: 29, color: '#ff7a7a' }
])

const lenzeCard = ref({
  okCount: 172,
  warningCount: 1,
  alarmCount: 2
})

const wamCard = ref({
  total: 0,
  stats: []
})

const toPercent = (value, total) => {
  if (!total) return 0
  return Math.max(0, Math.min(100, Math.round((value / total) * 100)))
}

const getStatusVisual = (label, index = 0) => {
  const normalized = String(label || '').trim().toLowerCase()
  if (normalized === 'ok') {
    return {
      color: 'rgba(0,216,255,0.92)',
      className: 'border border-benz-cyan/20 bg-benz-cyan/10 text-benz-cyan',
      textClass: 'text-benz-cyan',
      barClass: 'bg-benz-cyan'
    }
  }
  if (normalized.includes('warn')) {
    return {
      color: 'rgba(250,204,21,0.92)',
      className: 'border border-amber-400/18 bg-amber-400/10 text-amber-300',
      textClass: 'text-amber-300',
      barClass: 'bg-amber-300'
    }
  }
  if (normalized.includes('fault') || normalized.includes('alarm') || normalized.includes('nok')) {
    return {
      color: 'rgba(248,113,113,0.95)',
      className: 'border border-red-400/18 bg-red-500/10 text-red-300',
      textClass: 'text-red-300',
      barClass: 'bg-red-400/80'
    }
  }

  const fallbackColors = [
    'rgba(125,211,252,0.92)',
    'rgba(196,181,253,0.92)',
    'rgba(244,114,182,0.92)',
    'rgba(74,222,128,0.92)'
  ]
  return {
    color: fallbackColors[index % fallbackColors.length],
    className: 'border border-white/10 bg-white/[0.04] text-white/82',
    textClass: 'text-white/82',
    barClass: 'bg-white/70'
  }
}

const buildWamStats = (statusCounts) => {
  const entries = Object.entries(statusCounts || {})
  const total = entries.reduce((sum, [, value]) => sum + Number(value || 0), 0)
  return entries.map(([label, rawValue], index) => {
    const value = Number(rawValue || 0)
    const visual = getStatusVisual(label, index)
    return {
      key: `${String(label).toLowerCase()}-${index}`,
      label,
      value,
      percent: toPercent(value, total),
      caption: total ? `${value}/${total}` : '0/0',
      ...visual
    }
  })
}

const buildConicSegments = (segments, fallbackColor = 'rgba(0,255,255,0.2)') => {
  const total = segments.reduce((sum, segment) => sum + Math.max(0, Number(segment.value || 0)), 0)
  if (!total) {
    return `conic-gradient(${fallbackColor} 0deg 360deg)`
  }

  let currentDeg = 0
  const stops = segments.map((segment) => {
    const span = (Math.max(0, Number(segment.value || 0)) / total) * 360
    const start = currentDeg
    currentDeg += span
    return `${segment.color} ${start}deg ${currentDeg}deg`
  })

  return `conic-gradient(${stops.join(', ')})`
}

const wamTotal = computed(() => (
  wamCard.value.stats.reduce((sum, item) => sum + Number(item.value || 0), 0)
))

const wamRingBackground = computed(() => {
  return buildConicSegments(
    wamCard.value.stats.map(item => ({
      value: item.value,
      color: item.color
    }))
  )
})

const lenzeTotal = computed(() => (
  Number(lenzeCard.value.okCount || 0)
  + Number(lenzeCard.value.warningCount || 0)
  + Number(lenzeCard.value.alarmCount || 0)
))

const lenzeRingBackground = computed(() => buildConicSegments([
  { value: lenzeCard.value.okCount, color: 'rgba(0,216,255,0.92)' },
  { value: lenzeCard.value.warningCount, color: 'rgba(250,204,21,0.92)' },
  { value: lenzeCard.value.alarmCount, color: 'rgba(248,113,113,0.95)' }
]))

const lenzeStats = computed(() => {
  const total = lenzeTotal.value
  return [
    {
      key: 'ok',
      label: 'OK',
      value: Number(lenzeCard.value.okCount || 0),
      percent: toPercent(Number(lenzeCard.value.okCount || 0), total),
      caption: total ? `${lenzeCard.value.okCount}/${total}` : '0/0',
      textClass: 'text-benz-cyan',
      barClass: 'bg-benz-cyan'
    },
    {
      key: 'warning',
      label: 'Warning',
      value: Number(lenzeCard.value.warningCount || 0),
      percent: toPercent(Number(lenzeCard.value.warningCount || 0), total),
      caption: total ? `${lenzeCard.value.warningCount}/${total}` : '0/0',
      textClass: 'text-amber-300',
      barClass: 'bg-amber-300'
    },
    {
      key: 'alarm',
      label: 'Alarm',
      value: Number(lenzeCard.value.alarmCount || 0),
      percent: toPercent(Number(lenzeCard.value.alarmCount || 0), total),
      caption: total ? `${lenzeCard.value.alarmCount}/${total}` : '0/0',
      textClass: 'text-red-300',
      barClass: 'bg-red-400/80'
    }
  ]
})

const fillingTotal = computed(() => Number(fillingCard.value.okCount || 0) + Number(fillingCard.value.nokCount || 0))

const fillingRingBackground = computed(() => buildConicSegments([
  { value: fillingCard.value.nokCount, color: 'rgba(248,113,113,0.95)' },
  { value: fillingCard.value.okCount, color: 'rgba(0,216,255,0.92)' }
]))

const fillingStats = computed(() => {
  const okCount = Number(fillingCard.value.okCount || 0)
  const nokCount = Number(fillingCard.value.nokCount || 0)
  const total = okCount + nokCount
  return [
    {
      key: 'ok',
      label: 'OK',
      value: okCount,
      percent: toPercent(okCount, total),
      caption: total ? `${okCount}/${total}` : '0/0',
      textClass: 'text-benz-cyan',
      barClass: 'bg-benz-cyan'
    },
    {
      key: 'nok',
      label: 'NOK',
      value: nokCount,
      percent: toPercent(nokCount, total),
      caption: total ? `${nokCount}/${total}` : '0/0',
      textClass: 'text-red-300',
      barClass: 'bg-red-400/80'
    }
  ]
})

const renderDistributionChart = () => {
  if (!distributionChartRef.value) return

  if (!distributionChart) {
    distributionChart = echarts.init(distributionChartRef.value)
  }

  const box = distributionChartRef.value.getBoundingClientRect()
  const baseSize = box ? Math.min(box.width, box.height || box.width) : 240
  const ringInner = baseSize < 260 ? 58 : 54
  const ringOuter = baseSize < 260 ? 80 : 78
  const labelRadius = Math.max(34, ringInner - 10)
  const mainFontSize = Math.max(18, Math.round(baseSize * 0.11))
  const subFontSize = Math.max(9, Math.round(baseSize * 0.045))

  const rows = highRiskLegend.value
    .map((item) => ({
      name: item.label,
      value: Number(item.value || 0),
      color: item.color
    }))
    .filter(item => item.value > 0)

    const pieData = rows.map((row) => ({
    value: row.value,
    name: row.name,
    itemStyle: {
      borderRadius: 8,
      color: row.color,
      borderColor: 'rgba(255,255,255,0.18)',
      borderWidth: 1,
      shadowBlur: 16,
      shadowColor: row.color
    }
  }))

  distributionChart.setOption({
    animationDuration: 500,
    series: [
      {
        type: 'pie',
        radius: [`${ringInner}%`, `${ringOuter}%`],
        center: ['50%', '50%'],
        roseType: 'radius',
        padAngle: 4,
        itemStyle: { borderRadius: 8 },
        label: { show: false },
        data: pieData
      },
      {
        type: 'pie',
        radius: [0, `${labelRadius}%`],
        silent: true,
        label: {
          show: true,
          position: 'center',
          formatter: () => [`{v|${highRiskCard.value.total} / ${highRiskCard.value.overallTotal}}`, '{l|High Risk / Total}'].join('\n'),
          rich: {
            v: {
              fontSize: mainFontSize,
              fontWeight: 900,
              color: '#ffcc00',
              textShadow: '0 0 20px rgba(255, 204, 0, 0.45)',
              lineHeight: Math.round(mainFontSize * 1.1)
            },
            l: {
              fontSize: subFontSize,
              color: '#8899aa',
              paddingTop: 4,
              lineHeight: Math.round(subFontSize * 1.2)
            }
          }
        },
        data: [{ value: 1, itemStyle: { color: 'transparent' } }]
      }
    ],
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(10, 20, 35, 0.92)',
      borderColor: '#ffcc00',
      textStyle: { color: '#fff' },
      formatter: (params) => `${params.name}<br/>${params.value} (${params.percent}%)`
    }
  })
}

const applyOverviewSnapshot = (snapshot) => {
  const blocks = snapshot?.blocks || []
  const findBlock = (key) => blocks.find((block) => block.key === key)?.payload || {}
  latestUpdatedAt.value = formatSnapshotTime(snapshot?.generated_at)

  const wamPayload = findBlock('wam')
  if (Object.keys(wamPayload).length) {
    const counts = wamPayload.status_counts || {}
    const stats = buildWamStats(counts)
    wamCard.value = {
      total: Number(wamPayload.device_count ?? 0),
      stats
    }
  }

  const lenzePayload = findBlock('lenze')
  if (Object.keys(lenzePayload).length) {
    const counts = lenzePayload.status_counts || {}
    lenzeCard.value = {
      okCount: counts.OK ?? lenzeCard.value.okCount,
      warningCount: counts.Warning ?? lenzeCard.value.warningCount,
      alarmCount: counts.Alarm ?? lenzeCard.value.alarmCount
    }
  }

  const fillingPayload = findBlock('filling')
  if (Object.keys(fillingPayload).length) {
    const counts = fillingPayload.status_counts || {}
    fillingCard.value = {
      okCount: counts.OK ?? fillingCard.value.okCount,
      nokCount: counts.NOK ?? fillingCard.value.nokCount,
      note: '已从灌注状态文件重算 OK / NOK。'
    }
  }

  const highRiskPayload = findBlock('high_risk_distribution')
  if (Object.keys(highRiskPayload).length) {
    highRiskCard.value = {
      total: highRiskPayload.total_high_risk ?? highRiskCard.value.total,
      groupCount: (highRiskPayload.all_groups || highRiskPayload.groups || []).filter(item => Number(item.high_risk || 0) > 0).length,
      overallTotal: highRiskPayload.total_count ?? highRiskCard.value.overallTotal
    }
    const groups = highRiskPayload.all_groups || highRiskPayload.groups || []
    const highRiskGroups = groups.filter(item => Number(item.high_risk || 0) > 0)
    const topGroupTotal = highRiskGroups.reduce((sum, item) => sum + Number(item.high_risk || 0), 0)
    const palette = ['#00d8ff', '#ffcc00', '#ff7a7a', '#7dd3fc', '#c4b5fd', '#4ade80', '#f472b6', '#fb7185']
    highRiskLegend.value = highRiskGroups.map((item, index) => ({
      label: item.group,
      value: String(item.high_risk),
      percent: toPercent(Number(item.high_risk || 0), topGroupTotal),
      color: palette[index % palette.length]
    }))

    nextTick(() => {
      renderDistributionChart()
    })
  }
}

const loadExistingSnapshot = async () => {
  try {
    const payload = await getPortalOverviewSnapshot({ silent: true })
    if (payload?.snapshot) {
      applyOverviewSnapshot(payload.snapshot)
    }
  } catch (error) {
    console.error('loadExistingSnapshot failed:', error)
  }
}

const refreshOverviewData = async () => {
  if (refreshSuccessTimer) {
    window.clearTimeout(refreshSuccessTimer)
    refreshSuccessTimer = null
  }
  refreshLoading.value = true
  refreshButtonState.value = 'loading'
  try {
    const payload = await refreshPortalOverviewSnapshot({}, { silent: true })
    applyOverviewSnapshot(payload.snapshot)
    refreshButtonState.value = 'success'
    refreshSuccessTimer = window.setTimeout(() => {
      refreshButtonState.value = 'idle'
      refreshSuccessTimer = null
    }, 1600)
  } catch (error) {
    refreshButtonState.value = 'idle'
    console.error('refreshOverviewData failed:', error)
  } finally {
    refreshLoading.value = false
  }
}

onMounted(() => {
  loadExistingSnapshot()

  ctx = gsap.context(() => {
    gsap.set(headerRef.value, { opacity: 0, y: -22 })
    gsap.set(leftCardRef.value, { opacity: 0, x: -64, filter: 'blur(10px)' })
    gsap.set(highRiskCardRef.value, { opacity: 0, y: 72, filter: 'blur(8px)' })
    gsap.set(rightCardRef.value, { opacity: 0, x: 64, filter: 'blur(10px)' })
    gsap.set(centerCardRef.value, { opacity: 0, y: 84, scale: 0.96, filter: 'blur(12px)' })

    const introTimeline = gsap.timeline({
      scrollTrigger: {
        trigger: dashboardSection.value,
        start: 'top 76%',
        toggleActions: 'play none none reverse',
        invalidateOnRefresh: true
      }
    })

    introTimeline.to(headerRef.value, {
      opacity: 1,
      y: 0,
      duration: 0.65,
      ease: 'power3.out'
    })

    introTimeline.to(
      [leftCardRef.value, rightCardRef.value],
      {
        opacity: 1,
        x: 0,
        filter: 'blur(0px)',
        duration: 0.9,
        ease: 'power3.out'
      },
      '-=0.25'
    )

    introTimeline.to(
      centerCardRef.value,
      {
        opacity: 1,
        y: 0,
        scale: 1,
        filter: 'blur(0px)',
        duration: 0.9,
        ease: 'back.out(1.2)'
      },
      '-=0.62'
    )

    introTimeline.to(
      highRiskCardRef.value,
      {
        opacity: 1,
        y: 0,
        filter: 'blur(0px)',
        duration: 0.9,
        ease: 'power3.out'
      },
      '-=0.38'
    )
  }, dashboardSection.value)

  requestAnimationFrame(() => {
    ScrollTrigger.refresh()
  })

  nextTick(() => {
    renderDistributionChart()
  })

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (refreshSuccessTimer) {
    window.clearTimeout(refreshSuccessTimer)
    refreshSuccessTimer = null
  }
  ctx?.revert()
  distributionChart?.dispose()
  distributionChart = null
  window.removeEventListener('resize', handleResize)
})
</script>
