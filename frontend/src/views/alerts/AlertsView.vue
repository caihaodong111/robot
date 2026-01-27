<template>
  <div class="bi-viewport">
    <!-- Header Section -->
    <header class="bi-header">
      <div class="title-area">
        <h1>可视化分析 <small>Visual Analytics</small></h1>
        <p class="subtitle">基于机器人数据的交互式可视化分析平台</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" circle @click="handleLoad" :disabled="!activeName" class="refresh-btn"></el-button>
        <el-button type="primary" class="gradient-btn" :disabled="!activeName" @click="handleLoad">
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
            placeholder="请选择机器人"
            filterable
            clearable
            :disabled="!selectedGroup"
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
      <el-card v-else class="bi-card styled-card">
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
            class="bi-frame"
            :src="biUrl"
            title="BI 可视化"
            @load="handleFrameLoad"
          ></iframe>
        </div>
      </el-card>
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

// 车间变化时加载该车间所有机器人
const handleGroupChange = async () => {
  selectedRobot.value = ''
  robots.value = []
  activeName.value = ''
  currentRobotLabel.value = ''
  isLoading.value = false

  if (!selectedGroup.value) return

  // 自动加载该车间的所有机器人
  await loadRobots()
}

// 加载车间的所有机器人
const loadRobots = async () => {
  if (!selectedGroup.value) return

  robotsLoading.value = true
  try {
    const response = await request.get('/robots/components/bi_robots/', {
      params: {
        group: selectedGroup.value
      }
    })
    robots.value = response.results || []
  } catch (error) {
    console.error('加载机器人列表失败:', error)
    robots.value = []
  } finally {
    robotsLoading.value = false
  }
}

// 机器人选择变化
const handleRobotChange = (value) => {
  if (!value) {
    activeName.value = ''
    currentRobotLabel.value = ''
    isLoading.value = false
    return
  }
  const robot = robots.value.find(r => r.value === value)
  if (robot) {
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
    await loadRobots()

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
})
</script>

<style scoped>
.bi-viewport {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  background-color: #f8fafc;
  min-height: calc(100vh - 100px);
  color: #1e293b;
}

/* Header - 参考Dashboard样式 */
.bi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bi-header h1 {
  font-size: 28px;
  font-weight: 800;
  margin: 0;
  background: linear-gradient(135deg, #1e293b 0%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.bi-header h1 small {
  font-size: 14px;
  color: #64748b;
  font-weight: 400;
  margin-left: 8px;
  -webkit-text-fill-color: #64748b;
}

.subtitle {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 14px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.gradient-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

/* 玻璃态控制面板 */
.control-panel {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
}

.glass-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 20px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
}

.control-row {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 200px;
  flex: 1;
}

.control-item label {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 4px;
}

.styled-select {
  width: 100%;
}

.styled-select :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  background: #fff;
}

.styled-select :deep(.el-input__wrapper:hover) {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.styled-select :deep(.el-input__wrapper.is-focus) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 当前选择信息 */
.current-selection-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.1) 100%);
  border-radius: 14px;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.selection-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
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
  color: #64748b;
}

.selection-value {
  font-size: 14px;
  font-weight: 600;
  color: #3b82f6;
}

/* 内容区域 */
.bi-content {
  min-height: 560px;
}

/* 空状态 */
.bi-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 560px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  border-radius: 20px;
  border: 2px dashed #cbd5e1;
}

.empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.1) 100%);
  color: #3b82f6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
}

.empty-text {
  font-size: 15px;
  color: #64748b;
}

/* BI卡片 */
.styled-card {
  border-radius: 20px;
  border: none;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
}

.bi-frame-wrapper {
  position: relative;
  width: 100%;
  height: 720px;
  border-radius: 16px;
  overflow: hidden;
}

.bi-frame {
  width: 100%;
  height: 100%;
  border: none;
  background: #fff;
}

/* ============ 加载遮罩层 ============ */
.bi-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  backdrop-filter: blur(4px);
}

.bi-loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

/* 旋转Spinner */
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
  stroke: #3b82f6;
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

/* 加载文字 */
.loading-message {
  text-align: center;
}

.loading-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 6px;
}

.loading-tip {
  font-size: 13px;
  color: #64748b;
}

/* 进度条 */
.bi-progress-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(64, 158, 255, 0.1);
  overflow: hidden;
  z-index: 11;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #409eff 0%, #66b1ff 50%, #409eff 100%);
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

/* 过渡动画 */
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
