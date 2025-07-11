#!/bin/bash

# Chat Assistant Frontend Setup Script
# 聊天助手前端项目安装脚本

set -e

echo "🚀 正在安装聊天助手前端项目..."

# 检查Node.js版本
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    echo "✅ 检测到 Node.js 版本: $NODE_VERSION"
else
    echo "❌ 未检测到 Node.js，请先安装 Node.js 16+ 版本"
    exit 1
fi

# 检查包管理器
if command -v pnpm &> /dev/null; then
    PKG_MANAGER="pnpm"
elif command -v yarn &> /dev/null; then
    PKG_MANAGER="yarn"
elif command -v npm &> /dev/null; then
    PKG_MANAGER="npm"
else
    echo "❌ 未找到包管理器，请安装 npm、yarn 或 pnpm"
    exit 1
fi

echo "📦 使用包管理器: $PKG_MANAGER"

# 安装依赖
echo "📥 正在安装依赖..."
case $PKG_MANAGER in
    pnpm)
        pnpm install
        ;;
    yarn)
        yarn install
        ;;
    npm)
        npm install
        ;;
esac

echo "✅ 依赖安装完成！"

# 创建环境变量文件
if [ ! -f ".env.local" ]; then
    echo "📝 创建环境变量文件..."
    cat > .env.local << EOF
# API基础URL
VITE_API_BASE_URL=http://localhost:5001

# 开发模式
VITE_DEV_MODE=true

# 启用调试
VITE_DEBUG=true

# 应用标题
VITE_APP_TITLE=智能测试助手

# 版本信息
VITE_APP_VERSION=1.0.0
EOF
    echo "✅ 环境变量文件创建完成"
else
    echo "ℹ️  环境变量文件已存在，跳过创建"
fi

# 运行类型检查
echo "🔍 运行类型检查..."
case $PKG_MANAGER in
    pnpm)
        pnpm run type-check
        ;;
    yarn)
        yarn type-check
        ;;
    npm)
        npm run type-check
        ;;
esac

echo "✅ 类型检查通过！"

# 运行代码检查
echo "🔍 运行代码检查..."
case $PKG_MANAGER in
    pnpm)
        pnpm run lint
        ;;
    yarn)
        yarn lint
        ;;
    npm)
        npm run lint
        ;;
esac

echo "✅ 代码检查通过！"

echo ""
echo "🎉 聊天助手前端项目安装完成！"
echo ""
echo "📋 接下来的步骤:"
echo "1. 启动开发服务器: $PKG_MANAGER run dev"
echo "2. 构建生产版本: $PKG_MANAGER run build"
echo "3. 预览生产版本: $PKG_MANAGER run preview"
echo ""
echo "🌐 开发服务器地址: http://localhost:3000"
echo "🔧 确保后端API服务器运行在: http://localhost:5001"
echo ""
echo "💡 提示: 编辑 .env.local 文件可以修改配置"
echo "📖 查看 README.md 了解更多使用方法" 