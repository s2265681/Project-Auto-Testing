#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能聊天助手主类
Chat Assistant Main Class

整合意图识别、命令执行、对话管理和响应格式化功能
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from src.chat_assistant.intent_recognizer import IntentRecognizer, Intent, IntentType
from src.chat_assistant.command_executor import CommandExecutor, ExecutionResult
from src.chat_assistant.conversation_manager import ConversationManager, Message
from src.chat_assistant.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)

class ChatAssistant:
    """智能聊天助手"""
    
    def __init__(self):
        # 初始化各个组件
        self.intent_recognizer = IntentRecognizer()
        self.command_executor = CommandExecutor()
        self.conversation_manager = ConversationManager()
        self.response_formatter = ResponseFormatter()
        
        logger.info("聊天助手初始化完成")
    
    def process_message(self, message: str, session_id: Optional[str] = None, 
                       user_id: Optional[str] = None, device: Optional[str] = None) -> Dict[str, Any]:
        """
        处理用户消息并返回响应
        
        Args:
            message: 用户消息
            session_id: 会话ID（可选，自动生成）
            user_id: 用户ID（可选）
            device: 设备类型（可选，默认为desktop）
            
        Returns:
            包含响应和元数据的字典
        """
        try:
            # 生成或使用会话ID
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # 确保会话存在
            context = self.conversation_manager.get_context(session_id)
            if not context:
                context = self.conversation_manager.start_conversation(session_id, user_id)
            
            # 创建用户消息
            user_message = self.conversation_manager.create_user_message(session_id, message)
            
            # 识别意图
            intent = self.intent_recognizer.recognize_intent(message)
            logger.info(f"识别意图: {intent.type.value}, 置信度: {intent.confidence:.3f}")
            
            # 更新上下文中的意图
            self.conversation_manager.update_context(session_id, {'last_intent': intent.type.value})
            
            # 获取上下文参数
            context_params = self.conversation_manager.get_context_parameters(session_id)
            
            # 添加设备信息到上下文参数
            if device:
                context_params['device'] = device
            else:
                context_params.setdefault('device', 'desktop')  # 默认为desktop
            
            # 执行命令
            execution_result = self.command_executor.execute_intent(intent, context_params)
            
            # 格式化响应
            response_text = self.response_formatter.format_response(
                execution_result, intent.type, context_params
            )
            
            # 创建助手消息
            assistant_message = self.conversation_manager.create_assistant_message(
                session_id, 
                response_text,
                metadata={
                    'intent_type': intent.type.value,
                    'intent_confidence': intent.confidence,
                    'execution_success': execution_result.success,
                    'execution_time': execution_result.execution_time
                }
            )
            
            # 构建响应
            response = {
                'session_id': session_id,
                'message_id': assistant_message.id,
                'content': response_text,
                'success': execution_result.success,
                'intent': {
                    'type': intent.type.value,
                    'confidence': intent.confidence,
                    'parameters': intent.parameters
                },
                'execution': {
                    'success': execution_result.success,
                    'execution_time': execution_result.execution_time,
                    'data': execution_result.data
                },
                'context': {
                    'parameters': context_params,
                    'message_count': len(self.conversation_manager.get_conversation_history(session_id))
                },
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"消息处理完成: session={session_id}, success={execution_result.success}")
            return response
            
        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}")
            
            # 创建错误响应
            error_response = {
                'session_id': session_id or 'unknown',
                'message_id': f"error_{datetime.now().timestamp()}",
                'content': f"❌ 处理消息时发生错误: {str(e)}",
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            return error_response
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取对话历史"""
        try:
            messages = self.conversation_manager.get_conversation_history(session_id, limit)
            return [message.to_dict() for message in messages]
        except Exception as e:
            logger.error(f"获取对话历史失败: {e}")
            return []
    
    def clear_conversation(self, session_id: str) -> bool:
        """清除对话"""
        try:
            self.conversation_manager.clear_context(session_id)
            logger.info(f"清除对话上下文: session={session_id}")
            return True
        except Exception as e:
            logger.error(f"清除对话失败: {e}")
            return False
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """获取对话摘要"""
        try:
            return self.conversation_manager.get_conversation_summary(session_id)
        except Exception as e:
            logger.error(f"获取对话摘要失败: {e}")
            return {}
    
    def get_intent_examples(self) -> Dict[str, List[str]]:
        """获取意图示例"""
        return self.intent_recognizer.get_intent_examples()
    
    def get_available_commands(self) -> List[str]:
        """获取可用命令列表"""
        return [intent.value for intent in IntentType if intent != IntentType.UNKNOWN]
    
    def test_intent_recognition(self, test_messages: List[str]) -> List[Dict[str, Any]]:
        """测试意图识别"""
        results = []
        
        for message in test_messages:
            intent = self.intent_recognizer.recognize_intent(message)
            results.append({
                'message': message,
                'intent_type': intent.type.value,
                'confidence': intent.confidence,
                'parameters': intent.parameters
            })
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            # 创建一个临时会话来检查状态
            temp_session = str(uuid.uuid4())
            intent = Intent(
                type=IntentType.HEALTH_CHECK,
                confidence=1.0,
                parameters={},
                raw_text="health check"
            )
            
            result = self.command_executor.execute_intent(intent)
            
            return {
                'success': result.success,
                'data': result.data,
                'components': {
                    'intent_recognizer': self.intent_recognizer is not None,
                    'command_executor': self.command_executor is not None,
                    'conversation_manager': self.conversation_manager is not None,
                    'response_formatter': self.response_formatter is not None
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        return self.conversation_manager.cleanup_expired_contexts()
    
    def export_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """导出对话"""
        try:
            return self.conversation_manager.export_conversation(session_id)
        except Exception as e:
            logger.error(f"导出对话失败: {e}")
            return None
    
    def import_conversation(self, data: Dict[str, Any]) -> bool:
        """导入对话"""
        try:
            return self.conversation_manager.import_conversation(data)
        except Exception as e:
            logger.error(f"导入对话失败: {e}")
            return False
    
    def batch_process_messages(self, messages: List[Dict[str, str]], 
                              session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """批量处理消息"""
        responses = []
        current_session = session_id
        
        for msg_data in messages:
            message = msg_data.get('message', '')
            msg_session = msg_data.get('session_id', current_session)
            user_id = msg_data.get('user_id')
            
            if not message:
                continue
            
            response = self.process_message(message, msg_session, user_id)
            responses.append(response)
            
            # 更新当前会话ID
            current_session = response.get('session_id', current_session)
        
        return responses
    
    def get_conversation_statistics(self) -> Dict[str, Any]:
        """获取对话统计信息"""
        try:
            total_sessions = len(self.conversation_manager.contexts)
            total_messages = sum(len(msgs) for msgs in self.conversation_manager.conversations.values())
            
            # 计算活跃会话数
            active_sessions = sum(1 for context in self.conversation_manager.contexts.values() 
                                if self.conversation_manager._is_context_valid(context))
            
            # 最受欢迎的意图
            intent_counts = {}
            for context in self.conversation_manager.contexts.values():
                if context.last_intent:
                    intent_counts[context.last_intent] = intent_counts.get(context.last_intent, 0) + 1
            
            most_popular_intent = max(intent_counts.items(), key=lambda x: x[1]) if intent_counts else None
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'total_messages': total_messages,
                'average_messages_per_session': total_messages / total_sessions if total_sessions > 0 else 0,
                'most_popular_intent': most_popular_intent[0] if most_popular_intent else None,
                'intent_distribution': intent_counts,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取对话统计信息失败: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def suggest_next_action(self, session_id: str) -> Optional[str]:
        """建议下一步操作"""
        try:
            context = self.conversation_manager.get_context(session_id)
            if not context:
                return None
            
            params = context.parameters or {}
            suggestions = []
            
            # 根据已有参数建议操作
            if params.get('document_token') and not params.get('figma_url'):
                suggestions.append("您已提供文档token，可以试试：'生成测试用例' 或提供Figma URL进行视觉对比")
            
            if params.get('figma_url') and not params.get('website_url'):
                suggestions.append("您已提供Figma URL，可以提供网站URL进行视觉对比")
            
            if params.get('website_url') and not params.get('figma_url'):
                suggestions.append("您已提供网站URL，可以提供Figma URL进行视觉对比")
            
            if params.get('document_token') and params.get('figma_url') and params.get('website_url'):
                suggestions.append("您已提供完整参数，可以执行：'完整工作流测试'")
            
            if not suggestions:
                suggestions.append("您可以尝试：'生成测试用例'、'视觉对比'、'查看状态'或'帮助'")
            
            return suggestions[0] if suggestions else None
            
        except Exception as e:
            logger.error(f"生成建议失败: {e}")
            return None 