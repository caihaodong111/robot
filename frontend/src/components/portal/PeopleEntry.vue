<template>
  <section
    id="apps"
    ref="appsSection"
    class="relative z-30 -mt-[10vh] overflow-hidden pt-[18vh] pb-16 sm:pt-[20vh] sm:pb-20 lg:pt-[22vh] lg:pb-24"
    style="perspective: 1200px;"
  >
    <img
      ref="appsBackgroundRef"
      :src="appsBackgroundUrl"
      alt=""
      aria-hidden="true"
      class="absolute inset-0 h-full w-full object-cover object-center opacity-[0.34]"
    />
    <div
      class="absolute inset-0 bg-[linear-gradient(180deg,rgba(11,11,12,0.78)_0%,rgba(11,11,12,0.54)_28%,rgba(11,11,12,0.84)_100%),radial-gradient(circle_at_top_right,rgba(0,255,255,0.14),transparent_34%)]"
      aria-hidden="true"
    ></div>

    <div class="relative z-10 mx-auto max-w-[1440px] px-4 sm:px-6 lg:px-10">
      <div ref="headingRef" class="mb-16 max-w-4xl">
        <p class="text-sm font-semibold uppercase tracking-[0.3em] text-benz-blue">Application Entry</p>
        <h2 class="mt-4 text-4xl font-semibold tracking-[-0.05em] text-white sm:text-5xl lg:text-6xl">
          应用入口与常用链接
        </h2>
      </div>

      <div class="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        <article
          v-for="group in appGroups"
          :key="group.key"
          :ref="setInteractiveCardRef"
          class="interactive-glow app-card group h-full rounded-[32px] border border-benz-blue/16 bg-[linear-gradient(180deg,rgba(0,52,114,0.12),rgba(9,13,18,0.92)_22%,rgba(6,8,10,0.98))] p-5 shadow-panel transition-colors duration-300"
          :class="group.links.length === 1 ? 'cursor-pointer hover:border-benz-cyan/28' : 'hover:border-benz-cyan/20'"
          :role="group.links.length === 1 ? 'link' : undefined"
          :tabindex="group.links.length === 1 ? 0 : undefined"
          :aria-label="group.links.length === 1 ? `打开 ${group.name}` : undefined"
          @click="handleCardOpen(group)"
          @keydown.enter.prevent="handleCardOpen(group)"
          @keydown.space.prevent="handleCardOpen(group)"
        >
          <div :ref="setCardInnerRef" class="app-card-inner grid h-full grid-rows-[auto_1fr_auto] gap-5">
            <div class="relative aspect-[1066/700] overflow-hidden rounded-[26px] border border-benz-blue/16 bg-black/30">
              <img
                v-if="group.image"
                :src="group.image"
                :alt="`${group.name} 封面图`"
                class="absolute inset-0 block h-full w-full object-cover transition-transform duration-700 ease-apple-ease group-hover:scale-[1.04]"
              />
              <div
                v-else
                class="flex h-full w-full items-center justify-center bg-[radial-gradient(circle_at_top,rgba(0,255,255,0.18),transparent_34%),linear-gradient(180deg,rgba(0,113,227,0.24),rgba(8,12,18,0.96))]"
              >
                <div class="text-center">
                  <p class="text-xs font-semibold uppercase tracking-[0.28em] text-benz-cyan">Coming Soon</p>
                  <p class="mt-3 text-3xl font-semibold tracking-tight text-white">敬请期待</p>
                </div>
              </div>
              <div
                class="absolute inset-0 bg-[linear-gradient(180deg,rgba(4,8,14,0.08)_0%,rgba(4,8,14,0.16)_35%,rgba(4,8,14,0.92)_100%)]"
                aria-hidden="true"
              ></div>
              <div class="absolute inset-x-0 bottom-0 p-5">
                <p class="text-xs font-bold uppercase tracking-[0.28em] text-benz-cyan">{{ group.title }}</p>
                <h3 class="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-[1.75rem]">{{ group.name }}</h3>
              </div>
            </div>

            <div class="flex-1 rounded-[24px] border border-benz-blue/14 bg-[linear-gradient(180deg,rgba(0,48,105,0.08),rgba(5,8,12,0.92))] p-5">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-xs font-semibold uppercase tracking-[0.24em] text-benz-gray">应用范围</p>
                  <p class="mt-2 text-sm font-semibold text-white">{{ group.scope }}</p>
                </div>
                <span class="rounded-[16px] border border-benz-cyan/22 bg-benz-blue/12 px-3 py-1 text-xs font-semibold text-benz-cyan">
                  {{ group.pending ? '筹备中' : group.links.length === 1 ? '单入口' : '多入口' }}
                </span>
              </div>

              <p class="mt-4 text-sm leading-7 text-benz-gray">
                {{ group.summary }}
              </p>

              <div class="mt-4 flex flex-wrap gap-2">
                <span
                  v-for="tag in group.tags"
                  :key="tag"
                  class="rounded-[14px] border border-white/8 bg-white/[0.03] px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-white/72"
                >
                  {{ tag }}
                </span>
              </div>
            </div>

            <div
              class="gap-2"
              :class="group.links.length === 3 ? 'grid grid-cols-3' : 'flex flex-wrap'"
            >
              <button
                v-for="link in group.links"
                :key="link.label"
                type="button"
                :ref="bindGlow"
                class="interactive-glow portal-chip justify-center"
                :class="group.links.length === 3 ? 'min-w-0 px-2.5 text-[12px] whitespace-nowrap' : ''"
                @click.stop="openUrl(link.url)"
              >
                {{ link.label }}
              </button>
              <span
                v-if="group.pending"
                class="rounded-[16px] border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-semibold text-white/72"
              >
                敬请期待
              </span>
            </div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useMouseMoveGlow } from '@/utils/useMouseMoveGlow'

gsap.registerPlugin(ScrollTrigger)

const { bindGlow } = useMouseMoveGlow()
const appsSection = ref(null)
const appsBackgroundRef = ref(null)
const headingRef = ref(null)
const cardRefs = ref([])
const cardInnerRefs = ref([])
const appsBackgroundUrl = `${import.meta.env.BASE_URL}portal-people-bg.jpg`
const appImageBase = `${import.meta.env.BASE_URL}portal-apps`
const desktopColumns = 4
let ctx
let mediaMatcher

const setCardRef = (el) => {
  if (el && !cardRefs.value.includes(el)) {
    cardRefs.value.push(el)
  }
}

const setInteractiveCardRef = (el) => {
  setCardRef(el)
  bindGlow(el)
}

const setCardInnerRef = (el) => {
  if (el && !cardInnerRefs.value.includes(el)) {
    cardInnerRefs.value.push(el)
  }
}

const chunkRows = (items, size) => {
  const rows = []
  for (let index = 0; index < items.length; index += size) {
    rows.push(items.slice(index, index + size))
  }
  return rows
}

const appGroups = [
  {
    key: 'durr-suite',
    title: 'Shared Station',
    name: 'Durr / Lenze / 高温升降机',
    scope: 'PS2 NVU / PS2+MFA',
    summary: '同一台监控主机下的三类现场入口，覆盖扭矩、Lenze 告警和高温升降机电流查看。',
    tags: ['172.16.29.103', '扭矩', '告警', '电流'],
    image: `${appImageBase}/durr-suite.jpg`,
    links: [
      { label: 'Durr 扭矩', url: 'http://172.16.29.103:500/get_torque' },
      { label: 'Lenze 告警', url: 'http://172.16.29.103:500/PS3lenze-alert' },
      { label: '高温升降机', url: 'http://172.16.29.103:500/PS2HTconveyorcurrent' }
    ]
  },
  {
    key: 'wheel-alignment',
    title: 'PDM Application',
    name: '四轮定位',
    scope: 'BDA AS',
    summary: '四轮定位看板入口，适合直接进入现场状态查看与分析。',
    tags: ['BDA AS', 'WAM', '现场看板'],
    image: `${appImageBase}/wheel-alignment.jpg`,
    links: [
      { label: '打开应用', url: 'http://172.16.17.173:8050/' }
    ]
  },
  {
    key: 'lenze',
    title: 'PDM Application',
    name: 'LENZE',
    scope: 'AS',
    summary: 'Lenze Power BI 报表入口，用于查看相关设备与运行状态。',
    tags: ['Power BI', 'AS', 'LENZE'],
    image: `${appImageBase}/lenze-powerbi.jpg`,
    links: [
      { label: '打开应用', url: 'https://app.powerbi.cn/groups/4c00eb1e-18cd-4dd0-a41c-baceff07900e/reports/88fd389c-4681-4997-b8e5-30bedbdd1252' }
    ]
  },
  {
    key: 'hems',
    title: 'PDM Application',
    name: 'HEMS',
    scope: 'AS',
    summary: 'HEMS 监控入口，承接能源与相关运行状态查看。',
    tags: ['Power BI', 'AS', 'HEMS'],
    image: `${appImageBase}/hems.jpg`,
    links: [
      { label: '打开应用', url: 'https://app.powerbi.cn/groups/4c00eb1e-18cd-4dd0-a41c-baceff07900e/reports/7cccc504-eb44-4211-b756-fc35fb351e1f' }
    ]
  },
  {
    key: 'filling-machine',
    title: 'PDM Application',
    name: '加注机',
    scope: 'AS',
    summary: '加注机报表入口，适合继续查看灌注相关结果和状态分布。',
    tags: ['Power BI', 'AS', 'Filling'],
    image: `${appImageBase}/filling-machine.jpg`,
    links: [
      { label: '打开应用', url: 'https://app.powerbi.cn/groups/4c00eb1e-18cd-4dd0-a41c-baceff07900e/reports/93f1e6ed-6378-41c3-8cb4-0372af3960a6' }
    ]
  },
  {
    key: 'agv',
    title: 'PDM Application',
    name: 'AGV',
    scope: 'Shunyi AS',
    summary: 'AGV 入口，收口顺义 AS 相关报表与运转信息。',
    tags: ['Power BI', 'Shunyi AS', 'AGV'],
    image: `${appImageBase}/agv.jpg`,
    links: [
      { label: '打开应用', url: 'https://app.powerbi.cn/groups/4c00eb1e-18cd-4dd0-a41c-baceff07900e/reports/b83184fa-cff9-45fc-b527-af281a15eb0e' }
    ]
  },
  {
    key: 'digital-lubrication',
    title: 'PDM Application',
    name: '转毂数字化加油',
    scope: 'MRA1 AS',
    summary: 'SKF 系统入口，用于进入转毂数字化加油相关页面。',
    tags: ['SKF', 'MRA1 AS', '数字化加油'],
    image: `${appImageBase}/digital-lubrication.jpg`,
    links: [
      { label: '打开应用', url: 'https://lcp.skf.com.cn/#/home' }
    ]
  },
  {
    key: 'interior-cadence',
    title: 'PDM Application',
    name: '内饰线节拍监控',
    scope: 'AS',
    summary: '内饰线节拍监控报表入口，适合直接查看生产节拍与状态。',
    tags: ['Power BI', 'AS', '节拍监控'],
    image: `${appImageBase}/interior-cadence.jpg`,
    links: [
      { label: '打开应用', url: 'https://app.powerbi.cn/groups/4c00eb1e-18cd-4dd0-a41c-baceff07900e/reports/6131f262-5937-48b1-8450-b7c496da9529' }
    ]
  },
  {
    key: 'ect-tool',
    title: 'PDM Application',
    name: 'ECT工具',
    scope: 'BDA AS',
    summary: '简道云 ECT 工具入口，用于查看和操作相关业务面板。',
    tags: ['简道云', 'BDA AS', '工具页'],
    image: `${appImageBase}/ect-tool.jpg`,
    links: [
      { label: '打开应用', url: 'https://somi0rkqn2.jiandaoyun.com/dash/63183797899d360008ed0461' }
    ]
  },
  {
    key: 'cylinder',
    title: 'PDM Application',
    name: '气缸',
    scope: 'MRA2 AS',
    summary: '气缸相关报表入口，适合进入 MRA2 AS 的设备与过程视图。',
    tags: ['Power BI', 'MRA2 AS', '气缸'],
    image: `${appImageBase}/cylinder.jpg`,
    links: [
      { label: '打开应用', url: 'https://app.powerbi.cn/groups/me/reports/5ea5eafb-c369-4806-a91d-64f34a728269' }
    ]
  },
  {
    key: 'abb-robot',
    title: 'PDM Application',
    name: 'ABB 机器人',
    scope: 'PS1 Primer',
    summary: '当前处于接入筹备阶段，后续会补充正式入口和相关页面。',
    tags: ['PS1 Primer', 'ABB', '筹备中'],
    image: '',
    pending: true,
    links: []
  },
  {
    key: 'intec-gluing',
    title: 'PDM Application',
    name: 'Intec 涂胶',
    scope: 'MRA2 AS',
    summary: '当前处于接入筹备阶段，后续会补充正式入口和相关页面。',
    tags: ['MRA2 AS', 'Intec', '筹备中'],
    image: '',
    pending: true,
    links: []
  }
]

const openUrl = (url) => {
  window.open(url, '_blank', 'noopener,noreferrer')
}

const handleCardOpen = (group) => {
  if (group.pending) {
    return
  }

  if (group.links.length === 1) {
    openUrl(group.links[0].url)
  }
}

onMounted(() => {
  ctx = gsap.context(() => {
    gsap.set(headingRef.value, { opacity: 0, y: 26 })

    gsap.to(headingRef.value, {
      opacity: 1,
      y: 0,
      duration: 0.8,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: appsSection.value,
        start: 'top 82%',
        toggleActions: 'play none none reverse',
        invalidateOnRefresh: true
      }
    })

    gsap.to(appsBackgroundRef.value, {
      yPercent: 10,
      scale: 1.06,
      ease: 'none',
      scrollTrigger: {
        trigger: appsSection.value,
        start: 'top bottom',
        end: 'bottom top',
        scrub: 1,
        invalidateOnRefresh: true
      }
    })

    mediaMatcher = gsap.matchMedia()

    mediaMatcher.add('(min-width: 1280px)', () => {
      const rows = chunkRows(cardRefs.value, desktopColumns)

      rows.forEach((rowCards, rowIndex) => {
        const fromX = rowIndex % 2 === 0 ? -160 : 160

        gsap.fromTo(
          rowCards,
          {
            x: fromX,
            y: 42,
            opacity: 0.18
          },
          {
            x: 0,
            y: 0,
            opacity: 1,
            ease: 'none',
            scrollTrigger: {
              trigger: appsSection.value,
              start: 'top 88%',
              end: 'top 36%',
              scrub: 1,
              invalidateOnRefresh: true
            }
          }
        )
      })
    })

    mediaMatcher.add('(max-width: 1279px)', () => {
      gsap.set(cardRefs.value, {
        y: 48,
        opacity: 0
      })

      gsap.to(cardRefs.value, {
        y: 0,
        opacity: 1,
        duration: 0.8,
        stagger: 0.08,
        ease: 'power2.out',
        scrollTrigger: {
          trigger: appsSection.value,
          start: 'top 80%',
          toggleActions: 'play none none reverse',
          invalidateOnRefresh: true
        }
      })
    })

    gsap.set(cardInnerRefs.value, { y: 0 })
  }, appsSection.value)

  requestAnimationFrame(() => {
    ScrollTrigger.refresh()
  })
})

onUnmounted(() => {
  mediaMatcher?.revert()
  ctx?.revert()
})
</script>

<style scoped>
.app-card {
  transform-style: preserve-3d;
}

.app-card-inner {
  transition:
    transform 0.45s cubic-bezier(0.28, 0.11, 0.32, 1),
    filter 0.45s cubic-bezier(0.28, 0.11, 0.32, 1);
  will-change: transform;
}

.app-card:hover .app-card-inner,
.app-card:focus-within .app-card-inner {
  transform: translateY(-6px) translateZ(18px) scale(1.01);
  filter: drop-shadow(0 18px 28px rgba(0, 0, 0, 0.24));
}
</style>
