<template>
  <div class="portal-viewport">
    <header class="portal-header">
      <div class="title-area">
        <h1>应用门户 <small>Application Portal</small></h1>
        <p class="subtitle">统一入口 · 快速检索 · 一键打开/复制</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" circle @click="resetFilters" class="refresh-btn"></el-button>
      </div>
    </header>

    <!-- KPI Stats -->
    <div class="kpi-grid">
      <div class="kpi-card glass-card">
        <div class="kpi-icon total"><el-icon><Grid /></el-icon></div>
        <div class="kpi-info">
          <label>应用总数</label>
          <div class="value">{{ stats.total }}</div>
        </div>
      </div>
      <div class="kpi-card glass-card primary">
        <div class="kpi-icon web"><el-icon><Link /></el-icon></div>
        <div class="kpi-info">
          <label>Web 入口</label>
          <div class="value">{{ stats.web }}</div>
        </div>
      </div>
      <div class="kpi-card glass-card warning">
        <div class="kpi-icon offline"><el-icon><Monitor /></el-icon></div>
        <div class="kpi-info">
          <label>非 Web</label>
          <div class="value">{{ stats.offline }}</div>
        </div>
      </div>
      <div class="kpi-card glass-card muted">
        <div class="kpi-icon pending"><el-icon><Warning /></el-icon></div>
        <div class="kpi-info">
          <label>待补充</label>
          <div class="value">{{ stats.pending }}</div>
        </div>
      </div>
    </div>

    <!-- Filters Panel -->
    <div class="filters-panel glass-card">
      <el-input
        v-model="query"
        placeholder="搜索：应用名称 / 反馈人 / 范围 / 入口"
        clearable
        class="filter-search styled-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select
        v-model="scopeFilter"
        placeholder="范围"
        clearable
        filterable
        class="styled-select"
      >
        <el-option v-for="s in scopes" :key="s" :label="s" :value="s" />
      </el-select>

      <el-select
        v-model="reporterFilter"
        placeholder="反馈人"
        clearable
        filterable
        class="styled-select"
      >
        <el-option v-for="p in reporters" :key="p" :label="p" :value="p" />
      </el-select>

      <el-radio-group v-model="viewMode" class="view-toggle">
        <el-radio-button label="table">
          <el-icon><List /></el-icon>
        </el-radio-button>
        <el-radio-button label="cards">
          <el-icon><Grid /></el-icon>
        </el-radio-button>
      </el-radio-group>
    </div>

    <!-- Apps List Card -->
    <el-card class="apps-list-card styled-card">
      <template #header>
        <div class="body-header">
          <div class="body-title">
            <span>应用列表</span>
            <el-tag class="body-count" type="info" effect="plain">
              {{ filteredApps.length }} / {{ apps.length }}
            </el-tag>
          </div>
          <div class="body-actions">
            <el-button @click="resetFilters">重置筛选</el-button>
          </div>
        </div>
      </template>

      <el-empty v-if="!filteredApps.length" description="无匹配结果" />

      <div v-else>
        <div v-if="viewMode === 'cards'" class="cards">
          <el-row :gutter="16">
            <el-col
              v-for="app in filteredApps"
              :key="app.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="8"
            >
              <el-card class="app-card" shadow="hover">
                <div class="app-card-top">
                  <div class="app-name">
                    <span class="app-id">#{{ app.id }}</span>
                    <span class="app-name-text">{{ app.name }}</span>
                  </div>
                  <el-tag :type="entryBadge(app).type" effect="plain">
                    {{ entryBadge(app).label }}
                  </el-tag>
                </div>

                <div class="app-meta">
                  <div class="meta-row">
                    <span class="meta-k">反馈人</span>
                    <span class="meta-v">{{ app.reporter || '-' }}</span>
                  </div>
                  <div class="meta-row">
                    <span class="meta-k">范围</span>
                    <span class="meta-v">{{ app.scope || '-' }}</span>
                  </div>
                  <div class="meta-row">
                    <span class="meta-k">入口</span>
                    <span class="meta-v meta-entry">{{ app.entry || '待补充' }}</span>
                  </div>
                </div>

                <div class="app-actions">
                  <el-button
                    type="primary"
                    :disabled="!isWebUrl(app.entry)"
                    @click="openEntry(app)"
                  >
                    <el-icon><Link /></el-icon>
                    打开
                  </el-button>
                  <el-button
                    :disabled="!app.entry"
                    @click="copyEntry(app)"
                  >
                    <el-icon><CopyDocument /></el-icon>
                    复制入口
                  </el-button>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <el-table v-else :data="filteredApps" stripe class="apps-table">
          <el-table-column prop="id" label="序号" width="72" align="center" />
          <el-table-column prop="name" label="PDM应用名称" min-width="190" show-overflow-tooltip />
          <el-table-column prop="reporter" label="反馈人" width="100" />
          <el-table-column prop="scope" label="当前应用范围" min-width="150" show-overflow-tooltip />
          <el-table-column label="入口" min-width="320">
            <template #default="{ row }">
              <div class="entry-cell">
                <el-tag :type="entryBadge(row).type" effect="plain" class="entry-tag">
                  {{ entryBadge(row).label }}
                </el-tag>
                <span class="entry-text" :title="row.entry || '待补充'">{{ row.entry || '待补充' }}</span>
                <el-button
                  size="small"
                  type="primary"
                  :disabled="!isWebUrl(row.entry)"
                  @click="openEntry(row)"
                >
                  打开
                </el-button>
                <el-button
                  size="small"
                  :disabled="!row.entry"
                  @click="copyEntry(row)"
                >
                  复制
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument, Link, Search, Refresh, Grid, Monitor, Warning, List } from '@element-plus/icons-vue'
import { PDM_APPS } from '@/views/portal/pdmApps'

const apps = ref(PDM_APPS)
const query = ref('')
const scopeFilter = ref('')
const reporterFilter = ref('')
const viewMode = ref('table')

const normalize = (value) => String(value || '').trim().toLowerCase()

const isWebUrl = (value) => {
  const v = String(value || '').trim()
  return /^https?:\/\//i.test(v)
}

const entryBadge = (app) => {
  const entry = String(app?.entry || '').trim()
  if (isWebUrl(entry)) return { label: 'Web', type: 'success' }
  if (!entry) return { label: '待补充', type: 'info' }
  if (entry.includes('exe')) return { label: 'EXE', type: 'warning' }
  if (entry.includes('服务器')) return { label: '服务器+PC', type: 'warning' }
  if (entry.toLowerCase().includes('power bi') || entry.includes('Power BI')) return { label: 'Power BI', type: 'success' }
  if (entry.includes('开发中')) return { label: '开发中', type: 'info' }
  return { label: '其它', type: 'info' }
}

const scopes = computed(() => {
  const set = new Set(apps.value.map((a) => a.scope).filter(Boolean))
  return Array.from(set).sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'))
})

const reporters = computed(() => {
  const set = new Set(apps.value.map((a) => a.reporter).filter(Boolean))
  return Array.from(set).sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'))
})

const filteredApps = computed(() => {
  const q = normalize(query.value)
  return apps.value.filter((app) => {
    if (scopeFilter.value && app.scope !== scopeFilter.value) return false
    if (reporterFilter.value && app.reporter !== reporterFilter.value) return false
    if (!q) return true
    const haystack = normalize([app.id, app.name, app.reporter, app.scope, app.entry].join(' '))
    return haystack.includes(q)
  })
})

const stats = computed(() => {
  const rows = apps.value
  const web = rows.filter((a) => isWebUrl(a.entry)).length
  const offline = rows.filter((a) => a.entry && !isWebUrl(a.entry)).length
  const pending = rows.filter((a) => !String(a.entry || '').trim()).length
  return { total: rows.length, web, offline, pending }
})

const openEntry = (app) => {
  const url = String(app?.entry || '').trim()
  if (!isWebUrl(url)) {
    ElMessage.warning('该应用入口非 Web 链接（或尚未补充）')
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}

const copyText = async (text) => {
  const value = String(text || '')
  if (!value) return false
  if (navigator?.clipboard?.writeText) {
    await navigator.clipboard.writeText(value)
    return true
  }
  const textarea = document.createElement('textarea')
  textarea.value = value
  textarea.setAttribute('readonly', 'true')
  textarea.style.position = 'fixed'
  textarea.style.top = '-9999px'
  document.body.appendChild(textarea)
  textarea.select()
  const ok = document.execCommand('copy')
  document.body.removeChild(textarea)
  return ok
}

const copyEntry = async (app) => {
  const value = String(app?.entry || '').trim()
  if (!value) {
    ElMessage.warning('暂无可复制的入口')
    return
  }
  try {
    const ok = await copyText(value)
    if (ok) ElMessage.success('已复制入口')
    else ElMessage.error('复制失败')
  } catch {
    ElMessage.error('复制失败')
  }
}

const resetFilters = () => {
  query.value = ''
  scopeFilter.value = ''
  reporterFilter.value = ''
}
</script>

<style scoped>
/* Viewport */
.portal-viewport {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  background-color: #f8fafc;
  min-height: calc(100vh - 100px);
  color: #1e293b;
}

/* Header - 参考Dashboard样式 */
.portal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.portal-header h1 {
  font-size: 28px;
  font-weight: 800;
  margin: 0;
  background: linear-gradient(135deg, #1e293b 0%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.portal-header h1 small {
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

/* KPI Cards - 参考Dashboard玻璃态样式 */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.glass-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 20px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.glass-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 30px -10px rgba(0, 0, 0, 0.1);
}

.kpi-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.kpi-icon.total { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
.kpi-icon.web { background: rgba(16, 185, 129, 0.1); color: #10b981; }
.kpi-icon.offline { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
.kpi-icon.pending { background: rgba(148, 163, 184, 0.1); color: #64748b; }

.kpi-info label {
  display: block;
  font-size: 13px;
  color: #64748b;
  margin-bottom: 4px;
}

.kpi-info .value {
  font-size: 24px;
  font-weight: 800;
  color: #1e293b;
}

/* Filters Panel */
.filters-panel {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-search {
  flex: 1;
  min-width: 280px;
}

.styled-input :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  background: #fff;
}

.styled-input :deep(.el-input__wrapper:hover) {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.styled-input :deep(.el-input__wrapper.is-focus) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.styled-select {
  width: 160px;
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

.view-toggle :deep(.el-radio-button__inner) {
  border-radius: 12px;
  padding: 8px 16px;
}

/* Apps List Card */
.styled-card {
  border-radius: 20px;
  border: none;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
}

.apps-list-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
}

.body-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.body-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 700;
  color: #334155;
}

.body-count {
  font-weight: 500;
}

/* Cards View */
.cards {
  padding-top: 4px;
}

.app-card {
  height: 240px;
  margin-bottom: 16px;
  border-radius: 16px;
  border: 1px solid #f1f5f9;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.app-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}

.app-card :deep(.el-card__body) {
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
}

.app-name {
  display: flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.app-id {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.app-name-text {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-meta {
  margin-top: 12px;
  display: grid;
  gap: 8px;
  flex: 1;
  overflow: hidden;
}

.meta-row {
  display: grid;
  grid-template-columns: 54px 1fr;
  gap: 10px;
  align-items: start;
}

.meta-k {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  flex-shrink: 0;
}

.meta-v {
  font-size: 13px;
  color: #475569;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-entry {
  color: #94a3b8;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
}

.app-actions {
  margin-top: auto;
  padding-top: 12px;
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.app-actions .el-button {
  border-radius: 10px;
  font-weight: 500;
  flex: 1;
}

/* Table View */
.apps-table :deep(.el-table__header-wrapper) {
  border-radius: 12px 12px 0 0;
}

.apps-table :deep(.el-table th) {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
}

.apps-table .entry-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.apps-table .entry-tag {
  flex: 0 0 auto;
}

.apps-table .entry-text {
  flex: 1 1 auto;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: #64748b;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
}

/* Responsive */
@media (max-width: 1200px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .kpi-grid { grid-template-columns: 1fr; }
  .filters-panel { flex-direction: column; align-items: stretch; }
  .filter-search, .styled-select { width: 100%; }
}
</style>
