import React, { useState, useRef, useCallback, KeyboardEvent } from 'react';
import { Send, Loader2, Mic, MicOff, Paperclip, Monitor, Smartphone, Tablet } from 'lucide-react';
import { cn } from '../utils';
import { toast } from 'react-hot-toast';

interface ChatInputProps {
  onSendMessage: (message: string, device?: string, cookies?: string, localStorage?: string) => void;
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
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [cookies, setCookies] = useState('');
  const [localStorage, setLocalStorage] = useState('');
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

    // 传递所有参数到后端
    onSendMessage(trimmedMessage, selectedDevice, cookies, localStorage);
    setMessage('');
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [message, isLoading, disabled, selectedDevice, cookies, localStorage, onSendMessage]);

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
      {/* Device Selector and Advanced Options */}
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
          
          {/* Advanced Options Button */}
          <button
            onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
            disabled={disabled || isLoading}
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg transition-colors",
              "focus:outline-none focus:ring-2 focus:ring-blue-500",
              (disabled || isLoading) && "opacity-50 cursor-not-allowed",
              showAdvancedOptions && "bg-blue-100"
            )}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span>高级设置</span>
          </button>
        </div>
        
        <div className="text-xs text-gray-500">
          💡 视觉对比时将使用所选设备进行测试（任务可能需要1-5分钟）
        </div>
      </div>

      {/* Advanced Options Panel */}
      {showAdvancedOptions && (
        <div className="bg-gray-50 rounded-lg p-4 space-y-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              🍪 Cookie 设置
              <span className="text-xs text-gray-500 ml-1">(可选，用于登录态测试)</span>
            </label>
            <textarea
              value={cookies}
              onChange={(e) => setCookies(e.target.value)}
              placeholder="输入cookie字符串，例如：SESSION=xxx; deviceId=xxx; _ga=xxx..."
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
              disabled={disabled || isLoading}
            />
            <div className="text-xs text-gray-500">
              格式：name=value; name2=value2; name3=value3
            </div>
          </div>
          
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              💾 localStorage 设置
              <span className="text-xs text-gray-500 ml-1">(可选，用于页面状态设置)</span>
            </label>
            <textarea
              value={localStorage}
              onChange={(e) => setLocalStorage(e.target.value)}
              placeholder="输入localStorage JSON格式，例如：{&quot;language&quot;: &quot;es-ES&quot;, &quot;PHONE:86:15605889409|GlobalNotify-266&quot;: &quot;true&quot;}"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
              disabled={disabled || isLoading}
            />
            <div className="text-xs text-gray-500">
              格式：{"{"}"key": "value", "key2": "value2"{"}"}
            </div>
          </div>
          
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div>
              💡 这些设置将用于视觉对比测试中的页面状态控制
            </div>
            <button
              onClick={() => {
                setCookies('');
                setLocalStorage('');
              }}
              className="text-blue-600 hover:text-blue-800 underline"
              disabled={disabled || isLoading}
            >
              清空设置
            </button>
          </div>
        </div>
      )}

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