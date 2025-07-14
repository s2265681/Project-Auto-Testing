"""
静态资源URL转换工具
Static Asset URL Converter

提供统一的静态资源URL转换功能，支持环境判断和域名切换
"""

import os
from typing import Optional
from pathlib import Path
from config.environment import env_config


class AssetUrlConverter:
    """静态资源URL转换器"""
    
    def __init__(self):
        self.env_config = env_config
        
    def convert_to_web_url(self, file_path: str, base_prefix: str = "/files") -> str:
        """
        将本地文件路径转换为web可访问的URL
        
        Args:
            file_path: 本地文件路径
            base_prefix: 基础前缀，默认为 "/files"
            
        Returns:
            web可访问的URL路径
        """
        if not file_path:
            return ""
        
        # 确保使用正斜杠
        web_path = file_path.replace('\\', '/')
        
        # 如果路径不以base_prefix开头，添加前缀
        if not web_path.startswith(base_prefix):
            if web_path.startswith('./'):
                web_path = web_path[2:]
            elif web_path.startswith('/'):
                web_path = web_path[1:]
            web_path = f"{base_prefix}/{web_path}"
        
        # 根据环境添加对应的域名
        api_base_url = self.env_config.get_api_base_url()
        return f"{api_base_url}{web_path}"
    
    def convert_image_path(self, image_path: str) -> str:
        """
        转换图像路径为web URL
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            web可访问的图像URL
        """
        return self.convert_to_web_url(image_path)
    
    def convert_screenshot_path(self, screenshot_path: str) -> str:
        """
        转换截图路径为web URL
        
        Args:
            screenshot_path: 截图文件路径
            
        Returns:
            web可访问的截图URL
        """
        return self.convert_to_web_url(screenshot_path)
    
    def convert_diff_image_path(self, diff_image_path: str) -> str:
        """
        转换差异图像路径为web URL
        
        Args:
            diff_image_path: 差异图像文件路径
            
        Returns:
            web可访问的差异图像URL
        """
        return self.convert_to_web_url(diff_image_path)
    
    def ensure_file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件是否存在
        """
        if not file_path:
            return False
        
        # 处理相对路径
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        
        return os.path.exists(file_path) and os.path.isfile(file_path)
    
    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小（字节），如果文件不存在返回None
        """
        if not self.ensure_file_exists(file_path):
            return None
        
        return os.path.getsize(file_path)
    
    def get_relative_path(self, file_path: str, base_dir: str = ".") -> str:
        """
        获取相对路径
        
        Args:
            file_path: 文件路径
            base_dir: 基础目录
            
        Returns:
            相对路径
        """
        if not file_path:
            return ""
        
        try:
            path = Path(file_path)
            base = Path(base_dir)
            return str(path.relative_to(base))
        except ValueError:
            # 如果无法计算相对路径，返回原路径
            return file_path
    
    def normalize_path(self, file_path: str) -> str:
        """
        规范化路径
        
        Args:
            file_path: 文件路径
            
        Returns:
            规范化的路径
        """
        if not file_path:
            return ""
        
        # 统一使用正斜杠
        normalized = file_path.replace('\\', '/')
        
        # 处理多个连续斜杠
        while '//' in normalized:
            normalized = normalized.replace('//', '/')
        
        return normalized


# 创建全局实例
asset_converter = AssetUrlConverter()


# 便捷函数
def convert_to_web_url(file_path: str, base_prefix: str = "/files") -> str:
    """
    将本地文件路径转换为web可访问的URL
    
    Args:
        file_path: 本地文件路径
        base_prefix: 基础前缀
        
    Returns:
        web可访问的URL路径
    """
    return asset_converter.convert_to_web_url(file_path, base_prefix)


def convert_image_path(image_path: str) -> str:
    """
    转换图像路径为web URL
    
    Args:
        image_path: 图像文件路径
        
    Returns:
        web可访问的图像URL
    """
    return asset_converter.convert_image_path(image_path)


def convert_screenshot_path(screenshot_path: str) -> str:
    """
    转换截图路径为web URL
    
    Args:
        screenshot_path: 截图文件路径
        
    Returns:
        web可访问的截图URL
    """
    return asset_converter.convert_screenshot_path(screenshot_path)


def convert_diff_image_path(diff_image_path: str) -> str:
    """
    转换差异图像路径为web URL
    
    Args:
        diff_image_path: 差异图像文件路径
        
    Returns:
        web可访问的差异图像URL
    """
    return asset_converter.convert_diff_image_path(diff_image_path)


def ensure_file_exists(file_path: str) -> bool:
    """
    检查文件是否存在
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件是否存在
    """
    return asset_converter.ensure_file_exists(file_path)


def get_file_size(file_path: str) -> Optional[int]:
    """
    获取文件大小
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小（字节），如果文件不存在返回None
    """
    return asset_converter.get_file_size(file_path) 