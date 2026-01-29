<template>
  <div class="bi-viewport">
    <!-- 背景流光特效 -->
    <div class="space-ambient">
      <div class="nebula blue"></div>
      <div class="nebula gold"></div>
      <div class="scan-grid"></div>
    </div>

    <div class="layout-wrapper">
      <!-- Header Section -->
      <header class="page-header">
        <div class="title-area">
          <h1 class="metallic-title">可视化BI <span>VISUAL ANALYTICS</span></h1>
        </div>
        <div class="header-actions">
          <el-button :icon="Refresh" circle @click="handleLoad" :disabled="!activeName" class="refresh-btn"></el-button>
          <el-button type="primary" class="action-btn" :disabled="!activeName" @click="handleLoad">
            <el-icon v-if="!isLoading"><Search /></el-icon>
            {{ isLoading ? '加载中...' : '加载分析' }}
          </el-button>
        </div>
      </header>

      <!-- Control Panel -->
      <div class="control-panel glass-card">
        <div class="control-row">
          <!-- 车间选择 -->
          <div class="control-item">
            <label><el-icon><Location /></el-icon> 目标车间</label>
            <el-select
              v-model="selectedGroup"
              placeholder="请选择车间"
              clearable
              @change="handleGroupChange"
              class="styled-select"
            >
              <el-option
                v-for="group in groups"
                :key="group.key"
                :label="group.name"
                :value="group.key"
              />
            </el-select>
          </div>

          <!-- 机器人选择 -->
          <div class="control-item">
            <label><el-icon><Monitor /></el-icon> 机器人</label>
            <el-select
              v-model="selectedRobot"
              placeholder="请输入机器人名称搜索"
              filterable
              clearable
              remote
              reserve-keyword
              :remote-method="searchRobots"
              :loading="robotsLoading"
              @change="handleRobotChange"
              class="styled-select"
            >
              <el-option
                v-for="robot in robots"
                :key="robot.value"
                :label="robot.label"
                :value="robot.value"
              />
            </el-select>
          </div>

          <!-- 当前选择显示 -->
          <div v-if="activeName" class="current-selection-info">
            <div class="selection-icon"><el-icon><DataAnalysis /></el-icon></div>
            <div class="selection-text">
              <span class="selection-label">当前分析</span>
              <span class="selection-value">{{ currentRobotLabel }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Content Area -->
      <div class="bi-content">
        <div v-if="!activeName" class="bi-empty-state">
          <div class="empty-icon"><el-icon><PieChart /></el-icon></div>
          <div class="empty-text">请选择车间和机器人后加载 BI 可视化界面</div>
        </div>

        <!-- BI图表容器 -->
        <div v-else class="bi-card glass-card">
          <div class="bi-frame-wrapper">
            <!-- 加载遮罩层 -->
            <Transition name="fade">
              <div v-if="isLoading" class="bi-loading-overlay">
                <div class="bi-loading-content">
                  <!-- 加载动画 -->
                  <div class="loading-spinner">
                    <svg class="spinner" viewBox="0 0 50 50">
                      <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="4"></circle>
                    </svg>
                  </div>
                  <!-- 加载文字 -->
                  <div class="loading-message">
                    <div class="loading-title">正在加载数据</div>
                    <div class="loading-tip">请保持当前界面，数据加载中...</div>
                  </div>
                </div>
              </div>
            </Transition>

            <!-- 加载进度条 -->
            <Transition name="slide-down">
              <div v-if="isLoading" class="bi-progress-bar">
                <div class="progress-fill"></div>
              </div>
            </Transition>

            <iframe
              ref="biFrame"
              class="bi-frame"
              :src="biUrl"
              title="BI 可视化"
              @load="handleFrameLoad"
            ></iframe>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Refresh, Location, Monitor, Search, DataAnalysis, PieChart } from '@element-plus/icons-vue'
import request from '@/utils/request'

const route = useRoute()

const selectedGroup = ref('')
const selectedRobot = ref('')
const activeName = ref('')
const currentRobotLabel = ref('')

const groups = ref([])
const robots = ref([])
const robotsLoading = ref(false)
const isLoading = ref(false)
const biFrame = ref(null)

const biUrl = computed(() => {
  const name = activeName.value.trim()
  return name ? `/api/robots/bi/?table=${encodeURIComponent(name)}&embed=1` : ''
})

// 加载车间列表
const loadGroups = async () => {
  try {
    const response = await request.get('/robots/groups/')
    groups.value = response
  } catch (error) {
    console.error('加载车间列表失败:', error)
  }
}

// 车间变化时重新搜索机器人
const handleGroupChange = async () => {
  selectedRobot.value = ''
  activeName.value = ''
  currentRobotLabel.value = ''
  isLoading.value = false

  // 重新搜索机器人
  await searchRobots('')
}

// 远程搜索机器人
const searchRobots = async (query) => {
  robotsLoading.value = true
  try {
    const params = {}
    if (query) {
      params.keyword = query
    }
    if (selectedGroup.value) {
      params.group = selectedGroup.value
    }

    const response = await request.get('/robots/components/bi_robots/', { params })
    let results = response.results || []

    // 处理机器人名称，只保留括号前的内容
    robots.value = results.map(robot => {
      // 提取括号前的机器人名称
      let cleanLabel = robot.label
      if (cleanLabel.includes('(')) {
        cleanLabel = cleanLabel.split('(')[0].trim()
      }

      return {
        ...robot,
        label: cleanLabel
      }
    })

    // 如果有搜索关键词，在前端进一步过滤确保结果包含关键词
    if (query) {
      const lowerQuery = query.toLowerCase()
      robots.value = robots.value.filter(robot =>
        robot.label.toLowerCase().includes(lowerQuery)
      )
    }
  } catch (error) {
    console.error('搜索机器人失败:', error)
    robots.value = []
  } finally {
    robotsLoading.value = false
  }
}

// 机器人选择变化，自动设置对应车间并加载
const handleRobotChange = (value) => {
  if (!value) {
    activeName.value = ''
    currentRobotLabel.value = ''
    isLoading.value = false
    return
  }

  const robot = robots.value.find(r => r.value === value)
  if (robot) {
    // 如果机器人有group_key信息且与当前选中车间不同，自动设置车间
    if (robot.group_key && robot.group_key !== selectedGroup.value) {
      selectedGroup.value = robot.group_key
    }

    activeName.value = value
    currentRobotLabel.value = robot.label
    // 自动开始加载
    startLoading()
  }
}

// 开始加载动画
const startLoading = () => {
  isLoading.value = true
}

// iframe加载完成
const handleFrameLoad = () => {
  // 延迟一点关闭加载动画，确保内容已渲染
  setTimeout(() => {
    isLoading.value = false
  }, 500)
}

const handleLoad = () => {
  if (!activeName.value) return
  startLoading()
}

// 监听activeName变化，自动开始加载
watch(activeName, (newVal) => {
  if (newVal) {
    startLoading()
  }
})

// 初始化：检查URL参数
const initFromQuery = async () => {
  const queryGroup = route.query.group
  const queryRobot = route.query.robot

  if (queryGroup && queryRobot) {
    // 先设置车间
    selectedGroup.value = queryGroup

    // 加载该车间的所有机器人
    await searchRobots('')

    // 找到并设置选中的机器人
    const robot = robots.value.find(r => r.value === queryRobot)
    if (robot) {
      selectedRobot.value = robot.value
      activeName.value = robot.value
      currentRobotLabel.value = robot.label
    }
  }
}

onMounted(async () => {
  await loadGroups()
  // 等待groups加载后再初始化query参数
  await initFromQuery()

  // 监听来自iframe的postMessage（用于日期范围更新）
  window.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'updateBIUrl') {
      // 更新iframe的src来重新加载图表
      if (biFrame.value) {
        biFrame.value.src = event.data.url
      }
    }
  })
})
</script>

<style scoped>
/* === 基础布局与背景 === */
.bi-viewport {
  background: radial-gradient(circle at 50% 35%, #0d1a2d 0%, #030508 100%);
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  color: #fff;
}

/* === 背景流光元素 === */
.space-ambient {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.nebula {
  position: absolute;
  filter: blur(120px);
  opacity: 0.28;
  mix-blend-mode: screen;
}

.nebula.blue {
  width: 80vw;
  height: 70vh;
  background: radial-gradient(circle, #0066ff, transparent 75%);
  top: -10%;
  left: -5%;
}

.nebula.gold {
  width: 80vw;
  height: 70vh;
  background: radial-gradient(circle, #ffaa00, transparent 75%);
  bottom: -10%;
  right: -5%;
}

.scan-grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 50px 50px;
}

.layout-wrapper {
  position: relative;
  z-index: 1;
  padding: 40px;
  max-width: 1600px;
  margin: 0 auto;
}

/* === Header === */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.title-area {
  display: flex;
  flex-direction: column;
}

.metallic-title {
  font-size: 36px;
  font-weight: 900;
  letter-spacing: 5px;
  background: linear-gradient(180deg, #ffffff 30%, #a0a0a0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 40px rgba(0, 195, 255, 0.5);
  margin: 0 0 8px 0;
}

.metallic-title span {
  font-size: 14px;
  color: #636e72;
  margin-left: 15px;
  letter-spacing: 2px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.action-btn {
  background: linear-gradient(135deg, #00c3ff 0%, #0080ff 100%);
  border: none;
  box-shadow: 0 4px 14px rgba(0, 195, 255, 0.3);
}

.action-btn:hover {
  box-shadow: 0 6px 20px rgba(0, 195, 255, 0.5);
}

.refresh-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #8899aa;
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  background: #00c3ff;
  border-color: #00c3ff;
  color: #fff;
}

/* === Glass Card === */
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(40px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 4px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  transition: all 0.4s ease;
}

/* === 控制面板 === */
.control-panel {
  padding: 20px;
  margin-bottom: 20px;
}

.control-row {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 280px;
  flex: 1;
}

.control-item label {
  font-size: 12px;
  font-weight: 600;
  color: #8899aa;
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
  min-width: 80px;
}

.styled-select {
  flex: 1;
  min-width: 180px;
}

.styled-select :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.03);
}

.styled-select :deep(.el-input__wrapper:hover) {
  border-color: rgba(0, 195, 255, 0.3);
}

.styled-select :deep(.el-input__wrapper.is-focus) {
  border-color: #00c3ff;
  box-shadow: 0 0 0 3px rgba(0, 195, 255, 0.1);
}

.styled-select :deep(.el-input__inner) {
  color: #fff;
}

.styled-select :deep(.el-input__inner::placeholder) {
  color: #6a7a8a;
}

/* === 当前选择信息 === */
.current-selection-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  background: rgba(0, 195, 255, 0.1);
  border-radius: 14px;
  border: 1px solid rgba(0, 195, 255, 0.3);
}

.selection-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: rgba(0, 195, 255, 0.15);
  color: #00c3ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.selection-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.selection-label {
  font-size: 12px;
  color: #8899aa;
}

.selection-value {
  font-size: 14px;
  font-weight: 600;
  color: #00c3ff;
}

/* === 内容区域 === */
.bi-content {
  min-height: 560px;
}

/* === 空状态 === */
.bi-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 560px;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(40px);
  border-radius: 4px;
  border: 2px dashed rgba(255, 255, 255, 0.1);
}

.empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: rgba(0, 195, 255, 0.1);
  color: #00c3ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
}

.empty-text {
  font-size: 15px;
  color: #8899aa;
}

/* === BI卡片 === */
.bi-card {
  border-radius: 4px;
  border: none;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  padding: 0;
  overflow: hidden;
}

.bi-frame-wrapper {
  position: relative;
  width: 100%;
  height: 720px;
  border-radius: 4px;
  overflow: hidden;
  background: #000;
}

.bi-frame {
  width: 100%;
  height: 100%;
  border: none;
  background: #000;
}

/* === 加载遮罩层 === */
.bi-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(10, 15, 25, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  backdrop-filter: blur(20px);
}

.bi-loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

/* === 旋转Spinner === */
.loading-spinner {
  width: 48px;
  height: 48px;
}

.spinner {
  width: 100%;
  height: 100%;
  animation: rotate 1.5s linear infinite;
}

.spinner .path {
  stroke: #00c3ff;
  stroke-linecap: round;
  animation: dash 1.5s ease-in-out infinite;
}

@keyframes rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}

/* === 加载文字 === */
.loading-message {
  text-align: center;
}

.loading-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 6px;
}

.loading-tip {
  font-size: 13px;
  color: #8899aa;
}

/* === 进度条 === */
.bi-progress-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(0, 195, 255, 0.1);
  overflow: hidden;
  z-index: 11;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #00c3ff 0%, #00ffcc 50%, #00c3ff 100%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  width: 60%;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* === 过渡动画 === */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-100%);
}
</style>

<!-- 全局样式：下拉菜单深色主题 -->
<style>
/* Select Dropdown - 玻璃质感 */
.el-select-dropdown {
  background: rgba(10, 10, 15, 0.85) !important;
  backdrop-filter: blur(30px) !important;
  border: 1px solid rgba(0, 204, 255, 0.2) !important;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5) !important;
}

.el-select-dropdown__item {
  color: #aaa !important;
  background: transparent !important;
}

.el-select-dropdown__item.hover,
.el-select-dropdown__item:hover {
  background: rgba(0, 204, 255, 0.15) !important;
  color: #00ccff !important;
}

.el-select-dropdown__item.is-selected {
  color: #00ccff !important;
  background: rgba(0, 204, 255, 0.2) !important;
  font-weight: 600;
}

.el-select-dropdown__item.is-disabled {
  color: #666 !important;
}

.el-select-dropdown__empty-panel {
  color: #666 !important;
}

.el-select-dropdown__wrap {
  background: transparent !important;
}

.el-select-dropdown__list {
  background: transparent !important;
}

.el-popper.is-light .el-popper__arrow::before {
  background: rgba(10, 10, 15, 0.85) !important;
  border: 1px solid rgba(0, 204, 255, 0.2) !important;
}

.el-popper .el-popper__arrow::before {
  background: rgba(10, 10, 15, 0.85) !important;
  border: 1px solid rgba(0, 204, 255, 0.2) !important;
}
</style>
