"""
测试运行器
Test Runner

协调测试执行和报告生成
"""

import os
import json
from typing import List, Dict, Any
from datetime import datetime

from ..utils.logger import get_logger
from .types import TestCase, TestConfig, TestResult, TestReport
from .test_executor import TestExecutor
from .report_generator import ReportGenerator

logger = get_logger(__name__)


class TestRunner:
    """测试运行器"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.executor = TestExecutor(config)
        self.report_generator = ReportGenerator()
    
    def run_test_cases(self, test_cases: List[TestCase]) -> TestReport:
        """
        运行多个测试用例
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            TestReport: 测试报告
        """
        start_time = datetime.now()
        logger.info(f"开始运行测试，共 {len(test_cases)} 个测试用例")
        
        # 初始化测试报告
        test_report = TestReport(
            summary={
                "total": len(test_cases),
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration": 0
            },
            environment={
                "browser": "chrome",
                "device": self.config.device,
                "viewport": self.config.viewport or {"width": 1920, "height": 1080},
                "platform": "auto",
                "baseUrl": self.config.baseUrl,
                "headless": self.config.headless
            },
            startTime=start_time
        )
        
        # 执行测试用例
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"执行测试用例 {i}/{len(test_cases)}: {test_case.name}")
            
            try:
                # 为每个测试用例创建新的执行器实例
                executor = TestExecutor(self.config)
                test_result = executor.execute_test_case(test_case)
                test_report.testResults.append(test_result)
                
                # 更新统计信息
                if test_result.status == "passed":
                    test_report.summary["passed"] += 1
                elif test_result.status == "failed":
                    test_report.summary["failed"] += 1
                else:
                    test_report.summary["skipped"] += 1
                    
                logger.info(f"测试用例 {test_case.name} 完成: {test_result.status}")
                
            except Exception as e:
                logger.error(f"测试用例 {test_case.name} 执行异常: {e}")
                # 创建失败的测试结果
                failed_result = TestResult(
                    testCase=test_case,
                    status="failed",
                    duration=0,
                    error=str(e)
                )
                test_report.testResults.append(failed_result)
                test_report.summary["failed"] += 1
        
        # 完成测试
        end_time = datetime.now()
        test_report.endTime = end_time
        test_report.summary["duration"] = (end_time - start_time).total_seconds()
        
        # 生成报告
        report_path = self.report_generator.generate_html_report(test_report)
        test_report.reportPath = report_path
        
        logger.info(f"测试完成，总耗时: {test_report.summary['duration']:.2f}秒")
        logger.info(f"测试结果: 通过 {test_report.summary['passed']}, 失败 {test_report.summary['failed']}, 跳过 {test_report.summary['skipped']}")
        logger.info(f"测试报告: {report_path}")
        
        return test_report
    
    def run_single_test(self, test_case: TestCase) -> TestResult:
        """
        运行单个测试用例
        
        Args:
            test_case: 测试用例
            
        Returns:
            TestResult: 测试结果
        """
        logger.info(f"运行单个测试用例: {test_case.name}")
        
        executor = TestExecutor(self.config)
        test_result = executor.execute_test_case(test_case)
        
        # 生成单个测试的报告
        test_report = TestReport(
            summary={
                "total": 1,
                "passed": 1 if test_result.status == "passed" else 0,
                "failed": 1 if test_result.status == "failed" else 0,
                "skipped": 1 if test_result.status == "skipped" else 0,
                "duration": test_result.duration
            },
            environment={
                "browser": "chrome",
                "device": self.config.device,
                "viewport": self.config.viewport or {"width": 1920, "height": 1080},
                "platform": "auto",
                "baseUrl": self.config.baseUrl,
                "headless": self.config.headless
            },
            testResults=[test_result]
        )
        
        # 生成报告
        report_path = self.report_generator.generate_html_report(test_report)
        
        logger.info(f"单个测试完成: {test_result.status}, 报告: {report_path}")
        
        return test_result
    
    def validate_test_case(self, test_case: TestCase) -> Dict[str, Any]:
        """
        验证测试用例的有效性
        
        Args:
            test_case: 测试用例
            
        Returns:
            验证结果
        """
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
    
    def get_test_summary(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """
        获取测试摘要
        
        Args:
            test_results: 测试结果列表
            
        Returns:
            测试摘要
        """
        total = len(test_results)
        passed = sum(1 for r in test_results if r.status == "passed")
        failed = sum(1 for r in test_results if r.status == "failed")
        skipped = sum(1 for r in test_results if r.status == "skipped")
        
        total_duration = sum(r.duration for r in test_results)
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "total_duration": total_duration,
            "average_duration": (total_duration / total) if total > 0 else 0,
            "failed_tests": [r.testCase.name for r in test_results if r.status == "failed"]
        } 