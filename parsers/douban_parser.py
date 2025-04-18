"""
豆瓣数据解析模块，负责从页面提取结构化数据
"""
import re
from typing import Dict, List, Any

from playwright.async_api import Page

from core.utils import clean_title
from config.logging_config import setup_logger

# 创建解析器日志记录器
logger = setup_logger('douban_parser')

class DoubanParser:
    """豆瓣数据解析器，负责从页面提取影视信息"""
    
    @staticmethod
    def _clean_title(title: str) -> str:
        """
        清理标题，只保留主标题
        例如："肖申克的救赎 The Shawshank Redemption (1994)" -> "肖申克的救赎"
        """
        return clean_title(title)
    
    @staticmethod
    def _determine_content_type(url: str, genres: List[str], info_text: str) -> str:
        """
        判断内容类型是电影还是电视剧
        
        Args:
            url: 详情页URL
            genres: 类型标签列表
            info_text: 信息文本
            
        Returns:
            "电影" 或 "电视剧"
        """
        # 方法1: 通过URL判断
        if "movie" in url:
            return "电影"
        if "tv" in url:
            return "电视剧"
        
        # 方法2: 通过类型判断
        if "电视剧" in genres or "美剧" in genres or "日剧" in genres or "韩剧" in genres:
            return "电视剧"
        
        # 方法3: 通过集数信息判断
        if "集数:" in info_text or "单集片长:" in info_text:
            return "电视剧"
        
        # 默认为电影
        return "电影"
    
    @classmethod
    async def extract_movie_data(cls, page: Page) -> Dict[str, Any]:
        """
        从页面提取电影数据
        
        Args:
            page: Playwright页面对象
            
        Returns:
            电影数据字典
        """
        movie_data = {}
        
        # 提取标题
        try:
            title_elem = await page.query_selector('h1 span[property="v:itemreviewed"]')
            if title_elem:
                original_title = await title_elem.text_content()
                movie_data['title'] = cls._clean_title(original_title)
            else:
                # 备选提取方法
                h1_elem = await page.query_selector('h1')
                if h1_elem:
                    original_title = await h1_elem.text_content()
                    movie_data['title'] = cls._clean_title(original_title)
                else:
                    movie_data['title'] = None
        except Exception as e:
            logger.error(f"提取标题出错: {e}")
            movie_data['title'] = None
            
        # 提取导演
        try:
            directors = []
            director_elems = await page.query_selector_all('a[rel="v:directedBy"]')
            for director_elem in director_elems:
                name = await director_elem.text_content()
                url = await director_elem.get_attribute('href')
                directors.append({"name": name.strip(), "url": url})
            movie_data['directors'] = directors
        except Exception as e:
            logger.error(f"提取导演出错: {e}")
            movie_data['directors'] = []
            
        # 提取编剧
        try:
            screenwriters = []
            info_elem = await page.query_selector('#info')
            if info_elem:
                info_html = await info_elem.inner_html()
                # 使用正则表达式提取编剧信息
                screenwriter_match = re.search(r'编剧</span>:(.*?)<br/?>', info_html, re.DOTALL)
                if screenwriter_match:
                    screenwriter_html = screenwriter_match.group(1)
                    # 提取所有<a>标签
                    sw_links = re.findall(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', screenwriter_html)
                    for url, name in sw_links:
                        screenwriters.append({"name": name.strip(), "url": url})
            movie_data['screenwriters'] = screenwriters
        except Exception as e:
            logger.error(f"提取编剧出错: {e}")
            movie_data['screenwriters'] = []
            
        # 提取主演 (前5名)
        try:
            actors = []
            actor_elems = await page.query_selector_all('a[rel="v:starring"]')
            for actor_elem in actor_elems[:5]:  # 只取前5名
                name = await actor_elem.text_content()
                url = await actor_elem.get_attribute('href')
                actors.append({"name": name.strip(), "url": url})
            movie_data['actors'] = actors
        except Exception as e:
            logger.error(f"提取主演出错: {e}")
            movie_data['actors'] = []
            
        # 提取类型
        try:
            genres = []
            genre_elems = await page.query_selector_all('span[property="v:genre"]')
            for genre_elem in genre_elems:
                genre_text = await genre_elem.text_content()
                genres.append(genre_text.strip())
            movie_data['genres'] = genres
        except Exception as e:
            logger.error(f"提取类型出错: {e}")
            movie_data['genres'] = []
            
        # 提取语言
        try:
            info_elem = await page.query_selector('#info')
            if info_elem:
                info_text = await info_elem.text_content()
                language_match = re.search(r'语言:\s*(.*?)(?:\n|$)', info_text)
                if language_match:
                    languages = [lang.strip() for lang in language_match.group(1).split('/')]
                    movie_data['languages'] = languages
                else:
                    movie_data['languages'] = []
            else:
                movie_data['languages'] = []
        except Exception as e:
            logger.error(f"提取语言出错: {e}")
            movie_data['languages'] = []
            
        # 提取评分
        try:
            rating_elem = await page.query_selector('strong[property="v:average"]')
            if rating_elem:
                rating_text = await rating_elem.text_content()
                try:
                    movie_data['rating'] = float(rating_text)
                except ValueError:
                    movie_data['rating'] = None
            else:
                movie_data['rating'] = None
        except Exception as e:
            logger.error(f"提取评分出错: {e}")
            movie_data['rating'] = None
            
        # 提取IMDb ID
        try:
            info_elem = await page.query_selector('#info')
            if info_elem:
                info_text = await info_elem.text_content()
                imdb_match = re.search(r'IMDb:\s*(tt\d+)', info_text)
                if imdb_match:
                    movie_data['imdb_id'] = imdb_match.group(1)
                else:
                    # 尝试其他匹配方式
                    info_html = await info_elem.inner_html()
                    imdb_link_match = re.search(r'href="https?://www\.imdb\.com/title/(tt\d+)"', info_html)
                    if imdb_link_match:
                        movie_data['imdb_id'] = imdb_link_match.group(1)
                    else:
                        movie_data['imdb_id'] = None
            else:
                movie_data['imdb_id'] = None
        except Exception as e:
            logger.error(f"提取IMDb ID出错: {e}")
            movie_data['imdb_id'] = None
            
        # 提取上映日期（首播）
        try:
            release_elem = await page.query_selector('span[property="v:initialReleaseDate"]')
            if release_elem:
                release_text = await release_elem.text_content()
                # 保留完整日期文本，包括地区信息
                movie_data['release_date'] = release_text.strip()
            else:
                movie_data['release_date'] = None
        except Exception as e:
            logger.error(f"提取上映日期出错: {e}")
            movie_data['release_date'] = None
            
        # 提取剧情简介
        try:
            # 尝试获取展开的完整简介
            summary_elem = await page.query_selector('span[property="v:summary"]')
            if not summary_elem:
                # 尝试其他可能的选择器
                summary_elem = await page.query_selector('div.related-info div.indent span.short')
            
            if summary_elem:
                summary_text = await summary_elem.text_content()
                # 清理简介文本
                summary_text = re.sub(r'[\t\f\v ]+', ' ', summary_text).strip()
                # 将文本按段落分割
                paragraphs = re.split(r'\n+', summary_text)
                # 在每个段落前添加中文缩进空格
                formatted_paragraphs = ["　　" + p.strip() for p in paragraphs if p.strip()]
                # 重新组合文本，使用换行符连接
                summary_text = "\n".join(formatted_paragraphs)
                # 限制简介长度
                if len(summary_text) > 1000:
                    summary_text = summary_text[:997] + "..."
                movie_data['summary'] = summary_text
            else:
                movie_data['summary'] = None
        except Exception as e:
            logger.error(f"提取剧情简介出错: {e}")
            movie_data['summary'] = None
            
        # 提取又名
        try:
            info_elem = await page.query_selector('#info')
            if info_elem:
                info_text = await info_elem.text_content()
                aka_match = re.search(r'又名:(.*?)(?:\n|$)', info_text)
                if aka_match:
                    akas = [aka.strip() for aka in aka_match.group(1).split('/')]
                    movie_data['aka'] = "/".join([aka for aka in akas if aka])
                else:
                    movie_data['aka'] = ""
            else:
                movie_data['aka'] = ""
        except Exception as e:
            logger.error(f"提取又名出错: {e}")
            movie_data['aka'] = ""
            
        # 确定内容类型（电影或电视剧）
        try:
            url = page.url
            info_elem = await page.query_selector('#info')
            info_text = await info_elem.text_content() if info_elem else ""
            movie_data['category'] = cls._determine_content_type(url, movie_data.get('genres', []), info_text)
        except Exception as e:
            logger.error(f"确定内容类型出错: {e}")
            movie_data['category'] = "电影"  # 默认为电影
            
        # 提取封面图URL
        try:
            cover_elem = await page.query_selector('div#mainpic img')
            if cover_elem:
                cover_url = await cover_elem.get_attribute('src')
                # 尝试获取更高质量的图片
                if cover_url:
                    # 豆瓣图片链接通常有小中大三种尺寸，尝试获取大图
                    # s_ratio_poster -> l_ratio_poster
                    cover_url = re.sub(r's_ratio_poster', 'l_ratio_poster', cover_url)
                    # webp.image -> large.image
                    cover_url = re.sub(r'webp\.image', 'large.image', cover_url)
                    # x-small -> large
                    cover_url = re.sub(r'x-small', 'large', cover_url)
                    
                    # 确保URL有效，并且能够被Notion访问
                    # 处理一些特殊的URL格式问题
                    if '?' in cover_url:
                        cover_url = cover_url.split('?')[0]
                    
                    # 豆瓣的图片服务器可能被Notion封锁，尝试替换为CDN域名
                    if 'img1.doubanio.com' in cover_url:
                        cover_url = cover_url.replace('img1.doubanio.com', 'img9.doubanio.com')
                    elif 'img2.doubanio.com' in cover_url:
                        cover_url = cover_url.replace('img2.doubanio.com', 'img9.doubanio.com')
                    
                    logger.info(f"提取到封面URL: {cover_url}")
                    movie_data['cover_url'] = cover_url
                else:
                    logger.warning("未能提取到封面图URL属性")
                    movie_data['cover_url'] = None
            else:
                logger.warning("未找到封面图元素")
                movie_data['cover_url'] = None
        except Exception as e:
            logger.error(f"提取封面图URL出错: {e}")
            movie_data['cover_url'] = None
        
        return movie_data 