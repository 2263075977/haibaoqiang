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
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# 安装固定版本的Chrome (114.0.5735.90)
RUN wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_114.0.5735.90-1_amd64.deb \
    && rm ./google-chrome-stable_114.0.5735.90-1_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 安装匹配的ChromeDriver
RUN wget -q https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 环境变量配置
ENV PYTHONUNBUFFERED=1
# 设置ChromeDriver路径
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
# 设置Chrome路径
ENV CHROME_PATH=/usr/bin/google-chrome

# 暴露API端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"] 