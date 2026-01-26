<template>
  <div class="robot-status">
    <el-card class="group-card">
      <template #header>
        <div class="card-header">
          <div class="title">
            <span class="title-text">机器人状态信息</span>
          </div>
          <el-button :icon="Refresh" @click="handleRefresh">载入数据</el-button>
        </div>
      </template>

      <el-row :gutter="16" class="group-row">
        <el-col v-for="group in groups" :key="group.key" :span="6">
          <button
            type="button"
            class="group-tile"
            :class="{ active: group.key === selectedGroup }"
            @click="selectedGroup = group.key"
          >
            <div class="group-top">
              <div class="group-name">{{ group.name }}</div>
              <div class="group-total">{{ group.total }}</div>
            </div>
            <div class="group-meta">
              <span class="meta-item">在线 {{ group.stats.online }}</span>
              <span class="meta-item">维护 {{ group.stats.maintenance }}</span>
              <span class="meta-item meta-risk">高风险 {{ group.stats.highRisk }}</span>
            </div>
          </button>
        </el-col>
      </el-row>

    </el-card>

    <el-card class="list-card">
      <el-tabs v-model="activeTab" class="status-tabs">
        <el-tab-pane name="highRisk" label="高风险机器人列表" />
        <el-tab-pane name="all" label="所有机器人信息列表" />
        <el-tab-pane name="history" label="历史高风险机器人列表" />
      </el-tabs>

      <div class="filters">
        <el-row :gutter="12" align="middle">
          <el-col :span="10">
            <el-input v-model="keyword" placeholder="搜索：部件编号 / 参考编号 / 类型 / 工艺 / 备注" clearable />
          </el-col>
          <el-col :span="4">
            <el-select v-model="levelFilter" placeholder="等级(level)" clearable>
              <el-option label="H" value="H" />
              <el-option label="M" value="M" />
              <el-option label="L" value="L" />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select
              v-model="axisKeysFilter"
              placeholder="Axis(A1-A7)"
              multiple
              collapse-tags
              collapse-tags-tooltip
              clearable
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
            >
              <el-option label="正常" value="ok" />
              <el-option label="异常" value="bad" />
            </el-select>
          </el-col>
          <el-col :span="3">
            <el-select v-model="markMode" placeholder="标记(mark)" clearable>
              <el-option label="0" value="zero" />
              <el-option label="非0" value="nonzero" />
            </el-select>
          </el-col>
          <el-col :span="24" class="filters-right">
            <el-button type="primary" :icon="Search" @click="currentPage = 1">查询</el-button>
            <el-button :icon="Close" @click="resetFilters">重置</el-button>
          </el-col>
        </el-row>
      </div>

      <div class="table-legend">
        <span class="legend-item"><span class="dot dot-ok"></span>正常/符合要求</span>
        <span class="legend-item"><span class="dot dot-bad"></span>该项异常/待处理</span>
      </div>

      <el-table :data="pagedRows" stripe height="520" v-loading="loading">
        <el-table-column prop="partNo" label="部件编号(robot)" width="190" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button type="primary" link class="mono" @click="openBI(row)">
              {{ row.partNo }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="参考编号(reference)" width="170" show-overflow-tooltip>
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

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="DEMO_MODE ? filteredRows.length : serverTotal"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pager"
      />
    </el-card>

    <el-dialog v-model="detailVisible" title="部件详情" width="760px">
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

    <el-dialog v-model="editVisible" title="编辑字段" width="560px">
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
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Search, Close } from '@element-plus/icons-vue'
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

const selectedGroup = ref((DEMO_MODE ? mockGroups : [{ key: 'hop' }])[0].key)
const activeTab = ref('highRisk')
const keyword = ref('')
const levelFilter = ref('')
const axisKeysFilter = ref([])
const axisStateFilter = ref('')
const markMode = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

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
      online: group.stats?.online ?? 0,
      offline: group.stats?.offline ?? 0,
      maintenance: group.stats?.maintenance ?? 0,
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
  if (DEMO_MODE) return getGroupStats(selectedGroup.value)
  const group = groups.value.find((g) => g.key === selectedGroup.value)
  return group?.stats || { online: 0, highRisk: 0, historyHighRisk: 0 }
})

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
  if (!DEMO_MODE) return robots.value

  const list = robots.value
  if (activeTab.value === 'highRisk') return list.filter((r) => r.isHighRisk).filter(matchesFilters)
  if (activeTab.value === 'history') return list.filter((r) => r.riskHistory?.length).filter(matchesFilters)
  return list.filter(matchesFilters)
})

const pagedRows = computed(() => {
  if (!DEMO_MODE) return filteredRows.value
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
  // focusField kept for future focus handling
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

    // If currently in highRisk tab, level change can affect visibility; refresh.
    if (activeTab.value === 'highRisk' || activeTab.value === 'history') {
      loadGroups()
      loadRows()
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
  // 跳转到BI可视化页面，传递车间和机器人参数
  const partNo = robot?.partNo || robot?.part_no || ''
  const groupKey = robot?.group || selectedGroup.value || ''
  // 跳转到alerts页面，带上参数
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

const loadRows = async () => {
  if (DEMO_MODE) return
  loading.value = true
  try {
    const tabMap = { highRisk: 'highRisk', all: 'all', history: 'history' }
    const params = {
      group: selectedGroup.value,
      tab: tabMap[activeTab.value] || 'highRisk',
      keyword: keyword.value || undefined,
      level: levelFilter.value || undefined,
      axisKeys: axisKeysFilter.value.length ? axisKeysFilter.value.join(',') : undefined,
      axisOk: axisStateFilter.value ? axisStateFilter.value === 'ok' : undefined,
      markMode: markMode.value || undefined,
      page: currentPage.value,
      page_size: pageSize.value
    }
    const data = await getRobotComponents(params)
    serverRows.value = data.results || data
    serverTotal.value = data.count ?? serverRows.value.length
  } catch (error) {
    if (error?.response?.status === 404 && typeof error.response?.data?.detail === 'string' && error.response.data.detail.includes('Invalid page')) {
      currentPage.value = 1
      return
    }
    throw error
  } finally {
    loading.value = false
  }
}

watch([selectedGroup, activeTab], () => {
  currentPage.value = 1
  if (!DEMO_MODE) loadRows()
})

watch(pageSize, () => {
  if (!DEMO_MODE) {
    currentPage.value = 1
    loadRows()
  }
})

watch(currentPage, () => {
  if (!DEMO_MODE) loadRows()
})

watch([keyword, levelFilter, axisKeysFilter, axisStateFilter, markMode], () => {
  if (!DEMO_MODE) {
    currentPage.value = 1
    loadRows()
  }
})

if (!DEMO_MODE) {
  loadGroups()
  loadRows()
}
</script>

<style scoped>
.robot-status {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-text {
  font-size: 16px;
  font-weight: 700;
}

.group-row {
  margin-bottom: 6px;
}

.group-tile {
  width: 100%;
  border: 1px solid var(--app-border);
  background: rgba(148, 163, 184, 0.06);
  border-radius: var(--app-radius);
  padding: 14px 14px 12px;
  cursor: pointer;
  text-align: left;
  transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
}

.group-tile:hover {
  transform: translateY(-2px);
  box-shadow: var(--app-shadow);
}

.group-tile.active {
  border-color: rgba(37, 99, 235, 0.35);
  background: rgba(37, 99, 235, 0.08);
}

.group-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 10px;
}

.group-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
}

.group-total {
  font-size: 22px;
  font-weight: 800;
  color: rgba(15, 23, 42, 0.8);
}

.group-meta {
  margin-top: 10px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  color: rgba(15, 23, 42, 0.65);
  font-size: 12px;
}

.meta-item {
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(15, 23, 42, 0.08);
}

.meta-risk {
  color: #b45309;
  border-color: rgba(245, 158, 11, 0.28);
  background: rgba(245, 158, 11, 0.12);
}

.filters {
  margin: 6px 0 14px;
}

.filters-right {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 10px;
}

.table-legend {
  display: flex;
  gap: 16px;
  align-items: center;
  margin: 4px 0 10px;
  color: rgba(15, 23, 42, 0.7);
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
  box-shadow: 0 0 0 2px rgba(15, 23, 42, 0.06);
}

.dot-button {
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.dot-button:focus-visible {
  outline: 2px solid rgba(37, 99, 235, 0.55);
  outline-offset: 2px;
  border-radius: 999px;
}

.dot-ok {
  background: #22c55e;
}

.dot-bad {
  background: #ef4444;
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

.detail {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.detail-checks {
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  padding: 14px;
  background: rgba(148, 163, 184, 0.06);
}

.detail-checks-title {
  font-weight: 800;
  margin-bottom: 12px;
  color: rgba(15, 23, 42, 0.84);
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
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.detail-check-key {
  font-weight: 900;
  width: 28px;
}

.detail-check-label {
  flex: 1;
  color: rgba(15, 23, 42, 0.7);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.edit-form :deep(.el-form-item) {
  margin-bottom: 14px;
}

.edit-form :deep(.el-input__wrapper),
.edit-form :deep(.el-select__wrapper),
.edit-form :deep(.el-textarea__inner) {
  border-radius: 12px;
}

.form-label {
  display: inline-flex;
  flex-direction: column;
  line-height: 1.1;
  gap: 3px;
}

.form-label-title {
  font-weight: 800;
  color: rgba(15, 23, 42, 0.86);
}

.form-label-hint {
  color: var(--app-muted);
  font-size: 12px;
  font-weight: 600;
}

.pager {
  margin-top: 16px;
  justify-content: center;
}

.low {
  color: #b91c1c;
  font-weight: 700;
}
</style>
