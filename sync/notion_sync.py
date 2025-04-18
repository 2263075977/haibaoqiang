"""
Notion同步模块，将影视数据同步到Notion数据库
"""
import os
import json
import time
import requests
from typing import Dict, List, Union, Optional, Any

from config.logging_config import setup_logger
from config.settings import NOTION_API_VERSION, NOTION_API_BASE_URL
from sync.sync_base import BaseSyncModule, SyncException

# 创建日志记录器
logger = setup_logger("notion_sync")

class NotionSyncModule(BaseSyncModule):
    """Notion同步写入模块，用于将影视数据写入Notion数据库"""
    
    def __init__(self, database_id: str = None, token: str = None, retry_times: int = 3, retry_delay: int = 2):
        """
        初始化Notion同步模块
        
        Args:
            database_id: Notion数据库ID
            token: Notion API Token
            retry_times: 最大重试次数
            retry_delay: 初始重试延迟(秒)
        """
        super().__init__(retry_times, retry_delay)
        
        # 从环境变量或参数获取配置
        self.database_id = database_id or os.environ.get("NOTION_DATABASE_ID")
        self.token = token or os.environ.get("NOTION_TOKEN")
        
        # 检查必要配置
        if not self.database_id:
            raise SyncException("未提供Notion数据库ID")
        if not self.token:
            raise SyncException("未提供Notion API Token")
            
        # API配置
        self.api_base_url = NOTION_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_API_VERSION,
            "Content-Type": "application/json"
        }
        
        logger.info(f"Notion同步模块初始化完成，数据库ID: {self.database_id}")
    
    def convert_data_format(self, movie_data: Dict) -> Dict:
        """
        将影视数据转换为Notion属性格式
        
        Args:
            movie_data: 影视数据字典
            
        Returns:
            Notion格式的属性字典
        """
        return self.convert_to_notion_properties(movie_data)
    
    def convert_to_notion_properties(self, movie_data: Dict) -> Dict:
        """
        将影视数据转换为Notion属性格式
        
        Args:
            movie_data: 影视数据字典
            
        Returns:
            Notion格式的属性字典
        """
        properties = {}
        
        # 名称 (标题类型)：影片标题
        if "title" in movie_data:
            properties["名称"] = {
                "title": [{"text": {"content": movie_data["title"]}}]
            }
        
        # 类别 (选择类型)：电影/电视剧
        if "category" in movie_data:
            properties["类别"] = {
                "select": {"name": movie_data["category"]}
            }
            
        # 导演 (富文本类型)：导演信息
        if "directors" in movie_data and movie_data["directors"]:
            directors_text = ", ".join(movie_data["directors"])
            properties["导演"] = {
                "rich_text": [{"text": {"content": directors_text}}]
            }
        
        # 编剧 (富文本类型)：编剧信息
        if "screenwriters" in movie_data and movie_data["screenwriters"]:
            screenwriters_text = ", ".join(movie_data["screenwriters"])
            properties["编剧"] = {
                "rich_text": [{"text": {"content": screenwriters_text}}]
            }
        
        # 主演 (富文本类型)：演员信息
        if "actors" in movie_data and movie_data["actors"]:
            actors_text = ", ".join(movie_data["actors"])
            properties["主演"] = {
                "rich_text": [{"text": {"content": actors_text}}]
            }
        
        # 类型 (多选类型)：影片类型标签
        if "genres" in movie_data and movie_data["genres"]:
            properties["类型"] = {
                "multi_select": [{"name": genre} for genre in movie_data["genres"]]
            }
        
        # 语言 (多选类型)：影片语言
        if "languages" in movie_data and movie_data["languages"]:
            properties["语言"] = {
                "multi_select": [{"name": lang} for lang in movie_data["languages"]]
            }
        
        # 评分 (数字类型)：豆瓣评分
        if "rating" in movie_data:
            properties["评分"] = {
                "number": movie_data["rating"]
            }
        
        # IMDb (富文本类型)：IMDb编号
        if "imdb_id" in movie_data:
            properties["IMDb"] = {
                "rich_text": [{"text": {"content": movie_data["imdb_id"]}}]
            }
        
        # 首播 (富文本类型)：上映日期
        if "release_date" in movie_data:
            properties["首播"] = {
                "rich_text": [{"text": {"content": movie_data["release_date"]}}]
            }
        
        # 简介 (富文本类型)：影片剧情简介
        if "summary" in movie_data:
            # 限制长度，Notion Rich Text有长度限制
            summary = movie_data["summary"]
            if len(summary) > 2000:
                summary = summary[:1997] + "..."
                
            properties["简介"] = {
                "rich_text": [{"text": {"content": summary}}]
            }
        
        # 又名 (富文本类型)：影片别名
        if "aka" in movie_data:
            properties["又名"] = {
                "rich_text": [{"text": {"content": movie_data["aka"]}}]
            }
        
        return properties
    
    def add_to_database(self, properties: Dict) -> Dict:
        """
        向Notion数据库添加新记录
        
        Args:
            properties: Notion格式的属性字典
            
        Returns:
            API响应
        """
        url = f"{self.api_base_url}/pages"
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }
        
        # 记录请求内容用于调试
        logger.debug(f"API请求payload: {json.dumps(payload, ensure_ascii=False)[:500]}...")
        
        response = self._make_api_request("POST", url, payload)
        logger.info(f"已成功向数据库添加新记录: {response.get('id')}")
        return response
    
    def update_database_item(self, item_id: str, properties: Dict) -> Dict:
        """
        更新Notion数据库中的记录
        
        Args:
            item_id: 数据库记录ID
            properties: Notion格式的属性字典
            
        Returns:
            API响应
        """
        url = f"{self.api_base_url}/pages/{item_id}"
        payload = {"properties": properties}
        
        response = self._make_api_request("PATCH", url, payload)
        logger.info(f"已成功更新数据库记录: {item_id}")
        return response
    
    def sync_data(self, movie_data: Dict) -> Dict:
        """
        同步影视数据到Notion数据库
        
        Args:
            movie_data: 影视数据字典
            
        Returns:
            同步结果
        """
        return self.sync_movie(movie_data)
    
    def sync_movie(self, movie_data: Dict) -> Dict:
        """
        同步影视数据到Notion数据库
        
        Args:
            movie_data: 影视数据字典
            
        Returns:
            同步结果
        """
        # 验证数据
        self._validate_movie_data(movie_data)
        
        # 转换为Notion属性格式
        properties = self.convert_to_notion_properties(movie_data)
        
        # 直接添加到数据库，不再判断是否存在
        response = self.add_to_database(properties)
        result = {"status": "added", "item_id": response.get("id"), "title": movie_data.get("title")}
        
        return result
    
    def _validate_movie_data(self, movie_data: Dict) -> None:
        """
        验证影视数据的完整性
        
        Args:
            movie_data: 影视数据字典
        """
        if not movie_data:
            raise SyncException("影视数据不能为空")
        
        # 检查必填字段
        if "title" not in movie_data or not movie_data["title"]:
            raise SyncException("影视标题不能为空")
        
        if "category" not in movie_data or not movie_data["category"]:
            raise SyncException("影视类别不能为空")
    
    def _make_api_request(self, method: str, url: str, payload: Dict = None) -> Dict:
        """
        发送API请求，包含重试逻辑
        
        Args:
            method: HTTP方法
            url: 请求URL
            payload: 请求数据
            
        Returns:
            API响应
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                if method.upper() == "GET":
                    response = requests.get(url, headers=self.headers)
                elif method.upper() == "POST":
                    response = requests.post(url, headers=self.headers, json=payload)
                elif method.upper() == "PATCH":
                    response = requests.patch(url, headers=self.headers, json=payload)
                else:
                    raise SyncException(f"不支持的HTTP方法: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                retries += 1
                
                # 获取更详细的错误信息
                error_detail = ""
                response_text = ""
                
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    
                    # 尝试获取响应内容
                    try:
                        response_text = e.response.text
                        error_json = e.response.json()
                        error_detail = f"错误详情: {json.dumps(error_json, ensure_ascii=False)}"
                    except:
                        error_detail = f"无法解析错误响应: {response_text[:200]}"
                    
                    # 详细记录错误
                    logger.error(f"API请求失败: {e}, 状态码: {status_code}, {error_detail}")
                    
                    # 处理不同错误类型
                    if status_code == 401:
                        raise SyncException(f"Notion API认证失败，请检查Token: {error_detail}")
                    elif status_code == 403:
                        raise SyncException(f"没有权限访问该资源，请检查数据库权限设置: {error_detail}")
                    elif status_code == 404:
                        raise SyncException(f"资源未找到: {url}, {error_detail}")
                    elif status_code == 400:
                        raise SyncException(f"请求格式错误: {error_detail}")
                    elif status_code == 429:
                        # 速率限制错误，等待更长时间
                        retry_after = int(e.response.headers.get('Retry-After', self.retry_delay * 2))
                        logger.warning(f"API速率限制，等待 {retry_after} 秒后重试")
                        time.sleep(retry_after)
                        continue
                
                # 一般错误的指数退避重试
                if retries <= self.max_retries:
                    wait_time = self.retry_delay * (2 ** (retries - 1))
                    logger.warning(f"API请求失败: {str(e)}，{wait_time} 秒后重试 ({retries}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API请求失败，已达到最大重试次数: {str(e)}")
                    if response_text:
                        logger.error(f"错误响应内容: {response_text}")
                    raise SyncException(f"API请求失败: {str(e)}")
        
        raise SyncException("API请求失败，超出重试次数")

def test_database_connection(database_id, token):
    """测试Notion数据库连接是否正常"""
    url = f"{NOTION_API_BASE_URL}/databases/{database_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_API_VERSION
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        database_info = response.json()
        return True, f"数据库连接成功，标题: {database_info.get('title', [{}])[0].get('text', {}).get('content', '未知')}"
    except Exception as e:
        error_detail = ""
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
            except:
                error_detail = e.response.text
        return False, f"数据库连接失败: {str(e)}, 详情: {error_detail}" 