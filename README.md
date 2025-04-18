# 豆瓣影视数据爬取与Notion同步工具

这是一个用于从豆瓣获取影视数据并同步到Notion数据库的工具。它使用Playwright进行无头浏览器操作，通过模拟真实用户行为来避免被封锁，并使用Notion API将数据写入Notion数据库。

## 项目结构

```
项目/
├── api/                    # API模块
│   ├── __init__.py
│   └── server.py           # API服务器
├── config/                 # 配置模块
│   ├── __init__.py
│   ├── settings.py         # 全局配置项
│   └── logging_config.py   # 日志配置
├── core/                   # 核心功能
│   ├── __init__.py
│   ├── browser.py          # 浏览器管理
│   └── utils.py            # 工具函数
├── scrapers/               # 爬虫模块
│   ├── __init__.py
│   ├── base_scraper.py     # 爬虫基类
│   └── douban_scraper.py   # 豆瓣爬虫
├── parsers/                # 解析器模块
│   ├── __init__.py
│   └── douban_parser.py    # 豆瓣解析器
├── sync/                   # 同步模块
│   ├── __init__.py
│   ├── sync_base.py        # 同步基类
│   └── notion_sync.py      # Notion同步
├── main.py                 # 交互式命令行入口
├── api_server.py           # API服务器入口
├── Dockerfile              # Docker镜像构建文件
├── docker-compose.yml      # Docker Compose配置
├── .github/workflows/      # GitHub Actions工作流
├── requirements.txt        # 依赖配置
└── README.md               # 项目说明
```

## 依赖安装

```bash
pip install -r requirements.txt
playwright install chromium
```

## 配置

在使用前，需要设置以下环境变量：

- `NOTION_DATABASE_ID`: Notion数据库ID
- `NOTION_TOKEN`: Notion API Token

推荐在项目根目录创建`.env`文件来设置这些环境变量：

```
NOTION_DATABASE_ID=你的数据库ID
NOTION_TOKEN=你的API令牌
```

## 使用方法

### 交互式命令行模式

运行程序后，将进入交互式界面，按提示输入电影名称即可：

```bash
python main.py
```

程序启动后，界面如下：

```
===== 豆瓣影视数据爬取与Notion同步工具 =====

请输入电影名称 (输入q退出): 肖申克的救赎

开始处理: 肖申克的救赎

处理完成，可以继续输入下一部电影名称

请输入电影名称 (输入q退出): 
```

输入`q`可退出程序。

### API服务器模式（适用于iPhone捷径）

启动API服务器：

```bash
python api_server.py --port 6000
```

#### API端点

1. **健康检查**
   - URL: `/api/health`
   - 方法: `GET`
   - 响应示例:
     ```json
     {
       "status": "healthy",
       "message": "API服务正常运行"
     }
     ```

2. **处理电影**
   - URL: `/api/movie`
   - 方法: `POST`
   - 请求体:
     ```json
     {
       "title": "肖申克的救赎"
     }
     ```
   - 响应示例:
     ```json
     {
       "success": true,
       "title": "肖申克的救赎",
       "message": "处理成功",
       "data": {
         "title": "肖申克的救赎",
         "category": "电影",
         "rating": 9.7,
         "notion_page_id": "7d3f9a2b-5d48-4c8b-a198-6f96c3ad52e7"
       }
     }
     ```

#### iPhone捷径集成

1. 创建一个新的捷径
2. 添加"获取内容"操作
   - URL设置为你的服务器地址，如：`http://你的服务器IP:6000/api/movie`
   - 方法选择`POST`
   - 请求体类型选择`JSON`
   - 请求体内容：`{"title":"要查询的电影名称"}`
3. 添加"获取字典值"操作
   - 字典：选择上一步的输出
   - 可以取值如：`success`、`data.title`、`data.rating`等
4. 根据返回结果进行后续处理（如显示通知、添加到备忘录等）

## Docker部署

### 本地构建和运行

1. 构建Docker镜像：
   ```bash
   docker build -t haibaoqiang .
   ```

2. 运行容器：
   ```bash
   docker run -d -p 6000:6000 \
     -e NOTION_DATABASE_ID=你的数据库ID \
     -e NOTION_TOKEN=你的API令牌 \
     --name haibaoqiang \
     haibaoqiang
   ```

### 使用Docker Compose

1. 复制并编辑环境变量文件：
   ```bash
   cp .env.example .env
   # 编辑.env文件，填入你的配置
   ```

2. 启动服务：
   ```bash
   docker-compose up -d
   ```

### 在群晖Docker上部署

1. 在Docker注册表中添加镜像：`你的DockerHub用户名/haibaoqiang:latest`
2. 下载镜像并创建容器
3. 在"高级设置"中：
   - 添加环境变量：`NOTION_DATABASE_ID`和`NOTION_TOKEN`
   - 映射端口：本地端口6000到容器端口6000
   - 添加卷：创建本地文件夹映射到容器的`/app/logs`目录

## GitHub Actions自动构建

本项目配置了GitHub Actions工作流，当代码推送到main分支或创建新标签时，会自动构建Docker镜像并推送到DockerHub。

### 设置GitHub Secrets

在GitHub仓库设置中添加以下Secrets：
- `DOCKER_USERNAME`: 你的DockerHub用户名
- `DOCKER_PASSWORD`: 你的DockerHub密码或访问令牌

### 触发自动构建

- 推送到main分支会构建并推送镜像标签为`latest`和commit的SHA值
- 创建标签(如`v1.0.0`)会构建并推送对应版本的镜像

## 数据库结构

Notion数据库应包含以下属性：

- 名称 (标题类型)
- 类别 (选择类型): 电影/电视剧
- 导演 (富文本类型)
- 编剧 (富文本类型)
- 主演 (富文本类型)
- 类型 (多选类型)
- 语言 (多选类型)
- 评分 (数字类型)
- IMDb (富文本类型)
- 首播 (富文本类型)
- 简介 (富文本类型)
- 又名 (富文本类型)

## 注意事项

- 爬虫使用无头浏览器模拟真实用户行为，但仍需注意使用频率，避免被封IP
- 请确保Notion API Token具有访问目标数据库的权限
- 日志文件默认保存在logs目录下
- API服务器默认监听所有网络接口(0.0.0.0)端口6000，如需限制访问范围，请使用`--host`参数