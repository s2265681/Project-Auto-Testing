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
check_command python3
check_command pip3
check_command rsync

# 设置 SSH key 路径（优先 CI 环境的 deploy_key，否则用本地 pem）
SSH_KEY_PATH="$HOME/.ssh/deploy_key"
LOCAL_KEY_PATH="/Users/mac/Github/aws-project-key2.pem"
if [ -f "$SSH_KEY_PATH" ]; then
    SSH_KEY_OPTION="-i $SSH_KEY_PATH"
elif [ -f "$LOCAL_KEY_PATH" ]; then
    SSH_KEY_OPTION="-i $LOCAL_KEY_PATH"
else
    print_error "SSH key not found at $SSH_KEY_PATH or $LOCAL_KEY_PATH!"
    exit 1
fi

# 检查Python依赖
print_message "检查Python依赖..."
if [ -f "requirements.txt" ]; then
    print_message "requirements.txt 文件存在"
else
    print_error "requirements.txt 文件不存在"
    exit 1
fi

# 创建远程目录
print_message "创建远程目录..."
ssh $SSH_KEY_OPTION ubuntu@18.141.179.222 "mkdir -p /var/www/app/product-auto-test"

# 部署到 EC2 产品自动测试目录（排除不需要的文件）
print_message "开始部署产品自动测试系统到 EC2..."
rsync -avz --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' --exclude='logs' --exclude='reports' --exclude='screenshots' -e "ssh $SSH_KEY_OPTION" . ubuntu@18.141.179.222:/var/www/app/product-auto-test/

print_message "安装Python依赖和配置环境..."
ssh $SSH_KEY_OPTION ubuntu@18.141.179.222 "cd /var/www/app/product-auto-test && pip3 install -r requirements.txt"

# 创建生产环境的.env文件
print_message "创建生产环境配置文件..."
if [ -n "$FEISHU_APP_ID" ] && [ -n "$FEISHU_APP_SECRET" ] && [ -n "$GEMINI_API_KEY" ] && [ -n "$FIGMA_ACCESS_TOKEN" ]; then
    ssh $SSH_KEY_OPTION ubuntu@18.141.179.222 "cd /var/www/app/product-auto-test && cat > .env << EOF
FEISHU_APP_ID=$FEISHU_APP_ID
FEISHU_APP_SECRET=$FEISHU_APP_SECRET
FEISHU_VERIFICATION_TOKEN=$FEISHU_VERIFICATION_TOKEN
GEMINI_API_KEY=$GEMINI_API_KEY
FIGMA_ACCESS_TOKEN=$FIGMA_ACCESS_TOKEN
EOF"
    print_message "✅ 生产环境配置文件创建成功"
else
    print_error "⚠️ 环境变量缺失，将使用现有的.env文件或环境变量"
fi

# 重启后端服务
print_message "重启产品自动测试服务..."
ssh $SSH_KEY_OPTION ubuntu@18.141.179.222 "cd /var/www/app/product-auto-test && export ENVIRONMENT=production && pm2 restart product-auto-test || pm2 start api_server.py --name product-auto-test --interpreter python3"

print_message "部署完成！" 