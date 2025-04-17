#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from selenium.webdriver.chrome.options import Options

def get_chrome_options():
    """获取优化的Chrome选项配置，适用于Docker容器环境"""
    options = Options()
    
    # 基础设置
    options.add_argument("--headless")  # 无头模式
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Docker容器中必要的设置
    options.add_argument("--no-sandbox")  # 在容器中必须
    options.add_argument("--disable-dev-shm-usage")  # 避免内存不足
    
    # 禁用不必要的功能
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-sync")
    
    # 忽略证书错误
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    
    # 性能优化
    options.add_argument("--disable-infobars")
    options.add_argument("--js-flags=--expose-gc")
    options.add_argument("--enable-precise-memory-info")
    options.add_argument("--disable-default-apps")
    
    # 禁用日志
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # 用户代理
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    
    # 自定义Chrome路径
    if os.environ.get("CHROME_PATH"):
        options.binary_location = os.environ.get("CHROME_PATH")
    
    return options 