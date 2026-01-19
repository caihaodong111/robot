<template>
  <div class="portal">
    <el-card class="portal-hero">
      <div class="hero-top">
        <div class="hero-title">
          <div class="hero-title-main">PDM 应用门户</div>
          <div class="hero-title-sub">统一入口 · 快速检索 · 一键打开/复制</div>
        </div>
        <div class="hero-stats">
          <div class="stat">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">应用总数</div>
          </div>
          <div class="stat">
            <div class="stat-value">{{ stats.web }}</div>
            <div class="stat-label">Web 入口</div>
          </div>
          <div class="stat">
            <div class="stat-value">{{ stats.offline }}</div>
            <div class="stat-label">非 Web</div>
          </div>
          <div class="stat">
            <div class="stat-value">{{ stats.pending }}</div>
            <div class="stat-label">待补充</div>
          </div>
        </div>
      </div>

      <div class="hero-filters">
        <el-input
          v-model="query"
          placeholder="搜索：应用名称 / 反馈人 / 范围 / 入口"
          clearable
          class="filter-item filter-search"
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
          class="filter-item"
        >
          <el-option v-for="s in scopes" :key="s" :label="s" :value="s" />
        </el-select>

        <el-select
          v-model="reporterFilter"
          placeholder="反馈人"
          clearable
          filterable
          class="filter-item"
        >
          <el-option v-for="p in reporters" :key="p" :label="p" :value="p" />
        </el-select>

        <el-radio-group v-model="viewMode" class="filter-item">
          <el-radio-button label="table">表格</el-radio-button>
          <el-radio-button label="cards">卡片</el-radio-button>
        </el-radio-group>
      </div>
    </el-card>

    <el-card class="portal-body">
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
import { CopyDocument, Link, Search } from '@element-plus/icons-vue'
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
.portal {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.portal-hero {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.10), rgba(99, 102, 241, 0.08));
  border: 1px solid rgba(37, 99, 235, 0.12);
}

.hero-top {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
}

.hero-title-main {
  font-size: 18px;
  font-weight: 700;
  color: rgba(15, 23, 42, 0.92);
}

.hero-title-sub {
  margin-top: 6px;
  font-size: 13px;
  color: rgba(15, 23, 42, 0.60);
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(90px, 1fr));
  gap: 10px;
}

.stat {
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 10px;
  padding: 10px 12px;
  min-width: 90px;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: rgba(15, 23, 42, 0.92);
  line-height: 1.2;
}

.stat-label {
  margin-top: 2px;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.60);
}

.hero-filters {
  margin-top: 16px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.filter-item {
  width: 180px;
}

.filter-search {
  flex: 1;
  min-width: 280px;
}

.portal-body :deep(.el-card__header) {
  padding: 12px 16px;
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
  font-weight: 600;
}

.body-count {
  font-weight: 500;
}

.cards {
  padding-top: 4px;
}

.app-card {
  margin-bottom: 16px;
  border-radius: 12px;
}

.app-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.app-name {
  display: flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
}

.app-id {
  color: rgba(15, 23, 42, 0.45);
  font-size: 12px;
  font-weight: 600;
}

.app-name-text {
  font-size: 15px;
  font-weight: 700;
  color: rgba(15, 23, 42, 0.90);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-meta {
  margin-top: 12px;
  display: grid;
  gap: 8px;
}

.meta-row {
  display: grid;
  grid-template-columns: 54px 1fr;
  gap: 10px;
  align-items: start;
}

.meta-k {
  font-size: 12px;
  color: rgba(15, 23, 42, 0.55);
}

.meta-v {
  font-size: 13px;
  color: rgba(15, 23, 42, 0.86);
  word-break: break-word;
}

.meta-entry {
  color: rgba(15, 23, 42, 0.72);
}

.app-actions {
  margin-top: 14px;
  display: flex;
  gap: 10px;
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
  color: rgba(15, 23, 42, 0.75);
}

@media (max-width: 960px) {
  .hero-top {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-stats {
    grid-template-columns: repeat(2, minmax(90px, 1fr));
  }
}
</style>
