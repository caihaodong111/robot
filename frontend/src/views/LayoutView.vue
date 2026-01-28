<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapsed ? '60px' : '220px'" class="app-aside" :class="{ collapsed: isCollapsed }">
      <el-tooltip content="机器人技术管理平台" placement="right" :show-after="500" :disabled="!isCollapsed">
        <div class="logo">
          <el-icon :size="isCollapsed ? 28 : 30"><Cpu /></el-icon>
          <span v-show="!isCollapsed">机器人技术管理平台</span>
        </div>
      </el-tooltip>
      <el-menu
        class="app-menu"
        :default-active="activeMenu"
        :collapse="isCollapsed"
        :collapse-transition="false"
        router
      >
        <el-tooltip content="平台概览" placement="right" :show-after="500" :disabled="!isCollapsed">
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            <span>平台概览</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip content="机器人状态" placement="right" :show-after="500" :disabled="!isCollapsed">
          <el-menu-item index="/devices">
            <el-icon><Cpu /></el-icon>
            <span>机器人状态</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip content="关键轨迹检查" placement="right" :show-after="500" :disabled="!isCollapsed">
          <el-menu-item index="/monitoring">
            <el-icon><TrendCharts /></el-icon>
            <span>关键轨迹检查</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip content="可视化BI" placement="right" :show-after="500" :disabled="!isCollapsed">
          <el-menu-item index="/alerts">
            <el-icon><Bell /></el-icon>
            <span>可视化BI</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip content="应用门户" placement="right" :show-after="500" :disabled="!isCollapsed">
          <el-menu-item index="/portal">
            <el-icon><Grid /></el-icon>
            <span>应用门户</span>
          </el-menu-item>
        </el-tooltip>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部导航 -->
      <el-header>
        <div class="header-content">
          <div class="header-left">
            <el-icon class="collapse-btn" @click="toggleCollapse">
              <Expand v-if="isCollapsed" />
              <Fold v-else />
            </el-icon>
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item>{{ currentPageName }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="user-info">
            <el-dropdown>
              <span class="user-name">
                <el-icon><User /></el-icon>
                {{ userStore.username }}
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleLogout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <!-- 页面内容 -->
      <el-main class="app-main">
        <div class="page-shell">
          <RouterView />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  Odometer, Cpu, TrendCharts, Bell, User, SwitchButton, Grid, Expand, Fold
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useLayoutStore } from '@/stores/layout'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const layoutStore = useLayoutStore()

const isCollapsed = computed(() => layoutStore.isCollapsed)

const toggleCollapse = () => {
  layoutStore.toggleCollapse()
}

const activeMenu = computed(() => route.path)

const currentPageName = computed(() => {
  const names = {
    '/dashboard': '平台概览',
    '/devices': '机器人状态',
    '/monitoring': '关键轨迹检查',
    '/alerts': '可视化BI',
    '/portal': '应用门户'
  }
  return names[route.path] || '首页'
})

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      type: 'warning'
    })
    await userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    // 用户取消操作
  }
}
</script>

<style scoped>
.layout-container {
  height: 100%;
}

.app-aside {
  background: var(--app-surface);
  border-right: 1px solid var(--app-border);
  color: var(--app-text);
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
  will-change: width;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
  color: var(--app-text);
  gap: 8px;
  border-bottom: 1px solid var(--app-border);
  padding: 0 10px;
  white-space: nowrap;
}

.app-aside.collapsed .logo {
  padding: 0;
}

.app-menu {
  border-right: none;
}

.app-menu :deep(.el-menu-item),
.app-menu :deep(.el-sub-menu__title) {
  color: rgba(15, 23, 42, 0.8);
}

.app-menu :deep(.el-menu-item.is-active) {
  color: var(--app-primary);
  background: rgba(37, 99, 235, 0.08);
}

.el-header {
  background: rgba(255, 255, 255, 0.85);
  border-bottom: 1px solid var(--app-border);
  backdrop-filter: saturate(180%) blur(10px);
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.collapse-btn {
  font-size: 18px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--app-text);
}

.collapse-btn:hover {
  color: var(--app-primary);
}

.user-name {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  font-size: 14px;
}

.app-main {
  background: var(--app-bg);
  padding: 20px;
}

.page-shell {
  margin: 0 auto;
  transition: max-width 0.25s ease;
}
</style>
