#!/bin/bash

# 🚀 超简化部署脚本
# 用法: ./deploy.sh

# 配置
SERVER="ubuntu@18.141.179.222"
APP_DIR="/var/www/app/product-auto-test"

echo "🚀 开始部署到生产服务器..."

# 一键部署
ssh -o StrictHostKeyChecking=no $SERVER "
  echo '📦 更新代码...'
  cd $APP_DIR || { cd /var/www/app && git clone https://github.com/s2265681/Project-Aut-Testing.git product-auto-test && cd product-auto-test; }
  git pull origin main
  
  echo '📚 安装依赖...'
  python3 -m pip install -r requirements.txt --user --quiet
  
  echo '🔄 重启服务...'
  pm2 restart product-auto-test || pm2 start api_server.py --name product-auto-test --interpreter python3
  pm2 save
  
  echo '✅ 部署完成！访问: http://18.141.179.222:5001'
"

echo "🎉 部署完成！" 