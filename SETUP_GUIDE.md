# EduGenius 启动指南

这是一份详细的启动配置指南，帮助新开发者快速搭建和运行 EduGenius 项目。

## 目录

- [项目概述](#项目概述)
- [系统要求](#系统要求)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [详细配置](#详细配置)
- [数据库配置](#数据库配置)
- [API 密钥配置](#api-密钥配置)
- [启动服务](#启动服务)
- [常见问题](#常见问题)

---

## 项目概述

EduGenius 是一个高端 AI 自适应教育平台，包含：

- **前端**: Next.js 16 + React + TypeScript + Tailwind CSS
- **后端**: FastAPI + Python 3.12
- **数据库**: SQLite
- **向量数据库**: ChromaDB
- **AI 模型**: 通义千问 (DashScope)

---

## 系统要求

### 必需软件

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Node.js | >= 18.17.0 | 前端运行环境 |
| Python | 3.12 | 后端运行环境 |
| npm | >= 9.0.0 | 包管理器 |

### 验证安装

```bash
# 检查 Node.js
node --version

# 检查 npm
npm --version

# 检查 Python
python3 --version
```

---

## 项目结构

```
EduGenius/
├── api/                    # 后端 (FastAPI)
│   ├── app/               # 应用代码
│   ├── migrations/        # 数据库迁移脚本
│   ├── uploads/           # 上传文件存储
│   ├── chroma_db/         # 向量数据库
│   ├── edugenius.db       # SQLite 数据库
│   ├── main.py           # 后端入口
│   ├── requirements.txt   # Python 依赖
│   └── .env.example      # 环境变量示例
│
├── src/                   # 前端 (Next.js)
│   ├── app/              # 应用页面
│   ├── components/       # React 组件
│   ├── lib/              # 工具函数
│   └── contexts/         # React Context
│
├── package.json          # 前端依赖
└── README.md            # 项目说明
```

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/NissonCX/EduGenius.git
cd EduGenius
```

### 2. 安装前端依赖

```bash
npm install
```

### 3. 安装后端依赖

```bash
cd api
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cd api
cp .env.example .env
# 编辑 .env 文件，填入必需的 API 密钥
```

### 5. 初始化数据库

```bash
cd api
python3 init_db.py
```

### 6. 运行数据库迁移（重要！）

```bash
cd api/migrations

# 添加 refresh_token 列
python3 add_refresh_token.py

# 添加 subsection_number 列
python3 add_subsection_to_questions.py
```

### 7. 启动服务

**终端 1 - 启动后端:**
```bash
cd api
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**终端 2 - 启动前端:**
```bash
npm run dev
```

### 8. 访问应用

- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

---

## 详细配置

### 数据库配置

#### 数据库迁移脚本

项目包含多个迁移脚本来修复数据库结构问题：

```bash
cd api/migrations

# 1. 添加 refresh_token 列（用户登录必需）
python3 add_refresh_token.py

# 2. 添加 subsection_number 列（题目管理必需）
python3 add_subsection_to_questions.py

# 3. 添加索引（性能优化）
python3 add_indexes.py
```

#### 手动 SQL 迁移（备选方案）

如果迁移脚本无法运行，可以手动执行 SQL：

```bash
cd api
sqlite3 edugenius.db

# 添加 refresh_token 列
ALTER TABLE users ADD COLUMN refresh_token VARCHAR;

# 添加 subsection_number 列
ALTER TABLE questions ADD COLUMN subsection_number INTEGER;

# 验证更改
PRAGMA table_info(users);
PRAGMA table_info(questions);
```

### API 密钥配置

#### 1. 获取通义千问 API 密钥

1. 访问 [阿里云百炼平台](https://dashscope.console.aliyun.com/apiKey)
2. 创建 API Key
3. 复制密钥

#### 2. 配置环境变量

编辑 `api/.env` 文件：

```bash
# 必需配置
DASHSCOPE_API_KEY=sk-your-actual-api-key-here

# 生产环境必须更改
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
```

#### 3. 验证配置

```bash
cd api
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('DashScope API Key:', os.getenv('DASHSCOPE_API_KEY', 'NOT SET')[:20] + '...')
print('JWT Secret:', 'SET' if os.getenv('JWT_SECRET_KEY') else 'NOT SET')
"
```

---

## 启动服务

### 方式 1: 手动启动（推荐开发环境）

**后端:**
```bash
cd api
source venv/bin/activate  # 激活虚拟环境
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**前端:**
```bash
npm run dev
```

### 方式 2: 使用启动脚本

**后端:**
```bash
cd api
bash start_server.sh  # 后台运行
```

**前端:**
```bash
npm run dev
```

### 验证服务状态

```bash
# 检查后端
curl http://localhost:8000/health

# 检查前端
curl http://localhost:3000

# 查看 API 文档
open http://localhost:8000/docs
```

---

## 常见问题

### 问题 1: 数据库错误 "no such column"

**错误信息:**
```
sqlite3.OperationalError: no such column: users.refresh_token
```

**解决方案:**
```bash
cd api/migrations
python3 add_refresh_token.py
```

### 问题 2: 前端构建错误 "Export fetchCompetencyData doesn't exist"

**解决方案:** 这个问题已修复，确保你使用的是最新代码。

### 问题 3: 登录失败 "邮箱或密码错误"

**可能原因:**
1. 数据库缺少 `refresh_token` 列
2. 密码验证逻辑问题

**解决方案:**
```bash
cd api/migrations
python3 add_refresh_token.py

# 或注册新用户测试
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@test.com",
    "username": "testuser",
    "password": "Test1234",
    "preferred_teaching_style": 3
  }'
```

### 问题 4: 获取历史对话失败 (500 错误)

**错误信息:**
```
no such column: questions.subsection_number
```

**解决方案:**
```bash
cd api/migrations
python3 add_subsection_to_questions.py
```

### 问题 5: Python 依赖安装失败

**问题:** PaddleOCR 安装错误

**解决方案:**
```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或单独安装问题包
pip install paddlepaddle==2.6.2 -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install paddleocr==2.7.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 6: 前端端口被占用

**错误信息:**
```
Port 3000 is already in use
```

**解决方案:**
```bash
# 查找占用端口的进程
lsof -ti:3000 | xargs kill -9

# 或使用其他端口
npm run dev -- -p 3001
```

### 问题 7: CORS 错误

**错误信息:**
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS
```

**解决方案:** 检查 `api/.env` 文件中的 `ALLOWED_ORIGINS` 配置：
```bash
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3001
```

---

## 开发建议

### 推荐的开发工具

- **IDE**: VSCode + Python Extension
- **API 测试**: Postman 或 httpie
- **数据库管理**: DB Browser for SQLite
- **日志查看**: tail -f

### 有用的命令

```bash
# 查看后端日志
tail -f backend.log

# 查看数据库内容
sqlite3 api/edugenius.db "SELECT * FROM users;"

# 重置数据库
rm api/edugenius.db
cd api && python3 init_db.py

# 运行测试
cd api && pytest

# 代码格式化
cd api && black app/
```

---

## 生产部署

### 环境变量检查清单

生产环境部署前，确保：

- [ ] 修改 `JWT_SECRET_KEY` 为强随机密钥
- [ ] 配置真实的 `DASHSCOPE_API_KEY`
- [ ] 设置 `DEBUG=False`
- [ ] 配置正确的 `ALLOWED_ORIGINS`
- [ ] 设置数据库备份策略
- [ ] 配置日志监控

### 部署命令示例

```bash
# 后端 (使用 gunicorn)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 前端 (构建)
npm run build
npm start
```

---

## 获取帮助

- 查看项目 README.md
- 查看 DEBUGGING_GUIDE.md
- 查看 DEPLOYMENT_GUIDE.md
- 提交 Issue: https://github.com/NissonCX/EduGenius/issues

---

**最后更新:** 2026-02-04
**文档版本:** 1.0
