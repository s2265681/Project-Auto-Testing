#!/usr/bin/env python3
"""
飞书PRD解析模块测试脚本
Test script for Feishu PRD parsing module
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.feishu.client import FeishuClient
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

def test_feishu_client():
    """测试飞书客户端 Test Feishu client"""
    try:
        # 验证配置
        if not Config.validate_config():
            logger.error("配置验证失败，请检查环境变量")
            return False
        
        # 创建飞书客户端
        client = FeishuClient()
        logger.info("飞书客户端创建成功")
        
        # 测试获取访问令牌
        access_token = client.get_access_token()
        logger.info(f"访问令牌获取成功: {access_token[:20]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False

def test_document_parsing(document_token: str):
    """测试文档解析 Test document parsing"""
    try:
        client = FeishuClient()
        
        # 解析PRD文档
        result = client.parse_prd_document(document_token)
        
        logger.info("文档解析结果:")
        logger.info(f"文档标题: {result['title']}")
        logger.info(f"文本长度: {len(result['text_content'])} 字符")
        logger.info(f"块数量: {result['blocks_count']}")
        logger.info(f"标题数量: {len(result['structure']['headings'])}")
        logger.info(f"表格数量: {len(result['structure']['tables'])}")
        logger.info(f"列表数量: {len(result['structure']['lists'])}")
        
        # 显示前500个字符的文本内容
        preview = result['text_content'][:500]
        logger.info(f"文本预览: {preview}...")
        
        return result
        
    except Exception as e:
        logger.error(f"文档解析测试失败: {e}")
        return None

def main():
    """主函数 Main function"""
    logger.info("开始飞书PRD解析模块测试")
    
    # 测试客户端创建
    if not test_feishu_client():
        logger.error("客户端测试失败")
        return
    
    # 如果有文档token，测试文档解析
    import sys
    if len(sys.argv) > 1:
        document_token = sys.argv[1]
        logger.info(f"测试文档解析: {document_token}")
        result = test_document_parsing(document_token)
        if result:
            logger.info("文档解析测试成功")
        else:
            logger.error("文档解析测试失败")
    else:
        logger.info("未提供文档token，跳过文档解析测试")
        logger.info("使用方法: python test_feishu.py <document_token>")
    
    logger.info("测试完成")

if __name__ == "__main__":
    main() 