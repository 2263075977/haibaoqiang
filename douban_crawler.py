#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time
import random
import os
import sys
import logging
import urllib.parse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# 抑制WebDriver Manager的日志输出
os.environ['WDM_LOG_LEVEL'] = '0'
os.environ['WDM_PRINT_FIRST_LINE'] = 'False'

# 抑制TensorFlow的日志输出
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 设置TensorFlow日志级别为ERROR

# 设置Selenium日志级别
selenium_logger = logging.getLogger('selenium')
selenium_logger.setLevel(logging.ERROR)
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.ERROR)

# 加载环境变量
load_dotenv()

class DoubanCrawler:
    def __init__(self):
        """初始化爬虫"""
        self.browser = None
        self.init_browser()
        
    def init_browser(self):
        """初始化浏览器"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')  # Docker环境必需
            chrome_options.add_argument('--disable-dev-shm-usage')  # Docker环境必需
            chrome_options.add_argument('--disable-gpu')  # 禁用GPU加速
            chrome_options.add_argument('--disable-extensions')  # 禁用扩展
            chrome_options.add_argument('--disable-software-rasterizer')  # 禁用软件光栅化
            chrome_options.add_argument('--ignore-certificate-errors')  # 忽略证书错误
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # 禁用自动化控制检测
            
            # 设置Chrome和ChromeDriver路径
            chrome_bin = os.getenv('CHROME_BIN', '/usr/bin/google-chrome')
            chromedriver_path = os.getenv('CHROMEDRIVER_PATH', 'chromedriver')
            
            if os.path.exists(chrome_bin):
                chrome_options.binary_location = chrome_bin
            
            # 尝试使用环境变量中的ChromeDriver路径
            if os.path.exists(chromedriver_path):
                self.browser = webdriver.Chrome(
                    executable_path=chromedriver_path,
                    options=chrome_options
                )
            else:
                # 如果环境变量中的路径不存在，使用默认方式
                self.browser = webdriver.Chrome(options=chrome_options)
                
            self.browser.set_page_load_timeout(30)  # 设置页面加载超时
            self.browser.implicitly_wait(10)  # 设置隐式等待时间
            
        except Exception as e:
            print(f"初始化浏览器失败: {str(e)}")
            raise
    
    def _close_driver(self):
        """关闭浏览器驱动"""
        if self.browser:
            try:
                self.browser.quit()
            except Exception as e:
                print(f"关闭浏览器时出错: {e}")
            finally:
                self.browser = None
    
    def _random_sleep(self):
        """随机暂停，防止被封IP"""
        time.sleep(random.uniform(1, 3))
    
    def _clean_title(self, title):
        """清理标题，只保留第一个主标题"""
        if not title:
            return ""
        
        # 移除年份和括号内内容
        title = re.sub(r'\s*\(\d{4}\)', '', title)
        
        # 如果标题有多个版本（中英文或其他），只保留第一个
        title_parts = re.split(r'\s+', title, 1)
        return title_parts[0].strip()
    
    def _determine_content_type(self, url, genres, info_text):
        """判断内容是电影还是电视剧"""
        # 默认类型为电影
        content_type = "电影"
        
        # 判断依据一：检查URL
        if "/tv/" in url or "movie.douban" not in url and "tv.douban" in url:
            content_type = "电视剧"
            
        # 判断依据二：检查类型
        tv_keywords = ["剧集", "电视剧", "美剧", "日剧", "韩剧", "英剧", "综艺", "真人秀", "动画剧集"]
        if any(keyword in genre for genre in genres for keyword in tv_keywords):
            content_type = "电视剧"
            
        # 判断依据三：检查是否有集数信息
        if info_text and ("集数:" in info_text or "季数:" in info_text or "单集片长:" in info_text):
            content_type = "电视剧"
            
        # 判断依据四：检查是否有"季"字样在标题中
        if "第一季" in info_text or "第二季" in info_text or re.search(r'第[一二三四五六七八九十\d]+季', info_text):
            content_type = "电视剧"
            
        return content_type
    
    def search_movie(self, keyword):
        """使用Selenium搜索电影"""
        try:
            # 对关键词进行URL编码
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"https://search.douban.com/movie/subject_search?search_text={encoded_keyword}&cat=1002"
            
            # 添加重试机制
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    print(f"访问搜索页面: {search_url}")
                    self.browser.get(search_url)
                    break  # 成功访问，跳出循环
                except TimeoutException:
                    print("页面加载超时，尝试刷新页面...")
                    retry_count += 1
                    if retry_count >= max_retries:
                        print("多次尝试加载页面失败，尝试继续处理...")
                        break
                    self.browser.refresh()  # 刷新页面
                    time.sleep(2)  # 等待一段时间
                except Exception as e:
                    print(f"访问搜索页面出错: {e}")
                    return []
            
            # 等待搜索结果加载
            try:
                WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".search-result, .item-root, a[href*='/subject/']"))
                )
            except TimeoutException:
                print("等待搜索结果超时，页面可能加载不完整")
            
            # 获取页面源码并解析
            html = self.browser.page_source
            
            # 尝试使用Selenium直接查找结果
            search_items = self.browser.find_elements(By.CSS_SELECTOR, ".item-root")
            
            if not search_items or len(search_items) == 0:
                print("未找到.item-root元素，尝试其他选择器")
                search_items = self.browser.find_elements(By.CSS_SELECTOR, ".search-result .result, .search-result")
            
            if not search_items or len(search_items) == 0:
                print("未找到常规搜索结果元素，尝试查找任何电影链接")
                # 如果还是没有找到，使用更通用的选择器
                search_items = self.browser.find_elements(By.CSS_SELECTOR, "a[href*='/subject/']")
            
            # 结果列表
            result_list = []
            
            if search_items and len(search_items) > 0:
                # 处理找到的结果
                for item in search_items:
                    try:
                        # 如果是链接元素，直接使用
                        if item.tag_name == 'a':
                            url = item.get_attribute('href')
                            title = item.text.strip()
                            
                            # 确保是豆瓣电影链接
                            if '/subject/' not in url:
                                continue
                            
                            # 尝试从父元素或周围元素获取年份和评分
                            year = ''
                            rating = ''
                            
                            # 输出找到的项目
                            print(f"找到电影: {title} - {url}")
                            
                            result_list.append({
                                'title': self._clean_title(title),
                                'url': url,
                                'year': year,
                                'rating': rating
                            })
                        else:
                            # 如果是容器元素，查找内部的链接
                            link_elements = item.find_elements(By.CSS_SELECTOR, "a[href*='/subject/']")
                            if not link_elements:
                                continue
                                
                            link = link_elements[0]
                            url = link.get_attribute('href')
                            
                            # 查找标题
                            title_elem = None
                            try:
                                title_elems = item.find_elements(By.CSS_SELECTOR, ".title")
                                if title_elems:
                                    title_elem = title_elems[0]
                                else:
                                    title_elem = link
                            except NoSuchElementException:
                                title_elem = link
                                    
                            title = title_elem.text.strip()
                            if not title:
                                continue
                            
                            # 尝试查找年份
                            year = ''
                            try:
                                year_elems = item.find_elements(By.CSS_SELECTOR, ".meta, .subject-cast")
                                if year_elems:
                                    year_text = year_elems[0].text
                                    year_match = re.search(r'(\d{4})', year_text)
                                    if year_match:
                                        year = year_match.group(1)
                            except Exception:
                                pass
                            
                            # 尝试查找评分
                            rating = ''
                            try:
                                rating_elems = item.find_elements(By.CSS_SELECTOR, ".rating_nums, .rate")
                                if rating_elems:
                                    rating = rating_elems[0].text.strip()
                            except Exception:
                                pass
                            
                            print(f"找到电影: {title} ({year}) - {rating} - {url}")
                            
                            result_list.append({
                                'title': self._clean_title(title),
                                'url': url,
                                'year': year,
                                'rating': rating
                            })
                    except Exception as e:
                        print(f"处理搜索结果项时出错: {e}")
                        continue
            else:
                # 如果没有找到任何元素，尝试从HTML解析
                print("未能通过Selenium直接找到元素，尝试从HTML解析")
                soup = BeautifulSoup(html, 'lxml')
                
                # 查找所有电影链接
                movie_links = soup.select('a[href*="/subject/"]')
                for link in movie_links:
                    url = link.get('href', '')
                    if not url or '/subject/' not in url:
                        continue
                        
                    title = link.text.strip()
                    if not title:
                        continue
                        
                    print(f"从HTML解析找到电影: {title} - {url}")
                    result_list.append({
                        'title': self._clean_title(title),
                        'url': url,
                        'year': '',
                        'rating': ''
                    })
            
            # 去重，确保没有重复的电影
            unique_results = []
            urls = set()
            for movie in result_list:
                if movie['url'] not in urls:
                    urls.add(movie['url'])
                    unique_results.append(movie)
            
            print(f"共找到 {len(unique_results)} 个搜索结果")
            return unique_results
            
        except Exception as e:
            print(f"搜索电影出错: {e}")
            return []
    
    def get_movie_details(self, url):
        """获取电影详情"""
        try:
            self._random_sleep()  # 随机延迟
            
            print(f"访问电影详情页: {url}")
            try:
                self.browser.get(url)
            except TimeoutException:
                print("页面加载超时，尝试继续处理...")
            except Exception as e:
                print(f"访问电影详情页出错: {e}")
                return {}
            
            # 等待页面加载完成
            try:
                WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#content"))
                )
            except TimeoutException:
                print("等待页面加载超时，尝试继续处理")
            
            # 获取页面源码
            html = self.browser.page_source
            soup = BeautifulSoup(html, 'lxml')
            
            # 提取基本信息
            movie_data = {}
            
            # 标题
            try:
                title_elems = self.browser.find_elements(By.CSS_SELECTOR, 'h1 span[property="v:itemreviewed"]')
                if title_elems:
                    original_title = title_elems[0].text.strip()
                    # 只保留第一个标题（如果有多个版本）
                    movie_data['title'] = self._clean_title(original_title)
                else:
                    # 尝试从h1查找
                    h1_elems = self.browser.find_elements(By.CSS_SELECTOR, 'h1')
                    if h1_elems:
                        original_title = h1_elems[0].text.replace('(', ' (').strip()
                        movie_data['title'] = self._clean_title(original_title)
                    else:
                        movie_data['title'] = None
            except Exception as e:
                print(f"提取标题时出错: {e}")
                movie_data['title'] = None
            
            # 又名 - 新增
            try:
                info_elements = self.browser.find_elements(By.CSS_SELECTOR, '#info')
                if info_elements:
                    info_text = info_elements[0].text
                    
                    # 提取又名，格式通常为"又名: xxx / yyy / zzz"
                    aka_match = re.search(r'又名:(.*?)(?:\n|$)', info_text)
                    if aka_match:
                        # 提取所有又名，通常以 / 分隔
                        akas = [aka.strip() for aka in aka_match.group(1).split('/')]
                        # 过滤掉空字符串
                        movie_data['aka'] = [aka for aka in akas if aka]
                    else:
                        movie_data['aka'] = []
                else:
                    movie_data['aka'] = []
            except Exception as e:
                print(f"提取又名信息失败: {e}")
                movie_data['aka'] = []
            
            # 年份 - 按要求不保留
            movie_data['year'] = None
            
            # 导演 - 包含链接
            try:
                movie_data['directors'] = []
                director_elements = self.browser.find_elements(By.CSS_SELECTOR, 'a[rel="v:directedBy"]')
                for director in director_elements:
                    name = director.text.strip()
                    link = director.get_attribute('href')
                    movie_data['directors'].append({
                        'name': name,
                        'url': link
                    })
            except Exception as e:
                print(f"提取导演时出错: {e}")
                movie_data['directors'] = []
            
            # 编剧 - 包含链接
            movie_data['screenwriters'] = []
            try:
                info_elements = self.browser.find_elements(By.CSS_SELECTOR, '#info')
                if info_elements:
                    info_html = info_elements[0].get_attribute('innerHTML')
                    
                    # 使用BeautifulSoup解析
                    sw_soup = BeautifulSoup(info_html, 'lxml')
                    
                    # 找到编剧标签
                    screenwriter_span = sw_soup.find('span', text=re.compile(r'编剧'))
                    if screenwriter_span and screenwriter_span.parent:
                        # 获取编剧部分的所有链接
                        screenwriter_links = screenwriter_span.parent.find_all('a')
                        for link in screenwriter_links:
                            name = link.text.strip()
                            url = link.get('href')
                            if name and url:
                                movie_data['screenwriters'].append({
                                    'name': name,
                                    'url': url
                                })
            except Exception as e:
                print(f"提取编剧信息失败: {e}")
            
            # 主演 - 包含链接
            try:
                movie_data['actors'] = []
                actor_elements = self.browser.find_elements(By.CSS_SELECTOR, 'a[rel="v:starring"]')
                for actor in actor_elements[:5]:  # 只取前5个主演
                    name = actor.text.strip()
                    link = actor.get_attribute('href')
                    movie_data['actors'].append({
                        'name': name,
                        'url': link
                    })
            except Exception as e:
                print(f"提取主演时出错: {e}")
                movie_data['actors'] = []
            
            # 类型
            try:
                genres = self.browser.find_elements(By.CSS_SELECTOR, 'span[property="v:genre"]')
                movie_data['genres'] = [g.text.strip() for g in genres]
            except Exception as e:
                print(f"提取类型时出错: {e}")
                movie_data['genres'] = []
            
            # 上映日期 - 只保留第一个
            try:
                release_dates = self.browser.find_elements(By.CSS_SELECTOR, 'span[property="v:initialReleaseDate"]')
                if release_dates and len(release_dates) > 0:
                    movie_data['release_dates'] = [release_dates[0].text.strip()]
                else:
                    movie_data['release_dates'] = []
            except Exception as e:
                print(f"提取上映日期时出错: {e}")
                movie_data['release_dates'] = []
            
            # 提取IMDb ID - 修正为直接提取tt开头的ID
            try:
                info_elements = self.browser.find_elements(By.CSS_SELECTOR, '#info')
                if info_elements:
                    info_html = info_elements[0].get_attribute('innerHTML')
                    
                    # IMDb ID - 直接提取tt开头的ID
                    imdb_match = re.search(r'IMDb:</span>\s*<a[^>]*>(tt\d+)</a>', info_html)
                    if imdb_match:
                        movie_data['imdb_id'] = imdb_match.group(1)
                    else:
                        # 尝试找到任何tt开头的ID
                        imdb_direct_match = re.search(r'(tt\d+)', info_html)
                        movie_data['imdb_id'] = imdb_direct_match.group(1) if imdb_direct_match else None
                else:
                    movie_data['imdb_id'] = None
            except Exception as e:
                print(f"提取IMDb ID失败: {e}")
                movie_data['imdb_id'] = None
            
            # 语言
            try:
                info_elements = self.browser.find_elements(By.CSS_SELECTOR, '#info')
                if info_elements:
                    info_text = info_elements[0].text
                    
                    # 语言
                    language_match = re.search(r'语言:\s*(.*?)\n', info_text)
                    if language_match:
                        movie_data['languages'] = [l.strip() for l in language_match.group(1).split('/')]
                    else:
                        movie_data['languages'] = []
                else:
                    movie_data['languages'] = []
            except Exception as e:
                print(f"提取语言信息失败: {e}")
                movie_data['languages'] = []
            
            # 评分
            try:
                rating_elems = self.browser.find_elements(By.CSS_SELECTOR, '.rating_num')
                if rating_elems:
                    movie_data['rating'] = rating_elems[0].text.strip()
                else:
                    movie_data['rating'] = None
            except Exception as e:
                print(f"提取评分时出错: {e}")
                movie_data['rating'] = None
            
            # 剧情简介 - 新增
            try:
                # 先尝试获取展开后的简介
                summary_expanded = self.browser.find_elements(By.CSS_SELECTOR, 'span[property="v:summary"]')
                if summary_expanded and summary_expanded[0].text.strip():
                    summary_text = summary_expanded[0].text.strip()
                else:
                    # 如果找不到展开的简介，尝试找短简介
                    summary_short = self.browser.find_elements(By.CSS_SELECTOR, 'span.short')
                    if summary_short and summary_short[0].text.strip():
                        summary_text = summary_short[0].text.strip()
                    else:
                        # 尝试通过类获取
                        summary_div = self.browser.find_elements(By.CSS_SELECTOR, 'div.indent span.all.hidden, div.indent span.short')
                        if summary_div and summary_div[0].text.strip():
                            summary_text = summary_div[0].text.strip()
                        else:
                            # 最后尝试找任何可能包含简介的元素
                            summary_any = self.browser.find_elements(By.CSS_SELECTOR, 'div[id="link-report"] span, div.related-info div.indent')
                            if summary_any and summary_any[0].text.strip():
                                summary_text = summary_any[0].text.strip()
                            else:
                                # 备用方案：找任何可能的简介内容
                                summary_text = ""
                                for elem in self.browser.find_elements(By.CSS_SELECTOR, '.related-info'):
                                    if '剧情简介' in elem.text or '简介' in elem.text:
                                        summary_content = elem.text.replace('剧情简介', '').replace('简介', '').strip()
                                        if summary_content:
                                            summary_text = summary_content
                                            break
                
                # 清理简介文本
                if summary_text:
                    # 移除多余空白字符，但保留段落之间的换行
                    summary_text = re.sub(r'[\t\f\v ]+', ' ', summary_text).strip()
                    
                    # 将文本按段落分割
                    paragraphs = re.split(r'\n+', summary_text)
                    
                    # 在每个段落前添加中文缩进空格
                    formatted_paragraphs = ["　　" + p.strip() for p in paragraphs if p.strip()]
                    
                    # 重新组合文本，使用换行符连接
                    summary_text = "\n".join(formatted_paragraphs)
                    
                    # 限制简介长度，避免太长
                    if len(summary_text) > 1000:
                        summary_text = summary_text[:997] + "..."
                    movie_data['summary'] = summary_text
                else:
                    movie_data['summary'] = None
            except Exception as e:
                print(f"提取剧情简介时出错: {e}")
                movie_data['summary'] = None
            
            # 封面图片
            try:
                poster_elems = self.browser.find_elements(By.CSS_SELECTOR, '#mainpic img')
                if poster_elems:
                    movie_data['poster'] = poster_elems[0].get_attribute('src')
                else:
                    # 尝试其他可能的图片选择器
                    poster_elems = self.browser.find_elements(By.CSS_SELECTOR, '.nbgnbg img, .cover img')
                    if poster_elems:
                        movie_data['poster'] = poster_elems[0].get_attribute('src')
                    else:
                        movie_data['poster'] = None
            except Exception as e:
                print(f"提取封面图片时出错: {e}")
                movie_data['poster'] = None
            
            # 确定内容类型（电影或电视剧）
            info_text = info_elements[0].text if info_elements else ""
            movie_data['content_type'] = self._determine_content_type(url, movie_data.get('genres', []), info_text)
            print(f"内容类型: {movie_data['content_type']}")
            
            return movie_data
            
        except Exception as e:
            print(f"获取电影详情出错: {e}")
            return {}
        
    def __del__(self):
        """析构函数，确保关闭浏览器"""
        self._close_driver() 