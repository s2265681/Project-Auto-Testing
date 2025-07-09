#!/usr/bin/env python3
"""
本地视觉比较测试
Local Visual Comparison Test
"""

import os
import sys
import time
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.workflow.executor import WorkflowExecutor
from src.utils.logger import get_logger
from src.utils.config import Config

logger = get_logger(__name__)

def test_visual_comparison():
    """测试视觉比较功能"""
    print("=" * 60)
    print("🔍 开始本地视觉比较测试")
    print("=" * 60)
    
    # 用户提供的参数
    figma_url = "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/25%E5%85%A8%E5%B1%80%E8%BF%AD%E4%BB%A3?node-id=6862-67131&m=dev"
    website_url = "https://www.kalodata.com/product"
    xpath_selector = "/html/body/div[1]/div/div[2]/div[1]/div/div[4]/div[2]/div/div[1]/div[2]/div[1]/div[1]/div/div/span"
    device = "desktop"
    
    print(f"📋 测试参数:")
    print(f"   Figma URL: {figma_url}")
    print(f"   Website URL: {website_url}")
    print(f"   XPath: {xpath_selector}")
    print(f"   Device: {device}")
    print()
    
    # 验证配置
    print("🔧 验证配置...")
    if not Config.validate_config():
        print("❌ 配置验证失败，请检查.env文件")
        return False
    print("✅ 配置验证通过")
    
    # 创建工作流执行器
    print("🚀 初始化工作流执行器...")
    try:
        executor = WorkflowExecutor()
        print("✅ 工作流执行器初始化成功")
    except Exception as e:
        print(f"❌ 工作流执行器初始化失败: {e}")
        return False
    
    # 执行视觉比较
    print("\n🎯 开始执行视觉比较...")
    start_time = time.time()
    
    try:
        result = executor._compare_figma_and_website(
            figma_url=figma_url,
            website_url=website_url,
            xpath_selector=xpath_selector,
            device=device,
            output_dir="local_test_reports"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n🎉 视觉比较完成！耗时: {duration:.2f}秒")
        
        # 显示结果
        print("\n📊 比较结果:")
        print(f"   相似度分数: {result.get('comparison_result', {}).get('similarity_score', 0):.3f}")
        print(f"   SSIM分数: {result.get('comparison_result', {}).get('ssim_score', 0):.3f}")
        print(f"   MSE分数: {result.get('comparison_result', {}).get('mse_score', 0):.3f}")
        print(f"   哈希距离: {result.get('comparison_result', {}).get('hash_distance', 0)}")
        print(f"   差异区域数: {result.get('comparison_result', {}).get('differences_count', 0)}")
        
        # 显示文件路径
        print(f"\n📁 生成的文件:")
        print(f"   输出目录: {result.get('output_directory')}")
        print(f"   网站截图: {result.get('website_screenshot')}")
        print(f"   Figma截图: {result.get('figma_screenshot')}")
        print(f"   差异图像: {result.get('comparison_result', {}).get('diff_image_path')}")
        print(f"   报告文件: {result.get('report_path')}")
        
        # 验证文件是否存在
        print(f"\n✅ 文件验证:")
        files_to_check = [
            ("网站截图", result.get('website_screenshot')),
            ("Figma截图", result.get('figma_screenshot')),
            ("差异图像", result.get('comparison_result', {}).get('diff_image_path')),
            ("报告文件", result.get('report_path'))
        ]
        
        for name, path in files_to_check:
            if path and os.path.exists(path):
                size = os.path.getsize(path)
                print(f"   ✅ {name}: {path} ({size} bytes)")
            else:
                print(f"   ❌ {name}: 文件不存在 - {path}")
        
        return True
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"\n❌ 视觉比较失败！耗时: {duration:.2f}秒")
        print(f"   错误信息: {e}")
        logger.error(f"视觉比较失败: {e}", exc_info=True)
        return False

def main():
    """主函数"""
    print(f"🕐 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_visual_comparison()
    
    print(f"\n🕐 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        print("\n🎉 本地测试完成！")
        print("💡 如果本地测试成功，您可以部署到服务器进行进一步测试。")
    else:
        print("\n💥 本地测试失败！")
        print("💡 请检查错误信息并修复后重试。")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 