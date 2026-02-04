# 机器人状态页面 - 周结果数据集成文档

## 概述

本文档描述了如何将 `weeklyresult.csv` 文件中的数据导入到数据库，并通过 API 展示到机器人状态页面。系统支持每24小时自动刷新数据，UI 上只显示高风险（level=H）的机器人。

## 系统架构

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  weeklyresult   │ ───> │  Django Backend │ ───> │   Frontend UI   │
│   CSV Files     │      │     (API)       │      │  (只显示H级别)  │
└─────────────────┘      └─────────────────┘      └─────────────────┘
         ▲                         │
         │                         │
         └────── cron job (24h) ───┘
               或手动点击同步按钮
```

## CSV 文件存放位置

### 默认路径

```
P:/error rate trend/{project}/
```

### 支持的项目

| 项目 | 路径示例 |
|------|----------|
| reuse | `P:/error rate trend/reuse/` |
| engine-robot | `P:/error rate trend/engine-robot/` |
| v206 | `P:/error rate trend/v206/` |
| V214&254 | `P:/error rate trend/V214&254/` |

### 文件命名规范

CSV 文件应按以下格式命名：

```
{project}_{周开始日期}_{周结束日期}_weeklyresult.csv
```

示例：
- `reuse_250410-250516_weeklyresult.csv`
- `reuse_250517-250523_weeklyresult.csv`

系统会自动查找最新的文件（按文件创建时间排序）。

### 修改默认路径

如果需要修改默认路径，可以在以下位置修改：

1. **后端服务** (`backend/robots/weekly_result_service.py:28`)
   ```python
   folder_path = 'P:/error rate trend/'  # 修改为你的路径
   ```

2. **定时任务** (`backend/scripts/setup_cron.sh`)
   ```bash
   DEFAULT_FOLDER_PATH="P:/error rate trend/"  # 修改为你的路径
   ```

3. **前端调用** (`frontend/src/views/devices/DevicesView.vue:760`)
   ```javascript
   await importWeeklyResults({
     project: 'reuse',
     folder_path: '你的路径'  // 可选参数
   })
   ```

## 功能特性

1. **自动查找最新 CSV 文件** - 根据项目路径自动找到最新的 `weeklyresult.csv` 文件
2. **定时数据导入** - 每24小时自动执行导入任务
3. **数据导入** - 将 CSV 数据导入到 `WeeklyResult` 数据表
4. **API 展示** - 提供完整的 REST API 用于查询和展示数据
5. **前端筛选** - UI 只显示 level=H 的高风险机器人

## 快速开始

### 1. 数据库迁移

```bash
cd backend
python manage.py migrate
```

### 2. 手动导入数据（测试）

```bash
cd backend
python manage.py import_weekly_results --project=reuse
```

### 3. 配置定时任务（可选）

使用配置脚本设置每24小时自动导入：

```bash
cd backend/scripts
chmod +x setup_cron.sh
./setup_cron.sh
```

## 数据模型

### WeeklyResult 模型

| 字段 | 类型 | 描述 |
|------|------|------|
| robot | CharField | 机器人编号 |
| shop | CharField | 车间 |
| reference | CharField | 参考编号 |
| number | FloatField | 编号 |
| type | CharField | 类型 |
| tech | CharField | 工艺 |
| mark | IntegerField | 标记 |
| remark | TextField | 备注 |
| error1_c1 | FloatField | 错误率C1 |
| tem1_m ~ tem7_m | FloatField | 温度数据 M1-M7 |
| a1_e_rate ~ a7_e_rate | FloatField | A1-A7 错误率 |
| a1_rms ~ a7_rms | FloatField | A1-A7 RMS值 |
| a1_e ~ a7_e | FloatField | A1-A7 E值 |
| q1 ~ q7 | FloatField | Q1-Q7值 |
| curr_a1_max ~ curr_a7_max | FloatField | A1-A7 最大电流 |
| curr_a1_min ~ curr_a7_min | FloatField | A1-A7 最小电流 |
| a1 ~ a7 | FloatField | A1-A7 电流值 |
| p_change | FloatField | P变化 |
| level | CharField | 等级 (H/M/L/T/C) |
| source_file | CharField | 源文件名 |
| week_start | DateField | 周开始日期 |
| week_end | DateField | 周结束日期 |

## API 接口

### 基础路径: `/api/robots/weekly-results/`

#### 1. 获取高风险机器人列表（UI 使用）

```
GET /api/robots/weekly-results/?level=H&highRisk=1
```

**这是前端机器人状态页面使用的主要 API**，只返回 level=H 的数据。

**查询参数:**
- `level`: 等级筛选 (H/M/L/T/C)，UI 默认使用 H
- `highRisk`: 筛选高风险 (1/true/True)
- `shop`: 按车间筛选
- `keyword`: 搜索关键词
- `page`: 页码
- `page_size`: 每页数量

**响应示例:**
```json
{
    "count": 15,
    "results": [
        {
            "id": 1,
            "robot": "UB41_020RB_100",
            "shop": "MRA1 BS",
            "type": "KR600_R2830_Fortec",
            "tech": "抓手+涂胶",
            "level": "H",
            "remark": "温度相关可能，观察",
            "avgErrorRate": 0.0156,
            "isHighRisk": true,
            "updated_at": "2025-06-01T10:00:00Z"
        }
    ]
}
```

#### 2. 获取所有周结果列表

```
GET /api/robots/weekly-results/
```

支持所有筛选参数，用于管理界面。

#### 3. 获取统计数据

```
GET /api/robots/weekly-results/stats/
```

**响应示例:**
```json
{
    "total": 100,
    "high_risk": 15,
    "by_shop": [
        {"shop": "MRA1 BS", "total": 50, "high_risk": 8},
        {"shop": "MRA2 BS", "total": 30, "high_risk": 4}
    ],
    "by_level": [
        {"level": "H", "count": 15},
        {"level": "M", "count": 20},
        {"level": "L", "count": 65}
    ]
}
```

#### 4. 导入 CSV 文件（手动触发）

```
POST /api/robots/weekly-results/import_csv/
```

**请求体:**
```json
{
    "folder_path": "P:/error rate trend/",
    "project": "reuse"
}
```

## 定时任务配置

### 方式一：使用配置脚本（推荐）

```bash
cd backend/scripts
chmod +x setup_cron.sh
./setup_cron.sh
```

脚本会：
1. 检查项目目录
2. 配置定时任务参数
3. 添加 cron 任务（每天 00:00 执行）
4. 创建日志目录

### 方式二：手动配置 cron

编辑 crontab：

```bash
crontab -e
```

添加以下行：

```bash
0 0 * * * cd /Users/caihd/Desktop/sg/backend && /usr/bin/python3 manage.py import_weekly_results --project=reuse --folder-path='P:/error rate trend/' >> /Users/caihd/Desktop/sg/backend/logs/cron_import.log 2>&1
```

### 方式三：使用 Windows 任务计划程序

创建批处理文件 `import_weekly_results.bat`:

```batch
@echo off
cd /d P:\sg\backend
python manage.py import_weekly_results --project=reuse --folder-path="P:/error rate trend/"
```

然后在任务计划程序中创建每日任务。

### 查看定时任务日志

```bash
# 实时查看日志
tail -f backend/logs/cron_import.log

# 查看最近100行
tail -n 100 backend/logs/cron_import.log
```

## Management Command

### 导入周结果数据

```bash
# 使用默认配置
python manage.py import_weekly_results

# 指定项目
python manage.py import_weekly_results --project=reuse

# 指定文件夹路径
python manage.py import_weekly_results --folder-path="P:/error rate trend/" --project=reuse

# 指定具体文件
python manage.py import_weekly_results --file-path="P:/reuse/reuse_250410-250516_weeklyresult.csv"

# 导入前清空旧数据
python manage.py import_weekly_results --clear-old
```

## 前端集成

### API 调用函数

在 `frontend/src/api/robots.js` 中已添加以下函数：

```javascript
// 获取高风险机器人列表（机器人状态页面使用）
import { getHighRiskRobots } from '@/api/robots'

const result = await getHighRiskRobots({ shop: 'MRA1 BS' })

// 获取所有周结果
import { getWeeklyResults } from '@/api/robots'

const result = await getWeeklyResults({ level: 'H' })

// 获取统计数据
import { getWeeklyResultsStats } from '@/api/robots'

const stats = await getWeeklyResultsStats()
```

### Vue 组件使用示例

```vue
<template>
  <div class="robot-status-page">
    <el-table :data="robotList" v-loading="loading">
      <el-table-column prop="robot" label="机器人编号" />
      <el-table-column prop="shop" label="车间" />
      <el-table-column prop="type" label="类型" />
      <el-table-column prop="tech" label="工艺" />
      <el-table-column prop="level" label="等级">
        <template #default="{ row }">
          <el-tag v-if="row.level === 'H'" type="danger">高风险</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="remark" label="备注" />
      <el-table-column prop="avgErrorRate" label="平均错误率" />
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getHighRiskRobots } from '@/api/robots'

const robotList = ref([])
const loading = ref(false)

const fetchRobots = async () => {
  loading.value = true
  try {
    const response = await getHighRiskRobots()
    robotList.value = response.results || []
  } catch (error) {
    console.error('获取机器人列表失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchRobots()
  // 可选：定时刷新（如每小时）
  setInterval(fetchRobots, 3600000)
})
</script>
```

## 手动刷新功能

### UI 操作

在机器人状态页面右上角有一个 **"同步数据"** 按钮，点击即可手动刷新数据：

1. 点击按钮后会自动从指定路径导入最新的 `weeklyresult.csv` 文件
2. 导入成功后自动刷新页面数据显示
3. 整个过程有加载提示和成功/失败消息

### 工作流程

```
用户点击"同步数据"按钮
        ↓
显示"正在导入最新数据..."提示
        ↓
调用 API: POST /api/robots/weekly-results/import_csv/
        ↓
后端查找最新的 weeklyresult.csv 文件
        ↓
解析 CSV 并导入到数据库
        ↓
返回导入结果（新增/更新记录数）
        ↓
显示"数据导入成功！"消息
        ↓
自动刷新页面数据（只显示 level=H 的机器人）
```

### 技术实现

**前端代码** (`frontend/src/views/devices/DevicesView.vue:743-779`):

```javascript
const handleRefresh = async () => {
  // 显示加载状态
  const loading = ElMessage({
    message: '正在导入最新数据...',
    type: 'info',
    duration: 0,
  })

  try {
    // 先导入最新的 CSV 数据
    await importWeeklyResults({ project: 'reuse' })

    loading.close()
    ElMessage.success('数据导入成功！')

    // 导入成功后刷新页面数据
    currentPage.value = 1
    await loadGroups()
    await loadRows()
  } catch (error) {
    loading.close()
    ElMessage.error('数据导入失败：' + error.message)

    // 即使导入失败，也刷新页面数据
    currentPage.value = 1
    await loadGroups()
    await loadRows()
  }
}
```

### 配置项目

如果需要修改默认项目，可以在前端代码中修改：

```javascript
await importWeeklyResults({
  project: 'reuse',  // 修改为你的项目：reuse, engine-robot, v206, V214&254
  folder_path: 'P:/error rate trend/'  // 可选：自定义路径
})
```

## 配置说明

### CSV 文件路径配置

默认路径为 `P:/error rate trend/{project}/`，可通过以下方式修改：

1. 在 `weekly_result_service.py` 中修改默认路径
2. 在 API 调用时指定 `folder_path` 参数
3. 在 cron 任务中指定 `--folder-path` 参数

### 支持的项目

- `reuse`
- `engine-robot`
- `v206`
- `V214&254`

### 等级说明

| 等级 | 说明 | UI 显示 |
|------|------|---------|
| H | 高风险 | 显示 |
| M | 中风险 | 不显示 |
| L | 低风险 | 不显示 |
| T | 跟踪 | 不显示 |
| C | 检查 | 不显示 |

## 文件结构

```
backend/
├── robots/
│   ├── models.py                       # WeeklyResult 模型
│   ├── serializers.py                  # WeeklyResult 序列化器
│   ├── views.py                        # WeeklyResult 视图
│   ├── urls.py                         # 路由配置
│   ├── weekly_result_service.py        # CSV 导入服务
│   ├── management/commands/
│   │   └── import_weekly_results.py    # 定时导入命令
│   └── migrations/
│       └── 0004_...                    # 数据库迁移文件
├── scripts/
│   └── setup_cron.sh                   # Cron 配置脚本
└── logs/
    └── cron_import.log                 # 定时任务日志

frontend/
└── src/
    └── api/
        └── robots.js                   # API 调用函数

docs/
└── weekly_result_integration.md        # 本文档
```

## 注意事项

1. **数据库迁移** - 首次使用需要运行数据库迁移：
   ```bash
   python manage.py migrate
   ```

2. **依赖包** - 确保安装了 pandas：
   ```bash
   pip install pandas
   ```

3. **文件路径** - 确保 CSV 文件路径可访问，Windows 路径使用 `/` 或 `\\`

4. **日期格式** - CSV 文件名应包含日期范围，格式如 `250410-250516`

5. **日志监控** - 定期检查定时任务日志，确保导入正常执行

## 更新记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-02-03 | 1.0 | 初始版本 |
| 2026-02-03 | 1.1 | 添加定时任务配置，UI 只显示 H 级别 |
