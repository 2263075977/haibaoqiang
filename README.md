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

## Docker部署常见问题

### ChromeDriver错误

如果遇到如下错误：
```
搜索电影出错: 多次尝试初始化浏览器失败: There is no such driver by url https://chromedriver.storage.googleapis.com/LATEST_RELEASE...
```

可能的解决方案：

1. **重建Docker镜像**：
   ```bash
   docker-compose build --no-cache
   ```

2. **增加共享内存**：
   Chrome在Docker容器中运行时需要足够的共享内存。确保docker-compose.yml中包含：
   ```yaml
   shm_size: 1gb
   ```

3. **检查环境变量**：
   确保在容器中设置了以下环境变量：
   ```
   WDM_LOG_LEVEL=0
   WDM_CHROME_VERSION=114.0.5735.198
   ```

### 连接问题

如果API服务启动但无法访问：

1. **检查端口映射**：
   确保容器的8000端口已映射到主机端口

2. **检查防火墙**：
   确保主机防火墙允许8000端口的流量

3. **检查API服务日志**：
   ```bash
   docker logs douban-notion
   ```

### Notion API连接问题

如果无法连接到Notion API：

1. **检查Notion令牌**：
   确保`NOTION_TOKEN`环境变量设置正确

2. **检查数据库ID**：
   确保`NOTION_DATABASE_ID`环境变量设置正确
   
3. **检查Notion集成权限**：
   确保Notion集成有权访问您的数据库

### 性能优化建议

1. **持久化Chrome数据**：
   使用数据卷保存Chrome配置可以提高性能和稳定性

2. **增加资源限制**：
   如果爬虫经常崩溃，可以增加内存限制：
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2g
   ```

3. **使用代理**：
   如果经常被豆瓣限制，可以配置代理服务器 