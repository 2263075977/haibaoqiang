"""
同步功能基类，为所有同步功能提供通用方法
"""
import time
import json
from typing import Dict, Any, Optional, Tuple, List

from config.logging_config import setup_logger

# 创建日志记录器
logger = setup_logger('sync_base')

class SyncException(Exception):
    """同步模块自定义异常类"""
    pass

class BaseSyncModule:
    """同步功能基类"""
    
    def __init__(self, retry_times: int = 3, retry_delay: int = 2):
        """
        初始化同步模块
        
        Args:
            retry_times: 最大重试次数
            retry_delay: 初始重试延迟(秒)
        """
        self.max_retries = retry_times
        self.retry_delay = retry_delay
    
    def _validate_data(self, data: Dict[str, Any]) -> None:
        """
        验证数据的有效性，子类应重写此方法
        
        Args:
            data: 要验证的数据字典
            
        Raises:
            SyncException: 数据无效时抛出异常
        """
        if not data:
            raise SyncException("数据不能为空")
    
    def sync_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步数据，子类应重写此方法
        
        Args:
            data: 要同步的数据字典
            
        Returns:
            同步结果
        """
        raise NotImplementedError("子类必须实现sync_data方法")
    
    def convert_data_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换数据格式，子类应重写此方法
        
        Args:
            data: 原始数据字典
            
        Returns:
            转换后的数据字典
        """
        raise NotImplementedError("子类必须实现convert_data_format方法")

    def retry_operation(self, operation_func, *args, **kwargs):
        """
        通用的操作重试逻辑
        
        Args:
            operation_func: 要重试的函数
            *args, **kwargs: 传递给函数的参数
            
        Returns:
            函数的返回值
            
        Raises:
            Exception: 重试失败时抛出最后一次尝试的异常
        """
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return operation_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"操作失败: {str(e)}，{wait_time} 秒后重试 ({attempt + 1}/{self.max_retries})")
                time.sleep(wait_time)
        
        # 所有重试都失败
        if last_exception:
            logger.error(f"操作失败，已达到最大重试次数: {last_exception}")
            raise last_exception 