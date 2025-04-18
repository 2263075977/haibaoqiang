"""
豆瓣影视数据爬取与Notion同步主程序
"""
import os
import sys
import asyncio

from config.logging_config import setup_logger
from config.settings import DOUBAN_COOKIES
from core.browser import PlaywrightBrowser
from scrapers.douban_scraper import DoubanScraper
from sync.notion_sync import NotionSyncModule, test_database_connection

# 创建日志记录器
logger = setup_logger("main")

# 确保Windows环境下使用UTF-8编码进行输入输出
if sys.platform == 'win32':
    # 检查编码
    logger.info(f"当前控制台编码: {sys.stdout.encoding}")
    
    # 设置控制台输入为UTF-8模式
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')

async def scrape_and_sync_movie(title: str):
    """
    爬取并同步单部电影数据
    
    Args:
        title: 电影名称
    """
    logger.info(f"开始处理电影: {title}")
    
    # 检查Notion配置
    database_id = os.environ.get("NOTION_DATABASE_ID")
    token = os.environ.get("NOTION_TOKEN")
    
    if not database_id or not token:
        logger.error("未设置Notion配置，请设置NOTION_DATABASE_ID和NOTION_TOKEN环境变量")
        return
    
    # 测试数据库连接
    logger.info("测试Notion数据库连接...")
    success, message = test_database_connection(database_id, token)
    logger.info(message)
    
    if not success:
        logger.error("数据库连接测试失败，请检查配置后重试")
        return
    
    # 初始化同步模块
    notion_sync = NotionSyncModule()
    
    # 创建浏览器实例并爬取数据
    async with PlaywrightBrowser(headless=True, cookies=DOUBAN_COOKIES) as browser:
        # 创建爬虫实例
        scraper = DoubanScraper(browser)
        
        # 获取电影数据
        movie_data = await scraper.get_movie_by_title(title)
        
        if not movie_data:
            logger.warning(f"未找到电影: {title}")
            return
        
        logger.info(f"成功获取电影数据: {movie_data.get('title')} ({movie_data.get('category')}, 评分: {movie_data.get('rating')})")
        
        try:
            # 同步到Notion
            result = notion_sync.sync_movie(movie_data)
            logger.info(f"同步结果: {result}")
        except Exception as e:
            logger.error(f"同步电影 {title} 失败: {e}")

def main():
    """程序主入口"""
    print("\n===== 豆瓣影视数据爬取与Notion同步工具 =====\n")
    
    # 使用交互式输入获取电影名称
    while True:
        title = input("请输入电影名称 (输入q退出): ")
        
        if title.lower() == 'q':
            print("程序已退出")
            break
            
        if not title.strip():
            print("电影名称不能为空，请重新输入")
            continue
            
        # 运行爬取和同步任务
        print(f"\n开始处理: {title}\n")
        asyncio.run(scrape_and_sync_movie(title))
        print("\n处理完成，可以继续输入下一部电影名称\n")

if __name__ == "__main__":
    main() 