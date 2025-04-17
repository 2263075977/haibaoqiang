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
        # 配置Chrome选项
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")  # 无头模式，不显示浏览器窗口
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")  # 在Docker中必须
        self.chrome_options.add_argument("--disable-dev-shm-usage")  # 在Docker中必须
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-infobars")
        
        # 添加忽略SSL错误的选项
        self.chrome_options.add_argument("--ignore-certificate-errors")
        self.chrome_options.add_argument("--ignore-ssl-errors")
        self.chrome_options.add_argument("--allow-insecure-localhost")
        
        # 禁用所有日志输出
        self.chrome_options.add_argument("--log-level=3")  # 只显示FATAL错误
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 添加真实的User-Agent
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36")
        
        # 尝试使用环境变量中的Chrome二进制路径
        chrome_bin = os.environ.get("CHROME_BIN")
        if chrome_bin:
            self.chrome_options.binary_location = chrome_bin
            print(f"使用指定的Chrome二进制路径: {chrome_bin}")
        
        # 从环境变量中读取Cookie
        self.cookies = []
        bid = os.getenv("DOUBAN_BID")
        ll = os.getenv("DOUBAN_LL")
        dbcl2 = os.getenv("DOUBAN_DBCL2")
        ck = os.getenv("DOUBAN_CK")
        
        # 准备Cookie
        if bid:
            self.cookies.append({"name": "bid", "value": bid, "domain": ".douban.com"})
        if ll:
            self.cookies.append({"name": "ll", "value": f'"{ll}"', "domain": ".douban.com"})
        if dbcl2:
            self.cookies.append({"name": "dbcl2", "value": f'"{dbcl2}"', "domain": ".douban.com"})
        if ck:
            self.cookies.append({"name": "ck", "value": ck, "domain": ".douban.com"})
            
        # 豆瓣电影搜索URL
        self.search_url = "https://search.douban.com/movie/subject_search?search_text={}&cat=1002"
        
        # 驱动初始化标志
        self.driver = None
        
    def _initialize_driver(self):
        """初始化浏览器驱动"""
        if self.driver is None:
            print("初始化Chrome浏览器...")
            
            # 临时重定向标准输出以抑制ChromeDriver和TensorFlow的消息
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            sys.stdout = open(os.devnull, 'w')
            sys.stderr = open(os.devnull, 'w')
            
            try:
                # 设置重试次数
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        # 检查环境变量中是否有ChromeDriver路径
                        chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
                        
                        if chromedriver_path and os.path.exists(chromedriver_path):
                            # 使用指定的ChromeDriver路径
                            print(f"使用指定的ChromeDriver: {chromedriver_path}")
                            service = Service(executable_path=chromedriver_path)
                        else:
                            # 尝试使用webdriver-manager下载
                            print("使用webdriver-manager下载ChromeDriver")
                            service = Service(ChromeDriverManager().install())
                            
                        self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
                        
                        # 设置页面加载超时
                        self.driver.set_page_load_timeout(30)
                        
                        # 先访问豆瓣主页，然后添加Cookie
                        if self.cookies:
                            try:
                                self.driver.get("https://www.douban.com")
                                print("添加Cookie...")
                                for cookie in self.cookies:
                                    try:
                                        self.driver.add_cookie(cookie)
                                    except Exception as e:
                                        print(f"添加Cookie失败: {e}")
                            except Exception as e:
                                print(f"访问豆瓣首页失败: {e}")
                        
                        # 成功初始化，跳出循环
                        break
                    except Exception as e:
                        retry_count += 1
                        print(f"初始化Chrome浏览器失败 (尝试 {retry_count}/{max_retries}): {e}")
                        
                        # 如果之前创建了driver，确保关闭它
                        if self.driver:
                            try:
                                self.driver.quit()
                            except:
                                pass
                            self.driver = None
                            
                        # 如果达到最大重试次数，抛出异常
                        if retry_count >= max_retries:
                            raise Exception(f"多次尝试初始化浏览器失败: {e}")
                            
                        # 等待一段时间再重试
                        time.sleep(2)
            except Exception as e:
                print(f"初始化Chrome浏览器失败: {e}")
                raise
            finally:
                # 恢复标准输出
                sys.stdout = original_stdout
                sys.stderr = original_stderr
    
    def _close_driver(self):
        """关闭浏览器驱动"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"关闭浏览器时出错: {e}")
            finally:
                self.driver = None
    
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
            # 初始化驱动
            self._initialize_driver()
            
            # 对关键词进行URL编码
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = self.search_url.format(encoded_keyword)
            
            # 添加重试机制
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    print(f"访问搜索页面: {search_url}")
                    self.driver.get(search_url)
                    break  # 成功访问，跳出循环
                except TimeoutException:
                    print("页面加载超时，尝试刷新页面...")
                    retry_count += 1
                    if retry_count >= max_retries:
                        print("多次尝试加载页面失败，尝试继续处理...")
                        break
                    self.driver.refresh()  # 刷新页面
                    time.sleep(2)  # 等待一段时间
                except Exception as e:
                    print(f"访问搜索页面出错: {e}")
                    return []
            
            # 等待搜索结果加载
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".search-result, .item-root, a[href*='/subject/']"))
                )
            except TimeoutException:
                print("等待搜索结果超时，页面可能加载不完整")
            
            # 获取页面源码并解析
            html = self.driver.page_source
            
            # 尝试使用Selenium直接查找结果
            search_items = self.driver.find_elements(By.CSS_SELECTOR, ".item-root")
            
            if not search_items or len(search_items) == 0:
                print("未找到.item-root元素，尝试其他选择器")
                search_items = self.driver.find_elements(By.CSS_SELECTOR, ".search-result .result, .search-result")
            
            if not search_items or len(search_items) == 0:
                print("未找到常规搜索结果元素，尝试查找任何电影链接")
                # 如果还是没有找到，使用更通用的选择器
                search_items = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/subject/']")
            
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
            self._initialize_driver()
            self._random_sleep()  # 随机延迟
            
            print(f"访问电影详情页: {url}")
            try:
                self.driver.get(url)
            except TimeoutException:
                print("页面加载超时，尝试继续处理...")
            except Exception as e:
                print(f"访问电影详情页出错: {e}")
                return {}
            
            # 等待页面加载完成
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#content"))
                )
            except TimeoutException:
                print("等待页面加载超时，尝试继续处理")
            
            # 获取页面源码
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            
            # 提取基本信息
            movie_data = {}
            
            # 标题
            try:
                title_elems = self.driver.find_elements(By.CSS_SELECTOR, 'h1 span[property="v:itemreviewed"]')
                if title_elems:
                    original_title = title_elems[0].text.strip()
                    # 只保留第一个标题（如果有多个版本）
                    movie_data['title'] = self._clean_title(original_title)
                else:
                    # 尝试从h1查找
                    h1_elems = self.driver.find_elements(By.CSS_SELECTOR, 'h1')
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
                info_elements = self.driver.find_elements(By.CSS_SELECTOR, '#info')
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
                director_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[rel="v:directedBy"]')
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
                info_elements = self.driver.find_elements(By.CSS_SELECTOR, '#info')
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
                actor_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[rel="v:starring"]')
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
                genres = self.driver.find_elements(By.CSS_SELECTOR, 'span[property="v:genre"]')
                movie_data['genres'] = [g.text.strip() for g in genres]
            except Exception as e:
                print(f"提取类型时出错: {e}")
                movie_data['genres'] = []
            
            # 上映日期 - 只保留第一个
            try:
                release_dates = self.driver.find_elements(By.CSS_SELECTOR, 'span[property="v:initialReleaseDate"]')
                if release_dates and len(release_dates) > 0:
                    movie_data['release_dates'] = [release_dates[0].text.strip()]
                else:
                    movie_data['release_dates'] = []
            except Exception as e:
                print(f"提取上映日期时出错: {e}")
                movie_data['release_dates'] = []
            
            # 提取IMDb ID - 修正为直接提取tt开头的ID
            try:
                info_elements = self.driver.find_elements(By.CSS_SELECTOR, '#info')
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
                info_elements = self.driver.find_elements(By.CSS_SELECTOR, '#info')
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
                rating_elems = self.driver.find_elements(By.CSS_SELECTOR, '.rating_num')
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
                summary_expanded = self.driver.find_elements(By.CSS_SELECTOR, 'span[property="v:summary"]')
                if summary_expanded and summary_expanded[0].text.strip():
                    summary_text = summary_expanded[0].text.strip()
                else:
                    # 如果找不到展开的简介，尝试找短简介
                    summary_short = self.driver.find_elements(By.CSS_SELECTOR, 'span.short')
                    if summary_short and summary_short[0].text.strip():
                        summary_text = summary_short[0].text.strip()
                    else:
                        # 尝试通过类获取
                        summary_div = self.driver.find_elements(By.CSS_SELECTOR, 'div.indent span.all.hidden, div.indent span.short')
                        if summary_div and summary_div[0].text.strip():
                            summary_text = summary_div[0].text.strip()
                        else:
                            # 最后尝试找任何可能包含简介的元素
                            summary_any = self.driver.find_elements(By.CSS_SELECTOR, 'div[id="link-report"] span, div.related-info div.indent')
                            if summary_any and summary_any[0].text.strip():
                                summary_text = summary_any[0].text.strip()
                            else:
                                # 备用方案：找任何可能的简介内容
                                summary_text = ""
                                for elem in self.driver.find_elements(By.CSS_SELECTOR, '.related-info'):
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
                poster_elems = self.driver.find_elements(By.CSS_SELECTOR, '#mainpic img')
                if poster_elems:
                    movie_data['poster'] = poster_elems[0].get_attribute('src')
                else:
                    # 尝试其他可能的图片选择器
                    poster_elems = self.driver.find_elements(By.CSS_SELECTOR, '.nbgnbg img, .cover img')
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