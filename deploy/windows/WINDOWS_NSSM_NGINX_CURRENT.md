# Windows NSSM + Nginx 当前部署说明

这份文档总结当前项目在 Windows Server 上的后端服务拆分、`nssm` 注册方式、双前端 `nginx` 静态部署方式，以及当前实际跑通时需要注意的配置点。

## 1. 当前架构

当前项目在服务器上的角色分工是：

- `sg57-backend`
  Django ASGI 服务，端口 `8001`
- `sg57-bokeh`
  Bokeh 独立服务，端口 `5008`
- `sg57-celery-worker`
  Celery worker
- `sg57-celery-beat`
  Celery beat
- `nginx`
  对外统一入口，当前监听端口 `5173`

前端是两个静态站点：

- 主前端
  外部访问 `/`
- 第二前端
  外部访问 `/devops/`
- 主前端内部的 `/devops` 路由页
  通过 `iframe` 嵌入 `/devops/`

## 2. NSSM 服务拆分

仓库内的服务安装脚本：

- [set_project_env.bat](/Users/caihd/Desktop/sg5.7/deploy/windows/set_project_env.bat)
- [run_backend_daphne.bat](/Users/caihd/Desktop/sg5.7/deploy/windows/run_backend_daphne.bat)
- [run_bokeh_server.bat](/Users/caihd/Desktop/sg5.7/deploy/windows/run_bokeh_server.bat)
- [run_celery_worker.bat](/Users/caihd/Desktop/sg5.7/deploy/windows/run_celery_worker.bat)
- [run_celery_beat.bat](/Users/caihd/Desktop/sg5.7/deploy/windows/run_celery_beat.bat)
- [install_one_nssm_service.bat](/Users/caihd/Desktop/sg5.7/deploy/windows/install_one_nssm_service.bat)
- [install_nssm_services.bat](/Users/caihd/Desktop/sg5.7/deploy/windows/install_nssm_services.bat)

当前推荐的服务名：

- `sg57-backend`
- `sg57-bokeh`
- `sg57-celery-worker`
- `sg57-celery-beat`

## 3. 服务启动命令对应关系

### 3.1 backend

`sg57-backend` 实际调用：

```bat
python -m daphne -b 0.0.0.0 -p 8001 iot_monitor.asgi:application
```

对应脚本：
[run_backend_daphne.bat](/Users/caihd/Desktop/sg5.7/deploy/windows/run_backend_daphne.bat)

### 3.2 bokeh

`sg57-bokeh` 应当调用：

```bat
python manage.py run_bi_bokeh_server --port 5008 --address 0.0.0.0 --prefix /bi
```

注意：

- 当前仓库原始 [run_bokeh_server.bat](/Users/caihd/Desktop/sg5.7/deploy/windows/run_bokeh_server.bat) 默认只带 `--port` 和 `--address`
- 如果外部通过 `nginx /bi/` 反代访问 Bokeh，必须补上 `--prefix /bi`
- 否则 Bokeh 生成的资源路径会落到 `/static/js/bokeh*.js` 根路径，和 Django `/static/` 冲突

另外，Bokeh 启动命令对应的 Python 代码在：
[run_bi_bokeh_server.py](/Users/caihd/Desktop/sg5.7/backend/robots/management/commands/run_bi_bokeh_server.py)

### 3.3 celery worker

```bat
python -m celery -A iot_monitor worker -l info --pool=solo
```

对应脚本：
[run_celery_worker.bat](/Users/caihd/Desktop/sg5.7/deploy/windows/run_celery_worker.bat)

### 3.4 celery beat

```bat
python -m celery -A iot_monitor beat -l info --schedule "<项目根目录>\run\celerybeat-schedule" --pidfile "<项目根目录>\run\celerybeat.pid"
```

对应脚本：
[run_celery_beat.bat](/Users/caihd/Desktop/sg5.7/deploy/windows/run_celery_beat.bat)

## 4. NSSM 常用命令

安装：

```bat
cd C:\RobotUI\sg5.7\deploy\windows
install_nssm_services.bat
```

启动：

```bat
nssm start sg57-backend
nssm start sg57-bokeh
nssm start sg57-celery-worker
nssm start sg57-celery-beat
```

重启：

```bat
nssm restart sg57-backend
nssm restart sg57-bokeh
nssm restart sg57-celery-worker
nssm restart sg57-celery-beat
```

查看状态：

```bat
nssm status sg57-backend
nssm status sg57-bokeh
nssm status sg57-celery-worker
nssm status sg57-celery-beat
```

查看某个服务的启动配置：

```bat
nssm get sg57-bokeh Application
nssm get sg57-bokeh AppParameters
nssm get sg57-bokeh AppDirectory
```

## 5. 服务日志目录

当前服务日志目录：

```text
C:\RobotUI\sg5.7\logs\windows-services
```

重点日志：

- `backend.out.log`
- `backend.err.log`
- `bokeh.out.log`
- `bokeh.err.log`
- `celery-worker.out.log`
- `celery-worker.err.log`
- `celery-beat.out.log`
- `celery-beat.err.log`

出现以下问题时优先看 `bokeh.err.log`：

- `/bi/` 返回 `502 Bad Gateway`
- `/bi/` 返回 `500 Internal Server Error`
- 前端控制台里 Bokeh `autoload.js` 或 WebSocket 报错

## 6. 当前前端静态目录放法

当前跑通方式是把两个前端都放到 `nginx` 安装目录下的 `html` 子目录：

- 主前端目录：
  `C:\Users\azure\Desktop\nginx-1.28.3\nginx-1.28.3\html\main`
- 第二前端目录：
  `C:\Users\azure\Desktop\nginx-1.28.3\nginx-1.28.3\html\devops`

目录内容要求：

- `html\main\index.html` 存在
- `html\devops\index.html` 存在

复制示例：

```bat
xcopy C:\RobotUI\sg5.7\frontend\dist\* C:\Users\azure\Desktop\nginx-1.28.3\nginx-1.28.3\html\main\ /E /I /Y
xcopy C:\RobotUI\sg5.7\frontend-vue\dist\* C:\Users\azure\Desktop\nginx-1.28.3\nginx-1.28.3\html\devops\ /E /I /Y
```

## 7. 当前 Nginx 实际访问关系

当前对外入口端口：

- `5173`

访问关系：

- `http://20.2.24.166:5173/`
  主前端首页
- `http://20.2.24.166:5173/devops`
  主前端里的嵌套路由页
- `http://20.2.24.166:5173/devops/`
  第二前端本体
- `http://20.2.24.166:5173/api/`
  Django API
- `http://20.2.24.166:5173/admin/`
  Django Admin
- `http://20.2.24.166:5173/bi/`
  Bokeh 入口

注意：

- `/devops` 和 `/devops/` 不是同一个地址
- `/devops` 是主前端路由
- `/devops/` 是第二前端静态站点

## 8. 当前 Nginx 完整配置

服务器当前可用配置应当类似下面这样：

```nginx
#user  nobody;
worker_processes  1;

pid        logs/nginx.pid;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;

    server {
        listen 5173;
        server_name 20.2.24.166;

        client_max_body_size 50m;

        root C:/Users/azure/Desktop/nginx-1.28.3/nginx-1.28.3/html/main;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location /devops/ {
            alias C:/Users/azure/Desktop/nginx-1.28.3/nginx-1.28.3/html/devops/;
            try_files $uri $uri/ /devops/index.html;
        }

        location /api/ {
            proxy_pass http://127.0.0.1:8001;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
        }

        location /admin/ {
            proxy_pass http://127.0.0.1:8001;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
        }

        location /ws/ {
            proxy_pass http://127.0.0.1:8001;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
        }

        location /bi/ {
            proxy_pass http://127.0.0.1:5008/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        location ~ ^/static/js/bokeh.*\.js$ {
            proxy_pass http://127.0.0.1:5008;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
        }

        location /static/ {
            alias C:/RobotUI/sg5.7/backend/static/;
            access_log off;
            expires 7d;
        }

        location /media/ {
            alias C:/RobotUI/sg5.7/backend/media/;
            access_log off;
            expires 7d;
        }
    }
}
```

这里最关键的一个补丁是：

```nginx
location ~ ^/static/js/bokeh.*\.js$ {
    proxy_pass http://127.0.0.1:5008;
}
```

原因：

- 当前 Bokeh `autoload.js` 仍会请求根路径的 `/static/js/bokeh*.js`
- 如果不单独转发，这些请求会被 Django `/static/` 接走，最终 404

## 9. Bokeh 当前必须配置的环境变量

如果前端入口仍然走 `5173`，后端 `.env` 至少要有：

```env
BI_BOKEH_USE_SERVER=1
BI_BOKEH_PREFIX=/bi
BI_BOKEH_SERVER_URL=http://20.2.24.166:5173/bi/
BI_BOKEH_ALLOW_ORIGINS=20.2.24.166:5173,172.21.0.8:5173,127.0.0.1:5173,localhost:5173
```

作用：

- `BI_BOKEH_SERVER_URL`
  让 Django 生成的 `autoload.js` 指向 `nginx /bi/`，而不是直连 `5008`
- `BI_BOKEH_PREFIX`
  告诉 Bokeh 当前处在 `/bi` 反代前缀下
- `BI_BOKEH_ALLOW_ORIGINS`
  放行当前页面来源的 WebSocket 连接

## 10. Nginx 启动与重载

当前 `nginx.exe` 目录：

```text
C:\Users\azure\Desktop\nginx-1.28.3\nginx-1.28.3
```

常用命令：

```bat
cd C:\Users\azure\Desktop\nginx-1.28.3\nginx-1.28.3
nginx.exe -t
nginx.exe
nginx.exe -s reload
taskkill /F /IM nginx.exe
```

查看完整生效配置：

```bat
nginx.exe -T
```

## 11. 当前最容易踩的坑

### 11.1 把 `frontend/dist` 和 `frontend-vue/dist` 都丢进同一个目录

不行。

要拆成：

- `html/main`
- `html/devops`

### 11.2 `/devops` 和 `/devops/` 混用

- `/devops`
  主前端路由
- `/devops/`
  第二前端静态站点

### 11.3 Bokeh 服务虽然被 NSSM 标成 `SERVICE_RUNNING`，但 5008 没监听

出现这种情况时优先看：

- `bokeh.err.log`
- `bokeh.out.log`

因为这通常说明：

- 批处理命令参数不对
- 环境变量不对
- 启动后立刻报错退出

### 11.4 `Welcome to nginx!`

说明当前访问到的是默认站点，不是项目配置。  
应检查：

- `nginx.exe -T`
- `conf/nginx.conf`
- 当前 `root` 和 `alias` 是否指向实际目录

### 11.5 Bokeh 控制台报 `/static/js/bokeh*.js 404`

说明 Bokeh 静态 JS 被 Django `/static/` 接走了。  
解决方式就是在 `nginx.conf` 里增加：

```nginx
location ~ ^/static/js/bokeh.*\.js$ {
    proxy_pass http://127.0.0.1:5008;
}
```

## 12. 最终检查清单

后端服务：

- `sg57-backend` 已启动
- `sg57-bokeh` 已启动
- `sg57-celery-worker` 已启动
- `sg57-celery-beat` 已启动

端口：

- `8001` Django 正在监听
- `5008` Bokeh 正在监听
- `5173` Nginx 正在监听

前端目录：

- `html/main/index.html` 存在
- `html/devops/index.html` 存在

Nginx：

- `nginx.exe -t` 成功
- `nginx.exe -T` 输出为项目配置

页面：

- `http://20.2.24.166:5173/` 可打开主前端
- `http://20.2.24.166:5173/devops/` 可打开第二前端
- 主前端中的 BI 页不再报 `5008` 直连超时

