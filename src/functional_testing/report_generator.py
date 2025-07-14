"""
测试报告生成器
Test Report Generator

生成HTML格式的测试报告
"""

import os
import json
import glob
import shutil
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.asset_url_converter import convert_to_web_url, convert_screenshot_path, ensure_file_exists
from .types import TestReport, TestResult, StepResult, AssertionResult

logger = get_logger(__name__)


class ReportGenerator:
    """测试报告生成器"""
    
    def __init__(self):
        self.reports_dir = "reports"
        self.screenshots_dir = "screenshots"
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
    

    
    def _cleanup_old_reports(self):
        """清理旧的测试报告和截图文件夹，保留最新的一个"""
        logger.info("开始清理旧的测试报告和截图文件夹")
        try:
            # 清理旧的报告文件
            report_files = glob.glob(os.path.join(self.reports_dir, "test_report_*.html"))
            logger.info(f"找到 {len(report_files)} 个报告文件: {report_files}")
            if len(report_files) > 1:
                # 按修改时间排序，最新的在前面
                report_files.sort(key=os.path.getmtime, reverse=True)
                logger.info(f"按时间排序后的报告文件: {report_files}")
                # 删除除最新的一个之外的所有报告
                for report_file in report_files[1:]:
                    os.remove(report_file)
                    logger.info(f"删除旧的测试报告: {report_file}")
            
            # 清理旧的截图文件夹
            screenshot_dirs = glob.glob(os.path.join(self.screenshots_dir, "test_*"))
            logger.info(f"找到 {len(screenshot_dirs)} 个截图文件夹: {screenshot_dirs}")
            if len(screenshot_dirs) > 1:
                # 按修改时间排序，最新的在前面
                screenshot_dirs.sort(key=os.path.getmtime, reverse=True)
                logger.info(f"按时间排序后的截图文件夹: {screenshot_dirs}")
                # 删除除最新的一个之外的所有截图文件夹
                for screenshot_dir in screenshot_dirs[1:]:
                    if os.path.isdir(screenshot_dir):
                        shutil.rmtree(screenshot_dir)
                        logger.info(f"删除旧的截图文件夹: {screenshot_dir}")
                    
        except Exception as e:
            logger.warning(f"清理旧报告时出错: {e}")
        
        logger.info("清理旧的测试报告和截图文件夹完成")
    
    def generate_html_report(self, test_report: TestReport) -> str:
        """
        生成HTML测试报告
        
        Args:
            test_report: 测试报告数据
            
        Returns:
            报告文件路径
        """
        # 清理旧的报告文件和截图文件夹
        self._cleanup_old_reports()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"test_report_{timestamp}.html"
        report_path = os.path.join(self.reports_dir, report_filename)
        
        # 生成HTML内容
        html_content = self._generate_html_content(test_report)
        
        # 写入文件
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"测试报告已生成: {report_path}")
        return report_path
    
    def _generate_html_content(self, test_report: TestReport) -> str:
        """生成HTML内容"""
        
        # 计算成功率
        success_rate = 0
        if test_report.summary["total"] > 0:
            success_rate = (test_report.summary["passed"] / test_report.summary["total"]) * 100
        
        # 生成测试用例详情
        test_cases_html = self._generate_test_cases_html(test_report.testResults)
        
        # 生成截图展示
        screenshots_html = self._generate_screenshots_html(test_report.testResults)
        
        # 主要HTML模板
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>功能测试报告</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🧪 功能测试报告</h1>
            <div class="summary-cards">
                <div class="card total">
                    <h3>总计</h3>
                    <div class="number">{test_report.summary["total"]}</div>
                </div>
                <div class="card passed">
                    <h3>通过</h3>
                    <div class="number">{test_report.summary["passed"]}</div>
                </div>
                <div class="card failed">
                    <h3>失败</h3>
                    <div class="number">{test_report.summary["failed"]}</div>
                </div>
                <div class="card success-rate">
                    <h3>成功率</h3>
                    <div class="number">{success_rate:.1f}%</div>
                </div>
            </div>
        </header>
        
        <section class="meta-info">
            <h2>📋 测试信息</h2>
            <div class="info-grid">
                <div class="info-item">
                    <label>测试环境:</label>
                    <span>{test_report.environment.get("device", "desktop")} - {test_report.environment.get("browser", "chrome")}</span>
                </div>
                <div class="info-item">
                    <label>基础URL:</label>
                    <span>{test_report.environment.get("baseUrl", "未设置")}</span>
                </div>
                <div class="info-item">
                    <label>开始时间:</label>
                    <span>{test_report.startTime.strftime("%Y-%m-%d %H:%M:%S")}</span>
                </div>
                <div class="info-item">
                    <label>总耗时:</label>
                    <span>{test_report.summary["duration"]:.2f}秒</span>
                </div>
            </div>
        </section>
        
        <section class="test-cases">
            <h2>📝 测试用例详情</h2>
            {test_cases_html}
        </section>
        
        {screenshots_html}
        
        <footer class="footer">
            <p>测试报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </footer>
    </div>
    
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>
"""
        
        return html_template
    
    def _generate_test_cases_html(self, test_results: List[TestResult]) -> str:
        """生成测试用例HTML"""
        html_parts = []
        
        for i, result in enumerate(test_results, 1):
            status_class = result.status.lower()
            status_icon = "✅" if result.status == "passed" else "❌"
            
            # 生成步骤HTML
            steps_html = self._generate_steps_html(result.steps)
            
            # 生成断言HTML
            assertions_html = self._generate_assertions_html(result.assertions)
            
            # 生成网络请求HTML
            network_html = self._generate_network_requests_html(result.networkRequests)
            
            test_case_html = f"""
            <div class="test-case {status_class}">
                <div class="test-case-header" onclick="toggleDetails('test-{i}')">
                    <h3>{status_icon} {result.testCase.name}</h3>
                    <div class="test-meta">
                        <span class="duration">⏱️ {result.duration:.2f}s</span>
                        <span class="status {status_class}">{result.status.upper()}</span>
                    </div>
                </div>
                
                <div id="test-{i}" class="test-details" style="display: none;">
                    <div class="description">
                        <p>{result.testCase.description or '无描述'}</p>
                    </div>
                    
                    {f'<div class="error-message">❌ 错误: {result.error}</div>' if result.error else ''}
                    
                    <div class="tabs">
                        <button class="tab-button active" onclick="showTab('test-{i}', 'steps')">执行步骤</button>
                        <button class="tab-button" onclick="showTab('test-{i}', 'assertions')">断言验证</button>
                        <button class="tab-button" onclick="showTab('test-{i}', 'network')">网络请求</button>
                    </div>
                    
                    <div id="test-{i}-steps" class="tab-content active">
                        {steps_html}
                    </div>
                    
                    <div id="test-{i}-assertions" class="tab-content">
                        {assertions_html}
                    </div>
                    
                    <div id="test-{i}-network" class="tab-content">
                        {network_html}
                    </div>
                </div>
            </div>
            """
            
            html_parts.append(test_case_html)
        
        return "\n".join(html_parts)
    
    def _generate_steps_html(self, steps: List[StepResult]) -> str:
        """生成步骤HTML"""
        if not steps:
            return "<p>无执行步骤</p>"
        
        html_parts = ["<div class='steps-list'>"]
        
        for i, step in enumerate(steps, 1):
            status_icon = "✅" if step.status == "success" else "❌"
            status_class = step.status.lower()
            
            step_html = f"""
            <div class="step {status_class}">
                <div class="step-header">
                    <span class="step-number">{i}</span>
                    <span class="step-action">{step.step.action.upper()}</span>
                    <span class="step-status">{status_icon}</span>
                    <span class="step-duration">{step.duration:.2f}s</span>
                </div>
                <div class="step-details">
                    <p><strong>描述:</strong> {step.step.description or '无描述'}</p>
                    {f'<p><strong>选择器:</strong> <code>{step.step.selector}</code></p>' if step.step.selector else ''}
                    {f'<p><strong>值:</strong> <code>{step.step.value}</code></p>' if step.step.value else ''}
                    {f'<p class="error"><strong>错误:</strong> {step.error}</p>' if step.error else ''}
                    {f'<p><strong>截图:</strong> <img src="{convert_screenshot_path(step.screenshot)}" alt="步骤截图" class="step-screenshot"></p>' if step.screenshot else ''}
                </div>
            </div>
            """
            
            html_parts.append(step_html)
        
        html_parts.append("</div>")
        return "\n".join(html_parts)
    
    def _generate_assertions_html(self, assertions: List[AssertionResult]) -> str:
        """生成断言HTML"""
        if not assertions:
            return "<p>无断言验证</p>"
        
        html_parts = ["<div class='assertions-list'>"]
        
        for i, assertion in enumerate(assertions, 1):
            status_icon = "✅" if assertion.status == "passed" else "❌"
            status_class = assertion.status.lower()
            
            assertion_html = f"""
            <div class="assertion {status_class}">
                <div class="assertion-header">
                    <span class="assertion-number">{i}</span>
                    <span class="assertion-type">{assertion.assertion.type.upper()}</span>
                    <span class="assertion-status">{status_icon}</span>
                </div>
                <div class="assertion-details">
                    <p><strong>描述:</strong> {assertion.assertion.description or '无描述'}</p>
                    {f'<p><strong>目标:</strong> <code>{assertion.assertion.target}</code></p>' if assertion.assertion.target else ''}
                    <p><strong>条件:</strong> {assertion.assertion.condition}</p>
                    {f'<p><strong>期望值:</strong> <code>{assertion.assertion.expected}</code></p>' if assertion.assertion.expected is not None else ''}
                    {f'<p><strong>实际值:</strong> <code>{assertion.actual}</code></p>' if assertion.actual is not None else ''}
                    {f'<p class="error"><strong>错误:</strong> {assertion.error}</p>' if assertion.error else ''}
                </div>
            </div>
            """
            
            html_parts.append(assertion_html)
        
        html_parts.append("</div>")
        return "\n".join(html_parts)
    
    def _generate_network_requests_html(self, network_requests: List) -> str:
        """生成网络请求HTML"""
        if not network_requests:
            return "<p>无网络请求记录</p>"
        
        # 简化实现，显示占位符
        return "<p>网络请求记录功能正在开发中...</p>"
    
    def _generate_screenshots_html(self, test_results: List[TestResult]) -> str:
        """生成截图展示HTML"""
        all_screenshots = []
        
        for result in test_results:
            if result.screenshots:
                all_screenshots.extend(result.screenshots)
        
        if not all_screenshots:
            return ""
        
        html_parts = ["<section class='screenshots'>", "<h2>📸 测试截图</h2>", "<div class='screenshot-grid'>"]
        
        for i, screenshot in enumerate(all_screenshots, 1):
            if screenshot and ensure_file_exists(screenshot):
                screenshot_url = convert_screenshot_path(screenshot)
                html_parts.append(f"""
                <div class="screenshot-item">
                    <img src="{screenshot_url}" alt="测试截图 {i}" onclick="showFullscreen(this)">
                    <p>截图 {i}</p>
                </div>
                """)
        
        html_parts.extend(["</div>", "</section>"])
        return "\n".join(html_parts)
    
    def _get_css_styles(self) -> str:
        """获取CSS样式"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #2c3e50;
        }
        
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #ddd;
        }
        
        .card.total { border-left-color: #3498db; }
        .card.passed { border-left-color: #27ae60; }
        .card.failed { border-left-color: #e74c3c; }
        .card.success-rate { border-left-color: #f39c12; }
        
        .card h3 {
            margin-bottom: 10px;
            color: #666;
            font-size: 14px;
        }
        
        .card .number {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .meta-info {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        
        .info-item {
            display: flex;
            align-items: center;
        }
        
        .info-item label {
            font-weight: bold;
            margin-right: 10px;
            min-width: 80px;
        }
        
        .test-cases {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .test-case {
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
        }
        
        .test-case.passed { border-left: 4px solid #27ae60; }
        .test-case.failed { border-left: 4px solid #e74c3c; }
        
        .test-case-header {
            background: #f8f9fa;
            padding: 15px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .test-case-header:hover {
            background: #e9ecef;
        }
        
        .test-meta {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        
        .status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .status.passed { background: #d4edda; color: #155724; }
        .status.failed { background: #f8d7da; color: #721c24; }
        
        .test-details {
            padding: 20px;
        }
        
        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        
        .tabs {
            display: flex;
            border-bottom: 2px solid #ddd;
            margin-bottom: 20px;
        }
        
        .tab-button {
            background: none;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            font-size: 14px;
            color: #666;
            border-bottom: 2px solid transparent;
        }
        
        .tab-button.active {
            color: #3498db;
            border-bottom-color: #3498db;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .step, .assertion {
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-bottom: 10px;
            overflow: hidden;
        }
        
        .step.success { border-left: 4px solid #27ae60; }
        .step.failed { border-left: 4px solid #e74c3c; }
        
        .assertion.passed { border-left: 4px solid #27ae60; }
        .assertion.failed { border-left: 4px solid #e74c3c; }
        
        .step-header, .assertion-header {
            background: #f8f9fa;
            padding: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .step-number, .assertion-number {
            background: #3498db;
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
        }
        
        .step-details, .assertion-details {
            padding: 15px;
        }
        
        .step-screenshot {
            max-width: 300px;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .screenshots {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .screenshot-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .screenshot-item img {
            width: 100%;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 14px;
        }
        
        code {
            background: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        
        .error {
            color: #e74c3c;
        }
        """
    
    def _get_javascript(self) -> str:
        """获取JavaScript代码"""
        return """
        function toggleDetails(id) {
            const element = document.getElementById(id);
            if (element.style.display === 'none') {
                element.style.display = 'block';
            } else {
                element.style.display = 'none';
            }
        }
        
        function showTab(testId, tabName) {
            // 隐藏所有tab内容
            const tabContents = document.querySelectorAll(`#${testId} .tab-content`);
            tabContents.forEach(content => content.classList.remove('active'));
            
            // 移除所有tab按钮的active状态
            const tabButtons = document.querySelectorAll(`#${testId} .tab-button`);
            tabButtons.forEach(button => button.classList.remove('active'));
            
            // 显示选中的tab内容
            document.getElementById(`${testId}-${tabName}`).classList.add('active');
            
            // 激活选中的tab按钮
            event.target.classList.add('active');
        }
        
        function showFullscreen(img) {
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
                cursor: pointer;
            `;
            
            const modalImg = document.createElement('img');
            modalImg.src = img.src;
            modalImg.style.cssText = `
                max-width: 90%;
                max-height: 90%;
                border-radius: 8px;
            `;
            
            modal.appendChild(modalImg);
            document.body.appendChild(modal);
            
            modal.onclick = () => document.body.removeChild(modal);
        }
        """ 