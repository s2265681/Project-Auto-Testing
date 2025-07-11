import React, { useState, useEffect, memo } from 'react';
import { 
  Settings, 
  Download, 
  Trash2, 
  RefreshCw, 
  Info,
  Minimize2,
  Maximize2,
  X
} from 'lucide-react';
import { cn } from '../utils';
import { ChatStatus } from '../types';
import { chatApi } from '../services/api';

interface ChatHeaderProps {
  title?: string;
  onClearChat?: () => void;
  onExportHistory?: () => void;
  onToggleSettings?: () => void;
  onToggleInfo?: () => void;
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
  onClose?: () => void;
  showControls?: boolean;
  className?: string;
}

const ChatHeader: React.FC<ChatHeaderProps> = memo(({
  title = "智能测试助手",
  onClearChat,
  onExportHistory,
  onToggleSettings,
  onToggleInfo,
  isMinimized = false,
  onToggleMinimize,
  onClose,
  showControls = true,
  className,
}) => {
  const [status, setStatus] = useState<ChatStatus | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchStatus = async () => {
    try {
      setIsRefreshing(true);
      const statusData = await chatApi.getStatus();
      setStatus(statusData);
    } catch (error) {
      console.error('Failed to fetch status:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const handleClearChat = () => {
    if (onClearChat) {
      const confirmed = window.confirm('确定要清空聊天记录吗？此操作不可撤销。');
      if (confirmed) {
        onClearChat();
      }
    }
  };

  const handleExportHistory = () => {
    if (onExportHistory) {
      onExportHistory();
    }
  };

  const getStatusColor = (status: ChatStatus['status']) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'degraded':
        return 'bg-yellow-500';
      case 'unhealthy':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = (status: ChatStatus['status']) => {
    switch (status) {
      case 'healthy':
        return '正常运行';
      case 'degraded':
        return '性能下降';
      case 'unhealthy':
        return '服务异常';
      default:
        return '未知状态';
    }
  };

  return (
    <div className={cn(
      "flex items-center justify-between p-4 bg-white border-b border-gray-200",
      "sticky top-0 z-10 backdrop-blur-sm bg-white/95",
      className
    )}>
      {/* Left Side - Title and Status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center">
            <span className="text-white text-sm font-bold">AI</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
            {status && (
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  getStatusColor(status.status)
                )}></div>
                <span>{getStatusText(status.status)}</span>
                {status.active_sessions > 0 && (
                  <span className="ml-1">
                    • {status.active_sessions} 活跃会话
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Side - Controls */}
      {showControls && (
        <div className="flex items-center gap-1">
          {/* Refresh Status */}
          <button
            onClick={fetchStatus}
            disabled={isRefreshing}
            className={cn(
              "p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors",
              "focus:outline-none focus:ring-2 focus:ring-primary-500",
              isRefreshing && "animate-spin"
            )}
            title="刷新状态"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          {/* Info */}
          {onToggleInfo && (
            <button
              onClick={onToggleInfo}
              className={cn(
                "p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors",
                "focus:outline-none focus:ring-2 focus:ring-primary-500"
              )}
              title="系统信息"
            >
              <Info className="w-4 h-4" />
            </button>
          )}

          {/* Export History */}
          {onExportHistory && (
            <button
              onClick={handleExportHistory}
              className={cn(
                "p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors",
                "focus:outline-none focus:ring-2 focus:ring-primary-500"
              )}
              title="导出历史记录"
            >
              <Download className="w-4 h-4" />
            </button>
          )}

          {/* Settings */}
          {onToggleSettings && (
            <button
              onClick={onToggleSettings}
              className={cn(
                "p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors",
                "focus:outline-none focus:ring-2 focus:ring-primary-500"
              )}
              title="设置"
            >
              <Settings className="w-4 h-4" />
            </button>
          )}

          {/* Clear Chat */}
          {onClearChat && (
            <button
              onClick={handleClearChat}
              className={cn(
                "p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors",
                "focus:outline-none focus:ring-2 focus:ring-red-500"
              )}
              title="清空聊天"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}

          {/* Window Controls */}
          {onToggleMinimize && (
            <button
              onClick={onToggleMinimize}
              className={cn(
                "p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors",
                "focus:outline-none focus:ring-2 focus:ring-primary-500"
              )}
              title={isMinimized ? "展开" : "最小化"}
            >
              {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
            </button>
          )}

          {onClose && (
            <button
              onClick={onClose}
              className={cn(
                "p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors",
                "focus:outline-none focus:ring-2 focus:ring-red-500"
              )}
              title="关闭"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      )}
    </div>
  );
});

ChatHeader.displayName = 'ChatHeader';

export default ChatHeader; 