import request from '@/utils/request'

// 获取机器人组列表
export function getRobotGroups() {
  return request({
    url: '/robots/groups/',
    method: 'get'
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
export function executeGripperCheck(data) {
  return request({
    url: '/robots/gripper-check/execute/',
    method: 'post',
    data
  })
}

// 获取配置模板
export function getGripperConfigTemplate() {
  return request({
    url: '/robots/gripper-check/config_template/',
    method: 'get'
  })
}
