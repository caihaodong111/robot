# Standalone Data Service

一套完全独立于现有 Django 后端的采集与快照服务。

特性：

- 读取本地 `csv/xlsx` 文件
- 读取 MySQL 数据库
- 每天 `00:00` 通过 Celery Beat 生成一次总览快照
- 输出 JSON 文件，供前端或其他服务直接读取
- 不依赖现有 `backend/` 目录中的任何 Python 代码

## 当前数据源

- `WAM`: `/Users/caihd/Desktop/sg5.7/设备状态.xlsx`
- `Filling`: `/Users/caihd/Desktop/sg5.7/MRA1_filling_status.xlsx`
- `Lenze`: `/Users/caihd/Desktop/sg5.7/temperature_min_max_results.xlsx`
- `High-Risk Distribution`: MySQL `sg` 数据库

## 安装依赖

```bash
pip install -r standalone_data_service/requirements.txt
```

## 手动生成一次快照

```bash
python -m standalone_data_service.run_once
```

## 开发模式 HTTP 服务

```bash
python -m standalone_data_service.dev_api
```

接口：

- `GET /health`
- `GET /snapshot`
- `POST /refresh`

前端开发时可以直接点“刷新数据”按钮调用 `POST /refresh`。

## 启动 Celery Worker

```bash
celery -A standalone_data_service.celery_app worker -l info --pool=solo
```

## 启动 Celery Beat

```bash
celery -A standalone_data_service.celery_app beat -l info --schedule /tmp/standalone-data-service-beat.db
```

## 输出文件

- 总览快照：
  [overview_snapshot.json](/Users/caihd/Desktop/sg5.7/standalone_data_service/output/overview_snapshot.json)
- 最近任务元信息：
  [last_run_meta.json](/Users/caihd/Desktop/sg5.7/standalone_data_service/output/last_run_meta.json)

## 说明

- 这套代码中配置全部写死在 Python 文件内。
- 当前数据库读取使用独立 SQL，不调用现有项目的 Model / View / Service。
- 如需给前端使用，直接读取输出 JSON 即可。
