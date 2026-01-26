<template>
  <div class="bi-shell">
    <el-card class="bi-card">
      <template #header>
        <div class="bi-header">
          <div class="bi-title">
            <span class="title-text">可视化 BI</span>
            <span class="title-sub">选择车间和机器人后加载可视化界面</span>
          </div>
        </div>
      </template>

      <div class="bi-controls">
        <!-- 车间选择 -->
        <el-select
          v-model="selectedGroup"
          placeholder="选择车间"
          clearable
          style="width: 180px"
          @change="handleGroupChange"
        >
          <el-option
            v-for="group in groups"
            :key="group.key"
            :label="group.name"
            :value="group.key"
          />
        </el-select>

        <!-- 机器人搜索选择 -->
        <el-select
          v-model="selectedRobot"
          placeholder="搜索并选择机器人"
          filterable
          remote
          reserve-keyword
          clearable
          :remote-method="searchRobots"
          :loading="robotsLoading"
          :disabled="!selectedGroup"
          style="width: 320px"
          @change="handleRobotChange"
        >
          <el-option
            v-for="robot in robots"
            :key="robot.value"
            :label="robot.label"
            :value="robot.value"
          />
        </el-select>

        <el-button type="primary" :disabled="!activeName" @click="handleLoad">
          加载
        </el-button>
        <el-button :disabled="!activeName" @click="handleOpenNew">
          新窗口打开
        </el-button>

        <!-- 显示当前选择 -->
        <div v-if="activeName" class="current-selection">
          当前：{{ currentRobotLabel }}
        </div>
      </div>

      <div class="bi-content">
        <div v-if="!activeName" class="bi-empty">
          请选择车间和机器人后加载 BI 可视化界面
        </div>

        <!-- BI图表容器 -->
        <div v-else class="bi-frame-wrapper">
          <!-- 加载遮罩层 -->
          <Transition name="fade">
            <div v-if="isLoading" class="bi-loading-overlay">
              <div class="bi-loading-content">
                <!-- 脉冲圆点动画 -->
                <div class="pulse-dots">
                  <span class="pulse-dot"></span>
                  <span class="pulse-dot"></span>
                  <span class="pulse-dot"></span>
                </div>
                <!-- 加载文字 -->
                <div class="loading-text">
                  <span class="text-main">正在加载数据</span>
                  <span class="text-dots"></span>
                </div>
                <!-- 机器人名称 -->
                <div v-if="currentRobotLabel" class="loading-robot">
                  {{ currentRobotLabel }}
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
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
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

// 车间变化时重置机器人选择
const handleGroupChange = () => {
  selectedRobot.value = ''
  robots.value = []
  activeName.value = ''
  currentRobotLabel.value = ''
  isLoading.value = false
}

// 搜索机器人
const searchRobots = async (query) => {
  if (!query || !selectedGroup.value) {
    robots.value = []
    return
  }

  robotsLoading.value = true
  try {
    const response = await request.get('/robots/components/bi_robots/', {
      params: {
        group: selectedGroup.value,
        keyword: query
      }
    })
    robots.value = response.results || []
  } catch (error) {
    console.error('搜索机器人失败:', error)
    robots.value = []
  } finally {
    robotsLoading.value = false
  }
}

// 直接根据part_no获取机器人信息（用于从URL参数初始化）
const getRobotByPartNo = async (group, partNo) => {
  try {
    const response = await request.get('/robots/components/bi_robots/', {
      params: {
        group: group,
        keyword: partNo
      }
    })
    const results = response.results || []
    const robot = results.find(r => r.value === partNo)
    return robot
  } catch (error) {
    console.error('获取机器人信息失败:', error)
    return null
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

const handleOpenNew = () => {
  if (!activeName.value) return
  window.open(`/api/robots/bi/?table=${encodeURIComponent(activeName.value)}`, '_blank')
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

    // 获取该机器人信息并设置
    const robot = await getRobotByPartNo(queryGroup, queryRobot)
    if (robot) {
      selectedRobot.value = robot.value
      activeName.value = robot.value
      currentRobotLabel.value = robot.label
      // 也加入到搜索结果中，以便显示
      robots.value = [robot]
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
.bi-shell {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.bi-card :deep(.el-card__header) {
  padding: 14px 18px;
}

.bi-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.bi-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-text {
  font-size: 16px;
  font-weight: 700;
  color: rgba(15, 23, 42, 0.9);
}

.title-sub {
  font-size: 12px;
  color: rgba(15, 23, 42, 0.6);
}

.bi-controls {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.current-selection {
  padding: 6px 12px;
  background: rgba(64, 158, 255, 0.1);
  color: #409eff;
  border-radius: 4px;
  font-size: 13px;
}

.bi-content {
  min-height: 560px;
  border: 1px dashed rgba(148, 163, 184, 0.5);
  border-radius: 12px;
  background: rgba(148, 163, 184, 0.06);
  overflow: hidden;
}

.bi-empty {
  height: 560px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(15, 23, 42, 0.55);
  font-size: 14px;
}

.bi-frame-wrapper {
  position: relative;
  width: 100%;
  height: 720px;
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
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.98) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  backdrop-filter: blur(8px);
}

.bi-loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

/* 脉冲圆点动画 */
.pulse-dots {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pulse-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  animation: pulse 1.4s ease-in-out infinite;
  box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.4);
}

.pulse-dot:nth-child(1) {
  animation-delay: 0s;
}

.pulse-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.pulse-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
    box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.4);
  }
  50% {
    transform: scale(1.2);
    opacity: 1;
    box-shadow: 0 0 20px 8px rgba(64, 158, 255, 0);
  }
}

/* 加载文字 */
.loading-text {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 15px;
  font-weight: 500;
  color: rgba(15, 23, 42, 0.75);
  letter-spacing: 0.5px;
}

.text-dots {
  display: flex;
  gap: 2px;
}

.text-dots::before,
.text-dots::after {
  content: '';
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #409eff;
  animation: bounce 1.4s ease-in-out infinite;
}

.text-dots::before {
  animation-delay: 0.2s;
}

.text-dots::after {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  50% {
    transform: translateY(-6px);
    opacity: 1;
  }
}

/* 机器人名称 */
.loading-robot {
  font-size: 13px;
  color: rgba(15, 23, 42, 0.5);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  padding: 6px 14px;
  background: rgba(64, 158, 255, 0.08);
  border-radius: 6px;
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
