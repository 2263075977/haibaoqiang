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

# 安装Chrome使用官方仓库
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置Chrome路径环境变量
ENV CHROME_PATH=/usr/bin/google-chrome

# 检查Chrome版本并下载对应的ChromeDriver
RUN echo "正在获取Chrome版本..." \
    && google-chrome --version || echo "Chrome版本检测失败" \
    && CHROME_VERSION=$(google-chrome --version | grep -oP "Chrome \K[0-9]+\.[0-9]+\.[0-9]+") \
    && echo "解析到Chrome版本: ${CHROME_VERSION}" \
    && CHROME_MAJOR_VERSION="${CHROME_VERSION%%.*}" \
    && echo "Chrome主版本: ${CHROME_MAJOR_VERSION}" \
    && echo "尝试获取ChromeDriver版本..." \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}") \
    && echo "获取到ChromeDriver版本: ${CHROMEDRIVER_VERSION}" \
    && echo "开始下载ChromeDriver..." \
    && wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
    && echo "解压ChromeDriver..." \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver \
    && echo "ChromeDriver安装完成" \
    && ls -la /usr/local/bin/chromedriver \
    && /usr/local/bin/chromedriver --version

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