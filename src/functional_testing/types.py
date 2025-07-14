"""
功能测试类型定义
Functional Testing Type Definitions
"""

from typing import Dict, List, Optional, Any, Union, Literal
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TestStep:
    """测试步骤"""
    action: Literal["click", "input", "navigate", "hover", "wait", "scroll", "custom"]
    selector: Optional[str] = None  # CSS选择器或XPath
    value: Optional[str] = None  # 输入值或自定义脚本
    timeout: Optional[int] = 10  # 超时时间(秒)
    waitFor: Optional[Dict[str, Any]] = None  # 等待条件
    description: Optional[str] = None  # 步骤描述


@dataclass
class TestAssertion:
    """测试断言"""
    type: Literal["dom", "network", "url", "custom"]
    target: Optional[str] = None  # 选择器或URL
    condition: str = ""  # 验证条件
    expected: Any = None  # 期望值
    description: Optional[str] = None  # 断言描述


@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    description: Optional[str] = None
    steps: List[TestStep] = field(default_factory=list)
    assertions: List[TestAssertion] = field(default_factory=list)
    setup: Optional[Dict[str, Any]] = None  # 测试前置条件
    teardown: Optional[Dict[str, Any]] = None  # 测试后置条件


@dataclass
class TestConfig:
    """测试配置"""
    baseUrl: str
    device: str = "desktop"  # desktop, mobile, tablet
    cookies: Optional[str] = None
    localStorage: Optional[str] = None
    headless: bool = True
    slowMo: Optional[int] = None  # 操作间隔(ms)
    viewport: Optional[Dict[str, int]] = None  # 视口设置
    screenshot: Literal["on", "off", "only-on-failure"] = "on"
    timeout: int = 30  # 默认超时时间(秒)


@dataclass
class StepResult:
    """步骤执行结果"""
    step: TestStep
    status: Literal["success", "failed", "skipped"]
    duration: float  # 执行时长(秒)
    screenshot: Optional[str] = None  # 截图路径
    error: Optional[str] = None  # 错误信息
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AssertionResult:
    """断言结果"""
    assertion: TestAssertion
    status: Literal["passed", "failed"]
    actual: Any = None  # 实际值
    error: Optional[str] = None  # 错误信息
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class NetworkRequest:
    """网络请求记录"""
    url: str
    method: str
    status: int
    requestHeaders: Optional[Dict[str, str]] = None
    requestBody: Optional[Any] = None
    responseHeaders: Optional[Dict[str, str]] = None
    responseBody: Optional[Any] = None
    timing: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TestResult:
    """测试结果"""
    testCase: TestCase
    status: Literal["passed", "failed", "skipped"]
    duration: float  # 总耗时(秒)
    steps: List[StepResult] = field(default_factory=list)
    assertions: List[AssertionResult] = field(default_factory=list)
    networkRequests: List[NetworkRequest] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)
    startTime: datetime = field(default_factory=datetime.now)
    endTime: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class TestReport:
    """测试报告"""
    summary: Dict[str, Any]
    environment: Dict[str, Any]
    testResults: List[TestResult] = field(default_factory=list)
    startTime: datetime = field(default_factory=datetime.now)
    endTime: Optional[datetime] = None
    reportPath: Optional[str] = None 