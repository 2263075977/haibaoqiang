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

# 安装特定版本的Chrome
# 使用Chrome 114版本，这个版本有稳定的ChromeDriver
ARG CHROME_VERSION="114.0.5735.90-1"
RUN wget -q -O chrome.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_${CHROME_VERSION}_amd64.deb \
    && apt-get update \
    && apt install -y ./chrome.deb \
    && rm chrome.deb \
    && rm -rf /var/lib/apt/lists/*

# 设置Chrome路径环境变量
ENV CHROME_PATH=/usr/bin/google-chrome

# 手动下载匹配的ChromeDriver
RUN CHROMEDRIVER_VERSION=$(google-chrome --version | grep -oP "Chrome \K[0-9]+") \
    && wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver

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