# EduGenius 测试指南

## 📋 功能完成清单

### ✅ 已完成并验证的功能

#### 1. 核心教学系统
- [x] 教学图节点连接（evaluate_answer, tutor_hint）
- [x] 答案评估功能
- [x] 提示生成功能
- [x] 章节划分和进度跟踪
- [x] 自适应难度调整（L1-L5）

#### 2. 文档处理
- [x] PDF 文档处理（支持 OCR）
- [x] TXT 文档处理
- [x] Word 文档处理（DOCX）
- [x] PowerPoint 文档处理（PPTX）
- [x] 文档去重（MD5）
- [x] 章节自动划分

#### 3. 用户认证
- [x] 用户注册
- [x] 用户登录
- [x] JWT Token 认证
- [x] Token 自动刷新
- [x] 密码重置请求
- [x] 密码重置确认
- [x] 密码重置验证

#### 4. 前端页面
- [x] 登录页面 (`/login`)
- [x] 注册页面 (`/register`)
- [x] 忘记密码页面 (`/forgot-password`)
- [x] 重置密码页面 (`/reset-password`)
- [x] 学习页面 (`/study`)
- [x] 仪表盘 (`/dashboard`)
- [x] 文档管理 (`/documents`)
- [x] 错题本 (`/mistakes`)
- [x] 测验页面 (`/quiz`)

#### 5. 数据可视化
- [x] 能力雷达图（真实数据）
- [x] 知识图谱
- [x] 学习进度追踪
- [x] 学习曲线

---

## 🧪 测试步骤

### 前置准备

```bash
# 1. 安装依赖（如果还没安装）
npm install

# 2. 检查前端构建
npm run build

# 3. 启动前端开发服务器
npm run dev
```

### 测试 1: 用户注册和登录

1. **注册新用户**
   - 访问 `http://localhost:3000/register`
   - 输入邮箱、用户名、密码
   - 密码要求：8+字符，包含大小写字母和数字
   - 点击"立即注册"

2. **登录**
   - 访问 `http://localhost:3000/login`
   - 输入刚注册的邮箱和密码
   - 点击"登录"
   - 应该跳转到学习页面

### 测试 2: 文档上传

1. **上传文档**
   - 访问 `http://localhost:3000/documents`
   - 点击"选择文件"
   - 选择 PDF、TXT、DOCX 或 PPTX 文件（最大 50MB）
   - 点击"开始上传"
   - 等待处理完成（可能需要几秒到几分钟）

2. **查看文档列表**
   - 确认上传的文档显示在列表中
   - 检查文档状态（处理中/已完成）
   - 确认章节数量正确

### 测试 3: 学习流程

1. **选择文档**
   - 访问 `http://localhost:3000/study`
   - 如果没有文档，先上传一个
   - 点击文档的"开始学习"按钮

2. **选择章节**
   - 查看章节列表
   - 选择一个未锁定的章节
   - 点击章节进入学习

3. **AI 对话**
   - 在聊天界面输入问题
   - 等待 AI 回复
   - 检查回复质量

4. **答题测试**
   - 回答 AI 生成的问题
   - 查看反馈
   - 检查正确率统计

### 测试 4: 密码重置流程

1. **请求密码重置**
   - 访问 `http://localhost:3000/forgot-password`
   - 输入注册时使用的邮箱
   - 点击"发送重置链接"

2. **获取 Token（开发环境）**
   ```python
   # 在 api 目录运行
   python3 -c "
   import asyncio
   from app.db.database import async_session_maker
   from app.models.password_reset import PasswordReset
   from sqlalchemy import select

   async def get_token():
       async with async_session_maker() as db:
           result = await db.execute(
               select(PasswordReset)
               .order_by(PasswordReset.created_at.desc())
               .limit(1)
           )
           token = result.scalar_one_or_none()
           if token:
               print(f'Token: {token.token}')
               print(f'Email: {token.email}')

   asyncio.run(get_token())
   "
   ```

3. **重置密码**
   - 访问 `http://localhost:3000/reset-password?token=YOUR_TOKEN`
   - 输入新密码
   - 确认新密码
   - 点击"重置密码"

4. **验证新密码**
   - 返回登录页面
   - 使用新密码登录
   - 确认可以成功登录

### 测试 5: 仪表盘

1. **查看能力雷达图**
   - 访问 `http://localhost:3000/dashboard`
   - 查看能力雷达图是否显示
   - 确认数据来自真实的学习记录

2. **查看知识图谱**
   - 检查知识节点是否正确显示
   - 检查节点之间的关系

3. **查看学习统计**
   - 检查学习日历
   - 检查学习进度
   - 检查错题统计

---

## 🔍 已知问题

### 警告（不影响功能）

1. **元数据警告**
   - `viewport` 和 `themeColor` 应该移到 `viewport` 导出
   - 位置：各页面的 `layout.tsx` 或 `page.tsx`
   - 影响：仅警告，不影响功能

2. **TypeScript 错误**
   - 测试文件中缺少 `vitest` 类型声明
   - 位置：`src/lib/__tests__/`
   - 影响：不影响运行，仅类型检查错误

### 待配置

1. **邮件服务**
   - SMTP 配置未设置
   - 影响：密码重置邮件不会发送
   - 解决方案：在 `api/.env` 中配置 SMTP 设置

---

## 📝 快速命令参考

```bash
# 前端
npm run dev          # 启动开发服务器
npm run build        # 构建生产版本
npm run start        # 启动生产服务器

# 后端
cd api
python3 -m uvicorn main:app --reload  # 启动开发服务器
python3 test_password_reset.py         # 测试密码重置

# 数据库
cd api
python3 init_db.py    # 初始化数据库
```

---

## 🎯 下一步改进建议

1. **修复元数据警告**
   - 将 `viewport` 和 `themeColor` 移到 `viewport` 导出

2. **配置邮件服务**
   - 设置 SMTP 配置以启用密码重置邮件

3. **添加更多测试**
   - 端到端测试
   - 集成测试
   - 性能测试

4. **优化用户体验**
   - 添加骨架屏加载状态
   - 优化错误提示
   - 添加更多动画效果

5. **性能优化**
   - 代码分割
   - 图片优化
   - 缓存策略

---

## ✨ 验收标准

- [x] 所有页面可正常访问
- [x] 用户可注册、登录、登出
- [x] 文档可上传并正确处理
- [x] 学习流程可完整运行
- [x] 密码重置功能可用
- [x] 数据可视化正确显示
- [x] 前端构建成功
- [x] 无阻塞性错误

**项目状态**: ✅ 核心功能完成，可以开始用户测试
