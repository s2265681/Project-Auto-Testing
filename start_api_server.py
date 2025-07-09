#!/usr/bin/env python3
"""
API服务器启动脚本
API Server Startup Script
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def check_environment():
    """检查环境和依赖"""
    print("🔍 检查环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version < (3, 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查必要的环境变量
    required_env_vars = [
        'FEISHU_APP_ID',
        'FEISHU_APP_SECRET',
        'FIGMA_ACCESS_TOKEN',
        'GEMINI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  缺少环境变量: {', '.join(missing_vars)}")
        print("请检查 .env 文件或设置环境变量")
        return False
    
    print("✅ 环境变量检查完成")
    
    # 检查日志目录
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    print("✅ 日志目录准备完成")
    
    return True

def install_dependencies():
    """安装依赖"""
    print("📦 安装依赖...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError:
        print("❌ 依赖安装失败")
        return False

def start_server(host='0.0.0.0', port=5001, debug=False):
    """启动API服务器"""
    print(f"🚀 启动API服务器...")
    print(f"📍 地址: http://{host}:{port}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    
    # 设置环境变量
    os.environ['API_HOST'] = host
    os.environ['API_PORT'] = str(port)
    os.environ['API_DEBUG'] = str(debug).lower()
    
    try:
        # 导入并运行服务器
        from api_server import app
        app.run(host=host, port=port, debug=debug)
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🌟 飞书自动化测试API服务器 🌟")
    print("=" * 60)
    
    # 检查环境
    if not check_environment():
        print("❌ 环境检查失败，请修复后重试")
        sys.exit(1)
    
    # 询问是否安装依赖
    install_deps = input("是否安装/更新依赖？(y/n): ").lower().strip()
    if install_deps in ['y', 'yes', '是']:
        if not install_dependencies():
            print("❌ 依赖安装失败")
            sys.exit(1)
    
    # 获取启动参数
    host = input("输入监听地址 (默认: 0.0.0.0): ").strip() or '0.0.0.0'
    port = input("输入监听端口 (默认: 5001): ").strip() or '5001'
    debug = input("是否启用调试模式？(y/n): ").lower().strip() in ['y', 'yes', '是']
    
    try:
        port = int(port)
    except ValueError:
        print("❌ 无效的端口号")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🚀 正在启动服务器...")
    print("=" * 60)
    
    # 启动服务器
    start_server(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main() 