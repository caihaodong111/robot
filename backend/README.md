# 物联网环境监测系统 - 后端

基于 Django 6.0 + Django REST Framework 的物联网环境监测系统后端项目。

## 技术栈

- **框架**: Django 6.0
- **API**: Django REST Framework
- **异步任务**: Celery
- **WebSocket**: Django Channels
- **数据库**: MySQL (使用pymysql驱动)
- **缓存/队列**: Redis

## 项目结构

```
backend/
├── alerts/               # 报警管理模块
│   ├── admin.py         # 管理后台配置
│   ├── models.py        # 数据模型
│   ├── serializers.py   # 序列化器
│   ├── views.py         # 视图
│   ├── urls.py          # 路由
│   └── tasks.py         # Celery任务
├── devices/             # 设备管理模块
│   ├── admin.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── monitoring/          # 数据监测模块
│   ├── admin.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── consumers.py     # WebSocket消费者
│   └── routing.py       # WebSocket路由
├── users/               # 用户管理模块
│   ├── admin.py
│   ├── views.py
│   └── urls.py
├── iot_monitor/         # 项目配置
│   ├── settings.py      # Django配置
│   ├── urls.py          # 主路由
│   ├── celery.py        # Celery配置
│   ├── wsgi.py          # WSGI配置
│   └── asgi.py          # ASGI配置
├── static/              # 静态文件
├── templates/           # 模板文件
├── manage.py            # Django管理脚本
└── requirements.txt     # Python依赖
```

## 功能模块

### 1. 设备管理 (devices)
- 设备CRUD操作
- 设备状态管理
- 设备配置管理
- 设备数据查询

### 2. 数据监测 (monitoring)
- 传感器数据采集
- 实时数据查询
- 历史数据查询
- 数据统计
- 数据导出

### 3. 报警管理 (alerts)
- 报警规则配置
- 报警记录管理
- 报警通知
- 异步任务处理

### 4. 用户管理 (users)
- 用户注册
- 用户登录
- Token认证
- 权限控制

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制示例配置文件并根据需要修改：

```bash
cp env.example env
```

编辑 `.env` 文件，配置以下关键参数：

```env
# 数据库配置
DB_NAME=iot_monitor
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# Django密钥 (生产环境请修改)
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### 3. 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 创建超级用户

```bash
python manage.py createsuperuser
```

### 5. 启动服务

```bash
# Django开发服务器
python manage.py runserver

# Celery worker (另开终端)
celery -A iot_monitor worker -l info

# Celery beat (定时任务, 可选)
celery -A iot_monitor beat -l info
```

### 关键轨迹检查（TRAJECTORY CHECK）

关键轨迹检查通过 Celery 异步任务执行，依赖 Redis 作为 broker/cache。

## API接口

### 设备管理
- `GET /api/devices/devices/` - 获取设备列表
- `POST /api/devices/devices/` - 创建设备
- `GET /api/devices/devices/{id}/` - 获取设备详情
- `PUT /api/devices/devices/{id}/` - 更新设备
- `DELETE /api/devices/devices/{id}/` - 删除设备

### 数据监测
- `GET /api/monitoring/data/latest/` - 获取最新数据
- `POST /api/monitoring/upload/` - 上报数据
- `GET /api/monitoring/query/` - 查询历史数据
- `GET /api/monitoring/statistics/{id}/` - 获取统计数据
- `GET /api/monitoring/export/` - 导出数据

### 报警管理
- `GET /api/alerts/rules/` - 获取报警规则
- `POST /api/alerts/rules/` - 创建报警规则
- `GET /api/alerts/records/` - 获取报警记录
- `POST /api/alerts/records/{id}/acknowledge/` - 确认报警
- `POST /api/alerts/records/{id}/resolve/` - 解决报警

### 用户认证
- `POST /api/auth/register/` - 用户注册
- `POST /api/auth/login/` - 用户登录
- `POST /api/auth/logout/` - 用户登出
- `GET /api/auth/profile/` - 获取用户信息

## 数据模型

### Device (设备)
- name: 设备名称
- device_id: 设备ID
- device_type: 设备类型
- location: 安装位置
- status: 设备状态
- owner: 所属用户

### SensorData (传感器数据)
- device: 关联设备
- temperature: 温度
- humidity: 湿度
- light_intensity: 光照强度
- pm25: PM2.5
- co2: CO2浓度
- timestamp: 采集时间

### AlertRule (报警规则)
- name: 规则名称
- device: 关联设备
- sensor_type: 传感器类型
- condition: 条件
- threshold: 阈值
- severity: 严重程度
- enabled: 是否启用

### AlertRecord (报警记录)
- rule: 关联规则
- device: 关联设备
- status: 状态
- message: 报警消息
- current_value: 当前值
- triggered_at: 触发时间

## 开发指南

### 添加新的API端点

1. 在对应应用的 `views.py` 中添加视图函数
2. 在对应应用的 `urls.py` 中注册路由
3. 在 `iot_monitor/urls.py` 中包含应用路由

### 添加新的Celery任务

在对应应用的 `tasks.py` 中定义任务：

```python
from celery import shared_task

@shared_task
def my_task():
    # 任务逻辑
    pass
```

### WebSocket开发

1. 在 `monitoring/consumers.py` 中定义消费者
2. 在 `monitoring/routing.py` 中注册路由
3. 在 `iot_monitor/asgi.py` 中配置

## 配置说明

### Redis配置
用于Celery消息队列和WebSocket：

```python
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
```

### CORS配置
允许前端跨域访问：

```python
CORS_ALLOW_ALL_ORIGINS = True
```

## 部署

### 生产环境配置

1. 设置 `DEBUG = False`
2. 配置 `ALLOWED_HOSTS`
3. 使用生产级数据库
4. 配置静态文件服务
5. 使用Gunicorn+nginx部署

## License

MIT
