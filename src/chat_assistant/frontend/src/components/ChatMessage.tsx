import React, { memo } from 'react';
import { motion } from 'framer-motion';
import { Copy, User, Bot, Clock, Zap } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChatMessage as ChatMessageType } from '../types';
import { formatTimestamp, copyToClipboard, cn } from '../utils';
import { toast } from 'react-hot-toast';

interface ChatMessageProps {
  message: ChatMessageType;
  showTimestamp?: boolean;
  showMetadata?: boolean;
  className?: string;
}

const ChatMessage: React.FC<ChatMessageProps> = memo(({
  message,
  showTimestamp = true,
  showMetadata = false,
  className,
}) => {
  const { content, role, timestamp, isTyping, metadata } = message;
  const isUser = role === 'user';
  const isAssistant = role === 'assistant';

  const handleCopy = async () => {
    try {
      await copyToClipboard(content);
      toast.success('消息已复制到剪贴板');
    } catch (error) {
      toast.error('复制失败');
    }
  };

  const messageVariants = {
    initial: { opacity: 0, y: 20, scale: 0.9 },
    animate: { opacity: 1, y: 0, scale: 1 },
    exit: { opacity: 0, y: -20, scale: 0.9 },
  };

  const confidenceColor = metadata?.confidence 
    ? metadata.confidence > 0.8 
      ? 'text-green-600' 
      : metadata.confidence > 0.6 
        ? 'text-yellow-600' 
        : 'text-red-600'
    : 'text-gray-600';

  // Markdown渲染配置
  const markdownComponents = {
    // 代码块样式
    code: ({ className, children, ...props }: any) => {
      const isInline = !className;
      return isInline ? (
        <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800" {...props}>
          {children}
        </code>
      ) : (
        <pre className="bg-gray-100 p-3 rounded-lg overflow-x-auto my-2">
          <code className="font-mono text-sm text-gray-800" {...props}>
            {children}
          </code>
        </pre>
      );
    },
    // 图片样式和错误处理
    img: ({ src, alt, ...props }: any) => {
      return (
        <div className="my-3">
          <img
            src={src}
            alt={alt || '图片'}
            className="max-w-full h-auto rounded-lg shadow-md border"
            onError={(e: any) => {
              e.target.style.display = 'none';
              const errorDiv = document.createElement('div');
              errorDiv.className = 'bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm';
              errorDiv.innerHTML = `🖼️ 图片加载失败: ${alt || src}`;
              e.target.parentNode.appendChild(errorDiv);
            }}
            onLoad={(e: any) => {
              // 图片加载成功后的处理
              e.target.style.opacity = '1';
            }}
            style={{ opacity: '0.8', transition: 'opacity 0.3s', maxHeight: '400px' }}
            {...props}
          />
          {alt && (
            <p className="text-xs text-gray-500 mt-1 text-center italic">
              {alt}
            </p>
          )}
        </div>
      );
    },
    // 链接样式
    a: ({ href, children, ...props }: any) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 hover:text-blue-800 underline"
        {...props}
      >
        {children}
      </a>
    ),
    // 列表样式
    ul: ({ children, ...props }: any) => (
      <ul className="list-disc list-inside space-y-1 my-2" {...props}>
        {children}
      </ul>
    ),
    ol: ({ children, ...props }: any) => (
      <ol className="list-decimal list-inside space-y-1 my-2" {...props}>
        {children}
      </ol>
    ),
    li: ({ children, ...props }: any) => (
      <li className="ml-2" {...props}>
        {children}
      </li>
    ),
    // 标题样式
    h1: ({ children, ...props }: any) => (
      <h1 className="text-xl font-bold mt-4 mb-2" {...props}>
        {children}
      </h1>
    ),
    h2: ({ children, ...props }: any) => (
      <h2 className="text-lg font-bold mt-3 mb-2" {...props}>
        {children}
      </h2>
    ),
    h3: ({ children, ...props }: any) => (
      <h3 className="text-base font-bold mt-2 mb-1" {...props}>
        {children}
      </h3>
    ),
    // 段落样式
    p: ({ children, ...props }: any) => (
      <p className="mb-2 leading-relaxed" {...props}>
        {children}
      </p>
    ),
    // 强调样式
    strong: ({ children, ...props }: any) => (
      <strong className="font-bold text-gray-900" {...props}>
        {children}
      </strong>
    ),
    // 表格样式
    table: ({ children, ...props }: any) => (
      <div className="overflow-x-auto my-3">
        <table className="min-w-full border border-gray-200 rounded-lg" {...props}>
          {children}
        </table>
      </div>
    ),
    thead: ({ children, ...props }: any) => (
      <thead className="bg-gray-50" {...props}>
        {children}
      </thead>
    ),
    th: ({ children, ...props }: any) => (
      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200" {...props}>
        {children}
      </th>
    ),
    td: ({ children, ...props }: any) => (
      <td className="px-3 py-2 text-sm text-gray-900 border-b border-gray-200" {...props}>
        {children}
      </td>
    ),
  };

  return (
    <motion.div
      variants={messageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={cn(
        "flex gap-3 p-4 group hover:bg-gray-50/50 transition-colors",
        isUser && "flex-row-reverse",
        className
      )}
    >
      {/* Avatar */}
      <div className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
        isUser ? "bg-primary-500 text-white" : "bg-gray-200 text-gray-600"
      )}>
        {isUser ? (
          <User className="w-4 h-4" />
        ) : (
          <Bot className="w-4 h-4" />
        )}
      </div>

      {/* Message Content */}
      <div className={cn(
        "flex-1 min-w-0",
        isUser ? "text-right" : "text-left"
      )}>
        {/* Message Bubble */}
        <div className={cn(
          "inline-block message-bubble relative",
          isUser && "message-bubble-user",
          isAssistant && !isTyping && "message-bubble-assistant",
          isTyping && "message-bubble-typing"
        )}>
          {/* Typing Animation */}
          {isTyping ? (
            <div className="loading-dots">
              <div></div>
              <div></div>
              <div></div>
            </div>
          ) : isUser ? (
            // 用户消息保持纯文本显示
            <div className="whitespace-pre-wrap">
              {content}
            </div>
          ) : (
            // 助手消息使用markdown渲染
            <div className="markdown-content">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={markdownComponents}
              >
                {content}
              </ReactMarkdown>
            </div>
          )}

          {/* Copy Button */}
          {!isTyping && (
            <button
              onClick={handleCopy}
              className={cn(
                "absolute top-2 opacity-0 group-hover:opacity-100 transition-opacity",
                "w-6 h-6 rounded-full bg-black/10 hover:bg-black/20 flex items-center justify-center",
                isUser ? "left-2" : "right-2"
              )}
              title="复制消息"
            >
              <Copy className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Metadata */}
        {showMetadata && (metadata || message.device) && !isTyping && (
          <div className={cn(
            "mt-2 text-xs text-gray-500 space-y-1",
            isUser ? "text-right" : "text-left"
          )}>
            {metadata?.intent && (
              <div className="flex items-center gap-1">
                <Zap className="w-3 h-3" />
                <span>意图: {metadata.intent}</span>
                {metadata.confidence && (
                  <span className={cn("font-medium", confidenceColor)}>
                    ({Math.round(metadata.confidence * 100)}%)
                  </span>
                )}
              </div>
            )}
            {message.device && (
              <div className="flex items-center gap-1">
                <span>🖥️ 设备: {message.device === 'mobile' ? '移动端' : message.device === 'tablet' ? '平板' : '桌面端'}</span>
              </div>
            )}
            {metadata?.parameters && Object.keys(metadata.parameters).length > 0 && (
              <div className="text-xs bg-gray-100 rounded px-2 py-1 font-mono">
                {JSON.stringify(metadata.parameters, null, 2)}
              </div>
            )}
          </div>
        )}

        {/* Timestamp */}
        {showTimestamp && (
          <div className={cn(
            "flex items-center gap-1 mt-1 text-xs text-gray-400",
            isUser ? "justify-end" : "justify-start"
          )}>
            <Clock className="w-3 h-3" />
            <span>{formatTimestamp(timestamp)}</span>
          </div>
        )}
      </div>
    </motion.div>
  );
});

ChatMessage.displayName = 'ChatMessage';

export default ChatMessage; 