#!/usr/bin/env python3
"""
获取飞书文档列表和token的脚本
Script to get Feishu document list and tokens
"""
import sys
import os
import requests
from typing import List, Dict, Any

# 自动加载.env
from dotenv import load_dotenv
load_dotenv()

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config

class FeishuDocFetcher:
    """飞书文档获取器 Feishu Document Fetcher"""
    
    def __init__(self):
        """初始化 Initialize"""
        self.config = Config.get_feishu_config()
        self.base_url = "https://open.feishu.cn/open-apis"
        self.access_token = None
        
        if not self.config['app_id'] or not self.config['app_secret']:
            raise ValueError("请先配置飞书App ID和App Secret")
    
    def get_access_token(self) -> str:
        """获取访问令牌 Get access token"""
        if self.access_token:
            return self.access_token
            
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        data = {
            "app_id": self.config['app_id'],
            "app_secret": self.config['app_secret']
        }
        
        try:
            response = requests.post(url, json=data, verify=False)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                self.access_token = result['tenant_access_token']
                print("✅ 成功获取访问令牌")
                return self.access_token
            else:
                raise Exception(f"获取访问令牌失败: {result.get('msg', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ 获取访问令牌失败: {e}")
            raise
    
    def get_document_list(self) -> List[Dict[str, Any]]:
        """获取文档列表 Get document list"""
        access_token = self.get_access_token()
        url = f"{self.base_url}/drive/v1/files"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "type": "docx",  # 只获取文档类型
            "page_size": 50
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, verify=False)
            response.raise_for_status()
            result = response.json()
            print('API原始返回:', result)
            
            if result.get('code') == 0:
                files = result['data']['files']
                print(f"✅ 成功获取 {len(files)} 个文档")
                return files
            else:
                raise Exception(f"获取文档列表失败: {result.get('msg', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ 获取文档列表失败: {e}")
            raise
    
    def display_documents(self, documents: List[Dict[str, Any]]):
        """显示文档信息 Display document information"""
        print("\n📋 文档列表 / Document List:")
        print("=" * 80)
        
        for i, doc in enumerate(documents, 1):
            print(f"{i}. 标题: {doc.get('name', 'Unknown')}")
            print(f"   Token: {doc.get('token', 'Unknown')}")
            print(f"   类型: {doc.get('type', 'Unknown')}")
            print(f"   创建时间: {doc.get('created_time', 'Unknown')}")
            print(f"   更新时间: {doc.get('updated_time', 'Unknown')}")
            print("-" * 40)
    
    def get_document_info(self, document_token: str) -> Dict[str, Any]:
        """获取文档详细信息 Get document detailed information"""
        access_token = self.get_access_token()
        url = f"{self.base_url}/docx/v1/documents/{document_token}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                return result['data']
            else:
                raise Exception(f"获取文档信息失败: {result.get('msg', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ 获取文档信息失败: {e}")
            raise

def main():
    """主函数 Main function"""
    print("🔍 飞书文档获取工具 / Feishu Document Fetcher")
    print("=" * 60)
    
    try:
        # 检查配置
        if not Config.FEISHU_APP_ID or not Config.FEISHU_APP_SECRET:
            print("❌ 请先配置飞书App ID和App Secret")
            print("请在.env文件中设置以下变量:")
            print("FEISHU_APP_ID=your_app_id")
            print("FEISHU_APP_SECRET=your_app_secret")
            return
        
        # 创建获取器
        fetcher = FeishuDocFetcher()
        
        # 获取文档列表
        documents = fetcher.get_document_list()
        
        if not documents:
            print("📝 未找到任何文档")
            return
        
        # 显示文档列表
        fetcher.display_documents(documents)
        
        # 如果有文档，显示第一个的详细信息
        if documents:
            first_doc = documents[0]
            print(f"\n📄 第一个文档详细信息 / First Document Details:")
            print("=" * 60)
            
            try:
                doc_info = fetcher.get_document_info(first_doc['token'])
                print(f"标题: {doc_info.get('title', 'Unknown')}")
                print(f"Token: {first_doc['token']}")
                print(f"创建者: {doc_info.get('owner_id', 'Unknown')}")
                print(f"权限: {doc_info.get('permission', 'Unknown')}")
                
                print(f"\n💡 使用此token测试:")
                print(f"python3 main.py test-feishu --document-token {first_doc['token']}")
                
            except Exception as e:
                print(f"获取文档详细信息失败: {e}")
        
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")

if __name__ == "__main__":
    main() 