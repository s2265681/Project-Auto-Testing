import { useState, useCallback, useEffect, useRef } from 'react';
import { toast } from 'react-hot-toast';
import { chatApi } from '../services/api';
import { ChatMessage, ChatResponse, LoadingState, ApiError } from '../types';
import { generateId, getErrorMessage, scrollToBottom } from '../utils';

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  sessionId: string;
  sendMessage: (content: string, device?: string) => Promise<void>;
  clearMessages: () => void;
  loadHistory: () => Promise<void>;
  exportHistory: () => Promise<void>;
  loadingState: LoadingState;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>(() => generateId());
  const [loadingState, setLoadingState] = useState<LoadingState>({ isLoading: false });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottomSmooth = useCallback(() => {
    if (messagesEndRef.current) {
      scrollToBottom(messagesEndRef.current?.parentElement || messagesEndRef.current);
    }
  }, []);

  const addMessage = useCallback((message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: generateId(),
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage;
  }, []);



  const addTypingIndicator = useCallback(() => {
    return addMessage({
      content: '正在思考中...',
      role: 'assistant',
      isTyping: true,
    });
  }, [addMessage]);

  const removeTypingIndicator = useCallback((id: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== id));
  }, []);

  const sendMessage = useCallback(async (content: string, device?: string) => {
    if (!content.trim() || isLoading) return;

    setIsLoading(true);
    setLoadingState({ isLoading: true, message: '发送消息中...' });

    // Add user message
    addMessage({
      content: content.trim(),
      role: 'user',
      device: device, // 保存设备信息
    });

    // Add typing indicator
    const typingMessage = addTypingIndicator();

    // 检测是否为可能的长时间任务
    const isLongTask = /视觉对比|视觉比较|UI对比|UI比较|界面对比|界面比较|visual.*comparison/i.test(content);
    
    // 设置适当的加载提示
    let loadingMessages = ['等待响应...'];
    if (isLongTask) {
      loadingMessages = [
        '正在准备视觉对比...',
        '正在截取网页...',
        '正在获取设计稿...',
        '正在进行图像对比...',
        '正在生成分析报告...'
      ];
    }

    let messageIndex = 0;
    const updateLoadingMessage = () => {
      if (messageIndex < loadingMessages.length - 1) {
        messageIndex++;
        setLoadingState({ 
          isLoading: true, 
          message: loadingMessages[messageIndex]
        });
      }
    };

    // 为长时间任务设置定期更新加载消息
    let loadingInterval: NodeJS.Timeout | null = null;
    if (isLongTask) {
      loadingInterval = setInterval(updateLoadingMessage, 15000); // 每15秒更新一次提示
    }

    try {
      setLoadingState({ 
        isLoading: true, 
        message: loadingMessages[0] + (isLongTask ? ' (预计需要1-3分钟)' : '')
      });
      
      const response: ChatResponse = await chatApi.sendMessage(content, sessionId, device);
      
      // Clear loading interval
      if (loadingInterval) {
        clearInterval(loadingInterval);
      }
      
      // Remove typing indicator
      removeTypingIndicator(typingMessage.id);

      // Add assistant response
      addMessage({
        content: response.message,
        role: 'assistant',
        metadata: {
          intent: response.intent,
          confidence: response.confidence,
          parameters: response.parameters,
        },
      });

      // Update session ID if provided
      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id);
      }

      // Show suggestions as toast if provided
      if (response.suggestions && response.suggestions.length > 0) {
        toast.success(`💡 建议: ${response.suggestions.join(', ')}`);
      }

      // Auto-scroll to bottom
      setTimeout(scrollToBottomSmooth, 100);

    } catch (error) {
      // Clear loading interval
      if (loadingInterval) {
        clearInterval(loadingInterval);
      }
      
      // Remove typing indicator
      removeTypingIndicator(typingMessage.id);

      const apiError = error as ApiError;
      const errorMessage = getErrorMessage(error);

      // 特殊处理超时错误
      if (apiError.code === 'ECONNABORTED' && isLongTask) {
        addMessage({
          content: `⏳ 任务执行时间较长，可能仍在后台处理中。\n\n如果是视觉对比任务，请稍后查看报告目录，或重新发送命令查看结果。\n\n💡 提示：复杂的视觉对比任务可能需要1-5分钟才能完成。`,
          role: 'assistant',
        });
        toast.error('任务超时，但可能仍在后台处理中');
      } else {
        // Add error message
        addMessage({
          content: `❌ 抱歉，发生了错误：${errorMessage}`,
          role: 'assistant',
        });

        // Show error toast
        toast.error(errorMessage);
      }

      // If it's a critical error, suggest retrying
      if (apiError.status === 0 || apiError.status >= 500) {
        toast.error('请检查网络连接或稍后重试');
      }

      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
      setLoadingState({ isLoading: false });
    }
  }, [
    isLoading,
    sessionId,
    addMessage,
    addTypingIndicator,
    removeTypingIndicator,
    scrollToBottomSmooth,
  ]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setSessionId(generateId());
    
    // Clear server-side history
    chatApi.clearHistory(sessionId).catch(error => {
      console.error('Failed to clear server history:', error);
    });

    toast.success('聊天记录已清空');
  }, [sessionId]);

  const loadHistory = useCallback(async () => {
    try {
      setLoadingState({ isLoading: true, message: '加载历史记录...' });
      
      const history = await chatApi.getHistory(sessionId);
      
      const historyMessages: ChatMessage[] = history.messages.map(msg => ({
        ...msg,
        timestamp: new Date(msg.timestamp),
      }));

      setMessages(historyMessages);
      toast.success('历史记录加载成功');
      
      setTimeout(scrollToBottomSmooth, 100);
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      toast.error(`加载历史记录失败: ${errorMessage}`);
      console.error('Failed to load history:', error);
    } finally {
      setLoadingState({ isLoading: false });
    }
  }, [sessionId, scrollToBottomSmooth]);

  const exportHistory = useCallback(async () => {
    try {
      setLoadingState({ isLoading: true, message: '导出历史记录...' });
      
      const data = await chatApi.exportHistory(sessionId);
      
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chat-history-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success('历史记录导出成功');
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      toast.error(`导出历史记录失败: ${errorMessage}`);
      console.error('Failed to export history:', error);
    } finally {
      setLoadingState({ isLoading: false });
    }
  }, [sessionId]);

  // Load initial history on mount
  useEffect(() => {
    loadHistory();
  }, []);

  // Auto-scroll when messages change
  useEffect(() => {
    scrollToBottomSmooth();
  }, [messages, scrollToBottomSmooth]);

  return {
    messages,
    isLoading,
    sessionId,
    sendMessage,
    clearMessages,
    loadHistory,
    exportHistory,
    loadingState,
  };
} 