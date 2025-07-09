#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
页面结构分析工具
Page Structure Analysis Tool
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.screenshot.capture import ScreenshotCapture
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json

def analyze_page_structure():
    """分析页面结构，比较移动端和桌面端的差异"""
    print("🔍 页面结构分析")
    print("=" * 60)
    
    url = "https://www.kalodata.com/settings"
    target_xpath = "/html/body/div/div/div/div[2]/div/div/div[2]/div[2]"
    
    print(f"分析URL: {url}")
    print(f"目标XPath: {target_xpath}")
    print("-" * 60)
    
    # 分析桌面端和移动端
    devices = ['desktop', 'mobile']
    results = {}
    
    for device in devices:
        print(f"\n📱 分析{device}端...")
        
        try:
            capturer = ScreenshotCapture(browser='chrome', headless=True, language='en-US')
            device_size = capturer.DEVICE_SIZES.get(device, capturer.DEVICE_SIZES['desktop'])
            capturer._setup_driver(device_size, device_type=device)
            
            # 访问页面
            capturer.driver.get(url)
            capturer._set_language()
            
            # 等待页面加载
            WebDriverWait(capturer.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            capturer._wait_for_page_fully_loaded()
            
            # 分析页面结构
            analysis = {
                'device': device,
                'page_title': capturer.driver.title,
                'viewport_size': capturer.driver.get_window_size(),
                'body_structure': None,
                'xpath_exists': False,
                'xpath_elements': [],
                'similar_paths': []
            }
            
            # 获取body下的结构
            try:
                body_divs = capturer.driver.find_elements(By.XPATH, "//body/div")
                analysis['body_structure'] = f"{len(body_divs)} div(s) under body"
                
                # 尝试查找目标XPath
                try:
                    target_elements = capturer.driver.find_elements(By.XPATH, target_xpath)
                    if target_elements:
                        analysis['xpath_exists'] = True
                        analysis['xpath_elements'] = len(target_elements)
                        print(f"   ✅ 目标XPath存在，找到{len(target_elements)}个元素")
                    else:
                        print(f"   ❌ 目标XPath不存在")
                        
                        # 尝试查找相似的路径
                        print("   🔍 查找相似路径...")
                        
                        # 逐步简化XPath查找
                        simplified_paths = [
                            "//body/div",
                            "//body/div/div", 
                            "//body/div/div/div",
                            "//body/div/div/div/div[2]",
                            "//body/div/div/div/div[2]/div",
                            "//body/div/div/div/div[2]/div/div",
                            "//body/div/div/div/div[2]/div/div/div[2]"
                        ]
                        
                        for path in simplified_paths:
                            try:
                                elements = capturer.driver.find_elements(By.XPATH, path)
                                if elements:
                                    analysis['similar_paths'].append({
                                        'xpath': path,
                                        'count': len(elements),
                                        'texts': [elem.text[:50] for elem in elements[:3]]  # 前3个元素的文本
                                    })
                                    print(f"     - {path}: {len(elements)}个元素")
                            except Exception:
                                pass
                                
                except Exception as e:
                    print(f"   ❌ XPath查找出错: {str(e)[:100]}")
                    
            except Exception as e:
                print(f"   ❌ 页面结构分析失败: {str(e)[:100]}")
            
            results[device] = analysis
            
            # 截图保存当前页面
            try:
                screenshot_path = f"screenshots/structure_analysis_{device}.png"
                capturer.driver.save_screenshot(screenshot_path)
                print(f"   📸 页面截图保存: {screenshot_path}")
            except Exception:
                pass
                
            capturer.driver.quit()
            
        except Exception as e:
            print(f"   ❌ {device}端分析失败: {str(e)[:100]}")
            results[device] = {'error': str(e)}
    
    # 总结分析结果
    print("\n" + "=" * 60)
    print("📊 分析结果总结")
    print("=" * 60)
    
    for device, data in results.items():
        if 'error' in data:
            print(f"\n{device}端: ❌ 分析失败 - {data['error']}")
            continue
            
        print(f"\n{device}端:")
        print(f"  页面标题: {data['page_title']}")
        print(f"  视口大小: {data['viewport_size']}")
        print(f"  Body结构: {data['body_structure']}")
        print(f"  目标XPath存在: {'✅ 是' if data['xpath_exists'] else '❌ 否'}")
        
        if data['similar_paths']:
            print(f"  相似路径 ({len(data['similar_paths'])}个):")
            for path_info in data['similar_paths']:
                print(f"    - {path_info['xpath']}: {path_info['count']}个元素")
    
    # 给出建议
    print("\n" + "=" * 60)
    print("💡 建议和解决方案")
    print("=" * 60)
    
    desktop_xpath_exists = results.get('desktop', {}).get('xpath_exists', False)
    mobile_xpath_exists = results.get('mobile', {}).get('xpath_exists', False)
    
    if desktop_xpath_exists and not mobile_xpath_exists:
        print("🔧 问题：XPath在桌面端存在但在移动端不存在")
        print("解决方案：")
        print("1. 使用响应式的CSS选择器而不是绝对XPath")
        print("2. 为移动端和桌面端使用不同的选择器")
        print("3. 使用更灵活的相对XPath")
        
        # 建议替代选择器
        mobile_paths = results.get('mobile', {}).get('similar_paths', [])
        if mobile_paths:
            print("\n建议的移动端XPath:")
            for path_info in mobile_paths[-3:]:  # 显示最后几个（更具体的）路径
                print(f"  - {path_info['xpath']}")
                
    elif not desktop_xpath_exists and not mobile_xpath_exists:
        print("🔧 问题：XPath在桌面端和移动端都不存在")
        print("解决方案：")
        print("1. 检查页面是否需要登录")
        print("2. 确认XPath路径是否正确")
        print("3. 页面可能有动态加载内容，需要增加等待时间")
        
    else:
        print("✅ XPath在两端都存在，可能是其他问题导致崩溃")
    
    # 保存详细结果
    with open('screenshots/structure_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n📄 详细分析结果保存: screenshots/structure_analysis.json")

if __name__ == "__main__":
    analyze_page_structure() 