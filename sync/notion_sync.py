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
            
        # 导演 (富文本类型)：导演信息，带链接
        if "directors" in movie_data and movie_data["directors"]:
            rich_text_array = []
            for i, director in enumerate(movie_data["directors"]):
                # 添加导演名称，带链接
                if isinstance(director, dict) and "url" in director and "name" in director:
                    rich_text_array.append({
                        "type": "text",
                        "text": {
                            "content": director["name"],
                            "link": {"url": director["url"]}
                        }
                    })
                else:
                    # 兼容旧数据格式
                    rich_text_array.append({
                        "type": "text",
                        "text": {"content": director if isinstance(director, str) else director.get("name", "")}
                    })
                
                # 添加分隔符，除了最后一个
                if i < len(movie_data["directors"]) - 1:
                    rich_text_array.append({
                        "type": "text",
                        "text": {"content": " / "}
                    })
            
            properties["导演"] = {"rich_text": rich_text_array}
        
        # 编剧 (富文本类型)：编剧信息，带链接
        if "screenwriters" in movie_data and movie_data["screenwriters"]:
            rich_text_array = []
            for i, screenwriter in enumerate(movie_data["screenwriters"]):
                # 添加编剧名称，带链接
                if isinstance(screenwriter, dict) and "url" in screenwriter and "name" in screenwriter:
                    rich_text_array.append({
                        "type": "text",
                        "text": {
                            "content": screenwriter["name"],
                            "link": {"url": screenwriter["url"]}
                        }
                    })
                else:
                    # 兼容旧数据格式
                    rich_text_array.append({
                        "type": "text",
                        "text": {"content": screenwriter if isinstance(screenwriter, str) else screenwriter.get("name", "")}
                    })
                
                # 添加分隔符，除了最后一个
                if i < len(movie_data["screenwriters"]) - 1:
                    rich_text_array.append({
                        "type": "text",
                        "text": {"content": " / "}
                    })
            
            properties["编剧"] = {"rich_text": rich_text_array}
        
        # 主演 (富文本类型)：演员信息，带链接
        if "actors" in movie_data and movie_data["actors"]:
            rich_text_array = []
            for i, actor in enumerate(movie_data["actors"]):
                # 添加演员名称，带链接
                if isinstance(actor, dict) and "url" in actor and "name" in actor:
                    rich_text_array.append({
                        "type": "text",
                        "text": {
                            "content": actor["name"],
                            "link": {"url": actor["url"]}
                        }
                    })
                else:
                    # 兼容旧数据格式
                    rich_text_array.append({
                        "type": "text",
                        "text": {"content": actor if isinstance(actor, str) else actor.get("name", "")}
                    })
                
                # 添加分隔符，除了最后一个
                if i < len(movie_data["actors"]) - 1:
                    rich_text_array.append({
                        "type": "text",
                        "text": {"content": " / "}
                    })
            
            properties["主演"] = {"rich_text": rich_text_array}
        
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
        
        # 首播 (富文本类型)：上映日期，完整保留包括地区信息
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
    
    def _get_rating_icon(self, rating: float) -> Dict:
        """
        根据评分获取对应的图标配置
        
        Args:
            rating: 电影评分
            
        Returns:
            图标配置字典
        """
        if rating is None:
            return None
            
        # 对评分进行四舍五入，9分以上都算9
        rounded_rating = min(9, round(rating))
        
        # 映射评分到数字按键表情符号
        keycap_emojis = {
            0: "0️⃣",
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣",
            9: "9️⃣"
        }
        
        # 获取对应的按键表情
        emoji = keycap_emojis.get(rounded_rating, "0️⃣")
        
        return {
            "type": "emoji",
            "emoji": emoji
        }

    def _is_valid_image_url(self, url: str) -> bool:
        """
        检查URL是否是有效的图片URL
        
        Args:
            url: 图片URL
            
        Returns:
            是否有效
        """
        if not url:
            return False
            
        # 检查URL是否以http/https开头
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
            
        # 检查URL是否以常见图片扩展名结尾
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']
        if not any(url.lower().endswith(ext) for ext in image_extensions):
            # 如果不是明确的图片扩展名，检查URL中是否包含这些扩展名
            if not any(f'.{ext}' in url.lower() for ext in ['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp']):
                return False
                
        return True

    def _process_cover_url(self, url: str) -> str:
        """
        处理封面URL，确保其能被Notion正确显示
        
        Args:
            url: 原始封面URL
            
        Returns:
            处理后的URL
        """
        if not url:
            return None
            
        # 移除URL中的查询参数
        if '?' in url:
            url = url.split('?')[0]
            
        # 确保URL是https，Notion可能不支持http
        if url.startswith('http://'):
            url = 'https://' + url[7:]
            
        # 检查是否是有效的图片URL
        if not self._is_valid_image_url(url):
            logger.warning(f"无效的图片URL格式: {url}")
            return None
            
        return url

    def add_to_database(self, properties: Dict, cover_url: str = None, rating: float = None) -> Dict:
        """
        向Notion数据库添加新记录
        
        Args:
            properties: Notion格式的属性字典
            cover_url: 封面图片URL
            rating: 电影评分
            
        Returns:
            API响应
        """
        url = f"{self.api_base_url}/pages"
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }
        
        # 设置封面图片
        processed_cover_url = self._process_cover_url(cover_url)
        if processed_cover_url:
            logger.info(f"设置页面封面，原始URL: {cover_url}")
            logger.info(f"处理后的URL: {processed_cover_url}")
            payload["cover"] = {
                "type": "external",
                "external": {
                    "url": processed_cover_url
                }
            }
        else:
            logger.warning(f"未能设置封面，无效的URL: {cover_url}")
        
        # 设置图标(根据评分)
        icon = self._get_rating_icon(rating)
        if icon:
            payload["icon"] = icon
        
        # 记录请求内容用于调试
        logger.debug(f"API请求payload: {json.dumps(payload, ensure_ascii=False)[:500]}...")
        
        try:
            response = self._make_api_request("POST", url, payload)
            logger.info(f"已成功向数据库添加新记录: {response.get('id')}")
            return response
        except Exception as e:
            logger.error(f"添加数据库记录失败: {e}")
            
            # 如果失败了，尝试不带封面再次添加
            if processed_cover_url and "cover" in payload:
                logger.warning("尝试不带封面重新添加记录")
                del payload["cover"]
                return self._make_api_request("POST", url, payload)
            else:
                # 重新抛出异常
                raise

    def update_database_item(self, item_id: str, properties: Dict, cover_url: str = None, rating: float = None) -> Dict:
        """
        更新Notion数据库中的记录
        
        Args:
            item_id: 数据库记录ID
            properties: Notion格式的属性字典
            cover_url: 封面图片URL
            rating: 电影评分
            
        Returns:
            API响应
        """
        url = f"{self.api_base_url}/pages/{item_id}"
        payload = {"properties": properties}
        
        # 设置封面图片
        processed_cover_url = self._process_cover_url(cover_url)
        if processed_cover_url:
            logger.info(f"设置页面封面，处理后的URL: {processed_cover_url}")
            payload["cover"] = {
                "type": "external",
                "external": {
                    "url": processed_cover_url
                }
            }
        
        # 设置图标(根据评分)
        icon = self._get_rating_icon(rating)
        if icon:
            payload["icon"] = icon
        
        try:
            response = self._make_api_request("PATCH", url, payload)
            logger.info(f"已成功更新数据库记录: {item_id}")
            return response
        except Exception as e:
            logger.error(f"更新数据库记录失败: {e}")
            
            # 如果失败了，尝试不带封面再次更新
            if processed_cover_url and "cover" in payload:
                logger.warning("尝试不带封面重新更新记录")
                del payload["cover"]
                return self._make_api_request("PATCH", url, payload)
            else:
                # 重新抛出异常
                raise
    
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
        
        # 获取封面URL和评分
        cover_url = movie_data.get('cover_url')
        rating = movie_data.get('rating')
        
        # 直接添加到数据库，不再判断是否存在
        response = self.add_to_database(properties, cover_url, rating)
        result = {
            "status": "added", 
            "item_id": response.get("id"), 
            "title": movie_data.get("title"),
            "has_cover": bool(cover_url),
            "rating": rating
        }
        
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