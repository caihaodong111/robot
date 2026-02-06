# CSV 本地路径配置说明

本文档列出了系统中所有需要配置本地 CSV 文件路径的位置。

---

## 配置项汇总

| 序号 | 配置项 | 默认路径 | 配置位置 | 用途 |
|:---:|:---|:---|:---|:---|
| 1 | `ERROR_RATE_CSV_PATH` | `P:/` | `settings.py` / `.env` | 机器人错误率趋势图数据源 |
| 2 | 机器人配置文件路径 | `{项目根目录}/机器人配置文件.csv` | `robot_config_sync.py` | 机器人配置同步 |
| 3 | Reference 字典文件 | `{项目根目录}/dic information .csv` | `tasks.py` | 机器人 reference 字典 |
| 4 | WeeklyResult 文件目录 | `/Users/caihd/Desktop/sg` | `weekly_result_service.py` | 周检查结果导入 |

---

## 详细配置说明

### 1. 错误率趋势图 CSV

**文件路径配置：** `backend/iot_monitor/settings.py` 或 `.env`

```python
# settings.py
ERROR_RATE_CSV_PATH = '/path/to/csv/files'  # 替换为实际路径
```

或在 `.env` 文件中：
```bash
ERROR_RATE_CSV_PATH=/path/to/csv/files
```

**文件命名格式：** `{robot_part_no}-error-rate-trend.csv`

**示例：**
```
/as33_020rb_400-error-rate-trend.csv
/HC41_010RB_100-error-rate-trend.csv
/UB43_360RB_100-error-rate-trend.csv
```

**代码位置：** `backend/robots/error_trend_chart.py:16`

---

### 2. 机器人配置 CSV

**文件路径配置：** `backend/robots/robot_config_sync.py:15`

```python
DEFAULT_CSV_PATH = Path(settings.BASE_DIR).parent / "机器人配置文件.csv"
```

**文件命名格式：** `机器人配置文件.csv`

**默认位置：** 项目根目录（与 `backend` 同级）

**代码位置：** `backend/robots/robot_config_sync.py`

**用途：** 机器人数据编辑后同步到本地 CSV 文件

---

### 3. Reference 字典 CSV

**文件路径配置：** `backend/robots/tasks.py:20`

```python
csv_path = Path(settings.BASE_DIR).parent / "dic information .csv"
```

**文件命名格式：** `dic information .csv`（注意文件名有空格）

**默认位置：** 项目根目录（与 `backend` 同级）

**代码位置：** `backend/robots/tasks.py:20`

**用途：** 存储 robot、reference、number 的映射关系，通过 API 刷新到数据库

---

### 4. WeeklyResult CSV

**文件路径配置：** `backend/robots/weekly_result_service.py:198`

```python
if folder_path is None:
    folder_path = '/Users/caihd/Desktop/sg'  # 需要修改为实际路径
```

**文件命名格式：** `*weeklyresult.csv`

**示例：**
```
2.4_weeklyresult.csv
1.30_weeklyresult.csv
```

**代码位置：** `backend/robots/weekly_result_service.py:356`

**用途：** 导入周检查结果数据到 `robot_components` 表

**触发方式：**
- 手动同步：机器人状态页面点击"同步数据"按钮
- 自动同步：Celery Beat 每天凌晨 00:00 执行

---

## 项目目录结构示例

```
/Users/caihd/Desktop/sg/
├── backend/
│   ├── iot_monitor/
│   │   └── settings.py
│   └── robots/
│       ├── error_trend_chart.py
│       ├── robot_config_sync.py
│       ├── tasks.py
│       └── weekly_result_service.py
├── frontend/
├── 机器人配置文件.csv          # 配置项 2
├── dic information .csv        # 配置项 3
└── 2.4_weeklyresult.csv        # 配置项 4
```

---

## 环境变量配置建议

在 `.env` 文件中集中配置：

```bash
# 错误率趋势图 CSV 路径
ERROR_RATE_CSV_PATH=/path/to/error_rate/files

# WeeklyResult CSV 目录路径
WEEKLY_RESULT_CSV_PATH=/Users/caihd/Desktop/sg
```

---

## 相关 API 端点

| 端点 | 方法 | 用途 |
|:---|:---:|:---|
| `/api/robots/components/import_csv/` | POST | 手动导入 weeklyresult.csv |
| `/api/robots/reference-dict/refresh/` | POST | 刷新 reference 字典 |
| `/api/robots/{pk}/error_trend_chart/` | GET | 获取错误率趋势图 |

---

## 注意事项

1. **文件编码**：大部分 CSV 使用 `utf-8-sig` 编码，关键轨迹检查相关使用 `gbk` 编码
2. **文件名空格**：`dic information .csv` 文件名包含空格，需要注意
3. **路径分隔符**：使用 `pathlib.Path` 或 `os.path.join` 处理路径，保证跨平台兼容性
4. **定时任务**：Celery Beat 需要确保配置的路径存在且可读

---

*文档生成时间：2026-02-06*
