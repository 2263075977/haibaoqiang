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

本项目支持通过Docker部署，并可以配合GitHub Actions自动构建镜像。

### 使用预构建镜像

在群晖Docker上部署：

1. 在群晖Docker中添加映像，使用GitHub Container Registry地址：
   ```
   ghcr.io/[您的GitHub用户名]/douban-notion:main
   ```

2. 创建容器时设置环境变量：
   - `NOTION_TOKEN`: Notion API密钥
   - `NOTION_DATABASE_ID`: Notion数据库ID
   - 可选的豆瓣Cookie: `DOUBAN_BID`, `DOUBAN_LL`, `DOUBAN_DBCL2`, `DOUBAN_CK`

3. 设置端口映射：
   - 容器端口: 8000
   - 本地端口: 您希望使用的端口(如8000)

### 使用docker-compose

1. 复制项目中的`docker-compose.yml`和`.env.example`文件到您的群晖
2. 将`.env.example`重命名为`.env`并填入您的配置信息
3. 执行以下命令启动服务：
   ```bash
   docker-compose up -d
   ```

## 自建镜像部署流程

### 1. 将项目推送到GitHub

1. 在GitHub创建新仓库
2. 初始化本地仓库并推送：
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/您的用户名/douban-notion.git
   git push -u origin main
   ```

### 2. 启用GitHub Actions

1. 在GitHub仓库设置中，确保启用了GitHub Actions
2. 在仓库设置 -> Secrets中添加必要的密钥（如果需要）
3. 推送代码时会自动触发构建流程，构建完成后Docker镜像会被推送到GitHub Container Registry

### 3. 在群晖上部署

1. 在群晖Docker中登录GitHub Container Registry（如需要）
2. 拉取自动构建的镜像
3. 使用上述"使用预构建镜像"或"使用docker-compose"的方法部署

## API调用示例

使用Docker部署后，可以通过以下方式调用API：

```bash
# 搜索电影
curl -X POST http://您的群晖IP:8000/search -H "Content-Type: application/json" -d '{"keyword":"电影名称"}'

# 一站式服务（搜索并添加）
curl -X POST http://您的群晖IP:8000/search_and_add -H "Content-Type: application/json" -d '{"keyword":"电影名称"}'
```

您也可以通过浏览器访问API文档： http://您的群晖IP:8000/docs 

## 常见问题与排错

### Docker镜像构建或运行时的问题

1. **ChromeDriver版本不匹配错误**

   错误信息: `There is no such driver by url https://chromedriver.storage.googleapis.com/LATEST_RELEASE_XXX`
   
   解决方法:
   - Docker环境中已经预安装了匹配的ChromeDriver
   - 确保环境变量`CHROMEDRIVER_PATH`设置为`/usr/local/bin/chromedriver`

2. **Chrome安装失败**

   错误信息: `failed to solve: process "/bin/sh -c wget...`
   
   解决方法:
   - 我们更新了Dockerfile使用官方源安装Chrome并自动匹配ChromeDriver版本
   - 重新构建Docker镜像应该能解决问题

3. **无法启动Chrome浏览器**

   错误信息: `DevToolsActivePort file doesn't exist` 或 `unknown error: Chrome failed to start: crashed`
   
   解决方法:
   - 在Chrome选项中添加参数: `--no-sandbox`, `--disable-dev-shm-usage`
   - 这些参数已经在代码中添加，一般不需要修改

### API服务问题

1. **API返回404错误**

   错误信息: `"POST /search_and_add HTTP/1.1" 404 Not Found`
   
   解决方法:
   - 检查API服务是否正常启动，访问 http://群晖IP:8000/docs
   - 确保API URL路径正确

2. **无法连接到API服务**

   错误信息: `Connection refused`
   
   解决方法:
   - 检查容器是否正常运行: `docker ps`
   - 检查端口映射是否正确
   - 检查网络设置是否允许此端口访问

### Notion API问题

1. **Notion API验证失败**

   错误信息: `无法访问Notion数据库`
   
   解决方法:
   - 确认`.env`文件中的`NOTION_TOKEN`和`NOTION_DATABASE_ID`正确
   - 确认Notion集成已经与数据库共享
   - 检查Notion API权限设置

2. **添加到Notion失败**

   错误信息: `数据库属性名称不匹配`
   
   解决方法:
   - 确认Notion数据库中有必要的属性，如"名称", "类别", "导演"等
   - 确认属性类型正确，如"名称"应为标题类型，"评分"应为数字类型

### 其他问题的解决方法

如果遇到其他问题，可以尝试以下步骤:

1. 检查容器日志: `docker logs douban-notion`
2. 重启容器: `docker restart douban-notion`
3. 拉取最新镜像重试: `docker-compose pull && docker-compose up -d`
4. 如问题依然存在，请在GitHub项目中提交issue，附上错误日志 