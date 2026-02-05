import request from '@/utils/request'

// 获取机器人组列表
export function getRobotGroups(params) {
  return request({
    url: '/robots/groups/',
    method: 'get',
    params
  })
}

// 获取机器人部件列表
export function getRobotComponents(params) {
  return request({
    url: '/robots/components/',
    method: 'get',
    params
  })
}

// 获取单个机器人部件详情
export function getRobotComponent(id) {
  return request({
    url: `/robots/components/${id}/`,
    method: 'get'
  })
}

// 更新机器人部件
export function updateRobotComponent(id, data) {
  return request({
    url: `/robots/components/${id}/`,
    method: 'patch',
    data
  })
}

// 获取风险事件列表
export function getRiskEvents(params) {
  return request({
    url: '/robots/risk-events/',
    method: 'get',
    params
  })
}

// 获取单个风险事件详情
export function getRiskEvent(id) {
  return request({
    url: `/robots/risk-events/${id}/`,
    method: 'get'
  })
}

// 确认风险事件
export function acknowledgeRiskEvent(id, data) {
  return request({
    url: `/robots/risk-events/${id}/acknowledge/`,
    method: 'post',
    data
  })
}

// 解决风险事件
export function resolveRiskEvent(id, data) {
  return request({
    url: `/robots/risk-events/${id}/resolve/`,
    method: 'post',
    data
  })
}

// 获取风险事件统计
export function getRiskEventStatistics(params) {
  return request({
    url: '/robots/risk-events/statistics/',
    method: 'get',
    params
  })
}

// ==================== 关键轨迹检查 API ====================

// 获取可用的机器人表名列表
export function getGripperRobotTables(params) {
  return request({
    url: '/robots/gripper-check/robot_tables/',
    method: 'get',
    params
  })
}

// 执行关键轨迹检查
// 注意：此接口需要较长的超时时间，因为可能需要处理大量数据
export function executeGripperCheck(data) {
  return request({
    url: '/robots/gripper-check/execute/',
    method: 'post',
    data,
    timeout: 60000  // 设置60秒超时，避免处理大量数据时超时
  })
}

// 获取配置模板
export function getGripperConfigTemplate() {
  return request({
    url: '/robots/gripper-check/config_template/',
    method: 'get'
  })
}

// ==================== 错误率趋势图 API ====================

// 获取机器人关节错误率趋势图
export function getErrorTrendChart(robotId, axis, regenerate = false) {
  return request({
    url: `/robots/components/${robotId}/error_trend_chart/`,
    method: 'get',
    params: {
      axis,
      regenerate: regenerate ? 1 : 0
    }
  })
}

// ==================== 周结果数据 API ====================

// 获取周结果列表（用于机器人状态页面）
export function getWeeklyResults(params) {
  return request({
    url: '/robots/components/',
    method: 'get',
    params
  })
}

// 获取高风险机器人列表（level=H）
// 这是机器人状态页面使用的主要 API
export function getHighRiskRobots(params) {
  return request({
    url: '/robots/components/',
    method: 'get',
    params: {
      ...params,
      tab: 'highRisk',
      level: 'H',  // 只获取高风险
      highRisk: '1'
    }
  })
}

// 获取周结果统计数据
export function getWeeklyResultsStats(params) {
  return Promise.reject(new Error('weekly-results stats API removed; no replacement endpoint.'))
}

// 获取可用的 CSV 文件列表
export function getWeeklyResultFiles(params) {
  return Promise.reject(new Error('weekly-results files API removed; no replacement endpoint.'))
}

// 导入 CSV 文件（需要管理员权限）
export function importWeeklyResults(data) {
  return request({
    url: '/robots/components/import_csv/',
    method: 'post',
    data,
    timeout: 120000  // 2分钟超时
  })
}

// 同步机器人状态（从 WeeklyResult 同步到 RobotComponent）
export function syncRobotStatus() {
  return Promise.reject(new Error('weekly-results sync API removed; use components/import_csv instead.'))
}

// 直接导入 CSV 到 RobotComponent 表（跳过 WeeklyResult）
export function importRobotComponents(data) {
  return request({
    url: '/robots/components/import_csv/',
    method: 'post',
    data,
    timeout: 120000  // 2分钟超时
  })
}

// ==================== 历史高风险机器人 API ====================

// 获取历史高风险机器人列表
export function getHighRiskHistories(params) {
  return request({
    url: '/robots/high-risk-histories/',
    method: 'get',
    params
  })
}
