<template>
  <div class="robot-status-viewport">
    <!-- 背景流光特效 -->
    <div class="ambient-background">
      <div class="nebula blue"></div>
      <div class="nebula gold"></div>
      <div class="breathing-line gold-1"></div>
      <div class="breathing-line gold-2"></div>
      <div class="scan-grid"></div>
    </div>

    <div class="layout-wrapper">
      <!-- Header Section -->
      <header class="page-header entrance-slide-in">
        <div class="title-area">
          <h1 class="ios-title">机器人状态 <small>ROBOT STATUS</small></h1>
        </div>
        <div class="header-actions">
          <el-button :icon="Refresh" @click="handleRefresh" class="ios-btn btn-entrance">同步数据</el-button>
        </div>
      </header>

      <!-- KPI Metrics Grid -->
      <div class="kpi-selector-container">
        <button
          type="button"
          class="kpi-card ios-glass active hero-card entrance-scale-up"
          @click="drawerVisible = true"
        >
          <div class="border-glow gold-tint entrance-border-glow"></div>
          <div class="active-glow"></div>
          <div class="kpi-icon-box kpi-icon-entrance">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="kpi-content">
            <div class="selector-label-row">
              <label>当前监控车间</label>
              <span class="tap-hint">点击切换 <el-icon><ArrowRight /></el-icon></span>
            </div>
            <div class="main-value">{{ activeGroupName }} <small>WORKSPACE</small></div>
            <div class="status-mini-tags">
              <span class="tag risk">高风险 {{ groupStats.highRisk }}</span>
              <span class="tag total">总数 {{ groupStats.total }}</span>
            </div>
          </div>
        </button>
      </div>

      <!-- Workshop Drawer -->
      <el-drawer
        v-model="drawerVisible"
        title="选择监控车间"
        direction="rtl"
        size="420px"
        class="dark-drawer-glass"
      >
        <div class="workshop-drawer-list">
          <div
            v-for="group in groups"
            :key="group.key"
            class="workshop-item"
            :class="{ active: group.key === selectedGroup }"
            @click="handleSelectGroup(group.key)"
          >
            <div class="ws-info-top">
              <span class="ws-name">{{ group.name }}</span>
              <div class="ws-badges">
                <span v-if="group.stats.highRisk > 0" class="badge-risk">{{ group.stats.highRisk }}</span>
                <span class="badge-total">总数 {{ group.total }}</span>
              </div>
            </div>
            <div class="ws-progress-track">
              <div
                class="ws-progress-fill"
                :class="{ 'is-danger': group.stats.highRisk > 0 }"
                :style="{ width: (group.stats.highRisk / (group.total || 1) * 100) + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </el-drawer>

      <!-- Data Table Section -->
      <section class="data-table-section ios-glass entrance-scale-up-delay-4">
        <div class="border-glow gold-tint entrance-border-glow"></div>
        <div class="table-header">
          <span class="accent-bar"></span>
          <span>{{ activeGroupName }} - 实时状态列表</span>
        </div>

        <!-- Tabs -->
        <el-tabs v-model="activeTab" class="status-tabs-dark">
          <el-tab-pane name="highRisk" label="高风险机器人列表" />
          <el-tab-pane name="all" label="所有机器人信息列表" />
          <el-tab-pane name="history" label="历史高风险机器人列表" />
        </el-tabs>

        <!-- Filters -->
        <div class="filters">
          <el-row :gutter="10" align="middle">
            <el-col :span="8">
              <el-input
                v-model="keyword"
                placeholder="搜索：部件编号 / 参考编号 / 类型 / 工艺 / 备注"
                clearable
                class="dark-input"
                @keyup.enter="handleSearch"
                @clear="handleSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-col>
            <el-col :span="3">
              <el-select v-model="levelFilter" placeholder="等级(level)" clearable class="dark-select">
                <el-option label="H" value="H" />
                <el-option label="M" value="M" />
                <el-option label="L" value="L" />
                <el-option label="T" value="T" />
                <el-option label="C" value="C" />
              </el-select>
            </el-col>
            <el-col :span="3">
              <el-select
                v-model="axisKeysFilter"
                placeholder="Axis(A1-A7)"
                multiple
                collapse-tags
                collapse-tags-tooltip
                clearable
                class="dark-select"
              >
                <el-option v-for="k in CHECK_KEYS" :key="k" :label="k" :value="k" />
              </el-select>
            </el-col>
            <el-col :span="3">
              <el-select
                v-model="axisStateFilter"
                placeholder="Axis状态"
                clearable
                :disabled="!axisKeysFilter.length"
                class="dark-select"
              >
                <el-option label="正常" value="ok" />
                <el-option label="异常" value="bad" />
              </el-select>
            </el-col>
            <el-col :span="3">
              <el-select v-model="markMode" placeholder="标记(mark)" clearable class="dark-select">
                <el-option label="0" value="zero" />
                <el-option label="非0" value="nonzero" />
              </el-select>
            </el-col>
            <el-col :span="4" class="filters-right">
              <el-button :icon="Close" @click="resetFilters">重置</el-button>
            </el-col>
          </el-row>
        </div>

        <!-- Table Legend -->
        <div class="table-legend">
          <span class="legend-item"><span class="dot dot-ok"></span>正常/符合要求</span>
          <span class="legend-item"><span class="dot dot-bad"></span>该项异常/待处理</span>
        </div>

        <!-- Table -->
        <el-table :data="pagedRows" class="premium-table table-entrance" stripe height="520" v-loading="loading">
          <el-table-column prop="partNo" label="部件编号(robot)" width="190" show-overflow-tooltip>
            <template #default="{ row }">
              <el-button type="primary" link class="mono robot-name-cell" @click="openBI(row)">
                {{ row.partNo }}
              </el-button>
            </template>
          </el-table-column>
          <el-table-column label="参考编号(reference)" width="170">
            <template #default="{ row }">
              <el-button type="primary" link class="mono" @click="openEdit(row, 'referenceNo')">
                {{ row.referenceNo }}
              </el-button>
            </template>
          </el-table-column>
          <el-table-column prop="number" label="Number" width="110" align="center">
            <template #default="{ row }">
              <span class="mono">{{ row.number ?? 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="typeSpec" label="类型(type)" min-width="170" show-overflow-tooltip />
          <el-table-column prop="tech" label="工艺(tech)" min-width="140" show-overflow-tooltip />
          <el-table-column prop="mark" label="标记(mark)" width="110" align="center">
            <template #default="{ row }">
              <el-button type="primary" link class="mono" @click="openEdit(row, 'mark')">
                {{ row.mark ?? 0 }}
              </el-button>
            </template>
          </el-table-column>
          <el-table-column label="备注(remark)" min-width="220" show-overflow-tooltip>
            <template #default="{ row }">
              <el-button type="primary" link class="remark-link" @click="openEdit(row, 'remark')">
                {{ row.remark || '-' }}
              </el-button>
            </template>
          </el-table-column>

          <el-table-column v-for="key in CHECK_KEYS" :key="key" :label="key" width="58" align="center">
            <template #default="{ row }">
              <el-tooltip
                :content="checkTooltip(row, key)"
                placement="top"
                :show-after="120"
              >
                <span class="dot" :class="row.checks?.[key]?.ok ? 'dot-ok' : 'dot-bad'"></span>
              </el-tooltip>
            </template>
          </el-table-column>

          <el-table-column label="等级(level)" width="110" align="center">
            <template #default="{ row }">
              <el-button type="primary" link @click="openEdit(row, 'level')">
                <el-tag :type="levelTagType(row.level)" effect="light">{{ row.level }}</el-tag>
              </el-button>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="110" fixed="right" align="center">
            <template #default="{ row }">
              <el-button type="primary" link @click="openDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- Pagination -->
        <div class="pagination-wrapper">
          <div class="pagination-info">
            <span class="pagination-total">共 {{ DEMO_MODE ? filteredRows.length : serverTotal }} 条</span>
            <el-select v-model="pageSize" class="pagination-size-select">
              <el-option :value="10" label="10 条/页" />
              <el-option :value="20" label="20 条/页" />
              <el-option :value="50" label="50 条/页" />
              <el-option :value="100" label="100 条/页" />
            </el-select>
          </div>

          <div class="pagination-controls">
            <button
              class="pagination-arrow"
              :disabled="currentPage === 1"
              @click="goToPage(Math.max(1, currentPage - 1))"
            >
              <el-icon><ArrowLeft /></el-icon>
            </button>

            <div class="pagination-pages">
              <button
                v-for="page in displayPages"
                :key="`page-${page}-${currentPage}`"
                class="pagination-page"
                :class="{ active: page === currentPage, ellipsis: page === '...' }"
                :disabled="page === '...'"
                @click="handlePageClick(page)"
              >
                {{ page }}
              </button>
            </div>

            <button
              class="pagination-arrow"
              :disabled="currentPage === totalPages"
              @click="goToPage(Math.min(totalPages, currentPage + 1))"
            >
              <el-icon><ArrowRight /></el-icon>
            </button>
          </div>

          <div class="pagination-jumper">
            <span>前往</span>
            <el-input-number
              v-model="jumpPage"
              :min="1"
              :max="totalPages"
              :controls="false"
              class="pagination-jump-input"
              @change="handleJump"
            />
            <span>页</span>
          </div>
        </div>
      </section>
    </div>

    <!-- Detail Dialog -->
    <el-dialog v-model="detailVisible" title="部件详情" width="760px" class="dark-dialog">
      <div v-if="detailRobot" class="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="部件编号(robot)"><span class="mono">{{ detailRobot.partNo }}</span></el-descriptions-item>
          <el-descriptions-item label="参考编号(reference)"><span class="mono">{{ detailRobot.referenceNo }}</span></el-descriptions-item>
          <el-descriptions-item label="Number"><span class="mono">{{ detailRobot.number ?? 0 }}</span></el-descriptions-item>
          <el-descriptions-item label="类型(type)">{{ detailRobot.typeSpec }}</el-descriptions-item>
          <el-descriptions-item label="工艺(tech)">{{ detailRobot.tech }}</el-descriptions-item>
          <el-descriptions-item label="标记(mark)"><span class="mono">{{ detailRobot.mark ?? 0 }}</span></el-descriptions-item>
          <el-descriptions-item label="等级(level)">
            <el-tag :type="levelTagType(detailRobot.level)" effect="light">{{ detailRobot.level }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="备注(remark)" :span="2">{{ detailRobot.remark }}</el-descriptions-item>
        </el-descriptions>

        <div class="detail-checks">
          <div class="detail-checks-title">A1-A7 检查项</div>
          <div class="detail-checks-grid">
            <div v-for="k in CHECK_KEYS" :key="k" class="detail-check">
              <el-tooltip :content="checkTooltip(detailRobot, k)" placement="top" :show-after="120">
                <div class="detail-check-cell">
                  <span class="detail-check-key">{{ k }}</span>
                  <span class="detail-check-label">{{ detailRobot.checks?.[k]?.label || '-' }}</span>
                  <span class="dot" :class="detailRobot.checks?.[k]?.ok ? 'dot-ok' : 'dot-bad'"></span>
                </div>
              </el-tooltip>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- Edit Dialog -->
    <el-dialog v-model="editVisible" title="编辑字段" width="560px" class="dark-dialog">
      <el-form v-if="editTarget" :model="editForm" label-position="top" class="edit-form">
        <el-row :gutter="14">
          <el-col :span="16">
            <el-form-item>
              <template #label>
                <span class="form-label">
                  <span class="form-label-title">参考编号</span>
                  <span class="form-label-hint">(reference)</span>
                </span>
              </template>
              <el-select v-model="editForm.referenceNo" placeholder="请选择参考编号" style="width: 100%" @change="handleReferenceChange">
                <el-option v-for="item in REFERENCE_OPTIONS" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item>
              <template #label>
                <span class="form-label">
                  <span class="form-label-title">Number</span>
                  <span class="form-label-hint">&nbsp;</span>
                </span>
              </template>
              <el-input v-model="editForm.number" readonly />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="14">
          <el-col :span="12">
            <el-form-item>
              <template #label>
                <span class="form-label">
                  <span class="form-label-title">标记</span>
                  <span class="form-label-hint">(mark)</span>
                </span>
              </template>
              <el-input-number v-model="editForm.mark" :min="0" :max="999999" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item>
              <template #label>
                <span class="form-label">
                  <span class="form-label-title">等级</span>
                  <span class="form-label-hint">(level)</span>
                </span>
              </template>
              <el-select v-model="editForm.level" placeholder="请选择等级" style="width: 100%">
                <el-option label="H" value="H" />
                <el-option label="M" value="M" />
                <el-option label="L" value="L" />
                <el-option label="T" value="T" />
                <el-option label="C" value="C" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <template #label>
            <span class="form-label">
              <span class="form-label-title">备注</span>
              <span class="form-label-hint">(remark)</span>
            </span>
          </template>
          <el-input v-model="editForm.remark" type="textarea" :rows="4" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSaving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Search, Close, Monitor, ArrowRight, ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { DEMO_MODE } from '@/config/appConfig'
import { getRobotComponents, getRobotGroups, updateRobotComponent } from '@/api/robots'
import { getGroupStats, getRobotsByGroup, robotGroups as mockGroups } from '@/mock/robots'

const router = useRouter()

const CHECK_KEYS = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7']
const REFERENCE_OPTIONS = [
  '20230626-20230724',
  '20230626-20230811',
  '20231020-20231208',
  '2025-07-01_2025-08-14',
  '2025-07-30_2025-09-03',
  '240216-240322',
  '240412-240621',
  '241101-241220',
  '250410-250516'
]

const drawerVisible = ref(false)
const selectedGroup = ref((DEMO_MODE ? mockGroups : [{ key: 'hop' }])[0].key)
const activeTab = ref('highRisk')
const keyword = ref('')
const levelFilter = ref('')
const axisKeysFilter = ref([])
const axisStateFilter = ref('')
const markMode = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const jumpPage = ref(1)

const detailVisible = ref(false)
const detailRobot = ref(null)
const editVisible = ref(false)
const editSaving = ref(false)
const editTarget = ref(null)
const editForm = ref({
  referenceNo: '',
  number: 0,
  mark: 0,
  remark: '',
  level: 'L'
})

const loading = ref(false)
const groupsData = ref([])
const serverRows = ref([])
const serverTotal = ref(0)

const groups = computed(() => {
  if (DEMO_MODE) {
    return mockGroups.map((group) => ({
      ...group,
      stats: getGroupStats(group.key)
    }))
  }
  return groupsData.value.map((group) => ({
    key: group.key,
    name: group.name,
    total: group.expected_total ?? group.stats?.total ?? 0,
    stats: {
      highRisk: group.stats?.highRisk ?? 0,
      historyHighRisk: group.stats?.historyHighRisk ?? 0
    }
  }))
})

const activeGroupName = computed(() => {
  const list = DEMO_MODE ? mockGroups : groupsData.value
  const group = list.find((g) => g.key === selectedGroup.value)
  return group?.name || selectedGroup.value
})

const groupStats = computed(() => {
  if (DEMO_MODE) {
    const stats = getGroupStats(selectedGroup.value)
    return {
      highRisk: stats.highRisk ?? 0,
      historyHighRisk: stats.historyHighRisk ?? 0,
      total: stats.total ?? 0
    }
  }
  const group = groups.value.find((g) => g.key === selectedGroup.value)
  return {
    highRisk: group?.stats?.highRisk ?? 0,
    historyHighRisk: group?.stats?.historyHighRisk ?? 0,
    total: group?.total ?? 0
  }
})

// 分页相关计算属性
const totalPages = computed(() => {
  const total = DEMO_MODE ? filteredRows.value.length : serverTotal.value
  return Math.ceil(total / pageSize.value) || 1
})

const displayPages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  const pages = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    if (current <= 4) {
      pages.push(1, 2, 3, 4, 5, '...', total)
    } else if (current >= total - 3) {
      pages.push(1, '...', total - 4, total - 3, total - 2, total - 1, total)
    } else {
      pages.push(1, '...', current - 1, current, current + 1, '...', total)
    }
  }
  return pages
})

const handleJump = () => {
  const page = Math.max(1, Math.min(totalPages.value, jumpPage.value))
  goToPage(page)
}

// 页码按钮点击处理
const handlePageClick = (page) => {
  if (page === '...') return
  console.log('handlePageClick called with page:', page, 'totalPages:', totalPages.value, 'currentPage:', currentPage.value)
  goToPage(page)
}

// 添加原生事件监听用于调试
const setupPaginationDebug = () => {
  setTimeout(() => {
    const pageButtons = document.querySelectorAll('.pagination-page')
    console.log('Found pagination buttons:', pageButtons.length)
    pageButtons.forEach((btn, index) => {
      btn.addEventListener('click', (e) => {
        console.log('Native click on button:', btn.textContent.trim(), 'index:', index)
      })
    })
  }, 1000)
}

// 统一的页码跳转方法
const goToPage = (page) => {
  console.log('goToPage called with page:', page, 'DEMO_MODE:', DEMO_MODE)
  currentPage.value = page
  jumpPage.value = page
  // 非DEMO模式需要重新加载数据
  if (!DEMO_MODE) {
    loadRows()
  }
}

// 同步jumpPage与currentPage
watch(currentPage, (newVal) => {
  jumpPage.value = newVal
})

// 车间切换处理
const handleSelectGroup = (key) => {
  selectedGroup.value = key
  drawerVisible.value = false
  ElMessage.success(`已切换至: ${activeGroupName.value}`)
}

const getIconClass = (groupKey) => {
  const colorMap = {
    hop: 'blue',
    wb: 'purple',
    sb: 'green',
    tb: 'orange'
  }
  return colorMap[groupKey] || 'blue'
}

const robots = computed(() => (DEMO_MODE ? getRobotsByGroup(selectedGroup.value) : serverRows.value))

const riskName = (level) => {
  const names = { critical: '严重', high: '高', medium: '中', low: '低' }
  return names[level] || level
}

const riskTagType = (level) => {
  const types = { critical: 'danger', high: 'warning', medium: 'info', low: '' }
  return types[level] || 'info'
}

const levelTagType = (level) => {
  const types = { H: 'danger', M: 'warning', L: 'info' }
  return types[level] || 'info'
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

const latestRiskTime = (robot) => {
  if (!robot?.riskHistory?.length) return ''
  return robot.riskHistory
    .map((event) => event.time)
    .sort((a, b) => new Date(b).getTime() - new Date(a).getTime())[0]
}

const matchesKeyword = (robot) => {
  const key = keyword.value.trim().toLowerCase()
  if (!key) return true
  return (
    (robot.robot_id || robot.id || '').toString().toLowerCase().includes(key) ||
    (robot.name || '').toLowerCase().includes(key) ||
    (robot.model || '').toLowerCase().includes(key) ||
    (robot.partNo || robot.part_no || '').toLowerCase().includes(key) ||
    (robot.referenceNo || robot.reference_no || '').toLowerCase().includes(key) ||
    (robot.typeSpec || robot.type_spec || '').toLowerCase().includes(key) ||
    (robot.tech || '').toLowerCase().includes(key) ||
    (robot.remark || '').toLowerCase().includes(key)
  )
}

const matchesFilters = (robot) => {
  if (levelFilter.value && robot.level !== levelFilter.value) return false
  if (markMode.value === 'zero' && (robot.mark ?? 0) !== 0) return false
  if (markMode.value === 'nonzero' && (robot.mark ?? 0) === 0) return false
  if (axisKeysFilter.value.length) {
    const keys = axisKeysFilter.value
    if (axisStateFilter.value === 'bad') {
      const anyBad = keys.some((k) => robot?.checks?.[k]?.ok === false)
      if (!anyBad) return false
    } else if (axisStateFilter.value === 'ok') {
      const allOk = keys.every((k) => robot?.checks?.[k]?.ok !== false)
      if (!allOk) return false
    }
  }
  return matchesKeyword(robot)
}

const filteredRows = computed(() => {
  const list = robots.value

  // 根据当前标签页筛选数据
  let filtered = list
  if (activeTab.value === 'highRisk') {
    filtered = list.filter((r) => r.isHighRisk)
  } else if (activeTab.value === 'history') {
    filtered = list.filter((r) => r.riskHistory?.length)
  }

  // 应用所有过滤器（包括关键词搜索）
  // 前端始终进行过滤，确保搜索功能在所有模式下都能正常工作
  return filtered.filter(matchesFilters)
})

const pagedRows = computed(() => {
  // 非 DEMO 模式下，使用服务器分页
  if (!DEMO_MODE) return filteredRows.value
  // DEMO 模式下，前端分页
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRows.value.slice(start, start + pageSize.value)
})

const resetFilters = () => {
  keyword.value = ''
  levelFilter.value = ''
  axisKeysFilter.value = []
  axisStateFilter.value = ''
  markMode.value = ''
  currentPage.value = 1
  if (!DEMO_MODE) loadRows()
}

// 搜索处理函数
const handleSearch = () => {
  currentPage.value = 1
  if (!DEMO_MODE) {
    // 搜索时请求所有数据，由前端进行过滤
    loadRows(true)
  }
}

const handleRefresh = () => {
  currentPage.value = 1
  if (!DEMO_MODE) {
    loadGroups()
    loadRows()
  }
}

const openDetail = (robot) => {
  detailRobot.value = robot
  detailVisible.value = true
}

const normalizeRow = (row) => {
  if (!row) return null
  return {
    id: row.id,
    referenceNo: row.referenceNo ?? row.reference_no ?? '',
    number: row.number ?? 0,
    mark: row.mark ?? 0,
    remark: row.remark ?? '',
    level: row.level ?? 'L'
  }
}

const openEdit = (row, focusField) => {
  const next = normalizeRow(row)
  if (!next?.id) return
  editTarget.value = row
  editForm.value = { ...next }
  editVisible.value = true
}

const applyEditToRow = (row, patch) => {
  if (!row) return
  if ('referenceNo' in patch) row.referenceNo = patch.referenceNo
  if ('number' in patch) row.number = patch.number
  if ('mark' in patch) row.mark = patch.mark
  if ('remark' in patch) row.remark = patch.remark
  if ('level' in patch) row.level = patch.level
}

const randomNumber = () => Math.floor(100 + Math.random() * 9000)

const handleReferenceChange = () => {
  editForm.value.number = randomNumber()
}

const saveEdit = async () => {
  if (!editTarget.value) return
  const payload = {
    referenceNo: (editForm.value.referenceNo || '').trim(),
    number: Number(editForm.value.number ?? 0),
    mark: Number(editForm.value.mark ?? 0),
    remark: (editForm.value.remark || '').trim(),
    level: editForm.value.level
  }

  if (!payload.referenceNo) {
    ElMessage.warning('参考编号(reference)不能为空')
    return
  }

  editSaving.value = true
  try {
    if (DEMO_MODE) {
      applyEditToRow(editTarget.value, payload)
      ElMessage.success('已保存（演示模式）')
      editVisible.value = false
      return
    }

    await updateRobotComponent(editTarget.value.id, payload)
    applyEditToRow(editTarget.value, payload)
    ElMessage.success('保存成功')
    editVisible.value = false
    if (!DEMO_MODE) {
      await loadGroups()
      if (keyword.value.trim()) {
        currentPage.value = 1
        await loadRows(true)
      } else {
        await loadRows()
      }
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '保存失败')
  } finally {
    editSaving.value = false
  }
}

const checkTooltip = (robot, key) => {
  const check = robot?.checks?.[key]
  const label = check?.label ? `${key}（${check.label}）` : key
  if (!check) return label
  return check.ok ? `${label}：正常/符合要求` : `${label}：存在异常/待处理`
}

const openBI = (robot) => {
  const partNo = robot?.partNo || robot?.part_no || ''
  const groupKey = robot?.group || selectedGroup.value || ''
  router.push({
    path: '/alerts',
    query: {
      group: groupKey,
      robot: partNo
    }
  })
}

const loadGroups = async () => {
  if (DEMO_MODE) return
  try {
    loading.value = true
    groupsData.value = await getRobotGroups()
    if (!groupsData.value.find((g) => g.key === selectedGroup.value) && groupsData.value.length) {
      selectedGroup.value = groupsData.value[0].key
    }
  } finally {
    loading.value = false
  }
}

const loadRows = async (fetchAll = false) => {
  if (DEMO_MODE) return
  loading.value = true
  try {
    const tabMap = { highRisk: 'highRisk', all: 'all', history: 'history' }
    // 搜索时获取所有数据用于前端过滤
    const actualPageSize = fetchAll ? 10000 : pageSize.value
    const params = {
      group: selectedGroup.value,
      tab: tabMap[activeTab.value] || 'highRisk',
      // 不发送 keyword 参数，由前端过滤
      level: levelFilter.value || undefined,
      axisKeys: axisKeysFilter.value.length ? axisKeysFilter.value.join(',') : undefined,
      axisOk: axisStateFilter.value ? axisStateFilter.value === 'ok' : undefined,
      markMode: markMode.value || undefined,
      page: fetchAll ? 1 : currentPage.value,
      page_size: actualPageSize
    }
    console.log('Loading rows with params:', params)
    const data = await getRobotComponents(params)
    console.log('Loaded data:', { count: data.count, resultsLength: data.results?.length })
    serverRows.value = data.results || data
    serverTotal.value = data.count ?? serverRows.value.length
  } catch (error) {
    console.error('Error loading rows:', error)
    if (error?.response?.status === 404 && typeof error.response?.data?.detail === 'string' && error.response.data.detail.includes('Invalid page')) {
      currentPage.value = 1
      return
    }
    throw error
  } finally {
    loading.value = false
  }
}

// 初始化加载数据
const initData = async () => {
  if (!DEMO_MODE) {
    await loadGroups()
    await loadRows()
  }
  // 设置分页调试
  setupPaginationDebug()
}

// 监听页码变化
watch(currentPage, (newPage) => {
  console.log('Current page changed:', newPage)
  if (!DEMO_MODE) {
    loadRows()
  }
})

// 监听其他过滤器变化
watch([selectedGroup, activeTab], () => {
  console.log('selectedGroup or activeTab changed, resetting page to 1')
  currentPage.value = 1
  if (!DEMO_MODE) loadRows()
})

watch(pageSize, () => {
  if (!DEMO_MODE) {
    currentPage.value = 1
    loadRows()
  }
})

// 过滤器变化时自动触发（关键词需要按回车）
watch([levelFilter, axisKeysFilter, axisStateFilter, markMode], () => {
  console.log('Filters changed, resetting page to 1. Filters:', {
    level: levelFilter.value,
    axisKeys: axisKeysFilter.value,
    axisState: axisStateFilter.value,
    markMode: markMode.value
  })
  if (!DEMO_MODE) {
    currentPage.value = 1
    loadRows()
  }
})

// 当 axisKeysFilter 清空时，同步清空 axisStateFilter
watch(axisKeysFilter, (newVal) => {
  if (!newVal.length) {
    axisStateFilter.value = ''
  }
})

// 初始化数据
initData()
</script>

<style scoped>
/* === 入场动画系统 === */

/* 标题滑入淡入动画 */
.entrance-slide-in {
  animation: slideInFade 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  opacity: 0;
  transform: translateX(-40px);
}

@keyframes slideInFade {
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 卡片缩放淡入动画 - 主卡片 */
.entrance-scale-up {
  animation: scaleUpFade 0.9s cubic-bezier(0.16, 1, 0.3, 1) 0.2s forwards;
  opacity: 0;
  transform: scale(0.92) translateY(30px);
}

/* 卡片缩放淡入动画 - 延迟1 */
.entrance-scale-up-delay-1 {
  animation: scaleUpFade 0.9s cubic-bezier(0.16, 1, 0.3, 1) 0.3s forwards;
  opacity: 0;
  transform: scale(0.92) translateY(30px);
}

/* 卡片缩放淡入动画 - 延迟2 */
.entrance-scale-up-delay-2 {
  animation: scaleUpFade 0.9s cubic-bezier(0.16, 1, 0.3, 1) 0.4s forwards;
  opacity: 0;
  transform: scale(0.92) translateY(30px);
}

/* 卡片缩放淡入动画 - 延迟3 */
.entrance-scale-up-delay-3 {
  animation: scaleUpFade 0.9s cubic-bezier(0.16, 1, 0.3, 1) 0.5s forwards;
  opacity: 0;
  transform: scale(0.92) translateY(30px);
}

/* 卡片缩放淡入动画 - 延迟4 */
.entrance-scale-up-delay-4 {
  animation: scaleUpFade 0.9s cubic-bezier(0.16, 1, 0.3, 1) 0.6s forwards;
  opacity: 0;
  transform: scale(0.92) translateY(30px);
}

@keyframes scaleUpFade {
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* 边框光效入场 */
.entrance-border-glow {
  animation: borderBreathe 6s infinite ease-in-out, borderGlowEnter 1.2s ease-out forwards;
  opacity: 0;
}

@keyframes borderGlowEnter {
  0% {
    opacity: 0;
    transform: scale(0.95);
  }
  50% {
    opacity: 0.6;
  }
  100% {
    opacity: 0.3;
    transform: scale(1);
  }
}

/* 按钮淡入效果 */
.btn-entrance {
  animation: btnFadeIn 0.6s ease-out 0.7s forwards;
  opacity: 0;
  transform: translateY(-15px);
}

@keyframes btnFadeIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* KPI图标入场动画 */
.kpi-icon-entrance {
  animation: kpiIconFadeIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) 0.6s forwards;
  opacity: 0;
  transform: scale(0);
}

@keyframes kpiIconFadeIn {
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 表格入场动画 */
.table-entrance {
  animation: tableFadeIn 0.8s ease-out 0.8s forwards;
  opacity: 0;
}

@keyframes tableFadeIn {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* === iOS 风格基础布局与背景 === */
.robot-status-viewport {
  background: #030508;
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  color: #fff;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
}

.layout-wrapper {
  position: relative;
  z-index: 1;
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
}

/* === 背景流光元素 === */
.ambient-background {
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

.breathing-line {
  position: absolute;
  height: 1px;
  background: linear-gradient(90deg, transparent, #ffaa00, transparent);
  filter: blur(1px);
  opacity: 0.3;
  animation: breathe 8s infinite ease-in-out;
}
.gold-1 { width: 100%; top: 30%; left: -50%; transform: rotate(-5deg); }
.gold-2 { width: 100%; bottom: 20%; right: -50%; transform: rotate(3deg); animation-delay: -4s; }

@keyframes breathe {
  0%, 100% { opacity: 0.1; transform: scaleX(0.8) translateY(0); }
  50% { opacity: 0.5; transform: scaleX(1.2) translateY(-20px); }
}

.scan-grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: linear-gradient(to bottom, black, transparent);
  animation: gridMove 25s linear infinite;
}
@keyframes gridMove { from { background-position: 0 0; } to { background-position: 0 50px; } }

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

.ios-title {
  font-size: 32px;
  letter-spacing: -0.5px;
  background: linear-gradient(180deg, #fff 40%, rgba(255,255,255,0.6));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 0 8px 0;
  position: relative;
  animation: titleGlow 2s ease-out forwards;
}

@keyframes titleGlow {
  0% {
    text-shadow: 0 0 20px rgba(255, 170, 0, 0), 0 0 40px rgba(255, 170, 0, 0);
    filter: brightness(0.8);
  }
  50% {
    text-shadow: 0 0 20px rgba(255, 170, 0, 0.5), 0 0 40px rgba(255, 170, 0, 0.3);
    filter: brightness(1.2);
  }
  100% {
    text-shadow: 0 0 20px rgba(255, 170, 0, 0), 0 0 40px rgba(255, 170, 0, 0);
    filter: brightness(1);
  }
}

.ios-title small { font-size: 14px; color: #ffaa00; margin-left: 10px; font-weight: 300; letter-spacing: 2px; }

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.ios-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #fff;
  border-radius: 999px;
  padding: 8px 16px;
}
.ios-btn:hover { background: rgba(255, 255, 255, 0.12); }

/* === iOS 玻璃卡片 === */
.ios-glass {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(50px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
}
.border-glow {
  position: absolute;
  inset: 0;
  border-radius: 24px;
  padding: 1px;
  background: linear-gradient(135deg, rgba(255, 170, 0, 0.4), transparent 40%, rgba(255, 170, 0, 0.1));
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  animation: borderBreathe 6s infinite ease-in-out;
}
.border-glow.gold-tint { background: linear-gradient(135deg, rgba(255, 170, 0, 0.55), transparent 45%, rgba(255, 170, 0, 0.15)); }
@keyframes borderBreathe {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.8; box-shadow: inset 0 0 15px rgba(255, 170, 0, 0.2); }
}

.accent-bar {
  width: 4px; height: 16px; background: #ffaa00; border-radius: 10px;
  box-shadow: 0 0 10px #ffaa00;
}

/* === KPI 卡片 === */
.kpi-selector-container {
  margin: 30px 0;
  display: flex;
  justify-content: flex-start;
}

.kpi-card {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  text-align: left;
  border: none;
  width: 100%;
}

.hero-card {
  width: 480px;
}

.selector-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tap-hint {
  font-size: 11px;
  color: #ffaa00;
  opacity: 0.8;
  display: flex;
  align-items: center;
  gap: 4px;
}

.kpi-card:hover,
.kpi-card.active {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5), 0 0 15px rgba(255, 170, 0, 0.2);
}

.kpi-card.active .active-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: #ffaa00;
  box-shadow: 0 0 15px #ffaa00;
}

.kpi-icon-box {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  flex-shrink: 0;
  background: rgba(255, 170, 0, 0.12);
  color: #ffaa00;
}

.kpi-content {
  flex: 1;
  min-width: 0;
}

.kpi-content label {
  display: block;
  font-size: 12px;
  color: #8899aa;
  margin-bottom: 6px;
  font-weight: 500;
  letter-spacing: 1px;
}

.main-value {
  font-size: 28px;
  font-weight: 900;
  color: #fff;
  margin: 4px 0;
}

.main-value small {
  font-size: 10px;
  color: #667085;
  margin-left: 5px;
}

.status-mini-tags {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}

.tag {
  font-size: 10px;
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid rgba(255,255,255,0.1);
}

.tag.risk {
  color: #ff4444;
  border-color: rgba(255, 68, 68, 0.3);
  background: rgba(255, 68, 68, 0.1);
}

.tag.total {
  color: #8899aa;
  border-color: rgba(136, 153, 170, 0.3);
  background: rgba(136, 153, 170, 0.1);
}

/* === 数据表格区域 === */
.data-table-section {
  padding: 0;
  overflow: hidden;
  position: relative;
}

.table-header {
  padding: 15px 25px;
  font-size: 12px;
  color: #c0ccda;
  letter-spacing: 1px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  display: flex;
  align-items: center;
  gap: 10px;
}

/* === Tabs Dark === */
:deep(.status-tabs-dark) {
  --el-tabs-nav-wrap-bg-color: transparent;
  background: transparent;
}

:deep(.status-tabs-dark .el-tabs__nav-wrap::after) {
  display: none;
}

:deep(.status-tabs-dark .el-tabs__item) {
  color: #8899aa;
}

:deep(.status-tabs-dark .el-tabs__item.is-active) {
  color: #ffaa00;
}

:deep(.status-tabs-dark .el-tabs__active-bar) {
  background: #ffaa00;
}

:deep(.status-tabs-dark .el-tabs__nav-wrap) {
  padding-left: 25px;
}

/* === Filters === */
.filters {
  padding: 15px 25px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.filters-right {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* Dark inputs */
:deep(.dark-input .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: none;
}

:deep(.dark-input .el-input__wrapper:hover) {
  border-color: rgba(255, 170, 0, 0.3);
}

:deep(.dark-input .el-input__wrapper.is-focus) {
  border-color: #ffaa00;
}

:deep(.dark-input .el-input__inner) {
  color: #fff;
}

/* 搜索框前缀图标样式 */
:deep(.dark-input .el-input__prefix) {
  color: #8899aa;
}

:deep(.dark-input:focus-within .el-input__prefix) {
  color: #ffaa00;
}

:deep(.dark-select .el-select__wrapper) {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: none;
}

:deep(.dark-select .el-select__wrapper:hover) {
  border-color: rgba(255, 170, 0, 0.3);
}

:deep(.dark-select .el-select__wrapper.is-focus) {
  border-color: #ffaa00;
}

:deep(.dark-select .el-select__selected-item) {
  color: #fff;
}

:deep(.dark-select) {
  min-width: 120px;
}

:deep(.dark-select.el-select--multiple) {
  min-width: 140px;
}

/* === Table Legend === */
.table-legend {
  display: flex;
  gap: 16px;
  align-items: center;
  padding: 10px 25px;
  color: #8899aa;
  font-size: 12px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.2);
}

.dot-ok {
  background: #22c55e;
  box-shadow: 0 0 8px #22c55e;
}

.dot-bad {
  background: #ef4444;
  box-shadow: 0 0 8px #ef4444;
}

/* === Table === */
/* 表格 CSS 变量覆盖 - 参考平台概览的半透明风格 */
.data-table-section :deep(.el-table) {
  --el-table-bg-color: rgba(6, 10, 18, 0.9);
  --el-table-tr-bg-color: rgba(8, 12, 20, 0.45);
  --el-table-row-hover-bg-color: rgba(255, 170, 0, 0.08);
  --el-table-header-bg-color: rgba(255, 255, 255, 0.04);
  --el-table-border-color: rgba(255, 255, 255, 0.06);
  color: #dbe6f5;
}

.data-table-section :deep(.el-table__header th) {
  background: rgba(255, 255, 255, 0.04) !important;
  border-color: rgba(255, 255, 255, 0.06) !important;
  color: #8da0b7 !important;
  font-size: 10px;
  letter-spacing: 1.2px;
  font-weight: 600;
}

.data-table-section :deep(.el-table__body tr) {
  background: rgba(8, 12, 20, 0.5) !important;
}

.data-table-section :deep(.el-table__body tr.el-table__row--striped) {
  background: rgba(14, 20, 32, 0.65) !important;
}

.data-table-section :deep(.el-table__body td) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.04) !important;
  background-color: transparent !important;
  color: #dbe6f5 !important;
}

.data-table-section :deep(.el-table__row:hover td) {
  background: rgba(255, 170, 0, 0.08) !important;
}

.data-table-section :deep(.el-table__row.current-row td) {
  background: rgba(255, 170, 0, 0.14) !important;
}

/* 固定列样式 */
.data-table-section :deep(.el-table-fixed-column--right) {
  background: rgba(6, 10, 18, 0.92) !important;
}

.data-table-section :deep(.el-table-fixed--right .el-table__fixed-body-wrapper) {
  background: rgba(6, 10, 18, 0.92) !important;
}

/* 限制表格固定列的高度，防止遮挡分页 */
.data-table-section :deep(.el-table__fixed) {
  height: 520px !important;
}

.data-table-section :deep(.el-table__fixed-right) {
  height: 520px !important;
}

.data-table-section :deep(.el-table__fixed-right-patch) {
  height: 520px !important;
}

.robot-name-cell {
  color: #ffaa00;
  font-weight: 600;
}

.robot-name-cell:hover {
  text-shadow: 0 0 10px rgba(255, 170, 0, 0.5);
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  letter-spacing: 0.1px;
}

.remark-link {
  max-width: 100%;
  display: inline-flex;
  justify-content: flex-start;
  text-align: left;
  white-space: normal;
  line-height: 1.2;
}

/* === Custom Pagination === */
.pagination-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(3, 5, 8, 0.4);
  position: relative;
  z-index: 10;
}

.pagination-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pagination-total {
  color: #7f93a8;
  font-size: 13px;
  font-weight: 500;
}

.pagination-size-select {
  width: 110px;
}

:deep(.pagination-size-select .el-select__wrapper) {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.25s ease;
}

:deep(.pagination-size-select .el-select__wrapper:hover) {
  border-color: rgba(255, 170, 0, 0.4);
  background: rgba(255, 170, 0, 0.08);
}

:deep(.pagination-size-select .el-select__selected-item) {
  color: #8899aa;
  font-size: 13px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #8899aa;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.pagination-arrow:hover:not(:disabled) {
  background: rgba(255, 170, 0, 0.12);
  border-color: rgba(255, 170, 0, 0.4);
  color: #ffaa00;
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(255, 170, 0, 0.2);
}

.pagination-arrow:disabled {
  opacity: 0.3;
  cursor: not-allowed;
  background: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.05);
  color: rgba(136, 153, 170, 0.3);
  box-shadow: none;
}

.pagination-arrow svg {
  width: 18px;
  height: 18px;
}

.pagination-pages {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pagination-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 38px;
  height: 38px;
  padding: 0 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #8899aa;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  user-select: none;
}

.pagination-page:hover:not(.active):not(.ellipsis):not(:disabled) {
  background: rgba(255, 170, 0, 0.12);
  border-color: rgba(255, 170, 0, 0.4);
  color: #ffaa00;
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(255, 170, 0, 0.2);
  cursor: pointer;
}

.pagination-page.active {
  background: linear-gradient(135deg, #ffaa00, #ff8800);
  border-color: #ffaa00;
  color: #030508;
  font-weight: 700;
  box-shadow: 0 4px 16px rgba(255, 170, 0, 0.35), 0 0 20px rgba(255, 170, 0, 0.2);
  cursor: default;
}

.pagination-page.ellipsis {
  background: transparent;
  border: none;
  box-shadow: none;
  cursor: default;
  color: #5a6a7a;
}

.pagination-page:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.pagination-jumper {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #7f93a8;
  font-size: 13px;
  font-weight: 500;
}

.pagination-jump-input {
  width: 70px;
}

:deep(.pagination-jump-input .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.25s ease;
}

:deep(.pagination-jump-input .el-input__wrapper:hover),
:deep(.pagination-jump-input .el-input__wrapper.is-focus) {
  border-color: rgba(255, 170, 0, 0.4);
  background: rgba(255, 170, 0, 0.08);
}

:deep(.pagination-jump-input .el-input__inner) {
  color: #8899aa;
  text-align: center;
  font-size: 13px;
}

/* === Detail === */
.detail {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.detail-checks {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.03);
}

.detail-checks-title {
  font-weight: 800;
  margin-bottom: 12px;
  color: #fff;
}

.detail-checks-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.detail-check-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.detail-check-key {
  font-weight: 900;
  width: 28px;
}

.detail-check-label {
  flex: 1;
  color: #8899aa;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* === Edit Form === */
.edit-form :deep(.el-form-item) {
  margin-bottom: 14px;
}

.edit-form :deep(.el-input__wrapper),
.edit-form :deep(.el-select__wrapper),
.edit-form :deep(.el-textarea__inner) {
  border-radius: 10px;
}

.form-label {
  display: inline-flex;
  flex-direction: column;
  line-height: 1.1;
  gap: 3px;
}

.form-label-title {
  font-weight: 800;
  color: #fff;
}

.form-label-hint {
  color: #8899aa;
  font-size: 12px;
  font-weight: 600;
}

/* === Dark Dialog === */
:deep(.dark-dialog) {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(30px) saturate(160%);
  border-radius: 18px;
}

:deep(.dark-dialog .el-dialog__header) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  margin-right: 0;
  padding: 18px 24px 8px;
}

:deep(.dark-dialog .el-dialog__title) {
  color: #fff;
}

:deep(.dark-dialog .el-dialog__body) {
  color: #eee;
  padding: 14px 24px 24px;
}

:deep(.dark-dialog .el-dialog__close) {
  color: #9fb3c8;
}

:deep(.dark-dialog .el-dialog__close:hover) {
  color: #ffaa00;
}

:deep(.dark-dialog .el-descriptions) {
  --el-descriptions-table-border: 1px solid rgba(255, 255, 255, 0.06);
}

:deep(.dark-dialog .el-descriptions__label) {
  background: rgba(255, 255, 255, 0.03) !important;
  color: #7f93a8;
}

:deep(.dark-dialog .el-descriptions__content) {
  background: transparent !important;
  color: #dfe8f7;
}

:deep(.dark-dialog .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

:deep(.dark-dialog .el-input__inner) {
  color: #fff;
}

/* 下拉框与输入框样式统一 */
:deep(.dark-dialog .el-select__wrapper) {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

:deep(.dark-dialog .el-select__wrapper:hover) {
  border-color: rgba(255, 255, 255, 0.15);
}

:deep(.dark-dialog .el-select__wrapper.is-focus) {
  border-color: rgba(0, 195, 255, 0.4);
  box-shadow: 0 0 0 2px rgba(0, 195, 255, 0.1);
}

:deep(.dark-dialog .el-select .el-select__selected-item) {
  color: #fff;
}

/* el-input-number 与 el-input 样式统一 */
:deep(.dark-dialog .el-input-number .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

:deep(.dark-dialog .el-input-number .el-input__inner) {
  color: #fff;
}

/* el-input-number 上下按钮样式 */
:deep(.dark-dialog .el-input-number__decrease),
:deep(.dark-dialog .el-input-number__increase) {
  background: rgba(255, 255, 255, 0.05);
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  color: #8899aa;
}

:deep(.dark-dialog .el-input-number__decrease:hover),
:deep(.dark-dialog .el-input-number__increase:hover) {
  background: rgba(255, 255, 255, 0.1);
  color: #00c3ff;
}

:deep(.dark-dialog .el-input-number__decrease.is-disabled),
:deep(.dark-dialog .el-input-number__increase.is-disabled) {
  background: rgba(255, 255, 255, 0.02);
  border-left-color: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.15);
}

:deep(.dark-dialog .el-textarea__inner) {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #fff;
}

/* Responsive */
@media (max-width: 1200px) {
  .kpi-selector-container {
    justify-content: center;
  }
}

/* === Drawer 抽屉样式 === */
:deep(.dark-drawer-glass) {
  background: rgba(10, 15, 25, 0.8) !important;
  backdrop-filter: blur(40px) saturate(150%) !important;
  border-left: 1px solid rgba(255, 255, 255, 0.1) !important;
}

:deep(.dark-drawer-glass .el-drawer__title) {
  color: #fff;
  font-weight: 800;
}

:deep(.dark-drawer-glass .el-drawer__header) {
  margin-bottom: 0;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

:deep(.dark-drawer-glass .el-drawer__body) {
  padding: 20px 24px;
}

.workshop-drawer-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.workshop-item {
  padding: 20px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.workshop-item:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateX(-5px);
  border-color: rgba(255, 170, 0, 0.3);
}

.workshop-item.active {
  background: rgba(255, 170, 0, 0.1);
  border-color: #ffaa00;
}

.ws-info-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.ws-name {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.ws-badges {
  display: flex;
  gap: 8px;
}

.badge-risk {
  background: #ef4444;
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 800;
}

.badge-total {
  color: #8899aa;
  font-size: 11px;
}

.ws-progress-track {
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.ws-progress-fill {
  height: 100%;
  background: #ffaa00;
  box-shadow: 0 0 10px rgba(255, 170, 0, 0.4);
  transition: width 0.8s ease;
}

.ws-progress-fill.is-danger {
  background: linear-gradient(90deg, #ffaa00, #ef4444);
}
</style>

<!-- 全局样式：统一 Tag 样式 -->
<style>
/* === 统一 Tag 样式 (表格内或详情页) === */
.el-tag {
  border-radius: 6px !important;
  border: none !important;
  padding: 0 8px !important;
  height: 22px !important;
  line-height: 22px !important;
}

/* 覆盖 Element Plus 默认 Tag 颜色为暗黑适配色 */
.el-tag--success { background: rgba(34, 197, 94, 0.15) !important; color: #4ade80 !important; }
.el-tag--warning { background: rgba(255, 170, 0, 0.15) !important; color: #ffaa00 !important; }
.el-tag--danger { background: rgba(239, 68, 68, 0.15) !important; color: #f87171 !important; }
.el-tag--info { background: rgba(255, 255, 255, 0.1) !important; color: #94a3b8 !important; }

/* 多选Tag关闭按钮样式 */
.el-select .el-select__tags .el-tag__close {
  color: #ffaa00 !important;
}
.el-select .el-select__tags .el-tag__close:hover {
  background-color: rgba(255, 170, 0, 0.3) !important;
  color: #fff !important;
}
</style>
