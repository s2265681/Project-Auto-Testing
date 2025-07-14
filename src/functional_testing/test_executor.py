"""
测试执行器
Test Executor

执行测试步骤和断言，基于现有的ScreenshotCapture功能
"""

import time
import json
import os
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from ..screenshot.capture import ScreenshotCapture
from ..utils.logger import get_logger
from .types import (
    TestStep, TestAssertion, TestCase, TestConfig,
    StepResult, AssertionResult, TestResult, NetworkRequest
)

logger = get_logger(__name__)


class TestExecutor:
    """测试执行器"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.capture = ScreenshotCapture(
            browser='chrome',
            headless=config.headless,
            language='en-US'
        )
        self.network_requests = []
        self.screenshots_dir = None
        self._setup_screenshots_dir()
    
    def _setup_screenshots_dir(self):
        """设置截图目录"""
        self.screenshots_dir = os.path.join(
            "screenshots",
            f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def execute_test_case(self, test_case: TestCase) -> TestResult:
        """
        执行单个测试用例
        
        Args:
            test_case: 测试用例
            
        Returns:
            TestResult: 测试结果
        """
        start_time = datetime.now()
        logger.info(f"开始执行测试用例: {test_case.name}")
        
        test_result = TestResult(
            testCase=test_case,
            status="passed",
            duration=0,
            startTime=start_time
        )
        
        try:
            # 设置浏览器
            self._setup_browser()
            
            # 执行测试步骤
            for step in test_case.steps:
                step_result = self._execute_step(step)
                test_result.steps.append(step_result)
                
                if step_result.status == "failed":
                    test_result.status = "failed"
                    test_result.error = step_result.error
                    break
                
                # 收集网络请求（每步骤后）
                self._collect_network_requests()
                    
                # 如果需要截图
                if self.config.screenshot == "on":
                    screenshot_path = self._take_screenshot(f"step_{len(test_result.steps)}")
                    step_result.screenshot = screenshot_path
                    test_result.screenshots.append(screenshot_path)
            
            # 如果所有步骤都成功，执行断言
            if test_result.status == "passed":
                # 收集网络请求（在断言前）
                self._collect_network_requests()
                
                for assertion in test_case.assertions:
                    assertion_result = self._execute_assertion(assertion)
                    test_result.assertions.append(assertion_result)
                    
                    if assertion_result.status == "failed":
                        test_result.status = "failed"
                        test_result.error = assertion_result.error
                        # 失败时截图
                        if self.config.screenshot in ["on", "only-on-failure"]:
                            screenshot_path = self._take_screenshot(f"assertion_failure_{len(test_result.assertions)}")
                            test_result.screenshots.append(screenshot_path)
            
            # 记录网络请求
            test_result.networkRequests = self.network_requests.copy()
            
        except Exception as e:
            logger.error(f"测试用例执行失败: {e}")
            test_result.status = "failed"
            test_result.error = str(e)
            
            # 失败时截图
            if self.config.screenshot in ["on", "only-on-failure"]:
                screenshot_path = self._take_screenshot("execution_failure")
                test_result.screenshots.append(screenshot_path)
        
        finally:
            # 清理浏览器
            self._cleanup_browser()
            
            # 计算总耗时
            end_time = datetime.now()
            test_result.endTime = end_time
            test_result.duration = (end_time - start_time).total_seconds()
            
            logger.info(f"测试用例完成: {test_case.name}, 状态: {test_result.status}, 耗时: {test_result.duration:.2f}秒")
        
        return test_result
    
    def _setup_browser(self):
        """设置浏览器"""
        device_size = self.capture.DEVICE_SIZES.get(self.config.device, self.capture.DEVICE_SIZES['desktop'])
        device_type = 'mobile' if self.config.device in ['mobile', 'iphone', 'android'] else 'desktop'
        
        self.capture._setup_driver(device_size, device_type=device_type)
        
        # 设置超时
        self.capture.driver.implicitly_wait(5)
        
        # 启用网络请求监控
        self._enable_network_monitoring()
        
        # 如果有初始URL，先访问一次以设置cookies等
        if self.config.baseUrl:
            self.capture.driver.get(self.config.baseUrl)
            time.sleep(1)
            
            # 设置cookies
            if self.config.cookies:
                domain = self.capture.driver.execute_script("return document.domain;")
                self.capture._set_enhanced_cookies(self.config.cookies, domain)
            
            # 设置localStorage
            if self.config.localStorage:
                mobile_devices = ['mobile', 'iphone', 'android']
                self.capture._set_enhanced_local_storage(
                    self.config.localStorage, 
                    self.config.device, 
                    mobile_devices
                )
    
    def _cleanup_browser(self):
        """清理浏览器"""
        if self.capture.driver:
            self.capture.driver.quit()
            self.capture.driver = None
    
    def _enable_network_monitoring(self):
        """启用网络请求监控"""
        try:
            # 注入JavaScript代码来拦截网络请求
            script = """
            // 确保网络请求数组存在
            if (!window.networkRequests) {
                window.networkRequests = [];
            }
            
            // 添加调试日志函数
            window.logNetworkRequest = function(method, url, type, data) {
                try {
                    console.log('[Network Monitor] Captured:', method, url, type, data);
                    var request = {
                        method: method,
                        url: url,
                        timestamp: new Date().toISOString(),
                        type: type,
                        data: data
                    };
                    window.networkRequests.push(request);
                    console.log('[Network Monitor] Added to array. Total requests:', window.networkRequests.length);
                } catch (e) {
                    console.error('[Network Monitor] Error storing request:', e);
                }
            };
            
            // 拦截 XMLHttpRequest
            (function() {
                try {
                    var originalOpen = XMLHttpRequest.prototype.open;
                    var originalSend = XMLHttpRequest.prototype.send;
                    
                    XMLHttpRequest.prototype.open = function(method, url) {
                        this._method = method;
                        this._url = url;
                        console.log('[XHR Monitor] Opening:', method, url);
                        return originalOpen.apply(this, arguments);
                    };
                    
                    XMLHttpRequest.prototype.send = function(data) {
                        try {
                            var method = this._method || 'GET';
                            var url = this._url || '';
                            
                            console.log('[XHR Monitor] Sending:', method, url, data);
                            window.logNetworkRequest(method, url, 'xhr', data);
                        } catch (e) {
                            console.error('[XHR Monitor] Error:', e);
                        }
                        
                        return originalSend.apply(this, arguments);
                    };
                    
                    console.log('[XHR Monitor] XMLHttpRequest monitoring enabled');
                } catch (e) {
                    console.error('[XHR Monitor] Setup error:', e);
                }
            })();
            
            // 拦截 fetch
            (function() {
                try {
                    var originalFetch = window.fetch;
                    window.fetch = function() {
                        try {
                            var url = arguments[0];
                            var options = arguments[1] || {};
                            var method = (options.method || 'GET').toUpperCase();
                            var body = options.body;
                            
                            // 处理相对URL
                            if (typeof url === 'string' && !url.startsWith('http')) {
                                url = window.location.origin + (url.startsWith('/') ? '' : '/') + url;
                            }
                            
                            console.log('[Fetch Monitor] Requesting:', method, url, options);
                            window.logNetworkRequest(method, url, 'fetch', body);
                        } catch (e) {
                            console.error('[Fetch Monitor] Error:', e);
                        }
                        
                        return originalFetch.apply(this, arguments);
                    };
                    
                    console.log('[Fetch Monitor] Fetch monitoring enabled');
                } catch (e) {
                    console.error('[Fetch Monitor] Setup error:', e);
                }
            })();
            
            // 监听所有网络活动（备用方案）
            try {
                var observer = new PerformanceObserver(function(list) {
                    for (var entry of list.getEntries()) {
                        if (entry.entryType === 'resource' && entry.name.includes('api/log')) {
                            console.log('[Performance Monitor] Resource:', entry.name);
                            window.logNetworkRequest('UNKNOWN', entry.name, 'resource', null);
                        }
                    }
                });
                observer.observe({entryTypes: ['resource']});
                console.log('[Performance Monitor] Performance observer enabled');
            } catch (e) {
                console.error('[Performance Monitor] Setup error:', e);
            }
            
            console.log('[Network Monitor] Network monitoring enabled. Array length:', window.networkRequests.length);
            """
            
            self.capture.driver.execute_script(script)
            logger.info("网络请求监控已启用")
            
            # 测试JavaScript监控是否正常工作
            test_result = self.capture.driver.execute_script("return typeof window.networkRequests;")
            array_length = self.capture.driver.execute_script("return window.networkRequests ? window.networkRequests.length : -1;")
            logger.info(f"网络请求监控测试结果: {test_result}, 数组长度: {array_length}")
            
        except Exception as e:
            logger.warning(f"启用网络监控失败: {e}")
    
    def _collect_network_requests(self):
        """收集网络请求"""
        try:
            # 从JavaScript中收集网络请求
            js_requests = self.capture.driver.execute_script("return window.networkRequests || [];")
            
            logger.info(f"JavaScript中的网络请求数量: {len(js_requests)}")
            
            # 获取浏览器控制台日志以便调试
            try:
                logs = self.capture.driver.get_log('browser')
                network_logs = [log for log in logs if any(keyword in log['message'] for keyword in ['[Network Monitor]', '[XHR Monitor]', '[Fetch Monitor]'])]
                
                if network_logs:
                    logger.info(f"网络监控控制台日志 ({len(network_logs)} 条):")
                    for log in network_logs[-10:]:  # 只显示最后10条
                        logger.info(f"  {log['message']}")
                else:
                    logger.warning("未找到网络监控控制台日志")
                    
            except Exception as e:
                logger.warning(f"获取控制台日志失败: {e}")
            
            # 检查数组状态
            array_status = self.capture.driver.execute_script("""
                return {
                    exists: typeof window.networkRequests !== 'undefined',
                    length: window.networkRequests ? window.networkRequests.length : -1,
                    type: typeof window.networkRequests
                };
            """)
            logger.info(f"网络请求数组状态: {array_status}")
            
            for req in js_requests:
                # 检查是否已经存在（避免重复）
                existing = any(nr.url == req['url'] and nr.method == req['method'] 
                             for nr in self.network_requests)
                
                if not existing:
                    network_request = NetworkRequest(
                        url=req['url'],
                        method=req['method'],
                        status=200,  # 默认状态码，实际应该从响应中获取
                        timestamp=datetime.now()
                    )
                    self.network_requests.append(network_request)
                    logger.info(f"收集到网络请求: {req['method']} {req['url']}")
            
            logger.info(f"当前总网络请求数量: {len(self.network_requests)}")
            
        except Exception as e:
            logger.warning(f"收集网络请求失败: {e}")
    
    def _execute_step(self, step: TestStep) -> StepResult:
        """执行单个步骤"""
        start_time = datetime.now()
        logger.info(f"执行步骤: {step.action} - {step.description}")
        
        step_result = StepResult(
            step=step,
            status="success",
            duration=0,
            timestamp=start_time
        )
        
        try:
            if step.action == "navigate":
                self._navigate(step.value)
            elif step.action == "click":
                self._click(step.selector)
            elif step.action == "input":
                self._input(step.selector, step.value)
            elif step.action == "wait":
                self._wait(step)
            elif step.action == "hover":
                self._hover(step.selector)
            elif step.action == "scroll":
                self._scroll(step.selector)
            elif step.action == "screenshot":
                # 截图操作
                screenshot_path = self._take_screenshot("manual_screenshot")
                step_result.screenshot = screenshot_path
            else:
                raise ValueError(f"不支持的操作类型: {step.action}")
                
            # 添加操作间隔
            if self.config.slowMo:
                time.sleep(self.config.slowMo / 1000)
            
        except Exception as e:
            logger.error(f"步骤执行失败: {e}")
            step_result.status = "failed"
            step_result.error = str(e)
        
        finally:
            end_time = datetime.now()
            step_result.duration = (end_time - start_time).total_seconds()
        
        return step_result
    
    def _navigate(self, url: str):
        """导航到URL"""
        self.capture.driver.get(url)
        # 等待页面加载完成
        WebDriverWait(self.capture.driver, self.config.timeout).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
        # 页面导航后重新启用网络监控
        self._enable_network_monitoring()
    
    def _click(self, selector: str):
        """点击元素"""
        element = self._find_element(selector)
        
        # 滚动到元素可见
        self.capture.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
        
        # 等待元素可点击
        WebDriverWait(self.capture.driver, self.config.timeout).until(
            EC.element_to_be_clickable(element)
        )
        
        element.click()
    
    def _input(self, selector: str, value: str):
        """输入文本"""
        element = self._find_element(selector)
        
        # 滚动到元素可见
        self.capture.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
        
        # 清空并输入
        element.clear()
        element.send_keys(value)
    
    def _wait(self, step: TestStep):
        """等待操作"""
        if step.waitFor:
            if step.waitFor.get("selector"):
                # 等待元素出现
                WebDriverWait(self.capture.driver, step.timeout or self.config.timeout).until(
                    EC.presence_of_element_located(self._get_locator(step.waitFor["selector"]))
                )
            elif step.waitFor.get("networkIdle"):
                # 等待网络空闲（简化实现）
                time.sleep(2)
            elif step.waitFor.get("function"):
                # 等待自定义函数
                WebDriverWait(self.capture.driver, step.timeout or self.config.timeout).until(
                    lambda driver: driver.execute_script(step.waitFor["function"])
                )
        else:
            # 简单等待
            time.sleep(step.timeout or 3)
    
    def _hover(self, selector: str):
        """悬停元素"""
        element = self._find_element(selector)
        ActionChains(self.capture.driver).move_to_element(element).perform()
    
    def _scroll(self, selector: str):
        """滚动到元素"""
        element = self._find_element(selector)
        self.capture.driver.execute_script("arguments[0].scrollIntoView(true);", element)
    
    def _find_element(self, selector: str):
        """查找元素"""
        if not selector:
            raise ValueError("选择器不能为空")
        
        # 支持XPath和CSS选择器
        if selector.startswith('/'):
            # XPath
            return WebDriverWait(self.capture.driver, self.config.timeout).until(
                EC.presence_of_element_located((By.XPATH, selector))
            )
        else:
            # CSS选择器
            return WebDriverWait(self.capture.driver, self.config.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
    
    def _get_locator(self, selector: str) -> Tuple[str, str]:
        """获取定位器"""
        if selector.startswith('/'):
            return (By.XPATH, selector)
        else:
            return (By.CSS_SELECTOR, selector)
    
    def _execute_assertion(self, assertion: TestAssertion) -> AssertionResult:
        """执行断言"""
        start_time = datetime.now()
        logger.info(f"执行断言: {assertion.type} - {assertion.description}")
        
        assertion_result = AssertionResult(
            assertion=assertion,
            status="passed",
            timestamp=start_time
        )
        
        try:
            if assertion.type == "dom":
                actual = self._check_dom_assertion(assertion)
            elif assertion.type == "network":
                actual = self._check_network_assertion(assertion)
            elif assertion.type == "url":
                actual = self._check_url_assertion(assertion)
            else:
                raise ValueError(f"不支持的断言类型: {assertion.type}")
            
            assertion_result.actual = actual
            
            # 验证期望值
            if assertion.condition == "exists":
                if not actual:
                    assertion_result.status = "failed"
                    assertion_result.error = f"元素不存在: {assertion.target}"
            elif assertion.condition == "text_equals":
                if actual != assertion.expected:
                    assertion_result.status = "failed"
                    assertion_result.error = f"文本不匹配，期望: '{assertion.expected}', 实际: '{actual}'"
            elif assertion.condition == "called":
                if not actual:
                    assertion_result.status = "failed"
                    assertion_result.error = f"接口未被调用: {assertion.target}"
            
        except Exception as e:
            logger.error(f"断言执行失败: {e}")
            assertion_result.status = "failed"
            assertion_result.error = str(e)
        
        return assertion_result
    
    def _check_dom_assertion(self, assertion: TestAssertion) -> Any:
        """检查DOM断言"""
        if assertion.condition == "exists":
            try:
                element = self._find_element(assertion.target)
                return element is not None
            except:
                return False
        elif assertion.condition == "text_equals":
            try:
                element = self._find_element(assertion.target)
                return element.text.strip()
            except:
                return ""
        else:
            raise ValueError(f"不支持的DOM断言条件: {assertion.condition}")
    
    def _check_network_assertion(self, assertion: TestAssertion) -> Any:
        """检查网络断言"""
        if assertion.condition == "called":
            # 检查是否有匹配的网络请求
            target_path = assertion.target
            for request in self.network_requests:
                if target_path in request.url:
                    return True
            return False
        else:
            raise ValueError(f"不支持的网络断言条件: {assertion.condition}")
    
    def _check_url_assertion(self, assertion: TestAssertion) -> Any:
        """检查URL断言"""
        current_url = self.capture.driver.current_url
        if assertion.condition == "equals":
            return current_url == assertion.expected
        elif assertion.condition == "contains":
            return assertion.expected in current_url
        else:
            raise ValueError(f"不支持的URL断言条件: {assertion.condition}")
    
    def _take_screenshot(self, name: str) -> str:
        """截图"""
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join(self.screenshots_dir, filename)
        
        try:
            self.capture.driver.save_screenshot(filepath)
            logger.info(f"截图保存: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None 