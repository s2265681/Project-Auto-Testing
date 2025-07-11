import axios, { AxiosInstance, AxiosError } from 'axios';
import { 
  ChatResponse, 
  ChatHistory, 
  ChatStatus, 
  ChatExample, 
  ConversationContext, 
  ApiError 
} from '../types';

class ChatApi {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: '/api',
      timeout: 300000, // 5分钟超时，适应长时间的视觉对比任务
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        // Add timestamp to prevent caching
        config.params = {
          ...config.params,
          _t: Date.now(),
        };
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const apiError: ApiError = {
          message: error.message || '网络请求失败',
          status: error.response?.status || 0,
          code: error.code,
          details: error.response?.data,
        };

        if (error.response?.status === 429) {
          apiError.message = '请求过于频繁，请稍后再试';
        } else if (error.response?.status === 500) {
          apiError.message = '服务器内部错误，请稍后再试';
        } else if (error.response?.status === 503) {
          apiError.message = '服务暂时不可用，请稍后再试';
        } else if (error.code === 'ECONNABORTED') {
          // 超时错误特殊处理
          apiError.message = '请求超时，可能是因为任务正在后台处理中。如果是视觉对比等长时间任务，请耐心等待或稍后重试';
        } else if (!error.response) {
          apiError.message = '网络连接失败，请检查网络设置';
        }

        return Promise.reject(apiError);
      }
    );
  }

  async sendMessage(message: string, sessionId?: string, device?: string): Promise<ChatResponse> {
    const response = await this.api.post('/chat', {
      message,
      session_id: sessionId,
      device: device || 'desktop', // 添加设备参数
    });
    
    // 适配后端响应格式
    const backendData = response.data.data;
    return {
      message: backendData.content,
      intent: backendData.intent?.type || 'unknown',
      confidence: backendData.intent?.confidence || 0,
      parameters: backendData.intent?.parameters || {},
      session_id: backendData.session_id,
      timestamp: backendData.timestamp,
      status: backendData.success ? 'success' : 'error',
      suggestions: backendData.suggestions
    };
  }

  async getHistory(sessionId?: string): Promise<ChatHistory> {
    const response = await this.api.get('/chat/history', {
      params: { session_id: sessionId },
    });
    
    // 适配后端响应格式
    const backendData = response.data.data || response.data;
    return {
      messages: backendData.messages || [],
      session_id: sessionId || '',
      created_at: backendData.created_at || new Date().toISOString(),
      last_updated: backendData.last_updated || new Date().toISOString()
    };
  }

  async getSummary(sessionId?: string): Promise<string> {
    const response = await this.api.get<{ summary: string }>('/chat/summary', {
      params: { session_id: sessionId },
    });
    return response.data.summary;
  }

  async getExamples(): Promise<ChatExample[]> {
    const response = await this.api.get<ChatExample[]>('/chat/examples');
    return response.data;
  }

  async clearHistory(sessionId?: string): Promise<void> {
    await this.api.post('/chat/clear', {
      session_id: sessionId,
    });
  }

  async getStatus(): Promise<ChatStatus> {
    const response = await this.api.get('/chat/status');
    
    // 适配后端响应格式
    const backendData = response.data.data;
    const stats = backendData.statistics;
    const systemStatus = backendData.system_status;
    
    return {
      status: systemStatus.data?.status === 'healthy' ? 'healthy' : 'degraded',
      active_sessions: stats.active_sessions,
      total_messages: stats.total_messages,
      last_activity: stats.timestamp,
      version: '1.0.0', // 默认版本
      uptime: 0 // 默认运行时间
    };
  }

  async getContext(sessionId?: string): Promise<ConversationContext> {
    const response = await this.api.get<ConversationContext>('/chat/context', {
      params: { session_id: sessionId },
    });
    return response.data;
  }

  async exportHistory(sessionId?: string): Promise<string> {
    const response = await this.api.get<{ data: string }>('/chat/export', {
      params: { session_id: sessionId },
    });
    return response.data.data;
  }

  async importHistory(data: string): Promise<void> {
    await this.api.post('/chat/import', { data });
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.api.get('/health');
      return response.status === 200 && response.data?.status === 'healthy';
    } catch {
      return false;
    }
  }
}

export const chatApi = new ChatApi();
export default chatApi; 