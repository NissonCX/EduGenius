# EduGenius Docker 部署指南

本指南详细说明如何使用 Docker 和 Docker Compose 部署 EduGenius。

## 📋 目录

- [Docker 部署优势](#docker-部署优势)
- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [生产环境部署](#生产环境部署)
- [开发环境部署](#开发环境部署)
- [配置说明](#配置说明)
- [常用命令](#常用命令)
- [故障排查](#故障排查)
- [性能优化](#性能优化)

---

## Docker 部署优势

使用 Docker 部署 EduGenius 的优势：

- ✅ **环境一致性**：开发、测试、生产环境完全一致
- ✅ **快速部署**：一键启动所有服务（后端、前端、Redis）
- ✅ **依赖隔离**：不会影响主机系统环境
- ✅ **易于扩展**：可以轻松扩展服务实例
- ✅ **版本管理**：可以轻松回滚到任意版本
- ✅ **资源限制**：可以精确控制资源使用

---

## 前置要求

### 必需软件

1. **Docker** (>= 20.10)
   ```bash
   docker --version
   ```

2. **Docker Compose** (>= 2.0)
   ```bash
   docker compose version
   ```

### 安装 Docker

**macOS / Windows**:
- 下载 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- 安装并启动 Docker Desktop

**Linux (Ubuntu/Debian)**:
```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo apt-get install docker-compose-plugin

# 将当前用户添加到 docker 组（可选，避免每次 sudo）
sudo usermod -aG docker $USER
newgrp docker
```

### 验证安装

```bash
docker run hello-world
docker compose version
```

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/NissonCX/EduGenius.git
cd EduGenius
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入必需的 API 密钥
nano .env
```

**必须配置的变量：**
```bash
DASHSCOPE_API_KEY=your_actual_api_key_here
JWT_SECRET_KEY=your_super_secret_key_here
```

### 3. 启动服务

```bash
# 构建并启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 4. 初始化数据库

```bash
# 进入后端容器
docker compose exec backend bash

# 初始化数据库
python init_db.py

# 执行迁移
cd migrations
python add_refresh_token.py
python add_subsection_to_questions.py

# 退出容器
exit
```

### 5. 访问应用

- 🌐 **前端**: http://localhost:3000
- 🔌 **后端**: http://localhost:8000
- 📚 **API 文档**: http://localhost:8000/docs
- ❤️ **健康检查**: http://localhost:8000/health

---

## 生产环境部署

### 架构说明

生产环境使用以下服务：

```
┌─────────────────┐
│   Nginx (可选)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐  ┌─▼─────┐
│ 前端   │  │ 后端   │
│ :3000 │  │ :8000  │
└───────┘  └───┬────┘
              │
         ┌────┴────┐
         │         │
    ┌────▼───┐ ┌──▼────┐
    │ Redis  │ │ SQLite│
    │ :6379  │ │ DB    │
    └────────┘ └───────┘
```

### 部署步骤

#### 1. 构建生产镜像

```bash
# 构建所有服务的镜像
docker compose build

# 只构建特定服务
docker compose build backend
docker compose build frontend
```

#### 2. 启动生产服务

```bash
# 后台启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps
```

#### 3. 数据持久化

生产环境使用 Docker 卷来持久化数据：

```bash
# 查看所有卷
docker volume ls

# 备份卷数据
docker run --rm -v edugenius_chroma_db:/data -v $(pwd):/backup \
  alpine tar czf /backup/chroma_db_backup.tar.gz -C /data .

# 恢复卷数据
docker run --rm -v edugenius_chroma_db:/data -v $(pwd):/backup \
  alpine tar xzf /backup/chroma_db_backup.tar.gz -C /data
```

#### 4. 健康检查

Docker Compose 配置了健康检查：

```bash
# 查看健康状态
docker compose ps

# 查看健康检查日志
docker compose logs backend | grep health
```

#### 5. 日志管理

```bash
# 查看所有服务日志
docker compose logs

# 查看特定服务日志
docker compose logs backend
docker compose logs frontend

# 实时查看日志
docker compose logs -f

# 查看最近 100 行日志
docker compose logs --tail=100
```

---

## 开发环境部署

### 开发环境特点

- **热重载**：代码修改后自动重启
- **调试模式**：详细的调试日志
- **源码挂载**：容器内修改会同步到主机

### 启动开发环境

```bash
# 使用开发配置启动
docker compose -f docker-compose.dev.yml up -d

# 查看日志
docker compose -f docker-compose.dev.yml logs -f backend
```

### 开发工作流

1. **修改代码**
   - 在主机上编辑代码
   - 容器会自动检测到变化并重新加载

2. **查看日志**
   ```bash
   docker compose -f docker-compose.dev.yml logs -f backend
   ```

3. **进入容器调试**
   ```bash
   docker compose -f docker-compose.dev.yml exec backend bash
   ```

4. **重启服务**
   ```bash
   docker compose -f docker-compose.dev.yml restart backend
   ```

---

## 配置说明

### 环境变量配置

环境变量在 `.env` 文件或 `docker-compose.yml` 中配置：

#### 后端环境变量

```yaml
environment:
  # 数据库配置
  - DATABASE_URL=sqlite+aiosqlite:///./edugenius.db

  # Redis 配置
  - REDIS_HOST=redis
  - REDIS_PORT=6379
  - REDIS_ENABLED=true

  # ChromaDB 配置
  - CHROMA_PERSIST_DIR=/app/chroma_db

  # API 密钥
  - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
  - JWT_SECRET_KEY=${JWT_SECRET_KEY}

  # 应用配置
  - DEBUG=False
  - DEFAULT_MODEL=qwen-max
  - FALLBACK_MODEL=qwen-plus

  # CORS 配置
  - ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

  # 日志配置
  - LOG_LEVEL=INFO

  # 文档处理配置
  - MAX_FILE_SIZE_MB=50
  - CHUNK_SIZE=1000
  - CHUNK_OVERLAP=200

  # OCR 配置
  - OCR_TEXT_RATIO_THRESHOLD=0.1
  - OCR_CONFIDENCE_THRESHOLD=0.6
  - OCR_MAX_CONCURRENT=2
```

#### 前端环境变量

```yaml
environment:
  - NEXT_PUBLIC_API_URL=http://localhost:8000
  - NEXT_PUBLIC_MAX_FILE_SIZE=52428800
  - NEXT_PUBLIC_TOKEN_EXPIRE_MINUTES=120
```

### 卷配置

Docker 卷用于数据持久化：

```yaml
volumes:
  # Redis 数据
  redis_data:
    driver: local

  # 后端数据
  backend_data:
    driver: local

  # ChromaDB 向量数据库
  chroma_db:
    driver: local

  # 上传文件
  uploads:
    driver: local

  # 日志文件
  logs:
    driver: local
```

### 网络配置

服务之间通过内部网络通信：

```yaml
networks:
  edugenius-network:
    driver: bridge
```

---

## 常用命令

### 服务管理

```bash
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart backend

# 停止并删除所有服务、网络、卷
docker compose down -v
```

### 构建和重建

```bash
# 构建所有服务
docker compose build

# 重新构建并启动
docker compose up -d --build

# 强制重新构建（不使用缓存）
docker compose build --no-cache
```

### 日志查看

```bash
# 查看所有服务日志
docker compose logs

# 查看特定服务日志
docker compose logs backend

# 实时查看日志
docker compose logs -f

# 查看最近 100 行
docker compose logs --tail=100

# 查看特定时间的日志
docker compose logs --since 1h
```

### 容器操作

```bash
# 进入容器
docker compose exec backend bash
docker compose exec frontend sh

# 在容器中执行命令
docker compose exec backend python init_db.py

# 查看容器资源使用
docker stats

# 查看容器进程
docker compose top
```

### 镜像操作

```bash
# 查看所有镜像
docker images | grep edugenius

# 删除旧镜像
docker image prune -a

# 导出镜像
docker save edugenius-backend:latest -o backend.tar

# 导入镜像
docker load -i backend.tar
```

### 数据库操作

```bash
# 进入后端容器
docker compose exec backend bash

# 初始化数据库
python init_db.py

# 执行迁移
cd migrations
python add_refresh_token.py
python add_subsection_to_questions.py

# 备份数据库
cp edugenius.db edugenius.db.backup

# 查看数据库
sqlite3 edugenius.db
```

---

## 故障排查

### 问题 1: 容器无法启动

**症状**: `docker compose up` 失败

**排查步骤**:

1. 查看详细日志
   ```bash
   docker compose logs backend
   ```

2. 检查端口占用
   ```bash
   lsof -ti:3000
   lsof -ti:8000
   ```

3. 检查环境变量
   ```bash
   docker compose config
   ```

4. 重新构建镜像
   ```bash
   docker compose build --no-cache
   ```

### 问题 2: 后端无法连接 Redis

**症状**: 后端日志显示 "Redis connection failed"

**解决方案**:

1. 检查 Redis 服务状态
   ```bash
   docker compose ps redis
   docker compose logs redis
   ```

2. 测试 Redis 连接
   ```bash
   docker compose exec backend python -c "from app.core.redis_client import redis_client; print(redis_client.ping())"
   ```

3. 检查网络配置
   ```bash
   docker network inspect edugenius_edugenius-network
   ```

### 问题 3: 前端无法连接后端

**症状**: 前端显示 "Failed to fetch"

**解决方案**:

1. 检查后端服务状态
   ```bash
   docker compose ps backend
   docker compose logs backend
   ```

2. 检查 CORS 配置
   ```yaml
   environment:
     - ALLOWED_ORIGINS=http://localhost:3000,http://frontend:3000
   ```

3. 检查前端环境变量
   ```yaml
   environment:
     - NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

### 问题 4: 健康检查失败

**症状**: 容器状态显示 "unhealthy"

**解决方案**:

1. 查看健康检查日志
   ```bash
   docker inspect edugenius-backend | grep -A 10 Health
   ```

2. 手动测试健康检查
   ```bash
   curl http://localhost:8000/health
   ```

3. 检查健康检查配置
   ```yaml
   healthcheck:
     test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
     interval: 30s
     timeout: 10s
     retries: 3
   ```

### 问题 5: 数据卷权限问题

**症状**: 容器无法写入卷

**解决方案**:

1. 检查卷权限
   ```bash
   docker volume inspect edugenius_uploads
   ```

2. 修复权限
   ```bash
   docker compose run --rm backend chown -R appuser:appuser /app/uploads
   ```

3. 使用命名卷而非绑定挂载
   ```yaml
   volumes:
     - uploads:/app/uploads  # 推荐
     # - ./uploads:/app/uploads  # 可能有权限问题
   ```

### 问题 6: 内存不足

**症状**: 容器被 OOM Killer 杀死

**解决方案**:

1. 限制内存使用
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 2G
           reservations:
             memory: 1G
   ```

2. 减少并发数
   ```yaml
   environment:
     - OCR_MAX_CONCURRENT=1
   ```

3. 清理未使用的资源
   ```bash
   docker system prune -a
   ```

---

## 性能优化

### 1. 镜像优化

**多阶段构建**（已配置）：
- 前端使用多阶段构建，最终镜像只包含运行时文件
- 减小镜像大小，提高部署速度

**使用 Alpine 基础镜像**：
```dockerfile
FROM node:20-alpine  # 比 node:20 小得多
```

### 2. 资源限制

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 3. 缓存优化

**Redis 缓存**（已配置）：
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes
```

**构建缓存**：
```bash
# 使用缓存构建
docker compose build

# 清除缓存重新构建
docker compose build --no-cache
```

### 4. 网络优化

**使用自定义网络**（已配置）：
```yaml
networks:
  edugenius-network:
    driver: bridge
```

### 5. 日志轮转

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 6. 数据库优化

**SQLite 优化**：
```bash
# 定期清理数据库
docker compose exec backend python -c "
from app.db.database import engine
import sqlite3
conn = sqlite3.connect('edugenius.db')
conn.execute('VACUUM')
conn.close()
"
```

---

## 生产环境检查清单

部署到生产环境前，请检查：

- [ ] 修改了所有默认密码和密钥
- [ ] 配置了有效的 `DASHSCOPE_API_KEY`
- [ ] 设置了强随机 `JWT_SECRET_KEY`
- [ ] 修改了 `ALLOWED_ORIGINS` 为实际域名
- [ ] 设置了 `DEBUG=False`
- [ ] 配置了适当的日志级别
- [ ] 设置了资源限制
- [ ] 配置了日志轮转
- [ ] 设置了数据卷备份策略
- [ ] 配置了监控和告警
- [ ] 测试了健康检查
- [ ] 配置了反向代理（Nginx）
- [ ] 启用了 HTTPS
- [ ] 配置了防火墙规则

---

## 高级配置

### 使用 Nginx 反向代理

创建 `nginx.conf`:

```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name yourdomain.com;

    # 前端
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后端 API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API 文档
    location /docs {
        proxy_pass http://backend;
        proxy_set_header Host $host;
    }
}
```

添加到 `docker-compose.yml`:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend
    networks:
      - edugenius-network
```

### 使用 PostgreSQL（可选）

修改 `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=edugenius
      - POSTGRES_USER=edugenius
      - POSTGRES_PASSWORD=your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - edugenius-network

  backend:
    environment:
      - DATABASE_URL=postgresql+asyncpg://edugenius:your_password@postgres/edugenius
    depends_on:
      - postgres

volumes:
  postgres_data:
```

### 自动备份

创建 `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份 ChromaDB
docker run --rm \
  -v edugenius_chroma_db:/data \
  -v $(pwd)/$BACKUP_DIR:/backup \
  alpine tar czf /backup/chroma_db_$DATE.tar.gz -C /data .

# 备份数据库
docker compose exec backend \
  sqlite3 edugenius.db ".backup /tmp/backup.db"
docker cp edugenius-backend:/tmp/backup.db \
  $BACKUP_DIR/edugenius_$DATE.db

# 清理 7 天前的备份
find $BACKUP_DIR -mtime +7 -delete
```

添加到 crontab:
```bash
# 每天凌晨 2 点备份
0 2 * * * /path/to/backup.sh
```

---

## 总结

使用 Docker 部署 EduGenius 的优势：

- ✅ 一键启动所有服务
- ✅ 环境隔离，不影响主机
- ✅ 易于扩展和维护
- ✅ 支持开发和生产环境
- ✅ 完整的健康检查和日志管理

如有问题，请参考：
- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [项目 README.md](README.md)
- [安装指南](SETUP_GUIDE.md)
