#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError

# 加载环境变量
load_dotenv()

class NotionAPI:
    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        
        if not self.token or not self.database_id:
            raise ValueError("请在.env文件中设置NOTION_TOKEN和NOTION_DATABASE_ID")
        
        self.notion = Client(auth=self.token)
        
        # 验证API令牌和数据库访问权限
        try:
            print("正在验证Notion API访问权限...")
            # 尝试获取数据库信息
            self.database = self.notion.databases.retrieve(database_id=self.database_id)
            print("Notion API连接成功，数据库访问正常")
            
            # 验证数据库属性
            self._verify_database_properties()
            
        except APIResponseError as e:
            if "Could not find database" in str(e):
                print("\n错误: 无法访问Notion数据库！")
                print("请确保您已完成以下步骤:")
                print("1. 在Notion中创建了集成 (https://www.notion.so/my-integrations)")
                print("2. 复制了正确的集成密钥(API Token)")
                print("3. 将您的数据库与该集成共享 (在数据库页面右上角的...菜单中选择'添加连接')")
                print(f"4. 确认数据库ID正确: {self.database_id}")
                print("\n具体错误:", e)
            else:
                print(f"Notion API连接错误: {e}")
            raise
    
    def _verify_database_properties(self):
        """验证数据库是否包含所有必需的属性"""
        required_properties = {
            "名称": "title",
            "类别": "select",
            "导演": "rich_text",
            "主演": "rich_text",
            "评分": "number",
            "类型": "multi_select"
        }
        
        db_properties = self.database.get("properties", {})
        missing_properties = []
        wrong_type_properties = []
        
        for prop_name, prop_type in required_properties.items():
            if prop_name not in db_properties:
                missing_properties.append(prop_name)
            elif db_properties[prop_name]["type"] != prop_type:
                wrong_type_properties.append(f"{prop_name} (需要{prop_type}，实际{db_properties[prop_name]['type']})")
        
        if missing_properties or wrong_type_properties:
            print("\n警告: 数据库属性可能存在问题！")
            
            if missing_properties:
                print(f"缺少以下必需属性: {', '.join(missing_properties)}")
                
            if wrong_type_properties:
                print(f"以下属性类型不匹配: {', '.join(wrong_type_properties)}")
                
            print("\n您可能需要在Notion数据库中创建或调整这些属性")
            print("程序将继续运行，但可能会遇到问题")
    
    def create_rich_text_with_links(self, items_with_links):
        """创建带有超链接的富文本内容"""
        if not items_with_links:
            return []
            
        rich_text_array = []
        
        # 为每个人员添加超链接
        for i, item in enumerate(items_with_links):
            # 添加名称和超链接
            if isinstance(item, dict) and 'name' in item and 'url' in item:
                rich_text_array.append({
                    "type": "text",
                    "text": {
                        "content": item['name'],
                        "link": {"url": item['url']}
                    }
                })
            elif isinstance(item, str):
                # 处理纯字符串情况
                rich_text_array.append({
                    "type": "text",
                    "text": {"content": item}
                })
            
            # 如果不是最后一个，添加分隔符
            if i < len(items_with_links) - 1:
                rich_text_array.append({
                    "type": "text",
                    "text": {"content": " / "}
                })
        
        return rich_text_array
    
    def add_movie_to_notion(self, movie_data):
        """将电影信息添加到Notion数据库"""
        try:
            # 检查标题是否存在
            if not movie_data.get('title'):
                print("错误: 缺少电影标题")
                return False
            
            # 检查电影是否已存在
            if self._movie_exists_in_database(movie_data['title']):
                # 只提示已存在，但仍然继续添加
                print(f"\n提示: 数据库中已存在 《{movie_data['title']}》，将创建新记录")
            
            # 准备属性数据 - 根据实际Notion数据库属性调整
            properties = {
                # 标题字段改为"名称"
                "名称": {
                    "title": [
                        {
                            "text": {
                                "content": movie_data.get('title', '')
                            }
                        }
                    ]
                }
            }
            
            # 添加类别（电影/电视剧）
            content_type = movie_data.get('content_type', '电影')  # 默认为电影
            properties["类别"] = {
                "select": {
                    "name": content_type
                }
            }
            
            # 添加又名 - 使用rich_text
            if movie_data.get('aka') and movie_data['aka']:
                # 将所有又名连接为一个字符串，用 / 分隔
                aka_text = " / ".join(movie_data.get('aka', []))
                properties["又名"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": aka_text
                            }
                        }
                    ]
                }
            
            # 添加简介 - 新增，使用rich_text
            if movie_data.get('summary'):
                # 由于Notion API富文本单个块的长度限制，可能需要拆分长文本
                summary = movie_data.get('summary', '')
                
                # Notion API 富文本块最大长度约为2000字符，这里保守使用1900
                max_chunk_size = 1900
                
                if len(summary) <= max_chunk_size:
                    # 如果简介较短，直接添加
                    properties["简介"] = {
                        "rich_text": [
                            {
                                "text": {
                                    "content": summary
                                }
                            }
                        ]
                    }
                else:
                    # 如果简介较长，需要分块
                    rich_text_array = []
                    for i in range(0, len(summary), max_chunk_size):
                        chunk = summary[i:i + max_chunk_size]
                        rich_text_array.append({
                            "text": {
                                "content": chunk
                            }
                        })
                    
                    properties["简介"] = {
                        "rich_text": rich_text_array
                    }
            
            # 添加导演 - 使用rich_text和超链接
            if movie_data.get('directors'):
                properties["导演"] = {
                    "rich_text": self.create_rich_text_with_links(movie_data.get('directors', []))
                }
            
            # 添加编剧 - 使用rich_text和超链接
            if movie_data.get('screenwriters'):
                properties["编剧"] = {
                    "rich_text": self.create_rich_text_with_links(movie_data.get('screenwriters', []))
                }
            
            # 添加主演 - 使用rich_text和超链接
            if movie_data.get('actors'):
                properties["主演"] = {
                    "rich_text": self.create_rich_text_with_links(movie_data.get('actors', []))
                }
            
            # 添加类型
            if movie_data.get('genres'):
                properties["类型"] = {
                    "multi_select": [{"name": genre} for genre in movie_data.get('genres', [])[:10]]
                }
            
            # 添加语言
            if movie_data.get('languages'):
                properties["语言"] = {
                    "multi_select": [{"name": language} for language in movie_data.get('languages', [])[:10]]
                }
            
            # 添加上映日期 - 字段名改为"首播"
            if movie_data.get('release_dates') and movie_data['release_dates']:
                release_date = movie_data['release_dates'][0]
                properties["首播"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": release_date
                            }
                        }
                    ]
                }
            
            # 添加评分 - 使用number类型
            if movie_data.get('rating'):
                try:
                    # 尝试将评分转换为数字
                    rating_value = float(movie_data.get('rating', '0'))
                    properties["评分"] = {
                        "number": rating_value
                    }
                except ValueError:
                    # 如果转换失败，设置为0
                    properties["评分"] = {
                        "number": 0
                    }
            
            # 添加IMDb ID
            if movie_data.get('imdb_id'):
                properties["IMDb"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": movie_data.get('imdb_id', '')
                            }
                        }
                    ]
                }
            
            # 创建页面
            response = self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                # 如果有封面图片，添加封面
                cover={"external": {"url": movie_data.get('poster')}} if movie_data.get('poster') else None
            )
            
            print(f"成功添加{movie_data.get('content_type', '电影')} '{movie_data.get('title')}' 到Notion数据库")
            return True
        
        except APIResponseError as e:
            if "Could not find database" in str(e):
                print("\n错误: 无法访问Notion数据库！")
                print("请确保您已完成以下步骤:")
                print("1. 在Notion中创建了集成 (https://www.notion.so/my-integrations)")
                print("2. 复制了正确的集成密钥(API Token)")
                print("3. 将您的数据库与该集成共享 (在数据库页面右上角的...菜单中选择'添加连接')")
                print(f"4. 确认数据库ID正确: {self.database_id}")
            elif "is not a property that exists" in str(e):
                print("\n错误: Notion数据库属性名称不匹配！")
                print("请检查您的Notion数据库中的属性名称是否与代码中使用的一致")
                print("当前使用的属性: 名称, 类别, 又名, 简介, 导演, 编剧, 主演, 类型, 语言, 首播, 评分, IMDb")
                print("请确保这些属性在您的数据库中存在，或修改代码以匹配您的属性名称")
            else:
                print(f"添加电影到Notion出错: {e}")
            return False
        except Exception as e:
            print(f"添加电影到Notion时出现意外错误: {e}")
            return False 

    def _movie_exists_in_database(self, title):
        """检查电影是否已存在于数据库中"""
        try:
            # 查询标题匹配的记录
            response = self.notion.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "名称",
                    "title": {
                        "equals": title
                    }
                }
            )
            
            # 如果有结果，说明电影已存在
            return len(response.get('results', [])) > 0
        except:
            # 如果查询出错，假设电影不存在
            return False
            
    def generate_imdb_url(self, imdb_id):
        """根据IMDb ID生成IMDb链接"""
        if not imdb_id:
            return None
            
        # 确保ID格式正确 (以tt开头)
        if not imdb_id.startswith("tt"):
            return None
            
        return f"https://www.imdb.com/title/{imdb_id}/" 