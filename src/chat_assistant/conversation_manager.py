#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
对话管理器模块
Conversation Manager Module

管理用户对话上下文和历史记录
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """消息对象"""
    id: str
    type: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    user_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    last_intent: Optional[str] = None
    last_activity: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if self.last_activity:
            data['last_activity'] = self.last_activity.isoformat()
        return data

class ConversationManager:
    """对话管理器"""
    
    def __init__(self, max_history: int = 100, context_timeout: int = 3600):
        self.max_history = max_history
        self.context_timeout = context_timeout  # 上下文超时时间（秒）
        
        # 存储对话历史和上下文
        self.conversations: Dict[str, List[Message]] = defaultdict(list)
        self.contexts: Dict[str, ConversationContext] = {}
        
        # 参数提取和存储
        self.parameter_keys = [
            'document_token', 'figma_url', 'website_url', 'device',
            'project_name', 'app_token', 'table_id', 'record_id'
        ]
    
    def start_conversation(self, session_id: str, user_id: Optional[str] = None) -> ConversationContext:
        """开始新对话"""
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            parameters={},
            last_activity=datetime.now()
        )
        
        self.contexts[session_id] = context
        
        # 发送欢迎消息
        welcome_message = Message(
            id=f"msg_{datetime.now().timestamp()}",
            type="assistant",
            content="🤖 您好！我是自动化测试助手。\n\n我可以帮您执行测试用例生成、视觉对比、完整工作流等操作。\n\n输入 '帮助' 查看详细使用说明。",
            timestamp=datetime.now(),
            metadata={'type': 'welcome'}
        )
        
        self.add_message(session_id, welcome_message)
        
        logger.info(f"新对话开始: session_id={session_id}, user_id={user_id}")
        return context
    
    def add_message(self, session_id: str, message: Message) -> None:
        """添加消息到对话历史"""
        # 确保上下文存在
        if session_id not in self.contexts:
            self.start_conversation(session_id)
        
        # 更新上下文活动时间
        self.contexts[session_id].last_activity = datetime.now()
        
        # 添加消息到历史
        self.conversations[session_id].append(message)
        
        # 限制历史消息数量
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]
        
        # 如果是用户消息，尝试提取参数
        if message.type == "user":
            self._extract_and_store_parameters(session_id, message.content)
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Message]:
        """获取对话历史"""
        messages = self.conversations.get(session_id, [])
        if limit:
            messages = messages[-limit:]
        return messages
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """获取对话上下文"""
        context = self.contexts.get(session_id)
        if context and self._is_context_valid(context):
            return context
        return None
    
    def update_context(self, session_id: str, updates: Dict[str, Any]) -> None:
        """更新对话上下文"""
        if session_id in self.contexts:
            context = self.contexts[session_id]
            
            # 更新参数
            if 'parameters' in updates:
                if context.parameters is None:
                    context.parameters = {}
                context.parameters.update(updates['parameters'])
            
            # 更新其他属性
            for key, value in updates.items():
                if key != 'parameters' and hasattr(context, key):
                    setattr(context, key, value)
            
            # 更新活动时间
            context.last_activity = datetime.now()
    
    def clear_context(self, session_id: str) -> None:
        """清除对话上下文"""
        if session_id in self.contexts:
            self.contexts[session_id].parameters = {}
            self.contexts[session_id].last_intent = None
    
    def get_context_parameters(self, session_id: str) -> Dict[str, Any]:
        """获取上下文参数"""
        context = self.get_context(session_id)
        if context and context.parameters:
            return context.parameters.copy()
        return {}
    
    def create_user_message(self, session_id: str, content: str) -> Message:
        """创建用户消息"""
        message = Message(
            id=f"msg_{datetime.now().timestamp()}",
            type="user",
            content=content,
            timestamp=datetime.now(),
            metadata={'session_id': session_id}
        )
        
        self.add_message(session_id, message)
        return message
    
    def create_assistant_message(self, session_id: str, content: str, 
                                metadata: Optional[Dict[str, Any]] = None) -> Message:
        """创建助手消息"""
        message = Message(
            id=f"msg_{datetime.now().timestamp()}",
            type="assistant",
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.add_message(session_id, message)
        return message
    
    def _extract_and_store_parameters(self, session_id: str, content: str) -> None:
        """从消息内容中提取并存储参数"""
        extracted_params = {}
        
        # 使用简单的正则表达式提取参数
        import re
        
        # 提取URL
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, content)
        if urls:
            for url in urls:
                if 'figma.com' in url:
                    extracted_params['figma_url'] = url
                elif not extracted_params.get('website_url'):
                    extracted_params['website_url'] = url
        
        # 提取文档token
        token_patterns = [
            r'token[：:]\s*([A-Za-z0-9]{20,})',
            r'文档[：:]\s*([A-Za-z0-9]{20,})',
            r'([A-Za-z0-9]{20,})'
        ]
        
        for pattern in token_patterns:
            matches = re.findall(pattern, content)
            if matches:
                extracted_params['document_token'] = matches[0]
                break
        
        # 提取设备类型
        if re.search(r'移动端|手机|mobile', content, re.IGNORECASE):
            extracted_params['device'] = 'mobile'
        elif re.search(r'桌面端|电脑|desktop', content, re.IGNORECASE):
            extracted_params['device'] = 'desktop'
        elif re.search(r'平板|tablet', content, re.IGNORECASE):
            extracted_params['device'] = 'tablet'
        
        # 提取项目名称
        project_pattern = r'项目[：:]\s*([^\s]+)'
        project_match = re.search(project_pattern, content)
        if project_match:
            extracted_params['project_name'] = project_match.group(1)
        
        # 存储提取的参数
        if extracted_params:
            self.update_context(session_id, {'parameters': extracted_params})
            logger.info(f"从消息中提取参数: {extracted_params}")
    
    def _is_context_valid(self, context: ConversationContext) -> bool:
        """检查上下文是否有效（未超时）"""
        if not context.last_activity:
            return False
        
        now = datetime.now()
        time_diff = (now - context.last_activity).total_seconds()
        return time_diff < self.context_timeout
    
    def cleanup_expired_contexts(self) -> int:
        """清理过期的上下文"""
        expired_sessions = []
        
        for session_id, context in self.contexts.items():
            if not self._is_context_valid(context):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.contexts[session_id]
            if session_id in self.conversations:
                del self.conversations[session_id]
        
        logger.info(f"清理了 {len(expired_sessions)} 个过期的对话上下文")
        return len(expired_sessions)
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """获取对话摘要"""
        context = self.get_context(session_id)
        messages = self.get_conversation_history(session_id)
        
        summary = {
            'session_id': session_id,
            'message_count': len(messages),
            'context_valid': context is not None,
            'parameters': context.parameters if context else {},
            'last_intent': context.last_intent if context else None,
            'last_activity': context.last_activity.isoformat() if context and context.last_activity else None,
            'recent_messages': [msg.to_dict() for msg in messages[-5:]]  # 最近5条消息
        }
        
        return summary
    
    def export_conversation(self, session_id: str) -> Dict[str, Any]:
        """导出对话记录"""
        context = self.get_context(session_id)
        messages = self.get_conversation_history(session_id)
        
        export_data = {
            'session_id': session_id,
            'context': context.to_dict() if context else None,
            'messages': [msg.to_dict() for msg in messages],
            'export_timestamp': datetime.now().isoformat()
        }
        
        return export_data
    
    def import_conversation(self, data: Dict[str, Any]) -> bool:
        """导入对话记录"""
        try:
            session_id = data['session_id']
            
            # 导入上下文
            if data['context']:
                context_data = data['context']
                context = ConversationContext(
                    session_id=context_data['session_id'],
                    user_id=context_data.get('user_id'),
                    parameters=context_data.get('parameters', {}),
                    last_intent=context_data.get('last_intent'),
                    last_activity=datetime.fromisoformat(context_data['last_activity']) if context_data.get('last_activity') else None
                )
                self.contexts[session_id] = context
            
            # 导入消息
            messages = []
            for msg_data in data['messages']:
                message = Message(
                    id=msg_data['id'],
                    type=msg_data['type'],
                    content=msg_data['content'],
                    timestamp=datetime.fromisoformat(msg_data['timestamp']),
                    metadata=msg_data.get('metadata')
                )
                messages.append(message)
            
            self.conversations[session_id] = messages
            
            logger.info(f"成功导入对话记录: session_id={session_id}")
            return True
            
        except Exception as e:
            logger.error(f"导入对话记录失败: {e}")
            return False 