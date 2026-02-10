# 邮件服务配置指南

## 概述

EduGenius 使用 SMTP 协议发送邮件，主要用于密码重置功能。本指南将帮助您配置邮件服务。

---

## 快速开始

### 步骤 1: 选择邮件服务提供商

#### 推荐选项

| 服务商 | 免费额度 | 优势 | 配置难度 |
|--------|----------|------|----------|
| **Gmail** | 500封/天 | 稳定可靠，免费 | ⭐⭐ |
| **QQ邮箱** | 500封/天 | 国内速度快 | ⭐⭐ |
| **163邮箱** | 200封/天 | 国内速度快 | ⭐⭐ |
| **SendGrid** | 100封/天 | 专业服务，送达率高 | ⭐⭐⭐ |
| **Mailgun** | 5000封/月 | API 友好 | ⭐⭐⭐ |

---

## 方案一：Gmail SMTP（推荐个人使用）

### 1.1 启用 Gmail 两步验证

1. 访问 https://myaccount.google.com/security
2. 找到"两步验证"并启用

### 1.2 生成应用专用密码

1. 访问 https://myaccount.google.com/apppasswords
2. 选择"邮件"和"其他（自定义名称）"
3. 输入 "EduGenius"
4. 点击"生成"
5. **保存生成的 16 位密码**（只显示一次！）

### 1.3 配置 .env 文件

在 `api/.env` 文件中添加：

```bash
# Gmail SMTP 配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM=your-email@gmail.com
SMTP_FROM_NAME=EduGenius
SMTP_USE_TLS=true
```

---

## 方案二：QQ 邮箱 SMTP（推荐国内使用）

### 2.1 开启 SMTP 服务

1. 登录 QQ 邮箱 (https://mail.qq.com)
2. 点击"设置" → "账户"
3. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
4. 开启"IMAP/SMTP服务"
5. 按提示使用手机发送短信
6. **保存授权码**（非 QQ 密码！）

### 2.2 配置 .env 文件

```bash
# QQ 邮箱 SMTP 配置
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USER=your-email@qq.com
SMTP_PASSWORD=your-authorization-code
SMTP_FROM=your-email@qq.com
SMTP_FROM_NAME=EduGenius
SMTP_USE_TLS=true
```

---

## 方案三：163 邮箱 SMTP

### 3.1 开启 SMTP 服务

1. 登录 163 邮箱
2. 点击"设置" → "POP3/SMTP/IMAP"
3. 开启"IMAP/SMTP服务"
4. **保存授权码**

### 3.2 配置 .env 文件

```bash
# 163 邮箱 SMTP 配置
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USER=your-email@163.com
SMTP_PASSWORD=your-authorization-code
SMTP_FROM=your-email@163.com
SMTP_FROM_NAME=EduGenius
SMTP_USE_TLS=true
```

---

## 方案四：SendGrid（推荐生产环境）

### 4.1 注册 SendGrid

1. 访问 https://sendgrid.com/
2. 注册账号（免费套餐 100封/天）
3. 创建 API Key

### 4.2 配置 .env 文件

```bash
# SendGrid SMTP 配置
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=YOUR_SENDGRID_API_KEY
SMTP_FROM=noreply@yourdomain.com
SMTP_FROM_NAME=EduGenius
SMTP_USE_TLS=true
```

---

## 完整 .env 配置示例

创建或编辑 `api/.env` 文件：

```bash
# ========== 邮件配置 ==========
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-email@gmail.com
SMTP_FROM_NAME=EduGenius
SMTP_USE_TLS=true

# 密码重置配置
PASSWORD_RESET_TOKEN_EXPIRE_HOURS=1
FRONTEND_URL=http://localhost:3000

# ========== 其他配置 ==========
DASHSCOPE_API_KEY=your-dashscope-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=sqlite+aiosqlite:///./edugenius.db
```

---

## 测试邮件服务

### 使用测试脚本

运行提供的测试脚本：

```bash
cd api
python test_email.py
```

### 手动测试

在 Python 交互环境中：

```python
import asyncio
from app.core.email import email_service

async def test():
    result = await email_service.send_password_reset_email(
        email="test@example.com",
        reset_token="test_token_123"
    )
    print(f"发送结果: {result}")

asyncio.run(test())
```

---

## 常见问题

### ❌ 错误：Authentication failed

**原因**：用户名或密码错误

**解决方案**：
- Gmail：确保使用应用专用密码，而非账户密码
- QQ/163：确保使用授权码，而非邮箱密码
- 检查 SMTP_USER 是否包含完整的邮箱地址

### ❌ 错误：Connection refused

**原因**：SMTP 服务器地址或端口错误

**解决方案**：
- 检查 SMTP_HOST 是否正确
- 确认 SMTP_PORT（常用：25, 465, 587）
- 检查防火墙设置

### ❌ 错误：SSL/TLS 错误

**原因**：TLS 配置问题

**解决方案**：
- Gmail: 端口 587，SMTP_USE_TLS=true
- 其他服务: 尝试端口 465 (SSL) 或 587 (TLS)

### ⚠️ 邮件发送成功但未收到

**可能原因**：
1. 邮件被垃圾邮件过滤 - 检查垃圾邮件文件夹
2. 发送频率过高 - Gmail 限制 500封/天
3. 收件地址错误 - 检查邮箱地址拼写

---

## 生产环境建议

### 1. 使用专业邮件服务

对于生产环境，建议使用专业邮件服务：
- **SendGrid**：送达率高，详细分析
- **Mailgun**：API 友好，价格合理
- **AWS SES**：成本最低，适合大量邮件

### 2. 配置邮件域名

使用自定义域名发送邮件：
1. 在域名提供商处添加 SPF、DKIM、DMARC 记录
2. 提高邮件送达率
3. 防止被标记为垃圾邮件

### 3. 监控邮件发送

- 记录发送日志
- 监控失败率
- 设置告警机制

### 4. 优雅降级

当前实现已包含优雅降级：
```python
if not self.smtp_user:
    logger.warning("⚠️ 邮件服务未配置，跳过发送")
    return False
```

即使未配置邮件服务，系统仍可正常运行，只是不会发送重置邮件。

---

## 安全建议

1. **不要提交 .env 文件到 Git**
   ```bash
   echo "api/.env" >> .gitignore
   ```

2. **使用应用专用密码**
   - 不要使用主账户密码
   - 定期更换密码

3. **限制邮件发送频率**
   - 已在前端实现：同一邮箱 60 秒内只能请求一次

4. **定期检查日志**
   - 监控异常发送行为
   - 及时发现滥用

---

## 下一步

配置完成后：

1. ✅ 运行测试脚本验证配置
2. ✅ 在前端测试密码重置流程
3. ✅ 检查邮件是否正常接收
4. ✅ 查看 `/api` 目录下的日志

---

**文档版本**: v1.0.0
**更新时间**: 2026-02-10
**适用版本**: EduGenius v1.0.0+
