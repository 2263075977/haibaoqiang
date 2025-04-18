"""
爬虫基类，提供所有爬虫的通用方法
"""
from typing import Optional, Dict, Any

from playwright.async_api import Page, TimeoutError

from core.browser import PlaywrightBrowser
from config.logging_config import setup_logger
from config.settings import DEFAULT_RETRY_TIMES

# 创建日志记录器
logger = setup_logger('base_scraper')

class BaseScraper:
    """爬虫基类，提供基本功能"""
    
    def __init__(self, browser: PlaywrightBrowser, retry_times: int = DEFAULT_RETRY_TIMES):
        """
        初始化爬虫
        
        Args:
            browser: Playwright浏览器管理器实例
            retry_times: 重试次数
        """
        self.browser = browser
        self.retry_times = retry_times
    
    async def navigate_with_retry(self, url: str) -> Optional[Page]:
        """
        带重试功能的页面导航
        
        Args:
            url: 目标URL
            
        Returns:
            成功打开的页面对象，失败返回None
        """
        for attempt in range(self.retry_times):
            try:
                # 随机延迟，避免频繁请求
                await self.browser.random_sleep()
                
                # 创建新页面
                page = await self.browser.new_page()
                
                # 如果是重试，先访问首页，再访问目标页面
                if attempt > 0:
                    await self.browser.navigate(page, "https://www.google.com/")
                    await self.browser.random_sleep(1.0, 2.0)
                
                # 导航到目标页面
                if not await self.browser.navigate(page, url):
                    await page.close()
                    continue
                
                # 模拟人类行为
                await self.browser.simulate_human_behavior(page)
                
                return page
                
            except TimeoutError:
                logger.warning(f"页面加载超时，尝试继续处理...")
                if 'page' in locals():
                    await self.browser.save_debug_info(page, f"timeout_debug_{attempt}")
                    await page.close()
                    
            except Exception as e:
                logger.error(f"页面导航出错: {e}")
                if 'page' in locals():
                    await self.browser.save_debug_info(page, f"error_navigate_{attempt}")
                    await page.close()
                    
                # 失败后等待更长时间
                await self.browser.random_sleep(3.0, 5.0)
        
        logger.error(f"导航到 {url} 失败，已重试 {self.retry_times} 次")
        return None 