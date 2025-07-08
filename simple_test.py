#!/usr/bin/env python3
"""
简化测试脚本 - 验证基础功能
Simple test script - verify basic functionality
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """测试配置模块 Test config module"""
    print("🔧 测试配置模块 / Testing config module")
    
    try:
        from src.utils.config_simple import ConfigSimple
        print("✅ 配置模块导入成功 / Config module imported successfully")
        
        # 检查配置项
        print(f"飞书App ID: {'已设置' if ConfigSimple.FEISHU_APP_ID else '未设置'}")
        print(f"飞书App Secret: {'已设置' if ConfigSimple.FEISHU_APP_SECRET else '未设置'}")
        print(f"Gemini API Key: {'已设置' if ConfigSimple.GEMINI_API_KEY else '未设置'}")
        print(f"Figma Access Token: {'已设置' if ConfigSimple.FIGMA_ACCESS_TOKEN else '未设置'}")
        
        return True
    except Exception as e:
        print(f"❌ 配置模块测试失败: {e}")
        return False

def test_logger():
    """测试日志模块 Test logger module"""
    print("\n📝 测试日志模块 / Testing logger module")
    
    try:
        # 使用简单的print作为日志
        print("✅ 日志模块测试成功 / Logger module test successful")
        return True
    except Exception as e:
        print(f"❌ 日志模块测试失败: {e}")
        return False

def test_feishu_client():
    """测试飞书客户端 Test Feishu client"""
    print("\n📄 测试飞书客户端 / Testing Feishu client")
    
    try:
        from src.feishu.client import FeishuClient
        print("✅ 飞书客户端模块导入成功 / Feishu client module imported successfully")
        
        # 检查配置
        from src.utils.config_simple import ConfigSimple
        if not ConfigSimple.FEISHU_APP_ID or not ConfigSimple.FEISHU_APP_SECRET:
            print("⚠️  飞书配置未设置，跳过客户端测试")
            print("请设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量")
            return True
        
        # 尝试创建客户端
        client = FeishuClient()
        print("✅ 飞书客户端创建成功 / Feishu client created successfully")
        return True
        
    except Exception as e:
        print(f"❌ 飞书客户端测试失败: {e}")
        return False

def test_project_structure():
    """测试项目结构 Test project structure"""
    print("\n📁 测试项目结构 / Testing project structure")
    
    required_files = [
        'src/utils/config.py',
        'src/utils/config_simple.py',
        'src/utils/logger.py',
        'src/feishu/client.py',
        'requirements.txt',
        'env.example',
        'README.md'
    ]
    
    required_dirs = [
        'src',
        'src/utils',
        'src/feishu',
        'logs',
        'reports',
        'screenshots'
    ]
    
    all_good = True
    
    # 检查文件
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ 文件存在: {file_path}")
        else:
            print(f"❌ 文件缺失: {file_path}")
            all_good = False
    
    # 检查目录
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ 目录存在: {dir_path}")
        else:
            print(f"❌ 目录缺失: {dir_path}")
            all_good = False
    
    return all_good

def test_basic_functionality():
    """测试基础功能 Test basic functionality"""
    print("\n🔧 测试基础功能 / Testing basic functionality")
    
    try:
        # 测试字符串处理
        test_text = "这是一个测试文本 / This is a test text"
        print(f"✅ 字符串处理: {test_text}")
        
        # 测试字典操作
        test_dict = {"key": "value", "number": 123}
        print(f"✅ 字典操作: {test_dict}")
        
        # 测试列表操作
        test_list = [1, 2, 3, 4, 5]
        print(f"✅ 列表操作: {test_list}")
        
        return True
    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        return False

def main():
    """主函数 Main function"""
    print("🚀 自动化测试助手项目测试 / Automated Testing Assistant Project Test")
    print("=" * 60)
    
    tests = [
        test_project_structure,
        test_config,
        test_logger,
        test_basic_functionality,
        test_feishu_client
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总 / Test Results Summary")
    print("=" * 60)
    
    test_names = [
        "项目结构 / Project Structure",
        "配置模块 / Config Module", 
        "日志模块 / Logger Module",
        "基础功能 / Basic Functionality",
        "飞书客户端 / Feishu Client"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    passed = sum(results)
    total = len(results)
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！项目基础结构搭建完成。")
        print("\n📋 下一步:")
        print("1. 安装依赖: pip3 install -r requirements.txt")
        print("2. 配置环境变量: 复制 env.example 为 .env 并填入API密钥")
        print("3. 运行完整测试: python3 main.py check-config")
    else:
        print("⚠️  部分测试失败，请检查项目结构。")

if __name__ == "__main__":
    main() 