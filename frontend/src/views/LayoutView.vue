<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="app-aside">
      <div class="logo">
        <el-icon :size="30"><Cpu /></el-icon>
        <span>机器人技术管理平台</span>
      </div>
      <el-menu
        class="app-menu"
        :default-active="activeMenu"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>平台概览</span>
        </el-menu-item>
        <el-menu-item index="/devices">
          <el-icon><Cpu /></el-icon>
          <span>机器人状态</span>
        </el-menu-item>
        <el-menu-item index="/monitoring">
          <el-icon><TrendCharts /></el-icon>
          <span>关键轨迹检查</span>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><Bell /></el-icon>
          <span>可视化BI</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部导航 -->
      <el-header>
        <div class="header-content">
          <div class="breadcrumb">
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
  Odometer, Cpu, TrendCharts, Bell, User, SwitchButton
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

const currentPageName = computed(() => {
  const names = {
    '/dashboard': '平台概览',
    '/devices': '机器人状态',
    '/monitoring': '关键轨迹检查',
    '/alerts': '可视化BI'
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
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  color: var(--app-text);
  gap: 10px;
  border-bottom: 1px solid var(--app-border);
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
  max-width: 1200px;
  margin: 0 auto;
}
</style>
