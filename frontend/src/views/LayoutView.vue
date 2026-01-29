<template>
  <div class="layout-container">
    <!-- 左侧触发条 -->
    <div class="hover-trigger" @mouseenter="handleMouseEnter" @mouseleave="handleMouseLeave"></div>

    <!-- 隐藏式侧边栏 -->
    <transition name="slide-fade">
      <aside v-show="isSidebarVisible" class="app-sidebar" @mouseenter="handleMouseEnter" @mouseleave="handleMouseLeave">
        <div class="sidebar-content">
          <div class="logo">
            <el-icon :size="24"><Cpu /></el-icon>
            <span>RobotOps</span>
          </div>
          <nav class="sidebar-nav">
            <router-link to="/" class="nav-item" :class="{ active: route.path === '/' }">
              <el-icon><Odometer /></el-icon>
              <span>平台概览</span>
            </router-link>
            <router-link to="/devices" class="nav-item" :class="{ active: route.path === '/devices' }">
              <el-icon><Cpu /></el-icon>
              <span>机器人状态</span>
            </router-link>
            <router-link to="/monitoring" class="nav-item" :class="{ active: route.path === '/monitoring' }">
              <el-icon><TrendCharts /></el-icon>
              <span>关键轨迹检查</span>
            </router-link>
            <router-link to="/alerts" class="nav-item" :class="{ active: route.path === '/alerts' }">
              <el-icon><Bell /></el-icon>
              <span>可视化BI</span>
            </router-link>
            <router-link to="/portal" class="nav-item" :class="{ active: route.path === '/portal' }">
              <el-icon><Grid /></el-icon>
              <span>应用门户</span>
            </router-link>
          </nav>
        </div>
      </aside>
    </transition>

    <!-- 主内容区 -->
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, RouterView } from 'vue-router'
import {
  Odometer, Cpu, TrendCharts, Bell, Grid
} from '@element-plus/icons-vue'

const route = useRoute()

const isSidebarVisible = ref(false)
let hoverTimer = null

const handleMouseEnter = () => {
  if (hoverTimer) clearTimeout(hoverTimer)
  hoverTimer = setTimeout(() => {
    isSidebarVisible.value = true
  }, 100)
}

const handleMouseLeave = () => {
  if (hoverTimer) clearTimeout(hoverTimer)
  hoverTimer = setTimeout(() => {
    isSidebarVisible.value = false
  }, 100)
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  display: flex;
  background: #000;
}

/* === 触发条 === */
.hover-trigger {
  position: fixed;
  left: 0;
  top: 0;
  width: 8px;
  height: 100%;
  z-index: 999;
  cursor: pointer;
}

.hover-trigger::after {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 60px;
  background: linear-gradient(180deg,
    transparent,
    rgba(0, 204, 255, 0.3) 50%,
    transparent
  );
  border-radius: 0 2px 2px 0;
  transition: all 0.3s ease;
}

.hover-trigger:hover::after {
  background: linear-gradient(180deg,
    transparent,
    rgba(0, 204, 255, 0.6) 50%,
    transparent
  );
  box-shadow: 0 0 12px rgba(0, 204, 255, 0.4);
}

/* === 侧边栏 === */
.app-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  width: 220px;
  height: 100%;
  background: rgba(0, 0, 0, 0.95);
  backdrop-filter: blur(30px);
  border-right: 1px solid rgba(0, 204, 255, 0.2);
  box-shadow:
    4px 0 24px rgba(0, 0, 0, 0.6),
    inset -1px 0 0 rgba(0, 204, 255, 0.1);
  z-index: 1000;
}

/* 侧边栏发光边框 */
.app-sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(180deg,
    transparent,
    rgba(0, 204, 255, 0.5) 30%,
    rgba(0, 204, 255, 0.7) 50%,
    rgba(0, 204, 255, 0.5) 70%,
    transparent
  );
}

/* === 侧边栏内容 === */
.sidebar-content {
  padding: 20px 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* Logo */
.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 16px 20px;
  border-bottom: 1px solid rgba(0, 204, 255, 0.1);
  margin-bottom: 12px;
}

.logo .el-icon {
  color: #0066ff;
  filter: drop-shadow(0 0 10px rgba(0, 102, 255, 0.6));
}

.logo span {
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 1px;
  background: linear-gradient(180deg, #fff 30%, #888 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 导航 */
.sidebar-nav {
  flex: 1;
  padding: 0 12px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin: 4px 0;
  border-radius: 10px;
  color: #888;
  text-decoration: none;
  transition: all 0.3s ease;
  font-size: 14px;
}

.nav-item:hover {
  color: #00ccff;
  background: rgba(0, 204, 255, 0.08);
}

.nav-item.active {
  color: #00ccff;
  background: rgba(0, 204, 255, 0.12);
  border: 1px solid rgba(0, 204, 255, 0.25);
  box-shadow:
    0 0 20px rgba(0, 204, 255, 0.15),
    inset 0 0 20px rgba(0, 204, 255, 0.05);
}

.nav-item .el-icon {
  font-size: 18px;
  color: #666;
  transition: all 0.3s ease;
}

.nav-item:hover .el-icon,
.nav-item.active .el-icon {
  color: #00ccff;
  filter: drop-shadow(0 0 8px rgba(0, 204, 255, 0.5));
}

/* 滚动条 */
.sidebar-nav::-webkit-scrollbar {
  width: 4px;
}

.sidebar-nav::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-nav::-webkit-scrollbar-thumb {
  background: rgba(0, 204, 255, 0.3);
  border-radius: 2px;
}

/* === 主内容区 === */
.app-main {
  flex: 1;
  min-height: 100vh;
  background: #000;
}

/* === 过渡动画 === */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}
</style>
