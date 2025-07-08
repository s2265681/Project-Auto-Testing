# 飞书多维表格权限配置指南 / Feishu Bitable Permissions Setup Guide

## 🚨 问题诊断 / Problem Diagnosis

如果您遇到403 Forbidden错误，说明应用缺少多维表格的访问权限。

## 🔧 解决方案 / Solutions

### 步骤1: 检查应用权限范围 / Step 1: Check App Permissions

1. **登录飞书开放平台**
   - 访问: https://open.feishu.cn/
   - 进入您的应用管理页面

2. **添加多维表格权限**
   在"权限管理"页面添加以下权限：
   ```
   ✅ bitable:read    - 多维表格读取权限
   ✅ bitable:write   - 多维表格写入权限  
   ✅ docx:read       - 文档读取权限
   ```

3. **提交审核**
   - 添加权限后需要提交审核
   - 企业版应用需要管理员批准

### 步骤2: 应用授权访问多维表格 / Step 2: Authorize App Access

1. **方式一：通过多维表格设置**
   - 打开您的多维表格
   - 点击右上角"..."菜单
   - 选择"应用设置"或"API管理"  
   - 添加您的应用并授权

2. **方式二：通过应用安装**
   - 在应用管理页面生成安装链接
   - 访问安装链接并授权应用访问多维表格

### 步骤3: 验证token权限 / Step 3: Verify Token Permissions

1. **使用用户token而非tenant token**
   如果继续有权限问题，可能需要使用用户访问令牌：
   
   ```python
   # 在 src/feishu/client.py 中添加用户token支持
   def get_user_access_token(self, user_code: str) -> str:
       """获取用户访问令牌"""
       url = f"{self.base_url}/authen/v1/access_token"
       # 实现用户OAuth流程
   ```

2. **检查token范围**
   确保获取的token包含bitable相关权限

### 步骤4: 测试权限 / Step 4: Test Permissions

运行以下命令测试权限：

```bash
# 测试读取权限
python main.py inspect-bitable \
  --app-token "your_app_token" \
  --table-id "your_table_id"

# 测试写入权限  
python main.py test-bitable-update \
  --app-token "your_app_token" \
  --table-id "your_table_id" \
  --record-id "your_record_id" \
  --field-name "测试字段" \
  --field-value "测试值"
```

## 🔍 权限排查清单 / Permission Troubleshooting Checklist

- [ ] 应用已添加`bitable:read`和`bitable:write`权限
- [ ] 权限申请已通过审核
- [ ] 应用已被授权访问目标多维表格
- [ ] 使用的token有效且包含正确权限
- [ ] 多维表格和记录ID正确
- [ ] 字段名称完全匹配（区分大小写）

## 🆘 常见错误及解决方案 / Common Errors and Solutions

### 403 Forbidden
**原因**: 缺少权限或未授权
**解决**: 按照上述步骤1-2配置权限和授权

### 400 Bad Request  
**原因**: 请求参数错误
**解决**: 检查app_token、table_id、record_id是否正确

### 404 Not Found
**原因**: 资源不存在
**解决**: 确认多维表格和记录确实存在

### 500 Internal Server Error
**原因**: 服务器内部错误
**解决**: 稍后重试或联系飞书技术支持

## 📞 获得帮助 / Getting Help

如果问题仍然存在，请：

1. **检查飞书开放平台文档**
   - https://open.feishu.cn/document/

2. **联系管理员**
   - 请您的飞书管理员确认应用权限

3. **查看详细错误日志**
   ```bash
   tail -f logs/app.log
   ```

4. **使用测试环境**
   - 先在测试应用和测试表格上验证功能

## 🔐 安全建议 / Security Recommendations

1. **最小权限原则**
   - 只申请必要的权限
   - 定期review权限范围

2. **Token安全**
   - 不要在代码中硬编码token
   - 定期轮换access token

3. **审计日志**
   - 启用应用访问日志
   - 监控异常访问行为 