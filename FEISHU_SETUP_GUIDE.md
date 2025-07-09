# 飞书API配置指南 / Feishu API Setup Guide

## 1. 注册飞书开放平台应用

### 步骤 / Steps:

1. **访问飞书开放平台**
   - 中文：https://open.feishu.cn/
   - English: https://open.feishu.cn/

2. **创建应用**
   - 点击"开发者后台" → "创建应用"
   - Click "Developer Console" → "Create App"

3. **填写应用信息**
   - 应用名称：自动化测试助手
   - 应用描述：用于PRD文档解析和测试
   - App Name: Automated Testing Assistant
   - App Description: For PRD document parsing and testing

## 2. 配置应用权限

### 必需权限 / Required Permissions:

1. **文档权限 / Document Permissions:**
   - `docx:read` - 文档读取权限
   - `docx:write` - 文档写入权限（可选）

2. **云空间权限 / Drive Permissions:**
   - `drive:drive` - 云空间基础权限
   - `drive:file` - 文件访问权限（用于标题搜索功能）

3. **多维表格权限 / Bitable Permissions:**
   - `bitable:read` - 多维表格读取权限
   - `bitable:write` - 多维表格写入权限

### 配置步骤 / Configuration Steps:

1. 在应用详情页，找到"权限管理"
2. 搜索并添加上述权限
3. 提交审核（企业应用需要审核）

## 3. 获取应用凭证

### 获取信息 / Get Credentials:

1. 在应用详情页，找到"凭证与基础信息"
2. 记录以下信息：
   - **App ID** - 应用ID
   - **App Secret** - 应用密钥
   - **Verification Token** - 验证令牌（可选）

## 4. 配置环境变量

### 创建 .env 文件 / Create .env file:

```bash
# 复制示例文件
cp env.example .env
```

### 编辑 .env 文件 / Edit .env file:

```env
# 飞书开放平台配置
FEISHU_APP_ID=your_app_id_here
FEISHU_APP_SECRET=your_app_secret_here
FEISHU_VERIFICATION_TOKEN=your_verification_token_here

# 其他配置...
GEMINI_API_KEY=your_gemini_api_key
FIGMA_ACCESS_TOKEN=your_figma_access_token
```

## 5. 获取文档Token

### 方法一：从URL获取 / Method 1: From URL

1. 打开你的飞书文档
2. 从URL中提取token：
   ```
   https://your-company.feishu.cn/docx/xxxxxxxxxxxxxxxxxxxx
   ```
   其中 `xxxxxxxxxxxxxxxxxxxx` 就是文档token

### 方法二：使用脚本获取 / Method 2: Use Script

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行文档获取脚本
python3 get_feishu_docs.py
```

## 6. 测试配置

### 测试步骤 / Test Steps:

1. **检查配置**
   ```bash
   source venv/bin/activate
   python3 main.py check-config
   ```

2. **测试飞书API**
   ```bash
   # 测试连接
   python3 main.py test-feishu
   
   # 测试文档解析（需要文档token）
   python3 main.py test-feishu --document-token your_document_token
   ```

## 7. 常见问题 / Common Issues

### Q: 权限不足 / Insufficient Permissions
**A:** 确保应用已获得文档读取权限，且文档已分享给应用

### Q: Token无效 / Invalid Token
**A:** 检查App ID和App Secret是否正确，确保应用已发布

### Q: 文档访问失败 / Document Access Failed
**A:** 确保文档已分享给应用，或应用有足够的权限

## 8. 安全注意事项 / Security Notes

1. **不要提交 .env 文件到版本控制**
2. **定期轮换 App Secret**
3. **限制应用权限范围**
4. **监控API调用频率**

## 9. 下一步 / Next Steps

配置完成后，你可以：
1. 测试飞书PRD解析功能
2. 继续开发网站页面抓取模块
3. 集成Figma设计稿解析
4. 实现AI对比分析功能 