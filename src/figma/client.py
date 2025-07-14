"""
Figma API客户端
Figma API Client
"""
import os
import requests
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, parse_qs
import time

from ..utils.logger import get_logger
from ..utils.config import Config

logger = get_logger(__name__)

class FigmaClient:
    """Figma API客户端"""
    
    def __init__(self):
        """初始化Figma客户端"""
        self.access_token = Config.FIGMA_ACCESS_TOKEN
        if not self.access_token:
            raise ValueError("FIGMA_ACCESS_TOKEN not found in environment variables")
        
        self.base_url = "https://api.figma.com/v1"
        self.headers = {
            "X-Figma-Token": self.access_token,
            "Content-Type": "application/json"
        }
    
    def parse_figma_url(self, figma_url: str) -> Dict[str, str]:
        """
        解析Figma URL获取文件ID和节点ID
        Parse Figma URL to get file ID and node ID
        
        Args:
            figma_url: Figma文件URL
            
        Returns:
            包含file_id和node_id的字典
        """
        try:
            logger.info(f"正在解析Figma URL: {figma_url}")
            
            # 解析URL：支持多种格式
            # 标准格式：https://www.figma.com/file/{file_id}/{title}?node-id={node_id}
            # 简化格式：https://www.figma.com/file/{file_id}
            # 设计格式：https://www.figma.com/design/{file_id}/{title}?node-id={node_id}
            
            parsed = urlparse(figma_url)
            path_parts = [part for part in parsed.path.strip('/').split('/') if part]
            
            logger.info(f"URL路径部分: {path_parts}")
            logger.info(f"URL查询参数: {parsed.query}")
            
            # 检查域名
            if 'figma.com' not in parsed.netloc:
                raise ValueError(f"不是有效的Figma域名: {parsed.netloc}")
            
            # 检查路径格式
            if len(path_parts) < 2:
                raise ValueError(f"URL路径太短，需要至少2个部分，实际有{len(path_parts)}个: {path_parts}")
            
            # 支持 /file/ 和 /design/ 路径
            if path_parts[0] not in ['file', 'design']:
                raise ValueError(f"URL路径必须以 'file' 或 'design' 开头，实际是: {path_parts[0]}")
            
            file_id = path_parts[1]
            
            # 验证文件ID格式（通常是字母数字组合）
            if not file_id or len(file_id) < 10:
                raise ValueError(f"文件ID格式不正确: {file_id}")
            
            # 获取节点ID（如果存在）
            query_params = parse_qs(parsed.query)
            node_id = None
            
            # 支持多种节点ID参数格式
            for param_name in ['node-id', 'node_id', 'nodeId']:
                if param_name in query_params and query_params[param_name][0]:
                    node_id = query_params[param_name][0]
                    break
            
            # 如果node_id包含URL编码，进行解码
            if node_id:
                import urllib.parse
                node_id = urllib.parse.unquote(node_id)
            
            result = {"file_id": file_id}
            if node_id:
                result["node_id"] = node_id
                
            logger.info(f"解析Figma URL成功: file_id={file_id}, node_id={node_id}")
            return result
            
        except Exception as e:
            error_msg = f"解析Figma URL失败: {e}"
            logger.error(error_msg)
            logger.error(f"输入的URL: {figma_url}")
            
            # 提供帮助信息
            logger.info("支持的Figma URL格式:")
            logger.info("1. https://www.figma.com/file/{file_id}/{title}")
            logger.info("2. https://www.figma.com/file/{file_id}/{title}?node-id={node_id}")
            logger.info("3. https://www.figma.com/design/{file_id}/{title}?node-id={node_id}")
            
            raise ValueError(error_msg)
    
    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """
        获取Figma文件信息
        Get Figma file information
        
        Args:
            file_id: Figma文件ID
            
        Returns:
            文件信息字典
        """
        try:
            url = f"{self.base_url}/files/{file_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"成功获取Figma文件信息: {file_id}")
            return result
            
        except Exception as e:
            logger.error(f"获取Figma文件信息失败: {e}")
            raise
    
    def get_file_nodes(self, file_id: str, node_ids: List[str]) -> Dict[str, Any]:
        """
        获取指定节点信息
        Get specific node information
        
        Args:
            file_id: Figma文件ID
            node_ids: 节点ID列表
            
        Returns:
            节点信息字典
        """
        try:
            node_ids_str = ','.join(node_ids)
            url = f"{self.base_url}/files/{file_id}/nodes"
            params = {"ids": node_ids_str}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"成功获取节点信息: {node_ids}")
            return result
            
        except Exception as e:
            logger.error(f"获取节点信息失败: {e}")
            raise
    
    def export_images(self, file_id: str, node_ids: List[str], 
                     format: str = "png", scale: float = 2.0) -> Dict[str, str]:
        """
        导出节点为图片
        Export nodes as images
        
        Args:
            file_id: Figma文件ID
            node_ids: 节点ID列表
            format: 图片格式 (png, jpg, svg, pdf)
            scale: 图片缩放比例
            
        Returns:
            节点ID到图片URL的映射
        """
        try:
            node_ids_str = ','.join(node_ids)
            url = f"{self.base_url}/images/{file_id}"
            params = {
                "ids": node_ids_str,
                "format": format,
                "scale": scale
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('err'):
                raise Exception(f"Figma API error: {result.get('err')}")
            
            image_urls = result.get('images', {})
            logger.info(f"成功导出{len(image_urls)}张图片")
            return image_urls
            
        except Exception as e:
            logger.error(f"导出图片失败: {e}")
            raise
    
    def download_image(self, image_url: str, save_path: str) -> str:
        """
        下载图片到本地
        Download image to local file
        
        Args:
            image_url: 图片URL
            save_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"图片下载成功: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"图片下载失败: {e}")
            raise
    
    def get_design_tokens(self, file_id: str) -> Dict[str, Any]:
        """
        提取设计令牌（颜色、字体、间距等）
        Extract design tokens (colors, fonts, spacing, etc.)
        
        Args:
            file_id: Figma文件ID
            
        Returns:
            设计令牌字典
        """
        try:
            file_info = self.get_file_info(file_id)
            
            # 提取颜色
            colors = set()
            fonts = set()
            
            def extract_from_node(node):
                """递归提取节点中的设计令牌"""
                # 提取填充颜色
                if 'fills' in node:
                    for fill in node['fills']:
                        if fill.get('type') == 'SOLID' and 'color' in fill:
                            color = fill['color']
                            # 转换为hex格式
                            r = int(color.get('r', 0) * 255)
                            g = int(color.get('g', 0) * 255)
                            b = int(color.get('b', 0) * 255)
                            hex_color = f"#{r:02x}{g:02x}{b:02x}"
                            colors.add(hex_color)
                
                # 提取文本样式
                if 'style' in node and 'fontFamily' in node['style']:
                    fonts.add(node['style']['fontFamily'])
                
                # 递归处理子节点
                if 'children' in node:
                    for child in node['children']:
                        extract_from_node(child)
            
            # 遍历所有页面和节点
            document = file_info.get('document', {})
            if 'children' in document:
                for page in document['children']:
                    extract_from_node(page)
            
            design_tokens = {
                'colors': list(colors),
                'fonts': list(fonts),
                'file_name': file_info.get('name', ''),
                'last_modified': file_info.get('lastModified', '')
            }
            
            logger.info(f"成功提取设计令牌: {len(colors)}种颜色, {len(fonts)}种字体")
            return design_tokens
            
        except Exception as e:
            logger.error(f"提取设计令牌失败: {e}")
            raise
    
    def analyze_design_structure(self, file_id: str, node_id: str = None) -> Dict[str, Any]:
        """
        分析设计稿结构
        Analyze design structure
        
        Args:
            file_id: Figma文件ID
            node_id: 特定节点ID（可选）
            
        Returns:
            设计结构分析结果
        """
        try:
            if node_id:
                # 分析特定节点
                nodes_info = self.get_file_nodes(file_id, [node_id])
                target_node = nodes_info['nodes'][node_id]['document']
            else:
                # 分析整个文件
                file_info = self.get_file_info(file_id)
                target_node = file_info['document']
            
            structure = {
                'components_count': 0,
                'text_nodes_count': 0,
                'image_nodes_count': 0,
                'frame_nodes_count': 0,
                'layers_depth': 0,
                'total_nodes': 0
            }
            
            def analyze_node(node, depth=0):
                """递归分析节点结构"""
                structure['total_nodes'] += 1
                structure['layers_depth'] = max(structure['layers_depth'], depth)
                
                node_type = node.get('type', '')
                
                if node_type == 'COMPONENT':
                    structure['components_count'] += 1
                elif node_type == 'TEXT':
                    structure['text_nodes_count'] += 1
                elif node_type in ['RECTANGLE', 'ELLIPSE', 'POLYGON']:
                    # 检查是否是图片
                    fills = node.get('fills', [])
                    for fill in fills:
                        if fill.get('type') == 'IMAGE':
                            structure['image_nodes_count'] += 1
                            break
                elif node_type == 'FRAME':
                    structure['frame_nodes_count'] += 1
                
                # 递归处理子节点
                if 'children' in node:
                    for child in node['children']:
                        analyze_node(child, depth + 1)
            
            analyze_node(target_node)
            
            logger.info(f"设计结构分析完成: 总节点{structure['total_nodes']}个")
            return structure
            
        except Exception as e:
            logger.error(f"设计结构分析失败: {e}")
            raise 

    def capture_node_screenshot(self, file_id: str, node_id: str, 
                               format: str = "png", scale: float = 2.0,
                               save_path: str = None) -> str:
        """
        通过 Figma API 获取节点截图（比浏览器截图更快）
        Capture node screenshot via Figma API (faster than browser screenshot)
        
        Args:
            file_id: Figma文件ID
            node_id: 节点ID
            format: 图片格式 (png, jpg, svg, pdf)
            scale: 图片缩放比例 (1.0, 2.0, 3.0, 4.0)
            save_path: 保存路径，如果为None则自动生成
            
        Returns:
            保存的文件路径
        """
        try:
            logger.info(f"开始通过API获取节点截图: file_id={file_id}, node_id={node_id}")
            
            # 导出节点为图片URL
            image_urls = self.export_images(file_id, [node_id], format, scale)
            
            # 添加调试信息
            logger.info(f"export_images 返回的数据: {image_urls}")
            logger.info(f"返回数据的类型: {type(image_urls)}")
            logger.info(f"返回数据的键: {list(image_urls.keys()) if isinstance(image_urls, dict) else 'Not a dict'}")
            
            if not image_urls:
                raise Exception(f"export_images 返回空数据")
            
            if not isinstance(image_urls, dict):
                raise Exception(f"export_images 返回的数据不是字典类型: {type(image_urls)}")
            
            # 处理节点ID格式问题：Figma API 返回的键使用冒号分隔，URL中使用连字符
            # 尝试多种格式匹配
            possible_keys = [
                node_id,  # 原始格式
                node_id.replace('-', ':'),  # 连字符转冒号
                node_id.replace(':', '-'),  # 冒号转连字符
            ]
            
            image_url = None
            used_key = None
            
            for key in possible_keys:
                if key in image_urls and image_urls[key]:
                    image_url = image_urls[key]
                    used_key = key
                    logger.info(f"找到匹配的键: {key}")
                    break
            
            if not image_url:
                logger.warning(f"节点 {node_id} 不在返回的键中，可用的键: {list(image_urls.keys())}")
                # 尝试使用第一个可用的键
                if image_urls:
                    first_key = list(image_urls.keys())[0]
                    logger.info(f"使用第一个可用的键: {first_key}")
                    image_url = image_urls[first_key]
                    used_key = first_key
                else:
                    raise Exception(f"无法获取节点 {node_id} 的图片URL，返回的数据为空")
            
            logger.info(f"最终使用的键: {used_key}, URL: {image_url}")
            
            if not image_url:
                raise Exception(f"节点 {node_id} 的图片URL为空")
            
            # 如果没有指定保存路径，自动生成
            if not save_path:
                timestamp = int(time.time())
                save_path = f"screenshots/figma_node_{node_id}_{timestamp}.{format}"
            
            # 下载图片
            downloaded_path = self.download_image(image_url, save_path)
            
            logger.info(f"节点截图获取成功: {downloaded_path}")
            return downloaded_path
            
        except Exception as e:
            logger.error(f"获取节点截图失败: {e}")
            raise
    
    def capture_multiple_nodes_screenshots(self, file_id: str, node_ids: List[str],
                                         format: str = "png", scale: float = 2.0,
                                         output_dir: str = "screenshots") -> Dict[str, str]:
        """
        批量获取多个节点的截图
        Batch capture screenshots for multiple nodes
        
        Args:
            file_id: Figma文件ID
            node_ids: 节点ID列表
            format: 图片格式
            scale: 图片缩放比例
            output_dir: 输出目录
            
        Returns:
            节点ID到文件路径的映射
        """
        try:
            logger.info(f"开始批量获取节点截图: {len(node_ids)} 个节点")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 导出所有节点为图片URL
            image_urls = self.export_images(file_id, node_ids, format, scale)
            
            results = {}
            timestamp = int(time.time())
            
            for node_id in node_ids:
                # 处理节点ID格式问题：尝试多种格式匹配
                possible_keys = [
                    node_id,  # 原始格式
                    node_id.replace('-', ':'),  # 连字符转冒号
                    node_id.replace(':', '-'),  # 冒号转连字符
                ]
                
                image_url = None
                used_key = None
                
                for key in possible_keys:
                    if key in image_urls and image_urls[key]:
                        image_url = image_urls[key]
                        used_key = key
                        break
                
                if image_url:
                    try:
                        # 生成保存路径
                        filename = f"node_{node_id}_{timestamp}.{format}"
                        save_path = os.path.join(output_dir, filename)
                        
                        # 下载图片
                        downloaded_path = self.download_image(image_url, save_path)
                        results[node_id] = downloaded_path
                        
                        logger.info(f"节点 {node_id} 截图完成: {downloaded_path} (使用键: {used_key})")
                        
                    except Exception as e:
                        logger.error(f"节点 {node_id} 截图失败: {e}")
                        results[node_id] = None
                else:
                    logger.warning(f"节点 {node_id} 没有获取到图片URL")
                    # 尝试使用其他可用的键
                    if image_urls:
                        available_keys = list(image_urls.keys())
                        logger.info(f"可用的键: {available_keys}")
                        # 这里可以选择使用第一个可用的键，或者跳过
                        results[node_id] = None
                    else:
                        results[node_id] = None
            
            successful_count = sum(1 for path in results.values() if path is not None)
            logger.info(f"批量截图完成: {successful_count}/{len(node_ids)} 成功")
            
            return results
            
        except Exception as e:
            logger.error(f"批量获取节点截图失败: {e}")
            raise
    
    def capture_from_figma_url(self, figma_url: str, format: str = "png", 
                             scale: float = 2.0, save_path: str = None) -> str:
        """
        从 Figma URL 直接获取截图
        Capture screenshot directly from Figma URL
        
        Args:
            figma_url: Figma URL (包含文件ID和节点ID)
            format: 图片格式
            scale: 图片缩放比例
            save_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        try:
            # 解析 Figma URL
            parsed_info = self.parse_figma_url(figma_url)
            file_id = parsed_info["file_id"]
            node_id = parsed_info.get("node_id")
            
            if not node_id:
                raise ValueError("URL 中没有找到节点ID，请提供包含 node-id 参数的完整 URL")
            
            # 获取截图
            return self.capture_node_screenshot(file_id, node_id, format, scale, save_path)
            
        except Exception as e:
            logger.error(f"从 Figma URL 获取截图失败: {e}")
            raise 