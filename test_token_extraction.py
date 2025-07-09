#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试文档token提取功能
Test document token extraction functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 为了避免相对导入问题，我们直接导入所需的类
from src.feishu.client import FeishuClient

def test_token_extraction():
    """测试token提取功能"""
    client = FeishuClient()
    
    print("📄 测试文档token提取功能")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        # 有效的链接格式
        {
            "input": "https://company.feishu.cn/docx/ZzVudkYQqobhj7xn19GcZ3LFnwd",
            "expected": "success",
            "description": "完整飞书文档链接"
        },
        # 有效的token
        {
            "input": "ZzVudkYQqobhj7xn19GcZ3LFnwd",
            "expected": "success", 
            "description": "直接文档token"
        },
        # 有效的超链接对象格式
        {
            "input": {"text": "AI日历", "link": "https://company.feishu.cn/docx/ZzVudkYQqobhj7xn19GcZ3LFnwd"},
            "expected": "success",
            "description": "超链接对象格式"
        },
        # 应该失败的测试用例（之前会尝试搜索）
        {
            "input": "AI 日历",
            "expected": "error",
            "description": "文档标题（应该失败，不再搜索）"
        },
        # 缺少link字段的超链接对象
        {
            "input": {"text": "AI日历"},
            "expected": "error", 
            "description": "超链接对象缺少link字段（应该失败）"
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. 测试: {test_case['description']}")
        print(f"   输入: {test_case['input']}")
        
        try:
            result = client.extract_document_token(test_case['input'])
            if test_case['expected'] == "success":
                print(f"   ✅ 成功提取token: {result}")
            else:
                print(f"   ❌ 预期失败但成功了: {result}")
        except Exception as e:
            if test_case['expected'] == "error":
                print(f"   ✅ 预期失败: {str(e)}")
            else:
                print(f"   ❌ 预期成功但失败了: {str(e)}")

if __name__ == "__main__":
    test_token_extraction() 