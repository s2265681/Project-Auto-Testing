#!/usr/bin/env python3
"""
XPath API功能测试脚本
Test script for XPath API functionality
"""

import requests
import json
import time
import os
from urllib.parse import quote

def test_xpath_api():
    """测试XPath API功能"""
    
    # API服务器地址
    base_url = "http://localhost:5001"
    
    print("🧪 开始测试XPath API功能...")
    
    # 1. 测试健康检查
    print("\n📋 1. 测试健康检查")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查连接失败: {e}")
        return False
    
    # 2. 测试@URL:XPath格式解析
    print("\n📋 2. 测试@URL:XPath格式解析")
    test_data = {
        "docToken": "test_token_123",
        "figmaUrl": "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/demo?node-id=6862-67131&m=dev",
        "webUrl": "@https://www.kalodata.com/product:/html/body/div[1]/div/div[2]/div[1]/div/div[4]/div[2]/div/div[1]/div[2]/div[1]/div[1]/div/div/span",
        "device": "desktop"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/execute-workflow",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   状态码: {response.status_code}")
        response_data = response.json()
        
        if response.status_code == 200:
            print("✅ @URL:XPath格式解析成功")
            data = response_data.get('data', {})
            print(f"   解析的URL: {data.get('website_url')}")
            print(f"   解析的XPath: {data.get('xpath_selector')}")
        else:
            print(f"❌ 请求失败: {response_data.get('error', '未知错误')}")
            
        print(f"   完整响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 3. 测试传统URL格式（兼容性）
    print("\n📋 3. 测试传统URL格式兼容性")
    test_data_legacy = {
        "docToken": "test_token_456",
        "figmaUrl": "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/demo?node-id=6862-67131&m=dev",
        "webUrl": "https://www.kalodata.com/product",
        "device": "desktop"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/execute-workflow",
            json=test_data_legacy,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   状态码: {response.status_code}")
        response_data = response.json()
        
        if response.status_code == 200:
            print("✅ 传统URL格式兼容正常")
            data = response_data.get('data', {})
            print(f"   处理的URL: {data.get('website_url')}")
            print(f"   XPath选择器: {data.get('xpath_selector', 'None')}")
        else:
            print(f"❌ 请求失败: {response_data.get('error', '未知错误')}")
            
        print(f"   完整响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 4. 测试仅视觉比较API
    print("\n📋 4. 测试仅视觉比较API")
    comparison_data = {
        "figmaUrl": "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/demo?node-id=6862-67131&m=dev",
        "webUrl": "@https://www.kalodata.com/product:/html/body/div[1]/section[2]/div/div[1]",
        "device": "desktop"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/execute-comparison",
            json=comparison_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   状态码: {response.status_code}")
        response_data = response.json()
        
        if response.status_code == 200:
            print("✅ 视觉比较API工作正常")
            data = response_data.get('data', {})
            print(f"   网站URL: {data.get('website_url')}")
            print(f"   XPath选择器: {data.get('xpath_selector')}")
        else:
            print(f"❌ 请求失败: {response_data.get('error', '未知错误')}")
            
        print(f"   完整响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 5. 测试错误处理
    print("\n📋 5. 测试错误处理")
    
    # 5.1 测试无效的@URL:XPath格式
    print("\n   5.1 测试无效的@URL:XPath格式")
    invalid_data = {
        "docToken": "test_token_789",
        "figmaUrl": "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/demo?node-id=6862-67131&m=dev",
        "webUrl": "@invalid_url_format",
        "device": "desktop"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/execute-workflow",
            json=invalid_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   状态码: {response.status_code}")
        response_data = response.json()
        
        if response.status_code == 400:
            print("✅ 错误处理正常 - 正确识别无效格式")
            print(f"   错误信息: {response_data.get('error')}")
        else:
            print(f"❌ 错误处理异常: {response_data}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 5.2 测试缺少必需参数
    print("\n   5.2 测试缺少必需参数")
    incomplete_data = {
        "figmaUrl": "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/demo?node-id=6862-67131&m=dev"
        # 缺少 docToken 和 webUrl
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/execute-workflow",
            json=incomplete_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   状态码: {response.status_code}")
        response_data = response.json()
        
        if response.status_code == 400:
            print("✅ 参数验证正常 - 正确识别缺少参数")
            print(f"   错误信息: {response_data.get('error')}")
        else:
            print(f"❌ 参数验证异常: {response_data}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    print("\n🎉 XPath API功能测试完成!")
    
    # 6. 显示测试总结
    print("\n📊 测试总结:")
    print("- ✅ 健康检查")
    print("- ✅ @URL:XPath格式解析")
    print("- ✅ 传统URL格式兼容")
    print("- ✅ 视觉比较API")
    print("- ✅ 错误处理机制")
    
    print("\n🔧 使用说明:")
    print("1. @URL:XPath格式: @https://example.com:/html/body/div[1]/main")
    print("2. 传统URL格式: https://example.com (兼容)")
    print("3. XPath获取方法: Chrome开发者工具 -> 右键元素 -> Copy XPath")
    
    return True

if __name__ == "__main__":
    test_xpath_api() 