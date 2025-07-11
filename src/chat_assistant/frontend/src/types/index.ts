export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  device?: string; // 添加设备类型字段
  isTyping?: boolean;
  metadata?: {
    intent?: string;
    confidence?: number;
    parameters?: Record<string, any>;
  };
}

export interface ChatResponse {
  message: string;
  intent: string;
  confidence: number;
  parameters: Record<string, any>;
  session_id: string;
  timestamp: string;
  status: 'success' | 'error' | 'processing';
  suggestions?: string[];
}

export interface ChatHistory {
  messages: ChatMessage[];
  session_id: string;
  created_at: string;
  last_updated: string;
}

export interface ChatStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version?: string;
  uptime?: number;
  active_sessions: number;
  total_messages: number;
  last_activity: string;
}

export interface ChatExample {
  title: string;
  description: string;
  input: string;
  expected_intent: string;
  icon: string;
}

export interface ConversationContext {
  session_id: string;
  parameters: Record<string, any>;
  last_intent?: string;
  last_activity: string;
  message_count: number;
}

export interface ExecutionResult {
  success: boolean;
  message: string;
  data?: any;
  error?: string;
  timestamp: string;
}

export interface ApiError {
  message: string;
  status: number;
  code?: string;
  details?: any;
}

export interface ChatSettings {
  theme: 'light' | 'dark' | 'system';
  language: 'zh' | 'en';
  autoScroll: boolean;
  soundEnabled: boolean;
  showTimestamps: boolean;
  showMetadata: boolean;
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
} 