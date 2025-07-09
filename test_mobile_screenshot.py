#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试移动端页面截图问题
Test mobile page screenshot issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.screenshot.capture import ScreenshotCapture
from src.utils.logger import get_logger

logger = get_logger(__name__)

def test_mobile_screenshot():
    """测试移动端截图问题"""
    print("🔍 测试移动端页面截图问题")
    print("=" * 60)
    
    # 测试参数（从日志中提取）
    url = "https://www.kalodata.com/settings"
    xpath = "/html/body/div/div/div/div[2]/div/div/div[2]/div[2]"
    device = "mobile"
    output_path = "screenshots/test_mobile_debug.png"
    
    print(f"URL: {url}")
    print(f"XPath: {xpath}")
    print(f"设备: {device}")
    print(f"输出路径: {output_path}")
    print("-" * 60)
    
    try:
        # 创建截图器
        capturer = ScreenshotCapture(browser='chrome', headless=True, language='en-US')
        
        print("✅ 截图器创建成功")
        
        # 尝试截图
        print("🌐 开始访问页面...")
        result_path = capturer.capture_element_by_xpath(
            url=url,
            xpath=xpath,
            output_path=output_path,
            device=device,
            wait_time=5
        )
        
        print(f"✅ 截图成功保存: {result_path}")
        
        # 检查文件大小
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"📊 文件大小: {file_size} bytes")
        
    except Exception as e:
        print(f"❌ 截图失败: {str(e)}")
        
        # 提供诊断信息
        print("\n🔧 诊断建议:")
        print("1. 检查XPath是否在移动端存在")
        print("2. 增加等待时间")
        print("3. 检查页面是否需要登录")
        print("4. 尝试桌面端是否正常")
        
        # 尝试简化测试：只访问页面不截取元素
        try:
            print("\n🧪 尝试简化测试：只访问页面...")
            simple_output = "screenshots/test_mobile_simple.png"
            capturer_simple = ScreenshotCapture(browser='chrome', headless=True, language='en-US')
            simple_result = capturer_simple.capture_url(
                url=url,
                output_path=simple_output,
                device=device,
                wait_time=5,
                full_page=False
            )
            print(f"✅ 简单页面截图成功: {simple_result}")
        except Exception as simple_e:
            print(f"❌ 简单页面截图也失败: {str(simple_e)}")
            
            # 尝试桌面端
            try:
                print("\n🖥️  尝试桌面端...")
                desktop_output = "screenshots/test_desktop_simple.png"
                capturer_desktop = ScreenshotCapture(browser='chrome', headless=True, language='en-US')
                desktop_result = capturer_desktop.capture_url(
                    url=url,
                    output_path=desktop_output,
                    device='desktop',
                    wait_time=5,
                    full_page=False
                )
                print(f"✅ 桌面端截图成功: {desktop_result}")
            except Exception as desktop_e:
                print(f"❌ 桌面端截图也失败: {str(desktop_e)}")

if __name__ == "__main__":
    test_mobile_screenshot() 