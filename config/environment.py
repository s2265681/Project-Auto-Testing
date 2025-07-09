#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
环境配置模块
Environment Configuration Module
"""

import os
from typing import Dict, Any

class EnvironmentConfig:
    """环境配置类"""
    
    # 环境类型
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    
    def __init__(self):
        # 从环境变量获取当前环境，默认为development
        self.environment = os.getenv('ENVIRONMENT', self.DEVELOPMENT)
        
        # 环境配置
        self.config = {
            self.DEVELOPMENT: {
                'api_base_url': 'http://localhost:5001',
                'debug': True,
                'log_level': 'DEBUG'
            },
            self.PRODUCTION: {
                'api_base_url': 'http://18.141.179.222:5001',
                'debug': False,
                'log_level': 'INFO'
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前环境配置"""
        return self.config.get(self.environment, self.config[self.DEVELOPMENT])
    
    def get_api_base_url(self) -> str:
        """获取API基础URL"""
        return self.get_config()['api_base_url']
    
    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.environment == self.DEVELOPMENT
    
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.environment == self.PRODUCTION
    
    def get_environment(self) -> str:
        """获取当前环境名称"""
        return self.environment

# 全局环境配置实例
env_config = EnvironmentConfig()

# 便捷函数
def get_api_base_url() -> str:
    """获取API基础URL"""
    return env_config.get_api_base_url()

def is_development() -> bool:
    """判断是否为开发环境"""
    return env_config.is_development()

def is_production() -> bool:
    """判断是否为生产环境"""
    return env_config.is_production()

def get_environment() -> str:
    """获取当前环境名称"""
    return env_config.get_environment() 