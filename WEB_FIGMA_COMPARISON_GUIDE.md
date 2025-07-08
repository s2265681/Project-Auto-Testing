# 网页与Figma设计稿比对工具使用指南
## Website vs Figma Design Comparison Tool Guide

这个工具可以帮助你自动截取网页并与Figma设计稿进行视觉比对，快速发现实现与设计的差异。

### 🚀 快速开始

#### 1. 环境配置

首先确保你的 `.env` 文件中包含必要的配置：

```bash
# Figma配置
FIGMA_ACCESS_TOKEN=your_figma_access_token_here

# 其他可选配置
GEMINI_API_KEY=your_gemini_api_key
FEISHU_APP_ID=your_feishu_app_id  
FEISHU_APP_SECRET=your_feishu_app_secret
```

#### 2. 获取Figma访问令牌

1. 登录 [Figma](https://www.figma.com/)
2. 进入 Settings → Personal Access Tokens
3. 点击 "Create new token"
4. 复制生成的令牌到 `.env` 文件中

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 测试配置

```bash
# 检查基本配置
python main.py check-config

# 测试Figma URL解析和访问
python main.py test-figma-url --figma-url "你的Figma设计稿URL"
```

### 📋 使用方法

#### 测试Figma URL（推荐先运行）

```bash
python main.py test-figma-url \
    --figma-url "https://www.figma.com/file/ABC123/Design?node-id=1%3A2"
```

#### 基本比对命令

```bash
python main.py compare-web-figma \
    --website-url "https://example.com" \
    --figma-url "https://www.figma.com/file/ABC123/Design?node-id=1%3A2"
```

#### 完整参数

```bash
python main.py compare-web-figma \
    --website-url "https://example.com" \
    --figma-url "https://www.figma.com/file/ABC123/Design?node-id=1%3A2" \
    --device desktop \
    --output-dir reports \
    --wait-time 5
```

### 📱 支持的设备类型

| 设备类型 | 描述 | 分辨率 |
|---------|------|-------|
| `desktop` | 桌面端 | 1920×1080 |
| `laptop` | 笔记本 | 1366×768 |
| `tablet` | 平板 | 768×1024 |
| `mobile` | 手机 | 375×667 |
| `iphone` | iPhone | 414×896 |
| `android` | Android | 360×640 |

### 🔧 参数说明

- `--website-url` / `-w`: 要截图的网页URL（必需）
- `--figma-url` / `-f`: Figma设计稿URL（必需）
- `--device` / `-d`: 设备类型（默认：desktop）
- `--output-dir` / `-o`: 输出目录（默认：reports）
- `--wait-time` / `-t`: 页面加载等待时间，秒（默认：3）

### 📊 输出结果

工具会在指定的输出目录下创建一个时间戳命名的子目录，包含：

1. **网页截图** (`website_<device>.png`)
   - 指定设备尺寸下的网页完整截图

2. **Figma设计稿** (`figma_design.png`)
   - 从Figma导出的设计稿图片

3. **差异对比图** (`diff_comparison_*.png`)
   - 三联图：网页截图 | Figma设计稿 | 差异高亮

4. **详细报告** (`comparison_report.json`)
   - 包含所有比对指标和分析结果的JSON报告

### 📈 比对指标

工具会计算多个相似度指标：

#### 1. 相似度分数 (Similarity Score)
- 基于HSV直方图的相似度
- 范围：0-1（1为完全相似）
- 评级：优秀(≥0.9) | 良好(≥0.8) | 一般(≥0.7) | 较差(≥0.6) | 很差(<0.6)

#### 2. 结构相似性指数 (SSIM)
- 衡量图像结构的相似性
- 范围：-1到1（1为完全相似）
- 对亮度、对比度、结构变化敏感

#### 3. 均方误差 (MSE)
- 像素级别的差异度量
- 数值越小表示越相似
- 对颜色差异敏感

#### 4. 感知哈希距离 (Hash Distance)
- 基于图像感知特征的距离
- 数值越小表示越相似
- 对整体结构差异敏感

#### 5. 差异区域数 (Differences Count)
- 检测到的不同区域数量
- 反映布局差异的复杂程度

### 💡 使用技巧

#### 1. 网页截图优化
- **等待时间**：对于加载较慢的页面，增加 `--wait-time` 参数
- **设备选择**：根据设计稿的目标设备选择合适的设备类型
- **页面状态**：确保页面处于期望的状态（如已登录、特定页面等）

#### 2. Figma URL格式
- **标准格式**：`https://www.figma.com/file/{file_id}/{title}?node-id={node_id}`
- **设计格式**：`https://www.figma.com/design/{file_id}/{title}?node-id={node_id}`
- **简化格式**：`https://www.figma.com/file/{file_id}/{title}`（将使用第一个页面）
- **节点ID**：建议包含具体的节点ID，否则工具会使用第一个页面
- **权限**：确保Figma文件对你的令牌可见
- **测试**：使用 `test-figma-url` 命令验证URL是否正确

#### 3. 结果解读
- **高相似度（>0.8）**：实现基本符合设计
- **中等相似度（0.6-0.8）**：存在明显差异，需要调整
- **低相似度（<0.6）**：实现与设计差异较大，需要重新检查

### 🔍 故障排除

#### 常见问题

1. **"FIGMA_ACCESS_TOKEN not found"**
   - 确保 `.env` 文件中配置了正确的Figma访问令牌

2. **"Invalid Figma URL format"**
   - 检查Figma URL格式是否正确
   - 确保URL包含文件ID

3. **"无法读取图片文件"**
   - 检查网络连接
   - 确保网页可正常访问
   - 检查浏览器驱动是否正确安装

4. **"无法导出Figma图片"**
   - 检查Figma文件权限
   - 确认节点ID是否存在
   - 验证访问令牌权限

#### 调试建议

1. **先检查配置**：
   ```bash
   python main.py check-config
   ```

2. **测试Figma URL**：
   ```bash
   python main.py test-figma-url --figma-url "你的Figma URL"
   ```

3. **使用详细日志**：
   - 查看 `logs/app.log` 文件获取详细错误信息

4. **分步测试**：
   - 先测试简单的公开网页
   - 再测试复杂页面或需要认证的页面

### 🎯 最佳实践

1. **设计稿准备**
   - 确保Figma设计稿是最新版本
   - 选择与网页对应的正确页面/组件
   - 保持设计稿的清晰度

2. **网页准备**
   - 确保网页完全加载
   - 处理动态内容（如轮播图、动画等）
   - 考虑页面的响应式行为

3. **比对策略**
   - 对于复杂页面，可以分块进行比对
   - 定期进行比对，及时发现问题
   - 结合人工审查，自动比对作为辅助

### 📝 示例用法

#### 示例1：基本比对
```bash
python main.py compare-web-figma \
    --website-url "https://www.apple.com" \
    --figma-url "https://www.figma.com/file/example/Apple-Homepage?node-id=1%3A2"
```

#### 示例2：移动端比对
```bash
python main.py compare-web-figma \
    --website-url "https://m.taobao.com" \
    --figma-url "https://www.figma.com/file/example/Mobile-Design?node-id=5%3A10" \
    --device mobile \
    --wait-time 8
```

#### 示例3：自定义输出目录
```bash
python main.py compare-web-figma \
    --website-url "https://example.com/dashboard" \
    --figma-url "https://www.figma.com/file/example/Dashboard?node-id=15%3A20" \
    --device laptop \
    --output-dir "./comparison-results" \
    --wait-time 5
```

通过这个工具，你可以快速、准确地比对网页实现与设计稿的差异，提高开发效率和设计一致性。 