#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def check_chrome_installation():
    """检查Chrome安装情况"""
    print("=== Chrome检查 ===")
    
    # 检查环境变量中的Chrome路径
    chrome_path = os.environ.get('CHROME_PATH', '/usr/bin/google-chrome')
    
    if os.path.exists(chrome_path):
        print(f"✅ Chrome已找到: {chrome_path}")
        
        # 获取Chrome版本
        try:
            version_output = subprocess.check_output([chrome_path, '--version']).decode('utf-8').strip()
            print(f"✅ Chrome版本: {version_output}")
        except Exception as e:
            print(f"❌ 无法获取Chrome版本: {e}")
    else:
        print(f"❌ Chrome未找到: {chrome_path}")

def check_chromedriver_installation():
    """检查ChromeDriver安装情况"""
    print("\n=== ChromeDriver检查 ===")
    
    # 检查环境变量中的ChromeDriver路径
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver')
    
    if os.path.exists(chromedriver_path):
        print(f"✅ ChromeDriver已找到: {chromedriver_path}")
        
        # 获取ChromeDriver版本
        try:
            version_output = subprocess.check_output([chromedriver_path, '--version']).decode('utf-8').strip()
            print(f"✅ ChromeDriver版本: {version_output}")
        except Exception as e:
            print(f"❌ 无法获取ChromeDriver版本: {e}")
    else:
        print(f"❌ ChromeDriver未找到: {chromedriver_path}")

def try_selenium_connection():
    """尝试使用Selenium连接Chrome"""
    print("\n=== Selenium连接测试 ===")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # 检查Chrome路径
    chrome_path = os.environ.get('CHROME_PATH')
    if chrome_path and os.path.exists(chrome_path):
        chrome_options.binary_location = chrome_path
    
    # 检查ChromeDriver路径
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
    
    try:
        if chromedriver_path and os.path.exists(chromedriver_path):
            service = Service(executable_path=chromedriver_path)
        else:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 尝试访问一个页面
        driver.get('https://www.google.com')
        print(f"✅ Selenium连接成功! 页面标题: {driver.title}")
        
        # 关闭浏览器
        driver.quit()
    except Exception as e:
        print(f"❌ Selenium连接失败: {e}")

def main():
    """主函数"""
    print("Chrome和ChromeDriver健康检查\n")
    
    check_chrome_installation()
    check_chromedriver_installation()
    try_selenium_connection()

if __name__ == "__main__":
    main() 