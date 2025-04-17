# 豆瓣影视数据爬取到Notion工具

这是一个自动化工具，用于从豆瓣网站搜索和提取电影/电视剧信息，然后将详细数据添加到Notion数据库。

## 功能特点

- 🔍 **搜索豆瓣电影/电视剧**：根据关键词搜索影视作品
- 📝 **提取详细信息**：自动获取导演、编剧、演员、类型、评分等详细信息
- 🖼️ **格式化剧情简介**：自动为简介添加段落和中文缩进格式
- 🔗 **人员链接支持**：导演、编剧、演员信息包含原始豆瓣链接
- 📊 **自动分类**：自动识别电影和电视剧
- 📲 **Notion集成**：将所有数据自动添加到Notion数据库

## 安装说明

### 前提条件

- Python 3.7+
- Chrome浏览器
- Notion账户和API密钥

### 安装步骤

1. 克隆或下载本项目
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 创建`.env`文件，设置以下环境变量：
   ```
   # Notion相关
   NOTION_TOKEN=your_notion_integration_token
   NOTION_DATABASE_ID=your_notion_database_id
   
   # 豆瓣Cookie相关(可选)
   DOUBAN_BID=your_douban_bid
   DOUBAN_LL=your_douban_ll
   DOUBAN_DBCL2=your_douban_dbcl2
   DOUBAN_CK=your_douban_ck
   ```

## Notion数据库设置

在Notion中创建一个数据库，并确保包含以下属性：

- **名称** (标题类型)：影片标题
- **类别** (选择类型)：电影/电视剧
- **导演** (富文本类型)：导演信息
- **编剧** (富文本类型)：编剧信息
- **主演** (富文本类型)：演员信息
- **类型** (多选类型)：影片类型标签
- **语言** (多选类型)：影片语言
- **评分** (数字类型)：豆瓣评分
- **IMDb** (富文本类型)：IMDb编号
- **首播** (富文本类型)：上映日期
- **简介** (富文本类型)：影片剧情简介
- **又名** (富文本类型)：影片别名

然后，将数据库与你创建的Notion集成共享。

## 使用方法

### 命令行模式

运行主程序：

```bash
python main.py
```

1. 输入要搜索的电影或电视剧名称
2. 程序自动选择最匹配的影片并提取详情
3. 详情信息自动添加到Notion数据库

操作简单，一键完成从搜索到添加的全过程。

### API服务模式

启动API服务器：

```bash
python api.py
```

服务启动后，将在 http://localhost:8000 提供以下API端点：

- **POST /search** - 搜索电影
  ```json
  {"keyword": "电影名称"}
  ```

- **POST /movie/details** - 获取电影详情
  ```json
  {"url": "豆瓣电影URL"}
  ```

- **POST /add_to_notion** - 添加电影到Notion
  ```json
  {"movie_data": {...电影详细信息...}}
  ```

- **POST /search_and_add** - 一站式搜索并添加
  ```json
  {"keyword": "电影名称"}
  ```

API服务器自带交互式文档，访问 http://localhost:8000/docs 查看详细API说明。

### API客户端示例

提供了示例客户端脚本，展示如何调用API：

```bash
# 一站式模式
python api_client_example.py 电影名称

# 分步骤模式
python api_client_example.py --steps 电影名称
```

## 注意事项

- 本工具仅供个人学习和研究使用
- 请遵守豆瓣网站的使用条款和robots.txt规定
- 频繁抓取数据可能导致IP被限制，请适度使用

## 许可证

MIT 

## Docker部署

### 使用Selenium官方镜像（推荐）

本项目现在使用Selenium官方镜像，提供更稳定的Chrome和ChromeDriver支持：

```bash
docker run -d --name douban-notion-api \
  -p 8000:8000 \
  -e NOTION_TOKEN=your_token_here \
  -e NOTION_DATABASE_ID=your_database_id_here \
  ghcr.io/your-username/douban-notion:selenium
```

### 使用预构建镜像（原版）

```bash
docker run -d --name douban-notion-api \
  -p 8000:8000 \
  -e NOTION_TOKEN=your_token_here \
  -e NOTION_DATABASE_ID=your_database_id_here \
  ghcr.io/your-username/douban-notion:latest
```

### 使用Docker Compose

1. 克隆仓库
```bash
git clone https://github.com/your-username/douban-notion.git
cd douban-notion
```

2. 创建.env文件
```
NOTION_TOKEN=your_token_here
NOTION_DATABASE_ID=your_database_id_here
DOUBAN_BID=your_douban_bid
DOUBAN_LL=your_douban_ll
DOUBAN_DBCL2=your_douban_dbcl2
DOUBAN_CK=your_douban_ck
```

3. 启动服务
```bash
docker-compose up -d
```

## 在群晖上部署

### 方法一：使用Docker软件包

1. 在群晖DSM中打开Docker应用
2. 在"注册表"中搜索`ghcr.io/your-username/douban-notion`
3. 选择并下载带有`selenium`标签的镜像版本（推荐）
4. 在"映像"中找到下载的镜像，点击"启动"
5. 配置端口映射：8000 -> 8000
6. 添加环境变量：
   - NOTION_TOKEN
   - NOTION_DATABASE_ID
   - 可选：DOUBAN_BID, DOUBAN_LL, DOUBAN_DBCL2, DOUBAN_CK
7. 点击"应用"并启动容器

### 方法二：使用Docker Compose

1. 在群晖上安装Git和Docker Compose
   ```bash
   # 通过SSH连接到群晖
   sudo -i
   apk add git docker-compose
   ```

2. 克隆仓库并部署
   ```bash
   git clone https://github.com/your-username/douban-notion.git
   cd douban-notion
   
   # 创建环境变量文件
   nano .env
   # 添加必要的环境变量...
   
   # 启动服务
   docker-compose up -d
   ```

## 特别说明：Selenium官方镜像

本项目提供了基于Selenium官方镜像（selenium/standalone-chrome）的版本，解决了ChromeDriver兼容性问题。与普通镜像相比：

1. **优势**：
   - Chrome和ChromeDriver版本匹配，避免兼容性问题
   - 内置VNC服务器，可以远程查看浏览器运行状态
   - 由Selenium官方维护，稳定性更高

2. **使用VNC查看浏览器运行状态**：
   如果需要调试，可以通过以下步骤查看浏览器运行状态：
   ```bash
   docker run -d -p 8000:8000 -p 5900:5900 -e VNC_NO_PASSWORD=1 ghcr.io/your-username/douban-notion:selenium
   ```
   然后使用VNC客户端连接到 `your-server-ip:5900`

## GitHub自动构建

本项目已配置GitHub Actions自动构建流程：

1. 推送代码到GitHub仓库的main分支
2. GitHub Actions自动构建Docker镜像
3. 镜像发布到GitHub Container Registry
4. 版本标签会自动应用（基于git标签）

您可以直接通过标签引用指定版本的镜像：
```
ghcr.io/your-username/douban-notion:v1.0.0
``` 