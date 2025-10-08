# 使用官方 Python 运行时作为父镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 将依赖项文件复制到工作目录
COPY requirements.txt .

# 安装所需的包
# --no-cache-dir: 不存储缓存，减小镜像体积
# --trusted-host: 解决在国内构建时可能遇到的网络问题
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# 将 src 目录中的源代码复制到容器的 /app 目录
COPY src/ .

# 声明 API_KEY 环境变量，需要在运行时提供
ENV API_KEY=""

# 暴露端口 9999
EXPOSE 9999

# 运行 websocket_server.py
CMD ["python", "websocket_server.py"]
