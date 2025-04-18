"""
日志配置模块
"""
import logging
import os
from datetime import datetime

# 日志目录
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件命名格式：logs/app_年月日.log
current_date = datetime.now().strftime("%Y%m%d")
LOG_FILE = os.path.join(LOG_DIR, f"app_{current_date}.log")

# 日志级别
LOG_LEVEL = logging.INFO

# 日志格式 - 使用普通格式，兼容所有Python版本
LOG_FORMAT = '%(asctime)s - %(name)15s - %(levelname)8s - %(message)s'
# 时间格式 - 不包含毫秒
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def setup_logger(name, log_file=None, level=None):
    """
    设置并返回一个新的logger
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径，默认使用全局设置
        level: 日志级别，默认使用全局设置
        
    Returns:
        配置好的logger对象
    """
    log_file = log_file or LOG_FILE
    level = level or LOG_LEVEL
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 清除现有处理器，避免重复添加
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 创建格式器，使用不包含毫秒的时间格式
    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 