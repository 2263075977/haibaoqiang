"""
豆瓣影视数据爬取模块
"""
from typing import Dict, List, Optional, Any

from playwright.async_api import TimeoutError

from core.browser import PlaywrightBrowser
from scrapers.base_scraper import BaseScraper
from parsers.douban_parser import DoubanParser
from config.logging_config import setup_logger
from config.settings import DOUBAN_COOKIES

# 创建日志记录器
logger = setup_logger('douban_scraper')

class DoubanScraper(BaseScraper):
    """豆瓣影视数据抓取器"""
    
    def __init__(self, browser: PlaywrightBrowser, retry_times: int = 3):
        """
        初始化豆瓣数据抓取器
        
        Args:
            browser: Playwright浏览器管理器实例
            retry_times: 重试次数
        """
        super().__init__(browser, retry_times)
        
        # 豆瓣Cookie - 使用配置中的Cookie
        self.douban_cookies = DOUBAN_COOKIES
        
        # 设置豆瓣特有的请求头
        self.browser.headers["referer"] = "https://movie.douban.com/"
        
        # 如果提供了豆瓣Cookie，则添加到浏览器
        if hasattr(self.browser, 'cookies') and self.browser.cookies:
            logger.info("已提供浏览器通用Cookie")
        else:
            self.browser.cookies = self.douban_cookies
            logger.info("已设置豆瓣专用Cookie")
    
    async def search_movie(self, title: str) -> Optional[str]:
        """
        搜索电影，返回详情页URL
        
        Args:
            title: 电影名称
            
        Returns:
            详情页URL或None
        """
        search_url = f"https://search.douban.com/movie/subject_search?search_text={title}&cat=1002"
        
        page = await self.navigate_with_retry(search_url)
        if not page:
            return None
        
        try:
            # 延迟等待，模拟真实用户行为
            await self.browser.random_sleep(2.0, 4.0)
            
            # 等待页面完全加载
            try:
                # 尝试不同的选择器，因为页面结构可能有变化
                for selector in ["#root", ".search-result", ".search", ".item-root", ".result-list", ".search__content"]:
                    if await page.query_selector(selector):
                        await self.browser.wait_for_selector(page, selector, timeout=5000)
                        logger.info(f"找到选择器: {selector}")
                        break
            except Exception as e:
                logger.warning(f"等待选择器超时，尝试继续: {e}")
            
            # 查找第一个搜索结果 - 尝试多种可能的结构
            first_result = None
            for selector in [
                ".result h3 a",
                ".result-list .result h3 a", 
                ".result_list .item-root a",
                ".search-results .item h3 a",
                "a[href^='https://movie.douban.com/subject/']"
            ]:
                items = await page.query_selector_all(selector)
                if items and len(items) > 0:
                    first_result = items[0]
                    logger.info(f"使用选择器找到结果: {selector}")
                    break
            
            if not first_result:
                # 最后的备选方案：使用URL模式直接查找链接
                all_links = await page.query_selector_all("a")
                for link in all_links:
                    href = await link.get_attribute("href")
                    if href and "movie.douban.com/subject/" in href:
                        first_result = link
                        logger.info(f"使用链接模式找到结果: {href}")
                        break
            
            if not first_result:
                logger.warning(f"未找到影视: {title}")
                # 保存页面调试信息
                await self.browser.save_debug_info(page, f"search_debug_{title.replace(' ', '_')}")
                await page.close()
                return None
            
            detail_url = await first_result.get_attribute("href")
            logger.info(f"找到影视详情页: {detail_url}")
            
            await page.close()
            return detail_url
        
        except Exception as e:
            logger.error(f"搜索影视出错: {e}")
            try:
                # 保存页面调试信息
                await self.browser.save_debug_info(page, f"error_debug_{title.replace(' ', '_')}")
                await page.close()
            except:
                pass
            return None
        
    async def get_movie_by_url(self, url: str) -> Dict[str, Any]:
        """
        从URL获取电影详情
        
        Args:
            url: 电影详情页URL
            
        Returns:
            电影数据字典
        """
        for attempt in range(self.retry_times):
            try:
                logger.info(f"获取电影详情 (尝试 {attempt+1}/{self.retry_times}): {url}")
                
                # 使用基类的方法导航到页面
                page = await self.navigate_with_retry(url)
                if not page:
                    continue
                
                # 等待页面加载完成
                if not await self.browser.wait_for_selector(page, '#content', timeout=10000):
                    logger.warning("等待页面内容超时，尝试继续处理...")
                
                # 使用解析器提取数据
                movie_data = await DoubanParser.extract_movie_data(page)
                
                # 关闭页面
                await page.close()
                return movie_data
                
            except TimeoutError:
                logger.warning(f"页面加载超时，尝试继续处理...")
                if 'page' in locals():
                    await self.browser.save_debug_info(page, f"timeout_debug_{attempt}")
                    await page.close()
                    
            except Exception as e:
                logger.error(f"获取电影详情出错: {e}")
                if 'page' in locals():
                    await self.browser.save_debug_info(page, f"error_detail_{attempt}")
                    await page.close()
                    
                # 失败后等待更长时间
                await self.browser.random_sleep(3.0, 5.0)
                
        logger.error(f"获取电影详情失败，已重试 {self.retry_times} 次: {url}")
        return {}
        
    async def get_movie_by_title(self, title: str) -> Dict[str, Any]:
        """
        通过电影名称获取电影详情
        
        Args:
            title: 电影名称
            
        Returns:
            电影数据字典
        """
        # 搜索电影
        detail_url = await self.search_movie(title)
        if not detail_url:
            logger.warning(f"未找到电影: {title}")
            return {}
            
        # 获取电影详情
        return await self.get_movie_by_url(detail_url) 