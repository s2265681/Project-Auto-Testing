#!/bin/bash

# 🚀 超简化部署脚本
# 用法: ./deploy.sh

# 配置
SERVER_IP="18.141.179.222"
APP_DIR="/var/www/app/product-auto-test"
SSH_KEY="~/.ssh/deploy_key"

echo "🚀 开始部署到生产服务器..."

# 尝试不同的用户名
USERS=("ubuntu" "ec2-user" "admin" "root")
CONNECTED=false

for USER in "${USERS[@]}"; do
  echo "🔍 尝试连接 ${USER}@${SERVER_IP}..."
  
  if ssh -i $SSH_KEY -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${USER}@${SERVER_IP} "echo 'SSH连接成功'" 2>/dev/null; then
    echo "✅ 成功连接到 ${USER}@${SERVER_IP}"
    SERVER="${USER}@${SERVER_IP}"
    CONNECTED=true
    break
  else
    echo "❌ 无法连接到 ${USER}@${SERVER_IP}"
  fi
done

if [ "$CONNECTED" = false ]; then
  echo "💥 无法连接到服务器，请检查："
  echo "1. AWS安全组是否允许SSH (端口22)"
  echo "2. EC2实例是否运行"
  echo "3. 公网IP是否正确: $SERVER_IP"
  echo "4. SSH密钥是否正确"
  exit 1
fi

echo "🎯 使用用户: $SERVER"

# 部署代码
ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $SERVER "
  echo '📁 准备应用目录...'
  sudo mkdir -p /var/www/app
  sudo chown \$USER:\$USER /var/www/app
  
  echo '📦 更新代码...'
  cd /var/www/app
  if [ -d 'product-auto-test' ]; then
    cd product-auto-test
    # 检查是否为有效的git仓库
    if [ -d '.git' ] && git rev-parse --git-dir > /dev/null 2>&1; then
      echo '🔄 更新现有仓库...'
      git fetch origin
      git reset --hard origin/main
    else
      echo '🚨 目录存在但不是有效的git仓库，重新克隆...'
      cd ..
      sudo rm -rf product-auto-test
      git clone https://github.com/s2265681/Project-Auto-Testing.git product-auto-test
      cd product-auto-test
    fi
  else
    git clone https://github.com/s2265681/Project-Auto-Testing.git product-auto-test
    cd product-auto-test
  fi
  
  echo '🐍 设置Python环境...'
  python3 -m venv venv 2>/dev/null || echo 'venv已存在'
  source venv/bin/activate
  pip install --upgrade pip
  
  echo '📚 安装依赖...'
  pip install -r requirements.txt
  
  echo '⚙️ 设置环境变量...'
  cat > .env << EOF
FEISHU_APP_ID=${FEISHU_APP_ID}
FEISHU_APP_SECRET=${FEISHU_APP_SECRET}
FEISHU_VERIFICATION_TOKEN=${FEISHU_VERIFICATION_TOKEN}
GEMINI_API_KEY=${GEMINI_API_KEY}
FIGMA_ACCESS_TOKEN=${FIGMA_ACCESS_TOKEN}
ENVIRONMENT=production
EOF
  
  echo '🔄 重启服务...'
  pm2 delete product-auto-test 2>/dev/null || echo '服务不存在，新建中...'
  pm2 start api_server.py --name product-auto-test --interpreter \$(pwd)/venv/bin/python
  pm2 save
  
  echo '🔍 检查服务状态...'
  pm2 status
  
  echo '✅ 部署完成！访问: http://${SERVER_IP}:5001'
"

if [ $? -eq 0 ]; then
  echo "🎉 部署成功完成！"
else
  echo "💥 部署过程中出现错误"
  exit 1
fi 