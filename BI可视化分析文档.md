# BI可视化分析文档

## 1. 概述

本项目是一个基于 Django + Bokeh 的机器人监控可视化BI系统，用于实时分析工业机器人的运行状态、能耗情况和错误率趋势。

### 技术栈
- **后端**: Django 6.0 + Django REST Framework
- **数据库**: MySQL (pymysql驱动)
- **可视化**: Bokeh 3.8.0 (交互式图表) + Matplotlib (静态图表)
- **前端**: Vue 3 + Element Plus

---

## 2. 核心模块架构

```
backend/robots/
├── bokeh_charts.py       # Bokeh交互式图表生成核心模块
├── error_trend_chart.py  # Matplotlib错误率趋势图生成
├── views.py              # Django视图和API端点
├── urls.py               # URL路由配置
└── templates/
    ├── bi.html           # BI页面完整模板
    ├── bi_embed.html     # 嵌入式模板(用于iframe)
    └── bi_error.html     # 错误页面模板
```

---

## 3. Bokeh图表模块 (`bokeh_charts.py`)

### 3.1 轴配置 (AXIS_CONFIG)

支持7轴机器人的数据映射配置：

```python
AXIS_CONFIG = {
    'A1': {'curr': 'Curr_A1', 'max_curr': 'MAXCurr_A1', 'min_curr': 'MinCurr_A1',
           'torque': 'Torque1', 'speed': 'Speed1', 'fol': 'Fol1', 'axisp': 'AxisP1'},
    # ... A2-A6 配置类似
    'A7': {'curr': 'Curr_E1', 'max_curr': 'MAXCurr_E1', 'min_curr': 'MinCurr_E1',
           'torque': 'Torque7', 'speed': 'Speed7', 'fol': 'Fol7', 'axisp': 'AxisP7'},
}
```

### 3.2 主要函数

#### `create_bi_charts()` - 核心图表生成函数

**位置**: `backend/robots/bokeh_charts.py:84-826`

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `table_name` | str | `'as33_020rb_400'` | 机器人数据表名 |
| `days` | int | `None` | (已弃用) 天数范围 |
| `axis` | str | `'A1'` | 默认显示轴 |
| `program` | str | `None` | 默认程序 |
| `start_date` | str | `None` | 开始日期 |
| `end_date` | str | `None` | 结束日期 |

**返回值**:
```python
return script, div, {
    'table_name': table_name,
    'program_name': default_program,
    'data_count': len(df_full),
    'energy_count': len(energy_full),
    'programs': programs,
    'date_range': f"{start_time} ...",
}
```

#### 数据流程

```
1. 获取数据库连接
   └─> get_db_engine() → 从Django settings读取配置

2. 获取时间范围
   └─> get_table_time_range() → SQL查询MIN/MAX Timestamp

3. 获取主数据
   └─> fetch_data_from_mysql() → 机器人运行数据

4. 获取能耗数据
   └─> energy表查询 → ENERGY, LOSTENERGY字段

5. 数据预处理
   ├─> 删除marker列, 去重
   ├─> 时区转换 (+8小时)
   ├─> 类型转换 (SNR_C→int, AxisP→float)

6. 为每个轴和程序准备数据源
   └─> ColumnDataSource (时间序列 + 聚合数据)

7. 创建图表和控件
   ├─> 7个时间序列图表
   ├─> 1个聚合分析图表
   ├─> 能耗图表(可选)
   └─> 交互控件(程序/轴选择器, 日期选择器)

8. 生成components
   └─> components(main_layout) → script + div
```

### 3.3 图表类型

| 图表 | 标题 | X轴 | Y轴 | 用途 |
|------|------|-----|-----|------|
| **p_curr** | `{Axis} - 电流分析` | sort | 电流% | 实时电流/最大/最小电流监控 |
| **p_temp** | 温度 | sort | 温度(°C) | 电机温度监控(15-100°C范围) |
| **p_pos** | 轴位置 | sort | 轴位置 | 位置跟踪 |
| **p_speed** | 电机速度 | sort | 速度 | 速度分析 |
| **p_fol** | 跟随误差 | sort | 跟随误差 | 运动精度分析 |
| **p_torque** | 扭矩 | sort | 扭矩 | 扭矩监控 |
| **line_plot** | 聚合分析 | SNR_C | 分位值 | 1%/99%分位数+Min/Max带 |
| **EnergyP** | 能耗分析 | TimeStamp2 | 能量 | 能耗与损耗能耗趋势 |

### 3.4 代理数据源模式

**核心设计思想**: 使用固定列名的代理数据源，避免动态修改渲染器属性。

```python
# 代理数据源结构
proxy_source = ColumnDataSource(data={
    'sort': [...],
    'Timestamp': [...],
    'curr_value': [...],      # 固定列名
    'max_curr_value': [...],  # 固定列名
    'torque_value': [...],    # 固定列名
    # ...
})

# 切换轴/程序时，通过JavaScript回调更新数据
proxy_source.data['curr_value'] = source.data[currCol];
proxy_source.change.emit();
```

### 3.5 JavaScript回调联动

**位置**: `backend/robots/bokeh_charts.py:621-697`

```javascript
// 触发条件: program_select或axis_select值变化
program_select.js_on_change('value', linkage_callback)
axis_select.js_on_change('value', linkage_callback)

// 回调逻辑:
1. 获取当前选择的轴和程序
2. 从axis_sources获取对应的数据源
3. 更新代理数据源的数据 (复制到固定列名)
4. 更新图表标题
5. 触发数据更新事件
```

### 3.6 日期范围选择器

**实现方式**: 自定义HTML + JavaScript弹窗

```python
date_range_html = f'''
<div id="dateDisplay_{unique_id}">
    📅 {start_date_val} ~ {end_date_val}
</div>
<div id="datePopup_{unique_id}">  <!-- 弹窗 -->
    <input type="date" id="start_{unique_id}">
    <input type="date" id="end_{unique_id}">
    <button onclick="applyDateRange_{unique_id}()">应用</button>
</div>
'''
```

### 3.7 能耗模态框

**特点**: 独立的Bokeh图表，通过模态框显示

```python
energy_modal_html = f'''
<style>.energy-modal-bg-{{...}} {{ ... }}</style>
<div id="{energy_modal_id}_chart">{energy_div_content}</div>
<script>
function showEnergyModal_{id}() {{ /* 显示模态框 */ }}
function closeEnergyModal_{id}() {{ /* 关闭模态框 */ }}
</script>
{energy_script_content}
'''
```

---

## 4. 错误率趋势图模块 (`error_trend_chart.py`)

### 4.1 技术选型

使用 **Matplotlib** 而非 Bokeh，原因：
- 生成静态PNG图片
- 适合批量生成和历史归档
- 不需要实时交互

### 4.2 核心函数

#### `generate_trend_chart()`

**位置**: `backend/robots/error_trend_chart.py:20-56`

```python
def generate_trend_chart(robot_part_no: str, axis_num: int) -> str:
    """
    生成机器人关节错误率趋势图

    Args:
        robot_part_no: 机器人部件编号 (如 as33_020rb_400)
        axis_num: 关节编号 (1-7)

    Returns:
        str: 生成的图片文件路径
    """
    # CSV文件路径: {robot_part_no}-error-rate-trend.csv
    # 输出文件: {robot_part_no}_{axis_num}_trend.png
```

#### `_draw_chart()`

**位置**: `backend/robots/error_trend_chart.py:59-163`

生成7个子图的趋势分析：
1. **位置 (Q1-Q7)**: 关节位置变化
2. **错误率 (A1_e_rate - A7_e_rate)**: 错误发生频率
3. **RMS (A1_Rms - A7_Rms)**: 均方根值
4. **最小电流 (Curr_A1_min - Curr_A7_min)**: 最小电流趋势
5. **最大电流 (Curr_A1_max - Curr_A7_max)**: 最大电流趋势
6. **温度 (tem1_m - tem7_m)**: 温度监控
7. **错误计数 (error1_c1)**: 错误事件统计

```python
fig = plt.figure(figsize=(10, 15))
gs = fig.add_gridspec(7, 1, height_ratios=[1, 1, 1, 1, 1, 1, 1])
axes = [fig.add_subplot(gs[i]) for i in range(7)]
```

---

## 5. Django视图和API (`views.py`)

### 5.1 BI页面视图

**位置**: `backend/robots/views.py:334-393`

```python
@xframe_options_exempt
def bi_view(request):
    """
    BI可视化页面 - 使用Bokeh components静态嵌入
    支持程序、轴、时间范围选择
    支持embed参数：embed=1时返回纯净模板用于iframe嵌入
    """
    # URL参数:
    # ?robot=as33_020rb_400  (优先于table参数)
    # ?table=as33_020rb_400
    # ?embed=1               (嵌入模式)
    # ?program=xxx
    # ?axis=A1
    # ?start_date=2024-01-01
    # ?end_date=2024-01-31
```

### 5.2 API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/robots/bi/` | GET | BI可视化页面 |
| `/api/robots/bi_robots/` | GET | 获取机器人选择列表 |
| `/api/robots/components/{pk}/error_trend_chart/` | GET | 获取错误率趋势图 |
| `/api/robots/charts/<filename>` | GET | 提供图表图片服务 |

### 5.3 错误率趋势图API

**位置**: `backend/robots/views.py:206-275`

```python
@action(detail=True, methods=["get"])
def error_trend_chart(self, request, pk=None):
    """
    参数:
        axis: 关节编号 (1-7)，必填
        regenerate: 是否重新生成图表 (0/1)，默认为0

    返回:
        {
            "success": true,
            "chart_url": "/api/robots/charts/robot_1_trend.png",
            "axis": 1
        }
    """
```

### 5.4 机器人选择列表API

**位置**: `backend/robots/views.py:171-204`

```python
@action(detail=False, methods=["get"])
def bi_robots(self, request):
    """获取BI可视化机器人选择列表"""
    # 参数:
    # ?group=plant_a      (车间过滤)
    # ?keyword=RB001      (搜索关键词)
```

---

## 6. URL路由配置 (`urls.py`)

**位置**: `backend/robots/urls.py`

```python
urlpatterns = [
    path("bi/", bi_view, name="robot-bi"),                          # BI页面
    path("charts/<path:filename>", serve_chart, name="robot-chart"), # 图表服务
    path("", include(router.urls)),                                  # API路由
]
```

### 图表服务函数

```python
def serve_chart(request, filename):
    """
    提供错误率趋势图文件服务
    文件路径: ERROR_RATE_CHART_PATH / filename
    """
    file_path = os.path.join(CHART_OUTPUT_PATH, filename)
    return FileResponse(open(file_path, 'rb'), content_type='image/png')
```

---

## 7. 配置设置 (`settings.py`)

**位置**: `backend/iot_monitor/settings.py:262-266`

```python
# ==================== 机器人错误率趋势图配置 ====================
# CSV 数据文件存储路径
ERROR_RATE_CSV_PATH = '/Users/caihd/Desktop/sg'
# 图表生成输出路径
ERROR_RATE_CHART_PATH = '/Users/caihd/Desktop/sg/charts'
```

---

## 8. 前端模板

### 8.1 嵌入式模板 (`bi_embed.html`)

**特点**:
- 精简设计，用于iframe嵌入
- 加载Bokeh CDN资源 (3.8.0版本)
- 响应式布局
- Element Plus样式集成

**CDN资源**:
```html
<!-- Bokeh CSS -->
<link rel="stylesheet" href="https://cdn.pydata.org/bokeh/release/bokeh-3.8.0.min.css" />

<!-- Bokeh JS -->
<script src="https://cdn.pydata.org/bokeh/release/bokeh-3.8.0.min.js"></script>
<script src="https://cdn.pydata.org/bokeh/release/bokeh-widgets-3.8.0.min.js"></script>
<script src="https://cdn.pydata.org/bokeh/release/bokeh-tables-3.8.0.min.js"></script>
<script src="https://cdn.pydata.org/bokeh/release/bokeh-gl-3.8.0.min.js"></script>
```

### 8.2 错误页面 (`bi_error.html`)

当数据获取失败时显示，包含错误信息和表名。

---

## 9. 数据库表结构

### 9.1 机器人数据表

以机器人部件编号命名，如 `as33_020rb_400`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `Timestamp` | datetime | 时间戳 |
| `Name_C` | string | 程序名称 |
| `SNR_C` | int | 序列号 |
| `P_name` | string | 路径名称 |
| `Curr_A1~A7` | float | 实时电流 |
| `MAXCurr_A1~A7` | float | 最大电流 |
| `MinCurr_A1~A7` | float | 最小电流 |
| `Torque1~7` | float | 扭矩 |
| `Speed1~7` | float | 速度 |
| `Fol1~7` | float | 跟随误差 |
| `AxisP1~7` | float | 轴位置 |
| `Tem_1` | float | 温度 |

### 9.2 能耗表 (`energy`)

| 字段 | 类型 | 说明 |
|------|------|------|
| `RobotName` | string | 机器人名称(对应表名) |
| `TimeStamp2` | datetime | 时间戳 |
| `ENERGY` | float | 能耗 |
| `LOSTENERGY` | float | 损耗能耗 |

### 9.3 Django模型表

- `RobotComponent`: 机器人组件
- `RobotGroup`: 机器人分组(车间)
- `RiskEvent`: 风险事件

---

## 10. 依赖包 (`requirements.txt`)

```
# Bokeh相关
bokeh>=3.0

# 数据库
pymysql>=1.0.2
mysqlclient>=2.1.0
SQLAlchemy>=2.0.0

# 数据处理
pandas>=2.0.0

# 图表
matplotlib>=3.7.0
```

---

## 11. 使用示例

### 11.1 访问BI页面

```
# 基本访问
http://localhost:8000/api/robots/bi/

# 指定机器人
http://localhost:8000/api/robots/bi/?robot=as33_020rb_400

# 嵌入模式
http://localhost:8000/api/robots/bi/?robot=as33_020rb_400&embed=1

# 带过滤条件
http://localhost:8000/api/robots/bi/?robot=as33_020rb_400&axis=A1&program=PROG_01&start_date=2024-01-01&end_date=2024-01-31
```

### 11.2 前端集成

```javascript
// iframe嵌入
<iframe
  src="/api/robots/bi/?robot=as33_020rb_400&embed=1"
  width="100%"
  height="800px"
  frameborder="0"
></iframe>
```

### 11.3 API调用示例

```javascript
// 获取机器人列表
fetch('/api/robots/bi_robots/?group=plant_a&keyword=RB001')
  .then(r => r.json())
  .then(data => console.log(data.results))

// 获取错误率趋势图
fetch('/api/robots/components/1/error_trend_chart/?axis=1&regenerate=1')
  .then(r => r.json())
  .then(data => {
    console.log(data.chart_url)
    // /api/robots/charts/as33_020rb_400_1_trend.png
  })
```

---

## 12. 关键设计模式

### 12.1 静态嵌入 vs Bokeh Server

本项目采用 **静态嵌入** 方式，而非 Bokeh Server：

| 特性 | 静态嵌入 | Bokeh Server |
|------|----------|--------------|
| 部署复杂度 | 低 | 高 |
| 实时数据更新 | 通过JavaScript回调 | WebSocket |
| Python回调 | 不支持 | 支持 |
| 适用场景 | 中小型应用 | 大型实时应用 |

### 12.2 代理数据源模式

**优势**:
1. **简化联动逻辑**: 切换轴/程序时只需更新数据，无需修改渲染器
2. **提高性能**: 避免重新创建图表对象
3. **代码可维护性**: 固定列名使代码更清晰

### 12.3 图表布局策略

```python
# 垂直布局: 模态框 + 控件 + 图表
main_layout = column(
    energy_modal_div,    # 高度为0，绝对定位
    top_controls,        # 控件栏
    charts_column,       # 图表区域
    sizing_mode="stretch_width",
    width=2100
)
```

---

## 13. 性能优化

### 13.1 数据查询优化

```python
# 使用索引字段
WHERE `Timestamp` BETWEEN ? AND ?

# 预处理减少前端计算
df_full = df_full.drop_duplicates()
df_full['Time'] = pd.to_datetime(df_full['Timestamp']) + timedelta(hours=8)
```

### 13.2 渲染优化

```python
# 使用sizing_mode自动适配
sizing_mode="stretch_width"

# 共享x_range减少内存
x_range=p_curr.x_range
```

---

## 14. 错误处理

### 14.1 数据库连接失败

```python
try:
    engine = create_engine(f'mysql+pymysql://...')
except Exception as e:
    logger.error(f"数据库连接失败: {e}")
    return None, None, None  # 返回空值，显示错误页面
```

### 14.2 空数据处理

```python
if df_full.empty:
    logger.warning(f"表 {table_name} 没有数据")
    return None, None, None
```

### 14.3 参数验证

```python
if axis_num < 1 or axis_num > 7:
    raise ValueError(f"axis_num 必须在 1-7 之间")
```

---

## 15. 开发建议

### 15.1 添加新图表

1. 在 `AXIS_CONFIG` 中添加新字段映射
2. 在 `create_bi_charts()` 中创建新 figure
3. 更新 `proxy_source` 添加新列
4. 在 JavaScript 回调中添加数据复制逻辑

### 15.2 调试技巧

```python
# 启用详细日志
import logging
logger = logging.getLogger(__name__)
logger.info(f"图表生成成功: script长度={len(script)}")

# 检查数据源
print(f"可用程序列表: {programs}")
print(f"加载数据条数: {len(df_full)}")
```

---

## 16. 文件索引

| 文件 | 行数范围 | 功能 |
|------|----------|------|
| `bokeh_charts.py` | 1-827 | Bokeh图表生成核心 |
| `bokeh_charts.py` | 20-29 | 轴配置定义 |
| `bokeh_charts.py` | 84-229 | 数据获取和预处理 |
| `bokeh_charts.py` | 233-332 | 控件创建 |
| `bokeh_charts.py` | 334-593 | 图表创建 |
| `bokeh_charts.py` | 618-697 | JavaScript联动回调 |
| `bokeh_charts.py` | 702-814 | 布局组装 |
| `error_trend_chart.py` | 1-180 | Matplotlib趋势图 |
| `views.py` | 334-393 | BI页面视图 |
| `views.py` | 206-275 | 错误趋势图API |
| `urls.py` | 18-30 | 图表文件服务 |

---

*文档生成时间: 2026-02-02*
*Bokeh版本: 3.8.0*
*Django版本: 6.0.1*
