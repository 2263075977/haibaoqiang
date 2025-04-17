#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
from douban_crawler import DoubanCrawler
from notion_api import NotionAPI

def print_header():
    print("\n" + "=" * 60)
    print("  豆瓣影视数据爬取并添加到Notion数据库工具  ".center(60, "="))
    print("=" * 60)
    print("  作用: 搜索豆瓣电影/剧集并将详细信息保存到Notion数据库  ")
    print("=" * 60)

def print_movie_details(movie_data):
    title = movie_data.get('title', 'N/A')
    content_type = movie_data.get('content_type', '电影')
    
    print("\n" + "-" * 60)
    print(f"  《{title}》详情信息  ".center(60, "-"))
    print("-" * 60)
    
    # 显示内容类型（电影/电视剧）
    print(f"分类: {content_type}")
    
    # 显示又名信息
    akas = movie_data.get('aka', [])
    if akas:
        print(f"又名: {' / '.join(akas)}")
    
    # 处理导演信息 - 支持新的包含链接的格式
    directors = movie_data.get('directors', [])
    director_names = []
    for d in directors:
        if isinstance(d, dict) and 'name' in d:
            director_names.append(d['name'])
        elif isinstance(d, str):
            director_names.append(d)
    print(f"导演: {', '.join(director_names) if director_names else 'N/A'}")
    
    # 处理编剧信息 - 支持新的包含链接的格式
    screenwriters = movie_data.get('screenwriters', [])
    screenwriter_names = []
    for s in screenwriters:
        if isinstance(s, dict) and 'name' in s:
            screenwriter_names.append(s['name'])
        elif isinstance(s, str):
            screenwriter_names.append(s)
    print(f"编剧: {', '.join(screenwriter_names) if screenwriter_names else 'N/A'}")
    
    # 处理主演信息 - 支持新的包含链接的格式
    actors = movie_data.get('actors', [])
    actor_names = []
    for a in actors:
        if isinstance(a, dict) and 'name' in a:
            actor_names.append(a['name'])
        elif isinstance(a, str):
            actor_names.append(a)
    print(f"主演: {', '.join(actor_names) if actor_names else 'N/A'}")
    
    print(f"类型: {', '.join(movie_data.get('genres', []))}")
    print(f"语言: {', '.join(movie_data.get('languages', []))}")
    
    # 上映日期只显示第一个
    release_dates = movie_data.get('release_dates', [])
    release_date = release_dates[0] if release_dates else 'N/A'
    print(f"上映日期: {release_date}")
    
    print(f"评分: {movie_data.get('rating', 'N/A')}")
    print(f"IMDb: {movie_data.get('imdb_id', 'N/A')}")
    
    # 显示简介信息
    if movie_data.get('summary'):
        print("\n" + "-" * 60)
        print("  剧情简介  ".center(60, "-"))
        print("-" * 60)
        
        # 简介可能较长，显示适当长度
        summary = movie_data.get('summary')
        max_display_length = 500  # 控制台显示的最大长度
        
        if len(summary) > max_display_length:
            # 如果简介太长，显示部分并保留段落格式
            # 以段落为单位截断，避免截断到段落中间
            paragraphs = summary.split('\n')
            display_text = ""
            current_length = 0
            
            for p in paragraphs:
                if current_length + len(p) + 1 <= max_display_length:  # +1 是为了换行符
                    display_text += p + "\n"
                    current_length += len(p) + 1
                else:
                    # 如果无法显示完整段落，截断并添加省略号
                    remaining = max_display_length - current_length
                    if remaining > 3:  # 确保有足够空间显示省略号
                        display_text += p[:remaining-3] + "..."
                    break
            
            print(f"{display_text}\n(共{len(summary)}字)")
        else:
            # 直接显示完整简介，保留原有格式
            print(summary)
    
    print("-" * 60)

def main():
    print_header()
    crawler = None
    
    # 初始化爬虫和Notion API
    try:
        print("正在初始化Selenium和ChromeDriver...")
        crawler = DoubanCrawler()
        
        try:
            notion_api = NotionAPI()
            print("初始化完成")
        except Exception as e:
            print(f"Notion API初始化错误: {e}")
            print("请检查环境变量中是否正确设置了Notion API密钥和数据库ID")
            sys.exit(1)
    except Exception as e:
        print(f"浏览器初始化错误: {e}")
        print("请确保已正确安装Chrome浏览器")
        sys.exit(1)
    
    try:
        while True:
            try:
                # 获取用户输入
                print("\n" + "-" * 60)
                keyword = input("请输入影视名称 (输入'q'退出): ")
                print("-" * 60)
                
                if keyword.lower() == 'q':
                    print("感谢使用，正在关闭浏览器...")
                    break
                    
                if not keyword:
                    print("请输入有效的影视名称")
                    continue
                
                print(f"\n正在使用浏览器搜索 '{keyword}'...")
                search_results = crawler.search_movie(keyword)
                
                if not search_results:
                    print("未找到相关影视作品，请尝试其他关键词")
                    continue
                
                # 自动选择第一个结果，不再让用户选择
                selected_movie = search_results[0]
                
                # 如果有多个结果，显示找到了多少结果
                if len(search_results) > 1:
                    print(f"\n找到 {len(search_results)} 个结果，自动选择第一个")
                
                print(f"\n已选择: 《{selected_movie['title']}》")
                if 'rating' in selected_movie and selected_movie['rating']:
                    print(f"豆瓣评分: {selected_movie['rating']}")
                
                print(f"\n正在获取详细信息...")
                movie_details = crawler.get_movie_details(selected_movie['url'])
                
                if not movie_details:
                    print("获取影视详情失败，请稍后重试")
                    continue
                
                # 显示电影详情
                print_movie_details(movie_details)
                
                # 直接添加到Notion，不再询问用户
                print("\n正在添加到Notion数据库...")
                success = notion_api.add_movie_to_notion(movie_details)
                
                if success:
                    print(f"\n✅ 已成功将 《{movie_details['title']}》 添加到Notion数据库")
                else:
                    print("\n❌ 添加到Notion数据库失败，请检查API设置和网络连接")
                
                # 暂停一下，避免频繁请求
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n程序被中断")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                time.sleep(1)
                continue
    finally:
        # 确保浏览器被关闭
        if crawler:
            print("\n正在关闭浏览器...")
            del crawler

if __name__ == "__main__":
    main() 