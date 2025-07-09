# 飞书自动化测试API使用指南

## 📋 概述

这个API服务为飞书多维表格提供自动化测试功能，包括：
- 从PRD文档生成测试用例
- 比较Figma设计稿与网站实现
- 更新多维表格结果

## 🚀 快速开始

### 环境变量配置

```bash
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"
export FIGMA_ACCESS_TOKEN="your_figma_token"
export GEMINI_API_KEY="your_gemini_api_key"
```

### 启动服务

```bash
python start_api_server.py
```

默认端口：5001

## 📡 API端点

### 1. 健康检查

**GET** `/health`

**响应示例：**
```json
{
  "service": "飞书自动化测试服务",
  "status": "healthy",
  "timestamp": "2025-07-08T10:30:00.123456"
}
```

### 2. 执行完整工作流

**POST** `/api/execute-workflow`

**参数说明：**

#### 必需参数
- `docToken` (string): PRD文档的token
- `figmaUrl` (string): Figma设计稿URL
- `webUrl` (string): 网站URL，支持两种格式：
  
  **格式1 - @URL:XPath格式（推荐）：**
  ```
  @https://www.example.com/page:/html/body/div[1]/div/div[2]/div[1]/div/div[4]/div[2]/div/div[1]/div[2]/div[1]/div[1]/div/div/span
  ```
  
  **格式2 - 传统URL格式（兼容）：**
  ```
  https://www.example.com/page
  ```

#### 可选参数
- `device` (string): 设备类型，默认 "desktop"
  - 可选值: "desktop", "tablet", "mobile"
- `appToken` (string): 飞书应用token（如果环境变量未设置）
- `tableId` (string): 飞书表格ID（如果环境变量未设置）
- `recordId` (string): 记录ID

**请求示例：**

**使用@URL:XPath格式：**
```json
{
  "docToken": "ZzVudkYQqobhj7xn19GcZ3LFnwd",
  "figmaUrl": "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/demo?node-id=6862-67131&m=dev",
  "webUrl": "@https://www.kalodata.com/product:/html/body/div[1]/div/div[2]/div[1]/div/div[4]/div[2]/div/div[1]/div[2]/div[1]/div[1]/div/div/span",
  "device": "desktop"
}
```

**使用传统URL格式：**
```json
{
  "docToken": "ZzVudkYQqobhj7xn19GcZ3LFnwd",
  "figmaUrl": "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/demo?node-id=6862-67131&m=dev",
  "webUrl": "https://www.kalodata.com/product",
  "device": "desktop"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "工作流执行成功",
  "data": {
    "execution_id": "comparison_1751884835",
    "prd_document_token": "ZzVudkYQqobhj7xn19GcZ3LFnwd",
    "figma_url": "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/demo?node-id=6862-67131&m=dev",
    "website_url": "https://www.kalodata.com/product",
    "xpath_selector": "/html/body/div[1]/div/div[2]/div[1]/div/div[4]/div[2]/div/div[1]/div[2]/div[1]/div[1]/div/div/span",
    "device": "desktop",
    "completed_at": "2025-07-08T10:37:03.789",
    "test_cases_generated": true,
    "comparison_result": {
      "similarity_score": 0.85,
      "output_directory": "reports/comparison_1751884835"
    }
  }
}
```

### 3. 仅执行视觉比较

**POST** `/api/execute-comparison`

**参数说明：**
- `figmaUrl` (string): Figma设计稿URL
- `webUrl` (string): 网站URL，支持@URL:XPath格式
- `device` (string): 设备类型，默认 "desktop"

**请求示例：**
```json
{
  "figmaUrl": "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/demo?node-id=6862-67131&m=dev",
  "webUrl": "@https://www.kalodata.com/product:/html/body/div[1]/section[2]/div/div[1]",
  "device": "desktop"
}
```

### 4. 仅生成测试用例

**POST** `/api/generate-test-cases`

**参数说明：**
- `docToken` (string): PRD文档的token

**请求示例：**
```json
{
  "docToken": "ZzVudkYQqobhj7xn19GcZ3LFnwd"
}
```

## 🎯 XPath选择器说明

### 什么是XPath？
XPath是一种用于选择XML/HTML文档中节点的语言。相比CSS选择器，XPath提供了更强大和精确的元素定位功能。

### 如何获取XPath？
1. **Chrome浏览器方法：**
   - 打开开发者工具（F12）
   - 右键点击要截图的元素
   - 选择"检查"
   - 在Elements面板中右键HTML元素
   - 选择"Copy" → "Copy XPath"

2. **手动构建XPath：**
   ```
   /html/body/div[1]/section[2]/div/div[1]/h2
   ```

### @URL:XPath格式详解

**格式：** `@URL:XPath`

**示例：**
```
@https://www.example.com/page:/html/body/div[1]/main/section[2]/div/h1
```

**解析：**
- `@` - 格式标识符
- `https://www.example.com/page` - 网站URL
- `:` - 分隔符
- `/html/body/div[1]/main/section[2]/div/h1` - XPath选择器

### 常用XPath语法

| 语法 | 说明 | 示例 |
|------|------|------|
| `/` | 选择直接子节点 | `/html/body/div` |
| `//` | 选择后代节点 | `//div[@class='content']` |
| `[n]` | 选择第n个节点 | `div[1]` |
| `[@attr='value']` | 按属性选择 | `//div[@id='header']` |
| `[text()='text']` | 按文本内容选择 | `//span[text()='标题']` |

## 🔗 飞书集成

### 多维表格配置

1. **创建自动化规则**
2. **选择触发器：** 记录满足条件
3. **选择动作：** 发送HTTP请求
4. **配置请求：**
   - **方法：** POST
   - **URL：** `http://your-server:5001/api/execute-workflow`
   - **请求头：** `Content-Type: application/json`
   - **请求体：**
   ```json
   {
     "docToken": "{{第1步.prd 文档链接}}",
     "figmaUrl": "{{第1步.figma地址}}",
     "webUrl": "{{第1步.网页地址}}",
     "isMobile": "{{第1步.是否是移动端}}",
     "recordId": "{{第1步.记录ID}}"
   }
   ```

### 字段值映射说明
**"是否是移动端"字段值处理：**
- 当值为 `"是"` 时 → `device = "mobile"`
- 当值为 `"否"` 时 → `device = "desktop"`
- 支持的值：`"是"`, `"否"`, `"true"`, `"false"`, `"1"`, `"0"`

### 字段映射说明

**输入字段（多维表格）：**
- `prd 文档链接` - PRD文档的完整链接或token（支持两种格式）
- `figma地址` - Figma设计稿完整URL
- `网页地址` - 支持@URL:XPath格式或传统URL
- `是否是移动端` - 单选字段，"是"为移动端设备，"否"为桌面设备
- `记录ID` - 当前记录的ID

### PRD文档链接格式支持
**支持的格式：**
1. **完整链接：** `https://company.feishu.cn/docx/ZzVudkYQqobhj7xn19GcZ3LFnwd`
2. **直接token：** `ZzVudkYQqobhj7xn19GcZ3LFnwd`
3. **超链接对象：** `{"text": "AI 日历", "link": "https://company.feishu.cn/docx/token"}`

**字段类型支持：**
- **单行文本字段：** 支持完整链接、直接token和文档标题
- **超链接字段：** 自动从link属性提取URL，支持所有上述格式
- **文档标题：** 当飞书自动转换为标题时，系统会通过搜索找到对应token

系统会自动识别输入格式并提取正确的文档token。

**输出字段（自动更新）：**
- `测试用例` - AI生成的测试用例
- `网站相似度报告` - 视觉比较分析报告
- `相似度得分` - 数值评分（0-1）

## 🛠️ 开发和调试

### 测试API

```bash
# 测试健康检查
curl http://localhost:5001/health

# 测试完整工作流
curl -X POST http://localhost:5001/api/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "docToken": "test_token",
    "figmaUrl": "https://www.figma.com/design/example",
    "webUrl": "@https://example.com:/html/body/div[1]/main"
  }'
```

### 日志查看

```bash
tail -f logs/app.log
```

### 常见问题

**1. Gemini API不可用**
- 检查API密钥是否正确
- 确认网络连接和地理位置限制

**2. Figma API错误**
- 验证访问令牌权限
- 检查Figma URL格式

**3. XPath元素未找到**
- 验证XPath语法正确性
- 检查页面是否完全加载
- 考虑动态内容的加载时间

**4. 飞书集成问题**
- 确认API服务器地址正确
- 检查飞书应用权限设置
- 验证多维表格字段映射

## 📊 性能优化

- **截图等待时间：** 默认3-5秒，动态页面可增加
- **并发限制：** 建议同时处理不超过3个请求
- **缓存策略：** Figma图片和测试用例支持缓存

## 🔒 安全注意事项

- 环境变量中存储敏感信息
- 使用HTTPS进行生产部署
- 限制API访问IP范围
- 定期轮换API密钥

## 📈 版本更新

**v2.0.0 (当前版本)**
- ✅ 新增@URL:XPath格式支持
- ✅ 改进错误处理和重试机制
- ✅ 优化截图质量和精度
- ✅ 兼容原有CSS类名方式

**v1.0.0**
- 基础功能实现
- 飞书多维表格集成
- Figma和网站比较 