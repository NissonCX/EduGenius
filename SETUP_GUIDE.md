# EduGenius 安装指南

本指南提供了详细的安装和配置步骤，帮助你快速搭建 EduGenius 开发环境。

## 📋 目录

- [系统要求](#系统要求)
- [安装前准备](#安装前准备)
- [方式一：快速安装](#方式一快速安装)
- [方式二：手动安装](#方式二手动安装)
- [环境变量配置](#环境变量配置)
- [数据库初始化](#数据库初始化)
- [验证安装](#验证安装)
- [常见问题](#常见问题)

---

## 系统要求

### 必需软件

| 软件 | 最低版本 | 推荐版本 | 检查命令 |
|------|---------|---------|---------|
| Node.js | 18.0+ | 20.x LTS | `node --version` |
| npm | 9.0+ | 10.x | `npm --version` |
| Python | 3.10+ | 3.11+ | `python3 --version` |
| Git | 2.0+ | 最新版 | `git --version` |

### 可选软件

- **Redis** (推荐): 用于缓存，提升性能
- **PostgreSQL** (可选): 生产环境建议使用，开发环境可用 SQLite

### 系统要求

- **操作系统**: macOS, Linux, Windows (WSL2)
- **内存**: 最低 4GB，推荐 8GB+
- **磁盘空间**: 最低 2GB 可用空间

---

## 安装前准备

### 1. 检查系统环境

```bash
# 检查 Node.js 版本
node --version
# 如果版本过低，访问 https://nodejs.org/ 下载最新 LTS 版本

# 检查 Python 版本
python3 --version
# 如果版本过低或未安装，访问 https://www.python.org/downloads/

# 检查 npm 版本
npm --version

# 检查 Git
git --version
```

### 2. 获取 API 密钥

EduGenius 需要通义千问 (DashScope) API 密钥才能运行：

1. 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
2. 注册/登录阿里云账号
3. 创建 API Key
4. 保存 API Key，稍后配置时需要

**⚠️ 注意**: API Key 是收费服务的，请确认账户有足够的额度。

### 3. 克隆项目

```bash
# 克隆仓库
git clone https://github.com/NissonCX/EduGenius.git
cd EduGenius
```

---

## 方式一：快速安装

适合首次安装的用户，自动化完成大部分配置。

### 步骤 1: 运行安装脚本

```bash
# 赋予脚本执行权限
chmod +x install.sh

# 运行安装脚本
./install.sh
```

安装脚本会自动：
- ✅ 检查系统环境（Node.js, Python, Git）
- ✅ 安装前端依赖
- ✅ 创建 Python 虚拟环境
- ✅ 安装后端依赖
- ✅ 创建环境变量配置文件
- ⚠️  **提示你手动配置 API Key**

### 步骤 2: 配置环境变量

```bash
# 编辑后端环境变量
cd api
cp .env.example .env
nano .env  # 或使用你喜欢的编辑器
```

**必须配置的变量：**
```bash
# 必须配置！
DASHSCOPE_API_KEY=your_actual_api_key_here

# 必须配置！生产环境使用强随机密钥
JWT_SECRET_KEY=your_super_secret_key_change_in_production
```

**可选配置：**
```bash
# Redis 缓存（推荐）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=true

# 其他配置使用默认值即可
```

### 步骤 3: 配置前端环境变量

```bash
# 回到项目根目录
cd ..

# 创建前端环境变量
cp .env.local.example .env.local
```

`.env.local` 通常使用默认配置即可：
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAX_FILE_SIZE=52428800
NEXT_PUBLIC_TOKEN_EXPIRE_MINUTES=120
```

### 步骤 4: 初始化数据库

```bash
cd api
python3 init_db.py
```

### 步骤 5: 执行数据库迁移

```bash
cd migrations
python3 add_refresh_token.py
python3 add_subsection_to_questions.py
```

详细的迁移说明请参考 [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

### 步骤 6: 启动服务

```bash
# 回到项目根目录
cd ../..

# 启动所有服务
./start-dev.sh
```

服务将在以下地址启动：
- 🌐 前端: http://localhost:3000
- 🔌 后端: http://localhost:8000
- 📚 API 文档: http://localhost:8000/docs

---

## 方式二：手动安装

适合需要自定义配置的用户。

### 步骤 1: 安装前端依赖

```bash
# 在项目根目录
npm install
```

如果遇到网络问题，可以使用国内镜像：
```bash
npm install --registry=https://registry.npmmirror.com
```

### 步骤 2: 设置 Python 虚拟环境

```bash
# 进入 api 目录
cd api

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 升级 pip
pip install --upgrade pip
```

### 步骤 3: 安装后端依赖

```bash
# 确保虚拟环境已激活
# (提示符应该显示 (venv))

# 安装依赖
pip install -r requirements.txt
```

如果遇到 PaddlePaddle 安装问题，请参考 [常见问题](#paddleocr-安装问题)。

### 步骤 4: 配置环境变量

按照 [方式一](#方式一快速安装) 中的步骤 2 和 3 配置环境变量。

### 步骤 5: 初始化数据库

按照 [方式一](#方式一快速安装) 中的步骤 4 和 5 初始化数据库。

### 步骤 6: 手动启动服务

**启动后端：**
```bash
# 在 api 目录，确保虚拟环境已激活
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**启动前端（新开终端）：**
```bash
# 在项目根目录
npm run dev
```

---

## 环境变量配置

### 后端环境变量 (api/.env)

完整的环境变量说明请参考 `api/.env.example`。

**必需配置：**
```bash
# 通义千问 API 密钥
DASHSCOPE_API_KEY=sk-your-actual-key-here

# JWT 密钥（至少 32 字符）
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-min-32-chars
```

**推荐配置：**
```bash
# Redis 缓存
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=true

# 日志级别
LOG_LEVEL=INFO

# CORS 配置
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**可选配置：**
```bash
# 数据库
DATABASE_URL=sqlite+aiosqlite:///./edugenius.db

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db

# 文件上传
MAX_FILE_SIZE_MB=50

# OCR 配置
OCR_TEXT_RATIO_THRESHOLD=0.1
OCR_CONFIDENCE_THRESHOLD=0.6
OCR_MAX_CONCURRENT=2
```

### 前端环境变量 (.env.local)

```bash
# API 地址
NEXT_PUBLIC_API_URL=http://localhost:8000

# 文件上传大小限制（字节）
NEXT_PUBLIC_MAX_FILE_SIZE=52428800

# Token 有效期（分钟）
NEXT_PUBLIC_TOKEN_EXPIRE_MINUTES=120
```

---

## 数据库初始化

### SQLite 数据库

EduGenius 默认使用 SQLite 数据库，无需额外安装。

**初始化数据库：**
```bash
cd api
python3 init_db.py
```

这将创建 `api/edugenius.db` 文件并初始化表结构。

### 数据库迁移

数据库迁移是必要的步骤，用于添加新字段和修复数据结构。

**执行迁移：**
```bash
cd api/migrations
python3 add_refresh_token.py
python3 add_subsection_to_questions.py
```

详细的迁移说明请参考 [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)。

### Redis（可选）

如果使用 Redis 缓存：

**安装 Redis：**
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis

# Windows
# 下载 Redis for Windows 或使用 WSL2
```

**测试连接：**
```bash
redis-cli ping
# 应该返回: PONG
```

---

## 验证安装

### 1. 检查后端服务

```bash
# 访问健康检查端点
curl http://localhost:8000/health

# 应该返回: {"status":"healthy"}
```

### 2. 访问 API 文档

打开浏览器访问: http://localhost:8000/docs

你应该看到 FastAPI 自动生成的 Swagger 文档。

### 3. 检查前端服务

打开浏览器访问: http://localhost:3000

你应该看到 EduGenius 的登录/注册页面。

### 4. 测试用户注册

1. 访问 http://localhost:3000/register
2. 填写注册信息
3. 提交表单
4. 如果成功跳转到首页，说明安装完成

### 5. 测试 API 连接

在前端登录后，尝试上传一个 PDF 文档，如果上传成功且能识别章节，说明一切正常。

---

## 常见问题

### Node.js 版本过低

**问题**: `node --version` 显示版本低于 18.0

**解决方案**:
```bash
# 使用 nvm 安装最新版本
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc  # 或 source ~/.zshrc
nvm install --lts
nvm use --lts
```

### Python 版本过低

**问题**: `python3 --version` 显示版本低于 3.10

**解决方案**:

**macOS** (使用 Homebrew):
```bash
brew install python@3.11
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv
```

**Windows**: 从 [python.org](https://www.python.org/downloads/) 下载安装

### PaddleOCR 安装问题

**问题**: `pip install paddleocr` 失败或报错

**解决方案**:

1. **先安装 PaddlePaddle**:
```bash
# CPU 版本
pip install paddlepaddle==2.6.2

# GPU 版本（如果有 CUDA）
pip install paddlepaddle-gpu==2.6.2
```

2. **再安装 PaddleOCR**:
```bash
pip install paddleocr==2.7.0
```

3. **如果仍然失败，尝试降级 numpy**:
```bash
pip install "numpy<2.0"
```

### 虚拟环境激活失败

**问题**: `source venv/bin/activate` 报错

**解决方案**:
```bash
# 删除旧的虚拟环境
rm -rf venv

# 重新创建
python3 -m venv venv

# 再次激活
source venv/bin/activate
```

### API 密钥无效

**问题**: 启动后提示 "Invalid API Key" 或认证失败

**解决方案**:
1. 检查 `DASHSCOPE_API_KEY` 是否正确
2. 确认 API Key 账户有足够额度
3. 访问 [阿里云控制台](https://bailian.console.aliyun.com/) 验证 Key

### 端口被占用

**问题**: `Error: listen EADDRINUSE: address already in use :::3000`

**解决方案**:
```bash
# 查找占用端口的进程
lsof -ti:3000

# 终止进程
kill -9 $(lsof -ti:3000)

# 或使用 stop-dev.sh
./stop-dev.sh
```

### 数据库迁移失败

**问题**: 执行迁移脚本时报错

**解决方案**:
1. 检查虚拟环境是否激活
2. 确保在 `api/` 目录下执行
3. 删除数据库文件重新初始化:
```bash
cd api
rm edugenius.db
python3 init_db.py
cd migrations
python3 add_refresh_token.py
```

详见 [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

### OCR 内存不足

**问题**: 上传 PDF 时后端崩溃或变慢

**解决方案**:
调整 `api/.env` 中的 OCR 并发限制：
```bash
OCR_MAX_CONCURRENT=1  # 降低并发数
```

### 前端无法连接后端

**问题**: 前端页面报错 "Failed to fetch"

**解决方案**:
1. 确认后端已启动: `curl http://localhost:8000/health`
2. 检查 `.env.local` 中的 `NEXT_PUBLIC_API_URL`
3. 检查浏览器控制台的网络请求
4. 确认 CORS 配置正确

---

## 下一步

安装完成后，你可以：

1. **阅读开发文档**: 查看 [CLAUDE.md](CLAUDE.md) 了解项目架构
2. **查看 API 文档**: 访问 http://localhost:8000/docs
3. **开始开发**: 参考 [README.md](README.md) 中的开发指南

## 获取帮助

如果遇到问题：

1. 查看 [常见问题](#常见问题) 部分
2. 查阅 [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md)
3. 在 GitHub 上提 Issue: https://github.com/NissonCX/EduGenius/issues

---

**祝使用愉快！** 🎉
