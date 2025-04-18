"""
通用工具函数模块
"""
import re
import time
import random
from typing import List, Dict, Any, Optional

def clean_text(text: str) -> str:
    """
    清理文本，移除多余的空白字符
    
    Args:
        text: 原始文本
        
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    # 替换所有空白字符为单个空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def retry_decorator(max_retries: int = 3, delay: int = 2):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 基础延迟时间(秒)
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    wait_time = delay * (2 ** attempt)
                    # 添加随机波动，避免同步请求
                    wait_time = wait_time * (0.8 + random.random() * 0.4)
                    time.sleep(wait_time)
        return wrapper
    return decorator

def clean_title(title: str) -> str:
    """
    清理标题，只保留主标题
    例如："肖申克的救赎 The Shawshank Redemption (1994)" -> "肖申克的救赎"
    
    Args:
        title: 原始标题
        
    Returns:
        清理后的标题
    """
    if not title:
        return ""
    # 移除英文标题和年份
    title = re.sub(r'\s+[\w\s\.\,\:]+(\s+\(\d{4}\))?$', '', title)
    # 移除括号及其内容
    title = re.sub(r'\s*\(.*?\)', '', title)
    return title.strip()

def extract_year(text: str) -> Optional[str]:
    """
    从文本中提取年份
    
    Args:
        text: 原始文本
        
    Returns:
        提取的年份或None
    """
    match = re.search(r'\((\d{4})\)', text)
    if match:
        return match.group(1)
    return None 