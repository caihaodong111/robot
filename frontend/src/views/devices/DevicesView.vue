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
          <el-button
            :icon="Refresh"
            @click="handleRefresh"
            :loading="syncing"
            :disabled="syncing"
            class="ios-btn btn-entrance"
          >
            {{ syncing ? '同步中...' : '同步数据' }}
          </el-button>
          <span class="last-sync-time" :class="{ 'syncing': syncing }">
            <el-icon><Clock /></el-icon>
            {{ syncing ? '正在同步...' : lastSyncTimeText }}
          </span>
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
              <el-select v-model="levelFilter" placeholder="等级(level)" multiple collapse-tags collapse-tags-tooltip clearable class="dark-select">
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

        <!-- Table -->
        <el-table :data="pagedRows" class="status-table table-entrance" stripe height="520" v-loading="loading">
          <!-- 基础列（所有标签页通用） -->
          <el-table-column prop="partNo" label="robot" width="160" class-name="robot-column" sortable :sort-by="(row) => row.partNo || row.robot || ''">
            <template #default="{ row }">
              <el-button type="primary" link class="mono robot-name-cell" @click="openBI(row)">
                {{ row.partNo || row.robot }}
              </el-button>
            </template>
          </el-table-column>
          <el-table-column label="reference" width="200" sortable :sort-by="(row) => row.referenceNo || row.reference || ''">
            <template #default="{ row }">
              <template v-if="activeTab === 'history'">
                <span class="mono">{{ row.referenceNo || row.reference }}</span>
              </template>
              <el-button v-else type="primary" link class="mono" @click="openEdit(row, 'referenceNo')">
                {{ row.referenceNo || row.reference }}
              </el-button>
            </template>
          </el-table-column>
          <el-table-column prop="number" label="number" width="90" align="center" sortable>
            <template #default="{ row }">
              <template v-if="activeTab === 'history'">
                <span class="mono">{{ row.number ?? 0 }}</span>
              </template>
              <el-button v-else type="primary" link class="mono" @click="openEdit(row, 'number')">
                {{ row.number ?? 0 }}
              </el-button>
            </template>
          </el-table-column>
          <el-table-column prop="typeSpec" label="type" width="120" sortable :sort-by="(row) => row.typeSpec || row.type || ''">
            <template #default="{ row }">
              <span>{{ row.typeSpec || row.type }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="tech" label="tech" width="120" sortable />

          <!-- all 标签页的详细列 -->
          <template v-if="activeTab === 'all'">
            <el-table-column prop="mark" label="mark" width="80" align="center" sortable>
              <template #default="{ row }">
                <el-button type="primary" link class="mono" @click="openEdit(row, 'mark')">
                  {{ row.mark ?? 0 }}
                </el-button>
              </template>
            </el-table-column>
            <el-table-column label="remark" width="150" sortable :sort-by="(row) => row.remark || ''">
              <template #default="{ row }">
                <el-button type="primary" link class="remark-link" @click="openEdit(row, 'remark')">
                  {{ row.remark || '-' }}
                </el-button>
              </template>
            </el-table-column>
            <el-table-column prop="error1_c1" label="error1_c1" width="100" align="center" sortable>
              <template #default="{ row }">
                <span class="mono">{{ formatNumber(row.error1_c1) }}</span>
              </template>
            </el-table-column>
            <!-- 温度列 tem1_m - tem7_m -->
            <el-table-column
              v-for="i in 7"
              :key="`tem${i}_m`"
              :prop="`tem${i}_m`"
              :label="`tem${i}_m`"
              width="80"
              align="center"
              sortable
            >
              <template #default="{ row }">
                <span class="mono">{{ formatNumber(row[`tem${i}_m`]) }}</span>
              </template>
            </el-table-column>
            <!-- A1-A7 错误率列 A1_e_rate - A7_e_rate -->
            <el-table-column
              v-for="i in 7"
              :key="`a${i}_e_rate`"
              :prop="`a${i}_e_rate`"
              :label="`A${i}_e_rate`"
              width="90"
              align="center"
              sortable
            >
              <template #default="{ row }">
                <span class="mono">{{ formatNumber(row[`a${i}_e_rate`]) }}</span>
              </template>
            </el-table-column>
            <!-- A1-A7 Rms列 A1_Rms - A7_Rms -->
            <el-table-column
              v-for="i in 7"
              :key="`a${i}_rms`"
              :prop="`a${i}_rms`"
              :label="`A${i}_Rms`"
              width="85"
              align="center"
              sortable
            >
              <template #default="{ row }">
                <span class="mono">{{ formatNumber(row[`a${i}_rms`]) }}</span>
              </template>
            </el-table-column>
            <!-- A1-A7 E列 A1_E - A7_E -->
            <el-table-column
              v-for="i in 7"
              :key="`a${i}_e`"
              :prop="`a${i}_e`"
              :label="`A${i}_E`"
              width="75"
              align="center"
              sortable
            >
              <template #default="{ row }">
                <span class="mono">{{ formatNumber(row[`a${i}_e`]) }}</span>
              </template>
            </el-table-column>
            <!-- Q1-Q7列 -->
            <el-table-column
              v-for="i in 7"
              :key="`q${i}`"
              :prop="`q${i}`"
              :label="`Q${i}`"
              width="65"
              align="center"
              sortable
            >
              <template #default="{ row }">
                <span class="mono">{{ formatNumber(row[`q${i}`]) }}</span>
              </template>
            </el-table-column>
            <!-- Curr_A1_max - Curr_A7_max -->
            <el-table-column
              v-for="i in 7"
              :key="`curr_a${i}_max`"
              :prop="`curr_a${i}_max`"
              :label="`Curr_A${i}_max`"
              width="100"
              align="center"
              sortable
            >
              <template #default="{ row }">
                <span class="mono">{{ formatNumber(row[`curr_a${i}_max`]) }}</span>
              </template>
            </el-table-column>
            <!-- Curr_A1_min - Curr_A7_min -->
            <el-table-column
              v-for="i in 7"
              :key="`curr_a${i}_min`"
              :prop="`curr_a${i}_min`"
              :label="`Curr_A${i}_min`"
              width="100"
              align="center"
              sortable
            >
              <template #default="{ row }">
                <span class="mono">{{ formatNumber(row[`curr_a${i}_min`]) }}</span>
              </template>
            </el-table-column>
            <!-- A1-A7列 -->
            <el-table-column
              v-for="i in 7"
              :key="`a${i}`"
              :label="`A${i}`"
              width="65"
              align="center"
              :sort-by="(row) => row[`A${i}`] ?? row[`a${i}`] ?? ''"
            >
              <template #default="{ row }">
                <el-tooltip
                  :content="`A${i}: ${getAxisStatusText(row, i)}`"
                  placement="top"
                  :show-after="120"
                >
                  <span
                    class="dot clickable-dot"
                    :class="isAxisHigh(row, i) ? 'dot-bad' : 'dot-ok'"
                    @click="openErrorTrendChart(row, `A${i}`)"
                  ></span>
                </el-tooltip>
              </template>
            </el-table-column>
            <!-- P_Change -->
            <el-table-column prop="p_change" label="P_Change" width="95" align="center" sortable>
              <template #default="{ row }">
                <span class="mono">{{ formatNumber(row.p_change) }}</span>
              </template>
            </el-table-column>
            <!-- level -->
            <el-table-column prop="level" label="level" width="75" align="center" sortable>
              <template #default="{ row }">
                <el-tag :type="levelTagType(row.level)" effect="light">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <!-- 更新时间 -->
            <el-table-column label="更新时间" width="180" sortable :sort-by="(row) => getUpdatedAtSortValue(row)">
              <template #default="{ row }">
                <span class="mono">{{ getUpdatedAtText(row) }}</span>
              </template>
            </el-table-column>
          </template>

          <!-- highRisk 和 history 标签页的列 -->
          <template v-else>
            <el-table-column prop="mark" label="mark" width="80" align="center" sortable>
              <template #default="{ row }">
                <template v-if="activeTab === 'history'">
                  <span class="mono">{{ row.mark ?? 0 }}</span>
                </template>
                <el-button v-else type="primary" link class="mono" @click="openEdit(row, 'mark')">
                  {{ row.mark ?? 0 }}
                </el-button>
              </template>
            </el-table-column>
            <el-table-column label="remark" width="200" sortable :sort-by="(row) => row.remark || ''">
              <template #default="{ row }">
                <template v-if="activeTab === 'history'">
                  <span class="remark-link">{{ row.remark || '-' }}</span>
                </template>
                <el-button v-else type="primary" link class="remark-link" @click="openEdit(row, 'remark')">
                  {{ row.remark || '-' }}
                </el-button>
              </template>
            </el-table-column>

            <el-table-column
              v-for="key in CHECK_KEYS"
              :key="key"
              :label="key"
              width="60"
              align="center"
              :sort-by="(row) => row[key] ?? row[key.toLowerCase()] ?? ''"
            >
              <template #default="{ row }">
                <el-tooltip
                  :content="getAxisTooltipText(row, key)"
                  placement="top"
                  :show-after="120"
                >
                  <span
                    class="dot clickable-dot"
                    :class="isCheckHigh(row, key) ? 'dot-bad' : 'dot-ok'"
                    @click="openErrorTrendChart(row, key)"
                  ></span>
                </el-tooltip>
              </template>
            </el-table-column>

            <el-table-column prop="level" label="level" width="80" align="center" sortable>
              <template #default="{ row }">
                <el-button type="primary" link @click="openEdit(row, 'level')">
                  <el-tag :type="levelTagType(row.level)" effect="light">{{ row.level }}</el-tag>
                </el-button>
              </template>
            </el-table-column>
            <!-- 更新时间 -->
            <el-table-column label="更新时间" width="180" sortable :sort-by="(row) => getUpdatedAtSortValue(row)">
              <template #default="{ row }">
                <span class="mono">{{ getUpdatedAtText(row) }}</span>
              </template>
            </el-table-column>
          </template>
        </el-table>

        <!-- Pagination -->
        <div class="pagination-wrapper">
          <div class="pagination-info">
            <span class="pagination-total">共 {{ serverTotal }} 条</span>
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
    <el-dialog v-model="detailVisible" title="Details" width="760px" class="dark-dialog">
      <div v-if="detailRobot" class="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="robot"><span class="mono">{{ detailRobot.partNo }}</span></el-descriptions-item>
          <el-descriptions-item label="reference"><span class="mono">{{ detailRobot.referenceNo || detailRobot.reference || '-' }}</span></el-descriptions-item>
          <el-descriptions-item label="number"><span class="mono">{{ detailRobot.number ?? 0 }}</span></el-descriptions-item>
          <el-descriptions-item label="type">{{ detailRobot.typeSpec }}</el-descriptions-item>
          <el-descriptions-item label="tech">{{ detailRobot.tech }}</el-descriptions-item>
          <el-descriptions-item label="mark"><span class="mono">{{ detailRobot.mark ?? 0 }}</span></el-descriptions-item>
          <el-descriptions-item label="level">
            <el-tag :type="levelTagType(detailRobot.level)" effect="light">{{ detailRobot.level }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="remark" :span="2">{{ detailRobot.remark }}</el-descriptions-item>
        </el-descriptions>

        <div class="detail-checks">
          <div class="detail-checks-title">A1-A7 Checks</div>
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
        <el-button @click="detailVisible = false">Close</el-button>
      </template>
    </el-dialog>

    <!-- Edit Dialog -->
    <el-dialog v-model="editVisible" title="Edit" width="560px" class="dark-dialog">
      <el-form v-if="editTarget" :model="editForm" label-position="top" class="edit-form">
        <el-row :gutter="14">
          <el-col :span="18">
            <el-form-item>
              <template #label>
                <span class="form-label">
                  <span class="form-label-row">
                    <span class="form-label-title">reference</span>
                    <el-button
                      class="reference-refresh-button"
                      type="primary"
                      link
                      :icon="Refresh"
                      :loading="referenceRefreshing"
                      @click="refreshReferenceOptions"
                    />
                  </span>
                </span>
              </template>
              <div class="reference-select-row">
                <el-select
                  v-model="editForm.referenceNo"
                  class="reference-select"
                  placeholder="Select reference"
                  :loading="referenceLoading"
                  :disabled="referenceRefreshing"
                  @change="handleReferenceChange"
                >
                  <el-option v-for="item in referenceOptions" :key="item" :label="item" :value="item" />
                </el-select>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item>
              <template #label>
                <span class="form-label">
                  <span class="form-label-title">number</span>
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
                  <span class="form-label-title">mark</span>
                </span>
              </template>
              <el-input-number v-model="editForm.mark" :min="0" :max="999999" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item>
              <template #label>
                <span class="form-label">
                  <span class="form-label-title">level</span>
                </span>
              </template>
              <el-select v-model="editForm.level" placeholder="Select level" style="width: 100%">
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
              <span class="form-label-title">remark</span>
            </span>
          </template>
          <el-input v-model="editForm.remark" type="textarea" :rows="4" placeholder="Enter remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">Cancel</el-button>
        <el-button type="primary" :loading="editSaving" @click="saveEdit">Save</el-button>
      </template>
    </el-dialog>

    <!-- Edit Authentication Login Dialog -->
    <el-dialog v-model="loginVisible" title="编辑验证" width="420px" class="dark-dialog" :close-on-click-modal="false">
      <div class="login-dialog-content">
        <p class="login-hint">要编辑机器人数据，请先登录验证</p>
        <el-form :model="loginForm" label-position="top" class="login-form">
          <el-form-item label="用户名">
            <el-input v-model="loginForm.username" placeholder="请输入用户名" @keyup.enter="handleLogin" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password @keyup.enter="handleLogin" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="cancelLogin">取消</el-button>
        <el-button type="primary" :loading="loggingIn" @click="handleLogin">登录</el-button>
      </template>
    </el-dialog>

    <!-- Error Trend Chart Dialog -->
    <el-dialog
      v-model="chartDialogVisible"
      :title="`${chartDialogData.robotPartNo} - ${chartDialogData.axisName} Error Rate Trend Chart`"
      width="900px"
      center
      class="dark-dialog chart-dialog"
    >
      <div v-loading="chartDialogLoading" class="chart-dialog-content">
        <div v-if="chartDialogData.chartUrl" class="chart-image-wrapper">
          <img :src="chartDialogData.chartUrl" :alt="`${chartDialogData.axisName} Error Rate Trend Chart`" class="chart-image" />
        </div>
        <div v-else-if="!chartDialogLoading" class="chart-placeholder">
          <el-icon :size="48"><Picture /></el-icon>
          <p>No chart data available</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="chartDialogVisible = false">Close</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Refresh, Search, Close, Monitor, ArrowRight, ArrowLeft, Picture, Clock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getRobotComponents, getRobotGroups, updateRobotComponent, getErrorTrendChart, importRobotComponents, getHighRiskHistories, getReferenceDict, refreshReferenceDict, getReferenceDictRefreshStatus, resolveReferenceNumber, verifyEditCredentials, getEditAuthStatus } from '@/api/robots'
import request from '@/utils/request'

const router = useRouter()
const route = useRoute()

const CHECK_KEYS = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7']
const referenceOptions = ref([])
const referenceLoading = ref(false)
const referenceRefreshing = ref(false)

const drawerVisible = ref(false)

// 同步状态
const syncing = ref(false)
const lastSyncTime = ref(null)

// 排除的车间 key 列表（与后端保持一致）
const EXCLUDED_GROUP_KEYS = ['', '(空)', 'MRA1 BS', '未分配']

const normalizeGroupName = (group) => {
  if (!group) return group
  if (group.name === 'SA1' || group.key === 'SA1') {
    return { ...group, name: 'AS1' }
  }
  return group
}

// 优先使用 URL query 参数中的 group，否则使用第一个车间
const getInitialGroup = () => {
  const queryGroup = route.query.group
  if (queryGroup) {
    // 如果 URL 有 group 参数，返回空字符串等待数据加载
    return ''
  }
  return '' // 等待数据加载后使用第一个车间
}
const selectedGroup = ref(getInitialGroup())
const activeTab = ref('highRisk')
const keyword = ref('')
const levelFilter = ref([])
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

// 编辑认证相关状态
const isEditAuthenticated = ref(false)
const editSessionVersion = ref(null) // 存储会话版本号
const loginVisible = ref(false)
const loggingIn = ref(false)
const loginForm = ref({
  username: '',
  password: ''
})
const pendingEditData = ref(null) // 存储待处理的编辑操作

// localStorage key
const EDIT_AUTH_KEY = 'edit_auth_version'

// 从 localStorage 恢复登录状态
const restoreAuthState = () => {
  try {
    const stored = localStorage.getItem(EDIT_AUTH_KEY)
    if (stored) {
      const data = JSON.parse(stored)
      editSessionVersion.value = data.version
      // 检查会话是否仍然有效
      checkEditAuthStatus()
    }
  } catch (e) {
    console.error('Failed to restore auth state:', e)
  }
}

// 保存登录状态到 localStorage
const saveAuthState = (version) => {
  try {
    localStorage.setItem(EDIT_AUTH_KEY, JSON.stringify({
      version: version,
      timestamp: new Date().toISOString()
    }))
    editSessionVersion.value = version
  } catch (e) {
    console.error('Failed to save auth state:', e)
  }
}

// 清除登录状态
const clearAuthState = () => {
  try {
    localStorage.removeItem(EDIT_AUTH_KEY)
    editSessionVersion.value = null
    isEditAuthenticated.value = false
  } catch (e) {
    console.error('Failed to clear auth state:', e)
  }
}

// 检查编辑认证状态（版本是否有效）
const checkEditAuthStatus = async () => {
  if (!editSessionVersion.value) {
    isEditAuthenticated.value = false
    return
  }

  try {
    const result = await getEditAuthStatus({ version: editSessionVersion.value })
    if (result.valid) {
      isEditAuthenticated.value = true
    } else {
      // 会话失效，清除本地状态
      clearAuthState()
    }
  } catch (e) {
    console.error('Failed to check auth status:', e)
    // 请求失败时不做处理，保持当前状态
  }
}

const loadReferenceOptions = async (robot) => {
  if (!robot) {
    referenceOptions.value = []
    return
  }
  referenceLoading.value = true
  try {
    const response = await getReferenceDict({ robot })
    const results = response?.results || response || []
    referenceOptions.value = results.map((item) => item.reference).filter(Boolean)
  } catch (error) {
    console.error('加载reference字典失败:', error)
    referenceOptions.value = []
  } finally {
    referenceLoading.value = false
  }
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const waitForReferenceRefresh = async (taskId) => {
  const maxAttempts = 30
  const intervalMs = 2000
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const status = await getReferenceDictRefreshStatus({ task_id: taskId })
    const state = (status?.status || '').toLowerCase()
    if (state === 'success') return status.result || {}
    if (state === 'failed') {
      throw new Error(status?.error || status?.result?.error || '刷新失败')
    }
    await sleep(intervalMs)
  }
  throw new Error('刷新超时，请稍后重试')
}

const refreshReferenceOptions = async () => {
  if (!editTarget.value?.robot) {
    ElMessage.warning('未找到机器人编号，无法刷新')
    return
  }
  referenceRefreshing.value = true
  try {
    const start = await refreshReferenceDict()
    const taskId = start?.task_id
    if (!taskId) {
      throw new Error('未获取任务ID')
    }
    await waitForReferenceRefresh(taskId)
    await loadReferenceOptions(editTarget.value.robot)
    ElMessage.success('reference字典已刷新')
  } catch (error) {
    ElMessage.error(error?.response?.data?.error || error?.message || '刷新失败')
  } finally {
    referenceRefreshing.value = false
  }
}

// 错误率趋势图弹窗相关状态
const chartDialogVisible = ref(false)
const chartDialogLoading = ref(false)
const chartDialogData = ref({
  robot: null,
  robotPartNo: '',
  axisName: '',
  chartUrl: ''
})

const loading = ref(false)
const groupsData = ref([])
const serverRows = ref([])
const serverTotal = ref(0)

const groups = computed(() => {
  // 过滤掉排除的车间
  const filteredGroups = groupsData.value.filter(g => !EXCLUDED_GROUP_KEYS.includes(g.key))

  return filteredGroups.map((group) => {
    return {
      key: group.key,
      name: group.name,
      total: group.stats?.total ?? group.expected_total ?? 0,
      stats: {
        highRisk: group.stats?.highRisk ?? 0,
        historyHighRisk: group.stats?.historyHighRisk ?? 0
      }
    }
  })
})

const activeGroupName = computed(() => {
  if (!selectedGroup.value) return '加载中...'
  const group = groupsData.value.find((g) => g.key === selectedGroup.value)
  return group?.name || selectedGroup.value
})

const groupStats = computed(() => {
  if (!selectedGroup.value) {
    return { highRisk: 0, historyHighRisk: 0, total: 0 }
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
  const total = serverTotal.value
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

// 最近同步时间文本
const lastSyncTimeText = computed(() => {
  if (!lastSyncTime.value) return '最近更新：暂无同步记录'

  const syncTime = new Date(lastSyncTime.value)

  // 始终显示具体的日期时间：YYYY-MM-DD HH:mm:ss
  const year = syncTime.getFullYear()
  const month = String(syncTime.getMonth() + 1).padStart(2, '0')
  const day = String(syncTime.getDate()).padStart(2, '0')
  const hour = String(syncTime.getHours()).padStart(2, '0')
  const minute = String(syncTime.getMinutes()).padStart(2, '0')
  const second = String(syncTime.getSeconds()).padStart(2, '0')

  return `最近更新：${year}-${month}-${day} ${hour}:${minute}:${second}`
})

// 获取最近同步时间
const fetchLastSyncTime = async () => {
  try {
    const response = await request.get('/robots/last_sync_time/')
    if (response.last_sync_time) {
      lastSyncTime.value = response.last_sync_time
    }
  } catch (error) {
    console.error('获取同步时间失败:', error)
  }
}

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
  console.log('goToPage called with page:', page)
  currentPage.value = page
  jumpPage.value = page
  loadRows()
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

const robots = computed(() => serverRows.value)

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

const formatNumber = (val) => {
  if (val === null || val === undefined) return '-'
  if (typeof val === 'number') {
    // 如果是整数，直接返回；如果是小数，保留2位
    return Number.isInteger(val) ? val : val.toFixed(2)
  }
  return '-'
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

const getUpdatedAtText = (row) => {
  const value = row?.updated_at || row?.updatedAt
  return formatDateTime(value)
}

const getUpdatedAtSortValue = (row) => {
  const value = row?.updated_at || row?.updatedAt
  return value ? new Date(value).getTime() : 0
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
    (robot.robot || '').toLowerCase().includes(key) ||
    (robot.robot_id || robot.id || '').toString().toLowerCase().includes(key) ||
    (robot.name || '').toLowerCase().includes(key) ||
    (robot.model || '').toLowerCase().includes(key) ||
    (robot.partNo || '').toLowerCase().includes(key) ||
    (robot.referenceNo || robot.reference || '').toLowerCase().includes(key) ||
    (robot.type || robot.typeSpec || '').toLowerCase().includes(key) ||
    (robot.tech || '').toLowerCase().includes(key) ||
    (robot.remark || '').toLowerCase().includes(key)
  )
}

const matchesFilters = (robot) => {
  if (levelFilter.value.length && !levelFilter.value.includes(robot.level)) return false
  if (markMode.value === 'zero' && (robot.mark ?? 0) !== 0) return false
  if (markMode.value === 'nonzero' && (robot.mark ?? 0) === 0) return false
  if (axisKeysFilter.value.length) {
    const keys = axisKeysFilter.value
    if (axisStateFilter.value === 'bad') {
      // 筛选 label 为 'high' 的项
      const anyBad = keys.some((k) => robot?.checks?.[k]?.label?.toLowerCase() === 'high')
      if (!anyBad) return false
    } else if (axisStateFilter.value === 'ok') {
      // 筛选 label 不为 'high' 的项
      const allOk = keys.every((k) => robot?.checks?.[k]?.label?.toLowerCase() !== 'high')
      if (!allOk) return false
    }
  }
  return matchesKeyword(robot)
}

const filteredRows = computed(() => {
  const list = robots.value

  console.log('filteredRows computing:', {
    listLength: list.length,
    activeTab: activeTab.value,
    keyword: keyword.value,
    firstRobot: list[0]
  })

  // 根据当前标签页筛选数据
  let filtered = list
  if (activeTab.value === 'highRisk') {
    filtered = list.filter((r) => r.isHighRisk)
  } else if (activeTab.value === 'history') {
    // 历史列表数据直接从 API 获取，已经是完整的历史高风险数据，不需要额外过滤
    filtered = list
  }

  console.log('After tab filter:', { filteredLength: filtered.length })

  // 应用所有过滤器（包括关键词搜索）
  // 前端始终进行过滤，确保搜索功能在所有模式下都能正常工作
  const result = filtered.filter(matchesFilters)
  console.log('After all filters:', { resultLength: result.length })
  return result
})

const pagedRows = computed(() => {
  // 使用服务器分页，直接返回服务器数据
  return filteredRows.value
})

const resetFilters = () => {
  keyword.value = ''
  levelFilter.value = []
  axisKeysFilter.value = []
  axisStateFilter.value = ''
  markMode.value = ''
  currentPage.value = 1
  loadRows()
}

// 搜索处理函数
const handleSearch = () => {
  console.log('handleSearch called, keyword:', keyword.value)
  currentPage.value = 1
  // 搜索时请求所有数据，由前端进行过滤
  loadRows(true)
}

// 监听关键词变化，自动触发搜索（debounce 延迟）
let keywordTimer = null
watch(keyword, (newKeyword) => {
  console.log('keyword changed:', newKeyword)
  if (keywordTimer) {
    clearTimeout(keywordTimer)
  }
  keywordTimer = setTimeout(() => {
    if (newKeyword.trim() !== '') {
      console.log('Auto-triggering search for:', newKeyword)
      currentPage.value = 1
      loadRows(true)
    }
  }, 500)
})

const handleRefresh = () => {
  if (syncing.value) {
    ElMessage.warning('数据同步中，请稍候...')
    return
  }

  syncing.value = true

  // 保存同步状态到 sessionStorage
  const syncStartTime = Date.now()
  sessionStorage.setItem('robot_sync_state', JSON.stringify({
    syncing: true,
    startTime: syncStartTime
  }))

  // 异步执行同步，不阻塞UI
  importRobotComponents({}).then(async (result) => {
    syncing.value = false

    // 清除 sessionStorage 中的同步状态
    sessionStorage.removeItem('robot_sync_state')

    // 显示成功消息
    ElMessage.success(`同步成功！新增 ${result.records_created || 0} 条，更新 ${result.records_updated || 0} 条`)

    // 刷新页面数据
    currentPage.value = 1
    await loadGroups()
    await loadRows()
    await fetchLastSyncTime()
  }).catch((error) => {
    syncing.value = false

    // 即使失败也清除 sessionStorage
    sessionStorage.removeItem('robot_sync_state')

    console.error('导入数据失败:', error)

    // 显示失败消息
    ElMessage.error(`同步失败：${error.message || '未知错误'}`)

    // 即使导入失败，也刷新页面数据
    currentPage.value = 1
    loadGroups()
    loadRows()
  })
}

const openDetail = (robot) => {
  detailRobot.value = robot
  detailVisible.value = true
}

const normalizeRow = (row) => {
  if (!row) return null
  return {
    id: row.id,
    referenceNo: row.referenceNo ?? row.reference_no ?? row.reference ?? '',
    number: row.number ?? 0,
    mark: row.mark ?? 0,
    remark: row.remark ?? '',
    level: row.level ?? 'L'
  }
}

// 登录处理函数
const handleLogin = async () => {
  const { username, password } = loginForm.value
  if (!username || !password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  loggingIn.value = true
  try {
    const result = await verifyEditCredentials({ username, password })
    if (result.success) {
      isEditAuthenticated.value = true
      // 保存会话版本到 localStorage
      saveAuthState(result.sessionVersion)
      loginVisible.value = false
      loginForm.value = { username: '', password: '' }
      ElMessage.success('登录成功，可以编辑了')

      // 如果有待处理的编辑操作，执行它
      if (pendingEditData.value) {
        const { row, focusField } = pendingEditData.value
        pendingEditData.value = null
        // 延迟执行，确保对话框关闭动画完成
        nextTick(() => {
          openEdit(row, focusField)
        })
      }
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.error || '登录失败，请检查用户名和密码')
  } finally {
    loggingIn.value = false
  }
}

const cancelLogin = () => {
  loginVisible.value = false
  loginForm.value = { username: '', password: '' }
  pendingEditData.value = null
}

const openEdit = async (row, focusField) => {
  // 同步期间禁止编辑
  if (syncing.value) {
    ElMessage.warning('数据同步中，暂时无法编辑')
    return
  }

  // 检查编辑认证
  if (!isEditAuthenticated.value) {
    // 保存待编辑的数据，登录后继续
    pendingEditData.value = { row, focusField }
    loginVisible.value = true
    return
  }

  const next = normalizeRow(row)
  if (!next?.id) return
  editTarget.value = row
  editForm.value = { ...next }
  editVisible.value = true
  await loadReferenceOptions(row.robot)
}

const applyEditToRow = (row, patch) => {
  if (!row) return
  if ('referenceNo' in patch) row.referenceNo = patch.referenceNo
  if ('reference' in patch) {
    row.reference = patch.reference
    row.referenceNo = patch.reference
  }
  if ('number' in patch) row.number = patch.number
  if ('mark' in patch) row.mark = patch.mark
  if ('remark' in patch) row.remark = patch.remark
  if ('level' in patch) row.level = patch.level
}

const handleReferenceChange = async () => {
  const robot = editTarget.value?.robot
  const reference = (editForm.value.referenceNo || '').trim()
  if (!robot || !reference) {
    editForm.value.number = 0
    return
  }
  try {
    const result = await resolveReferenceNumber({ robot, reference })
    editForm.value.number = Number(result?.number ?? 0)
  } catch (error) {
    editForm.value.number = 0
    if (error?.response?.status !== 404) {
      ElMessage.error(error?.response?.data?.error || error?.message || '匹配number失败')
    }
  }
}

const saveEdit = async () => {
  if (!editTarget.value) return
  const payload = {
    reference: (editForm.value.referenceNo || '').trim(),
    number: Number(editForm.value.number ?? 0),
    mark: Number(editForm.value.mark ?? 0),
    remark: (editForm.value.remark || '').trim(),
    level: editForm.value.level
  }

  if (!payload.reference) {
    ElMessage.warning('参考编号(reference)不能为空')
    return
  }

  editSaving.value = true
  try {
    await updateRobotComponent(editTarget.value.id, payload)
    applyEditToRow(editTarget.value, payload)
    ElMessage.success('保存成功')
    editVisible.value = false
    await loadGroups()
    if (keyword.value.trim()) {
      currentPage.value = 1
      await loadRows(true)
    } else {
      await loadRows()
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '保存失败')
  } finally {
    editSaving.value = false
  }
}

const checkTooltip = (robot, key) => {
  const axisKey = key.toUpperCase()
  const value = robot?.[axisKey] ?? robot?.[axisKey.toLowerCase()]
  const label = value ? `${key}（${value}）` : key
  if (!value) return label
  const isHigh = value.toLowerCase() === 'high'
  return isHigh ? `${label}：存在异常/待处理` : `${label}：正常/符合要求`
}

// 判断 A1-A7 字段的值是否为 high
const isCheckHigh = (robot, key) => {
  // 直接读取 A1-A7 字段的值（大写字段名）
  const axisKey = key.toUpperCase()  // 'A1' -> 'A1'
  const value = robot?.[axisKey] ?? robot?.[axisKey.toLowerCase()]
  return value?.toLowerCase() === 'high'
}

// 获取轴的提示文本（用于 highRisk 和 history 标签页）
const getAxisTooltipText = (robot, key) => {
  const axisKey = key.toUpperCase()
  const value = robot?.[axisKey] ?? robot?.[axisKey.toLowerCase()]
  if (!value) return `${key}: 无数据`
  const isHigh = value.toLowerCase() === 'high'
  return `${key}: ${value}${isHigh ? ' (高风险)' : ' (正常)'}`
}

// 判断 A1-A7 的值是否为 high（用于 all 标签页）
const isAxisHigh = (row, axisNum) => {
  const axisKey = `A${axisNum}`
  const value = row?.[axisKey] ?? row?.[axisKey.toLowerCase()]
  return value?.toLowerCase() === 'high'
}

// 获取轴的状态文本（用于 all 标签页）
const getAxisStatusText = (row, axisNum) => {
  const axisKey = `A${axisNum}`
  const value = row?.[axisKey] ?? row?.[axisKey.toLowerCase()]
  if (value) {
    const isHigh = value.toLowerCase() === 'high'
    return `${value}${isHigh ? ' (高风险)' : ' (正常)'}`
  }
  return '无数据'
}

const openBI = async (robot) => {
  const partNo = robot?.partNo || robot?.part_no || robot?.robot || ''
  const groupKey = robot?.group || selectedGroup.value || ''

  if (!partNo) {
    ElMessage.warning('Cannot get robot information')
    return
  }

  try {
    // 调用API获取数据库实际时间范围
    const response = await request.get('/robots/components/time_range/', {
      params: { robot: partNo }
    })

    const { start_date, end_date } = response

    router.push({
      path: '/alerts',
      query: {
        group: groupKey,
        robot: partNo,
        start_date: start_date,
        end_date: end_date
      }
    })
  } catch (error) {
    console.error('Failed to get time range:', error)
    ElMessage.error('Failed to get robot data time range, please try again later')
  }
}

// 打开错误率趋势图弹窗
const openErrorTrendChart = async (robot, axisKey) => {
  const axisNum = parseInt(axisKey.replace('A', ''))
  if (!robot?.id) {
    ElMessage.error('无法获取机器人信息')
    return
  }

  // 设置弹窗数据
  chartDialogData.value = {
    robot: robot,
    axis: axisNum,
    axisName: axisKey,
    chartUrl: '',
    robotPartNo: robot.partNo || robot.part_no || ''
  }
  chartDialogVisible.value = true
  chartDialogLoading.value = true

  try {
    const response = await getErrorTrendChart(robot.id, axisNum)
    if (response.success) {
      // 将 base64 数据转换为 data URL
      chartDialogData.value.chartUrl = `data:image/png;base64,${response.chart_data}`
    } else {
      ElMessage.error(response.error || '获取图表失败')
      chartDialogVisible.value = false
    }
  } catch (error) {
    console.error('获取图表失败:', error)
    ElMessage.error(error?.response?.data?.error || error?.message || '获取图表失败')
    chartDialogVisible.value = false
  } finally {
    chartDialogLoading.value = false
  }
}

const loadGroups = async () => {
  try {
    loading.value = true
    const response = await getRobotGroups()
    groupsData.value = (response || []).map(normalizeGroupName)
    const queryGroup = route.query.group

    if (queryGroup && groupsData.value.find((g) => g.key === queryGroup)) {
      selectedGroup.value = queryGroup
    } else if (!selectedGroup.value && groupsData.value.length) {
      selectedGroup.value = groupsData.value[0].key
    }
  } finally {
    loading.value = false
  }
}

const loadRows = async (fetchAll = false) => {
  loading.value = true
  try {
    const tabMap = { highRisk: 'highRisk', all: 'all', history: 'history' }
    // 搜索时获取所有数据用于前端过滤
    const actualPageSize = fetchAll ? 10000 : pageSize.value

    console.log('loadRows called:', { activeTab: activeTab.value, fetchAll, keyword: keyword.value, actualPageSize })

    // 根据标签页选择不同的 API
    let data
    if (activeTab.value === 'history') {
      // 历史高风险机器人列表使用 HighRiskHistory API
      const historyParams = {
        group: selectedGroup.value,
        keyword: keyword.value || undefined,
        level: levelFilter.value.length ? levelFilter.value.join(',') : undefined,
        axisOk: axisStateFilter.value || undefined,
        page: fetchAll ? 1 : currentPage.value,
        page_size: actualPageSize
      }
      console.log('Calling getHighRiskHistories with params:', historyParams)
      data = await getHighRiskHistories(historyParams)
    } else {
      // highRisk 和 all 标签页都使用 RobotComponent API
      const params = {
        group: selectedGroup.value,
        tab: tabMap[activeTab.value] || 'highRisk',
        keyword: keyword.value || undefined,
        level: levelFilter.value.length ? levelFilter.value.join(',') : undefined,
        axisKeys: axisKeysFilter.value.length ? axisKeysFilter.value.join(',') : undefined,
        axisOk: axisStateFilter.value ? axisStateFilter.value === 'ok' : undefined,
        markMode: markMode.value || undefined,
        page: fetchAll ? 1 : currentPage.value,
        page_size: actualPageSize
      }
      console.log('Calling getRobotComponents with params:', params)
      data = await getRobotComponents(params)
    }

    console.log('Loaded data:', { count: data.count, resultsLength: data.results?.length })
    // 打印第一条数据，检查字段名
    if (data.results && data.results.length > 0) {
      console.log('First row data:', data.results[0])
      console.log('First row fields:', Object.keys(data.results[0]))
    }
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
  // 检查并恢复同步状态
  await checkAndRestoreSyncState()

  await loadGroups()
  await loadRows()
  await fetchLastSyncTime()

  // 设置分页调试
  setupPaginationDebug()
}

// 检查并恢复同步状态
const checkAndRestoreSyncState = async () => {
  try {
    const syncStateStr = sessionStorage.getItem('robot_sync_state')
    if (!syncStateStr) return

    const syncState = JSON.parse(syncStateStr)

    // 检查同步状态是否太旧（超过5分钟则认为已失效）
    const SYNC_TIMEOUT = 5 * 60 * 1000 // 5分钟
    const now = Date.now()

    if (now - syncState.startTime > SYNC_TIMEOUT) {
      // 同步状态已过期，清除
      sessionStorage.removeItem('robot_sync_state')
      console.log('同步状态已过期，已清除')
      return
    }

    // 恢复同步状态
    syncing.value = true
    console.log('恢复同步状态:', syncState)

    // 启动轮询检查后端同步状态
    pollSyncStatus()
  } catch (error) {
    console.error('检查同步状态失败:', error)
    sessionStorage.removeItem('robot_sync_state')
  }
}

// 轮询检查后端同步状态
let syncPollTimer = null
const pollSyncStatus = async () => {
  // 清除之前的定时器
  if (syncPollTimer) {
    clearInterval(syncPollTimer)
  }

  // 每秒检查一次
  syncPollTimer = setInterval(async () => {
    try {
      // 通过获取最后同步时间来检查同步是否完成
      // 如果后端同步时间距离现在很近（几秒内），说明刚完成
      const response = await request.get('/robots/last_sync_time/')
      const lastSyncTime = response.last_sync_time

      if (lastSyncTime) {
        const syncTime = new Date(lastSyncTime).getTime()
        const now = Date.now()
        const timeDiff = now - syncTime

        // 如果最后同步时间在最近5秒内，说明同步刚完成
        if (timeDiff < 5000 && timeDiff > 0) {
          // 同步完成
          syncing.value = false
          sessionStorage.removeItem('robot_sync_state')
          clearInterval(syncPollTimer)
          syncPollTimer = null

          // 显示成功消息
          ElMessage.success('数据同步已成功完成')

          // 刷新数据
          currentPage.value = 1
          await loadGroups()
          await loadRows()
          await fetchLastSyncTime()
        }
      }
    } catch (error) {
      console.error('检查同步状态失败:', error)
    }
  }, 2000) // 每2秒检查一次
}

// 监听页码变化
watch(currentPage, (newPage) => {
  console.log('Current page changed:', newPage)
  loadRows()
})

// 监听其他过滤器变化
let suppressFilterLoad = false
watch([selectedGroup, activeTab], () => {
  console.log('selectedGroup or activeTab changed, resetting page to 1')
  suppressFilterLoad = true
  levelFilter.value = activeTab.value === 'highRisk' ? ['H'] : []
  currentPage.value = 1
  loadRows()
  suppressFilterLoad = false
})

watch(pageSize, () => {
  currentPage.value = 1
  loadRows()
})

// 过滤器变化时自动触发（关键词需要按回车）
watch([levelFilter, axisKeysFilter, axisStateFilter, markMode], () => {
  if (suppressFilterLoad) return
  console.log('Filters changed, resetting page to 1. Filters:', {
    level: levelFilter.value,
    axisKeys: axisKeysFilter.value,
    axisState: axisStateFilter.value,
    markMode: markMode.value
  })
  currentPage.value = 1
  loadRows()
})

// 当 axisKeysFilter 清空时，同步清空 axisStateFilter
watch(axisKeysFilter, (newVal) => {
  if (!newVal.length) {
    axisStateFilter.value = ''
  }
})

// 初始化数据
initData()

// 组件挂载时恢复登录状态
onMounted(() => {
  restoreAuthState()
})

// 组件卸载时清理定时器
onUnmounted(() => {
  if (syncPollTimer) {
    clearInterval(syncPollTimer)
    syncPollTimer = null
  }
})
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
  max-width: 100%;
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

.last-sync-time {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 215, 0, 0.15);
  border-radius: 999px;
  color: #ffd700;
  font-size: 13px;
  transition: all 0.3s ease;
}

.last-sync-time.syncing {
  background: rgba(34, 197, 94, 0.15);
  border-color: rgba(34, 197, 94, 0.4);
  color: #4ade80;
  animation: syncPulse 2s ease-in-out infinite;
}

.last-sync-time .el-icon {
  font-size: 14px;
}

.last-sync-time.syncing .el-icon {
  animation: syncSpin 1s linear infinite;
}

@keyframes syncPulse {
  0%, 100% {
    box-shadow: 0 0 5px rgba(74, 222, 128, 0.3);
  }
  50% {
    box-shadow: 0 0 15px rgba(74, 222, 128, 0.6);
  }
}

@keyframes syncSpin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
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
  font-size: 12px;
  letter-spacing: 0.5px;
  font-weight: 600;
  white-space: nowrap;
  user-select: none;
}

.data-table-section :deep(.el-table__header th .cell) {
  white-space: nowrap;
  padding: 0 8px;
  overflow: visible !important;
  text-overflow: clip !important;
}

/* 排序列表头保持统一颜色，不显示“可选”蓝色 */
.data-table-section :deep(.el-table__header th.is-sortable),
.data-table-section :deep(.el-table__header th.is-sortable .cell) {
  color: #8da0b7 !important;
  cursor: pointer !important;
  background: rgba(255, 255, 255, 0.04) !important;
}

/* 永久禁用表头排序激活色 - 统一为浅蓝灰色 */
.data-table-section :deep(.el-table__header th:hover .cell),
.data-table-section :deep(.el-table__header th.is-sortable:hover),
.data-table-section :deep(.el-table__header th.is-sortable:hover .cell),
.data-table-section :deep(.el-table__header th.ascending),
.data-table-section :deep(.el-table__header th.ascending .cell),
.data-table-section :deep(.el-table__header th.descending),
.data-table-section :deep(.el-table__header th.descending .cell),
.data-table-section :deep(.el-table__header th.is-sortable .cell:hover) {
  color: #8da0b7 !important;
  background: rgba(255, 255, 255, 0.04) !important;
}

/* 排序图标颜色 */
.data-table-section :deep(.el-table__header th .caret-wrapper .sort-caret.ascending),
.data-table-section :deep(.el-table__header th .caret-wrapper .sort-caret.descending) {
  color: #8da0b7 !important;
  border-top-color: #8da0b7 !important;
  border-bottom-color: #8da0b7 !important;
  opacity: 0.6;
}

.data-table-section :deep(.el-table__header th .caret-wrapper),
.data-table-section :deep(.el-table__header th .caret-wrapper .sort-caret) {
  cursor: pointer !important;
}

/* 简约菱形排序按钮：上下三角组合 */
.data-table-section :deep(.el-table__header th .caret-wrapper) {
  width: 10px;
  height: 12px;
  margin-left: 6px;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.data-table-section :deep(.el-table__header th .caret-wrapper::before),
.data-table-section :deep(.el-table__header th .caret-wrapper::after) {
  content: '';
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  opacity: 0.35;
  transition: opacity 0.15s ease, border-color 0.15s ease;
}

.data-table-section :deep(.el-table__header th .caret-wrapper::before) {
  border-bottom: 5px solid #8da0b7;
}

.data-table-section :deep(.el-table__header th .caret-wrapper::after) {
  border-top: 5px solid #8da0b7;
}

.data-table-section :deep(.el-table__header th.ascending .caret-wrapper::before) {
  opacity: 0.9;
  border-bottom-color: #cbd5e1;
}

.data-table-section :deep(.el-table__header th.ascending .caret-wrapper::after) {
  opacity: 0.2;
  border-top-color: #8da0b7;
}

.data-table-section :deep(.el-table__header th.descending .caret-wrapper::after) {
  opacity: 0.9;
  border-top-color: #cbd5e1;
}

.data-table-section :deep(.el-table__header th.descending .caret-wrapper::before) {
  opacity: 0.2;
  border-bottom-color: #8da0b7;
}

.data-table-section :deep(.el-table__header th .caret-wrapper .sort-caret) {
  display: none;
}

/* robot 列表头右移，内容不变 */
.data-table-section :deep(.el-table__header th.robot-column .cell) {
  padding-left: 34px !important;
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
  white-space: nowrap;
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

.form-label-row {
  display: inline-flex;
  align-items: center;
  gap: 6px;
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

.reference-select-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.reference-select-row :deep(.el-select),
.reference-select {
  flex: 1;
  width: 100%;
}

.reference-select-row :deep(.el-select__wrapper) {
  width: 100%;
}

.reference-refresh-button {
  padding: 0;
  height: 18px;
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

/* === 可点击关节点样式 === */
.clickable-dot {
  cursor: pointer;
  transition: all 0.2s ease;
}

.clickable-dot:hover {
  transform: scale(1.3);
  box-shadow: 0 0 12px currentColor;
}

/* === 图表弹窗样式 === */
:deep(.chart-dialog) {
  max-width: 95vw;
  margin-top: 5vh !important;
}

:deep(.chart-dialog .el-dialog__header) {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

:deep(.chart-dialog .el-dialog__title) {
  font-size: 15px;
  font-weight: 700;
  color: #fff;
}

:deep(.chart-dialog .el-dialog__body) {
  padding: 0;
}

.chart-dialog-content {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  padding: 0;
}

.chart-image-wrapper {
  width: 100%;
  display: flex;
  justify-content: center;
}

.chart-image {
  width: 100%;
  height: auto;
  display: block;
}

.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #666;
}

.chart-placeholder p {
  margin: 0;
  font-size: 13px;
}

/* === Login Dialog Styles === */
.login-dialog-content {
  padding: 10px 0;
}

.login-hint {
  margin: 0 0 20px 0;
  padding: 12px 16px;
  background: rgba(255, 170, 0, 0.08);
  border-left: 3px solid #ffaa00;
  border-radius: 6px;
  color: #ffd700;
  font-size: 14px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.login-form :deep(.el-form-item__label) {
  color: #fff;
  font-weight: 600;
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
