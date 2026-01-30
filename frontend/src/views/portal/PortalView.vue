<template>
  <div class="portal-viewport">
    <!-- 背景流光特效 -->
    <div class="ambient-background">
      <div class="nebula blue"></div>
      <div class="nebula gold"></div>
      <div class="breathing-line gold-1"></div>
      <div class="breathing-line gold-2"></div>
      <div class="scan-grid"></div>
    </div>

    <div class="layout-wrapper">
      <header class="portal-header entrance-slide-in">
      <div class="title-area">
        <h1>应用门户 <small>Application Portal</small></h1>
        <p class="subtitle">统一入口 · 快速检索 · 一键打开/复制</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="resetFilters" class="ios-btn btn-entrance">同步数据</el-button>
      </div>
    </header>

    <!-- KPI Stats -->
    <div class="kpi-grid">
      <div class="kpi-card ios-glass entrance-scale-up">
        <div class="border-glow gold-tint entrance-border-glow"></div>
        <div class="kpi-icon-box kpi-icon-entrance"><el-icon><Grid /></el-icon></div>
        <div class="kpi-content">
          <label>应用总数</label>
          <div class="main-value">{{ stats.total }} <small>TOTAL</small></div>
        </div>
      </div>
      <div class="kpi-card ios-glass entrance-scale-up-delay-1">
        <div class="border-glow gold-tint entrance-border-glow"></div>
        <div class="kpi-icon-box kpi-icon-entrance"><el-icon><Link /></el-icon></div>
        <div class="kpi-content">
          <label>Web 入口</label>
          <div class="main-value">{{ stats.web }} <small>WEB</small></div>
        </div>
      </div>
      <div class="kpi-card ios-glass entrance-scale-up-delay-2">
        <div class="border-glow gold-tint entrance-border-glow"></div>
        <div class="kpi-icon-box kpi-icon-entrance"><el-icon><Monitor /></el-icon></div>
        <div class="kpi-content">
          <label>非 Web</label>
          <div class="main-value">{{ stats.offline }} <small>OFFLINE</small></div>
        </div>
      </div>
      <div class="kpi-card ios-glass entrance-scale-up-delay-3">
        <div class="border-glow gold-tint entrance-border-glow"></div>
        <div class="kpi-icon-box kpi-icon-entrance"><el-icon><Warning /></el-icon></div>
        <div class="kpi-content">
          <label>待补充</label>
          <div class="main-value">{{ stats.pending }} <small>PENDING</small></div>
        </div>
      </div>
    </div>

    <!-- Filters Panel -->
    <div class="filters-panel ios-glass entrance-scale-up-delay-4">
      <div class="border-glow gold-tint entrance-border-glow"></div>
      <el-input
        v-model="query"
        placeholder="搜索应用名称 / 反馈人 / 范围 / 入口"
        clearable
        class="filter-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <div class="filter-row">
        <el-select
          v-model="scopeFilter"
          placeholder="范围"
          clearable
          filterable
          class="filter-select"
        >
          <el-option v-for="s in scopes" :key="s" :label="s" :value="s" />
        </el-select>

        <el-select
          v-model="reporterFilter"
          placeholder="反馈人"
          clearable
          filterable
          class="filter-select"
        >
          <el-option v-for="p in reporters" :key="p" :label="p" :value="p" />
        </el-select>

        <el-radio-group v-model="viewMode" class="view-toggle">
          <el-radio-button label="table">列表</el-radio-button>
          <el-radio-button label="cards">卡片</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- Apps List Card -->
    <section class="apps-list-section ios-glass entrance-scale-up-delay-4">
      <div class="border-glow gold-tint entrance-border-glow"></div>
      <div class="table-header">
        <span class="accent-bar"></span>
        <span>应用列表</span>
        <div style="flex: 1"></div>
        <el-tag class="body-count" type="info" effect="plain">
          {{ filteredApps.length }} / {{ apps.length }}
        </el-tag>
        <el-button @click="resetFilters" class="ios-btn">重置筛选</el-button>
      </div>

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

        <el-table v-else :data="filteredApps" stripe class="apps-table premium-table">
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
    </section>
    </div>
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

/* === iOS 风格基础布局与背景 === */
.portal-viewport {
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
.portal-header {
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

.portal-header h1 {
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

.portal-header h1 small {
  font-size: 14px;
  color: #ffaa00;
  margin-left: 10px;
  font-weight: 300;
  letter-spacing: 2px;
}

.subtitle {
  margin: 4px 0 0;
  color: #8899aa;
  font-size: 14px;
}

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
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin: 30px 0;
}

.kpi-card {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.kpi-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5), 0 0 15px rgba(255, 170, 0, 0.2);
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

/* === Filters Panel === */
.filters-panel {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-input {
  width: 100%;
}

:deep(.filter-input .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: none;
  padding: 8px 12px;
  min-height: 40px;
}

:deep(.filter-input .el-input__wrapper:hover) {
  border-color: rgba(255, 170, 0, 0.3);
}

:deep(.filter-input .el-input__wrapper.is-focus) {
  border-color: #ffaa00;
}

:deep(.filter-input .el-input__inner) {
  color: #fff;
  font-size: 13px;
  line-height: 24px;
}

:deep(.filter-input .el-input__prefix) {
  color: #8899aa;
}

:deep(.filter-input:focus-within .el-input__prefix) {
  color: #ffaa00;
}

.filter-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.filter-select {
  flex: 1;
  min-width: 0;
}

:deep(.filter-select .el-select__wrapper) {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: none;
  padding: 6px 12px;
}

:deep(.filter-select .el-select__wrapper:hover) {
  border-color: rgba(255, 170, 0, 0.3);
}

:deep(.filter-select .el-select__wrapper.is-focus) {
  border-color: #ffaa00;
}

:deep(.filter-select .el-select__selected-item) {
  color: #fff;
  font-size: 13px;
}

.view-toggle {
  flex-shrink: 0;
}

:deep(.view-toggle .el-radio-button__inner) {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #8899aa;
  padding: 6px 14px;
  font-size: 13px;
}

:deep(.view-toggle .el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: rgba(255, 170, 0, 0.2);
  border-color: #ffaa00;
  color: #ffaa00;
}

:deep(.view-toggle .el-radio-button__inner:hover) {
  color: #ffaa00;
}

/* === Apps List Section === */
.apps-list-section {
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

.body-count {
  font-weight: 500;
  margin-left: auto;
}

/* === Table === */
.apps-table :deep(.el-table) {
  --el-table-bg-color: rgba(6, 10, 18, 0.9);
  --el-table-tr-bg-color: rgba(8, 12, 20, 0.45);
  --el-table-row-hover-bg-color: rgba(255, 170, 0, 0.08);
  --el-table-header-bg-color: rgba(255, 255, 255, 0.04);
  --el-table-border-color: rgba(255, 255, 255, 0.06);
  color: #dbe6f5;
}

.apps-table :deep(.el-table__header th) {
  background: rgba(255, 255, 255, 0.04) !important;
  border-color: rgba(255, 255, 255, 0.06) !important;
  color: #8da0b7 !important;
  font-size: 10px;
  letter-spacing: 1.2px;
  font-weight: 600;
}

.apps-table :deep(.el-table__body tr) {
  background: rgba(8, 12, 20, 0.5) !important;
}

.apps-table :deep(.el-table__body tr.el-table__row--striped) {
  background: rgba(14, 20, 32, 0.65) !important;
}

.apps-table :deep(.el-table__body td) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.04) !important;
  background-color: transparent !important;
  color: #dbe6f5 !important;
}

.apps-table :deep(.el-table__row:hover td) {
  background: rgba(255, 170, 0, 0.08) !important;
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
  color: #8899aa;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
}

/* === Cards View === */
.cards {
  padding: 20px;
}

.app-card {
  height: 240px;
  margin-bottom: 16px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.app-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
  border-color: rgba(255, 170, 0, 0.3);
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
  color: #8899aa;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.app-name-text {
  font-size: 15px;
  font-weight: 700;
  color: #fff;
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
  color: #8899aa;
  font-weight: 500;
  flex-shrink: 0;
}

.meta-v {
  font-size: 13px;
  color: #b0c4d8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-entry {
  color: #8899aa;
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

/* Responsive */
@media (max-width: 1200px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .kpi-grid { grid-template-columns: 1fr; }
  .filter-row { flex-wrap: wrap; }
  .filter-select { min-width: calc(50% - 5px); }
  .view-toggle { width: 100%; }
  :deep(.view-toggle .el-radio-button) { flex: 1; }
}
</style>

<!-- 全局样式：统一 Tag 样式 -->
<style>
.el-tag {
  border-radius: 6px !important;
  border: none !important;
  padding: 0 8px !important;
  height: 22px !important;
  line-height: 22px !important;
}

.el-tag--success { background: rgba(34, 197, 94, 0.15) !important; color: #4ade80 !important; }
.el-tag--warning { background: rgba(255, 170, 0, 0.15) !important; color: #ffaa00 !important; }
.el-tag--danger { background: rgba(239, 68, 68, 0.15) !important; color: #f87171 !important; }
.el-tag--info { background: rgba(255, 255, 255, 0.1) !important; color: #94a3b8 !important; }
</style>
