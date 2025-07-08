"""
飞书API客户端
Feishu API Client
"""
import requests
import json
from typing import Dict, List, Optional, Any
from ..utils.logger import get_logger
from ..utils.config import Config

logger = get_logger(__name__)

class FeishuClient:
    """飞书API客户端 Feishu API Client"""
    
    def __init__(self):
        """初始化飞书客户端 Initialize Feishu client"""
        self.config = Config.get_feishu_config()
        self.base_url = "https://open.feishu.cn/open-apis"
        self.access_token = None
        
        if not self.config['app_id'] or not self.config['app_secret']:
            raise ValueError("飞书App ID和App Secret不能为空 / Feishu App ID and App Secret cannot be empty")
    
    def get_access_token(self) -> str:
        """
        获取访问令牌
        Get access token
        
        Returns:
            访问令牌 access token
        """
        if self.access_token:
            return self.access_token
            
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        data = {
            "app_id": self.config['app_id'],
            "app_secret": self.config['app_secret']
        }
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                self.access_token = result['tenant_access_token']
                logger.info("成功获取飞书访问令牌 / Successfully obtained Feishu access token")
                return self.access_token
            else:
                raise Exception(f"获取访问令牌失败: {result.get('msg', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"获取飞书访问令牌失败: {e}")
            raise
    
    def get_document_content(self, document_token: str) -> Dict[str, Any]:
        """
        获取文档内容
        Get document content
        
        Args:
            document_token: 文档token document token
            
        Returns:
            文档内容 document content
        """
        access_token = self.get_access_token()
        url = f"{self.base_url}/docx/v1/documents/{document_token}/raw_content"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                logger.info(f"成功获取文档内容: {document_token}")
                return result['data']
            else:
                raise Exception(f"获取文档内容失败: {result.get('msg', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"获取文档内容失败: {e}")
            raise
    
    def get_document_blocks(self, document_token: str) -> List[Dict[str, Any]]:
        """
        获取文档块内容
        Get document blocks
        
        Args:
            document_token: 文档token document token
            
        Returns:
            文档块列表 document blocks
        """
        access_token = self.get_access_token()
        url = f"{self.base_url}/docx/v1/documents/{document_token}/blocks"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                logger.info(f"成功获取文档块: {document_token}")
                return result['data']['items']
            else:
                raise Exception(f"获取文档块失败: {result.get('msg', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"获取文档块失败: {e}")
            raise
    
    def extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """
        从文档块中提取文本并转换为markdown格式
        Extract text from document blocks and convert to markdown format
        """
        text_parts = []
        
        for i, block in enumerate(blocks):
            try:
                # 获取块类型
                block_type = block.get('block_type') or block.get('type', '')
                
                # 调试：打印前几个块的结构
                if i < 5:
                    logger.debug(f"Block {i}: type={block_type}, keys={list(block.keys())}")
                
                # 处理段落块
                if block_type == 'paragraph':
                    paragraph = block.get('paragraph', {})
                    elements = paragraph.get('elements', [])
                    
                    paragraph_text = ""
                    for element in elements:
                        if element.get('type') == 'text_run':
                            text_run = element.get('text_run', {})
                            content = text_run.get('content', '')
                            if content:
                                paragraph_text += content
                    
                    if paragraph_text.strip():
                        text_parts.append(paragraph_text.strip())
                
                # 处理标题块
                elif block_type == 'heading':
                    heading = block.get('heading', {})
                    elements = heading.get('elements', [])
                    level = heading.get('level', 1)
                    
                    heading_text = ""
                    for element in elements:
                        if element.get('type') == 'text_run':
                            text_run = element.get('text_run', {})
                            content = text_run.get('content', '')
                            if content:
                                heading_text += content
                    
                    if heading_text.strip():
                        markdown_prefix = "#" * min(level, 6)  # 最多6级标题
                        text_parts.append(f"\n{markdown_prefix} {heading_text.strip()}\n")
                
                # 处理文本块（旧版API兼容）
                elif block_type == 'text':
                    text = block.get('text', {})
                    if isinstance(text, dict):
                        content = text.get('content', '') or text.get('text', '')
                    else:
                        content = str(text)
                    
                    if content and content.strip():
                        text_parts.append(content.strip())
                
                # 处理列表
                elif block_type in ['bullet_list', 'numbered_list']:
                    # 这里需要处理列表项，但飞书API的列表结构较复杂
                    # 暂时跳过，后续可以改进
                    pass
                
                # 处理表格
                elif block_type == 'table':
                    # 表格处理也比较复杂，暂时跳过
                    pass
                
                # 处理图片
                elif block_type == 'image':
                    text_parts.append("\n[图片]\n")
                
                # 处理分割线
                elif block_type == 'divider':
                    text_parts.append("\n---\n")
                
                # 处理代码块
                elif block_type == 'code':
                    code = block.get('code', {})
                    language = code.get('language', '')
                    content = code.get('content', '')
                    if content:
                        text_parts.append(f"\n```{language}\n{content}\n```\n")
                
                # 处理引用
                elif block_type == 'quote':
                    quote = block.get('quote', {})
                    elements = quote.get('elements', [])
                    
                    quote_text = ""
                    for element in elements:
                        if element.get('type') == 'text_run':
                            text_run = element.get('text_run', {})
                            content = text_run.get('content', '')
                            if content:
                                quote_text += content
                    
                    if quote_text.strip():
                        text_parts.append(f"\n> {quote_text.strip()}\n")
                
            except Exception as e:
                logger.warning(f"处理块 {i} 时出错: {e}")
                continue
        
        # 如果没有提取到内容，尝试其他字段
        if not text_parts:
            logger.warning("未能提取到文档内容，尝试其他字段...")
            for i, block in enumerate(blocks):
                # 尝试提取任何可能的文本字段
                for key in ['content', 'text', 'plain_text', 'raw_text']:
                    if key in block and block[key]:
                        content = block[key]
                        if isinstance(content, str) and content.strip():
                            text_parts.append(content.strip())
                        elif isinstance(content, dict):
                            # 递归查找文本内容
                            def extract_text_recursive(obj):
                                texts = []
                                if isinstance(obj, dict):
                                    for k, v in obj.items():
                                        if k in ['content', 'text', 'plain_text'] and isinstance(v, str):
                                            texts.append(v)
                                        else:
                                            texts.extend(extract_text_recursive(v))
                                elif isinstance(obj, list):
                                    for item in obj:
                                        texts.extend(extract_text_recursive(item))
                                return texts
                            
                            recursive_texts = extract_text_recursive(content)
                            text_parts.extend([t.strip() for t in recursive_texts if t.strip()])
        
        result = '\n\n'.join([t for t in text_parts if t.strip()])
        logger.info(f"提取到文本长度: {len(result)} 字符")
        return result
    
    def parse_prd_document(self, document_token: str) -> Dict[str, Any]:
        """
        解析PRD文档
        Parse PRD document
        
        Args:
            document_token: 文档token document token
            
        Returns:
            解析结果 parsing result
        """
        try:
            logger.info(f"开始解析PRD文档: {document_token}")
            
            # 获取文档基本信息
            doc_info = self.get_document_content(document_token)
            
            # 获取文档块
            blocks = self.get_document_blocks(document_token)
            
            # 提取文本内容
            text_content = self.extract_text_from_blocks(blocks)
            
            # 分析文档结构
            structure = self.analyze_document_structure(blocks)
            
            result = {
                'document_token': document_token,
                'title': doc_info.get('title', ''),
                'text_content': text_content,
                'structure': structure,
                'blocks_count': len(blocks),
                'parsed_at': doc_info.get('updated_at', '')
            }
            
            logger.info(f"PRD文档解析完成: {document_token}")
            return result
            
        except Exception as e:
            logger.error(f"解析PRD文档失败: {e}")
            raise
    
    def analyze_document_structure(self, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析文档结构
        Analyze document structure
        
        Args:
            blocks: 文档块列表 document blocks
            
        Returns:
            文档结构分析结果 document structure analysis
        """
        structure = {
            'headings': [],
            'sections': [],
            'tables': [],
            'lists': [],
            'text_blocks': []
        }
        
        current_section = None
        
        for block in blocks:
            block_type = block.get('type')
            content = block.get('content', {})
            
            if block_type == 'heading':
                heading_text = content.get('text', '')
                if heading_text:
                    structure['headings'].append(heading_text)
                    current_section = heading_text
                    
            elif block_type == 'table':
                table_info = {
                    'section': current_section,
                    'rows': len(content.get('table', {}).get('rows', [])),
                    'columns': len(content.get('table', {}).get('rows', [{}])[0].get('cells', [])) if content.get('table', {}).get('rows') else 0
                }
                structure['tables'].append(table_info)
                
            elif block_type == 'list':
                list_info = {
                    'section': current_section,
                    'items_count': len(content.get('items', []))
                }
                structure['lists'].append(list_info)
                
            elif block_type == 'text':
                text_length = len(content.get('text', ''))
                if text_length > 0:
                    structure['text_blocks'].append({
                        'section': current_section,
                        'length': text_length
                    })
        
        return structure

    def get_bitable_info(self, app_token: str) -> Dict[str, Any]:
        """
        获取多维表格信息
        Get bitable information
        
        Args:
            app_token: 多维表格token bitable app token
            
        Returns:
            多维表格信息 bitable information
        """
        access_token = self.get_access_token()
        url = f"{self.base_url}/bitable/v1/apps/{app_token}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                logger.info(f"成功获取多维表格信息: {app_token}")
                return result['data']
            else:
                raise Exception(f"获取多维表格信息失败: {result.get('msg', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"获取多维表格信息失败: {e}")
            raise

    def get_bitable_tables(self, app_token: str) -> List[Dict[str, Any]]:
        """
        获取多维表格的数据表列表
        Get tables in bitable
        
        Args:
            app_token: 多维表格token bitable app token
            
        Returns:
            数据表列表 tables list
        """
        access_token = self.get_access_token()
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                logger.info(f"成功获取数据表列表: {app_token}")
                return result['data']['items']
            else:
                raise Exception(f"获取数据表列表失败: {result.get('msg', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"获取数据表列表失败: {e}")
            raise

    def get_bitable_fields(self, app_token: str, table_id: str) -> List[Dict[str, Any]]:
        """
        获取数据表字段信息
        Get table fields information
        
        Args:
            app_token: 多维表格token bitable app token
            table_id: 数据表ID table ID
            
        Returns:
            字段列表 fields list
        """
        access_token = self.get_access_token()
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                logger.info(f"成功获取字段列表: {table_id}")
                return result['data']['items']
            else:
                raise Exception(f"获取字段列表失败: {result.get('msg', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"获取字段列表失败: {e}")
            raise

    def create_bitable_record(self, app_token: str, table_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        在多维表格中创建记录
        Create record in bitable
        
        Args:
            app_token: 多维表格token bitable app token
            table_id: 数据表ID table ID
            fields: 字段数据 field data
            
        Returns:
            创建的记录信息 created record information
        """
        access_token = self.get_access_token()
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "fields": fields
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                logger.info(f"成功创建记录: {table_id}")
                return result['data']['record']
            else:
                raise Exception(f"创建记录失败: {result.get('msg', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"创建记录失败: {e}")
            raise

    def update_bitable_record(self, app_token: str, table_id: str, record_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新多维表格中的记录
        Update record in bitable
        
        Args:
            app_token: 多维表格token bitable app token
            table_id: 数据表ID table ID
            record_id: 记录ID record ID
            fields: 更新的字段数据 updated field data
            
        Returns:
            更新后的记录信息 updated record information
        """
        access_token = self.get_access_token()
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "fields": fields
        }
        
        try:
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                logger.info(f"成功更新记录: {record_id}")
                return result['data']['record']
            else:
                error_msg = f"更新记录失败: {result.get('msg', 'Unknown error')}"
                logger.error(f"{error_msg}, 错误代码: {result.get('code')}, 详细信息: {result}")
                raise Exception(error_msg)
                
        except requests.exceptions.HTTPError as e:
            # 详细记录HTTP错误信息
            error_details = {
                'status_code': e.response.status_code,
                'url': url,
                'headers': headers,
                'data': data,
                'response_text': e.response.text if hasattr(e.response, 'text') else 'N/A'
            }
            logger.error(f"HTTP错误详细信息: {error_details}")
            
            if e.response.status_code == 403:
                logger.error("403错误可能原因: 1)应用缺少bitable:write权限 2)应用未被授权访问此表格 3)token权限不足")
            
            logger.error(f"更新记录失败: {e}")
            raise
        except Exception as e:
            logger.error(f"更新记录失败: {e}")
            raise

    def get_bitable_records(self, app_token: str, table_id: str, page_token: str = None, page_size: int = 100) -> Dict[str, Any]:
        """
        获取多维表格记录
        Get bitable records
        
        Args:
            app_token: 多维表格token bitable app token
            table_id: 数据表ID table ID
            page_token: 分页token pagination token
            page_size: 页面大小 page size
            
        Returns:
            记录列表 records list
        """
        access_token = self.get_access_token()
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "page_size": page_size
        }
        
        if page_token:
            params["page_token"] = page_token
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                logger.info(f"成功获取记录: {table_id}")
                return result['data']
            else:
                raise Exception(f"获取记录失败: {result.get('msg', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"获取记录失败: {e}")
            raise 