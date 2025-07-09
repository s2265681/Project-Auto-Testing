#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装"
        exit 1
    fi
}

# 检查必要的工具
check_command ssh

# 设置服务器信息
if [ -z "$SERVER_HOST" ]; then
    print_error "SERVER_HOST 环境变量未设置!"
    exit 1
fi

if [ -z "$SERVER_USER" ]; then
    SERVER_USER="ubuntu"
fi

# 设置GitHub仓库地址
GITHUB_REPO="${GITHUB_REPOSITORY:-https://github.com/s2265681/Project-Aut-Testing.git}"
APP_DIR="/var/www/app/product-auto-test"

print_message "开始部署到服务器: $SERVER_HOST"

# 测试SSH连接
print_message "测试SSH连接..."
if ! ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "echo 'SSH连接测试成功'"; then
    print_error "SSH连接失败，请检查服务器配置和密钥"
    exit 1
fi

# 创建部署目录并克隆/更新代码
print_message "创建部署目录并更新代码..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << 'EOF'
    sudo mkdir -p /var/www/app
    sudo chown -R ubuntu:ubuntu /var/www/app
    cd /var/www/app/product-auto-test
    
    if [ -d '.git' ]; then
        echo "更新现有代码..."
        git pull origin main
    else
        echo "克隆新代码..."
        cd /var/www/app
        git clone https://github.com/s2265681/Project-Aut-Testing.git product-auto-test
    fi
EOF

# 等待命令完成
sleep 5

# 安装Python依赖
print_message "安装Python依赖..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << 'EOF'
    cd /var/www/app/product-auto-test
    python3 -m pip install -r requirements.txt --user
EOF

# 等待命令完成
sleep 10

# 创建生产环境的.env文件
print_message "创建生产环境配置文件..."
if [ -n "$FEISHU_APP_ID" ] && [ -n "$FEISHU_APP_SECRET" ] && [ -n "$GEMINI_API_KEY" ] && [ -n "$FIGMA_ACCESS_TOKEN" ]; then
    ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << EOF
        cd /var/www/app/product-auto-test
        cat > .env << 'ENVEOF'
ENVIRONMENT=production
FEISHU_APP_ID=$FEISHU_APP_ID
FEISHU_APP_SECRET=$FEISHU_APP_SECRET
FEISHU_VERIFICATION_TOKEN=$FEISHU_VERIFICATION_TOKEN
GEMINI_API_KEY=$GEMINI_API_KEY
FIGMA_ACCESS_TOKEN=$FIGMA_ACCESS_TOKEN
ENVEOF
EOF
    
    print_message "✅ 生产环境配置文件创建成功"
else
    print_error "⚠️ 环境变量缺失，将使用现有的.env文件或环境变量"
fi

# 重启应用服务
print_message "重启产品自动测试服务..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << 'EOF'
    cd /var/www/app/product-auto-test
    export ENVIRONMENT=production
    
    # 停止现有服务
    pm2 stop product-auto-test 2>/dev/null || true
    
    # 启动新服务
    pm2 start api_server.py --name product-auto-test --interpreter python3
    
    # 保存PM2配置
    pm2 save
EOF

# 等待服务启动
sleep 3

# 验证部署状态
print_message "验证部署状态..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << 'EOF'
    echo "=== PM2状态 ==="
    pm2 status
    
    echo ""
    echo "=== 端口监听 ==="
    ss -tlnp | grep :5001 || echo "端口5001未监听"
    
    echo ""
    echo "=== 健康检查 ==="
    sleep 2
    curl -s http://localhost:5001/health || echo "健康检查失败，服务可能还在启动中"
EOF

print_message "🎉 部署完成！"
print_message "应用地址: http://$SERVER_HOST:5001"
print_message "健康检查: http://$SERVER_HOST:5001/health"
print_message "如果服务未响应，请等待30秒后再次尝试" 