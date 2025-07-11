// 前端应用配置管理

interface AppConfig {
  apiBaseUrl: string;
  environment: 'development' | 'production' | 'staging';
  apiTimeout: number;
  debug: boolean;
  version: string;
}

/**
 * 获取API基础URL
 */
function getApiBaseUrl(): string {
  // 优先使用环境变量配置
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // 根据当前环境自动判断
  const isProduction = import.meta.env.PROD;
  const isDevelopment = import.meta.env.DEV;
  
  if (isDevelopment) {
    // 开发环境：使用localhost
    return 'http://localhost:5001';
  }
  
  if (isProduction) {
    // 生产环境：智能判断域名
    const currentHost = window.location.host;
    
    // 如果当前域名包含生产服务器IP，使用当前域名
    if (currentHost.includes('18.141.179.222')) {
      return `${window.location.protocol}//${currentHost}`;
    }
    
    // 否则使用默认生产域名
    return 'http://18.141.179.222:8000';
  }
  
  // 默认回退到相对路径
  return '';
}

/**
 * 获取环境类型
 */
function getEnvironment(): 'development' | 'production' | 'staging' {
  if (import.meta.env.VITE_APP_ENV) {
    return import.meta.env.VITE_APP_ENV as 'development' | 'production' | 'staging';
  }
  
  if (import.meta.env.PROD) {
    return 'production';
  }
  
  return 'development';
}

/**
 * 应用配置
 */
export const config: AppConfig = {
  apiBaseUrl: getApiBaseUrl(),
  environment: getEnvironment(),
  apiTimeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '300000'),
  debug: import.meta.env.VITE_DEBUG === 'true' || import.meta.env.DEV,
  version: import.meta.env.VITE_APP_VERSION || '1.0.0',
};

/**
 * 是否为开发环境
 */
export const isDevelopment = config.environment === 'development';

/**
 * 是否为生产环境
 */
export const isProduction = config.environment === 'production';

/**
 * 获取完整的API URL
 */
export function getApiUrl(path: string = ''): string {
  const baseUrl = config.apiBaseUrl;
  const apiPath = '/api';
  
  if (baseUrl) {
    return `${baseUrl}${apiPath}${path}`;
  }
  
  return `${apiPath}${path}`;
}

/**
 * 打印配置信息（仅在开发环境）
 */
export function logConfig(): void {
  if (isDevelopment) {
    console.group('🔧 应用配置信息');
    console.log('- 环境:', config.environment);
    console.log('- API Base URL:', config.apiBaseUrl);
    console.log('- API超时时间:', config.apiTimeout);
    console.log('- 调试模式:', config.debug);
    console.log('- 版本:', config.version);
    console.groupEnd();
  }
}

export default config; 