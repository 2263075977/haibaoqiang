#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import time

from douban_crawler import DoubanCrawler
from notion_api import NotionAPI

# 初始化FastAPI应用
app = FastAPI(
    title="豆瓣电影到Notion API",
    description="搜索豆瓣电影并添加到Notion数据库的API服务",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 创建全局实例
crawler = None
notion_api = None

# 请求模型
class SearchRequest(BaseModel):
    keyword: str
    
class MovieDetailRequest(BaseModel):
    url: str
    
class AddToNotionRequest(BaseModel):
    movie_data: Dict[str, Any]

# 响应模型
class SearchResult(BaseModel):
    title: str
    url: str
    year: Optional[str] = None
    rating: Optional[str] = None
    
class SearchResponse(BaseModel):
    results: List[SearchResult]
    
class MovieDetailResponse(BaseModel):
    movie_data: Dict[str, Any]
    
class AddToNotionResponse(BaseModel):
    success: bool
    message: str

# 初始化爬虫和Notion API
def initialize_services():
    global crawler, notion_api
    if crawler is None:
        crawler = DoubanCrawler()
    if notion_api is None:
        notion_api = NotionAPI()

# 启动时执行
@app.on_event("startup")
async def startup_event():
    # 在后台初始化
    background_tasks = BackgroundTasks()
    background_tasks.add_task(initialize_services)

@app.on_event("shutdown")
async def shutdown_event():
    global crawler
    if crawler:
        del crawler

# API路由
@app.get("/", tags=["健康检查"])
async def root():
    return {"status": "ok", "message": "豆瓣电影到Notion API服务运行中"}

@app.post("/search", response_model=SearchResponse, tags=["电影搜索"])
async def search_movie(request: SearchRequest):
    global crawler
    if crawler is None:
        initialize_services()
        
    # 搜索电影
    try:
        results = crawler.search_movie(request.keyword)
        # 转换为响应格式
        response_results = []
        for result in results:
            response_results.append(SearchResult(
                title=result['title'],
                url=result['url'],
                year=result.get('year', ''),
                rating=result.get('rating', '')
            ))
        return SearchResponse(results=response_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索电影失败: {str(e)}")

@app.post("/movie/details", response_model=MovieDetailResponse, tags=["电影详情"])
async def get_movie_details(request: MovieDetailRequest):
    global crawler
    if crawler is None:
        initialize_services()
        
    # 获取电影详情
    try:
        movie_data = crawler.get_movie_details(request.url)
        if not movie_data:
            raise HTTPException(status_code=404, detail="未找到电影详情")
        return MovieDetailResponse(movie_data=movie_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取电影详情失败: {str(e)}")

@app.post("/add_to_notion", response_model=AddToNotionResponse, tags=["添加到Notion"])
async def add_to_notion(request: AddToNotionRequest):
    global notion_api
    if notion_api is None:
        initialize_services()
        
    # 添加到Notion
    try:
        success = notion_api.add_movie_to_notion(request.movie_data)
        if success:
            return AddToNotionResponse(
                success=True, 
                message=f"成功将《{request.movie_data.get('title', '未知影片')}》添加到Notion数据库"
            )
        else:
            return AddToNotionResponse(
                success=False, 
                message="添加到Notion数据库失败"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加到Notion失败: {str(e)}")

@app.post("/search_and_add", tags=["一站式服务"])
async def search_and_add(request: SearchRequest):
    global crawler, notion_api
    if crawler is None or notion_api is None:
        initialize_services()
        
    try:
        # 1. 搜索电影
        search_results = crawler.search_movie(request.keyword)
        if not search_results:
            raise HTTPException(status_code=404, detail="未找到相关电影")
            
        # 2. 获取第一个结果的详情
        selected_movie = search_results[0]
        movie_details = crawler.get_movie_details(selected_movie['url'])
        
        if not movie_details:
            raise HTTPException(status_code=404, detail="获取电影详情失败")
            
        # 3. 添加到Notion
        success = notion_api.add_movie_to_notion(movie_details)
        
        if success:
            return {
                "success": True,
                "message": f"成功将《{movie_details.get('title', '未知影片')}》添加到Notion数据库",
                "movie_data": movie_details
            }
        else:
            raise HTTPException(status_code=500, detail="添加到Notion数据库失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")

# 主入口
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 