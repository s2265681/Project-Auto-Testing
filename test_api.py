#!/usr/bin/env python3
"""
API测试脚本
API Testing Script
"""
import requests
import json
import time
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config.environment import get_api_base_url
except ImportError:
    # 如果环境配置不可用，则使用默认值
    def get_api_base_url():
        return "http://localhost:5001"

class APITester:
    def __init__(self, base_url=None):
        # 如果没有指定base_url，则从环境配置获取
        if base_url is None:
            base_url = get_api_base_url()
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'API-Tester/1.0'
        })

    def test_health(self):
        """测试健康检查端点"""
        print("🩺 测试健康检查...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 健康检查成功: {data.get('service')}")
                print(f"   时间戳: {data.get('timestamp')}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False

    def test_generate_test_cases(self, doc_token="ZzVudkYQqobhj7xn19GcZ3LFnwd"):
        """测试测试用例生成"""
        print("📝 测试测试用例生成...")
        try:
            payload = {
                "docToken": doc_token
            }
            
            response = self.session.post(
                f"{self.base_url}/api/generate-test-cases",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ 测试用例生成成功")
                    print(f"   文档Token: {data['data'].get('document_token')}")
                    print(f"   API状态: {data['data'].get('api_status')}")
                    print(f"   PRD长度: {data['data'].get('prd_text_length')} 字符")
                    return True
                else:
                    print(f"❌ 测试用例生成失败: {data.get('error')}")
                    return False
            else:
                print(f"❌ 请求失败: {response.status_code}")
                if response.text:
                    print(f"   响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 测试用例生成异常: {e}")
            return False

    def test_visual_comparison(self, 
                             figma_url="https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/25%E5%85%A8%E5%B1%80%E8%BF%AD%E4%BB%A3?node-id=6862-67131&m=dev",
                             web_url="https://www.kalodata.com/product"):
        """测试视觉比较"""
        print("👁️  测试视觉比较...")
        try:
            payload = {
                "figmaUrl": figma_url,
                "webUrl": web_url,
                "device": "desktop",
                "websiteClasses": "ant-input-affix-wrapper css-2yep4o ant-input-outlined w-[599px]"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/execute-comparison",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ 视觉比较成功")
                    print(f"   相似度: {data['data'].get('similarity_score', 0):.3f}")
                    print(f"   输出目录: {data['data'].get('output_directory')}")
                    return True
                else:
                    print(f"❌ 视觉比较失败: {data.get('error')}")
                    return False
            else:
                print(f"❌ 请求失败: {response.status_code}")
                if response.text:
                    print(f"   响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 视觉比较异常: {e}")
            return False

    def test_full_workflow(self,
                          doc_token="ZzVudkYQqobhj7xn19GcZ3LFnwd",
                          figma_url="https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/25%E5%85%A8%E5%B1%80%E8%BF%AD%E4%BB%A3?node-id=6862-67131&m=dev",
                          web_url="https://www.kalodata.com/product",
                          app_token="GzpBblAM5aoH18sHNt0cpDYXnYf",
                          table_id="tblsLP3GVnzFobjP",
                          record_id="receLUWNBZ"):
        """测试完整工作流"""
        print("🔄 测试完整工作流...")
        try:
            payload = {
                "docToken": doc_token,
                "figmaUrl": figma_url,
                "webUrl": web_url,
                "appToken": app_token,
                "tableId": table_id,
                "recordId": record_id,
                "device": "desktop",
                "websiteClasses": "ant-input-affix-wrapper css-2yep4o ant-input-outlined w-[599px]"
            }
            
            print("⏳ 发送请求，请稍候...")
            response = self.session.post(
                f"{self.base_url}/api/execute-workflow",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ 完整工作流执行成功")
                    print(f"   执行ID: {data['data'].get('execution_id')}")
                    print(f"   测试用例生成: {'成功' if data['data'].get('test_cases_generated') else '失败'}")
                    print(f"   相似度: {data['data']['comparison_result'].get('similarity_score', 0):.3f}")
                    print(f"   完成时间: {data['data'].get('completed_at')}")
                    return True
                else:
                    print(f"❌ 完整工作流失败: {data.get('error')}")
                    return False
            else:
                print(f"❌ 请求失败: {response.status_code}")
                if response.text:
                    print(f"   响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 完整工作流异常: {e}")
            return False

    def test_error_handling(self):
        """测试错误处理"""
        print("⚠️  测试错误处理...")
        
        # 测试缺少参数
        try:
            response = self.session.post(
                f"{self.base_url}/api/execute-workflow",
                json={}
            )
            
            if response.status_code == 400:
                data = response.json()
                if not data.get('success') and '缺少必需参数' in data.get('error', ''):
                    print("✅ 参数验证错误处理正常")
                    return True
            
            print("❌ 错误处理异常")
            return False
            
        except Exception as e:
            print(f"❌ 错误处理测试异常: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🧪 API 功能测试开始")
        print("=" * 60)
        print(f"🌐 目标服务器: {self.base_url}")
        print()
        
        results = []
        
        # 1. 健康检查
        results.append(("健康检查", self.test_health()))
        
        # 2. 错误处理
        results.append(("错误处理", self.test_error_handling()))
        
        # 3. 测试用例生成
        results.append(("测试用例生成", self.test_generate_test_cases()))
        
        # 4. 视觉比较
        results.append(("视觉比较", self.test_visual_comparison()))
        
        # 5. 完整工作流（可选，因为比较耗时）
        run_full_test = input("\n是否运行完整工作流测试？(y/n): ").lower().strip()
        if run_full_test in ['y', 'yes', '是']:
            results.append(("完整工作流", self.test_full_workflow()))
        
        # 结果汇总
        print("\n" + "=" * 60)
        print("📊 测试结果汇总")
        print("=" * 60)
        
        passed = 0
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:<15} {status}")
            if result:
                passed += 1
        
        print(f"\n总计: {passed}/{len(results)} 个测试通过")
        
        if passed == len(results):
            print("🎉 所有测试通过！API服务器工作正常。")
            return True
        else:
            print("⚠️  有测试失败，请检查服务器配置。")
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='API功能测试脚本')
    default_url = get_api_base_url()
    parser.add_argument('--url', default=default_url, 
                       help=f'API服务器地址 (默认: {default_url})')
    parser.add_argument('--test', choices=['health', 'test-cases', 'comparison', 'workflow', 'all'],
                       default='all', help='要运行的测试类型')
    
    args = parser.parse_args()
    
    tester = APITester(args.url)
    
    if args.test == 'health':
        return tester.test_health()
    elif args.test == 'test-cases':
        return tester.test_generate_test_cases()
    elif args.test == 'comparison':
        return tester.test_visual_comparison()
    elif args.test == 'workflow':
        return tester.test_full_workflow()
    else:
        return tester.run_all_tests()

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生未处理的异常: {e}")
        sys.exit(1) 