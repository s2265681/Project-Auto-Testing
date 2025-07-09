# 部署配置指南 / Deployment Configuration Guide

## 🚀 自动部署设置

### GitHub Actions 配置

项目已配置GitHub Actions，当代码推送到 `main` 分支时自动部署到生产服务器。

**部署目标：** `ubuntu@18.141.179.222:/var/www/app/product-auto-test`

**部署流程：**
1. 代码推送到 `main` 分支
2. GitHub Actions 自动触发
3. 安装Python依赖
4. 部署到生产服务器
5. 重启服务

### 必需的GitHub Secrets

在GitHub仓库设置中添加以下secrets：

```
AWS_ACCESS_KEY_ID: AWS访问密钥ID
AWS_SECRET_ACCESS_KEY: AWS访问密钥Secret
EC2_INSTANCE_ID: EC2实例ID (例如: i-1234567890abcdef0)
S3_BUCKET_NAME: S3存储桶名称 (setup-aws-resources.sh脚本会生成)
FEISHU_APP_ID: 飞书应用ID
FEISHU_APP_SECRET: 飞书应用密钥
FEISHU_VERIFICATION_TOKEN: 飞书验证令牌
GEMINI_API_KEY: Gemini API密钥
FIGMA_ACCESS_TOKEN: Figma访问令牌
```

**注意：** 
- 使用AWS Systems Manager Session Manager代替SSH连接
- 需要创建S3存储桶用于临时文件存储
- 这些secrets将在部署时自动创建生产环境的.env文件

### 部署脚本

- **文件位置：** `deploy.sh`
- **功能：** 通过AWS Systems Manager自动部署Python应用到EC2实例
- **部署方式：** 使用S3临时存储 + SSM命令执行
- **排除文件：** venv, __pycache__, *.pyc, .git, logs, reports, screenshots

## 🌍 环境配置

### AWS环境设置

#### 快速设置（推荐）

使用提供的自动化脚本快速设置AWS资源：

```bash
chmod +x setup-aws-resources.sh
./setup-aws-resources.sh
```

该脚本会自动：
- 创建S3存储桶
- 创建IAM角色和实例配置文件
- 列出可用的EC2实例
- 验证资源设置

#### 手动设置

**1. 创建S3存储桶**
```bash
aws s3 mb s3://temp-deployment-bucket --region ap-southeast-1
```

**2. 创建IAM角色**
```bash
# 创建角色
aws iam create-role --role-name ProductAutoTestEC2Role --assume-role-policy-document file://trust-policy.json

# 附加策略
aws iam attach-role-policy --role-name ProductAutoTestEC2Role --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam attach-role-policy --role-name ProductAutoTestEC2Role --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
aws iam attach-role-policy --role-name ProductAutoTestEC2Role --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy

# 创建实例配置文件
aws iam create-instance-profile --instance-profile-name ProductAutoTestEC2Role
aws iam add-role-to-instance-profile --instance-profile-name ProductAutoTestEC2Role --role-name ProductAutoTestEC2Role
```

**3. 确保EC2实例有适当的IAM角色**
将创建的IAM角色附加到EC2实例：
```bash
aws ec2 associate-iam-instance-profile --instance-id i-1234567890abcdef0 --iam-instance-profile Name=ProductAutoTestEC2Role
```

**4. 安装SSM Agent（通常已预装）**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install amazon-ssm-agent

# 启动服务
sudo systemctl start amazon-ssm-agent
sudo systemctl enable amazon-ssm-agent
```

**5. 验证SSM连接**
```bash
aws ssm describe-instance-information --filters "Key=InstanceIds,Values=i-1234567890abcdef0"
```

### 动态环境切换

系统支持通过环境变量 `ENVIRONMENT` 动态切换开发/生产环境：

**开发环境（默认）：**
```bash
# 不设置环境变量，或者：
export ENVIRONMENT=development
# API服务器：http://localhost:5001
```

**生产环境：**
```bash
export ENVIRONMENT=production
# API服务器：http://18.141.179.222:5001
```

### .env文件处理

#### 开发环境
- 使用项目根目录的`.env`文件
- 包含本地开发所需的API密钥

#### 生产环境
- `.env`文件不会被git跟踪（在.gitignore中）
- 部署时通过GitHub Secrets自动创建生产环境的`.env`文件
- 包含生产环境所需的API密钥和配置

**自动创建的生产环境.env文件内容：**
```env
FEISHU_APP_ID=从GitHub Secrets获取
FEISHU_APP_SECRET=从GitHub Secrets获取
FEISHU_VERIFICATION_TOKEN=从GitHub Secrets获取
GEMINI_API_KEY=从GitHub Secrets获取
FIGMA_ACCESS_TOKEN=从GitHub Secrets获取
```

### 环境配置文件

- **文件位置：** `config/environment.py`
- **功能：** 统一管理环境配置
- **主要函数：**
  - `get_api_base_url()` - 获取API基础URL
  - `is_development()` - 判断是否为开发环境
  - `is_production()` - 判断是否为生产环境

### 更新的文件

以下文件已更新以支持动态环境配置：

1. **`test_xpath_api.py`** - 测试脚本使用动态URL
2. **`src/workflow/executor.py`** - 工作流执行器使用动态URL
3. **`test_api.py`** - API测试脚本使用动态URL
4. **`API_USAGE_GUIDE.md`** - 文档更新环境配置说明

## 📋 部署检查清单

### 部署前检查

- [ ] 代码已推送到 `main` 分支
- [ ] GitHub Secrets 已配置（包括所有API密钥）
- [ ] AWS凭证权限正确
- [ ] EC2实例ID正确且实例运行中
- [ ] EC2实例已安装SSM Agent
- [ ] S3存储桶已创建（运行setup-aws-resources.sh自动创建）
- [ ] 本地.env文件包含所有必需的环境变量

### 部署后验证

- [ ] 服务正常启动
- [ ] 环境变量设置正确（ENVIRONMENT=production）
- [ ] 生产环境.env文件创建成功
- [ ] API端点可访问
- [ ] 日志无错误
- [ ] 飞书/Gemini/Figma API可正常调用

## 🛠️ 手动部署

如需手动部署，在项目根目录运行：

```bash
chmod +x deploy.sh
./deploy.sh
```

## 🔍 部署验证

### 自动验证脚本

使用提供的验证脚本检查部署是否成功：

```bash
# 本地验证
python verify_deployment.py

# 在生产服务器上验证
ssh ubuntu@18.141.179.222 "cd /var/www/app/product-auto-test && python3 verify_deployment.py"
```

**验证项目：**
- 环境变量配置检查
- 关键文件存在性验证
- API服务健康状态检查

### 手动验证步骤

1. **检查EC2实例状态**
   ```bash
   aws ec2 describe-instances --instance-ids i-1234567890abcdef0
   ```

2. **通过SSM检查服务状态**
   ```bash
   aws ssm send-command \
     --instance-ids i-1234567890abcdef0 \
     --document-name "AWS-RunShellScript" \
     --parameters 'commands=["pm2 status product-auto-test"]'
   ```

3. **检查API端点**
   ```bash
   curl http://18.141.179.222:5001/health
   ```

4. **通过SSM检查环境变量**
   ```bash
   aws ssm send-command \
     --instance-ids i-1234567890abcdef0 \
     --document-name "AWS-RunShellScript" \
     --parameters 'commands=["cd /var/www/app/product-auto-test && cat .env"]'
   ```

5. **通过SSM检查日志**
   ```bash
   aws ssm send-command \
     --instance-ids i-1234567890abcdef0 \
     --document-name "AWS-RunShellScript" \
     --parameters 'commands=["pm2 logs product-auto-test --lines 50"]'
   ```

## 📊 服务管理

### 在生产服务器上

```bash
# 查看服务状态
pm2 status product-auto-test

# 查看日志
pm2 logs product-auto-test

# 重启服务
pm2 restart product-auto-test

# 停止服务
pm2 stop product-auto-test
```

## 🔍 问题排查

### 常见问题

1. **部署失败**
   - 检查SSH密钥是否正确
   - 确认服务器磁盘空间足够
   - 查看GitHub Actions日志

2. **服务启动失败**
   - 检查Python依赖是否安装完整
   - 确认端口5001未被占用
   - 查看pm2日志定位问题

3. **环境配置错误**
   - 确认环境变量设置正确
   - 检查配置文件路径
   - 验证API地址可达性

### 日志位置

- **应用日志：** `/var/www/app/product-auto-test/logs/`
- **PM2日志：** `~/.pm2/logs/`

## 🔒 安全考虑

- SSH密钥仅在CI/CD环境中使用
- 生产环境API地址限制访问
- 定期更新依赖包
- 监控服务器资源使用

## 📈 更新记录

**v2.2.0 (当前版本)**
- ✅ 改用AWS Systems Manager Session Manager部署
- ✅ 移除SSH私钥依赖，使用AWS Access Key
- ✅ 添加S3临时存储支持
- ✅ 提供自动化AWS资源设置脚本
- ✅ 优化IAM角色和权限配置

**v2.1.0**
- ✅ 实现GitHub Actions自动部署
- ✅ 添加动态环境配置支持
- ✅ 优化部署脚本和流程
- ✅ 更新API文档和测试脚本

**v2.0.0**
- ✅ 新增@URL:XPath格式支持
- ✅ 改进错误处理和重试机制 