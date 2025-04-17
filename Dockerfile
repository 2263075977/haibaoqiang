FROM python:3.9-slim

WORKDIR /app

# 安装Chrome依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    ca-certificates \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# 使用固定版本的Chrome，避免版本不匹配问题
RUN wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.198-1_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_114.0.5735.198-1_amd64.deb \
    && rm ./google-chrome-stable_114.0.5735.198-1_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 下载对应版本的ChromeDriver
RUN wget -q https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip -d /usr/local/bin/ \
    && rm chromedriver_linux64.zip \
    && chmod +x /usr/local/bin/chromedriver

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 环境变量配置
ENV PYTHONUNBUFFERED=1

# 设置Chrome和ChromeDriver相关环境变量
ENV CHROME_BIN=/usr/bin/google-chrome-stable
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
ENV WDM_LOG_LEVEL=0
ENV WDM_PRINT_FIRST_LINE=False

# 暴露API端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"] 