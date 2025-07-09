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
check_command aws

# 设置EC2实例ID
if [ -z "$EC2_INSTANCE_ID" ]; then
    print_error "EC2_INSTANCE_ID 环境变量未设置!"
    exit 1
fi

# 设置S3存储桶名称
if [ -z "$S3_BUCKET_NAME" ]; then
    S3_BUCKET_NAME="temp-deployment-bucket"
    print_message "使用默认S3存储桶: $S3_BUCKET_NAME"
else
    print_message "使用S3存储桶: $S3_BUCKET_NAME"
fi

print_message "使用EC2实例: $EC2_INSTANCE_ID"

# 检查AWS连接
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS认证失败，请检查AWS凭证!"
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
aws ssm send-command \
    --instance-ids "$EC2_INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["mkdir -p /var/www/app/product-auto-test"]' \
    --output text --query 'Command.CommandId' > /tmp/command_id

# 等待命令完成
sleep 2

# 创建部署包
print_message "创建部署包..."
tar -czf /tmp/deploy.tar.gz --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' --exclude='logs' --exclude='reports' --exclude='screenshots' .

# 上传文件到S3临时存储
print_message "上传部署包到S3..."
aws s3 cp /tmp/deploy.tar.gz s3://$S3_BUCKET_NAME/product-auto-test/deploy.tar.gz

# 在EC2实例上下载并解压
print_message "在EC2实例上下载并部署..."
aws ssm send-command \
    --instance-ids "$EC2_INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[
        \"cd /var/www/app/product-auto-test\",
        \"aws s3 cp s3://$S3_BUCKET_NAME/product-auto-test/deploy.tar.gz .\",
        \"tar -xzf deploy.tar.gz\",
        \"rm deploy.tar.gz\"
    ]" \
    --output text --query 'Command.CommandId' > /tmp/command_id

# 等待命令完成
sleep 5

print_message "安装Python依赖和配置环境..."
aws ssm send-command \
    --instance-ids "$EC2_INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=[
        "cd /var/www/app/product-auto-test",
        "pip3 install -r requirements.txt"
    ]' \
    --output text --query 'Command.CommandId' > /tmp/command_id

# 等待命令完成
sleep 10

# 创建生产环境的.env文件
print_message "创建生产环境配置文件..."
if [ -n "$FEISHU_APP_ID" ] && [ -n "$FEISHU_APP_SECRET" ] && [ -n "$GEMINI_API_KEY" ] && [ -n "$FIGMA_ACCESS_TOKEN" ]; then
    aws ssm send-command \
        --instance-ids "$EC2_INSTANCE_ID" \
        --document-name "AWS-RunShellScript" \
        --parameters "commands=[
            \"cd /var/www/app/product-auto-test\",
            \"cat > .env << EOF
FEISHU_APP_ID=$FEISHU_APP_ID
FEISHU_APP_SECRET=$FEISHU_APP_SECRET
FEISHU_VERIFICATION_TOKEN=$FEISHU_VERIFICATION_TOKEN
GEMINI_API_KEY=$GEMINI_API_KEY
FIGMA_ACCESS_TOKEN=$FIGMA_ACCESS_TOKEN
EOF\"
        ]" \
        --output text --query 'Command.CommandId' > /tmp/command_id
    
    sleep 2
    print_message "✅ 生产环境配置文件创建成功"
else
    print_error "⚠️ 环境变量缺失，将使用现有的.env文件或环境变量"
fi

# 重启后端服务
print_message "重启产品自动测试服务..."
aws ssm send-command \
    --instance-ids "$EC2_INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=[
        "cd /var/www/app/product-auto-test",
        "export ENVIRONMENT=production",
        "pm2 restart product-auto-test || pm2 start api_server.py --name product-auto-test --interpreter python3"
    ]' \
    --output text --query 'Command.CommandId' > /tmp/command_id

# 等待命令完成
sleep 5

# 清理临时文件
print_message "清理临时文件..."
rm -f /tmp/deploy.tar.gz
aws s3 rm s3://$S3_BUCKET_NAME/product-auto-test/deploy.tar.gz

print_message "部署完成！" 