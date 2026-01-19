# 使用Python官方镜像
FROM python:3.10-alpine

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apk update && apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    libffi-dev \
    openssl-dev \
    make \
    git \
    curl

# 复制requirements.txt文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --upgrade pip && pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE iot_monitor.settings

# 运行Django应用（使用daphne作为ASGI服务器）
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "iot_monitor.asgi:application"]
