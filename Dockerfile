FROM python:3.9-slim

WORKDIR /app

# 安装Chrome浏览器和必要依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libcairo2 \
    libcups2 \
    libxss1 \
    fonts-liberation \
    xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装固定版本的Chrome (版本 125.0.6422.141)
RUN wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_125.0.6422.141-1_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_125.0.6422.141-1_amd64.deb \
    && rm ./google-chrome-stable_125.0.6422.141-1_amd64.deb

# 安装固定版本的ChromeDriver (版本 125.0.6422.141)
RUN wget -q https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/125.0.6422.141/linux64/chromedriver-linux64.zip \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm chromedriver-linux64.zip \
    && rm -rf chromedriver-linux64

# 复制依赖文件并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有项目文件
COPY . .

# 暴露API端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV NOTION_TOKEN=your_token_here
ENV NOTION_DATABASE_ID=your_database_id_here
# 设置ChromeDriver环境变量
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV CHROME_BIN=/usr/bin/google-chrome-stable

# 使用非root用户运行
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# 运行API服务
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"] 