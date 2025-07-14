"""
Figma API 截图服务
Figma API Screenshot Service
"""
import os
import time
from typing import Dict, List, Optional, Tuple
from ..figma.client import FigmaClient
from ..utils.logger import get_logger

logger = get_logger(__name__)

class FigmaScreenshotService:
    """Figma API 截图服务，用于替换浏览器截图功能"""
    
    def __init__(self):
        """初始化 Figma 截图服务"""
        self.figma_client = FigmaClient()
        self.supported_formats = ['png', 'jpg', 'svg', 'pdf']
        self.supported_scales = [1.0, 2.0, 3.0, 4.0]
    
    def capture_figma_node(self, 
                          figma_url: str,
                          output_path: str,
                          format: str = "png",
                          scale: float = 2.0) -> str:
        """
        从 Figma URL 获取节点截图
        
        Args:
            figma_url: Figma URL
            output_path: 输出路径
            format: 图片格式
            scale: 缩放比例
            
        Returns:
            截图文件路径
        """
        try:
            logger.info(f"开始获取 Figma 节点截图: {figma_url}")
            
            # 使用新的 API 截图方法
            screenshot_path = self.figma_client.capture_from_figma_url(
                figma_url=figma_url,
                format=format,
                scale=scale,
                save_path=output_path
            )
            
            logger.info(f"Figma 节点截图完成: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Figma 节点截图失败: {e}")
            raise
    
    def capture_figma_nodes_batch(self,
                                 figma_urls: List[str],
                                 output_dir: str,
                                 format: str = "png",
                                 scale: float = 2.0) -> Dict[str, str]:
        """
        批量获取多个 Figma 节点的截图
        
        Args:
            figma_urls: Figma URL 列表
            output_dir: 输出目录
            format: 图片格式
            scale: 缩放比例
            
        Returns:
            URL 到文件路径的映射
        """
        try:
            logger.info(f"开始批量获取 {len(figma_urls)} 个 Figma 节点截图")
            
            results = {}
            
            for i, figma_url in enumerate(figma_urls):
                try:
                    # 生成输出文件名
                    timestamp = int(time.time())
                    filename = f"figma_node_{i}_{timestamp}.{format}"
                    output_path = os.path.join(output_dir, filename)
                    
                    # 获取截图
                    screenshot_path = self.capture_figma_node(
                        figma_url=figma_url,
                        output_path=output_path,
                        format=format,
                        scale=scale
                    )
                    
                    results[figma_url] = screenshot_path
                    logger.info(f"节点 {i+1}/{len(figma_urls)} 截图完成")
                    
                except Exception as e:
                    logger.error(f"节点 {i+1} 截图失败: {e}")
                    results[figma_url] = None
            
            successful_count = sum(1 for path in results.values() if path is not None)
            logger.info(f"批量截图完成: {successful_count}/{len(figma_urls)} 成功")
            
            return results
            
        except Exception as e:
            logger.error(f"批量 Figma 截图失败: {e}")
            raise
    
    def capture_figma_file_nodes(self,
                                figma_url: str,
                                node_ids: List[str],
                                output_dir: str,
                                format: str = "png",
                                scale: float = 2.0) -> Dict[str, str]:
        """
        从同一个 Figma 文件中获取多个节点的截图
        
        Args:
            figma_url: Figma URL
            node_ids: 节点ID列表
            output_dir: 输出目录
            format: 图片格式
            scale: 缩放比例
            
        Returns:
            节点ID到文件路径的映射
        """
        try:
            logger.info(f"开始获取 Figma 文件中的 {len(node_ids)} 个节点截图")
            
            # 解析 Figma URL
            figma_info = self.figma_client.parse_figma_url(figma_url)
            file_id = figma_info['file_id']
            
            # 使用批量截图方法
            results = self.figma_client.capture_multiple_nodes_screenshots(
                file_id=file_id,
                node_ids=node_ids,
                format=format,
                scale=scale,
                output_dir=output_dir
            )
            
            logger.info(f"Figma 文件节点截图完成: {len(results)} 个节点")
            return results
            
        except Exception as e:
            logger.error(f"Figma 文件节点截图失败: {e}")
            raise
    
    def get_figma_file_info(self, figma_url: str) -> Dict[str, any]:
        """
        获取 Figma 文件信息
        
        Args:
            figma_url: Figma URL
            
        Returns:
            文件信息
        """
        try:
            # 解析 Figma URL
            figma_info = self.figma_client.parse_figma_url(figma_url)
            file_id = figma_info['file_id']
            
            # 获取文件信息
            file_info = self.figma_client.get_file_info(file_id)
            
            return {
                'file_id': file_id,
                'node_id': figma_info.get('node_id'),
                'file_name': file_info.get('name', 'Unknown'),
                'last_modified': file_info.get('lastModified', 'Unknown'),
                'pages_count': len(file_info.get('document', {}).get('children', [])),
                'figma_url': figma_url
            }
            
        except Exception as e:
            logger.error(f"获取 Figma 文件信息失败: {e}")
            raise
    
    def analyze_figma_design(self, figma_url: str) -> Dict[str, any]:
        """
        分析 Figma 设计结构
        
        Args:
            figma_url: Figma URL
            
        Returns:
            设计分析结果
        """
        try:
            # 解析 Figma URL
            figma_info = self.figma_client.parse_figma_url(figma_url)
            file_id = figma_info['file_id']
            node_id = figma_info.get('node_id')
            
            # 分析设计结构
            design_structure = self.figma_client.analyze_design_structure(file_id, node_id)
            
            return {
                'file_id': file_id,
                'node_id': node_id,
                'design_structure': design_structure,
                'figma_url': figma_url
            }
            
        except Exception as e:
            logger.error(f"分析 Figma 设计失败: {e}")
            raise
    
    def validate_figma_url(self, figma_url: str) -> bool:
        """
        验证 Figma URL 是否有效
        
        Args:
            figma_url: Figma URL
            
        Returns:
            是否有效
        """
        try:
            # 尝试解析 URL
            figma_info = self.figma_client.parse_figma_url(figma_url)
            
            # 尝试获取文件信息
            file_id = figma_info['file_id']
            self.figma_client.get_file_info(file_id)
            
            return True
            
        except Exception as e:
            logger.warning(f"Figma URL 验证失败: {e}")
            return False
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的图片格式"""
        return self.supported_formats.copy()
    
    def get_supported_scales(self) -> List[float]:
        """获取支持的缩放比例"""
        return self.supported_scales.copy()
    
    def cleanup(self):
        """清理资源"""
        try:
            self.figma_client = None
            logger.info("Figma 截图服务清理完成")
        except Exception as e:
            logger.warning(f"Figma 截图服务清理失败: {e}")


class HybridScreenshotService:
    """混合截图服务，支持 Figma API 和浏览器截图"""
    
    def __init__(self, prefer_figma_api: bool = True):
        """
        初始化混合截图服务
        
        Args:
            prefer_figma_api: 是否优先使用 Figma API
        """
        self.prefer_figma_api = prefer_figma_api
        self.figma_service = FigmaScreenshotService()
        self.browser_service = None  # 延迟初始化
        
    def _get_browser_service(self):
        """延迟初始化浏览器截图服务"""
        if self.browser_service is None:
            from .capture import ScreenshotCapture
            self.browser_service = ScreenshotCapture()
        return self.browser_service
    
    def capture_screenshot(self,
                          url: str,
                          output_path: str,
                          device: str = "desktop",
                          wait_time: int = 3,
                          **kwargs) -> str:
        """
        智能截图：优先使用 Figma API，失败时回退到浏览器截图
        
        Args:
            url: URL（Figma URL 或网站 URL）
            output_path: 输出路径
            device: 设备类型
            wait_time: 等待时间
            **kwargs: 其他参数
            
        Returns:
            截图文件路径
        """
        try:
            # 检查是否是 Figma URL
            if self._is_figma_url(url):
                if self.prefer_figma_api:
                    logger.info("检测到 Figma URL，使用 API 截图")
                    return self.figma_service.capture_figma_node(
                        figma_url=url,
                        output_path=output_path,
                        **kwargs
                    )
                else:
                    logger.info("检测到 Figma URL，但配置为使用浏览器截图")
                    return self._capture_with_browser(url, output_path, device, wait_time)
            else:
                logger.info("检测到网站 URL，使用浏览器截图")
                return self._capture_with_browser(url, output_path, device, wait_time)
                
        except Exception as e:
            logger.error(f"智能截图失败: {e}")
            
            # 如果是 Figma URL 且 API 失败，尝试浏览器截图
            if self._is_figma_url(url) and self.prefer_figma_api:
                logger.info("Figma API 截图失败，回退到浏览器截图")
                return self._capture_with_browser(url, output_path, device, wait_time)
            else:
                raise
    
    def _is_figma_url(self, url: str) -> bool:
        """检查是否是 Figma URL"""
        return 'figma.com' in url.lower()
    
    def _capture_with_browser(self, url: str, output_path: str, device: str, wait_time: int) -> str:
        """使用浏览器截图"""
        browser_service = self._get_browser_service()
        return browser_service.capture_url(
            url=url,
            output_path=output_path,
            device=device,
            wait_time=wait_time
        )
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.figma_service:
                self.figma_service.cleanup()
            if self.browser_service:
                self.browser_service._cleanup_processes()
            logger.info("混合截图服务清理完成")
        except Exception as e:
            logger.warning(f"混合截图服务清理失败: {e}") 