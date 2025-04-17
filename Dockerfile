FROM python:3.9-slim

WORKDIR /app

# 安装Chrome依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    ca-certificates \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# 安装特定版本的Chrome 114
RUN wget -q -O chrome.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.198-1_amd64.deb \
    && apt-get update \
    && apt install -y ./chrome.deb \
    && rm chrome.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置Chrome路径环境变量
ENV CHROME_PATH=/usr/bin/google-chrome

# 使用固定版本的ChromeDriver 114.0.5735.90（与Chrome 114兼容）
RUN echo "安装ChromeDriver 114.0.5735.90..." \
    && wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver

# 验证Chrome和ChromeDriver版本
RUN google-chrome --version && /usr/local/bin/chromedriver --version

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 环境变量配置
ENV PYTHONUNBUFFERED=1
# 禁用自动下载ChromeDriver，使用预先下载的版本
ENV WDM_LOCAL=1
ENV WDM_CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# 暴露API端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"] 