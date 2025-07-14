import React, { useState, useRef, useCallback, KeyboardEvent } from 'react';
import { Send, Loader2, Mic, MicOff, Paperclip, Monitor, Smartphone, Tablet } from 'lucide-react';
import { cn } from '../utils';
import { toast } from 'react-hot-toast';

interface ChatInputProps {
  onSendMessage: (message: string, device?: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading = false,
  placeholder = "输入您的问题...",
  className,
  disabled = false,
}) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<'desktop' | 'mobile' | 'tablet'>('desktop');
  const [showDeviceSelector, setShowDeviceSelector] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Device options configuration
  const deviceOptions = [
    { 
      id: 'desktop' as const, 
      label: 'PC端', 
      icon: Monitor,
      description: '桌面端 (1920x1080)' 
    },
    { 
      id: 'mobile' as const, 
      label: '移动端', 
      icon: Smartphone,
      description: '手机端 (375x667)' 
    },
    { 
      id: 'tablet' as const, 
      label: '平板', 
      icon: Tablet,
      description: '平板端 (768x1024)' 
    }
  ];

  const currentDevice = deviceOptions.find(option => option.id === selectedDevice);

  const handleSend = useCallback(() => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage || isLoading || disabled) return;

    // 直接传递设备参数而不是追加到消息文本中
    onSendMessage(trimmedMessage, selectedDevice);
    setMessage('');
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [message, isLoading, disabled, selectedDevice, onSendMessage]);

  const handleKeyDown = useCallback((event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const handleInput = useCallback(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, []);

  const handleVoiceInput = useCallback(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      toast.error('您的浏览器不支持语音识别');
      return;
    }

    if (isRecording) {
      setIsRecording(false);
      // Stop recording logic would go here
      return;
    }

    setIsRecording(true);
    
    // This would be implemented with the Web Speech API
    // For now, just show a placeholder
    toast.success('语音识别功能正在开发中');
    setTimeout(() => setIsRecording(false), 2000);
  }, [isRecording]);

  const handleFileUpload = useCallback(() => {
    // File upload logic would go here
    toast.success('文件上传功能正在开发中');
  }, []);

  return (
    <div className={cn(
      "flex flex-col gap-2 p-4 bg-white border-t border-gray-200",
      className
    )}>
      {/* Device Selector */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">设备:</span>
          <div className="relative">
            <button
              onClick={() => setShowDeviceSelector(!showDeviceSelector)}
              disabled={disabled || isLoading}
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors",
                "focus:outline-none focus:ring-2 focus:ring-primary-500",
                (disabled || isLoading) && "opacity-50 cursor-not-allowed"
              )}
            >
              {currentDevice && <currentDevice.icon className="w-4 h-4" />}
              <span>{currentDevice?.label}</span>
              <svg className={cn("w-4 h-4 transition-transform", showDeviceSelector && "rotate-180")} 
                   fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {showDeviceSelector && (
              <div className="absolute bottom-full left-0 mb-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                {deviceOptions.map((option) => (
                  <button
                    key={option.id}
                    onClick={() => {
                      setSelectedDevice(option.id);
                      setShowDeviceSelector(false);
                    }}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2 text-sm text-left hover:bg-gray-50",
                      "first:rounded-t-lg last:rounded-b-lg",
                      selectedDevice === option.id && "bg-primary-50 text-primary-700"
                    )}
                  >
                    <option.icon className="w-4 h-4 flex-shrink-0" />
                    <div>
                      <div className="font-medium">{option.label}</div>
                      <div className="text-xs text-gray-500">{option.description}</div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
        
        <div className="text-xs text-gray-500">
          💡 视觉对比时将使用所选设备进行测试（任务可能需要1-5分钟）<br/>
          <span className="block mt-1">
            <b>如需测试登录态请设置 cookie：</b><br/>
            <code>"SESSION": "OGZmYmU1MGEtZDc3ZC00ZGJkLWI5N2YtODE5MTgzMjAzMmRi", "deviceId": "4b609475-5a78-479b-8315-7e9df9cec2cd", ...&#125;</code>
          </span>
          <span className="block mt-1">
            <b>如需设置页面状态请设置 localStorage：</b><br/>
            <code>localStorage: &#123;<br/>
            &nbsp;&nbsp;PHONE:86:15605889409|GlobalNotify-266: "true", // 关闭首次登录出现的弹窗<br/>
            &nbsp;&nbsp;language: "es-ES" // 西班牙语<br/>
            &#125;</code>
          </span>
        </div>
      </div>

      {/* Input Section */}
      <div className="flex items-center gap-2">
        {/* File Upload Button */}
        <button
          onClick={handleFileUpload}
          disabled={disabled || isLoading}
          className={cn(
            "flex-shrink-0 p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors",
            "focus:outline-none focus:ring-2 focus:ring-primary-500",
            (disabled || isLoading) && "opacity-50 cursor-not-allowed"
          )}
          title="上传文件"
        >
          <Paperclip className="w-5 h-5" />
        </button>

        {/* Message Input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            className={cn(
              "chat-input resize-none pr-12",
              (disabled || isLoading) && "opacity-50 cursor-not-allowed"
            )}
            rows={1}
          />
          
          {/* Voice Input Button */}
          <button
            onClick={handleVoiceInput}
            disabled={disabled || isLoading}
            className={cn(
              "absolute right-2 top-1/2 transform -translate-y-1/2",
              "p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors",
              "focus:outline-none focus:ring-2 focus:ring-primary-500",
              (disabled || isLoading) && "opacity-50 cursor-not-allowed",
              isRecording && "text-red-500 hover:text-red-600"
            )}
            title={isRecording ? "停止录音" : "语音输入"}
          >
            {isRecording ? (
              <MicOff className="w-4 h-4" />
            ) : (
              <Mic className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={!message.trim() || isLoading || disabled}
          className={cn(
            "flex-shrink-0 p-2 rounded-lg transition-colors",
            "focus:outline-none focus:ring-2 focus:ring-primary-500",
            message.trim() && !isLoading && !disabled
              ? "bg-primary-500 text-white hover:bg-primary-600"
              : "bg-gray-100 text-gray-400 cursor-not-allowed"
          )}
          title="发送消息"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
    </div>
  );
};

export default ChatInput; 