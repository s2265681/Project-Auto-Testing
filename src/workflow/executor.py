"""
工作流执行器 - 整合PRD解析、测试用例生成和视觉比较功能
Workflow Executor - Integrating PRD parsing, test case generation and visual comparison
"""
import os
import time
import json
from typing import Dict, List, Any, Optional
from ..utils.logger import get_logger
from ..feishu.client import FeishuClient
from ..ai_analysis.gemini_case_generator import GeminiCaseGenerator
from ..screenshot.capture import ScreenshotCapture
from ..figma.client import FigmaClient
from ..visual_comparison.comparator import VisualComparator

logger = get_logger(__name__)

class WorkflowExecutor:
    """工作流执行器 Workflow Executor"""
    
    def __init__(self):
        """初始化执行器 Initialize executor"""
        self.feishu_client = FeishuClient()
        self.gemini_generator = GeminiCaseGenerator()
        self.screenshot_capture = ScreenshotCapture()
        self.figma_client = FigmaClient()
        self.visual_comparator = VisualComparator()
        
    def execute_button_click(self, 
                           app_token: str,
                           table_id: str, 
                           record_id: str,
                           prd_document_token: str,
                           figma_url: str,
                           website_url: str,
                           website_classes: str = None,
                           device: str = "desktop",
                           output_dir: str = "reports") -> Dict[str, Any]:
        """
        执行按钮点击的完整工作流
        Execute complete workflow for button click
        
        Args:
            app_token: 多维表格应用token bitable app token
            table_id: 数据表ID table ID  
            record_id: 记录ID record ID
            prd_document_token: PRD文档token PRD document token
            figma_url: Figma设计稿URL Figma design URL
            website_url: 网站URL website URL
            website_classes: 网站CSS类名 website CSS classes (optional)
            device: 设备类型 device type
            output_dir: 输出目录 output directory
            
        Returns:
            执行结果 execution result
        """
        logger.info("开始执行工作流 / Starting workflow execution")
        
        result = {
            "status": "success",
            "timestamp": int(time.time()),
            "test_cases": None,
            "comparison_result": None,
            "bitable_updates": {},
            "errors": []
        }
        
        try:
            # 步骤1: 解析PRD文档生成测试用例
            logger.info("步骤1: 解析PRD文档并生成测试用例")
            test_cases = self._generate_test_cases_from_prd(prd_document_token)
            result["test_cases"] = test_cases
            
            # 步骤2: 比较Figma设计和网站
            logger.info("步骤2: 比较Figma设计和网站")
            comparison_result = self._compare_figma_and_website(
                figma_url, website_url, website_classes, device, output_dir
            )
            result["comparison_result"] = comparison_result
            
            # 步骤3: 更新多维表格
            logger.info("步骤3: 更新多维表格")
            bitable_updates = self._update_bitable_record(
                app_token, table_id, record_id, test_cases, comparison_result
            )
            result["bitable_updates"] = bitable_updates
            
            logger.info("工作流执行完成 / Workflow execution completed")
            return result
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            result["status"] = "error"
            result["errors"].append(str(e))
            return result
    
    def _generate_test_cases_from_prd(self, document_token: str) -> Dict[str, Any]:
        """
        从PRD文档生成测试用例
        Generate test cases from PRD document
        """
        try:
            # 解析PRD文档
            prd_result = self.feishu_client.parse_prd_document(document_token)
            prd_text = prd_result['text_content']
            
            # 使用AI生成测试用例
            try:
                test_cases_text = self.gemini_generator.generate_test_cases(prd_text, case_count=10)
                
                return {
                    "document_token": document_token,
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
- **PRD文档**: {document_token}
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
                    "document_token": document_token,
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
                                 website_classes: str = None,
                                 device: str = "desktop",
                                 output_dir: str = "reports") -> Dict[str, Any]:
        """
        比较Figma设计和网站
        Compare Figma design and website
        """
        try:
            # 创建输出目录
            timestamp = int(time.time())
            current_output_dir = os.path.join(output_dir, f"comparison_{timestamp}")
            os.makedirs(current_output_dir, exist_ok=True)
            
            # 1. 网页截图
            website_screenshot_path = os.path.join(current_output_dir, f"website_{device}.png")
            
            if website_classes:
                # 按CSS类截图
                self.screenshot_capture.capture_by_classes(
                    url=website_url,
                    classes=website_classes,
                    output_dir=current_output_dir,
                    element_index=0,
                    device=device,
                    wait_time=5
                )
                # 重命名文件
                class_filename = self.screenshot_capture.build_filename_from_classes(
                    website_classes, 0, device, website_url
                )
                original_path = os.path.join(current_output_dir, class_filename)
                if os.path.exists(original_path):
                    os.rename(original_path, website_screenshot_path)
            else:
                # 全页截图
                self.screenshot_capture.capture_full_page(
                    url=website_url,
                    output_path=website_screenshot_path,
                    device=device,
                    wait_time=5
                )
            
            # 2. Figma截图
            figma_image_path = os.path.join(current_output_dir, "figma_design.png")
            
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
            
            # 3. 视觉比较
            comparison_result = self.visual_comparator.compare_images(
                image1_path=website_screenshot_path,
                image2_path=figma_image_path,
                output_dir=current_output_dir
            )
            
            # 4. 生成报告
            report_path = os.path.join(current_output_dir, "comparison_report.json")
            self.visual_comparator.generate_report(comparison_result, report_path)
            
            return {
                "figma_url": figma_url,
                "website_url": website_url,
                "website_classes": website_classes,
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
            
            # 更新测试用例文档栏
            if test_cases and test_cases.get('test_cases_text'):
                update_fields['测试用例文档'] = test_cases['test_cases_text']
            
            # 更新网站相似度报告栏
            if comparison_result:
                similarity_report = self._format_similarity_report(comparison_result)
                update_fields['网站相似度报告'] = similarity_report
            
            # 更新执行状态
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

        report += f"""

## 文件路径
- **输出目录**: {comparison_result.get('output_directory', 'N/A')}
- **差异对比图**: {comp_data.get('diff_image_path', 'N/A')}
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