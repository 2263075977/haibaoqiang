"""
API服务器模块，提供HTTP接口供iPhone捷径等外部服务调用
"""
import os
import json
import asyncio
from typing import Dict, Any
from threading import Thread
from queue import Queue

from flask import Flask, request, jsonify

from config.logging_config import setup_logger
from config.settings import DOUBAN_COOKIES
from core.browser import PlaywrightBrowser
from scrapers.douban_scraper import DoubanScraper
from sync.notion_sync import NotionSyncModule, test_database_connection

# 创建日志记录器
logger = setup_logger("api_server")

# 创建Flask应用
app = Flask(__name__)

# 用于存储任务结果的队列
results_queue = Queue()

def run_task(title: str) -> Dict[str, Any]:
    """
    运行异步任务，爬取并同步电影数据
    
    Args:
        title: 电影名称
        
    Returns:
        处理结果
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(scrape_and_sync_movie_async(title))
    finally:
        loop.close()

async def scrape_and_sync_movie_async(title: str) -> Dict[str, Any]:
    """
    爬取并同步单部电影数据的异步任务
    
    Args:
        title: 电影名称
        
    Returns:
        处理结果
    """
    result = {
        "success": False,
        "title": title,
        "message": "",
        "data": {}
    }
    
    logger.info(f"API请求: 开始处理电影 '{title}'")
    
    # 检查Notion配置
    database_id = os.environ.get("NOTION_DATABASE_ID")
    token = os.environ.get("NOTION_TOKEN")
    
    if not database_id or not token:
        error_msg = "未设置Notion配置，请设置NOTION_DATABASE_ID和NOTION_TOKEN环境变量"
        logger.error(error_msg)
        result["message"] = error_msg
        return result
    
    # 测试数据库连接
    logger.info("测试Notion数据库连接...")
    success, message = test_database_connection(database_id, token)
    logger.info(message)
    
    if not success:
        error_msg = "数据库连接测试失败，请检查配置"
        logger.error(error_msg)
        result["message"] = error_msg
        return result
    
    try:
        # 初始化同步模块
        notion_sync = NotionSyncModule()
        
        # 创建浏览器实例并爬取数据
        async with PlaywrightBrowser(headless=True, cookies=DOUBAN_COOKIES) as browser:
            # 创建爬虫实例
            scraper = DoubanScraper(browser)
            
            # 获取电影数据
            movie_data = await scraper.get_movie_by_title(title)
            
            if not movie_data:
                error_msg = f"未找到电影: {title}"
                logger.warning(error_msg)
                result["message"] = error_msg
                return result
            
            logger.info(f"成功获取电影数据: {movie_data.get('title')} ({movie_data.get('category')}, 评分: {movie_data.get('rating')})")
            
            # 同步到Notion
            sync_result = notion_sync.sync_movie(movie_data)
            logger.info(f"同步结果: {sync_result}")
            
            # 设置成功结果
            result["success"] = True
            result["message"] = "处理成功"
            result["data"] = {
                "title": movie_data.get("title"),
                "category": movie_data.get("category"),
                "rating": movie_data.get("rating"),
                "notion_page_id": sync_result.get("item_id")
            }
            
    except Exception as e:
        error_msg = f"处理电影 '{title}' 出错: {str(e)}"
        logger.error(error_msg)
        result["message"] = error_msg
        
    return result

@app.route('/api/movie', methods=['POST'])
def process_movie():
    """处理电影请求的API端点"""
    data = request.get_json()
    
    if not data or 'title' not in data:
        return jsonify({
            "success": False,
            "message": "请提供电影标题",
            "data": {}
        }), 400
    
    title = data['title']
    if not title.strip():
        return jsonify({
            "success": False,
            "message": "电影标题不能为空",
            "data": {}
        }), 400
    
    logger.info(f"收到API请求，电影标题: {title}")
    
    # 在新线程中运行异步任务
    result = run_task(title)
    
    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查API端点"""
    return jsonify({
        "status": "healthy",
        "message": "API服务正常运行"
    })

def run_server(host='0.0.0.0', port=6000, debug=False):
    """启动API服务器"""
    logger.info(f"启动API服务器，监听地址: {host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    run_server() 