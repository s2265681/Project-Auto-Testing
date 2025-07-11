#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
聊天助手测试脚本
Chat Assistant Test Script

测试聊天助手的各项功能
"""

import os
import sys
import json
import asyncio
import logging
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.chat_assistant.chat_assistant import ChatAssistant
from src.chat_assistant.intent_recognizer import IntentRecognizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

class ChatAssistantTester:
    """聊天助手测试器"""
    
    def __init__(self):
        self.chat_assistant = ChatAssistant()
        self.intent_recognizer = IntentRecognizer()
        self.test_messages = [
            # 帮助相关
            "帮助",
            "你能做什么",
            "使用说明",
            
            # 测试用例生成
            "生成测试用例",
            "根据PRD生成测试用例",
            "文档token: ZzVudkYQqobhj7xn19GcZ3LFnwd 生成测试用例",
            
            # 视觉对比
            "视觉对比",
            "UI对比",
            "对比网站 https://www.example.com 和 Figma https://figma.com/xxx",
            
            # 完整工作流
            "完整测试",
            "执行完整工作流",
            "全流程测试",
            
            # 状态查询
            "检查状态",
            "查看状态",
            "系统状态如何",
            
            # 报告查看
            "查看报告",
            "看看报告",
            "最近的测试报告",
            
            # 项目列表
            "列出项目",
            "项目列表",
            "有哪些项目",
            
            # 健康检查
            "健康检查",
            "系统正常吗",
            "服务状态",
            
            # 复杂测试
            "我想用文档 ZzVudkYQqobhj7xn19GcZ3LFnwd 生成测试用例",
            "对比移动端 https://m.example.com 和 https://figma.com/mobile",
            "完整测试 文档:ZzVudkYQqobhj7xn19GcZ3LFnwd 网站:https://example.com Figma:https://figma.com/xxx"
        ]
    
    def test_intent_recognition(self):
        """测试意图识别"""
        logger.info("🧪 测试意图识别功能...")
        
        results = []
        for message in self.test_messages:
            intent = self.intent_recognizer.recognize_intent(message)
            results.append({
                'message': message,
                'intent_type': intent.type.value,
                'confidence': intent.confidence,
                'parameters': intent.parameters
            })
            
            logger.info(f"输入: {message}")
            logger.info(f"意图: {intent.type.value} (置信度: {intent.confidence:.3f})")
            logger.info(f"参数: {intent.parameters}")
            logger.info("-" * 60)
        
        return results
    
    def test_chat_processing(self):
        """测试聊天处理"""
        logger.info("🤖 测试聊天处理功能...")
        
        session_id = "test_session_001"
        results = []
        
        for message in self.test_messages[:10]:  # 测试前10条消息
            logger.info(f"处理消息: {message}")
            
            try:
                response = self.chat_assistant.process_message(
                    message=message,
                    session_id=session_id
                )
                
                results.append({
                    'input': message,
                    'success': response.get('success', False),
                    'intent_type': response.get('intent', {}).get('type'),
                    'confidence': response.get('intent', {}).get('confidence'),
                    'response_preview': response.get('content', '')[:100] + '...'
                })
                
                logger.info(f"响应: {response.get('content', '')[:100]}...")
                logger.info(f"成功: {response.get('success', False)}")
                logger.info("-" * 60)
                
            except Exception as e:
                logger.error(f"处理消息失败: {e}")
                results.append({
                    'input': message,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def test_conversation_context(self):
        """测试对话上下文"""
        logger.info("💬 测试对话上下文功能...")
        
        session_id = "test_session_002"
        
        # 测试参数提取和上下文维护
        test_sequence = [
            "我有一个文档token: ZzVudkYQqobhj7xn19GcZ3LFnwd",
            "还有Figma地址: https://figma.com/design/xxx",
            "以及网站: https://example.com",
            "现在执行完整工作流",
            "检查状态",
            "清除上下文",
            "再次检查状态"
        ]
        
        results = []
        for i, message in enumerate(test_sequence):
            logger.info(f"步骤 {i+1}: {message}")
            
            try:
                response = self.chat_assistant.process_message(
                    message=message,
                    session_id=session_id
                )
                
                # 获取上下文信息
                context = response.get('context', {})
                parameters = context.get('parameters', {})
                
                results.append({
                    'step': i + 1,
                    'input': message,
                    'success': response.get('success', False),
                    'parameters': parameters,
                    'message_count': context.get('message_count', 0)
                })
                
                logger.info(f"当前参数: {parameters}")
                logger.info(f"消息总数: {context.get('message_count', 0)}")
                logger.info("-" * 60)
                
            except Exception as e:
                logger.error(f"步骤 {i+1} 失败: {e}")
                results.append({
                    'step': i + 1,
                    'input': message,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def test_system_functions(self):
        """测试系统功能"""
        logger.info("🔧 测试系统功能...")
        
        results = {}
        
        # 测试系统状态
        try:
            status = self.chat_assistant.get_system_status()
            results['system_status'] = status
            logger.info(f"系统状态: {status.get('success', False)}")
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            results['system_status'] = {'error': str(e)}
        
        # 测试统计信息
        try:
            stats = self.chat_assistant.get_conversation_statistics()
            results['statistics'] = stats
            logger.info(f"统计信息: {stats}")
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            results['statistics'] = {'error': str(e)}
        
        # 测试意图示例
        try:
            examples = self.chat_assistant.get_intent_examples()
            results['examples'] = examples
            logger.info(f"意图示例数量: {len(examples)}")
        except Exception as e:
            logger.error(f"获取意图示例失败: {e}")
            results['examples'] = {'error': str(e)}
        
        return results
    
    def test_error_handling(self):
        """测试错误处理"""
        logger.info("⚠️ 测试错误处理...")
        
        error_cases = [
            "",  # 空消息
            "   ",  # 空白消息
            "生成测试用例",  # 缺少必要参数
            "视觉对比",  # 缺少URL
            "完整工作流",  # 缺少所有参数
            "无意义的随机文本 xyz123 abc456",  # 无法识别的意图
        ]
        
        results = []
        session_id = "test_session_error"
        
        for message in error_cases:
            logger.info(f"测试错误情况: '{message}'")
            
            try:
                response = self.chat_assistant.process_message(
                    message=message,
                    session_id=session_id
                )
                
                results.append({
                    'input': message,
                    'success': response.get('success', False),
                    'has_error_handling': not response.get('success', True),
                    'response_preview': response.get('content', '')[:100] + '...'
                })
                
                logger.info(f"错误处理正常: {not response.get('success', True)}")
                logger.info("-" * 60)
                
            except Exception as e:
                logger.error(f"意外错误: {e}")
                results.append({
                    'input': message,
                    'success': False,
                    'unexpected_error': str(e)
                })
        
        return results
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始聊天助手全面测试...")
        
        test_results = {
            'timestamp': asyncio.get_event_loop().time(),
            'tests': {}
        }
        
        # 1. 意图识别测试
        try:
            test_results['tests']['intent_recognition'] = self.test_intent_recognition()
        except Exception as e:
            logger.error(f"意图识别测试失败: {e}")
            test_results['tests']['intent_recognition'] = {'error': str(e)}
        
        # 2. 聊天处理测试
        try:
            test_results['tests']['chat_processing'] = self.test_chat_processing()
        except Exception as e:
            logger.error(f"聊天处理测试失败: {e}")
            test_results['tests']['chat_processing'] = {'error': str(e)}
        
        # 3. 对话上下文测试
        try:
            test_results['tests']['conversation_context'] = self.test_conversation_context()
        except Exception as e:
            logger.error(f"对话上下文测试失败: {e}")
            test_results['tests']['conversation_context'] = {'error': str(e)}
        
        # 4. 系统功能测试
        try:
            test_results['tests']['system_functions'] = self.test_system_functions()
        except Exception as e:
            logger.error(f"系统功能测试失败: {e}")
            test_results['tests']['system_functions'] = {'error': str(e)}
        
        # 5. 错误处理测试
        try:
            test_results['tests']['error_handling'] = self.test_error_handling()
        except Exception as e:
            logger.error(f"错误处理测试失败: {e}")
            test_results['tests']['error_handling'] = {'error': str(e)}
        
        return test_results
    
    def generate_test_report(self, results: Dict[str, Any]):
        """生成测试报告"""
        logger.info("📊 生成测试报告...")
        
        report = {
            'summary': {
                'total_tests': len(results.get('tests', {})),
                'passed_tests': 0,
                'failed_tests': 0,
                'timestamp': results.get('timestamp')
            },
            'details': results.get('tests', {})
        }
        
        # 统计测试结果
        for test_name, test_result in results.get('tests', {}).items():
            if isinstance(test_result, dict) and 'error' in test_result:
                report['summary']['failed_tests'] += 1
            else:
                report['summary']['passed_tests'] += 1
        
        # 保存报告
        report_file = f"test_report_chat_assistant_{int(asyncio.get_event_loop().time())}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"测试报告已保存: {report_file}")
            
            # 打印摘要
            logger.info("=" * 60)
            logger.info("📋 测试摘要")
            logger.info("=" * 60)
            logger.info(f"总测试数: {report['summary']['total_tests']}")
            logger.info(f"通过测试: {report['summary']['passed_tests']}")
            logger.info(f"失败测试: {report['summary']['failed_tests']}")
            logger.info(f"成功率: {(report['summary']['passed_tests'] / report['summary']['total_tests'] * 100):.1f}%")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"保存测试报告失败: {e}")
        
        return report

def main():
    """主函数"""
    logger.info("🧪 聊天助手测试开始...")
    
    tester = ChatAssistantTester()
    results = tester.run_all_tests()
    report = tester.generate_test_report(results)
    
    logger.info("✅ 聊天助手测试完成!")
    
    return report

if __name__ == "__main__":
    try:
        report = main()
        exit(0)
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        exit(1) 