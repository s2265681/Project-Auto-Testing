import React, { useState, useRef, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Toaster } from 'react-hot-toast';
import { cn, scrollToBottom } from '../utils';
import { useChat } from '../hooks/useChat';
import ChatHeader from './ChatHeader';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { Loader2, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

interface ChatAppProps {
  className?: string;
  showHeader?: boolean;
  showWelcome?: boolean;
}

const ChatApp: React.FC<ChatAppProps> = ({
  className,
  showHeader = true,
  showWelcome = true,
}) => {
  const {
    messages,
    isLoading,
    sendMessage,
    clearMessages,
    exportHistory,
    loadingState,
  } = useChat();

  const [showSettings, setShowSettings] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [showTimestamps, setShowTimestamps] = useState(false);
  const [showMetadata, setShowMetadata] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesContainerRef.current) {
      scrollToBottom(messagesContainerRef.current);
    }
  }, [messages]);

  const welcomeExamples = [
    {
      title: "生成测试用例",
      description: "为网站或应用生成自动化测试用例",
      input: "帮我生成一个登录页面的测试用例",
      icon: "🧪"
    },
    {
      title: "视觉对比测试",
      description: "进行UI界面的视觉对比测试（需要1-5分钟）",
      input: "执行视觉对比测试",
      icon: "👁️"
    },
    {
      title: "完整工作流",
      description: "运行完整的自动化测试工作流",
      input: "运行完整的测试工作流",
      icon: "⚙️"
    },
    {
      title: "查看报告",
      description: "查看测试结果和报告",
      input: "显示最新的测试报告",
      icon: "📊"
    }
  ];

  const handleExampleClick = (input: string) => {
    sendMessage(input, 'desktop'); // 示例使用默认桌面设备
  };

  const handleRetry = () => {
    if (messages.length > 0) {
      const lastUserMessage = messages
        .filter(m => m.role === 'user')
        .pop();
      if (lastUserMessage) {
        // 使用原消息的设备类型，如果没有则默认为desktop
        sendMessage(lastUserMessage.content, lastUserMessage.device || 'desktop');
      }
    }
  };

  return (
    <div className={cn(
      "flex flex-col h-screen bg-gray-50 overflow-hidden",
      className
    )}>
      {/* Toast Notifications */}
      <Toaster
        position="top-center"
        toastOptions={{
          duration: 4000,
          className: 'text-sm',
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#ffffff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#ffffff',
            },
          },
        }}
      />

      {/* Header */}
      {showHeader && (
        <ChatHeader
          onClearChat={clearMessages}
          onExportHistory={exportHistory}
          onToggleSettings={() => setShowSettings(!showSettings)}
          onToggleInfo={() => setShowInfo(!showInfo)}
        />
      )}

      {/* Messages Container */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto scrollbar-thin"
      >
        <div className="container-chat py-4">
          {/* Welcome Message */}
          {showWelcome && messages.length === 0 && !isLoading && (
            <div className="text-center py-8 px-4">
              <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-2xl font-bold">AI</span>
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                欢迎使用智能测试助手
              </h2>
              <p className="text-gray-600 mb-8 max-w-md mx-auto">
                我可以帮助您生成测试用例、执行视觉对比测试、运行完整的工作流等。
                选择下面的示例开始对话，或者直接输入您的问题。
              </p>

              {/* Example Buttons */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                {welcomeExamples.map((example, index) => (
                  <button
                    key={index}
                    onClick={() => handleExampleClick(example.input)}
                    className="group p-4 text-left bg-white rounded-lg border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all duration-200"
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{example.icon}</span>
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900 group-hover:text-primary-700 transition-colors">
                          {example.title}
                        </h3>
                        <p className="text-sm text-gray-600 mt-1">
                          {example.description}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          <AnimatePresence mode="popLayout">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                showTimestamp={showTimestamps}
                showMetadata={showMetadata}
              />
            ))}
          </AnimatePresence>

          {/* Loading State */}
          {loadingState.isLoading && (
            <div className="flex items-center justify-center py-8">
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>{loadingState.message || '处理中...'}</span>
              </div>
            </div>
          )}

          {/* Error State */}
          {messages.length > 0 && !isLoading && (
            <div className="flex justify-center py-4">
              <button
                onClick={handleRetry}
                className="flex items-center gap-2 px-4 py-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span>重试上一条消息</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="border-t border-gray-200 p-4 bg-white">
          <h3 className="font-medium text-gray-900 mb-3">设置</h3>
          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={showTimestamps}
                onChange={(e) => setShowTimestamps(e.target.checked)}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">显示时间戳</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={showMetadata}
                onChange={(e) => setShowMetadata(e.target.checked)}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">显示元数据</span>
            </label>
          </div>
        </div>
      )}

      {/* Info Panel */}
      {showInfo && (
        <div className="border-t border-gray-200 p-4 bg-white">
          <h3 className="font-medium text-gray-900 mb-3">系统信息</h3>
          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span>系统运行正常</span>
            </div>
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-blue-500" />
              <span>当前会话: {messages.length} 条消息</span>
            </div>
          </div>
        </div>
      )}

      {/* Input Area */}
      <ChatInput
        onSendMessage={sendMessage}
        isLoading={isLoading}
        disabled={loadingState.isLoading}
      />
    </div>
  );
};

export default ChatApp; 