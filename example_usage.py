#!/usr/bin/env python3
"""
网页与Figma设计稿比对使用示例
Example usage of website vs Figma design comparison
"""

def main():
    """使用示例"""
    print("🔍 网页与Figma设计稿比对工具使用示例")
    print("=" * 50)
    
    print("\n📋 使用方法:")
    print("python main.py compare-web-figma --website-url <网页URL> --figma-url <Figma设计稿URL>")
    
    print("\n🌐 示例命令:")
    print("python main.py compare-web-figma \\")
    print("    --website-url 'https://example.com' \\")
    print("    --figma-url 'https://www.figma.com/file/ABC123/Design?node-id=1%3A2' \\")
    print("    --device desktop \\")
    print("    --output-dir reports \\")
    print("    --wait-time 5")
    
    print("\n📱 支持的设备类型:")
    devices = {
        'desktop': '桌面端 (1920x1080)',
        'laptop': '笔记本 (1366x768)', 
        'tablet': '平板 (768x1024)',
        'mobile': '手机 (375x667)',
        'iphone': 'iPhone (414x896)',
        'android': 'Android (360x640)'
    }
    
    for device, description in devices.items():
        print(f"  • {device}: {description}")
    
    print("\n🔧 配置要求:")
    print("请确保在.env文件中配置以下信息:")
    print("  • FIGMA_ACCESS_TOKEN - Figma访问令牌")
    print("  • 其他必要的API密钥")
    
    print("\n📊 输出结果:")
    print("工具会生成以下文件:")
    print("  • 网页截图 (website_<device>.png)")
    print("  • Figma设计稿 (figma_design.png)")
    print("  • 差异对比图 (diff_comparison_*.png)")
    print("  • 详细报告 (comparison_report.json)")
    
    print("\n📈 比对指标:")
    print("  • 相似度分数: 基于直方图的相似度 (0-1)")
    print("  • 结构相似性 (SSIM): 结构相似性指数 (0-1)")
    print("  • 均方误差 (MSE): 像素差异的均方误差")
    print("  • 哈希距离: 感知哈希距离")
    print("  • 差异区域数: 检测到的不同区域数量")
    
    print("\n💡 使用技巧:")
    print("  • 确保网页已完全加载（调整wait-time参数）")
    print("  • 选择合适的设备类型进行比对")
    print("  • Figma URL需要包含具体的节点ID")
    print("  • 首次使用建议先运行 'python main.py check-config' 检查配置")
    
    print("\n🚀 快速开始:")
    print("1. 复制 env.example 到 .env")
    print("2. 在 .env 中填入 FIGMA_ACCESS_TOKEN")
    print("3. 运行: python main.py check-config")
    print("4. 测试Figma URL: python main.py test-figma-url --figma-url <你的Figma URL>")
    print("5. 运行比对命令")
    
    print("\n🔧 常用命令:")
    print("# 检查配置")
    print("python main.py check-config")
    print()
    print("# 测试Figma URL")
    print("python main.py test-figma-url --figma-url 'https://www.figma.com/file/ABC/Design'")
    print()
    print("# 运行比对")
    print("python main.py compare-web-figma --website-url 'https://example.com' --figma-url 'https://www.figma.com/file/ABC/Design'")

if __name__ == "__main__":
    main() 