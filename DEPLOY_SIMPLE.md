# 🚀 超简化部署指南

## 📋 **一次性配置**

### **1. GitHub Secrets配置**
在GitHub仓库 `Settings > Secrets and variables > Actions` 中添加：

```
SERVER_HOST=18.141.179.222
SERVER_USER=ubuntu
SSH_PRIVATE_KEY=你的SSH私钥内容
FEISHU_APP_ID=你的飞书应用ID
FEISHU_APP_SECRET=你的飞书应用密钥
FEISHU_VERIFICATION_TOKEN=你的飞书验证令牌
GEMINI_API_KEY=你的Gemini API密钥
FIGMA_ACCESS_TOKEN=你的Figma访问令牌
```

### **2. 服务器准备**
在服务器上运行一次：
```bash
# 创建目录
sudo mkdir -p /var/www/app
sudo chown -R ubuntu:ubuntu /var/www/app

# 安装必要软件
sudo apt update
sudo apt install -y python3 python3-pip nodejs npm git
sudo npm install -g pm2

# 添加SSH公钥到 ~/.ssh/authorized_keys
```

## 🎯 **使用方法**

### **自动部署**
推送代码到main分支即可：
```bash
git add .
git commit -m "部署更新"
git push origin main
```

### **手动部署**
如需手动部署：
```bash
chmod +x deploy.sh
./deploy.sh
```

## 📊 **部署流程**

1. **代码更新** - 从GitHub拉取最新代码
2. **依赖安装** - 安装Python包
3. **环境配置** - 创建生产环境配置
4. **服务重启** - 重启PM2服务

## 🔗 **访问地址**

- **应用地址**: http://18.141.179.222:5001
- **健康检查**: http://18.141.179.222:5001/health

## 📝 **对比原来的改进**

| 项目 | 原来 | 现在 |
|------|------|------|
| GitHub Actions | 3个步骤，40行 | 1个步骤，28行 |
| deploy.sh | 207行复杂脚本 | 23行简单脚本 |
| 配置文件 | 多个复杂配置 | 1个简单说明 |
| 部署时间 | ~2-3分钟 | ~30-60秒 |
| 调试输出 | 大量日志 | 简洁输出 |

## ⚡ **特点**

- **极简**: 只保留核心功能
- **快速**: 最少的步骤和等待
- **可靠**: 无复杂逻辑和错误处理
- **清晰**: 一目了然的部署过程

---

**总结**: 推送代码 → 自动部署 → 立即可用 🎉 