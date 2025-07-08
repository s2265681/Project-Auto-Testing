"""
配置管理模块
Configuration management module
"""
import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置类 Configuration class"""
    
    # 飞书配置 Feishu configuration
    FEISHU_APP_ID: str = os.getenv('FEISHU_APP_ID', '')
    FEISHU_APP_SECRET: str = os.getenv('FEISHU_APP_SECRET', '')
    FEISHU_VERIFICATION_TOKEN: str = os.getenv('FEISHU_VERIFICATION_TOKEN', '')
    
    # Gemini AI配置 Gemini AI configuration
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    
    # Figma配置 Figma configuration
    FIGMA_ACCESS_TOKEN: str = os.getenv('FIGMA_ACCESS_TOKEN', '')
    
    # 测试配置 Test configuration
    TEST_MODE: str = os.getenv('TEST_MODE', 'development')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # 报告配置 Report configuration
    REPORT_OUTPUT_DIR: str = os.getenv('REPORT_OUTPUT_DIR', './reports')
    SCREENSHOT_DIR: str = os.getenv('SCREENSHOT_DIR', './screenshots')
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        验证配置是否完整
        Validate if configuration is complete
        """
        required_configs = [
            ('FEISHU_APP_ID', cls.FEISHU_APP_ID),
            ('FEISHU_APP_SECRET', cls.FEISHU_APP_SECRET),
            ('GEMINI_API_KEY', cls.GEMINI_API_KEY),
            ('FIGMA_ACCESS_TOKEN', cls.FIGMA_ACCESS_TOKEN),
        ]
        
        missing_configs = []
        for name, value in required_configs:
            if not value:
                missing_configs.append(name)
        
        if missing_configs:
            print(f"缺少必要的配置项: {', '.join(missing_configs)}")
            print("Missing required configurations:", ', '.join(missing_configs))
            return False
        
        return True
    
    @classmethod
    def get_feishu_config(cls) -> dict:
        """获取飞书配置 Get Feishu configuration"""
        return {
            'app_id': cls.FEISHU_APP_ID,
            'app_secret': cls.FEISHU_APP_SECRET,
            'verification_token': cls.FEISHU_VERIFICATION_TOKEN,
        }
    
    @classmethod
    def get_gemini_config(cls) -> dict:
        """获取Gemini配置 Get Gemini configuration"""
        return {
            'api_key': cls.GEMINI_API_KEY,
        }
    
    @classmethod
    def get_figma_config(cls) -> dict:
        """获取Figma配置 Get Figma configuration"""
        return {
            'access_token': cls.FIGMA_ACCESS_TOKEN,
        } 