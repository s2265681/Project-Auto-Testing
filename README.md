# 自动化测试助手项目 (Automated Testing Assistant)

## 项目目标
通过对比飞书PRD文档与网站功能、Figma设计稿与网站视觉，实现自动化测试分析。

## 功能模块
1. **飞书PRD解析模块** - 访问和解析飞书文档内容
2. **网站页面抓取模块** - 获取网站页面内容和截图
3. **Figma设计稿解析模块** - 获取Figma设计文件
4. **AI对比分析模块** - 使用Gemini AI进行文本和图像对比
5. **报告生成模块** - 生成测试报告
6. **多维表格操作模块** - 操作飞书多维表格，更新测试结果
7. **工作流执行模块** - 一键执行完整测试流程

## 新增功能 🆕
### 执行按钮工作流
当点击执行结果栏按钮时，自动完成以下流程：
1. 解析PRD文档生成测试用例
2. 比较Figma设计与网站视觉效果
3. 将测试用例填入多维表格的测试用例文档栏
4. 将比较结果填入网站相似度报告栏

## 技术栈
- Python 3.8+
- Selenium/Playwright (网页自动化)
- Pillow/OpenCV (图像处理)
- Google Gemini AI API
- 飞书开放平台API
- Figma API

## 安装和运行
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入API密钥

# 运行测试
python main.py
```

## 项目结构
```
Project-Aut-Testing/
├── src/
│   ├── feishu/          # 飞书PRD解析模块 + 多维表格操作
│   ├── website/          # 网站页面抓取模块
│   ├── figma/           # Figma设计稿解析模块
│   ├── ai_analysis/     # AI对比分析模块
│   ├── reporting/       # 报告生成模块
│   ├── workflow/        # 工作流执行模块 🆕
│   └── utils/           # 工具函数
├── config/              # 配置文件
├── tests/               # 测试文件
├── reports/             # 生成的报告
├── requirements.txt     # Python依赖
├── .env.example        # 环境变量示例
└── main.py             # 主程序入口
```

## 🚀 新功能使用指南

### 1. 执行完整工作流

```bash
# 执行按钮点击工作流
python main.py execute-workflow \
  --app-token <多维表格应用token> \
  --table-id <数据表ID> \
  --record-id <记录ID> \
  --prd-document-token <PRD文档token> \
  --figma-url <Figma设计稿URL> \
  --website-url <网站URL> \
  --website-classes <CSS类名(可选)> \
  --device desktop \
  --output-dir reports
```

#### 参数说明：
- `--app-token` / `-a`: 飞书多维表格应用token
- `--table-id` / `-t`: 数据表ID
- `--record-id` / `-r`: 要更新的记录ID
- `--prd-document-token` / `-p`: PRD文档token
- `--figma-url` / `-f`: Figma设计稿URL
- `--website-url` / `-w`: 网站URL
- `--website-classes` / `-c`: CSS类名(可选，用于截取特定元素)
- `--device` / `-d`: 设备类型 (desktop, mobile, tablet)
- `--output-dir` / `-o`: 输出目录

### 2. 检查多维表格结构

```bash
# 检查表格结构，确保字段配置正确
python main.py inspect-bitable \
  --app-token <多维表格应用token> \
  --table-id <数据表ID>
```

### 3. 多维表格字段要求

为了正确使用工作流功能，请确保您的多维表格包含以下字段：

| 字段名 | 类型 | 用途 |
|--------|------|------|
| `项目名称` | 单行文本 | 项目标识 |
| `prd文档链接token` | 单行文本 | PRD文档token |
| `测试用例文档` | 多行文本 | 存储生成的测试用例 |
| `figma地址` | URL | Figma设计稿链接 |
| `网页地址` | URL | 要测试的网页链接 |
| `网页类名` | 单行文本 | CSS类名(可选) |
| `网站相似度报告` | 多行文本 | 存储比较结果报告 |
| `执行结果` | 单选 | 执行状态标记 |

## 📋 使用示例

### 示例1：基本工作流执行

```bash
python main.py execute-workflow \
  --app-token "bascAbCdEfGhIjKl" \
  --table-id "tblXyZ123456" \
  --record-id "recAbc789def" \
  --prd-document-token "ZzVudkYQqobhj7xn19GcZ3LFnwd" \
  --figma-url "https://www.figma.com/design/ABC123/Design?node-id=1234" \
  --website-url "https://www.kalodata.com/product" \
  --device desktop
```

### 示例2：指定CSS类的元素比较

```bash
python main.py execute-workflow \
  --app-token "bascAbCdEfGhIjKl" \
  --table-id "tblXyZ123456" \
  --record-id "recAbc789def" \
  --prd-document-token "ZzVudkYQqobhj7xn19GcZ3LFnwd" \
  --figma-url "https://www.figma.com/design/ABC123/Design?node-id=1234" \
  --website-url "https://www.kalodata.com/product" \
  --website-classes "ant-input-affix-wrapper css-2yep4o ant-input-outlined w-[599px]" \
  --device desktop
```

### 示例3：移动端比较

```bash
python main.py execute-workflow \
  --app-token "bascAbCdEfGhIjKl" \
  --table-id "tblXyZ123456" \
  --record-id "recAbc789def" \
  --prd-document-token "ZzVudkYQqobhj7xn19GcZ3LFnwd" \
  --figma-url "https://www.figma.com/design/ABC123/Mobile-Design?node-id=5678" \
  --website-url "https://m.kalodata.com/product" \
  --device mobile
```

## 🔧 原有功能命令

# 提取任何飞书文档内容
python main.py extract-document -d <document_token> -o <output_file>

# 解析飞书文档
python main.py extract-document -d ZzVudkYQqobhj7xn19GcZ3LFnwd

# 生成测试用例
python main.py generate-cases -d <document_token> -n <case_count>
python main.py generate-cases -d ZzVudkYQqobhj7xn19GcZ3LFnwd

# 查看项目状态
python main.py status

# 检查配置
python main.py check-config

# 测试Figma URL
python main.py test-figma-url --figma-url 'https://www.figma.com/file/ABC/Design'

# 对比网站与Figma设计
python main.py compare-web-figma --website-url 'https://example.com' --figma-url 'https://www.figma.com/file/ABC/Design'    

# 指定区域网站某个区域与Figma设计
source venv/bin/activate && python main.py compare-web-figma --selector ".bg-kalo-container" --website-url "https://www.kalodata.com/product" --figma-url "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/25%E5%85%A8%E5%B1%80%E8%BF%AD%E4%BB%A3?node-id=6862-67203&m=dev"

# 截取指定区域图片
 source venv/bin/activate && python main.py capture-element \
       --website-url "https://www.kalodata.com/product" \
       --selector "其他CSS选择器" \
       --device desktop \
       --wait-time 5

# 根据tailwindcss样式截图
python main.py capture-by-classes --website-url "https://www.kalodata.com/product" --classes "ant-input-affix-wrapper css-2yep4o ant-input-outlined w-[599px]" --element-index 0 --output-dir "screenshots" --device desktop

# 指定浏览器的语言环境 英语
python main.py capture-by-classes --website-url "https://www.kalodata.com/product" --classes "ant-input-affix-wrapper css-2yep4o ant-input-outlined w-[599px]" --element-index 0 --output-dir "screenshots" --device desktop --language "en-US"

# 网页局部与figma部分内容进行对比 
source venv/bin/activate && python main.py compare-web-figma \
  --website-url "https://www.kalodata.com/product" \
  --classes "ant-input-affix-wrapper css-2yep4o ant-input-outlined w-[599px]" \
  --figma-url "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/25%E5%85%A8%E5%B1%80%E8%BF%AD%E4%BB%A3?node-id=6862-67131&m=dev" \
  --language "en-US"

## 🔗 配置要求

确保在 `.env` 文件中配置以下信息：

```env
# 飞书开放平台配置
FEISHU_APP_ID=your_app_id_here
FEISHU_APP_SECRET=your_app_secret_here

# Figma配置
FIGMA_ACCESS_TOKEN=your_figma_access_token_here

# Gemini AI配置
GEMINI_API_KEY=your_gemini_api_key_here
```

## ⚠️ 权限要求

### 飞书权限
- `docx:read` - 文档读取权限
- `bitable:read` - 多维表格读取权限
- `bitable:write` - 多维表格写入权限

### Figma权限
- 确保Figma访问令牌有权限访问指定的设计文件

## 🏗️ 工作流程说明

1. **PRD解析**: 从飞书文档中提取PRD内容
2. **测试用例生成**: 使用Gemini AI根据PRD生成测试用例
3. **网页截图**: 捕获网页或指定元素的截图
4. **Figma截图**: 从Figma导出设计稿图像
5. **视觉比较**: 计算相似度指标和差异
6. **结果更新**: 将测试用例和比较报告更新到多维表格

## 📊 输出结果

工作流会生成以下内容：
- 测试用例文档（填入多维表格）
- 网站相似度报告（填入多维表格）
- 比较图像文件（保存到本地）
- 详细的JSON报告（保存到本地）

## 🚨 故障排除

1. **权限问题**: 确保飞书应用有足够的权限访问文档和多维表格
2. **字段名称**: 检查多维表格的字段名称是否与代码中定义的一致
3. **网络问题**: 确保网络连接稳定，可以访问Figma和目标网站
4. **浏览器驱动**: 确保已安装Chrome浏览器和对应的ChromeDriver

## 📞 技术支持

如果遇到问题，请检查：
1. 配置文件 `.env` 是否正确设置
2. 使用 `python main.py check-config` 验证配置
3. 使用 `python main.py inspect-bitable` 检查表格结构
4. 查看日志文件 `logs/app.log` 获取详细错误信息




# 通过飞书多维表格进行执行任务
python main.py execute-workflow \
  --app-token "GzpBblAM5aoH18sHNt0cpDYXnYf" \
  --table-id "tblsLP3GVnzFobjP" \
  --record-id "Dq3YrJb2ke0LQdcmLjZccaZ2nz0" \
  --prd-document-token "ZzVudkYQqobhj7xn19GcZ3LFnwd" \
  --figma-url "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/25%E5%85%A8%E5%B1%80%E8%BF%AD%E4%BB%A3?node-id=6862-67131&m=dev" \
  --website-url "https://www.kalodata.com/product" \
  --website-classes "ant-input-affix-wrapper css-2yep4o ant-input-outlined w-[599px]" \
  --device desktop
<!-- 
@https://rxd3bf272sk.feishu.cn/base/GzpBblAM5aoH18sHNt0cpDYXnYf?table=tblsLP3GVnzFobjP&view=vewNhLnlHf 
@https://rxd3bf272sk.feishu.cn/record/Dq3YrJb2ke0LQdcmLjZccaZ2nz0  -->

apptoken GzpBblAM5aoH18sHNt0cpDYXnYf
recordid Dq3YrJb2ke0LQdcmLjZccaZ2nz0


# 内容回填多维表格
 cd /Users/mac/Github/Project-Aut-Testing && python main.py inspect-bitable --app-token "GzpBblAM5aoH18sHNt0cpDYXnYf" --table-id "tblsLP3GVnzFobjP"


 # 更新
 python main.py test-bitable-update --app-token "GzpBblAM5aoH18sHNt0cpDYXnYf" --table-id "tblsLP3GVnzFobjP" --record-id "Dq3YrJb2ke0LQdcmLjZccaZ2nz0" --field-name "测试用例文档" --field-value "这是一个测试更新 - $(date)"

# 查询当前条的id
python main.py inspect-bitable --app-token "GzpBblAM5aoH18sHNt0cpDYXnYf" --table-id "tblsLP3GVnzFobjP"


 # 1. 测试权限是否配置成功
python main.py test-bitable-update \
  --app-token "GzpBblAM5aoH18sHNt0cpDYXnYf" \
  --table-id "tblsLP3GVnzFobjP" \
  --record-id "receLUWNBZ" \
  --field-name "测试用例文档" \
  --field-value "权限测试成功 ✅"

# 2. 如果测试成功，运行完整工作流
python main.py execute-workflow \
  --app-token "GzpBblAM5aoH18sHNt0cpDYXnYf" \
  --table-id "tblsLP3GVnzFobjP" \
  --record-id "receLUWNBZ" \
  --prd-document-token "ZzVudkYQqobhj7xn19GcZ3LFnwd" \
  --figma-url "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/25%E5%85%A8%E5%B1%80%E8%BF%AD%E4%BB%A3?node-id=6862-67131&m=dev" \
  --website-url "https://www.kalodata.com/product" \
  --website-classes "ant-input-affix-wrapper css-2yep4o ant-input-outlined w-[599px]" \
  --device desktop


  # 最终测试
  python main.py execute-workflow --app-token "GzpBblAM5aoH18sHNt0cpDYXnYf" --table-id "tblsLP3GVnzFobjP" --record-id "receLUWNBZ" --prd-document-token "ZzVudkYQqobhj7xn19GcZ3LFnwd" --figma-url "https://www.figma.com/design/VHgFAzQGYpZtOgYJxk609O/25%E5%85%A8%E5%B1%80%E8%BF%AD%E4%BB%A3?node-id=6862-67131&m=dev" --website-url "https://www.kalodata.com/product" --website-classes "ant-input-affix-wrapper css-2yep4o ant-input-outlined w-[599px]" --device desktop