# 机器人技术管理平台

一个基于 Vue3 + Django 的现代化机器人设备监控与管理平台，提供实时数据监测、风险预警、设备管理等功能。

## 项目简介

本平台采用前后端分离架构，专为工业物联网场景设计，实现对机器人设备的全生命周期管理，包括设备监控、风险识别、数据分析和报警处理。

### 主要功能

- **仪表盘** - 设备总数统计、高风险部件统计、历史风险记录
- **设备管理** - 机器人部件列表、详情查看、信息编辑、按组筛选
- **数据监测** - 实时数据监控、历史数据查询、数据统计图表
- **报警管理** - 风险事件列表、严重程度分级、事件状态管理

## 技术栈

### 前端
| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.5.24 | 渐进式 JavaScript 框架 |
| Vite | 7.2.4 | 下一代前端构建工具 |
| Element Plus | 2.13.1 | Vue 3 组件库 |
| Vue Router | 4.6.4 | 官方路由管理器 |
| Pinia | 3.0.4 | Vue 状态管理库 |
| Axios | 1.13.2 | HTTP 客户端 |
| ECharts | 6.0.0 | 数据可视化图表库 |

### 后端
| 技术 | 版本 | 说明 |
|------|------|------|
| Django | 6.0.1 | Python Web 框架 |
| Django REST Framework | 3.16.1 | Django 扩展，构建 Web API |
| channels | 4.3.2 | Django WebSocket 支持 |
| Celery | 5.6.2 | 分布式任务队列 |
| Redis | 7.1.0 | 缓存和消息队列 |
| PyMySQL | 1.1.2 | MySQL 数据库驱动 |
| pandas | 2.2.3 | 数据处理 |

## 项目结构

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
│   ├── package.json
│   └── vite.config.js
├── backend/                  # Django 后端项目
│   ├── robots/              # 机器人模块
│   ├── devices/             # 设备管理模块
│   ├── monitoring/          # 数据监测模块
│   ├── alerts/              # 报警管理模块
│   ├── users/               # 用户管理模块
│   ├── iot_monitor/         # 项目配置
│   ├── manage.py
│   └── requirements.txt
└── README.md
```

## 快速开始

### 环境要求

- Node.js >= 18
- Python >= 3.10
- MySQL >= 8.0
- Redis >= 6.0

### 后端启动

```bash
# 1. 进入后端目录
cd backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量（编辑 .env 文件）
cp .env.example .env

# 4. 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 5. 创建超级用户（可选）
python manage.py createsuperuser

# 6. 启动服务
python manage.py runserver

# 7. 启动 Celery（新终端）
celery -A iot_monitor worker -l info

# 8. 启动 Celery Beat（新终端，定时任务）
celery -A iot_monitor beat -l info
```

### 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev

# 4. 构建生产版本
npm run build
```

访问地址：http://localhost:5173

## 配置说明

### 环境变量 (.env)

```env
# Django 配置
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库配置
DB_NAME=robot
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306

# Redis 配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0

# Celery 配置
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
```

### API 代理

前端开发环境自动将 `/api` 请求代理到后端 `http://localhost:8000`

## 数据模型

### RobotGroup（机器人组）
| 字段 | 类型 | 说明 |
|------|------|------|
| key | String | 组标识符 |
| name | String | 组名称 |
| expected_total | Integer | 预期数量 |

### RobotComponent（机器人部件）
| 字段 | 类型 | 说明 |
|------|------|------|
| robot_id | String | 机器人 ID |
| name | String | 部件名称 |
| status | String | 状态 |
| battery | Integer | 电池电量 |
| health | String | 健康状态 |
| risk_score | Float | 风险评分 |
| risk_level | String | 风险等级 |

### RiskEvent（风险事件）
| 字段 | 类型 | 说明 |
|------|------|------|
| robot_id | String | 机器人 ID |
| message | String | 事件信息 |
| severity | String | 严重程度 |
| status | String | 处理状态 |
| triggered_at | DateTime | 触发时间 |

## 项目特色

- 采用 Vue3 Composition API 和 Django 6.0 最新技术栈
- 前后端分离架构，易于维护和扩展
- WebSocket 支持实时数据推送
- ECharts 数据可视化展示
- 基于 Token 的用户认证机制
- Celery 异步任务处理
- 支持 Excel 数据导出

## 开发计划

- [ ] 用户权限管理优化
- [ ] 设备远程控制功能
- [ ] 数据报表生成
- [ ] 移动端适配
- [ ] 多语言支持

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎提交 Issue
