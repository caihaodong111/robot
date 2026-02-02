<template>
  <div class="layout-container">
    <div class="hover-trigger" @mouseenter="handleMouseEnter" @mouseleave="handleMouseLeave"></div>

    <transition name="slide-fade">
      <aside v-show="isSidebarVisible" class="app-sidebar" @mouseenter="handleMouseEnter" @mouseleave="handleMouseLeave">
        <div class="sidebar-content">
          <div class="logo">
            <div class="logo-icon-wrapper">
              <el-icon :size="24"><Cpu /></el-icon>
            </div>
            <span>RobotOps <small>AIGC</small></span>
          </div>

          <nav class="sidebar-nav">
            <router-link to="/" class="nav-item" :class="{ active: route.path === '/' }">
              <div class="active-indicator"></div>
              <el-icon><Odometer /></el-icon>
              <span>机器人概览</span>
            </router-link>

            <router-link to="/devices" class="nav-item" :class="{ active: route.path === '/devices' }">
              <div class="active-indicator"></div>
              <el-icon><Cpu /></el-icon>
              <span>机器人状态</span>
            </router-link>

            <router-link to="/monitoring" class="nav-item" :class="{ active: route.path === '/monitoring' }">
              <div class="active-indicator"></div>
              <el-icon><TrendCharts /></el-icon>
              <span>关键轨迹检查</span>
            </router-link>

            <router-link to="/alerts" class="nav-item" :class="{ active: route.path === '/alerts' }">
              <div class="active-indicator"></div>
              <el-icon><Bell /></el-icon>
              <span>可视化BI</span>
            </router-link>

            <div class="nav-divider"></div>

            <router-link to="/portal" class="nav-item portal-link" :class="{ active: route.path === '/portal' }">
              <div class="active-indicator"></div>
              <el-icon><Grid /></el-icon>
              <span>应用门户</span>
            </router-link>
          </nav>

          <div class="sidebar-footer">
            <div class="version-tag">VER 2.0.4</div>
          </div>
        </div>
      </aside>
    </transition>

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
  }, 200)
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  display: flex;
  background: #030508; /* 与主界面背景色对齐 */
}

/* === 触发条：模拟激光线条 === */
.hover-trigger {
  position: fixed;
  left: 0;
  top: 0;
  width: 12px;
  height: 100%;
  z-index: 1100;
  cursor: pointer;
}

.hover-trigger::after {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 2px;
  height: 100%;
  background: linear-gradient(to bottom, transparent, rgba(0, 195, 255, 0.4), transparent);
  opacity: 0.5;
}

/* === 侧边栏：深空玻璃材质 === */
.app-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  width: 240px;
  height: 100%;
  background: rgba(10, 15, 25, 0.85); /* 提升通透感 */
  backdrop-filter: blur(40px); /* 强化模糊效果 */
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 20px 0 50px rgba(0, 0, 0, 0.8);
  z-index: 1050;
}

/* 侧栏顶部的流光线条 */
.app-sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  right: -1px;
  width: 2px;
  height: 100%;
  background: linear-gradient(180deg, transparent, #00c3ff 50%, transparent);
  box-shadow: 0 0 15px rgba(0, 195, 255, 0.6);
}

.sidebar-content {
  padding: 30px 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* === Logo 样式优化 === */
.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 24px 30px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.logo-icon-wrapper {
  color: #00c3ff;
  filter: drop-shadow(0 0 10px rgba(0, 195, 255, 0.6));
}

.logo span {
  font-size: 18px;
  font-weight: 900;
  letter-spacing: 1px;
  background: linear-gradient(180deg, #fff 0%, #a0a0a0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.logo small {
  font-size: 10px;
  color: #00c3ff;
  margin-left: 4px;
}

/* === 导航项交互逻辑 === */
.sidebar-nav {
  flex: 1;
  padding: 20px 14px;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  margin: 6px 0;
  border-radius: 4px;
  color: #a0aec0; /* 调亮默认字体颜色 */
  text-decoration: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 14px;
  overflow: hidden;
}

/* 激活态指示条 */
.active-indicator {
  position: absolute;
  left: 0;
  top: 0;
  width: 0;
  height: 100%;
  background: linear-gradient(90deg, rgba(0, 195, 255, 0.2), transparent);
  transition: width 0.3s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.03);
  color: #fff;
  padding-left: 24px; /* 轻微向右偏移 */
}

.nav-item.active {
  color: #00c3ff;
  background: rgba(0, 195, 255, 0.06);
  text-shadow: 0 0 10px rgba(0, 195, 255, 0.3);
}

.nav-item.active .active-indicator {
  width: 100%;
}

.nav-item .el-icon {
  font-size: 20px;
  transition: transform 0.3s ease;
}

.nav-item:hover .el-icon {
  transform: scale(1.1);
  color: #00c3ff;
}

.nav-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
  margin: 15px 0;
}

.sidebar-footer {
  padding: 20px;
  text-align: center;
}

.version-tag {
  font-size: 10px;
  color: #444;
  letter-spacing: 2px;
}

/* === 主内容区 === */
.app-main {
  flex: 1;
  background: #000;
  min-width: 0;
}

/* === 过渡动画 === */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}
</style>
