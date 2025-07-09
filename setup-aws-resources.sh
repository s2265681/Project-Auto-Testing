#!/bin/bash

# AWS资源快速设置脚本
# Quick Setup Script for AWS Resources

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

# 检查AWS CLI是否已安装
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI未安装，请先安装AWS CLI"
        exit 1
    fi
    
    # 检查AWS凭证
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS凭证未配置，请运行 'aws configure'"
        exit 1
    fi
    
    print_message "AWS CLI已安装并配置"
}

# 创建S3存储桶
create_s3_bucket() {
    local bucket_name="temp-deployment-bucket-$(date +%s)"
    local region="ap-southeast-1"
    
    print_message "创建S3存储桶: $bucket_name"
    
    aws s3 mb s3://$bucket_name --region $region
    
    if [ $? -eq 0 ]; then
        print_message "✅ S3存储桶创建成功: $bucket_name"
        echo "S3_BUCKET_NAME=$bucket_name" >> aws-resources.env
    else
        print_error "❌ S3存储桶创建失败"
        exit 1
    fi
}

# 创建IAM角色
create_iam_role() {
    local role_name="ProductAutoTestEC2Role"
    
    print_message "创建IAM角色: $role_name"
    
    # 创建信任策略
    cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
    
    # 创建角色
    aws iam create-role \
        --role-name $role_name \
        --assume-role-policy-document file://trust-policy.json
    
    # 附加必要的策略
    aws iam attach-role-policy \
        --role-name $role_name \
        --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
    
    aws iam attach-role-policy \
        --role-name $role_name \
        --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
    
    aws iam attach-role-policy \
        --role-name $role_name \
        --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy
    
    # 创建实例配置文件
    aws iam create-instance-profile --instance-profile-name $role_name
    aws iam add-role-to-instance-profile \
        --instance-profile-name $role_name \
        --role-name $role_name
    
    if [ $? -eq 0 ]; then
        print_message "✅ IAM角色创建成功: $role_name"
        echo "IAM_ROLE_NAME=$role_name" >> aws-resources.env
    else
        print_warning "⚠️ IAM角色可能已存在或创建失败"
    fi
    
    # 清理临时文件
    rm -f trust-policy.json
}

# 获取EC2实例信息
get_ec2_info() {
    print_message "获取EC2实例信息..."
    
    # 列出所有运行中的实例
    instances=$(aws ec2 describe-instances \
        --filters "Name=instance-state-name,Values=running" \
        --query "Reservations[].Instances[].[InstanceId,PublicIpAddress,Tags[?Key=='Name']|[0].Value]" \
        --output table)
    
    if [ -n "$instances" ]; then
        print_message "运行中的EC2实例："
        echo "$instances"
        echo
        print_warning "请手动选择要使用的实例ID，并在GitHub Secrets中设置 EC2_INSTANCE_ID"
    else
        print_warning "没有找到运行中的EC2实例"
    fi
}

# 验证设置
verify_setup() {
    print_message "验证AWS资源设置..."
    
    # 验证S3存储桶
    if [ -f aws-resources.env ]; then
        source aws-resources.env
        if [ -n "$S3_BUCKET_NAME" ]; then
            aws s3 ls s3://$S3_BUCKET_NAME > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                print_message "✅ S3存储桶验证成功"
            else
                print_error "❌ S3存储桶验证失败"
            fi
        fi
    fi
}

# 主函数
main() {
    print_message "开始AWS资源设置..."
    
    # 清理旧的配置文件
    rm -f aws-resources.env
    
    # 检查AWS CLI
    check_aws_cli
    
    # 创建S3存储桶
    create_s3_bucket
    
    # 创建IAM角色
    create_iam_role
    
    # 获取EC2实例信息
    get_ec2_info
    
    # 验证设置
    verify_setup
    
    print_message "AWS资源设置完成！"
    print_message "资源信息已保存到 aws-resources.env"
    print_message "请在GitHub Secrets中设置以下变量："
    print_message "- AWS_ACCESS_KEY_ID"
    print_message "- AWS_SECRET_ACCESS_KEY"
    print_message "- EC2_INSTANCE_ID"
    print_message "- 其他API密钥..."
}

# 运行主函数
main 