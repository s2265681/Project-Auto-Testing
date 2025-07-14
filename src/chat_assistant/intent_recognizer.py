#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
意图识别模块
Intent Recognition Module

解析用户的自然语言输入，识别意图和提取参数
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """意图类型枚举"""
    # 测试相关
    GENERATE_TEST_CASES = "generate_test_cases"
    VISUAL_COMPARISON = "visual_comparison"
    FULL_WORKFLOW = "full_workflow"
    
    # 查询相关
    CHECK_STATUS = "check_status"
    VIEW_REPORTS = "view_reports"
    LIST_PROJECTS = "list_projects"
    
    # 系统相关
    HELP = "help"
    HEALTH_CHECK = "health_check"
    
    # 未知意图
    UNKNOWN = "unknown"

@dataclass
class Intent:
    """意图对象"""
    type: IntentType
    confidence: float
    parameters: Dict[str, Any]
    raw_text: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'type': self.type.value,
            'confidence': self.confidence,
            'parameters': self.parameters,
            'raw_text': self.raw_text
        }

class IntentRecognizer:
    """意图识别器"""
    
    def __init__(self):
        self.intent_patterns = self._init_intent_patterns()
        self.parameter_extractors = self._init_parameter_extractors()
    
    def _init_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """初始化意图匹配模式"""
        return {
            IntentType.GENERATE_TEST_CASES: [
                r'生成测试用例',
                r'创建测试用例',
                r'生成.*测试',
                r'测试用例.*生成',
                r'根据.*生成.*用例',
                r'generate.*test.*case',
                r'create.*test.*case',
                r'测试.*生成'
            ],
            
            IntentType.VISUAL_COMPARISON: [
                r'视觉对比',
                r'视觉比较',
                r'UI对比',
                r'UI比较',
                r'界面对比',
                r'界面比较',
                r'对比.*网站',
                r'对比.*figma',
                r'对比.*设计',
                r'网站.*对比',
                r'figma.*对比',
                r'figma.*比较',
                r'设计.*对比',
                r'设计.*比较',
                r'网站.*figma',
                r'figma.*网站',
                r'visual.*comparison',
                r'ui.*comparison',
                r'design.*comparison',
                r'compare.*website',
                r'compare.*figma'
            ],
            
            IntentType.FULL_WORKFLOW: [
                r'完整测试',
                r'全流程测试',
                r'执行完整.*流程',
                r'运行完整.*测试',
                r'完整.*工作流',
                r'全部测试',
                r'完整.*流程',
                r'full.*workflow',
                r'complete.*test',
                r'full.*test'
            ],
            
            IntentType.CHECK_STATUS: [
                r'检查状态',
                r'查看状态',
                r'状态.*如何',
                r'进度.*如何',
                r'执行.*状态',
                r'测试.*状态',
                r'check.*status',
                r'view.*status',
                r'状态'
            ],
            
            IntentType.VIEW_REPORTS: [
                r'查看报告',
                r'看看报告',
                r'报告.*内容',
                r'测试.*报告',
                r'结果.*报告',
                r'view.*report',
                r'show.*report',
                r'报告'
            ],
            
            IntentType.LIST_PROJECTS: [
                r'列出项目',
                r'查看项目',
                r'项目.*列表',
                r'有哪些项目',
                r'显示.*项目',
                r'list.*project',
                r'show.*project',
                r'项目'
            ],
            
            IntentType.HELP: [
                r'帮助',
                r'怎么用',
                r'使用说明',
                r'能做什么',
                r'功能.*介绍',
                r'help',
                r'usage',
                r'how.*to',
                r'what.*can'
            ],
            
            IntentType.HEALTH_CHECK: [
                r'健康检查',
                r'系统.*状态',
                r'服务.*状态',
                r'运行.*正常',
                r'health.*check',
                r'system.*status',
                r'service.*status'
            ]
        }
    
    def _init_parameter_extractors(self) -> Dict[str, List[str]]:
        """初始化参数提取模式"""
        return {
            'url': [
                r'https?://[^\s]+',
                r'www\.[^\s]+',
                r'[^\s]+\.com[^\s]*',
                r'[^\s]+\.cn[^\s]*'
            ],
            'figma_url': [
                r'https://www\.figma\.com/[^\s]+',
                r'figma\.com/[^\s]+',
                r'figma[^\s]*://[^\s]+'
            ],
            'document_token': [
                r'\b[A-Za-z0-9]{20,}\b',  # 飞书文档token格式（word boundary）
                r'文档[：:\s]*([A-Za-z0-9]{15,})',  # "文档 token" 格式
                r'token[：:\s]*([A-Za-z0-9]{15,})',  # "token: xxx" 格式
                r'doc[A-Za-z0-9]{15,}',  # doc开头的token
                r'[A-Za-z0-9]{25,}'  # 更长的token（确保是文档token）
            ],
            'device': [
                r'移动端|手机|mobile',
                r'桌面端|电脑|desktop',
                r'平板|tablet'
            ],
            'project_name': [
                r'项目[：:]\s*([^\s]+)',
                r'project[：:]\s*([^\s]+)',
                r'名称[：:]\s*([^\s]+)'
            ],
            'cookie': [
                r'cookie[：:\s]*([^;\n]+(?:;[^;\n]+)*)',  # cookie: xxx;yyy;zzz
                r'Cookie[：:\s]*([^;\n]+(?:;[^;\n]+)*)',  # Cookie: xxx;yyy;zzz
                r'cookies[：:\s]*([^;\n]+(?:;[^;\n]+)*)',  # cookies: xxx;yyy;zzz
                r'Cookies[：:\s]*([^;\n]+(?:;[^;\n]+)*)'  # Cookies: xxx;yyy;zzz
            ],
            'localstorage': [
                r'localstorage[：:\s]*(\{[^}]+\})',  # localStorage: {...}
                r'localStorage[：:\s]*(\{[^}]+\})',  # localStorage: {...}
                r'local_storage[：:\s]*(\{[^}]+\})',  # local_storage: {...}
                r'LocalStorage[：:\s]*(\{[^}]+\})'   # LocalStorage: {...}
            ]
        }
    
    def recognize_intent(self, text: str) -> Intent:
        """识别用户输入的意图"""
        original_text = text.strip()  # 保存原始文本用于参数提取
        normalized_text = original_text.lower()  # 小写文本用于意图识别
        
        # 尝试匹配各种意图模式
        best_match = None
        best_confidence = 0.0
        
        for intent_type, patterns in self.intent_patterns.items():
            confidence = self._calculate_confidence(normalized_text, patterns)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = intent_type
        
        # 如果没有匹配到明确意图，返回未知意图
        if best_match is None or best_confidence < 0.3:
            best_match = IntentType.UNKNOWN
            best_confidence = 0.0
        
        # 使用原始文本提取参数（保持大小写）
        parameters = self._extract_parameters(original_text)
        
        return Intent(
            type=best_match,
            confidence=best_confidence,
            parameters=parameters,
            raw_text=original_text
        )
    
    def _calculate_confidence(self, text: str, patterns: List[str]) -> float:
        """计算匹配置信度"""
        if not patterns:
            return 0.0
            
        max_match_score = 0.0
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # 计算模式匹配分数
                pattern_score = 0.5  # 基础匹配分数
                
                # 完全匹配加分
                if re.fullmatch(pattern, text, re.IGNORECASE):
                    pattern_score = 1.0
                elif text.strip() == pattern.strip():
                    pattern_score = 1.0
                # 包含匹配但更精确的加分
                elif len(pattern) <= len(text) and pattern in text:
                    pattern_score = 0.8
                # 复杂模式匹配加分
                elif len(pattern) > 10:
                    pattern_score = 0.7
                
                max_match_score = max(max_match_score, pattern_score)
        
        return max_match_score
    
    def _extract_parameters(self, text: str) -> Dict[str, Any]:
        """从文本中提取参数"""
        parameters = {}
        
        # 提取URL
        urls = self._extract_urls(text)
        if urls:
            # 过滤和优先排序URL：优先选择完整的https/http URL
            def url_priority(url):
                if url.startswith(('https://', 'http://')):
                    return 0  # 最高优先级
                elif url.startswith('www.'):
                    return 1  # 中等优先级
                else:
                    return 2  # 最低优先级
            
            urls.sort(key=url_priority)
            parameters['urls'] = urls
            
            # 处理URL:XPath格式和识别Figma URL
            figma_urls = []
            website_urls = []
            
            for url in urls:
                if 'figma.com' in url:
                    figma_urls.append(url)
                else:
                    # 检查是否为URL:XPath格式
                    processed_url, xpath = self._parse_url_xpath_format(url)
                    website_urls.append(processed_url)
                    if xpath:
                        parameters['xpath_selector'] = xpath
            
            if figma_urls:
                parameters['figma_url'] = figma_urls[0]
            if website_urls:
                # 选择优先级最高的website URL
                website_urls.sort(key=url_priority)
                parameters['website_url'] = website_urls[0]
            elif len(urls) == 1 and not figma_urls:
                # 单个URL且不是Figma URL
                processed_url, xpath = self._parse_url_xpath_format(urls[0])
                parameters['website_url'] = processed_url
                if xpath:
                    parameters['xpath_selector'] = xpath
        
        # 提取文档token
        doc_tokens = self._extract_document_tokens(text)
        if doc_tokens:
            parameters['document_token'] = doc_tokens[0]
        
        # 提取设备类型
        device = self._extract_device_type(text)
        if device:
            parameters['device'] = device
        
        # 提取项目名称
        project_name = self._extract_project_name(text)
        if project_name:
            parameters['project_name'] = project_name
        
        # 提取cookie
        cookies = self._extract_cookies(text)
        if cookies:
            parameters['cookies'] = cookies
        
        # 提取localStorage
        local_storage = self._extract_localstorage(text)
        if local_storage:
            parameters['local_storage'] = local_storage
        
        return parameters
    
    def _extract_urls(self, text: str) -> List[str]:
        """提取URL"""
        urls = []
        for pattern in self.parameter_extractors['url']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            urls.extend(matches)
        return list(set(urls))  # 去重
    
    def _extract_document_tokens(self, text: str) -> List[str]:
        """提取文档token"""
        tokens = []
        for pattern in self.parameter_extractors['document_token']:
            # 检查是否包含捕获组
            if '(' in pattern and ')' in pattern:
                # 包含捕获组，使用findall获取捕获的内容
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # 处理可能的元组结果（多个捕获组）
                    for match in matches:
                        if isinstance(match, tuple):
                            tokens.extend([m for m in match if m])
                        else:
                            tokens.append(match)
            else:
                # 不包含捕获组，使用findall获取完整匹配
                matches = re.findall(pattern, text, re.IGNORECASE)
                tokens.extend(matches)
        
        # 过滤掉过短的token和重复的token
        valid_tokens = [token for token in tokens if len(token) >= 15]
        return list(set(valid_tokens))
    
    def _extract_device_type(self, text: str) -> Optional[str]:
        """提取设备类型"""
        device_patterns = {
            'mobile': r'移动端|手机|mobile',
            'desktop': r'桌面端|电脑|desktop',
            'tablet': r'平板|tablet'
        }
        
        for device, pattern in device_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return device
        
        return None
    
    def _extract_project_name(self, text: str) -> Optional[str]:
        """提取项目名称"""
        patterns = [
            r'项目[：:]\s*([^\s]+)',
            r'project[：:]\s*([^\s]+)',
            r'名称[：:]\s*([^\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_cookies(self, text: str) -> Optional[str]:
        """提取cookie字符串"""
        for pattern in self.parameter_extractors['cookie']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_localstorage(self, text: str) -> Optional[Dict[str, Any]]:
        """提取localStorage对象"""
        for pattern in self.parameter_extractors['localstorage']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # 尝试解析JSON格式的localStorage
                    import json
                    local_storage_str = match.group(1).strip()
                    return json.loads(local_storage_str)
                except (json.JSONDecodeError, ValueError):
                    # 如果JSON解析失败，尝试解析简单的键值对格式
                    try:
                        # 处理简单的键值对格式，如 "key: value, key2: value2"
                        local_storage_str = match.group(1).strip()
                        result = {}
                        
                        # 移除大括号
                        if local_storage_str.startswith('{') and local_storage_str.endswith('}'):
                            local_storage_str = local_storage_str[1:-1]
                        
                        # 分割键值对
                        pairs = local_storage_str.split(',')
                        for pair in pairs:
                            if ':' in pair:
                                key, value = pair.split(':', 1)
                                key = key.strip().strip('"\'')
                                value = value.strip().strip('"\'')
                                result[key] = value
                        
                        return result if result else None
                    except:
                        return None
        return None
    
    def _parse_url_xpath_format(self, url_string: str) -> Tuple[str, Optional[str]]:
        """
        解析URL:XPath格式
        返回 (清理后的URL, XPath选择器)
        """
        # 检查是否包含XPath（URL后面跟着冒号和路径）
        # 需要跳过协议中的冒号（如https:、http:）和端口号中的冒号
        
        # 先找到协议结束的位置
        if '://' in url_string:
            protocol_end = url_string.find('://') + 3
            # 在协议后面查找冒号
            remaining = url_string[protocol_end:]
            
            # 寻找XPath分隔符（避免与端口号混淆）
            # 策略：从后往前查找最后一个符合XPath特征的冒号
            colon_positions = [i for i, char in enumerate(remaining) if char == ':']
            
            # 从后往前检查每个冒号
            for pos in reversed(colon_positions):
                xpath_part = remaining[pos + 1:]
                
                # 检查冒号后面是否看起来像XPath
                if xpath_part.startswith('/') or any(tag in xpath_part.lower() for tag in ['html', 'body', 'div', 'span', 'p', '[', ']']):
                    # 进一步验证：XPath应该不是纯数字（排除端口号）
                    if not xpath_part.replace('/', '').replace('[', '').replace(']', '').isdigit():
                        actual_colon_pos = protocol_end + pos
                        url_part = url_string[:actual_colon_pos]
                        return url_part, xpath_part
            
            # 没有找到有效的XPath分隔符
            return url_string, None
        else:
            # 没有协议的URL，从后往前查找XPath分隔符
            if ':' in url_string:
                # 从后往前查找符合XPath特征的冒号
                parts = url_string.split(':')
                for i in range(len(parts) - 1, 0, -1):
                    url_part = ':'.join(parts[:i])
                    xpath_part = ':'.join(parts[i:])
                    
                    # 检查是否为有效的XPath
                    if xpath_part.startswith('/') or any(tag in xpath_part.lower() for tag in ['html', 'body', 'div', 'span', 'p', '[', ']']):
                        if not xpath_part.replace('/', '').replace('[', '').replace(']', '').isdigit():
                            return url_part, xpath_part
                
                # 没有找到有效的XPath，返回原始URL
                return url_string, None
            else:
                return url_string, None
    
    def get_intent_examples(self) -> Dict[str, List[str]]:
        """获取意图示例"""
        return {
            "生成测试用例": [
                "帮我生成测试用例",
                "根据PRD文档生成测试用例",
                "创建测试用例 文档token: ZzVudkYQqobhj7xn19GcZ3LFnwd"
            ],
            "视觉对比": [
                "对比网站和Figma设计",
                "进行UI对比 网站: https://example.com Figma: https://figma.com/xxx",
                "视觉比较 https://example.com:/html/body/div[1] Figma: https://figma.com/xxx",
                "视觉比较 移动端"
            ],
            "完整测试": [
                "执行完整测试流程",
                "运行完整工作流",
                "全流程测试 项目: AI日历"
            ],
            "查看状态": [
                "检查测试状态",
                "查看执行进度",
                "测试进行得怎么样"
            ],
            "查看报告": [
                "查看测试报告",
                "显示最新报告",
                "测试结果如何"
            ],
            "帮助": [
                "帮助",
                "怎么使用",
                "你能做什么"
            ]
        } 