"""
工作流执行器 - 整合PRD解析、测试用例生成和视觉比较功能
Workflow Executor - Integrating PRD parsing, test case generation and visual comparison
"""
import os
import time
import json
import sys
import signal
import psutil
import threading
import shutil
from typing import Dict, List, Any, Optional
from ..utils.logger import get_logger
from ..feishu.client import FeishuClient
from ..ai_analysis.gemini_case_generator import GeminiCaseGenerator
from ..screenshot.capture import ScreenshotCapture
from ..figma.client import FigmaClient
from ..visual_comparison.comparator import VisualComparator

# 导入环境配置
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from config.environment import get_api_base_url
except ImportError:
    # 如果环境配置不可用，则使用默认值
    def get_api_base_url():
        return "http://localhost:5001"

logger = get_logger(__name__)

class TimeoutException(Exception):
    """超时异常"""
    pass

class WorkflowTimeoutHandler:
    """工作流超时处理器"""
    
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        self.timer = None
        
    def __enter__(self):
        """进入上下文管理器"""
        def timeout_handler():
            logger.error(f"工作流执行超时 ({self.timeout_seconds}秒)")
            raise TimeoutException(f"工作流执行超时 ({self.timeout_seconds}秒)")
        
        self.timer = threading.Timer(self.timeout_seconds, timeout_handler)
        self.timer.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        if self.timer:
            self.timer.cancel()

def get_image_url(file_path, base_url=None):
    """
    获取图片的可访问URL
    Get accessible URL for image files
    """
    if not file_path or not os.path.exists(file_path):
        return None
    
    # 如果没有指定base_url，则从环境配置获取
    if base_url is None:
        base_url = get_api_base_url()
    
    # 获取相对于项目根目录的路径
    project_root = os.getcwd()
    try:
        rel_path = os.path.relpath(file_path, project_root)
        # 将Windows路径分隔符转换为URL格式
        url_path = rel_path.replace('\\', '/')
        return f"{base_url.rstrip('/')}/files/{url_path}"
    except Exception as e:
        logger.warning(f"路径转换失败: {e}")
        return None

class WorkflowExecutor:
    """工作流执行器 Workflow Executor"""
    
    # 执行超时设置 (已优化减少等待时间)
    MAX_EXECUTION_TIME = 180   # 3分钟总超时 (从5分钟减少)
    MAX_SCREENSHOT_TIME = 60   # 1分钟截图超时 (从2分钟减少)
    MAX_AI_GENERATION_TIME = 120  # 2分钟AI生成超时 (从3分钟减少)
    MAX_COMPARISON_TIME = 30   # 30秒比较超时 (从1分钟减少)
    
    def __init__(self):
        """初始化执行器 Initialize executor"""
        self.feishu_client = FeishuClient()
        self.gemini_generator = GeminiCaseGenerator()
        self.screenshot_capture = None  # 延迟初始化以节省内存
        self.figma_client = None       # 延迟初始化以节省内存
        self.visual_comparator = None  # 延迟初始化以节省内存
        
        # 资源监控
        self.process = psutil.Process()
        self.start_memory = None
        
    def _log_resource_usage(self, stage: str):
        """记录资源使用情况"""
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent()
            
            if self.start_memory is None:
                self.start_memory = memory_mb
            
            memory_increase = memory_mb - self.start_memory
            
            logger.info(f"[{stage}] 内存: {memory_mb:.1f}MB (+{memory_increase:.1f}MB), CPU: {cpu_percent:.1f}%")
            
            # 内存使用警告和限制
            if memory_mb > 1024:  # 1GB
                logger.warning(f"内存使用过高: {memory_mb:.1f}MB")
                # 强制垃圾回收以释放内存
                import gc
                gc.collect()
                logger.info("已执行垃圾回收以释放内存")
            
            # 严重内存警告
            if memory_mb > 2048:  # 2GB
                logger.error(f"内存使用严重过高: {memory_mb:.1f}MB，建议优化或增加内存")
                # 清理所有组件
                self._cleanup_component('screenshot_capture')
                self._cleanup_component('figma_client')
                self._cleanup_component('visual_comparator')
                
        except Exception as e:
            logger.warning(f"资源监控失败: {e}")
    
    def _initialize_component_if_needed(self, component_name: str):
        """按需初始化组件以节省内存"""
        if component_name == 'screenshot_capture' and self.screenshot_capture is None:
            logger.info("初始化截图捕获器")
            self.screenshot_capture = ScreenshotCapture()
            
        elif component_name == 'figma_client' and self.figma_client is None:
            logger.info("初始化Figma客户端")
            self.figma_client = FigmaClient()
            
        elif component_name == 'visual_comparator' and self.visual_comparator is None:
            logger.info("初始化视觉比较器")
            self.visual_comparator = VisualComparator()
    
    def _cleanup_component(self, component_name: str):
        """清理组件以释放内存"""
        if component_name == 'screenshot_capture' and self.screenshot_capture:
            try:
                # 确保浏览器进程被清理
                self.screenshot_capture._cleanup_processes()
                self.screenshot_capture = None
                logger.info("已清理截图捕获器")
            except Exception as e:
                logger.warning(f"清理截图捕获器失败: {e}")
                
        elif component_name == 'figma_client' and self.figma_client:
            self.figma_client = None
            logger.info("已清理Figma客户端")
            
        elif component_name == 'visual_comparator' and self.visual_comparator:
            self.visual_comparator = None
            logger.info("已清理视觉比较器")
        
        # 强制垃圾回收
        import gc
        gc.collect()
    
    def _cleanup_old_reports(self, reports_dir: str):
        """
        每次视觉对比前，清空 reports 目录下所有 comparison_* 文件夹，保证只保留本次新生成的一个
        """
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir, exist_ok=True)
            return

        # 找到所有 comparison_ 开头的文件夹，全部删除
        comparison_dirs = [
            os.path.join(reports_dir, d)
            for d in os.listdir(reports_dir)
            if d.startswith("comparison_") and os.path.isdir(os.path.join(reports_dir, d))
        ]
        for old_dir in comparison_dirs:
            try:
                shutil.rmtree(old_dir)
            except Exception as e:
    
                logger.warning(f"删除旧对比目录失败: {old_dir}, {e}")
    
    def execute_button_click(self, 
                           app_token: str,
                           table_id: str, 
                           record_id: str,
                           prd_document_token: str,
                           figma_url: str,
                           website_url: str,
                           xpath_selector: str = None,  # 改为XPath选择器
                           device: str = "desktop",
                           output_dir: str = "reports",
                           test_type: str = "完整测试") -> Dict[str, Any]:
        """
        执行飞书多维表格按钮点击的工作流
        Execute workflow for Feishu multidimensional table button click
        
        Args:
            app_token: 应用token app token
            table_id: 数据表ID table ID  
            record_id: 记录ID record ID
            prd_document_token: PRD文档token PRD document token
            figma_url: Figma设计稿URL Figma design URL
            website_url: 网站URL website URL
            xpath_selector: XPath选择器 XPath selector (optional)
            device: 设备类型 device type
            output_dir: 输出目录 output directory
            test_type: 测试类型 test type ("功能测试", "UI测试", "完整测试")
            
        Returns:
            执行结果 execution result
        """
        logger.info(f"开始执行工作流 / Starting workflow execution - 测试类型: {test_type}")
        
        result = {
            "status": "success",
            "timestamp": int(time.time()),
            "test_type": test_type,
            "test_cases": None,
            "comparison_result": None,
            "bitable_updates": {},
            "errors": []
        }
        
        try:
            # 步骤0: 更新状态为"进行中"
            logger.info("步骤0: 更新执行状态为进行中")
            self._update_execution_status(app_token, table_id, record_id, "进行中")
            result["status_updates"] = ["进行中"]
            test_cases = None
            comparison_result = None
            
            # 根据测试类型执行不同的步骤
            if test_type == "功能测试":
                # 只执行PRD解析和测试用例生成
                logger.info("执行功能测试: 解析PRD文档并生成测试用例")
                test_cases = self._generate_test_cases_from_prd(prd_document_token)
                result["test_cases"] = test_cases
                logger.info("功能测试完成，跳过视觉比较")
                
            elif test_type == "UI测试":
                # 只执行Figma与网站的视觉比较
                logger.info("执行UI测试: 比较Figma设计和网站")
                comparison_result = self._compare_figma_and_website(
                    figma_url, website_url, xpath_selector, device, output_dir
                )
                result["comparison_result"] = comparison_result
                logger.info("UI测试完成，跳过PRD解析")
                
            else:
                # 默认执行完整测试（兼容原有行为）
                logger.info("执行完整测试: PRD解析 + 视觉比较")
                
                # 步骤1: 解析PRD文档生成测试用例
                logger.info("步骤1: 解析PRD文档并生成测试用例")
                test_cases = self._generate_test_cases_from_prd(prd_document_token)
                result["test_cases"] = test_cases
                
                # 步骤2: 比较Figma设计和网站
                logger.info("步骤2: 比较Figma设计和网站")
                comparison_result = self._compare_figma_and_website(
                    figma_url, website_url, xpath_selector, device, output_dir
                )
                result["comparison_result"] = comparison_result
            
            # 步骤3: 更新多维表格（所有测试类型都需要更新）
            logger.info("步骤3: 更新多维表格")
            bitable_updates = self._update_bitable_record(
                app_token, table_id, record_id, test_cases, comparison_result
            )
            result["bitable_updates"] = bitable_updates
            
            # 步骤4: 更新状态为"已完成"
            logger.info("步骤4: 更新执行状态为已完成")
            self._update_execution_status(app_token, table_id, record_id, "已完成")
            result["status_updates"].append("已完成")
            
            logger.info(f"工作流执行完成 / Workflow execution completed - 测试类型: {test_type}")
            return result
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            
            # 更新状态为"失败"
            try:
                logger.info("更新执行状态为失败")
                self._update_execution_status(app_token, table_id, record_id, "失败")
                result["status_updates"] = result.get("status_updates", []) + ["失败"]
            except Exception as status_error:
                logger.error(f"更新失败状态时出错: {status_error}")
                
            result["status"] = "error"
            result["errors"].append(str(e))
            return result
    
    def _generate_test_cases_from_prd(self, document_input: str) -> Dict[str, Any]:
        """
        从PRD文档生成测试用例 (支持完整链接或token)
        Generate test cases from PRD document (supports full URL or token)
        
        Args:
            document_input: 文档链接或token (document URL or token)
        """
        try:
            # 解析PRD文档 (新方法自动处理完整链接或token)
            prd_result = self.feishu_client.parse_prd_document(document_input)
            prd_text = prd_result['text_content']
            
            # 使用AI生成测试用例
            try:
                test_cases_text = self.gemini_generator.generate_test_cases(prd_text, case_count=10)
                
                return {
                    "document_input": document_input,
                    "prd_text_length": len(prd_text),
                    "test_cases_text": test_cases_text,
                    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "api_status": "success"
                }
                
            except Exception as api_error:
                # Gemini API调用失败，记录错误信息
                error_message = str(api_error)
                logger.error(f"Gemini API调用失败: {error_message}")
                
                # 创建包含错误信息的测试用例文档
                error_report = f"""# ⚠️ 测试用例生成失败

## 错误信息
**Gemini API调用失败**: {error_message}

## 详细说明
- **时间**: {time.strftime("%Y-%m-%d %H:%M:%S")}
- **PRD文档**: {document_input}
- **PRD文本长度**: {len(prd_text)} 字符
- **错误类型**: API服务不可用

## 可能的原因
1. **地理位置限制**: Gemini API在当前地区不可用
2. **网络连接问题**: 无法连接到Google AI服务
3. **API配置错误**: API密钥或配置有误
4. **服务超时**: API响应时间过长

## 建议解决方案
1. **检查网络**: 确认网络连接正常
2. **更换地区**: 尝试使用VPN或其他网络环境  
3. **验证配置**: 检查GEMINI_API_KEY环境变量
4. **稍后重试**: 等待服务恢复后重新执行

## PRD文档内容预览
```
{prd_text[:500]}{"..." if len(prd_text) > 500 else ""}
```

*注意: 可以手动基于上述PRD内容编写测试用例，或等待API服务恢复后重新执行工作流。*
"""
                
                return {
                    "document_input": document_input,
                    "prd_text_length": len(prd_text),
                    "test_cases_text": error_report,
                    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "api_status": "failed",
                    "api_error": error_message
                }
            
        except Exception as e:
            logger.error(f"生成测试用例失败: {e}")
            raise
    
    def _compare_figma_and_website(self, 
                                 figma_url: str, 
                                 website_url: str, 
                                 xpath_selector: str = None,  # 改为XPath选择器
                                 device: str = "desktop",
                                 output_dir: str = "reports") -> Dict[str, Any]:
        """
        比较Figma设计和网站
        Compare Figma design and website
        """
        try:
            self._log_resource_usage("开始视觉比较")
            
            # 清理旧报告目录（只保留最新的一个）
            self._cleanup_old_reports(output_dir)
            
            # 创建输出目录
            timestamp = int(time.time())
            current_output_dir = os.path.join(output_dir, f"comparison_{timestamp}")
            os.makedirs(current_output_dir, exist_ok=True)
            
            # 1. 网页截图 (按需初始化截图捕获器)
            self._initialize_component_if_needed('screenshot_capture')
            website_screenshot_path = os.path.join(current_output_dir, f"website_{device}.png")
            
            logger.info("开始网页截图")
            if xpath_selector:
                # 按XPath截图
                logger.info(f"使用XPath截图: {xpath_selector}")
                self.screenshot_capture.capture_by_xpath(
                    url=website_url,
                    xpath=xpath_selector,
                    output_dir=current_output_dir,
                    device=device,
                    wait_time=5  # 减少等待时间以提高效率
                )
                # 重命名文件为标准格式
                xpath_filename = self.screenshot_capture.build_filename_from_xpath(
                    xpath_selector, device, website_url
                )
                original_path = os.path.join(current_output_dir, xpath_filename)
                if os.path.exists(original_path):
                    os.rename(original_path, website_screenshot_path)
                    logger.info(f"XPath截图已保存: {website_screenshot_path}")
                else:
                    logger.warning(f"XPath截图文件未找到: {original_path}")
            else:
                # 全页截图
                logger.info("使用全页截图")
                self.screenshot_capture.capture_full_page(
                    url=website_url,
                    output_path=website_screenshot_path,
                    device=device,
                    wait_time=5  # 减少等待时间以提高效率
                )
            
            self._log_resource_usage("网页截图完成")
            
            # 2. Figma截图 (按需初始化Figma客户端)
            self._initialize_component_if_needed('figma_client')
            figma_image_path = os.path.join(current_output_dir, "figma_design.png")
            
            logger.info("开始Figma设计稿获取")
            # 解析Figma URL
            figma_info = self.figma_client.parse_figma_url(figma_url)
            
            # 导出Figma图片
            node_id = figma_info.get('node_id')
            if not node_id:
                # 如果没有节点ID，获取文件信息并使用第一个页面
                file_info = self.figma_client.get_file_info(figma_info['file_id'])
                pages = file_info.get('document', {}).get('children', [])
                if pages:
                    node_id = pages[0]['id']
                else:
                    raise ValueError("无法找到可用的节点ID")
            
            # 调用export_images方法（注意是复数形式）
            image_urls = self.figma_client.export_images(
                file_id=figma_info['file_id'],
                node_ids=[node_id],
                format='png',
                scale=2.0
            )
            
            # 获取图片URL - 处理节点ID格式转换
            if not image_urls:
                raise ValueError(f"Figma API没有返回任何图片URL")
            
            # 尝试不同的节点ID格式（URL格式和API格式）
            figma_image_url = None
            actual_node_id = None
            
            # 方法1：直接使用原始节点ID
            if node_id in image_urls and image_urls[node_id]:
                figma_image_url = image_urls[node_id]
                actual_node_id = node_id
            
            # 方法2：转换横线为冒号（URL格式 -> API格式）
            if not figma_image_url:
                api_format_node_id = node_id.replace('-', ':')
                if api_format_node_id in image_urls and image_urls[api_format_node_id]:
                    figma_image_url = image_urls[api_format_node_id]
                    actual_node_id = api_format_node_id
            
            # 方法3：使用第一个可用的URL
            if not figma_image_url:
                for key, url in image_urls.items():
                    if url:  # 确保URL不为空
                        figma_image_url = url
                        actual_node_id = key
                        break
            
            if not figma_image_url:
                available_nodes = list(image_urls.keys())
                raise ValueError(f"无法获取节点 {node_id} 的图片URL。可用节点: {available_nodes}")
            
            logger.info(f"使用节点ID: {actual_node_id} (原始: {node_id})")
            
            # 下载Figma图片
            self.figma_client.download_image(figma_image_url, figma_image_path)
            
            # 3. 视觉比较 (按需初始化视觉比较器)
            self._initialize_component_if_needed('visual_comparator')
            comparison_result = self.visual_comparator.compare_images(
                image1_path=website_screenshot_path,
                image2_path=figma_image_path,
                output_dir=current_output_dir
            )
            
            self._log_resource_usage("视觉比较完成")
            
            # 4. 生成报告
            report_path = os.path.join(current_output_dir, "comparison_report.json")
            self.visual_comparator.generate_report(comparison_result, report_path)
            
            self._log_resource_usage("报告生成完成")
            
            # 5. 清理组件以释放内存
            self._cleanup_component('screenshot_capture')
            self._cleanup_component('figma_client')
            self._cleanup_component('visual_comparator')
            
            self._log_resource_usage("组件清理完成")
            
            return {
                "figma_url": figma_url,
                "website_url": website_url,
                "xpath_selector": xpath_selector,  # XPath选择器
                "device": device,
                "output_directory": current_output_dir,
                "website_screenshot": website_screenshot_path,
                "figma_screenshot": figma_image_path,
                "comparison_result": {
                    "similarity_score": comparison_result.similarity_score,
                    "ssim_score": comparison_result.ssim_score,
                    "mse_score": comparison_result.mse_score,
                    "hash_distance": comparison_result.hash_distance,
                    "differences_count": comparison_result.differences_count,
                    "diff_image_path": comparison_result.diff_image_path
                },
                "report_path": report_path,
                "compared_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"视觉比较失败: {e}")
            raise
    
    def _update_bitable_record(self, 
                             app_token: str, 
                             table_id: str, 
                             record_id: str,
                             test_cases: Dict[str, Any],
                             comparison_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新多维表格记录
        Update bitable record
        """
        try:
            # 准备更新字段
            update_fields = {}
            
            # 根据有无数据来判断执行的测试类型
            test_type_executed = []
            
            # 更新测试用例栏（功能测试结果）
            if test_cases and test_cases.get('test_cases_text'):
                update_fields['测试用例'] = test_cases['test_cases_text']
                test_type_executed.append("功能测试")
            
            # 更新网站相似度报告栏（UI测试结果）
            if comparison_result:
                similarity_report = self._format_similarity_report(comparison_result)
                update_fields['网站相似度报告'] = similarity_report
                test_type_executed.append("UI测试")
            
            # 更新执行状态，显示具体执行的测试类型
            if test_type_executed:
                executed_types = " + ".join(test_type_executed)
                update_fields['执行结果'] = f"已完成({executed_types})"
            else:
                update_fields['执行结果'] = "已完成"
            
            # 执行更新
            updated_record = self.feishu_client.update_bitable_record(
                app_token=app_token,
                table_id=table_id,
                record_id=record_id,
                fields=update_fields
            )
            
            return {
                "app_token": app_token,
                "table_id": table_id,
                "record_id": record_id,
                "updated_fields": list(update_fields.keys()),
                "update_result": updated_record,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"更新多维表格失败: {e}")
            raise
    
    def _update_execution_status(self, app_token: str, table_id: str, record_id: str, status: str) -> Dict[str, Any]:
        """
        更新执行状态
        Update execution status
        
        Args:
            app_token: 应用token
            table_id: 数据表ID
            record_id: 记录ID
            status: 状态值 ("未开始", "进行中", "已完成", "失败")
            
        Returns:
            更新结果
        """
        try:
            logger.info(f"正在更新执行状态为: {status}")
            
            # 准备状态更新字段
            status_fields = {
                '执行状态': status
            }
            
            # 执行状态更新
            updated_record = self.feishu_client.update_bitable_record(
                app_token=app_token,
                table_id=table_id,
                record_id=record_id,
                fields=status_fields
            )
            
            logger.info(f"执行状态更新成功: {status}")
            
            return {
                "app_token": app_token,
                "table_id": table_id,
                "record_id": record_id,
                "status": status,
                "update_result": updated_record,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"更新执行状态失败: {e}")
            # 状态更新失败不应该中断主流程，只记录错误
            raise Exception(f"状态更新失败: {e}")
    
    def _format_similarity_report(self, comparison_result: Dict[str, Any]) -> str:
        """
        格式化相似度报告
        Format similarity report
        """
        comp_data = comparison_result.get('comparison_result', {})
        
        # 尝试读取完整的比较报告文件以获取recommendations
        recommendations = []
        detailed_analysis = {}
        
        report_path = comparison_result.get('report_path')
        if report_path and os.path.exists(report_path):
            try:
                import json
                with open(report_path, 'r', encoding='utf-8') as f:
                    full_report = json.load(f)
                    recommendations = full_report.get('recommendations', [])
                    detailed_analysis = full_report.get('analysis', {})
            except Exception as e:
                logger.warning(f"无法读取详细报告文件: {e}")
        
        report = f"""# 网站与Figma设计相似度报告

## 基本信息
- **Figma地址**: {comparison_result.get('figma_url', 'N/A')}
- **网站地址**: {comparison_result.get('website_url', 'N/A')}
- **CSS类名**: {comparison_result.get('website_classes') or '全页截图'}
- **设备类型**: {comparison_result.get('device', 'desktop')}
- **对比时间**: {comparison_result.get('compared_at', 'N/A')}

## 相似度指标
- **总体相似度**: {comp_data.get('similarity_score', 0):.3f} ({self._get_similarity_rating(comp_data.get('similarity_score', 0))})
- **结构相似性(SSIM)**: {comp_data.get('ssim_score', 0):.3f}
- **均方误差(MSE)**: {comp_data.get('mse_score', 0):.2f}
- **感知哈希距离**: {comp_data.get('hash_distance', 0)}
- **差异区域数**: {comp_data.get('differences_count', 0)}"""

        # 添加详细分析信息（如果可用）
        if detailed_analysis:
            diff_percentage = detailed_analysis.get('diff_percentage', 0)
            total_diff_area = detailed_analysis.get('total_diff_area', 0)
            color_analysis = detailed_analysis.get('color_analysis', {})
            
            report += f"""

## 详细分析
- **差异百分比**: {diff_percentage:.2f}%
- **差异区域面积**: {total_diff_area} 像素
- **颜色差异**: 最大差异 {color_analysis.get('max_color_diff', 0):.2f}"""

        # 获取图片URL
        figma_image_url = get_image_url(comparison_result.get('figma_screenshot'))
        website_image_url = get_image_url(comparison_result.get('website_screenshot'))
        diff_image_url = get_image_url(comp_data.get('diff_image_path'))

        report += f"""

## 对比图片
- **Figma设计稿**: {figma_image_url or '无法访问'}
- **网站截图**: {website_image_url or '无法访问'}
- **差异对比图**: {diff_image_url or '无法访问'}

## 文件路径
- **输出目录**: {comparison_result.get('output_directory', 'N/A')}
- **详细报告**: {comparison_result.get('report_path', 'N/A')}"""

        # 添加AI建议部分
        if recommendations:
            report += f"""

## AI 分析建议
"""
            for i, rec in enumerate(recommendations, 1):
                report += f"- {rec}\n"
        
        report += f"""

## 分析结论
{self._get_comparison_conclusion(comp_data.get('similarity_score', 0))}
"""
        return report
    
    def _get_similarity_rating(self, score: float) -> str:
        """获取相似度评级"""
        if score >= 0.9:
            return "优秀"
        elif score >= 0.8:
            return "良好"
        elif score >= 0.7:
            return "一般"
        elif score >= 0.6:
            return "较差"
        else:
            return "很差"
    
    def _get_comparison_conclusion(self, score: float) -> str:
        """获取比较结论"""
        if score >= 0.9:
            return "实现效果与设计高度一致，无需调整。"
        elif score >= 0.8:
            return "实现效果良好，基本符合设计要求，可考虑微调细节。"
        elif score >= 0.7:
            return "实现效果一般，存在一些差异，建议检查并优化。"
        elif score >= 0.6:
            return "实现效果较差，与设计存在明显差异，需要重点调整。"
        else:
            return "实现效果很差，与设计差异极大，建议重新实现。"
    
    def reset_execution_status_to_default(self, app_token: str, table_id: str, record_id: str) -> Dict[str, Any]:
        """
        重置执行状态为默认值"未开始"
        Reset execution status to default value "未开始"
        
        Args:
            app_token: 应用token
            table_id: 数据表ID
            record_id: 记录ID
            
        Returns:
            更新结果
        """
        try:
            return self._update_execution_status(app_token, table_id, record_id, "未开始")
        except Exception as e:
            logger.error(f"重置执行状态失败: {e}")
            raise
    
    def get_bitable_structure(self, app_token: str, table_id: str) -> Dict[str, Any]:
        """
        获取多维表格结构信息，用于调试
        Get bitable structure for debugging
        """
        try:
            # 获取表格信息
            tables = self.feishu_client.get_bitable_tables(app_token)
            current_table = None
            
            for table in tables:
                if table['table_id'] == table_id:
                    current_table = table
                    break
            
            if not current_table:
                raise Exception(f"未找到表格: {table_id}")
            
            # 获取字段信息
            fields = self.feishu_client.get_bitable_fields(app_token, table_id)
            
            # 获取记录样例
            records_data = self.feishu_client.get_bitable_records(app_token, table_id, page_size=3)
            
            return {
                "table_info": current_table,
                "fields": fields,
                "sample_records": records_data.get('items', []),
                "total_records": records_data.get('total', 0)
            }
            
        except Exception as e:
            logger.error(f"获取表格结构失败: {e}")
            raise 