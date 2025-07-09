"""
Gemini测试用例生成模块
Gemini Test Case Generator Module
"""
import os
import concurrent.futures
import google.generativeai as genai
from typing import List, Dict

class TimeoutError(Exception):
    pass

class GeminiCaseGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        
        # 尝试多个模型，按优先级排序
        self.model_names = [
            'gemini-1.5-flash',
            'gemini-1.5-pro', 
            'gemini-pro',
            'gemini-1.0-pro'
        ]
        
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """初始化可用的模型"""
        for model_name in self.model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                print(f"✅ 成功初始化模型: {model_name}")
                break
            except Exception as e:
                print(f"⚠️  模型 {model_name} 初始化失败: {e}")
                continue
        
        if not self.model:
            raise Exception("无法初始化任何Gemini模型")

    def _call_gemini_api(self, prompt: str):
        """调用Gemini API的内部方法"""
        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=2048,
                temperature=0.7,
            )
        )
        return response.text

    def generate_test_cases(self, prd_text: str, case_count: int = 5) -> str:
        """
        根据PRD文本生成测试用例
        Generate test cases from PRD text
        """
        if not self.model:
            print("⚠️  模型未初始化")
            raise Exception("Gemini模型初始化失败，无法生成测试用例")
        
        prompt = f"""
请根据以下PRD文档内容，自动生成{case_count}条功能测试用例，要求每条用例包含：
- 用例标题
- 前置条件
- 测试步骤
- 预期结果

PRD内容：
{prd_text}

请用中文回答，格式要清晰易读。
"""
        try:
            print("🤖 正在调用Gemini API生成测试用例...")
            
            # 使用ThreadPoolExecutor实现超时
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._call_gemini_api, prompt)
                try:
                    result = future.result(timeout=50)  # 50秒超时
                    print("✅ Gemini API调用成功")
                    return result
                except concurrent.futures.TimeoutError:
                    print("⚠️  Gemini API调用超时")
                    raise TimeoutError("Gemini API调用超时，请检查网络连接或稍后重试")
            
        except TimeoutError:
            print("⚠️  Gemini API调用超时")
            raise TimeoutError("Gemini API调用超时，请检查网络连接或稍后重试")
        except Exception as e:
            print(f"⚠️  Gemini API调用失败: {e}")
            # 重新抛出异常，让调用者处理
            raise e

    def _generate_fallback_test_cases(self, prd_text: str, case_count: int = 5) -> str:
        """
        当Gemini API不可用时的备用测试用例生成
        Fallback test case generation when Gemini API is unavailable
        """
        return f"""
## 🔄 备用测试用例生成 (Gemini API不可用)

基于PRD内容分析，生成以下{case_count}条测试用例：

### 测试用例1: 应用启动测试
- **前置条件**: 设备已安装今汐日历App
- **测试步骤**: 
  1. 点击应用图标启动App
  2. 观察启动画面和加载过程
- **预期结果**: App正常启动，显示主界面

### 测试用例2: 日历界面显示测试  
- **前置条件**: App已启动
- **测试步骤**:
  1. 观察主界面日历显示
  2. 检查当前日期是否正确高亮
  3. 验证界面美观度符合文艺小资风格
- **预期结果**: 日历界面美观，当前日期正确显示

### 测试用例3: 天气信息显示测试
- **前置条件**: 设备联网，已获取定位权限
- **测试步骤**:
  1. 观察主界面天气信息
  2. 验证当前城市和温度显示
  3. 检查天气相关背景音乐
- **预期结果**: 天气信息准确，背景音乐契合天气状态

### 测试用例4: AI每日资讯功能测试
- **前置条件**: 网络连接正常
- **测试步骤**:
  1. 查看每日资讯内容
  2. 验证AI生成的背景图
  3. 检查资讯内容质量
- **预期结果**: 每日资讯内容丰富，背景图美观

### 测试用例5: 分享功能测试
- **前置条件**: App正常运行
- **测试步骤**:
  1. 找到分享功能入口
  2. 选择分享内容
  3. 测试分享到不同平台
- **预期结果**: 分享功能正常，内容格式美观

---
**注意**: 这是基于PRD内容的基础测试用例模板。建议配置Gemini API以获得更智能的测试用例生成。

PRD原文内容:
{prd_text[:200]}...
"""

if __name__ == "__main__":
    # 示例用法
    prd_text = """
【示例PRD】
1. 用户可以注册账号。
2. 用户可以登录系统。
3. 用户可以重置密码。
"""
    generator = GeminiCaseGenerator()
    cases = generator.generate_test_cases(prd_text, case_count=3)
    print("Gemini生成的测试用例：\n", cases) 