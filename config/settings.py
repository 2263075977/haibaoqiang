"""
全局配置项
"""
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# API配置
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")

# 浏览器配置
DEFAULT_TIMEOUT = 30000  # 默认超时时间（毫秒）
DEFAULT_HEADLESS = True  # 默认无头模式

# 豆瓣Cookie配置
DOUBAN_COOKIES = [
    {"name": "bid", "value": "k9F2SdgqHPk", "domain": ".douban.com", "path": "/"},
    {"name": "ll", "value": "\"118181\"", "domain": ".douban.com", "path": "/"},
    {"name": "_pk_id.100001.4cf6", "value": "d0a3e13364f9de30.1740444565.", "domain": ".douban.com", "path": "/"},
    {"name": "_vwo_uuid_v2", "value": "DF90204C8576B6CD106D9FE0CD5E5FC92|8f4560798eebf81287569112258a2fa8", "domain": ".douban.com", "path": "/"},
    {"name": "push_noty_num", "value": "0", "domain": ".douban.com", "path": "/"},
    {"name": "push_doumail_num", "value": "0", "domain": ".douban.com", "path": "/"},
    {"name": "__utmv", "value": "30149280.25486", "domain": ".douban.com", "path": "/"},
    {"name": "_ga", "value": "GA1.1.1420817860.1741833180", "domain": ".douban.com", "path": "/"},
    {"name": "__utmz", "value": "30149280.1743725890.12.6.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided)", "domain": ".douban.com", "path": "/"},
    {"name": "_pk_ref.100001.4cf6", "value": "%5B%22%22%2C%22%22%2C1743912935%2C%22https%3A%2F%2Fwww.google.com%2F%22%5D", "domain": ".douban.com", "path": "/"},
    {"name": "__utma", "value": "30149280.567141070.1740444565.1743725890.1743912935.13", "domain": ".douban.com", "path": "/"},
    {"name": "dbcl2", "value": "\"254862890:Nxexho7wPBk\"", "domain": ".douban.com", "path": "/"},
    {"name": "ck", "value": "FJeN", "domain": ".douban.com", "path": "/"},
    {"name": "frodotk_db", "value": "\"34540d04897890d29cfc270d9c69b276\"", "domain": ".douban.com", "path": "/"}
]

# 浏览器请求头
BROWSER_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "zh-CN,zh;q=0.9",
    "dnt": "1",
    "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1"
}

# 爬虫配置
DEFAULT_RETRY_TIMES = 3  # 默认重试次数

# Notion API设置
NOTION_API_VERSION = "2022-06-28"
NOTION_API_BASE_URL = "https://api.notion.com/v1"

# 用户代理列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
] 