#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令执行器模块
Command Executor Module

将识别的意图转换为具体的API调用和操作
"""

import os
import sys
import logging
import concurrent.futures
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

import google.generativeai as genai

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.workflow.executor import WorkflowExecutor
from src.chat_assistant.intent_recognizer import Intent, IntentType
from src.functional_testing.test_manager import FunctionalTestManager

logger = logging.getLogger(__name__)

@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'success': self.success,
            'message': self.message,
            'timestamp': datetime.now().isoformat()
        }
        if self.data:
            result['data'] = self.data
        if self.error:
            result['error'] = self.error
        if self.execution_time:
            result['execution_time'] = self.execution_time
        return result

class CommandExecutor:
    """命令执行器"""
    
    def __init__(self):
        self.workflow_executor = None
        self._init_workflow_executor()
        
        # 初始化Gemini模型
        self.gemini_model = None
        self._init_gemini_model()
        
        # 初始化功能测试管理器
        self.functional_test_manager = FunctionalTestManager()
        
        # 默认配置
        self.default_config = {
            'app_token': os.getenv('FEISHU_APP_TOKEN'),
            'table_id': os.getenv('FEISHU_TABLE_ID'),
            'device': 'desktop',
            'output_dir': 'reports'
        }
    
    def _init_workflow_executor(self):
        """初始化工作流执行器"""
        try:
            self.workflow_executor = WorkflowExecutor()
            logger.info("工作流执行器初始化成功")
        except Exception as e:
            logger.error(f"工作流执行器初始化失败: {e}")
            self.workflow_executor = None
    
    def _init_gemini_model(self):
        """初始化Gemini模型"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY未配置，未知意图将无法使用AI对话功能")
                return
            
            genai.configure(api_key=api_key)
            
            # 尝试多个模型，按优先级排序
            model_names = [
                'gemini-1.5-flash',
                'gemini-1.5-pro', 
                'gemini-pro',
                'gemini-1.0-pro'
            ]
            
            for model_name in model_names:
                try:
                    self.gemini_model = genai.GenerativeModel(model_name)
                    logger.info(f"Gemini模型初始化成功: {model_name}")
                    break
                except Exception as e:
                    logger.warning(f"模型 {model_name} 初始化失败: {e}")
                    continue
            
            if not self.gemini_model:
                logger.error("无法初始化任何Gemini模型")
        except Exception as e:
            logger.error(f"Gemini模型初始化失败: {e}")
            self.gemini_model = None
    
    def _get_base_url(self) -> str:
        """获取基础URL，根据环境自动判断"""
        # 检查环境变量
        env_base_url = os.getenv("BASE_URL") or os.getenv("SERVER_BASE_URL")
        if env_base_url:
            return env_base_url
        
        # 检查是否是开发环境
        is_dev = self._is_development_environment()
        
        if is_dev:
            # 开发环境，检查端口
            port = os.getenv("PORT", "5001")
            return f"http://localhost:{port}"
        else:
            # 生产环境
            return "http://18.141.179.222:5001"
    
    def _is_development_environment(self) -> bool:
        """智能判断是否为开发环境"""
        # 1. 检查明确的环境变量
        if (os.getenv("FLASK_ENV") == "development" or
            os.getenv("ENVIRONMENT") == "development" or
            os.getenv("NODE_ENV") == "development"):
            return True
        
        # 2. 检查开发环境标识文件
        if os.path.exists("/.dev_environment"):
            return True
        
        # 3. 检查当前工作目录是否包含开发环境的标识
        current_dir = os.getcwd().lower()
        dev_indicators = [
            "desktop", "documents", "github", "workspace", "dev", "development",
            "local", "project", "code", "src", "home", "users"
        ]
        
        for indicator in dev_indicators:
            if indicator in current_dir:
                return True
        
        # 4. 检查是否存在开发环境的文件/目录
        dev_files = [
            "venv", ".venv", "node_modules", ".git", "requirements.txt", 
            "package.json", "Pipfile", "pyproject.toml", ".env", ".env.local"
        ]
        
        for file in dev_files:
            if os.path.exists(file):
                return True
        
        # 5. 检查Python虚拟环境
        if (os.getenv("VIRTUAL_ENV") or 
            os.getenv("CONDA_DEFAULT_ENV") or 
            hasattr(sys, 'real_prefix') or 
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
            return True
        
        # 6. 检查是否在本地网络环境中
        try:
            import socket
            hostname = socket.gethostname()
            if ("local" in hostname.lower() or 
                "dev" in hostname.lower() or 
                hostname.startswith("mac") or 
                hostname.startswith("pc")):
                return True
        except:
            pass
        
        # 默认为生产环境
        return False
    
    def execute_intent(self, intent: Intent, context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """执行意图"""
        start_time = datetime.now()
        
        try:
            # 根据意图类型选择执行方法
            if intent.type == IntentType.GENERATE_TEST_CASES:
                result = self._execute_generate_test_cases(intent, context)
            elif intent.type == IntentType.VISUAL_COMPARISON:
                result = self._execute_visual_comparison(intent, context)
            elif intent.type == IntentType.FULL_WORKFLOW:
                result = self._execute_full_workflow(intent, context)
            elif intent.type == IntentType.FUNCTIONAL_TEST:
                result = self._execute_functional_test(intent, context)
            elif intent.type == IntentType.CHECK_STATUS:
                result = self._execute_check_status(intent, context)
            elif intent.type == IntentType.VIEW_REPORTS:
                result = self._execute_view_reports(intent, context)
            elif intent.type == IntentType.LIST_PROJECTS:
                result = self._execute_list_projects(intent, context)
            elif intent.type == IntentType.HELP:
                result = self._execute_help(intent, context)
            elif intent.type == IntentType.HEALTH_CHECK:
                result = self._execute_health_check(intent, context)
            else:
                result = self._execute_unknown_intent(intent, context)
            
            # 计算执行时间
            end_time = datetime.now()
            result.execution_time = (end_time - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            logger.error(f"执行意图时发生错误: {e}")
            end_time = datetime.now()
            return ExecutionResult(
                success=False,
                message=f"执行失败: {str(e)}",
                error=str(e),
                execution_time=(end_time - start_time).total_seconds()
            )
    
    def _execute_generate_test_cases(self, intent: Intent, context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """执行生成测试用例"""
        # 检查必需参数
        doc_token = intent.parameters.get('document_token')
        if not doc_token and context:
            doc_token = context.get('document_token')
        
        if not doc_token:
            return ExecutionResult(
                success=False,
                message="需要提供PRD文档token才能生成测试用例。\n请提供文档token，例如：'生成测试用例 文档token: ZzVudkYQqobhj7xn19GcZ3LFnwd'",
                error="Missing document token"
            )
        
        if not self.workflow_executor:
            return ExecutionResult(
                success=False,
                message="工作流执行器未初始化，请检查系统配置",
                error="Workflow executor not initialized"
            )
        
        try:
            # 生成测试用例
            result = self.workflow_executor._generate_test_cases_from_prd(doc_token)
            
            return ExecutionResult(
                success=True,
                message="✅ 测试用例生成成功！",
                data={
                    'document_token': doc_token,
                    'test_cases': result.get('test_cases_text', ''),
                    'prd_length': result.get('prd_text_length', 0),
                    'generated_at': result.get('generated_at')
                }
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"生成测试用例失败: {str(e)}",
                error=str(e)
            )
    
    def _execute_visual_comparison(self, intent: Intent, context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """执行视觉对比"""
        # 检查必需参数
        figma_url = intent.parameters.get('figma_url')
        website_url = intent.parameters.get('website_url')
        xpath_selector = intent.parameters.get('xpath_selector')
        device = intent.parameters.get('device', 'desktop')
        cookies = intent.parameters.get('cookies')
        local_storage = intent.parameters.get('local_storage')
        
        if context:
            figma_url = figma_url or context.get('figma_url')
            website_url = website_url or context.get('website_url')
            xpath_selector = xpath_selector or context.get('xpath_selector')
            device = context.get('device', device)
            cookies = cookies or context.get('cookies')
            local_storage = local_storage or context.get('local_storage')
        
        if not figma_url or not website_url:
            return ExecutionResult(
                success=False,
                message="需要提供Figma URL和网站URL才能进行视觉对比。\n例如：'视觉对比 网站: https://example.com Figma: https://figma.com/xxx'\n\n**使用提示:**\n- 需要同时提供Figma URL和网站URL\n- 格式: '视觉对比 网站: https://example.com Figma: https://figma.com/xxx'\n- 或者分别提供: '对比 https://example.com 和 https://figma.com/xxx'\n- 支持XPath选择器: '视觉对比 https://example.com:/html/body/div[1] Figma: https://figma.com/xxx'\n- 可选择设备类型: 桌面端(默认)、移动端、平板端\n- 添加设备示例: '视觉对比 网站: https://example.com Figma: https://figma.com/xxx 移动端'\n- 支持Cookie注入: 'cookie: SESSION=xxx; deviceId=xxx'\n- 支持localStorage: 'localStorage: {language: \"es-ES\"}'",
                error="Missing required URLs"
            )
        
        if not self.workflow_executor:
            return ExecutionResult(
                success=False,
                message="工作流执行器未初始化，请检查系统配置",
                error="Workflow executor not initialized"
            )
        
        try:
            # 执行视觉对比
            result = self.workflow_executor._compare_figma_and_website(
                figma_url=figma_url,
                website_url=website_url,
                xpath_selector=xpath_selector,
                device=device,
                output_dir=self.default_config['output_dir'],
                cookies=cookies,
                local_storage=local_storage
            )
            
            return ExecutionResult(
                success=True,
                message="✅ 视觉对比完成！",
                data={
                    'figma_url': figma_url,
                    'website_url': website_url,
                    'xpath_selector': xpath_selector,
                    'device': device,
                    'cookies_injected': bool(cookies),
                    'localstorage_injected': bool(local_storage),
                    'similarity_score': result.get('comparison_result', {}).get('similarity_score', 0),
                    'output_directory': result.get('output_directory', ''),
                    'comparison_images': result.get('comparison_result', {}).get('diff_image_path', '')
                }
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"视觉对比失败: {str(e)}",
                error=str(e)
            )
    
    def _execute_functional_test(self, intent: Intent, context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """执行功能测试"""
        try:
            # 获取参数
            parameters = intent.parameters
            device = context.get('device', 'mobile') if context else 'mobile'
            cookies = context.get('cookies', '') if context else ''
            localStorage = context.get('localStorage', '') if context else ''
            
            # 检查是否有测试用例描述
            if 'test_description' in parameters:
                test_description = parameters['test_description']
            else:
                # 如果没有明确的测试用例描述，使用原始文本
                test_description = intent.raw_text
            
            # 提取URL
            urls = parameters.get('urls', [])
            if not urls:
                return ExecutionResult(
                    success=False,
                    message="未找到测试URL，请提供要测试的网站地址"
                )
            
            base_url = urls[0]
            
            # 创建测试配置
            config = self.functional_test_manager.create_test_config(
                base_url=base_url,
                device=device,
                cookies=cookies,
                local_storage=localStorage,
                headless=True
            )
            
            # 判断是否运行演示测试
            if any(keyword in intent.raw_text.lower() for keyword in ['demo', '演示', '示例']):
                # 运行演示测试用例
                result = self.functional_test_manager.run_demo_test(config)
            else:
                # 运行自定义测试用例
                result = self.functional_test_manager.run_test_from_description(test_description, config)
            
            if result['success']:
                message = f"🎉 功能测试执行成功！\n\n"
                message += f"📋 测试用例: {result['test_case']['name']}\n"
                message += f"📊 执行结果: {result['result']['status'].upper()}\n"
                message += f"⏱️ 耗时: {result['result']['duration']:.2f}秒\n"
                message += f"✅ 步骤通过: {result['result']['steps_passed']}/{result['test_case']['steps_count']}\n"
                message += f"🔍 断言通过: {result['result']['assertions_passed']}/{result['test_case']['assertions_count']}\n"
                
                if result['result']['error']:
                    message += f"❌ 错误信息: {result['result']['error']}\n"
                
                # 生成可点击的报告链接
                if result['report_path']:
                    base_url = self._get_base_url()
                    report_url = f"{base_url}/files/{result['report_path']}"
                    message += f"📄 详细报告: [点击查看HTML报告]({report_url})\n"
                
                # 生成可点击的截图链接
                if result['screenshots']:
                    base_url = self._get_base_url()
                    message += f"📸 截图: {len(result['screenshots'])} 张\n"
                    for i, screenshot in enumerate(result['screenshots'], 1):
                        screenshot_url = f"{base_url}/files/{screenshot}"
                        message += f"   • [截图 {i}]({screenshot_url})\n"
                
                return ExecutionResult(
                    success=True,
                    message=message,
                    data=result
                )
            else:
                return ExecutionResult(
                    success=False,
                    message=f"功能测试执行失败: {result['error']}",
                    error=result.get('error', ''),
                    data=result
                )
                
        except Exception as e:
            logger.error(f"功能测试执行失败: {e}")
            return ExecutionResult(
                success=False,
                message=f"功能测试执行失败: {str(e)}",
                error=str(e)
            )
    
    def _execute_full_workflow(self, intent: Intent, context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """执行完整工作流"""
        # 检查必需参数
        doc_token = intent.parameters.get('document_token')
        figma_url = intent.parameters.get('figma_url')
        website_url = intent.parameters.get('website_url')
        device = intent.parameters.get('device', 'desktop')
        
        if context:
            doc_token = doc_token or context.get('document_token')
            figma_url = figma_url or context.get('figma_url')
            website_url = website_url or context.get('website_url')
            device = context.get('device', device)
        
        # 验证必需参数
        missing_params = []
        if not doc_token:
            missing_params.append('PRD文档token')
        if not figma_url:
            missing_params.append('Figma URL')
        if not website_url:
            missing_params.append('网站URL')
        
        if missing_params:
            return ExecutionResult(
                success=False,
                message=f"完整工作流需要以下参数: {', '.join(missing_params)}",
                error="Missing required parameters"
            )
        
        if not self.workflow_executor:
            return ExecutionResult(
                success=False,
                message="工作流执行器未初始化，请检查系统配置",
                error="Workflow executor not initialized"
            )
        
        try:
            # 执行完整工作流
            result = self.workflow_executor.execute_button_click(
                app_token=self.default_config['app_token'],
                table_id=self.default_config['table_id'],
                record_id=None,  # 在聊天模式下不更新多维表格
                prd_document_token=doc_token,
                figma_url=figma_url,
                website_url=website_url,
                device=device,
                output_dir=self.default_config['output_dir']
            )
            
            return ExecutionResult(
                success=True,
                message="✅ 完整工作流执行成功！",
                data={
                    'execution_id': result.get('output_directory', '').split('/')[-1],
                    'document_token': doc_token,
                    'figma_url': figma_url,
                    'website_url': website_url,
                    'device': device,
                    'test_cases_generated': result.get('test_cases_generated', False),
                    'comparison_result': result.get('comparison_result', {})
                }
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"完整工作流执行失败: {str(e)}",
                error=str(e)
            )
    
    def _execute_check_status(self, intent: Intent, context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """检查状态"""
        try:
            # 检查系统状态
            status_info = {
                'system_status': 'healthy',
                'workflow_executor': 'initialized' if self.workflow_executor else 'not_initialized',
                'reports_directory': os.path.exists('reports'),
                'recent_reports': self._get_recent_reports()
            }
            
            return ExecutionResult(
                success=True,
                message="📊 系统状态检查完成",
                data=status_info
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"状态检查失败: {str(e)}",
                error=str(e)
            )
    
    def _execute_view_reports(self, intent: Intent, context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """查看报告"""
        try:
            reports = self._get_recent_reports(limit=5)
            
            if not reports:
                return ExecutionResult(
                    success=True,
                    message="暂无测试报告",
                    data={'reports': []}
                )
            
            return ExecutionResult(
                success=True,
                message=f"📋 找到 {len(reports)} 个最近的测试报告",
                data={'reports': reports}
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"查看报告失败: {str(e)}",
                error=str(e)
            )
    
    def _execute_list_projects(self, intent: Intent, context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """列出项目"""
        try:
            projects = self._get_project_list()
            
            return ExecutionResult(
                success=True,
                message=f"📁 找到 {len(projects)} 个项目",
                data={'projects': projects}
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"获取项目列表失败: {str(e)}",
                error=str(e)
            )
    
    def _execute_help(self, intent: Intent, context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """显示帮助"""
        help_text = """
🤖 自动化测试助手帮助

我可以帮您执行以下操作：

📝 **生成测试用例**
- "生成测试用例 文档token: ZzVudkYQqobhj7xn19GcZ3LFnwd"
- "根据PRD文档生成测试用例"

🎨 **视觉对比**
- "视觉对比 网站: https://example.com:XPath Figma: https://figma.com/xxx"
- "UI对比 移动端" - 支持设备类型选择
- 支持XPath选择器: "https://example.com:/html/body/div[1] 对比 Figma: https://figma.com/xxx"
- 支持的设备类型: 桌面端(默认)、移动端、平板端
- 可在界面上方选择设备类型，或在命令中指定

🔄 **完整工作流**
- "执行完整测试流程"
- "运行完整工作流"

📊 **查看信息**
- "检查状态" - 查看系统状态
- "查看报告" - 查看最近的测试报告
- "列出项目" - 显示项目列表

💡 **使用技巧**
- 可以在对话中提供URL、文档token等参数
- 支持中英文输入
- 可以组合使用多个参数
        """
        
        return ExecutionResult(
            success=True,
            message=help_text.strip(),
            data={
                'available_commands': [
                    'generate_test_cases',
                    'visual_comparison',
                    'full_workflow',
                    'check_status',
                    'view_reports',
                    'list_projects',
                    'help'
                ]
            }
        )
    
    def _execute_health_check(self, intent: Intent, context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """健康检查"""
        try:
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'workflow_executor': self.workflow_executor is not None,
                    'reports_directory': os.path.exists('reports'),
                    'environment_config': bool(os.getenv('FEISHU_APP_ID')),
                }
            }
            
            all_healthy = all(health_status['components'].values())
            
            return ExecutionResult(
                success=all_healthy,
                message="✅ 系统健康状况良好" if all_healthy else "⚠️ 系统存在一些问题",
                data=health_status
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"健康检查失败: {str(e)}",
                error=str(e)
            )
    
    def _get_recent_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的报告"""
        reports = []
        reports_dir = 'reports'
        
        if not os.path.exists(reports_dir):
            return reports
        
        try:
            for item in os.listdir(reports_dir):
                item_path = os.path.join(reports_dir, item)
                if os.path.isdir(item_path):
                    # 获取目录信息
                    stat = os.stat(item_path)
                    reports.append({
                        'name': item,
                        'path': item_path,
                        'created_time': stat.st_mtime,
                        'created_datetime': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # 按创建时间排序
            reports.sort(key=lambda x: x['created_time'], reverse=True)
            return reports[:limit]
            
        except Exception as e:
            logger.error(f"获取报告列表失败: {e}")
            return []
    
    def _get_project_list(self) -> List[Dict[str, Any]]:
        """获取项目列表"""
        projects = []
        
        # 从报告目录获取项目信息
        reports = self._get_recent_reports(limit=50)
        project_names = set()
        
        for report in reports:
            # 从报告名称中提取项目信息
            name = report['name']
            if name.startswith('comparison_'):
                project_names.add('Visual Comparison')
            elif name.startswith('test_cases_'):
                project_names.add('Test Cases Generation')
            else:
                project_names.add(name)
        
        for name in project_names:
            projects.append({
                'name': name,
                'type': 'automated_test',
                'last_activity': datetime.now().isoformat()
            })
        
        return projects 
    
    def _execute_unknown_intent(self, intent: Intent, context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """处理未知意图，使用Gemini AI进行对话"""
        if not self.gemini_model:
            return ExecutionResult(
                success=False,
                message="抱歉，我不理解您的意图。请尝试使用更具体的描述，或者输入'帮助'查看可用功能。",
                error="Gemini model not initialized"
            )
        
        try:
            # 构建对话提示
            prompt = f"""
你是一个专业的自动化测试助手，主要帮助用户进行软件测试相关的工作。

用户问题: {intent.raw_text}

请根据你的专业知识回答用户的问题。如果问题与软件测试、UI测试、自动化测试相关，请提供专业的建议。如果是其他技术问题，也可以尽力解答。

回答要求:
1. 用输入语同样的语言来回答
2. 内容要专业准确
3. 如果涉及测试工具或方法，可以提供具体建议
4. 保持友好和乐于助人的语气
5. 如果问题不清楚，可以询问更多细节

请直接回答，不需要额外的格式或前缀。
"""
            
            # 调用Gemini API
            logger.info(f"使用Gemini处理未知意图: {intent.raw_text}")
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._call_gemini_api, prompt)
                try:
                    response = future.result(timeout=30)  # 30秒超时
                    
                    return ExecutionResult(
                        success=True,
                        message=response,
                        data={
                            'ai_response': True,
                            'original_query': intent.raw_text,
                            'response_type': 'gemini_chat'
                        }
                    )
                except concurrent.futures.TimeoutError:
                    return ExecutionResult(
                        success=False,
                        message="AI响应超时，请稍后再试。如果需要具体功能帮助，请输入'帮助'查看可用命令。",
                        error="Gemini API timeout"
                    )
        
        except Exception as e:
            logger.error(f"Gemini对话失败: {e}")
            return ExecutionResult(
                success=False,
                message="抱歉，AI对话功能暂时不可用。请尝试使用更具体的描述，或者输入'帮助'查看可用功能。",
                error=str(e)
            )
    
    def _call_gemini_api(self, prompt: str) -> str:
        """调用Gemini API"""
        response = self.gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1024,
                temperature=0.7,
            )
        )
        return response.text