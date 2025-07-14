"""
功能测试管理器
Functional Test Manager

提供统一的功能测试接口，集成所有测试组件
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..utils.logger import get_logger
from .types import TestCase, TestConfig, TestResult, TestReport
from .case_converter import TestCaseConverter
from .test_runner import TestRunner
from .test_executor import TestExecutor
from .report_generator import ReportGenerator

logger = get_logger(__name__)


class FunctionalTestManager:
    """功能测试管理器"""
    
    def __init__(self):
        self.converter = TestCaseConverter()
        self.report_generator = ReportGenerator()
        logger.info("功能测试管理器初始化完成")
    
    def run_test_from_description(self, test_description: str, config: TestConfig) -> Dict[str, Any]:
        """
        从测试描述运行测试
        
        Args:
            test_description: 测试描述文本
            config: 测试配置
            
        Returns:
            测试结果字典
        """
        try:
            # 转换测试用例
            test_case = self.converter.convert_simple_test_case(test_description)
            
            # 验证测试用例
            validation = self._validate_test_case(test_case)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": "测试用例验证失败",
                    "details": validation
                }
            
            # 运行测试
            runner = TestRunner(config)
            test_result = runner.run_single_test(test_case)
            
            # 生成报告
            test_report = TestReport(
                summary={
                    "total": 1,
                    "passed": 1 if test_result.status == "passed" else 0,
                    "failed": 1 if test_result.status == "failed" else 0,
                    "skipped": 0,
                    "duration": test_result.duration
                },
                environment={
                    "browser": "chrome",
                    "device": config.device,
                    "baseUrl": config.baseUrl,
                    "headless": config.headless
                },
                testResults=[test_result]
            )
            
            report_path = self.report_generator.generate_html_report(test_report)
            
            return {
                "success": True,
                "test_case": {
                    "id": test_case.id,
                    "name": test_case.name,
                    "description": test_case.description,
                    "steps_count": len(test_case.steps),
                    "assertions_count": len(test_case.assertions)
                },
                "result": {
                    "status": test_result.status,
                    "duration": test_result.duration,
                    "steps_passed": len([s for s in test_result.steps if s.status == "success"]),
                    "assertions_passed": len([a for a in test_result.assertions if a.status == "passed"]),
                    "error": test_result.error
                },
                "report_path": report_path,
                "screenshots": test_result.screenshots
            }
            
        except Exception as e:
            logger.error(f"运行测试失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "details": {"exception": str(e)}
            }
    
    def run_demo_test(self, config: TestConfig) -> Dict[str, Any]:
        """
        运行演示测试用例
        
        Args:
            config: 测试配置
            
        Returns:
            测试结果字典
        """
        try:
            # 创建演示测试用例
            test_case = self.converter.create_demo_test_case()
            
            # 运行测试
            runner = TestRunner(config)
            test_result = runner.run_single_test(test_case)
            
            # 生成报告
            test_report = TestReport(
                summary={
                    "total": 1,
                    "passed": 1 if test_result.status == "passed" else 0,
                    "failed": 1 if test_result.status == "failed" else 0,
                    "skipped": 0,
                    "duration": test_result.duration
                },
                environment={
                    "browser": "chrome",
                    "device": config.device,
                    "baseUrl": config.baseUrl,
                    "headless": config.headless
                },
                testResults=[test_result]
            )
            
            report_path = self.report_generator.generate_html_report(test_report)
            
            return {
                "success": True,
                "test_case": {
                    "id": test_case.id,
                    "name": test_case.name,
                    "description": test_case.description,
                    "steps_count": len(test_case.steps),
                    "assertions_count": len(test_case.assertions)
                },
                "result": {
                    "status": test_result.status,
                    "duration": test_result.duration,
                    "steps_passed": len([s for s in test_result.steps if s.status == "success"]),
                    "assertions_passed": len([a for a in test_result.assertions if a.status == "passed"]),
                    "error": test_result.error
                },
                "report_path": report_path,
                "screenshots": test_result.screenshots
            }
            
        except Exception as e:
            logger.error(f"运行演示测试失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "details": {"exception": str(e)}
            }
    
    def convert_test_case(self, test_description: str) -> Dict[str, Any]:
        """
        转换测试用例描述为规范格式
        
        Args:
            test_description: 测试描述文本
            
        Returns:
            转换结果
        """
        try:
            test_case = self.converter.convert_simple_test_case(test_description)
            validation = self._validate_test_case(test_case)
            
            return {
                "success": True,
                "test_case": {
                    "id": test_case.id,
                    "name": test_case.name,
                    "description": test_case.description,
                    "steps": [
                        {
                            "action": step.action,
                            "selector": step.selector,
                            "value": step.value,
                            "description": step.description
                        } for step in test_case.steps
                    ],
                    "assertions": [
                        {
                            "type": assertion.type,
                            "target": assertion.target,
                            "condition": assertion.condition,
                            "expected": assertion.expected,
                            "description": assertion.description
                        } for assertion in test_case.assertions
                    ]
                },
                "validation": validation
            }
            
        except Exception as e:
            logger.error(f"转换测试用例失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_demo_test_json(self) -> Dict[str, Any]:
        """
        获取演示测试用例的JSON格式
        
        Returns:
            演示测试用例JSON
        """
        try:
            test_case = self.converter.create_demo_test_case()
            
            return {
                "success": True,
                "test_case": {
                    "id": test_case.id,
                    "name": test_case.name,
                    "description": test_case.description,
                    "steps": [
                        {
                            "action": step.action,
                            "selector": step.selector,
                            "value": step.value,
                            "timeout": step.timeout,
                            "waitFor": step.waitFor,
                            "description": step.description
                        } for step in test_case.steps
                    ],
                    "assertions": [
                        {
                            "type": assertion.type,
                            "target": assertion.target,
                            "condition": assertion.condition,
                            "expected": assertion.expected,
                            "description": assertion.description
                        } for assertion in test_case.assertions
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"获取演示测试用例失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_test_case(self, test_case: TestCase) -> Dict[str, Any]:
        """验证测试用例"""
        errors = []
        warnings = []
        
        # 基本验证
        if not test_case.id:
            errors.append("测试用例ID不能为空")
        if not test_case.name:
            errors.append("测试用例名称不能为空")
        if not test_case.steps:
            errors.append("测试用例必须包含至少一个步骤")
        
        # 步骤验证
        for i, step in enumerate(test_case.steps):
            if not step.action:
                errors.append(f"步骤 {i+1}: 操作类型不能为空")
            
            if step.action in ["click", "input", "hover", "scroll"] and not step.selector:
                errors.append(f"步骤 {i+1}: {step.action} 操作需要指定选择器")
            
            if step.action == "input" and not step.value:
                warnings.append(f"步骤 {i+1}: input 操作建议指定输入值")
            
            if step.action == "navigate" and not step.value:
                errors.append(f"步骤 {i+1}: navigate 操作需要指定URL")
        
        # 断言验证
        for i, assertion in enumerate(test_case.assertions):
            if not assertion.type:
                errors.append(f"断言 {i+1}: 断言类型不能为空")
            
            if assertion.type == "dom" and not assertion.target:
                errors.append(f"断言 {i+1}: DOM断言需要指定目标选择器")
            
            if assertion.type == "network" and not assertion.target:
                errors.append(f"断言 {i+1}: 网络断言需要指定目标URL")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def create_test_config(self, base_url: str, device: str = "mobile", 
                          cookies: Optional[str] = None, 
                          local_storage: Optional[str] = None,
                          headless: bool = True) -> TestConfig:
        """
        创建测试配置
        
        Args:
            base_url: 基础URL
            device: 设备类型
            cookies: Cookie字符串
            local_storage: localStorage字符串
            headless: 是否无头模式
            
        Returns:
            测试配置对象
        """
        return TestConfig(
            baseUrl=base_url,
            device=device,
            cookies=cookies,
            localStorage=local_storage,
            headless=headless,
            screenshot="on",
            timeout=30
        )
    
    def get_available_actions(self) -> List[str]:
        """获取可用的操作类型"""
        return ["click", "input", "navigate", "hover", "wait", "scroll", "custom"]
    
    def get_available_assertions(self) -> List[str]:
        """获取可用的断言类型"""
        return ["dom", "network", "url", "custom"]
    
    def cleanup_old_reports(self, days: int = 7):
        """清理旧的测试报告"""
        try:
            reports_dir = "reports"
            if not os.path.exists(reports_dir):
                return
            
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for filename in os.listdir(reports_dir):
                filepath = os.path.join(reports_dir, filename)
                if os.path.isfile(filepath) and filename.endswith('.html'):
                    if os.path.getctime(filepath) < cutoff_time:
                        os.remove(filepath)
                        logger.info(f"清理旧报告: {filename}")
            
        except Exception as e:
            logger.error(f"清理旧报告失败: {e}")
    
    def get_test_statistics(self) -> Dict[str, Any]:
        """获取测试统计信息"""
        try:
            reports_dir = "reports"
            if not os.path.exists(reports_dir):
                return {"total_reports": 0, "recent_reports": []}
            
            reports = []
            for filename in os.listdir(reports_dir):
                if filename.endswith('.html'):
                    filepath = os.path.join(reports_dir, filename)
                    create_time = os.path.getctime(filepath)
                    reports.append({
                        "filename": filename,
                        "create_time": datetime.fromtimestamp(create_time).strftime("%Y-%m-%d %H:%M:%S"),
                        "size": os.path.getsize(filepath)
                    })
            
            # 按创建时间排序
            reports.sort(key=lambda x: x["create_time"], reverse=True)
            
            return {
                "total_reports": len(reports),
                "recent_reports": reports[:10]  # 最近10个报告
            }
            
        except Exception as e:
            logger.error(f"获取测试统计失败: {e}")
            return {"error": str(e)} 