# 项目学习文档（学习笔记）

> 说明：该文档基于对当前代码仓库的整体审阅整理，面向研发/维护人员快速了解项目结构、关键流程与注意事项。

## 1. 项目概览

- 架构：前后端分离
- 前端：Vue 3 + Vite + Element Plus + Pinia + Vue Router
- 后端：Django + DRF + Channels + Celery
- 存储：MySQL
- 缓存/队列：Redis

## 2. 目录结构速览

```
sg/
├── frontend/                 # Vue3 前端项目
│   ├── src/
│   │   ├── api/             # API 接口封装
│   │   ├── components/      # 公共组件
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── utils/           # 工具函数
│   │   └── views/           # 页面组件
│   └── vite.config.js
├── backend/                  # Django 后端项目
│   ├── devices/             # 设备管理模块
│   ├── monitoring/          # 数据监测模块
│   ├── alerts/              # 报警管理模块
│   ├── users/               # 用户管理模块
│   ├── robots/              # 机器人模块 + BI/关键轨迹
│   ├── iot_monitor/         # Django 配置
│   └── requirements.txt
└── README.md
```

## 3. 核心模块梳理

### 3.1 devices（设备管理）
- `Device`：设备主表，包含基础信息、状态、地理信息、生命周期字段。
- `DeviceConfig`：设备配置（采集间隔、报警开关、保留天数等）。
- `DeviceMaintenance`：维护记录（计划/完成/费用）。

**典型接口：**
- `GET /api/devices/devices/` 设备列表
- `POST /api/devices/devices/` 创建设备
- `POST /api/devices/devices/{id}/update_config/` 更新配置
- `POST /api/devices/devices/{id}/toggle-status/` 更新状态

### 3.2 monitoring（监测与数据）
- `SensorData`：传感器数据流水（温湿度/PM2.5/CO2 等）。
- `DataSummary`：按小时/天/月汇总的数据结构。
- `DataExport`：导出记录。

**典型接口：**
- `POST /api/monitoring/upload/` 设备上报
- `GET /api/monitoring/query/` 历史查询
- `GET /api/monitoring/statistics/{device_id}/` 统计数据
- `GET /api/monitoring/export/` 导出 Excel/CSV

### 3.3 alerts（报警与通知）
- `AlertRule`：报警规则（条件 + 阈值 + 严重等级）。
- `AlertRecord`：报警记录（状态、确认/解决、通知）。
- `NotificationConfig/Log`：通知策略与日志。

**典型接口：**
- `GET /api/alerts/rules/` 规则列表
- `GET /api/alerts/records/` 报警记录
- `POST /api/alerts/records/{id}/acknowledge/` 确认
- `POST /api/alerts/records/{id}/resolve/` 解决

### 3.4 robots（机器人与BI/关键轨迹）
- `RobotGroup`：机器人组
- `RobotComponent`：机器人部件（风险分级、状态、电流等）
- `RiskEvent`：风险事件记录
- `RobotAxisData`：轴数据时序

**BI 功能：**
- `/api/robots/bi/?table=...&embed=1` 生成 Bokeh 图表

**关键轨迹检查：**
- `/api/robots/gripper-check/execute/` 执行轨迹检查
- `/api/robots/gripper-check/robot_tables/` 查询机器人表名

### 3.5 users（用户管理）
- 基于 `Token` 的登录/登出/用户信息接口
- `UserProfile/UserActivityLog` 为扩展表

## 4. 关键数据流

### 4.1 设备上报与告警
1) 设备 `POST /api/monitoring/upload/` 上报数据
2) 保存 `SensorData`
3) Celery 任务 `check_alert_rules` 执行规则判断
4) 触发 `AlertRecord` 并发送通知

### 4.2 BI 可视化
1) 前端 iframe 打开 `/api/robots/bi/?table=...&embed=1`
2) 后端 `bokeh_charts.py` 读取数据库表
3) Bokeh 生成嵌入式图表脚本

### 4.3 关键轨迹检查
1) 前端提交机器人表名 + 时间范围 + key paths
2) `gripper_service.py` 直接 SQL 读取原始表
3) pandas 计算并返回结果

## 5. 前端页面结构

- `LayoutView`：主布局容器
- `DashboardView`：综合看板
- `DevicesView`：机器人部件/设备列表
- `MonitoringView`：关键轨迹检查
- `AlertsView`：BI 可视化
- `PortalView`：入口门户

## 6. 配置要点

- 后端 `.env`：数据库、Redis、Secret、Celery
- 前端 `vite.config.js`：开发代理 `/api -> http://localhost:8000`

## 7. 重要注意点（现状梳理）

- DRF 的认证/权限配置为开放（`AllowAny`），与前端 Token 逻辑不一致。
- BI / 关键轨迹功能使用原生 SQL 查询，存在参数安全风险，需严格校验。
- 部分路由逻辑存在路径不匹配（前端 `/login`、`/dashboard` 未定义）。
- 大部分测试文件为空，缺少集成测试覆盖。

> 如果需要，我可以继续输出：
> - 一份“修复建议清单（按优先级）”
> - 一份“数据库表结构与字段字典”
> - 一份“接口文档模板（OpenAPI草案）”
