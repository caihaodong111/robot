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
            <p class="mt-4 text-base leading-8 text-benz-gray sm:text-lg">
              这里先汇总 WAM、Lenze、Filling 和高风险分布四类信息，用一屏建立对当前状态结构的整体判断。
            </p>
            <div class="mt-8 flex flex-wrap justify-center gap-3">
              <button
                type="button"
                :ref="bindGlow"
                class="interactive-glow portal-btn-secondary min-w-[132px]"
                :disabled="refreshLoading"
                @click="refreshOverviewData"
              >
                {{ refreshLoading ? '刷新中...' : '刷新数据' }}
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
            <p class="mt-4 text-sm text-benz-gray">
              {{ refreshStatus }}
            </p>
          </div>

          <div class="grid gap-6 xl:grid-cols-12">
            <article
              ref="leftCardRef"
              class="interactive-glow rounded-[32px] border border-benz-blue/16 bg-[linear-gradient(180deg,rgba(0,60,130,0.12),rgba(8,12,18,0.9)_26%,rgba(5,7,10,0.96))] p-7 backdrop-blur-xl xl:col-span-3"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-sm font-bold uppercase tracking-[0.24em] text-benz-cyan">WAM</p>
                  <h3 class="mt-3 text-2xl font-semibold tracking-tight text-white">设备数量总览</h3>
                </div>
                <span class="rounded-[16px] border border-benz-blue/20 bg-benz-blue/10 px-3 py-1 text-xs font-semibold text-benz-cyan">
                  占位方案
                </span>
              </div>
              <div class="mt-6 space-y-5">
                <div
                  class="relative mx-auto h-28 w-28 rounded-full border border-benz-blue/18"
                  style="background: conic-gradient(rgba(0,255,255,0.2) 0deg 360deg);"
                >
                  <div class="absolute inset-[10px] rounded-full bg-[#06080c]"></div>
                  <div class="absolute inset-0 flex flex-col items-center justify-center">
                    <span class="text-3xl font-black text-white">{{ wamCard.deviceCount }}</span>
                    <span class="text-[11px] uppercase tracking-[0.22em] text-benz-gray">devices</span>
                  </div>
                </div>
                <p class="text-sm leading-7 text-white/[0.62]">
                  {{ wamCard.note }}
                </p>
                <div class="flex flex-wrap gap-2">
                  <span
                    v-for="status in wamCard.statusTypes"
                    :key="status.label"
                    class="rounded-[14px] px-3 py-1 text-xs font-semibold"
                    :class="status.className"
                  >
                    {{ status.label }}
                  </span>
                </div>
              </div>
            </article>

            <article
              ref="centerCardRef"
              class="interactive-glow rounded-[32px] border border-benz-cyan/18 bg-[linear-gradient(180deg,rgba(0,113,227,0.26),rgba(8,16,26,0.92)_38%,rgba(5,7,10,0.98))] p-7 shadow-glow-blue backdrop-blur-xl xl:col-span-4"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-sm font-bold uppercase tracking-[0.24em] text-white/82">Lenze</p>
                  <h3 class="mt-3 text-2xl font-semibold tracking-tight text-white">温度状态总览</h3>
                </div>
                <span class="rounded-[16px] border border-benz-cyan/24 bg-benz-cyan/10 px-3 py-1 text-xs font-semibold text-benz-cyan">
                  环形图
                </span>
              </div>
              <div class="mt-6 grid gap-5 lg:grid-cols-[0.88fr_1.12fr]">
                <div
                  class="relative mx-auto h-36 w-36 rounded-full border border-benz-blue/18"
                  style="background: conic-gradient(#00d8ff 0deg 354deg, rgba(250,204,21,0.9) 354deg 358deg, rgba(248,113,113,0.95) 358deg 360deg);"
                >
                  <div class="absolute inset-[14px] rounded-full bg-[#06101a]"></div>
                  <div class="absolute inset-0 flex flex-col items-center justify-center">
                    <span class="text-3xl font-black text-white">{{ lenzeCard.okCount }}</span>
                    <span class="text-[11px] uppercase tracking-[0.24em] text-benz-gray">OK</span>
                  </div>
                </div>
                <div class="space-y-3">
                  <div class="rounded-[20px] border border-benz-blue/18 bg-[linear-gradient(180deg,rgba(0,113,227,0.12),rgba(5,8,12,0.92))] p-4">
                    <div class="flex items-center justify-between gap-3">
                      <span class="text-xs uppercase tracking-[0.2em] text-benz-gray">Warning</span>
                      <span class="text-lg font-semibold text-amber-300">{{ lenzeCard.warningCount }}</span>
                    </div>
                  </div>
                  <div class="rounded-[20px] border border-benz-blue/18 bg-[linear-gradient(180deg,rgba(0,113,227,0.12),rgba(5,8,12,0.92))] p-4">
                    <div class="flex items-center justify-between gap-3">
                      <span class="text-xs uppercase tracking-[0.2em] text-benz-gray">Alarm</span>
                      <span class="text-lg font-semibold text-red-300">{{ lenzeCard.alarmCount }}</span>
                    </div>
                  </div>
                  <div class="rounded-[20px] border border-benz-blue/18 bg-[linear-gradient(180deg,rgba(0,113,227,0.12),rgba(5,8,12,0.92))] p-4">
                    <p class="text-xs uppercase tracking-[0.2em] text-benz-gray">展示重点</p>
                    <p class="mt-2 text-sm leading-6 text-white/[0.62]">{{ lenzeCard.note }}</p>
                  </div>
                </div>
              </div>
            </article>

            <article
              :ref="setDetailRef"
              class="interactive-glow overflow-hidden rounded-[32px] border border-amber-300/16 bg-[linear-gradient(180deg,rgba(255,204,0,0.08),rgba(18,16,10,0.92)_26%,rgba(7,7,8,0.98))] p-7 backdrop-blur-xl xl:col-span-5"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-sm font-bold uppercase tracking-[0.24em] text-amber-300">High-Risk Distribution</p>
                  <h3 class="mt-3 text-2xl font-semibold tracking-tight text-white">风险分布总览</h3>
                </div>
                <span class="rounded-[16px] border border-amber-300/18 bg-amber-300/10 px-3 py-1 text-xs font-semibold text-amber-300">
                  饼图占位
                </span>
              </div>
              <div class="mt-6 grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
                <div class="relative mx-auto h-36 w-36 rounded-full border border-amber-300/16 bg-[conic-gradient(#00d8ff_0deg_120deg,#ffcc00_120deg_220deg,#ff7a7a_220deg_360deg)]">
                  <div class="absolute inset-[14px] rounded-full bg-[#0a0c10]"></div>
                  <div class="absolute inset-0 flex flex-col items-center justify-center">
                    <span class="text-3xl font-black text-white">{{ highRiskCard.total }} / {{ highRiskCard.groupCount }}</span>
                    <span class="text-[11px] uppercase tracking-[0.22em] text-benz-gray">high risk</span>
                  </div>
                </div>
                <div class="space-y-3">
                  <div v-for="item in highRiskLegend" :key="item.label" class="flex items-center justify-between gap-3 rounded-[18px] border border-white/6 bg-black/18 px-4 py-3">
                    <div class="flex items-center gap-3">
                      <span class="h-2.5 w-2.5 rounded-full" :style="{ background: item.color }"></span>
                      <span class="text-sm font-medium text-white">{{ item.label }}</span>
                    </div>
                    <span class="text-sm font-semibold text-benz-gray">{{ item.value }}</span>
                  </div>
                </div>
              </div>
            </article>

            <article
              ref="rightCardRef"
              class="interactive-glow rounded-[32px] border border-benz-blue/16 bg-[linear-gradient(180deg,rgba(0,60,130,0.12),rgba(8,12,18,0.9)_26%,rgba(5,7,10,0.96))] p-7 backdrop-blur-xl xl:col-span-12"
            >
              <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p class="text-sm font-bold uppercase tracking-[0.24em] text-benz-cyan">Filling</p>
                  <h3 class="mt-3 text-2xl font-semibold tracking-tight text-white">灌注结果总览</h3>
                </div>
                <span class="rounded-[16px] border border-red-400/18 bg-red-500/10 px-3 py-1 text-xs font-semibold text-red-300">
                  NOK 偏高
                </span>
              </div>
              <div class="mt-6 grid gap-6 xl:grid-cols-[0.34fr_0.66fr]">
                <div class="flex items-center gap-6">
                  <div
                    class="relative h-32 w-32 shrink-0 rounded-full border border-benz-blue/18"
                    style="background: conic-gradient(rgba(248,113,113,0.95) 0deg 226deg, #00d8ff 226deg 360deg);"
                  >
                    <div class="absolute inset-[12px] rounded-full bg-[#070b10]"></div>
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                      <span class="text-3xl font-black text-white">{{ fillingCard.nokCount }}</span>
                      <span class="text-[11px] uppercase tracking-[0.24em] text-red-300">NOK</span>
                    </div>
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="text-sm leading-7 text-white/[0.62]">
                      {{ fillingCard.note }}
                    </p>
                  </div>
                </div>
                <div class="grid gap-3">
                  <div v-for="station in fillingStations" :key="station.label">
                    <div class="mb-1 flex items-center justify-between gap-3 text-xs uppercase tracking-[0.18em] text-benz-gray">
                      <span>{{ station.label }}</span>
                      <span>{{ station.ok }} OK / {{ station.nok }} NOK</span>
                    </div>
                    <div class="h-2.5 overflow-hidden rounded-full bg-benz-blue/12">
                      <div class="flex h-full w-full">
                        <span class="block h-full bg-red-400/80" :style="{ width: `${station.nokWidth}%` }"></span>
                        <span class="block h-full bg-benz-cyan" :style="{ width: `${station.okWidth}%` }"></span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </article>
          </div>

          <div class="mt-6 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
            <article
              :ref="setDetailRef"
              class="interactive-glow overflow-hidden rounded-[32px] border border-benz-blue/16 bg-[linear-gradient(180deg,rgba(0,48,105,0.12),rgba(6,10,16,0.92)_26%,rgba(5,7,10,0.98))] p-6 backdrop-blur-xl"
            >
              <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <p class="text-xs font-semibold uppercase tracking-[0.24em] text-benz-cyan">Display Structure</p>
                  <h3 class="mt-3 text-3xl font-semibold tracking-tight text-white">展示结构预览</h3>
                </div>
                <span class="rounded-full border border-benz-blue/24 bg-benz-blue/10 px-3 py-1 text-xs font-semibold text-benz-cyan">
                  前端占位版
                </span>
              </div>

              <div class="mt-8 grid gap-8 lg:grid-cols-[0.95fr_1.05fr]">
                <div class="flex min-h-[220px] items-end gap-3">
                  <div
                    v-for="bar in displayBars"
                    :key="bar.label"
                    class="flex flex-1 flex-col items-center justify-end gap-3"
                  >
                    <div class="flex h-[190px] w-full items-end rounded-[22px] border border-benz-blue/16 bg-[linear-gradient(180deg,rgba(0,113,227,0.1),rgba(5,8,12,0.84))] p-2">
                      <span
                        class="trend-fill block w-full rounded-[16px] bg-gradient-to-t from-benz-blue to-benz-cyan"
                        :style="{ height: `${bar.value}%` }"
                      ></span>
                    </div>
                    <span class="text-xs font-semibold uppercase tracking-[0.18em] text-benz-gray">{{ bar.label }}</span>
                  </div>
                </div>

                <div class="grid gap-3 sm:grid-cols-2">
                  <article
                    v-for="item in displayCards"
                    :key="item.label"
                    class="rounded-[24px] border border-benz-blue/16 bg-[linear-gradient(180deg,rgba(0,113,227,0.08),rgba(5,8,12,0.9))] p-4"
                  >
                    <p class="text-xs font-semibold uppercase tracking-[0.24em] text-benz-gray">{{ item.label }}</p>
                    <p class="mt-3 text-3xl font-semibold text-white">{{ item.value }}</p>
                    <p class="mt-3 text-sm leading-6 text-white/[0.58]">{{ item.copy }}</p>
                  </article>
                </div>
              </div>
            </article>

            <div class="grid gap-4">
              <article
                :ref="setDetailRef"
                class="interactive-glow rounded-[32px] border border-benz-blue/16 bg-[linear-gradient(180deg,rgba(0,48,105,0.12),rgba(6,10,16,0.92)_26%,rgba(5,7,10,0.98))] p-6 backdrop-blur-xl"
              >
                <div class="flex items-center justify-between gap-4">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.24em] text-benz-cyan">Chart Guidance</p>
                    <h3 class="mt-3 text-2xl font-semibold tracking-tight text-white">图形建议</h3>
                  </div>
                  <span class="text-xs font-semibold uppercase tracking-[0.2em] text-benz-gray">Overview</span>
                </div>

                <div class="mt-6 space-y-5">
                  <div v-for="signal in chartGuides" :key="signal.label">
                    <div class="mb-2 flex items-center justify-between gap-4">
                      <span class="text-sm font-semibold text-white">{{ signal.label }}</span>
                      <span class="text-sm text-benz-gray">{{ signal.value }}</span>
                    </div>
                    <div class="h-2 overflow-hidden rounded-full bg-benz-blue/12">
                      <span
                        class="block h-full rounded-full bg-gradient-to-r from-benz-blue to-benz-cyan"
                        :style="{ width: `${signal.progress}%` }"
                      ></span>
                    </div>
                  </div>
                </div>
              </article>

              <article
                :ref="setDetailRef"
                class="interactive-glow rounded-[32px] border border-benz-blue/16 bg-[linear-gradient(180deg,rgba(0,48,105,0.12),rgba(6,10,16,0.92)_26%,rgba(5,7,10,0.98))] p-6 backdrop-blur-xl"
              >
                <div class="flex items-center justify-between gap-4">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.24em] text-benz-cyan">Placeholder Notes</p>
                    <h3 class="mt-3 text-2xl font-semibold tracking-tight text-white">当前占位说明</h3>
                  </div>
                  <span class="text-xs font-semibold uppercase tracking-[0.2em] text-benz-gray">Pending Data</span>
                </div>

                <div class="mt-6 space-y-4">
                  <div v-for="item in placeholderNotes" :key="item.title" class="flex gap-4">
                    <span class="mt-1.5 h-3 w-3 shrink-0 rounded-full bg-benz-cyan shadow-glow-cyan"></span>
                    <div>
                      <p class="text-base font-semibold text-white">{{ item.title }}</p>
                      <p class="mt-1 text-sm leading-6 text-white/[0.58]">{{ item.copy }}</p>
                    </div>
                  </div>
                </div>
              </article>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useMouseMoveGlow } from '@/utils/useMouseMoveGlow'

gsap.registerPlugin(ScrollTrigger)

const { bindGlow } = useMouseMoveGlow()
const router = useRouter()
const dashboardSection = ref(null)
const headerRef = ref(null)
const leftCardRef = ref(null)
const centerCardRef = ref(null)
const rightCardRef = ref(null)
const detailRefs = ref([])
const dashboardImageUrl = `${import.meta.env.BASE_URL}portal-dashboard-bg.jpg`
const devDataApiBase = 'http://127.0.0.1:8765'
const refreshLoading = ref(false)
const refreshStatus = ref('开发模式下可点击“刷新数据”读取本地文件和数据库。')
let ctx

const setDetailRef = (el) => {
  if (el && !detailRefs.value.includes(el)) {
    detailRefs.value.push(el)
  }
}

const displayBars = [
  { label: 'WAM', value: 34 },
  { label: 'Lenze', value: 92 },
  { label: 'Filling', value: 61 },
  { label: 'OK', value: 88 },
  { label: 'NOK', value: 58 },
  { label: 'Trend', value: 72 }
]

const displayCards = [
  { label: 'WAM', value: '数量卡', copy: '当前先展示设备总数与状态类型说明。' },
  { label: 'Lenze', value: '环形总览', copy: '适合强调 OK 为主、少量异常的状态结构。' },
  { label: 'Filling', value: '环图 + 堆叠', copy: '先看 NOK 占比，再看各工位分布差异。' },
  { label: 'Style', value: 'Dark Benz', copy: '统一维持蓝黑底、青色高亮和玻璃卡层次。' }
]

const chartGuides = [
  { label: 'WAM', value: '数量卡优先', progress: 42 },
  { label: 'Lenze', value: '环形图优先', progress: 90 },
  { label: 'Filling', value: '环图 + 堆叠条', progress: 84 },
  { label: '全局', value: '总览先于明细', progress: 76 }
]

const placeholderNotes = [
  { title: '当前不接真实数据', copy: '这一版只做前端展示结构和视觉样式，后续再接 Excel 或接口数据。' },
  { title: 'WAM 暂时不展示占比', copy: '因为当前文件不适合直接映射真实 OK / NOK，所以先做数量型总览。' },
  { title: 'Lenze、Filling 与 High-Risk 已预留图形位', copy: '后续接入数据后，只需要替换环图角度、标签文案和工位条形宽度。' }
]

const fillingCard = ref({
  nokCount: 360,
  okCount: 213,
  note: '这一块更适合突出 NOK 占比，再用工位堆叠条补充 Filing1 到 Filing4 的分布差异。'
})

const fillingStations = ref([
  { label: 'Filing1', ok: 65, nok: 125, okWidth: 34, nokWidth: 66 },
  { label: 'Filing2', ok: 77, nok: 56, okWidth: 58, nokWidth: 42 },
  { label: 'Filing3', ok: 48, nok: 88, okWidth: 35, nokWidth: 65 },
  { label: 'Filing4', ok: 23, nok: 91, okWidth: 20, nokWidth: 80 }
])

const highRiskCard = ref({
  total: 14,
  groupCount: 3
})

const highRiskLegend = ref([
  { label: 'AS1 / 核心风险组', value: '6', color: '#00d8ff' },
  { label: 'MRA / 中风险组', value: '4', color: '#ffcc00' },
  { label: '其他车间 / 待跟进', value: '4', color: '#ff7a7a' }
])

const lenzeCard = ref({
  okCount: 172,
  warningCount: 1,
  alarmCount: 2,
  note: '适合用单个环形图强调“绝大多数正常，少量异常”的状态结构。'
})

const wamCard = ref({
  deviceCount: 9,
  note: '当前先展示设备数量和状态类型说明，后续接入真实状态后再切换为三段环图。',
  statusTypes: [
    { label: 'OK', className: 'border border-benz-cyan/20 bg-benz-cyan/10 text-benz-cyan' },
    { label: 'Warning', className: 'border border-amber-400/18 bg-amber-400/10 text-amber-300' },
    { label: 'Fault', className: 'border border-red-400/18 bg-red-500/10 text-red-300' }
  ]
})

const buildStatusTypeClass = (label) => {
  const normalized = String(label).toLowerCase()
  if (normalized.includes('warn')) return 'border border-amber-400/18 bg-amber-400/10 text-amber-300'
  if (normalized.includes('fault') || normalized.includes('alarm') || normalized.includes('nok')) {
    return 'border border-red-400/18 bg-red-500/10 text-red-300'
  }
  return 'border border-benz-cyan/20 bg-benz-cyan/10 text-benz-cyan'
}

const applyOverviewSnapshot = (snapshot) => {
  const blocks = snapshot?.blocks || []
  const findBlock = (key) => blocks.find((block) => block.key === key)?.payload || {}

  const wamPayload = findBlock('wam')
  if (Object.keys(wamPayload).length) {
    wamCard.value = {
      deviceCount: wamPayload.device_count ?? wamCard.value.deviceCount,
      note: wamPayload.note || wamCard.value.note,
      statusTypes: (wamPayload.status_types || []).map((status) => ({
        label: status,
        className: buildStatusTypeClass(status)
      }))
    }
    if (!wamCard.value.statusTypes.length) {
      wamCard.value.statusTypes = [
        { label: 'OK', className: buildStatusTypeClass('OK') },
        { label: 'Warning', className: buildStatusTypeClass('Warning') },
        { label: 'Fault', className: buildStatusTypeClass('Fault') }
      ]
    }
  }

  const lenzePayload = findBlock('lenze')
  if (Object.keys(lenzePayload).length) {
    const counts = lenzePayload.status_counts || {}
    lenzeCard.value = {
      okCount: counts.OK ?? lenzeCard.value.okCount,
      warningCount: counts.Warning ?? lenzeCard.value.warningCount,
      alarmCount: counts.Alarm ?? lenzeCard.value.alarmCount,
      note: '已从温度结果文件重算状态计数。'
    }
  }

  const fillingPayload = findBlock('filling')
  if (Object.keys(fillingPayload).length) {
    const counts = fillingPayload.status_counts || {}
    fillingCard.value = {
      okCount: counts.OK ?? fillingCard.value.okCount,
      nokCount: counts.NOK ?? fillingCard.value.nokCount,
      note: '已从灌注状态文件重算 OK / NOK，并同步到工位分布。'
    }
    fillingStations.value = (fillingPayload.station_breakdown || []).map((station) => {
      const total = station.total || station.ok + station.nok || 1
      return {
        label: String(station.station).replace('MRA1_', ''),
        ok: station.ok,
        nok: station.nok,
        okWidth: Math.round((station.ok / total) * 100),
        nokWidth: Math.round((station.nok / total) * 100)
      }
    })
  }

  const highRiskPayload = findBlock('high_risk_distribution')
  if (Object.keys(highRiskPayload).length) {
    highRiskCard.value = {
      total: highRiskPayload.total_high_risk ?? highRiskCard.value.total,
      groupCount: highRiskPayload.group_count ?? highRiskCard.value.groupCount
    }
    highRiskLegend.value = (highRiskPayload.groups || []).slice(0, 3).map((item, index) => ({
      label: item.group,
      value: String(item.high_risk_count),
      color: ['#00d8ff', '#ffcc00', '#ff7a7a'][index % 3]
    }))
  }
}

const refreshOverviewData = async () => {
  refreshLoading.value = true
  refreshStatus.value = '正在读取本地文件和数据库...'
  try {
    const response = await fetch(`${devDataApiBase}/refresh`, {
      method: 'POST'
    })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const payload = await response.json()
    applyOverviewSnapshot(payload.snapshot)
    refreshStatus.value = `刷新完成：${payload.snapshot?.generated_at || '数据已更新'}`
  } catch (error) {
    refreshStatus.value = '刷新失败：请先启动 standalone_data_service.dev_api'
    console.error('refreshOverviewData failed:', error)
  } finally {
    refreshLoading.value = false
  }
}

onMounted(() => {
  ctx = gsap.context(() => {
    gsap.set(headerRef.value, { opacity: 0, y: -22 })
    gsap.set(leftCardRef.value, { opacity: 0, x: -64, filter: 'blur(10px)' })
    gsap.set(rightCardRef.value, { opacity: 0, x: 64, filter: 'blur(10px)' })
    gsap.set(centerCardRef.value, { opacity: 0, y: 84, scale: 0.96, filter: 'blur(12px)' })
    gsap.set(detailRefs.value, { opacity: 0, y: 72, filter: 'blur(8px)' })

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
      detailRefs.value,
      {
        opacity: 1,
        y: 0,
        filter: 'blur(0px)',
        duration: 0.9,
        stagger: 0.12,
        ease: 'power3.out'
      },
      '-=0.38'
    )

    gsap.from('.trend-fill', {
      height: 0,
      duration: 1.1,
      stagger: 0.08,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: dashboardSection.value,
        start: 'top 58%',
        toggleActions: 'play none none reverse',
        invalidateOnRefresh: true
      }
    })
  }, dashboardSection.value)

  requestAnimationFrame(() => {
    ScrollTrigger.refresh()
  })
})

onUnmounted(() => {
  ctx?.revert()
})
</script>
