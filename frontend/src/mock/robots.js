const ROBOT_GROUPS = [
  { key: 'PT', name: 'PT', total: 88 },
  { key: 'EATS', name: 'EATS', total: 965 },
  { key: 'EB5', name: 'EB5', total: 128 },
  { key: 'MRA2', name: 'MRA2', total: 143 },
  { key: 'HOP', name: 'HOP', total: 655 },
  { key: '540', name: '540', total: 89 },
  { key: '214Reuse', name: '214Reuse', total: 331 },
  { key: 'MMA', name: 'MMA', total: 198 },
  { key: 'Shunyi', name: 'Shunyi', total: 245 },
  { key: 'AS1', name: 'AS1', total: 176 },
  { key: 'AS2', name: 'AS2', total: 212 }
]

const GROUP_COUNTS = ROBOT_GROUPS.reduce((acc, group) => {
  acc[group.key] = group.total
  return acc
}, {})

const clamp = (value, min, max) => Math.min(max, Math.max(min, value))

const mulberry32 = (seed) => {
  let t = seed >>> 0
  return () => {
    t += 0x6D2B79F5
    let x = t
    x = Math.imul(x ^ (x >>> 15), x | 1)
    x ^= x + Math.imul(x ^ (x >>> 7), x | 61)
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296
  }
}

const hashString = (text) => {
  let hash = 2166136261
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

const padNumber = (number, length) => String(number).padStart(length, '0')

const pick = (rand, list) => list[Math.floor(rand() * list.length)]

const now = () => new Date()

const formatIso = (date) => date.toISOString()

const buildRobotId = (groupKey, index) => {
  const prefix = groupKey.replaceAll('/', '-').toUpperCase()
  return `${prefix}-${padNumber(index + 1, 4)}`
}

const deriveStatus = (rand) => {
  const r = rand()
  if (r < 0.78) return 'online'
  if (r < 0.9) return 'maintenance'
  return 'offline'
}

const deriveRiskLevel = (score) => {
  if (score >= 90) return 'critical'
  if (score >= 80) return 'high'
  if (score >= 60) return 'medium'
  return 'low'
}

const deriveRiskReason = (robot) => {
  if (robot.status === 'offline') return '长时间离线'
  if (robot.battery <= 12) return '电量过低'
  if (robot.health <= 70) return '健康度偏低'
  if (robot.networkLatency >= 280) return '网络时延异常'
  if (robot.motorTemp >= 88) return '电机温度偏高'
  return pick(mulberry32(hashString(robot.id) ^ 0x9e3779b9), [
    '运动控制异常',
    '定位漂移',
    '急停触发次数偏多',
    '传感器数据波动'
  ])
}

const formatYYMMDD = (date) => {
  const y = String(date.getFullYear()).slice(-2)
  const m = padNumber(date.getMonth() + 1, 2)
  const d = padNumber(date.getDate(), 2)
  return `${y}${m}${d}`
}

const createReferenceNo = (rand) => {
  const base = new Date()
  const endOffsetDays = 5 + Math.floor(rand() * 25)
  const startOffsetDays = endOffsetDays + 8 + Math.floor(rand() * 45)
  const end = new Date(base.getTime() - endOffsetDays * 24 * 3600_000)
  const start = new Date(base.getTime() - startOffsetDays * 24 * 3600_000)
  return `${formatYYMMDD(start)}-${formatYYMMDD(end)}`
}

const createPartNo = (rand) => {
  const prefix = pick(rand, ['UB41', 'UB42', 'UA20', 'UD18', 'UX07'])
  const section = padNumber(1 + Math.floor(rand() * 99), 3)
  const family = pick(rand, ['RB', 'RC', 'RD', 'RE'])
  const suffix = padNumber(1 + Math.floor(rand() * 180), 3)
  return `${prefix}_${section}${family}_${suffix}`
}

const createTech = (rand) => {
  const pool = ['抓手', '涂胶', '焊接', '拧紧', '涂装', '码垛', '搬运', '检测', '打标']
  const first = pick(rand, pool)
  let second = pick(rand, pool)
  if (second === first) second = pick(rand, pool)
  const count = rand() < 0.55 ? 2 : 1
  return count === 2 ? `${first} + ${second}` : first
}

const createTypeSpec = (rand) => pick(rand, [
  'KR600_R2830_Fortec',
  'KR210_R3100_Quantec',
  'KR120_R2700_Quantec',
  'IRB_6700_205_2.75',
  'FANUC_M_900iB_700',
  'Kawasaki_RS080N',
  'UR10e_1300',
  'Yaskawa_GP225'
])

const checkKeys = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7']

const checkLabels = {
  A1: '供电/线束',
  A2: '温度/散热',
  A3: '通信/网络',
  A4: '传感器/对位',
  A5: '抓手/执行器',
  A6: '控制/程序',
  A7: '安全/急停'
}

const createChecks = (rand, robot) => {
  const checks = {}

  const baseFailRate = robot.riskScore >= 90 ? 0.18 : robot.riskScore >= 80 ? 0.12 : 0.06
  const tempBias = robot.motorTemp >= 88 ? 0.12 : 0
  const latencyBias = robot.networkLatency >= 280 ? 0.1 : 0
  const lowBatteryBias = robot.battery <= 15 ? 0.08 : 0

  for (const key of checkKeys) {
    let failRate = baseFailRate
    if (key === 'A2') failRate += tempBias
    if (key === 'A3') failRate += latencyBias
    if (key === 'A1') failRate += lowBatteryBias

    const ok = rand() >= failRate
    checks[key] = {
      ok,
      label: checkLabels[key]
    }
  }

  // 高风险机器人强制至少一项异常（更符合列表语义）
  if (robot.riskScore >= 80 && Object.values(checks).every((c) => c.ok)) {
    const preferred = robot.motorTemp >= 88 ? 'A2' : robot.networkLatency >= 280 ? 'A3' : 'A6'
    checks[preferred].ok = false
  }

  return checks
}

const createLevel = (robot) => {
  if (robot.riskScore >= 85) return 'H'
  if (robot.riskScore >= 65) return 'M'
  return 'L'
}

const createRobot = (groupKey, index) => {
  const seed = hashString(`${groupKey}::${index}`)
  const rand = mulberry32(seed)

  const status = deriveStatus(rand)
  const model = pick(rand, ['R-Atlas', 'R-Nova', 'R-Kite', 'R-Edge'])
  const workMode = pick(rand, ['巡检', '搬运', '分拣', '配送', '待命'])
  const zone = pick(rand, ['A区', 'B区', 'C区', 'D区', 'E区'])

  const baseBattery = Math.round(15 + rand() * 85)
  const battery = clamp(
    status === 'offline' ? Math.round(baseBattery * (0.25 + rand() * 0.45)) : baseBattery,
    0,
    100
  )

  const baseHealth = Math.round(62 + rand() * 38)
  const health = clamp(status === 'maintenance' ? baseHealth - Math.round(5 + rand() * 15) : baseHealth, 0, 100)

  const motorTemp = clamp(Math.round(52 + rand() * 44 + (status === 'maintenance' ? 6 : 0)), 35, 98)
  const networkLatency = clamp(Math.round(20 + rand() * 330 + (status === 'offline' ? 160 : 0)), 10, 500)

  const lastSeenMinutesAgo = Math.round(rand() * (status === 'online' ? 40 : 320))
  const lastSeen = new Date(now().getTime() - lastSeenMinutesAgo * 60_000)

  const score =
    30 +
    (100 - health) * 0.55 +
    (30 - battery) * 0.7 +
    (status === 'offline' ? 20 : 0) +
    (motorTemp >= 88 ? 8 : 0) +
    (networkLatency >= 280 ? 8 : 0) +
    rand() * 12

  const riskScore = clamp(Math.round(score), 0, 100)
  const riskLevel = deriveRiskLevel(riskScore)

  const riskHistory = []
  const historyCount = rand() < 0.22 ? 1 + Math.floor(rand() * 3) : 0
  for (let h = 0; h < historyCount; h += 1) {
    const pastHours = 8 + Math.round(rand() * 120)
    const eventTime = new Date(now().getTime() - pastHours * 3600_000)
    const eventScore = clamp(Math.round(riskScore - 10 + rand() * 25), 40, 100)
    riskHistory.push({
      id: `${seed}-${h}`,
      time: formatIso(eventTime),
      score: eventScore,
      level: deriveRiskLevel(eventScore)
    })
  }

  const robot = {
    id: buildRobotId(groupKey, index),
    group: groupKey,
    name: `${model} #${padNumber(index + 1, 4)}`,
    partNo: '',
    referenceNo: '',
    typeSpec: '',
    tech: '',
    number: 0,
    mark: 0,
    remark: '',
    level: 'L',
    checks: {},
    model,
    status,
    battery,
    health,
    motorTemp,
    networkLatency,
    workMode,
    zone,
    lastSeen: formatIso(lastSeen),
    riskScore,
    riskLevel,
    riskHistory
  }

  robot.riskReason = deriveRiskReason(robot)

  robot.partNo = createPartNo(rand)
  robot.referenceNo = createReferenceNo(rand)
  robot.number = 0
  robot.typeSpec = createTypeSpec(rand)
  robot.tech = createTech(rand)
  robot.level = createLevel(robot)
  robot.isHighRisk = robot.level === 'H'
  robot.checks = createChecks(rand, robot)

  const remarkHints = []
  if (robot.motorTemp >= 88) remarkHints.push('温度相关可能')
  if (robot.networkLatency >= 280) remarkHints.push('通信波动')
  if (robot.battery <= 15) remarkHints.push('低电量影响')
  const attention = robot.riskScore >= 90 ? '重点关注' : robot.riskScore >= 80 ? '需留意观察' : '观察'
  const hintText = remarkHints.length ? `${remarkHints.join('，')}，${attention}` : attention
  robot.remark = `${robot.riskReason}；${hintText}`

  return robot
}

const robotsCache = new Map()

export const robotGroups = ROBOT_GROUPS

export const getRobotsByGroup = (groupKey) => {
  if (!GROUP_COUNTS[groupKey]) return []
  if (robotsCache.has(groupKey)) return robotsCache.get(groupKey)

  const list = Array.from({ length: GROUP_COUNTS[groupKey] }, (_, index) => createRobot(groupKey, index))
  robotsCache.set(groupKey, list)
  return list
}

export const getAllRobots = () => robotGroups.flatMap((group) => getRobotsByGroup(group.key))

export const getGroupStats = (groupKey) => {
  const robots = getRobotsByGroup(groupKey)
  const stats = {
    total: robots.length,
    online: 0,
    offline: 0,
    maintenance: 0,
    highRisk: 0,
    historyHighRisk: 0
  }

  for (const robot of robots) {
    stats[robot.status] += 1
    if (robot.isHighRisk) stats.highRisk += 1
    if (robot.riskHistory?.length) stats.historyHighRisk += 1
  }

  return stats
}

export const createTelemetrySeries = (robotId, points = 60, intervalSeconds = 60) => {
  const seed = hashString(robotId) ^ 0xA5A5A5A5
  const rand = mulberry32(seed)
  const end = now().getTime()
  const baseBattery = 40 + rand() * 50
  const baseHealth = 70 + rand() * 25
  const baseMotorTemp = 55 + rand() * 15
  const baseLatency = 40 + rand() * 80

  const series = []
  for (let i = 0; i < points; i += 1) {
    const ts = new Date(end - (points - 1 - i) * intervalSeconds * 1000)
    const noise = () => (rand() - 0.5) * 6

    series.push({
      timestamp: formatIso(ts),
      battery: clamp(baseBattery - i * (0.05 + rand() * 0.04) + noise(), 0, 100),
      health: clamp(baseHealth - i * (0.015 + rand() * 0.02) + noise() * 0.7, 0, 100),
      motorTemp: clamp(baseMotorTemp + Math.sin(i / 6) * 3 + noise(), 35, 98),
      networkLatency: clamp(baseLatency + Math.sin(i / 4) * 12 + noise() * 5, 10, 500)
    })
  }

  return series
}

export const createRiskEvents = (count = 120) => {
  const robots = getAllRobots()
  const rand = mulberry32(hashString('risk-events'))
  const events = []
  const reasons = ['电量过低', '健康度偏低', '网络时延异常', '电机温度偏高', '运动控制异常', '定位漂移']
  const statuses = ['pending', 'acknowledged', 'resolved']

  for (let i = 0; i < count; i += 1) {
    const robot = robots[Math.floor(rand() * robots.length)]
    const hoursAgo = Math.round(rand() * 72)
    const triggeredAt = new Date(now().getTime() - hoursAgo * 3600_000 - Math.round(rand() * 3600_000))
    const severity = pick(rand, ['critical', 'high', 'medium', 'low'])
    const status = pick(rand, statuses)
    const reason = pick(rand, reasons)
    const score = clamp(Math.round(55 + rand() * 45 + (severity === 'critical' ? 15 : 0)), 0, 100)

    events.push({
      id: `${i + 1}`,
      robot_id: robot.id,
      robot_name: robot.name,
      group: robot.group,
      message: `风险事件：${reason}`,
      reason,
      severity,
      riskScore: score,
      status,
      triggered_at: formatIso(triggeredAt),
      current_value: score
    })
  }

  events.sort((a, b) => new Date(b.triggered_at).getTime() - new Date(a.triggered_at).getTime())
  return events
}
