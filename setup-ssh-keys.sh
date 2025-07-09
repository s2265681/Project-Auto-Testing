#!/bin/bash

# SSH密钥配置脚本
# SSH Keys Setup Script

set -e

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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 服务器信息
SERVER_HOST="18.141.179.222"
SERVER_USER="ubuntu"
KEY_NAME="product-auto-test-key"

print_message "开始配置SSH密钥..."

# 1. 检查是否已有SSH密钥
print_message "1. 检查现有SSH密钥..."
if [ -f ~/.ssh/id_rsa ]; then
    print_warning "发现现有SSH密钥: ~/.ssh/id_rsa"
    echo -n "是否使用现有密钥? (y/n): "
    read -r use_existing
    if [ "$use_existing" = "y" ] || [ "$use_existing" = "Y" ]; then
        PRIVATE_KEY_FILE=~/.ssh/id_rsa
        PUBLIC_KEY_FILE=~/.ssh/id_rsa.pub
    else
        PRIVATE_KEY_FILE=~/.ssh/${KEY_NAME}
        PUBLIC_KEY_FILE=~/.ssh/${KEY_NAME}.pub
    fi
else
    PRIVATE_KEY_FILE=~/.ssh/${KEY_NAME}
    PUBLIC_KEY_FILE=~/.ssh/${KEY_NAME}.pub
fi

# 2. 生成SSH密钥（如果不存在）
if [ ! -f "$PRIVATE_KEY_FILE" ]; then
    print_message "2. 生成SSH密钥..."
    ssh-keygen -t rsa -b 4096 -f "$PRIVATE_KEY_FILE" -N "" -C "github-actions-deployment"
    print_success "SSH密钥已生成: $PRIVATE_KEY_FILE"
else
    print_message "2. 使用现有SSH密钥: $PRIVATE_KEY_FILE"
fi

# 3. 显示公钥
print_message "3. 公钥内容:"
echo "================================"
cat "$PUBLIC_KEY_FILE"
echo "================================"

# 4. 测试SSH连接
print_message "4. 测试SSH连接..."
if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -i "$PRIVATE_KEY_FILE" $SERVER_USER@$SERVER_HOST "echo 'SSH连接成功'" 2>/dev/null; then
    print_success "✅ SSH连接测试成功"
else
    print_error "❌ SSH连接失败"
    print_message "请按照以下步骤配置："
    echo ""
    echo "1. 复制上面的公钥内容"
    echo "2. 登录到服务器: ssh $SERVER_USER@$SERVER_HOST"
    echo "3. 运行以下命令添加公钥:"
    echo "   mkdir -p ~/.ssh"
    echo "   echo '公钥内容' >> ~/.ssh/authorized_keys"
    echo "   chmod 600 ~/.ssh/authorized_keys"
    echo "   chmod 700 ~/.ssh"
    echo ""
    echo "4. 重新运行此脚本验证连接"
    echo ""
    echo "或者通过AWS控制台连接到实例并运行:"
    echo "   aws ssm start-session --target i-02a4517ea69668f5f --region ap-southeast-1"
fi

# 5. 显示私钥内容（用于GitHub Secrets）
print_message "5. 私钥内容（用于GitHub Secrets）:"
echo "================================"
echo "复制以下内容到 GitHub Secrets 中的 SSH_PRIVATE_KEY："
echo ""
cat "$PRIVATE_KEY_FILE"
echo ""
echo "================================"

# 6. 显示GitHub Secrets配置
print_message "6. GitHub Secrets配置:"
echo ""
echo "在 GitHub 仓库的 Settings > Secrets and variables > Actions 中添加："
echo ""
echo "SERVER_HOST=$SERVER_HOST"
echo "SERVER_USER=$SERVER_USER"
echo "SSH_PRIVATE_KEY=<复制上面的私钥内容>"
echo ""
echo "以及其他API密钥..."

# 7. 提供一键配置命令
print_message "7. 一键配置命令（在服务器上运行）:"
echo ""
echo "如果SSH连接失败，请在服务器上运行以下命令:"
echo ""
echo "mkdir -p ~/.ssh"
echo "echo '$(cat "$PUBLIC_KEY_FILE")' >> ~/.ssh/authorized_keys"
echo "chmod 600 ~/.ssh/authorized_keys"
echo "chmod 700 ~/.ssh"
echo ""

print_message "✅ SSH密钥配置完成！"
print_warning "请确保将私钥添加到GitHub Secrets中，然后测试部署" 