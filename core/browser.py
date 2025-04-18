"""
浏览器管理模块，提供Playwright浏览器的基础功能
"""
import asyncio
import random
import time
from typing import Optional, List, Dict, Any

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError

from config.logging_config import setup_logger
from config.settings import (
    DEFAULT_TIMEOUT, 
    DEFAULT_HEADLESS, 
    BROWSER_HEADERS,
    USER_AGENTS
)

# 创建日志记录器
logger = setup_logger('browser')

class PlaywrightBrowser:
    """Playwright浏览器管理器，提供无头浏览器的基础功能"""
    
    def __init__(self, 
                 headless: bool = DEFAULT_HEADLESS, 
                 proxy: Optional[str] = None, 
                 user_agent: Optional[str] = None,
                 timeout: int = DEFAULT_TIMEOUT,
                 cookies: Optional[List[Dict[str, str]]] = None):
        """
        初始化浏览器管理器
        
        Args:
            headless: 是否使用无头模式
            proxy: 代理服务器地址 格式为 "http://ip:port"
            user_agent: 自定义User-Agent
            timeout: 页面加载超时时间(毫秒)
            cookies: 浏览器Cookie列表
        """
        self.headless = headless
        self.proxy = proxy
        self.user_agent = user_agent or self._get_random_ua()
        self.timeout = timeout
        self.cookies = cookies or []
        self.browser = None
        self.context = None
        self.playwright = None
        
        # 请求头
        self.headers = BROWSER_HEADERS.copy()
    
    def _get_random_ua(self) -> str:
        """获取随机User-Agent"""
        return random.choice(USER_AGENTS)
    
    async def __aenter__(self):
        await self.init_browser()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def init_browser(self):
        """初始化浏览器和上下文"""
        self.playwright = await async_playwright().start()
        browser_args = {}
        
        if self.proxy:
            browser_args["proxy"] = {"server": self.proxy}
        
        # 启动浏览器时设置更多真实特性
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        
        # 创建上下文时设置更多真实参数
        self.context = await self.browser.new_context(
            user_agent=self.user_agent,
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            **browser_args
        )
        
        # 添加Cookie
        if self.cookies:
            await self.context.add_cookies(self.cookies)
        
        # 设置额外的headers
        await self.context.set_extra_http_headers(self.headers)
        
        # 仅阻止图片等资源加载，提高速度
        await self.context.route("**/*.{png,jpg,jpeg,gif,svg,ico}", lambda route: route.abort())
        
        logger.info("浏览器模块初始化完成")
        return self.context
    
    async def close(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("浏览器已关闭")
    
    async def new_page(self) -> Page:
        """创建新页面"""
        if not self.context:
            await self.init_browser()
        
        page = await self.context.new_page()
        page.set_default_navigation_timeout(self.timeout)
        return page
    
    async def navigate(self, page: Page, url: str, wait_until: str = "domcontentloaded") -> bool:
        """
        导航到指定URL
        
        Args:
            page: Playwright页面对象
            url: 目标URL
            wait_until: 等待页面加载策略
            
        Returns:
            是否导航成功
        """
        try:
            await page.goto(url, wait_until=wait_until)
            return True
        except Exception as e:
            logger.error(f"导航到 {url} 失败: {e}")
            return False
    
    async def wait_for_selector(self, page: Page, selector: str, timeout: int = 10000) -> bool:
        """
        等待选择器出现
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间(毫秒)
            
        Returns:
            是否等待成功
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            logger.warning(f"等待选择器 {selector} 超时: {e}")
            return False
    
    async def random_sleep(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """随机等待一段时间，防止被反爬"""
        sleep_time = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(sleep_time)
    
    async def simulate_human_behavior(self, page: Page):
        """模拟人类行为，随机滚动页面"""
        try:
            # 随机滚动页面
            await page.evaluate("""
                () => {
                    const scrollHeight = Math.floor(document.body.scrollHeight * 0.7);
                    window.scrollTo(0, Math.floor(Math.random() * scrollHeight));
                }
            """)
            
            # 随机暂停
            await self.random_sleep(1.0, 2.0)
        except Exception as e:
            logger.warning(f"模拟人类行为失败: {e}")
    
    async def save_debug_info(self, page: Page, prefix: str = "debug"):
        """
        保存页面截图和HTML用于调试
        
        Args:
            page: Playwright页面对象
            prefix: 文件名前缀
        """
        try:
            timestamp = int(time.time())
            filename = f"{prefix}_{timestamp}"
            
            await page.screenshot(path=f"{filename}.png")
            
            page_content = await page.content()
            with open(f"{filename}.html", "w", encoding="utf-8") as f:
                f.write(page_content)
                
            logger.info(f"已保存调试信息: {filename}.png 和 {filename}.html")
        except Exception as e:
            logger.error(f"保存调试信息失败: {e}") 