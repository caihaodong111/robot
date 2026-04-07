<template>
  <header
    class="fixed inset-x-0 top-0 z-50 border-b border-benz-blue/14 bg-benz-black/70 backdrop-blur-2xl transition-all duration-300"
  >
    <div class="mx-auto flex max-w-[1440px] items-center justify-between px-5 py-3 lg:px-10">
      <button
        type="button"
        class="portal-btn-reset flex items-center gap-3 p-0 text-left text-white"
        @click="scrollToSection('hero')"
      >
        <div
          class="flex h-11 w-11 items-center justify-center rounded-2xl border border-benz-cyan/25 bg-[linear-gradient(180deg,rgba(0,113,227,0.2),rgba(11,11,12,0.9))] text-benz-cyan shadow-[0_0_24px_rgba(0,113,227,0.18)]"
        >
          <svg viewBox="0 0 48 48" class="h-6 w-6" fill="currentColor" aria-hidden="true">
            <path d="M24 6c1.6 8.7 4.8 12 13.5 13.5C28.8 21 25.6 24.2 24 33c-1.6-8.8-4.8-12-13.5-13.5C19.2 18 22.4 14.7 24 6Z" />
          </svg>
        </div>
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.28em] text-benz-cyan">Mercedes-Benz</p>
          <p class="text-lg font-semibold tracking-tight">Robotics Portal</p>
        </div>
      </button>

      <nav class="portal-nav-shell hidden items-center gap-1 lg:flex">
        <button
          v-for="item in navItems"
          :key="item.name"
          type="button"
          class="portal-btn-reset portal-nav-pill group"
          :class="
            activeMenu === item.name
              ? 'portal-nav-pill-active'
              : ''
          "
          @click="handleNav(item)"
        >
          <span>{{ item.name }}</span>
          <svg
            v-if="item.hasMenu"
            viewBox="0 0 10 6"
            class="ml-1.5 inline-block h-2.5 w-2.5 transition-transform duration-300"
            :class="activeMenu === item.name ? 'rotate-180 text-benz-blue' : 'opacity-60 group-hover:opacity-100'"
            aria-hidden="true"
          >
            <path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" />
          </svg>
        </button>
      </nav>

      <div class="flex items-center gap-3">
        <button
          type="button"
          class="portal-btn-reset portal-nav-pill px-4 py-2 text-sm lg:hidden"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          菜单
        </button>
        <button
          type="button"
          :ref="bindGlow"
          class="portal-btn-reset interactive-glow portal-btn-primary px-6 py-2.5 text-[15px] active:scale-[0.98]"
          @click="router.push('/dashboard')"
        >
          进入系统
        </button>
      </div>
    </div>
  </header>

  <Transition name="megamenu">
    <div
      v-show="activeMenu"
      class="fixed inset-0 top-[73px] z-40 overflow-y-auto border-t border-benz-blue/14 bg-benz-black/58 backdrop-blur-[28px]"
      @click.self="activeMenu = null"
    >
      <div class="mx-auto max-w-[1440px] px-6 py-10 lg:px-10 lg:py-16">
        <div class="mb-10 max-w-2xl">
          <p class="text-sm font-semibold uppercase tracking-[0.32em] text-benz-cyan">{{ activeMenu }}</p>
          <h2 class="mt-4 text-4xl font-semibold tracking-tight text-white lg:text-6xl">
            {{ activeMenu === '产品' ? '把当前项目里的核心页面组织成清晰入口。' : '让值班、排查和技术处理路径更直接。' }}
          </h2>
        </div>

        <div class="grid gap-5 lg:grid-cols-4">
          <article
            v-for="section in currentMenuContent"
            :key="section.title"
            :ref="bindGlow"
            class="interactive-glow overflow-hidden rounded-[32px] border border-benz-blue/18 bg-[linear-gradient(180deg,rgba(0,113,227,0.12),rgba(8,12,18,0.94)_34%,rgba(5,7,10,0.98))] p-6 shadow-panel transition-transform duration-500 ease-apple-ease hover:-translate-y-1"
          >
            <p class="text-xs font-bold uppercase tracking-[0.28em] text-benz-gray">{{ section.title }}</p>
            <ul class="mt-6 space-y-3">
              <li v-for="link in section.links" :key="link.name">
                <a
                  href="#"
                  :ref="bindGlow"
                  class="portal-menu-link interactive-glow group"
                  @click.prevent="navigate(link)"
                >
                  <div
                    class="mt-0.5 flex h-11 w-11 shrink-0 items-center justify-center rounded-[18px] border border-benz-blue/22 bg-[linear-gradient(180deg,rgba(0,113,227,0.16),rgba(6,10,16,0.96))] text-benz-cyan transition-colors duration-300 group-hover:border-benz-cyan/50"
                  >
                    <span class="h-2.5 w-2.5 rounded-full bg-current"></span>
                  </div>
                  <div>
                    <p class="text-base font-semibold text-white transition-colors duration-300 group-hover:text-benz-cyan">
                      {{ link.name }}
                    </p>
                    <p class="mt-1 text-sm leading-relaxed text-benz-gray">{{ link.desc }}</p>
                  </div>
                </a>
              </li>
            </ul>
          </article>
        </div>
      </div>
    </div>
  </Transition>

  <Transition name="megamenu">
    <div
      v-show="mobileMenuOpen"
      class="fixed inset-0 top-[73px] z-40 overflow-y-auto border-t border-benz-blue/14 bg-benz-black/72 px-5 py-6 backdrop-blur-[28px] lg:hidden"
      @click.self="mobileMenuOpen = false"
    >
      <div class="mx-auto max-w-[720px] space-y-8">
        <div class="space-y-3">
          <p class="text-xs font-semibold uppercase tracking-[0.32em] text-benz-cyan">Navigation</p>
          <div class="grid gap-3">
            <button
              v-for="item in navItems"
              :key="`mobile-${item.name}`"
              type="button"
              class="portal-btn-reset portal-mobile-link text-lg font-semibold text-white"
              @click="handleMobileNav(item)"
            >
              {{ item.name }}
            </button>
          </div>
        </div>

        <div class="space-y-3">
          <p class="text-xs font-semibold uppercase tracking-[0.32em] text-benz-cyan">Quick Access</p>
          <div class="grid gap-3">
            <a
              v-for="link in mobileQuickLinks"
              :key="link.name"
              href="#"
              class="portal-mobile-link block"
              @click.prevent="navigate(link, { closeMobile: true })"
            >
              <p class="text-base font-semibold text-white">{{ link.name }}</p>
              <p class="mt-1 text-sm leading-6 text-benz-gray">{{ link.desc }}</p>
            </a>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useMouseMoveGlow } from '@/utils/useMouseMoveGlow'

const router = useRouter()
const { bindGlow } = useMouseMoveGlow()
const activeMenu = ref(null)
const mobileMenuOpen = ref(false)

const navItems = [
  { name: '首页', target: 'hero', hasMenu: false },
  { name: '产品', hasMenu: true },
  { name: '人员入口', target: 'people', hasMenu: false },
  { name: '支持', hasMenu: true }
]

const menuData = {
  产品: [
    {
      title: '智能看板',
      links: [
        { name: '当班节拍', desc: '实时 Robot 节拍与 OK 率联动', type: 'route', to: '/dashboard' },
        { name: '机器人总览', desc: '进入 Dashboard 查看总体风险和分组态势', type: 'route', to: '/dashboard' }
      ]
    },
    {
      title: '业务入口',
      links: [
        { name: '关键轨迹检查', desc: '进入 Monitoring 做机器人与时间区间诊断', type: 'route', to: '/monitoring' },
        { name: '机器人状态', desc: '进入 Devices 查看状态和高风险机器人列表', type: 'route', to: '/devices' }
      ]
    },
    {
      title: '应用矩阵',
      links: [
        { name: '程序周期同步', desc: '进入 Alerts 做 PROGRAM CYCLE SYNC 分析', type: 'route', to: '/alerts' },
        { name: '负责人入口', desc: '按负责人进入当前项目常用页面', type: 'scroll', target: 'people' }
      ]
    },
    {
      title: '运维观测',
      links: [
        { name: '技术管理', desc: '进入 DevOps 处理技术管理相关内容', type: 'route', to: '/devops' },
        { name: '门户首屏', desc: '回到门户首页重新选择入口', type: 'scroll', target: 'hero' }
      ]
    }
  ],
  支持: [
    {
      title: '文档',
      links: [
        { name: '门户说明', desc: '回到首页查看当前系统入口结构', type: 'scroll', target: 'hero' },
        { name: '模块总览', desc: '查看 Dashboard 与主能力编排', type: 'scroll', target: 'dashboard' }
      ]
    },
    {
      title: '值班支持',
      links: [
        { name: '轨迹诊断', desc: '快速进入 Monitoring 排查异常机器人', type: 'route', to: '/monitoring' },
        { name: '周期同步分析', desc: '进入 Alerts 查看程序周期同步问题', type: 'route', to: '/alerts' }
      ]
    },
    {
      title: '系统访问',
      links: [
        { name: '机器人总览', desc: '跳转到 Dashboard', type: 'route', to: '/dashboard' },
        { name: '设备状态', desc: '进入 Devices 页面', type: 'route', to: '/devices' }
      ]
    },
    {
      title: '应用负责人',
      links: [
        { name: '负责人入口墙', desc: '按负责人进入常用页面', type: 'scroll', target: 'people' },
        { name: '门户首页', desc: '回到主视觉首屏', type: 'scroll', target: 'hero' }
      ]
    }
  ]
}

const currentMenuContent = computed(() => menuData[activeMenu.value] || [])
const mobileQuickLinks = [
  { name: '机器人总览', desc: '进入 Dashboard 查看总体概况', type: 'route', to: '/dashboard' },
  { name: '关键轨迹检查', desc: '进入 Monitoring 做巡检诊断', type: 'route', to: '/monitoring' },
  { name: '负责人入口', desc: '跳转到人员入口区', type: 'scroll', target: 'people' },
  { name: '门户首屏', desc: '回到首页重新选择入口', type: 'scroll', target: 'hero' }
]

const scrollToSection = (id) => {
  activeMenu.value = null
  mobileMenuOpen.value = false
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const toggleMenu = (name) => {
  activeMenu.value = activeMenu.value === name ? null : name
}

const handleNav = (item) => {
  if (item.hasMenu) {
    mobileMenuOpen.value = false
    toggleMenu(item.name)
    return
  }

  scrollToSection(item.target)
}

const handleMobileNav = (item) => {
  if (item.hasMenu) {
    mobileMenuOpen.value = false
    toggleMenu(item.name)
    return
  }

  scrollToSection(item.target)
}

const navigate = (link, options = {}) => {
  if (options.closeMobile) {
    mobileMenuOpen.value = false
  }

  if (link.type === 'route') {
    activeMenu.value = null
    router.push(link.to)
    return
  }

  scrollToSection(link.target)
}

const handleKeydown = (event) => {
  if (event.key === 'Escape') {
    activeMenu.value = null
    mobileMenuOpen.value = false
  }
}

watch(activeMenu, (value) => {
  document.body.style.overflow = value || mobileMenuOpen.value ? 'hidden' : ''
})

watch(mobileMenuOpen, (value) => {
  document.body.style.overflow = value || activeMenu.value ? 'hidden' : ''
})

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.megamenu-enter-active,
.megamenu-leave-active {
  transition:
    opacity 0.45s ease,
    transform 0.45s cubic-bezier(0.28, 0.11, 0.32, 1);
}

.megamenu-enter-from,
.megamenu-leave-to {
  opacity: 0;
  transform: translateY(-14px);
}
</style>
