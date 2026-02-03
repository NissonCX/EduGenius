# 🚀 EduGenius 部署指南

## 快速开始

本指南将帮助你在 5-10 分钟内完成 EduGenius 的本地部署。

---

## 📋 前置要求

### 系统要求
- **操作系统**: macOS / Linux / Windows (WSL2)
- **Python**: 3.10+
- **Node.js**: 18+
- **内存**: 至少 4GB RAM
- **磁盘**: 至少 2GB 可用空间

### 必需工具
```bash
# 检查 Python 版本
python --version  # 应该 >= 3.10

# 检查 Node.js 版本
node --version    # 应该 >= 18

# 检查 npm 版本
npm --version     # 应该 >= 9
```

---

## 🔧 后端部署

### 1. 创建虚拟环境
```bash
cd api
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

**注意**: 如果遇到 PaddleOCR 相关依赖问题，请确保：
- NumPy 版本 < 2.0（requirements.txt 中已指定）
- PaddlePaddle 版本为 2.6.2
- PaddleOCR 版本为 2.7.0

### 3. 配置环境变量
```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用你喜欢的编辑器
```

**必须配置的变量**:
```bash
# 生成强随机 JWT Secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 将生成的密钥填入 .env
JWT_SECRET_KEY=<生成的密钥>

# 配置 DashScope API Key（必需）
DASHSCOPE_API_KEY=<你的API密钥>

# Token 有效期（可选，默认 120 分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=120
```

### 4. 初始化数据库
```bash
# 创建数据库表
python init_db.py

# 应用数据库迁移
python migrations/add_indexes.py
python migrations/add_subsection_to_questions.py
python migrations/add_refresh_token.py
```

### 5. 启动后端服务
```bash
# 开发模式
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**验证**: 访问 http://localhost:8000/docs 查看 API 文档

---

## 🎨 前端部署

### 1. 安装依赖
```bash
# 回到项目根目录
cd ..

# 安装 npm 包
npm install
```

### 2. 配置环境变量
```bash
# 复制配置文件
cp .env.local.example .env.local

# 编辑 .env.local 文件
nano .env.local
```

**配置内容**:
```bash
# API 地址（开发环境）
NEXT_PUBLIC_API_URL=http://localhost:8000

# 文件上传大小限制（50MB）
NEXT_PUBLIC_MAX_FILE_SIZE=52428800

# Token 有效期（与后端保持一致）
NEXT_PUBLIC_TOKEN_EXPIRE_MINUTES=120
```

### 3. 启动前端服务
```bash
# 开发模式
npm run dev

# 生产模式
npm run build
npm start
```

**验证**: 访问 http://localhost:3000

---

## ✅ 验证部署

### 1. 健康检查
```bash
# 后端健康检查
curl http://localhost:8000/health

# 预期响应
{"status":"healthy","service":"EduGenius API"}
```

### 2. 注册测试账户
1. 访问 http://localhost:3000/register
2. 填写注册信息
3. 选择教学风格（L1-L5）
4. 点击"创建账户"

### 3. 上传测试文档
1. 登录后访问仪表板
2. 点击"上传文档"
3. 选择一个 PDF 文件（建议使用有清晰目录结构的教材）
4. 等待处理完成

### 4. 开始学习
1. 在文档列表中选择上传的文档
2. 选择要学习的章节
3. 开始与 AI 导师对话

---

## 🐳 Docker 部署（推荐）

### 1. 创建 Dockerfile（后端）
```dockerfile
# api/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 创建 Dockerfile（前端）
```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

### 3. 创建 docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - ACCESS_TOKEN_EXPIRE_MINUTES=120
    volumes:
      - ./api/edugenius.db:/app/edugenius.db
      - ./api/chroma_db:/app/chroma_db
    restart: unless-stopped

  frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped
```

### 4. 启动服务
```bash
# 创建 .env 文件
echo "JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" > .env
echo "DASHSCOPE_API_KEY=your-api-key" >> .env

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 🌐 生产环境部署

### 1. 服务器要求
- **CPU**: 2 核心+
- **内存**: 4GB+
- **磁盘**: 20GB+
- **带宽**: 10Mbps+

### 2. 安全配置

#### 后端安全
```bash
# 1. 使用强随机 JWT Secret
JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(64))')

# 2. 配置 HTTPS
# 使用 Nginx 反向代理
sudo apt install nginx certbot python3-certbot-nginx

# 3. 配置防火墙
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### Nginx 配置示例
```nginx
# /etc/nginx/sites-available/edugenius-api
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}

# /etc/nginx/sites-available/edugenius
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 配置 SSL
```bash
# 自动配置 SSL
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

### 4. 进程管理（使用 PM2）
```bash
# 安装 PM2
npm install -g pm2

# 启动后端
cd api
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name edugenius-api

# 启动前端
cd ..
pm2 start npm --name edugenius-web -- start

# 保存配置
pm2 save

# 开机自启
pm2 startup
```

---

## 📊 监控和日志

### 1. 日志配置
```bash
# 后端日志
tail -f api/logs/app.log

# PM2 日志
pm2 logs edugenius-api
pm2 logs edugenius-web
```

### 2. 性能监控
```bash
# 使用 PM2 监控
pm2 monit

# 查看资源使用
pm2 status
```

---

## 🔧 故障排查

### 常见问题

#### 1. 后端无法启动
```bash
# 检查端口占用
lsof -i :8000

# 检查 Python 环境
which python
python --version

# 检查依赖
pip list
```

#### 2. 前端无法连接后端
```bash
# 检查环境变量
cat .env.local

# 检查网络连接
curl http://localhost:8000/health

# 检查 CORS 配置
# 在 api/main.py 中确认 CORS 设置
```

#### 3. 数据库错误
```bash
# 重新初始化数据库
rm api/edugenius.db
python init_db.py

# 检查数据库文件权限
ls -la api/edugenius.db
```

#### 4. 文件上传失败
```bash
# 检查文件大小限制
# 在 .env 中调整 MAX_FILE_SIZE_MB

# 检查磁盘空间
df -h

# 检查临时目录权限
ls -la /tmp
```

#### 5. OCR 识别问题
```bash
# 检查 PaddleOCR 安装
python -c "from paddleocr import PaddleOCR; print('OK')"

# 重新安装 OCR 依赖
pip install --upgrade paddleocr==2.7.0 paddlepaddle==2.6.2
```

---

## 🎯 性能优化

### 1. 数据库优化
```bash
# 使用 PostgreSQL 替代 SQLite（生产环境推荐）
pip install asyncpg

# 更新 DATABASE_URL
DATABASE_URL=postgresql+asyncpg://user:password@localhost/edugenius
```

### 2. 缓存配置
```bash
# 安装 Redis
sudo apt install redis-server

# 启动 Redis
sudo systemctl start redis
sudo systemctl enable redis
```

### 3. CDN 配置
- 使用 Cloudflare 或 AWS CloudFront
- 缓存静态资源
- 启用 Gzip 压缩

---

## 📝 维护建议

### 日常维护
- 每日检查日志
- 每周备份数据库
- 每月更新依赖

### 备份策略
```bash
# 数据库备份
cp api/edugenius.db backups/edugenius_$(date +%Y%m%d).db

# ChromaDB 备份
tar -czf backups/chroma_$(date +%Y%m%d).tar.gz api/chroma_db/

# 自动备份脚本
# 添加到 crontab
0 2 * * * /path/to/backup.sh
```

---

## 🆘 获取帮助

- **文档**: 查看项目 README.md
- **调试**: 参考 DEBUGGING_GUIDE.md
- **问题**: 提交 GitHub Issue

---

## 📚 相关文档

- [README.md](README.md) - 项目概述
- [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) - 调试指南
- [LEARNING_PROGRESS_DESIGN.md](LEARNING_PROGRESS_DESIGN.md) - 学习进度设计
- [QUIZ_BUSINESS_PLAN.md](QUIZ_BUSINESS_PLAN.md) - 测验业务方案

---

**文档版本**: v1.1.0
**更新时间**: 2026-02-03
**适用版本**: EduGenius v1.0.0+
