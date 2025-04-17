#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from selenium.webdriver.chrome.options import Options

def get_chrome_options():
    """获取优化的Chrome选项配置"""
    chrome_options = Options()
    
    # 无头模式
    chrome_options.add_argument("--headless")
    
    # 基本设置
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 如果在Docker环境中，添加额外的安全设置
    if os.environ.get('CHROME_NO_SANDBOX'):
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 禁用不必要的扩展和功能
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-background-networking")
    
    # 提高性能的设置
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-web-security")  # 注意：这可能影响安全性
    
    # 忽略SSL错误
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    
    # 禁用日志
    chrome_options.add_argument("--log-level=3")  # 只显示FATAL错误
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 添加真实的User-Agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    
    # 如果存在，设置自定义的Chrome可执行文件路径
    if os.environ.get('CHROME_PATH'):
        chrome_options.binary_location = os.environ.get('CHROME_PATH')
    
    return chrome_options 