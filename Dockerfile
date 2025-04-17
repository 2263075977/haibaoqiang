FROM python:3.9-slim

WORKDIR /app

# 安装基础依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 安装特定版本的Chrome及其依赖
ARG CHROME_VERSION="119.0.6045.105-1"
RUN wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_${CHROME_VERSION}_amd64.deb \
    && apt-get update \
    # 安装依赖项，并允许降级以解决可能的版本冲突
    && apt-get install -y --allow-downgrades ./google-chrome-stable_${CHROME_VERSION}_amd64.deb \
        libglib2.0-0 \
        libnss3 \
        libgconf-2-4 \
        libfontconfig1 \
        libx11-xcb1 \
        libdbus-1-3 \
        libxtst6 \
        libxss1 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libgbm1 \
        libasound2 \
    && rm google-chrome-stable_${CHROME_VERSION}_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 验证Chrome版本
RUN google-chrome --version

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 环境变量配置
ENV PYTHONUNBUFFERED=1

# 暴露API端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]