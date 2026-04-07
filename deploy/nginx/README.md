# 单 Nginx 承载两个前端

目标：

- 主前端挂在 `/`
- 第二前端挂在 `/devops/`
- Django 挂在 `/api/`、`/admin/`、`/ws/`
- Bokeh 挂在 `/bi/`

## 主前端

主前端已经支持：

- 开发环境默认读取 `http://localhost:5174/`
- 生产环境默认读取 `/devops/`

相关代码：

- `frontend/src/views/devops/DevOpsView.vue`

如需显式覆盖，可在主前端构建前设置：

```env
VITE_FRONTEND_VUE_URL=/devops/
```

如果主站通过公网 IP `20.2.24.166` 访问，并且 Bokeh 通过同域名反代到 `/bi/`，后端建议显式配置：

```env
ALLOWED_HOSTS=20.2.24.166,127.0.0.1,localhost
BI_BOKEH_USE_SERVER=1
BI_BOKEH_SERVER_URL=http://20.2.24.166/bi/
BI_BOKEH_ALLOW_ORIGINS=20.2.24.166,20.2.24.166:80,20.2.24.166:443
```

这样 Django 生成的 Bokeh 脚本会直接指向公网入口 `/bi/`，而不是自动推导成 `:5008`。

## 第二前端

第二前端如果要挂在 `/devops/`，它自己的打包配置也必须使用：

```js
base: '/devops/'
```

否则打包后的静态资源路径通常会错误。

## Nginx

可直接参考：

- `deploy/nginx/nginx.single-server.conf`

里面的目录需要按你的 Windows 实际路径修改，尤其是：

- 主前端 `frontend/dist`
- 第二前端 `frontend-vue2/dist`
- Django `static/`
- Django `media/`

## 构建顺序

1. 构建主前端 `frontend`
2. 构建第二前端，并确保其 `base=/devops/`
3. 将两个 `dist` 放到 Nginx 配置指向的目录
4. 重载 Nginx

## Windows 服务重启

后端 `.env` 或 Bokeh 相关配置修改后，需要至少重启：

```bat
nssm restart sg57-backend
nssm restart sg57-bokeh
```
