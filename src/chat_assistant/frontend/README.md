# Chat Assistant Frontend

智能测试助手前端项目 - 使用 React + TypeScript + TailwindCSS + Sass 构建的现代化聊天界面。

## 🚀 特性

- **现代化技术栈**: React 18 + TypeScript + Vite
- **精美UI设计**: TailwindCSS + Sass + Framer Motion
- **响应式布局**: 移动端和桌面端完美适配
- **实时通信**: 与后端API无缝集成
- **智能交互**: 支持语音输入、文件上传等功能
- **丰富动画**: 流畅的交互动画和过渡效果
- **完整功能**: 消息历史、导出功能、设置面板等

## 📦 项目结构

```
frontend/
├── src/
│   ├── components/          # React组件
│   │   ├── ChatApp.tsx      # 主应用组件
│   │   ├── ChatHeader.tsx   # 聊天头部
│   │   ├── ChatMessage.tsx  # 消息组件
│   │   └── ChatInput.tsx    # 输入组件
│   ├── hooks/               # 自定义Hook
│   │   └── useChat.ts       # 聊天功能Hook
│   ├── services/            # API服务
│   │   └── api.ts           # API接口
│   ├── types/               # TypeScript类型
│   │   └── index.ts         # 类型定义
│   ├── utils/               # 工具函数
│   │   └── index.ts         # 通用工具
│   ├── styles/              # 样式文件
│   │   └── globals.scss     # 全局样式
│   └── main.tsx             # 应用入口
├── public/                  # 静态资源
├── package.json             # 依赖配置
├── tsconfig.json            # TypeScript配置
├── tailwind.config.js       # TailwindCSS配置
├── vite.config.ts           # Vite配置
└── README.md                # 项目说明
```

## 🛠️ 安装和使用

### 1. 安装依赖

```bash
# 使用 npm
npm install

# 使用 yarn
yarn install

# 使用 pnpm
pnpm install
```

### 2. 启动开发服务器

```bash
# 使用 npm
npm run dev

# 使用 yarn
yarn dev

# 使用 pnpm
pnpm dev
```

应用将在 `http://localhost:3000` 启动。

### 3. 构建生产版本

```bash
# 使用 npm
npm run build

# 使用 yarn
yarn build

# 使用 pnpm
pnpm build
```

### 4. 预览生产版本

```bash
# 使用 npm
npm run preview

# 使用 yarn
yarn preview

# 使用 pnpm
pnpm preview
```

## 🎯 功能特性

### 智能对话
- 支持自然语言交互
- 实时响应和打字效果
- 智能意图识别和参数提取

### 用户体验
- 现代化的聊天界面
- 流畅的动画效果
- 响应式设计
- 深色/浅色主题切换

### 高级功能
- 消息历史记录
- 导出聊天记录
- 语音输入支持
- 文件上传功能
- 系统状态监控

### 测试功能
- 测试用例生成
- 视觉对比测试
- 完整工作流执行
- 测试报告查看

## 🔧 配置

### 环境变量

创建 `.env.local` 文件：

```env
# API基础URL
VITE_API_BASE_URL=http://localhost:5001

# 开发模式
VITE_DEV_MODE=true

# 启用调试
VITE_DEBUG=true
```

### 自定义主题

在 `tailwind.config.js` 中修改颜色配置：

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // 自定义主色调
      },
      secondary: {
        // 自定义辅助色
      }
    }
  }
}
```

## 🚀 部署

### 使用 Docker

```bash
# 构建镜像
docker build -t chat-assistant-frontend .

# 运行容器
docker run -p 3000:3000 chat-assistant-frontend
```

### 使用 Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /var/www/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📝 开发指南

### 代码规范

- 使用 ESLint 和 Prettier 进行代码格式化
- 遵循 React 和 TypeScript 最佳实践
- 组件命名使用 PascalCase
- 文件命名使用 camelCase

### 组件开发

```typescript
// 组件模板
import React from 'react';
import { cn } from '@/utils';

interface ComponentProps {
  className?: string;
  children?: React.ReactNode;
}

const Component: React.FC<ComponentProps> = ({ 
  className, 
  children 
}) => {
  return (
    <div className={cn("base-styles", className)}>
      {children}
    </div>
  );
};

export default Component;
```

### API 集成

```typescript
// API调用示例
import { chatApi } from '@/services/api';

const response = await chatApi.sendMessage(message);
```

## 🐛 问题排查

### 常见问题

1. **端口冲突**: 修改 `vite.config.ts` 中的端口配置
2. **依赖问题**: 删除 `node_modules` 重新安装
3. **类型错误**: 确保所有依赖的类型定义已安装
4. **样式问题**: 检查 TailwindCSS 配置和样式文件

### 调试技巧

- 使用浏览器开发者工具
- 查看控制台错误信息
- 检查网络请求状态
- 使用 React DevTools

## 📈 性能优化

- 使用 React.memo 优化组件渲染
- 实现虚拟滚动处理大量消息
- 使用 lazy loading 延迟加载组件
- 启用 Gzip 压缩和缓存

## 🔐 安全性

- 输入验证和消毒
- XSS 防护
- CSRF 保护
- 安全的 API 通信

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

## 📄 许可证

MIT License

## 🆘 支持

如有问题或建议，请提交 Issue 或联系维护者。 