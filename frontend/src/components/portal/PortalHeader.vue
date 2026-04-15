<template>
  <header
    class="fixed inset-x-0 top-0 z-50 border-b border-white/6 bg-[linear-gradient(180deg,rgba(5,7,12,0.9),rgba(5,7,12,0.56))] backdrop-blur-2xl transition-all duration-300"
  >
    <div class="mx-auto flex max-w-[1440px] items-center justify-between px-5 py-3 lg:px-8">
      <button
        type="button"
        class="portal-btn-reset flex items-center gap-3 rounded-[24px] px-2 py-1.5 text-left text-white transition-colors duration-300 hover:bg-white/[0.03]"
        @click="scrollToSection('hero')"
      >
        <div
          class="flex h-11 w-11 items-center justify-center rounded-2xl border border-benz-cyan/20 bg-[linear-gradient(180deg,rgba(0,113,227,0.14),rgba(11,11,12,0.92))] text-benz-cyan shadow-[0_0_24px_rgba(0,113,227,0.14)]"
        >
          <svg viewBox="0 0 64 64" class="h-6 w-6" aria-hidden="true">
            <circle cx="32" cy="32" r="25" fill="none" stroke="currentColor" stroke-width="2.6" />
            <circle cx="32" cy="32" r="4.2" fill="currentColor" />
            <path d="M32 12.5v19.8" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" />
            <path d="M32 32 17.4 49.3" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" />
            <path d="M32 32 46.6 49.3" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" />
          </svg>
        </div>
        <div>
          <p class="text-[11px] font-semibold uppercase tracking-[0.28em] text-benz-cyan/90">Mercedes-Benz</p>
          <p class="text-lg font-semibold tracking-tight text-white">Robotics Portal</p>
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
      class="pointer-events-none fixed inset-x-0 top-[78px] z-40 px-5 lg:px-8"
      @click.self="activeMenu = null"
    >
      <div class="mx-auto max-w-[1320px]">
        <div
          class="pointer-events-auto overflow-hidden rounded-[34px] border border-white/8 bg-[linear-gradient(180deg,rgba(6,9,14,0.94),rgba(6,9,14,0.78))] px-6 py-7 shadow-[0_28px_80px_rgba(0,0,0,0.42)] backdrop-blur-[28px] lg:px-8 lg:py-8"
        >
        <div class="grid gap-4 lg:grid-cols-4">
          <a
            v-for="link in currentMenuLinks"
            :key="link.name"
            href="#"
            :ref="bindGlow"
            class="portal-menu-link interactive-glow group min-h-[124px]"
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
        </div>
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
  { name: '应用入口', target: 'apps', hasMenu: false },
  { name: '支持', hasMenu: true }
]

const menuData = {
  产品: [
    {
      title: '智能看板',
      links: [
        { name: '机器人总览', desc: '进入 Dashboard 查看分组、高风险和连接状态总览。', type: 'route', to: '/dashboard' },
        { name: '核心数据看板', desc: '在门户看板区快速查看 WAM、Lenze、Filling 与高风险分布。', type: 'scroll', target: 'dashboard' }
      ]
    },
    {
      title: '业务入口',
      links: [
        { name: '关键轨迹检查', desc: '进入 Monitoring 按机器人和时间区间排查轨迹异常。', type: 'route', to: '/monitoring' },
        { name: '机器人状态', desc: '进入 Devices 查看设备状态与高风险机器人列表。', type: 'route', to: '/devices' }
      ]
    },
    {
      title: '应用矩阵',
      links: [
        { name: '应用入口墙', desc: '按当前 PDM 应用分组进入现场链接和报表系统。', type: 'scroll', target: 'apps' },
        { name: '程序周期同步', desc: '进入 Alerts 查看 PROGRAM CYCLE SYNC 分析结果。', type: 'route', to: '/alerts' }
      ]
    },
    {
      title: '运维观测',
      links: [
        { name: '技术管理', desc: '进入 DevOps 处理技术管理、配置和发布相关内容。', type: 'route', to: '/devops' }
      ]
    }
  ],
  支持: [
    {
      title: '入口定位',
      links: [
        { name: '门户首屏', desc: '回到首页重新确认当前门户的主入口结构。', type: 'scroll', target: 'hero' },
        { name: '应用入口墙', desc: '下滑到应用入口区，按 PDM 应用继续进入各系统。', type: 'scroll', target: 'apps' }
      ]
    },
    {
      title: '值班支持',
      links: [
        { name: '轨迹诊断', desc: '快速进入 Monitoring 排查异常机器人和时间段问题。', type: 'route', to: '/monitoring' },
        { name: '周期同步分析', desc: '进入 Alerts 查看程序周期同步异常和回看结果。', type: 'route', to: '/alerts' }
      ]
    },
    {
      title: '系统访问',
      links: [
        { name: '机器人总览', desc: '跳转到 Dashboard 查看全局分组和高风险分布。', type: 'route', to: '/dashboard' },
        { name: '设备状态', desc: '进入 Devices 页面查看设备状态与重点设备。', type: 'route', to: '/devices' }
      ]
    },
    {
      title: '应用入口',
      links: [
        { name: '技术管理', desc: '进入 DevOps 查看技术处理和运维管理内容。', type: 'route', to: '/devops' },
        { name: '门户首页', desc: '回到主视觉首屏切换不同入口路径。', type: 'scroll', target: 'hero' }
      ]
    }
  ]
}

const currentMenuContent = computed(() => menuData[activeMenu.value] || [])
const currentMenuLinks = computed(() => currentMenuContent.value.flatMap((section) => section.links || []))
const mobileQuickLinks = [
  { name: '机器人总览', desc: '进入 Dashboard 查看总体概况', type: 'route', to: '/dashboard' },
  { name: '关键轨迹检查', desc: '进入 Monitoring 做巡检诊断', type: 'route', to: '/monitoring' },
  { name: '应用入口', desc: '跳转到应用入口区', type: 'scroll', target: 'apps' },
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
