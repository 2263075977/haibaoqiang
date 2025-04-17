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
    libxi6 \
    libxss1 \
    fonts-liberation \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# 安装特定版本的Chrome (114版本，较稳定)
RUN wget -q -O chrome.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.198-1_amd64.deb \
    && apt-get update \
    && apt install -y ./chrome.deb \
    && rm chrome.deb \
    && rm -rf /var/lib/apt/lists/*

# 安装匹配的ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1) \
    && CHROMEDRIVER_VERSION=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION") \
    && wget -q --no-verbose -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 环境变量配置
ENV PYTHONUNBUFFERED=1
ENV WDM_LOG_LEVEL=0
ENV WDM_PRINT_FIRST_LINE=False
# 禁用自动更新ChromeDriver，使用预装版本
ENV WDM_CHROME_VERSION=114.0.5735.198
ENV PYTHONPATH="/app:${PYTHONPATH}"

# 暴露API端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"] 