# Windows + NSSM 部署说明

这套项目可以放到 Windows Server，但不建议继续沿用开发态的“开一堆终端”方式。

## 先说结论

`nssm` 适合把**单个常驻进程**注册成 Windows 服务，不适合把整套前后端都塞进一个批处理后只看父进程。

这个项目按当前代码结构，更稳的拆法是：

1. `sg57-backend`
   使用 `Daphne` 跑 Django ASGI，而不是 `manage.py runserver`。
2. `sg57-bokeh`
   独立跑 `manage.py run_bi_bokeh_server`。
3. `sg57-celery-worker`
   跑 `celery worker`，Windows 下继续使用 `--pool=solo`。
4. `sg57-celery-beat`
   跑 `celery beat`。

前端不要挂 `npm run dev` 服务。生产上应先 `npm run build`，再用 IIS 或其他静态站点托管。

## 这份仓库里新增的脚本

- `deploy/windows/set_project_env.bat`
- `deploy/windows/run_backend_daphne.bat`
- `deploy/windows/run_bokeh_server.bat`
- `deploy/windows/run_celery_worker.bat`
- `deploy/windows/run_celery_beat.bat`
- `deploy/windows/install_nssm_services.bat`

## 前置条件

1. 安装 Python 虚拟环境，并保证存在 `venv57\Scripts\python.exe`。
   如果路径不是这个，先设置环境变量：

```bat
set SG57_PYTHON=D:\apps\sg57\venv\Scripts\python.exe
```

2. 后端依赖已安装完成：

```bat
cd D:\apps\sg57\backend
..\venv57\Scripts\python.exe -m pip install -r requirements.txt
```

3. 数据库可连通，`.env` 已配置。

4. Redis 必须可用。
   这套项目的 `Celery`、缓存和 `Channels` 都依赖 Redis。

## 服务安装

假设项目目录是 `D:\apps\sg57`，并且 `nssm.exe` 已加入 `PATH`。

管理员命令行执行：

```bat
cd D:\apps\sg57\deploy\windows
install_nssm_services.bat
```

如果 `nssm` 没加到 `PATH`，先指定：

```bat
set NSSM_EXE=C:\tools\nssm\nssm.exe
install_nssm_services.bat
```

安装完成后启动：

```bat
nssm start sg57-backend
nssm start sg57-bokeh
nssm start sg57-celery-worker
nssm start sg57-celery-beat
```

日志默认写到：

```text
<项目根目录>\logs\windows-services\
```

## 前端部署建议

`frontend` 当前是标准 Vite 项目，生产部署建议：

```bat
cd D:\apps\sg57\frontend
npm install
npm run build
```

然后把 `dist` 托管到 IIS。

注意两点：

1. 当前主前端里 `DevOpsView` 默认会 iframe 到 `http://localhost:5174/`。
2. 当前仓库里的 `frontend-vue` 目录缺少完整的构建配置文件，不能直接按第二个 Vite 项目部署。

所以生产上你需要二选一：

1. 提供一个真实可访问的第二站点，并把 `VITE_FRONTEND_VUE_URL` 指向它。
2. 如果这块功能不用，直接在主前端里去掉这个 iframe 页面依赖。

## 不建议的一种做法

不要把 4 个后端进程都写进一个 `start_all.bat`，再让 `nssm` 只盯这个批处理。

原因很简单：

1. 子进程挂了，`nssm` 很难精确感知。
2. 某一个服务重启时会牵连整组进程。
3. 日志、故障定位、开机自启顺序都会变差。

## 当前项目里和部署直接相关的代码点

1. 后端文档现在还是开发态多终端启动：
   `backend/docs/启动文档.md`
2. 后端已经启用了 `ASGI_APPLICATION`、`channels`、`Celery`、`Redis`：
   `backend/iot_monitor/settings.py`
3. Bokeh 是独立管理命令：
   `backend/robots/management/commands/run_bi_bokeh_server.py`
4. 数据上报接口会直接把报警检查扔给 Celery：
   `backend/monitoring/views.py`
5. 主前端会把 DevOps 页面 iframe 到另一个站点：
   `frontend/src/views/devops/DevOpsView.vue`
