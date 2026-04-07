<template>
  <section
    id="people"
    ref="peopleSection"
    class="relative z-30 -mt-[10vh] overflow-hidden pt-[18vh] pb-16 sm:pt-[20vh] sm:pb-20 lg:pt-[22vh] lg:pb-24"
    style="perspective: 1200px;"
  >
    <img
      ref="peopleBackgroundRef"
      :src="peopleBackgroundUrl"
      alt=""
      aria-hidden="true"
      class="absolute inset-0 h-full w-full object-cover object-center opacity-[0.34]"
    />
    <div
      class="absolute inset-0 bg-[linear-gradient(180deg,rgba(11,11,12,0.78)_0%,rgba(11,11,12,0.54)_28%,rgba(11,11,12,0.84)_100%),radial-gradient(circle_at_top_right,rgba(0,255,255,0.14),transparent_34%)]"
      aria-hidden="true"
    ></div>

    <div class="relative z-10 mx-auto max-w-[1440px] px-4 sm:px-6 lg:px-10">
      <article
        ref="bridgeRef"
        class="mx-auto mb-14 max-w-[980px] rounded-[32px] border border-benz-blue/18 bg-[linear-gradient(180deg,rgba(0,113,227,0.16),rgba(8,12,18,0.9)_24%,rgba(5,7,10,0.96))] p-6 shadow-[0_28px_90px_rgba(0,0,0,0.42)] backdrop-blur-2xl"
      >
        <div class="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div class="max-w-2xl">
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-benz-cyan">Layer Transition</p>
            <h3 class="mt-3 text-2xl font-semibold tracking-[-0.04em] text-white sm:text-3xl">
              从系统能力切换到负责人入口，用角色视角接住页面入口。
            </h3>
            <p class="mt-3 text-sm leading-7 text-white/[0.58] sm:text-base">
              上一层讲的是模块，这一层讲的是谁负责进入什么页面，让门户内容从功能结构自然过渡到日常使用路径。
            </p>
          </div>
          <div class="grid grid-cols-3 gap-3 text-left">
            <div class="rounded-[20px] border border-benz-blue/16 bg-[linear-gradient(180deg,rgba(0,48,105,0.12),rgba(5,8,12,0.92))] px-4 py-3">
              <p class="text-xs uppercase tracking-[0.2em] text-benz-gray">Pulse</p>
              <p class="mt-2 text-xl font-semibold text-white">Live</p>
            </div>
            <div class="rounded-[20px] border border-benz-cyan/22 bg-[linear-gradient(180deg,rgba(0,113,227,0.24),rgba(5,8,12,0.94))] px-4 py-3">
              <p class="text-xs uppercase tracking-[0.2em] text-benz-gray">Bridge</p>
              <p class="mt-2 text-xl font-semibold text-benz-cyan">Shift</p>
            </div>
            <div class="rounded-[20px] border border-benz-blue/16 bg-[linear-gradient(180deg,rgba(0,48,105,0.12),rgba(5,8,12,0.92))] px-4 py-3">
              <p class="text-xs uppercase tracking-[0.2em] text-benz-gray">People</p>
              <p class="mt-2 text-xl font-semibold text-white">Entry</p>
            </div>
          </div>
        </div>
      </article>

      <div ref="headingRef" class="mb-16 max-w-3xl">
        <p class="text-sm font-semibold uppercase tracking-[0.3em] text-benz-blue">People Entry</p>
        <h2 class="mt-4 text-4xl font-semibold tracking-[-0.05em] text-white sm:text-5xl lg:text-6xl">
          负责人入口与常用页面
        </h2>
        <p class="mt-4 text-base leading-8 text-benz-gray sm:text-lg">
          不再按系统名平铺入口，而是按当前项目里的负责人和使用场景，把 Dashboard、Monitoring、Devices、Alerts、DevOps 串起来。
        </p>
      </div>

      <div class="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="person in people"
          :key="person.name"
          :ref="setCardRef"
          class="interactive-glow people-card group rounded-[32px] border border-benz-blue/16 bg-[linear-gradient(180deg,rgba(0,52,114,0.12),rgba(9,13,18,0.92)_22%,rgba(6,8,10,0.98))] p-7 shadow-panel transition-colors duration-300 hover:border-benz-cyan/24"
        >
          <div :ref="setCardInnerRef" class="people-card-inner">
            <div class="flex items-start gap-5">
              <div class="h-20 w-20 shrink-0 overflow-hidden rounded-[24px] border border-benz-blue/18 bg-[linear-gradient(180deg,rgba(0,113,227,0.12),rgba(5,8,12,0.96))]">
                <img
                  :src="person.image"
                  :alt="`${person.name} 头像`"
                  class="h-full w-full object-cover grayscale transition-all duration-500 group-hover:grayscale-0"
                />
              </div>

              <div class="min-w-0 flex-1">
                <p class="text-xs font-bold uppercase tracking-[0.28em] text-benz-blue">{{ person.title }}</p>
                <h3 class="mt-2 text-3xl font-bold tracking-tight text-white">{{ person.name }}</h3>
                <p class="mt-3 text-sm leading-7 text-benz-gray">{{ person.summary }}</p>

                <div class="mt-6 flex flex-wrap gap-2">
                  <button
                    v-for="app in person.apps"
                    :key="app.label"
                    type="button"
                    :ref="bindGlow"
                    class="interactive-glow portal-chip"
                    @click="router.push(app.to)"
                  >
                    {{ app.label }}
                  </button>
                </div>
              </div>
            </div>

            <div class="mt-7 rounded-[24px] border border-benz-blue/14 bg-[linear-gradient(180deg,rgba(0,48,105,0.1),rgba(5,8,12,0.92))] p-4">
              <div class="mb-3 flex items-center justify-between gap-4">
                <span class="text-xs font-semibold uppercase tracking-[0.22em] text-benz-gray">负责范围</span>
                <span class="rounded-[16px] border border-benz-cyan/22 bg-benz-blue/12 px-3 py-1 text-xs font-semibold text-benz-cyan">
                  {{ person.scope }}
                </span>
              </div>
              <ul class="space-y-2 text-sm leading-6 text-white/[0.62]">
                <li v-for="item in person.highlights" :key="item">{{ item }}</li>
              </ul>
            </div>
          </div>
        </article>
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
const peopleSection = ref(null)
const peopleBackgroundRef = ref(null)
const bridgeRef = ref(null)
const headingRef = ref(null)
const cardRefs = ref([])
const cardInnerRefs = ref([])
const peopleBackgroundUrl = `${import.meta.env.BASE_URL}portal-people-bg.jpg`
let ctx

const setCardRef = (el) => {
  if (el && !cardRefs.value.includes(el)) {
    cardRefs.value.push(el)
  }
}

const setCardInnerRef = (el) => {
  if (el && !cardInnerRefs.value.includes(el)) {
    cardInnerRefs.value.push(el)
  }
}

const people = [
  {
    name: '张妍',
    title: 'KUKA Lead',
    image: `${import.meta.env.BASE_URL}portal-people/zhang-yan.svg`,
    summary: '更适合承接机器人总览和关键轨迹检查相关入口，覆盖调试、联调和班次巡检视角。',
    scope: '总览 / 监控',
    highlights: ['Dashboard 总览入口', 'Monitoring 诊断巡检', '机器人调试联动'],
    apps: [
      { label: '机器人总览', to: '/dashboard' },
      { label: '轨迹检查', to: '/monitoring' }
    ]
  },
  {
    name: '钟鸣',
    title: 'Production Systems',
    image: `${import.meta.env.BASE_URL}portal-people/zhong-ming.svg`,
    summary: '更偏向入口整合和结构梳理，适合连接门户首页、机器人状态和综合页面编排。',
    scope: '入口 / 状态',
    highlights: ['门户入口编排', 'Devices 页面收口', '场景路径整理'],
    apps: [
      { label: '门户总览', to: '/dashboard' },
      { label: '机器人状态', to: '/devices' }
    ]
  },
  {
    name: '赵洋',
    title: 'Operations Enablement',
    image: `${import.meta.env.BASE_URL}portal-people/zhao-yang.svg`,
    summary: '围绕值班和支持使用场景，适合快速进入监控、告警和处理链路。',
    scope: '支持 / 值班',
    highlights: ['支持路径整理', '告警处理入口', '值班巡检视角'],
    apps: [
      { label: '监控中心', to: '/monitoring' },
      { label: '周期同步', to: '/alerts' }
    ]
  },
  {
    name: '闫宇灿',
    title: 'Energy Expert',
    image: `${import.meta.env.BASE_URL}portal-people/yan-yucan.svg`,
    summary: '当前门户里更适合落在设备状态、风险观察和偏工艺诊断的使用路径上。',
    scope: '设备 / 风险',
    highlights: ['设备状态查看', '高风险列表关注', '诊断入口协同'],
    apps: [
      { label: '设备状态', to: '/devices' },
      { label: '轨迹诊断', to: '/monitoring' }
    ]
  },
  {
    name: '刘飞',
    title: 'Process Eng.',
    image: `${import.meta.env.BASE_URL}portal-people/liu-fei.svg`,
    summary: '更贴近程序周期同步和技术管理，适合从分析结果继续进入维护和发布处理。',
    scope: '告警 / 技术',
    highlights: ['PROGRAM CYCLE SYNC 入口', '技术管理协同', '分析结果落地'],
    apps: [
      { label: '周期同步', to: '/alerts' },
      { label: 'DevOps', to: '/devops' }
    ]
  }
]

onMounted(() => {
  ctx = gsap.context(() => {
    gsap.set(bridgeRef.value, {
      opacity: 0,
      y: 90,
      scale: 0.92,
      filter: 'blur(10px)'
    })
    gsap.set(headingRef.value, { opacity: 0, y: 26 })
    gsap.set(cardRefs.value, {
      y: 100,
      rotationX: 15,
      opacity: 0,
      transformOrigin: 'top center',
      filter: 'blur(8px)'
    })

    gsap.to(bridgeRef.value, {
      opacity: 1,
      y: 0,
      scale: 1,
      filter: 'blur(0px)',
      duration: 1,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: peopleSection.value,
        start: 'top 92%',
        end: 'top 58%',
        scrub: 1,
        invalidateOnRefresh: true
      }
    })

    gsap.to(headingRef.value, {
      opacity: 1,
      y: 0,
      duration: 0.8,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: peopleSection.value,
        start: 'top 82%',
        toggleActions: 'play none none reverse',
        invalidateOnRefresh: true
      }
    })

    gsap.to(peopleBackgroundRef.value, {
      yPercent: 10,
      scale: 1.06,
      ease: 'none',
      scrollTrigger: {
        trigger: peopleSection.value,
        start: 'top bottom',
        end: 'bottom top',
        scrub: 1,
        invalidateOnRefresh: true
      }
    })

    gsap.to(cardRefs.value, {
      y: 0,
      rotationX: 0,
      opacity: 1,
      filter: 'blur(0px)',
      duration: 0.85,
      stagger: 0.14,
      ease: 'power2.out',
      scrollTrigger: {
        trigger: peopleSection.value,
        start: 'top 74%',
        toggleActions: 'play none none reverse',
        invalidateOnRefresh: true
      }
    })

    gsap.to(cardInnerRefs.value, {
      y: (index) => {
        const offset = index % 3
        if (offset === 0) return -22
        if (offset === 1) return 10
        return -10
      },
      ease: 'none',
      scrollTrigger: {
        trigger: peopleSection.value,
        start: 'top bottom',
        end: 'bottom top',
        scrub: 1,
        invalidateOnRefresh: true
      }
    })
  }, peopleSection.value)

  requestAnimationFrame(() => {
    ScrollTrigger.refresh()
  })
})

onUnmounted(() => {
  ctx?.revert()
})
</script>

<style scoped>
.people-card {
  transform-style: preserve-3d;
}

.people-card-inner {
  transition:
    transform 0.45s cubic-bezier(0.28, 0.11, 0.32, 1),
    filter 0.45s cubic-bezier(0.28, 0.11, 0.32, 1);
  will-change: transform;
}

.people-card:hover .people-card-inner,
.people-card:focus-within .people-card-inner {
  transform: translateY(-6px) translateZ(18px) scale(1.01);
  filter: drop-shadow(0 18px 28px rgba(0, 0, 0, 0.24));
}
</style>
