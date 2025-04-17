FROM python:3.9-slim

WORKDIR /app

# 安装Chrome浏览器
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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

# 使用非root用户运行
RUN useradd -m appuser
USER appuser

# 运行API服务
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"] 