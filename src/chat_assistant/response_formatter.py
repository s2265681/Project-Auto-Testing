#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
响应格式化器模块
Response Formatter Module

将执行结果转换为自然语言回复
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.chat_assistant.command_executor import ExecutionResult
from src.chat_assistant.intent_recognizer import IntentType

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """响应格式化器"""
    
    def __init__(self):
        self.emoji_map = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'processing': '⏳',
            'completed': '🎉',
            'report': '📋',
            'chart': '📊',
            'folder': '📁',
            'robot': '🤖',
            'tool': '🔧',
            'test': '🧪',
            'design': '🎨',
            'web': '🌐',
            'document': '📄',
            'clock': '⏰',
            'star': '⭐',
            'arrow': '➡️',
            'check': '✔️',
            'cross': '✖️',
            'image': '🖼️'
        }
    
    def format_response(self, result: ExecutionResult, intent_type: IntentType, 
                       context: Optional[Dict[str, Any]] = None) -> str:
        """格式化响应消息"""
        try:
            if result.success:
                return self._format_success_response(result, intent_type, context)
            else:
                return self._format_error_response(result, intent_type, context)
        except Exception as e:
            logger.error(f"格式化响应失败: {e}")
            return f"{self.emoji_map['error']} 响应格式化失败: {str(e)}"
    
    def _format_success_response(self, result: ExecutionResult, intent_type: IntentType, 
                                context: Optional[Dict[str, Any]]) -> str:
        """格式化成功响应"""
        if intent_type == IntentType.GENERATE_TEST_CASES:
            return self._format_test_cases_response(result)
        elif intent_type == IntentType.VISUAL_COMPARISON:
            return self._format_visual_comparison_response(result)
        elif intent_type == IntentType.FULL_WORKFLOW:
            return self._format_full_workflow_response(result)
        elif intent_type == IntentType.CHECK_STATUS:
            return self._format_status_response(result)
        elif intent_type == IntentType.VIEW_REPORTS:
            return self._format_reports_response(result)
        elif intent_type == IntentType.LIST_PROJECTS:
            return self._format_projects_response(result)
        elif intent_type == IntentType.HEALTH_CHECK:
            return self._format_health_check_response(result)
        elif intent_type == IntentType.HELP:
            return result.message  # 帮助消息已经格式化好了
        else:
            return f"{self.emoji_map['success']} {result.message}"
    
    def _format_error_response(self, result: ExecutionResult, intent_type: IntentType, 
                              context: Optional[Dict[str, Any]]) -> str:
        """格式化错误响应"""
        # 判断是否为参数缺失的提示性错误
        is_parameter_missing = any([
            "document token" in result.error.lower() if result.error else False,
            "需要提供" in result.message.lower(),
            "缺少" in result.message.lower(),
            "missing" in result.error.lower() if result.error else False,
            "url" in result.error.lower() if result.error else False,
            "参数" in result.message.lower(),
        ])
        
        # 对于参数缺失使用警告图标，真正的错误使用错误图标
        icon = self.emoji_map['warning'] if is_parameter_missing else self.emoji_map['error']
        base_message = f"{icon} {result.message}"
        
        # 添加特定的错误处理建议
        if intent_type == IntentType.GENERATE_TEST_CASES:
            if "document token" in result.error.lower() if result.error else False:
                base_message += "\n\n💡 **使用提示:**\n"
                base_message += "- 请提供有效的PRD文档token\n"
                base_message += "- 格式: '生成测试用例 文档token: ZzVudkYQqobhj7xn19GcZ3LFnwd'\n"
                base_message += "- 或者: '根据文档 ZzVudkYQqobhj7xn19GcZ3LFnwd 生成测试用例'"
        
        elif intent_type == IntentType.VISUAL_COMPARISON:
            if "url" in result.error.lower() if result.error else False:
                base_message += "\n\n💡 **使用提示:**\n"
                base_message += "- 需要同时提供Figma URL和网站URL\n"
                base_message += "- 格式: '视觉对比 网站: https://example.com:XPath Figma: https://figma.com/xxx'\n"
                base_message += "- 或者分别提供: '对比 https://example.com 和 https://figma.com/xxx'"
        
        elif intent_type == IntentType.FULL_WORKFLOW:
            if "missing" in result.error.lower() if result.error else False:
                base_message += "\n\n💡 **使用提示:**\n"
                base_message += "- 完整工作流需要：PRD文档token、Figma URL、网站URL\n"
                base_message += "- 您可以逐步提供这些信息\n"
                base_message += "- 或者一次性提供: '完整测试 文档:XXX 网站:XXX Figma:XXX'"
        
        # 添加执行时间信息
        if result.execution_time:
            base_message += f"\n\n{self.emoji_map['clock']} 执行时间: {result.execution_time:.2f}秒"
        
        return base_message
    
    def _format_test_cases_response(self, result: ExecutionResult) -> str:
        """格式化测试用例生成响应"""
        data = result.data or {}
        
        response = f"{self.emoji_map['success']} **测试用例生成成功！**\n\n"
        
        # 基本信息
        response += f"{self.emoji_map['document']} **文档信息:**\n"
        response += f"- 文档Token: `{data.get('document_token', 'N/A')}`\n"
        response += f"- PRD文档长度: {data.get('prd_length', 0)} 字符\n"
        response += f"- 生成时间: {data.get('generated_at', 'N/A')}\n\n"
        
        # 测试用例内容 - 不包装在代码块中，让markdown表格正常渲染
        test_cases = data.get('test_cases', '')
        if test_cases:
            response += f"{self.emoji_map['test']} **生成的测试用例:**\n\n"
            
            # 检查内容长度，决定是否截断
            if len(test_cases) > 3000:
                response += test_cases[:3000] + "\n\n... (内容已截断，完整内容已保存)\n\n"
            else:
                response += test_cases + "\n\n"
        
        # 执行时间
        if result.execution_time:
            response += f"{self.emoji_map['clock']} 执行时间: {result.execution_time:.2f}秒"
        
        return response
    
    def _format_visual_comparison_response(self, result: ExecutionResult) -> str:
        """格式化视觉对比响应"""
        data = result.data or {}
        
        response = f"{self.emoji_map['success']} **视觉对比完成！**\n\n"
        
        # 基本信息
        response += f"{self.emoji_map['info']} **对比信息:**\n"
        response += f"- 网站: {data.get('website_url', 'N/A')}\n"
        if data.get('xpath_selector'):
            response += f"- XPath选择器: `{data.get('xpath_selector')}`\n"
        response += f"- Figma: {data.get('figma_url', 'N/A')}\n"
        response += f"- 设备: {data.get('device', 'desktop')}\n\n"
        
        # 读取完整报告内容
        output_dir = data.get('output_directory', '')
        report_content = self._read_comparison_report(output_dir)
        
        if report_content:
            # 详细相似度分析
            comparison_result = report_content.get('comparison_result', {})
            if comparison_result:
                response += f"{self.emoji_map['chart']} **详细分析结果:**\n"
                response += f"- 相似度得分: {comparison_result.get('similarity_score', 0):.4f}\n"
                response += f"- SSIM (结构相似性): {comparison_result.get('ssim_score', 0):.4f}\n"
                response += f"- MSE (均方误差): {comparison_result.get('mse_score', 0):.2f}\n"
                response += f"- 哈希距离: {comparison_result.get('hash_distance', 0)}\n"
                response += f"- 差异区域数: {comparison_result.get('differences_count', 0)}\n"
                
                # 评级
                overall_rating = comparison_result.get('overall_rating', '未知')
                response += f"- 总体评级: **{overall_rating}**\n\n"
            
            # 差异分析
            analysis = report_content.get('analysis', {})
            if analysis:
                response += f"{self.emoji_map['tool']} **差异分析:**\n"
                response += f"- 图像尺寸: {analysis.get('image_dimensions', {}).get('width', 'N/A')} x {analysis.get('image_dimensions', {}).get('height', 'N/A')}\n"
                response += f"- 差异面积: {analysis.get('total_diff_area', 0)} 像素\n"
                response += f"- 差异占比: {analysis.get('diff_percentage', 0):.2f}%\n"
                
                # 颜色分析
                color_analysis = analysis.get('color_analysis', {})
                if color_analysis:
                    response += f"- 最大颜色差异: {color_analysis.get('max_color_diff', 0):.2f}\n"
                
                response += "\n"
            
            # 建议
            recommendations = report_content.get('recommendations', [])
            if recommendations:
                response += f"{self.emoji_map['warning']} **改进建议:**\n"
                for i, rec in enumerate(recommendations, 1):
                    response += f"{i}. {rec}\n"
                response += "\n"
            
            # 图片展示 - 使用markdown语法直接显示图片
            diff_image_path = report_content.get('diff_image_path')
            if diff_image_path and os.path.exists(diff_image_path):
                # 转换为可访问的URL
                image_url = self._convert_to_accessible_url(diff_image_path)
                if image_url:
                    response += f"{self.emoji_map['image']} **对比图像:**\n\n"
                    response += f"![差异对比图]({image_url})\n\n"
                else:
                    response += f"{self.emoji_map['image']} **对比图像:**\n\n"
                    response += f"🖼️ 图片加载失败: 差异对比图\n\n"
            
            # 输出结果 - 显示所有文件的可点击链接
            if output_dir and os.path.exists(output_dir):
                response += f"{self.emoji_map['document']} **输出结果:**\n\n"
                
                # 按文件类型分组显示
                json_files = []
                image_files = []
                other_files = []
                
                for file in os.listdir(output_dir):
                    file_path = os.path.join(output_dir, file)
                    file_url = self._convert_to_accessible_url(file_path)
                    if file_url:
                        if file.endswith('.json') and 'report' in file.lower():
                            json_files.append((file, file_url))
                        elif file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                            image_files.append((file, file_url))
                        else:
                            other_files.append((file, file_url))
                
                # 显示报告文件
                if json_files:
                    for file, file_url in json_files:
                        response += f"📋 [报告链接]({file_url}) - {file}\n"
                
                # 显示图片文件
                if image_files:
                    for file, file_url in image_files:
                        if 'diff_comparison' in file:
                            response += f"📊 [差异对比图]({file_url}) - {file}\n"
                        elif 'diff_only' in file:
                            response += f"🔍 [差异区域图]({file_url}) - {file}\n"
                        elif 'website' in file:
                            response += f"📱 [网站截图]({file_url}) - {file}\n"
                        elif 'figma' in file:
                            response += f"🎨 [Figma设计图]({file_url}) - {file}\n"
                        else:
                            response += f"🖼️ [图片文件]({file_url}) - {file}\n"
                
                # 显示其他文件
                if other_files:
                    for file, file_url in other_files:
                        response += f"📄 [文件]({file_url}) - {file}\n"
                
                response += "\n"
        
        else:
            # 如果无法读取详细报告，显示基本信息
            similarity_score = data.get('similarity_score', 0)
            if similarity_score > 0:
                response += f"{self.emoji_map['chart']} **相似度分析:**\n"
                response += f"- 相似度得分: {similarity_score:.3f}\n"
                
                # 相似度评级
                if similarity_score >= 0.95:
                    response += f"- 评级: {self.emoji_map['star']} 优秀 (几乎完全一致)\n"
                elif similarity_score >= 0.85:
                    response += f"- 评级: {self.emoji_map['check']} 良好 (高度相似)\n"
                elif similarity_score >= 0.70:
                    response += f"- 评级: {self.emoji_map['warning']} 一般 (存在差异)\n"
                else:
                    response += f"- 评级: {self.emoji_map['cross']} 较差 (差异较大)\n"
                
                response += "\n"
        
        # 执行时间
        if result.execution_time:
            response += f"{self.emoji_map['clock']} 执行时间: {result.execution_time:.2f}秒"
        
        return response
    
    def _read_comparison_report(self, output_dir: str) -> Optional[Dict[str, Any]]:
        """读取对比报告文件内容"""
        if not output_dir:
            return None
        
        try:
            # 查找报告文件
            report_files = []
            if os.path.exists(output_dir):
                for file in os.listdir(output_dir):
                    if file.endswith('.json') and 'report' in file.lower():
                        report_files.append(os.path.join(output_dir, file))
            
            if not report_files:
                return None
            
            # 读取最新的报告文件
            latest_report = max(report_files, key=os.path.getmtime)
            
            with open(latest_report, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"读取报告文件失败: {e}")
            return None
    
    def _convert_to_accessible_url(self, file_path: str, base_url: str = None) -> Optional[str]:
        """将本地文件路径转换为可访问的完整URL"""
        if not file_path:
            logger.warning("文件路径为空")
            return None
            
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return None
        
        try:
            # 获取相对于项目根目录的路径
            project_root = os.getcwd()
            
            # 如果file_path已经是相对路径，直接使用
            if not os.path.isabs(file_path):
                rel_path = file_path
            else:
                rel_path = os.path.relpath(file_path, project_root)
            
            # 将Windows路径分隔符转换为URL格式
            url_path = rel_path.replace('\\', '/')
            
            # 动态获取base_url
            if not base_url:
                try:
                    # 尝试从Flask request中获取当前的host和scheme
                    from flask import request, has_request_context
                    if has_request_context():
                        base_url = f"{request.scheme}://{request.host}"
                        logger.info(f"从Flask request获取base_url: {base_url}")
                    else:
                        # 没有request上下文时的fallback
                        base_url = self._get_fallback_base_url()
                        logger.info(f"使用fallback base_url: {base_url}")
                except ImportError:
                    # Flask不可用时的fallback
                    base_url = self._get_fallback_base_url()
                    logger.info(f"Flask不可用，使用fallback base_url: {base_url}")
            
            # 确保base_url不以斜杠结尾
            base_url = base_url.rstrip('/')
            
            # 构建完整URL (使用静态文件服务路径)
            final_url = f"{base_url}/files/{url_path}"
            
            logger.info(f"URL转换: {file_path} -> {final_url}")
            return final_url
            
        except Exception as e:
            logger.error(f"路径转换失败: {file_path} - {e}")
            return None
    
    def _get_fallback_base_url(self) -> str:
        """获取fallback的base URL"""
        # 优先从环境变量获取
        env_url = os.getenv('SERVER_BASE_URL')
        if env_url:
            return env_url
        
        # 检查是否在本地开发环境
        if self._is_local_development():
            return 'http://localhost:5001'
        
        # 生产环境默认值
        return 'http://18.141.179.222:5001'
    
    def _is_local_development(self) -> bool:
        """检查是否在本地开发环境"""
        # 检查常见的本地开发环境指标
        local_indicators = [
            os.getenv('FLASK_ENV') == 'development',
            os.getenv('ENVIRONMENT') == 'local',
            os.getenv('DEBUG') == 'True',
            # 检查是否在常见的本地开发路径
            any(path in os.getcwd().lower() for path in ['desktop', 'documents', 'github', 'workspace', 'dev']),
        ]
        
        return any(local_indicators)
    
    def _format_full_workflow_response(self, result: ExecutionResult) -> str:
        """格式化完整工作流响应"""
        data = result.data or {}
        
        response = f"{self.emoji_map['completed']} **完整工作流执行成功！**\n\n"
        
        # 基本信息
        response += f"{self.emoji_map['info']} **执行信息:**\n"
        response += f"- 执行ID: `{data.get('execution_id', 'N/A')}`\n"
        response += f"- 文档Token: `{data.get('document_token', 'N/A')}`\n"
        response += f"- 网站: {data.get('website_url', 'N/A')}\n"
        response += f"- Figma: {data.get('figma_url', 'N/A')}\n"
        response += f"- 设备: {data.get('device', 'desktop')}\n\n"
        
        # 执行结果
        response += f"{self.emoji_map['chart']} **执行结果:**\n"
        
        # 测试用例生成
        test_cases_generated = data.get('test_cases_generated', False)
        if test_cases_generated:
            response += f"- {self.emoji_map['check']} 测试用例生成: 成功\n"
        else:
            response += f"- {self.emoji_map['cross']} 测试用例生成: 失败\n"
        
        # 视觉对比
        comparison_result = data.get('comparison_result', {})
        if comparison_result:
            similarity_score = comparison_result.get('similarity_score', 0)
            if similarity_score > 0:
                response += f"- {self.emoji_map['check']} 视觉对比: 成功 (相似度: {similarity_score:.3f})\n"
            else:
                response += f"- {self.emoji_map['cross']} 视觉对比: 失败\n"
        
        response += "\n"
        
        # 执行时间
        if result.execution_time:
            response += f"{self.emoji_map['clock']} 总执行时间: {result.execution_time:.2f}秒"
        
        return response
    
    def _format_status_response(self, result: ExecutionResult) -> str:
        """格式化状态检查响应"""
        data = result.data or {}
        
        response = f"{self.emoji_map['info']} **系统状态检查**\n\n"
        
        # 系统状态
        system_status = data.get('system_status', 'unknown')
        if system_status == 'healthy':
            response += f"- {self.emoji_map['check']} 系统状态: 健康\n"
        else:
            response += f"- {self.emoji_map['warning']} 系统状态: {system_status}\n"
        
        # 工作流执行器状态
        workflow_executor = data.get('workflow_executor', 'unknown')
        if workflow_executor == 'initialized':
            response += f"- {self.emoji_map['check']} 工作流执行器: 已初始化\n"
        else:
            response += f"- {self.emoji_map['cross']} 工作流执行器: 未初始化\n"
        
        # 报告目录
        reports_dir = data.get('reports_directory', False)
        if reports_dir:
            response += f"- {self.emoji_map['check']} 报告目录: 存在\n"
        else:
            response += f"- {self.emoji_map['cross']} 报告目录: 不存在\n"
        
        # 最近的报告
        recent_reports = data.get('recent_reports', [])
        if recent_reports:
            response += f"- {self.emoji_map['report']} 最近报告: {len(recent_reports)} 个\n"
        else:
            response += f"- {self.emoji_map['info']} 最近报告: 暂无\n"
        
        return response
    
    def _format_reports_response(self, result: ExecutionResult) -> str:
        """格式化报告查看响应"""
        data = result.data or {}
        reports = data.get('reports', [])
        
        if not reports:
            return f"{self.emoji_map['info']} 暂无测试报告"
        
        response = f"{self.emoji_map['report']} **最近的测试报告**\n\n"
        
        for i, report in enumerate(reports[:5], 1):
            response += f"{i}. **{report['name']}**\n"
            response += f"   - 路径: `{report['path']}`\n"
            response += f"   - 创建时间: {report['created_datetime']}\n\n"
        
        if len(reports) > 5:
            response += f"... 还有 {len(reports) - 5} 个报告未显示"
        
        return response
    
    def _format_projects_response(self, result: ExecutionResult) -> str:
        """格式化项目列表响应"""
        data = result.data or {}
        projects = data.get('projects', [])
        
        if not projects:
            return f"{self.emoji_map['info']} 暂无项目"
        
        response = f"{self.emoji_map['folder']} **项目列表**\n\n"
        
        for i, project in enumerate(projects, 1):
            response += f"{i}. **{project['name']}**\n"
            response += f"   - 类型: {project['type']}\n"
            response += f"   - 最后活动: {project['last_activity']}\n\n"
        
        return response
    
    def _format_health_check_response(self, result: ExecutionResult) -> str:
        """格式化健康检查响应"""
        data = result.data or {}
        
        response = f"{self.emoji_map['tool']} **系统健康检查**\n\n"
        
        # 整体状态
        status = data.get('status', 'unknown')
        timestamp = data.get('timestamp', 'N/A')
        
        if status == 'healthy':
            response += f"{self.emoji_map['check']} 系统状态: 健康\n"
        else:
            response += f"{self.emoji_map['warning']} 系统状态: {status}\n"
        
        response += f"{self.emoji_map['clock']} 检查时间: {timestamp}\n\n"
        
        # 组件状态
        components = data.get('components', {})
        if components:
            response += f"{self.emoji_map['info']} **组件状态:**\n"
            for component, status in components.items():
                if status:
                    response += f"- {self.emoji_map['check']} {component}: 正常\n"
                else:
                    response += f"- {self.emoji_map['cross']} {component}: 异常\n"
        
        return response
    
    def format_conversation_summary(self, summary: Dict[str, Any]) -> str:
        """格式化对话摘要"""
        response = f"{self.emoji_map['robot']} **对话摘要**\n\n"
        
        response += f"- 会话ID: `{summary.get('session_id', 'N/A')}`\n"
        response += f"- 消息数量: {summary.get('message_count', 0)}\n"
        response += f"- 上下文状态: {'有效' if summary.get('context_valid') else '无效'}\n"
        response += f"- 最后活动: {summary.get('last_activity', 'N/A')}\n"
        
        # 当前参数
        parameters = summary.get('parameters', {})
        if parameters:
            response += f"\n{self.emoji_map['info']} **当前参数:**\n"
            for key, value in parameters.items():
                response += f"- {key}: `{value}`\n"
        
        return response 