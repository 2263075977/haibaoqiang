"""
API服务器启动程序
"""
import os
import sys
import argparse
from api.server import run_server
from config.logging_config import setup_logger

# 创建日志记录器
logger = setup_logger("api_launcher")

def main():
    """主程序入口"""
    # 确认控制台使用UTF-8编码
    if sys.platform == 'win32':
        logger.info("Windows环境: 控制台编码 %s", sys.stdout.encoding)
    else:
        logger.info("非Windows环境: 控制台编码 %s", sys.stdout.encoding)
    
    parser = argparse.ArgumentParser(description="豆瓣影视数据API服务器")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="服务器监听地址")
    parser.add_argument("--port", type=int, default=6000, help="服务器端口")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    args = parser.parse_args()
    
    # 检查环境变量
    database_id = os.environ.get("NOTION_DATABASE_ID")
    token = os.environ.get("NOTION_TOKEN")
    
    if not database_id or not token:
        logger.warning("未设置Notion环境变量，API调用可能会失败")
        logger.warning("请确保设置了NOTION_DATABASE_ID和NOTION_TOKEN环境变量")
    
    # 打印启动信息
    logger.info(f"启动API服务器 - 地址: {args.host}:{args.port}")
    logger.info("API接口:")
    logger.info("  - 健康检查: GET /api/health")
    logger.info("  - 处理电影: POST /api/movie (需要JSON格式的title字段)")
    logger.info("iPhone捷径调用示例：")
    logger.info("  1. 使用'获取内容'操作，设置URL为服务器地址+/api/movie")
    logger.info("  2. 请求方法选择POST，请求体JSON格式: {\"title\": \"电影名称\"}")
    logger.info("  3. 使用'获取词典值'操作处理返回的JSON数据")
    
    # 启动服务器
    run_server(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main() 