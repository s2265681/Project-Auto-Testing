import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  return {
    plugins: [react()],
    
    // 定义全局常量
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
      __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
    },
    
    server: {
      port: 3000,
      host: true, // 允许外部访问
      proxy: {
        '/api': {
          target: process.env.VITE_API_BASE_URL || 'http://localhost:5001',
          changeOrigin: true,
          secure: false,
          configure: (proxy, options) => {
            proxy.on('error', (err, req, res) => {
              console.log('proxy error', err);
            });
            proxy.on('proxyReq', (proxyReq, req, res) => {
              console.log('Sending Request to the Target:', req.method, req.url);
            });
            proxy.on('proxyRes', (proxyRes, req, res) => {
              console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
            });
          },
        },
      },
    },
    
    build: {
      outDir: 'dist',
      sourcemap: mode !== 'production', // 只在非生产环境生成sourcemap
      minify: mode === 'production' ? 'esbuild' : false,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
            ui: ['lucide-react', 'framer-motion'],
            utils: ['axios', 'react-markdown'],
          },
        },
      },
      // 压缩配置
      terserOptions: {
        compress: {
          drop_console: mode === 'production', // 生产环境移除console
          drop_debugger: true,
        },
      },
    },
    
    // 预览服务配置（用于生产构建预览）
    preview: {
      port: 3001,
      host: true,
    },
    
    // 环境变量配置
    envPrefix: 'VITE_',
  }
}) 