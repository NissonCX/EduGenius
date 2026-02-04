#!/bin/bash

# EduGenius 开发环境一键启动脚本
# 使用方法: ./start-dev.sh

set -e  # 遇到错误立即退出

echo "================================"
echo "  EduGenius 开发环境启动"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查必需软件
echo "🔍 检查系统环境..."

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js 未安装${NC}"
    echo "请访问 https://nodejs.org/ 下载安装"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 未安装${NC}"
    echo "请访问 https://www.python.org/ 下载安装"
    exit 1
fi

echo -e "${GREEN}✅ Node.js: $(node --version)${NC}"
echo -e "${GREEN}✅ Python: $(python3 --version)${NC}"
echo ""

# 检查前端依赖
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 安装前端依赖...${NC}"
    npm install
    echo -e "${GREEN}✅ 前端依赖安装完成${NC}"
else
    echo -e "${GREEN}✅ 前端依赖已存在${NC}"
fi

# 检查后端依赖
if [ ! -d "api/venv" ]; then
    echo -e "${YELLOW}📦 安装后端依赖...${NC}"
    cd api
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    cd ..
    echo -e "${GREEN}✅ 后端依赖安装完成${NC}"
else
    echo -e "${GREEN}✅ 后端依赖已存在${NC}"
fi

# 检查环境变量文件
if [ ! -f "api/.env" ]; then
    echo -e "${YELLOW}⚙️  配置环境变量...${NC}"
    cp api/.env.example api/.env
    echo -e "${YELLOW}⚠️  请编辑 api/.env 文件，填入你的 API 密钥${NC}"
    echo -e "${YELLOW}   特别是 DASHSCOPE_API_KEY${NC}"
    echo ""
    read -p "按 Enter 继续（确保已配置 .env 文件）..."
fi

# 检查数据库
if [ ! -f "api/edugenius.db" ]; then
    echo -e "${YELLOW}🗄️  初始化数据库...${NC}"
    cd api
    source venv/bin/activate
    python3 init_db.py
    deactivate
    cd ..
    echo -e "${GREEN}✅ 数据库初始化完成${NC}"
else
    echo -e "${GREEN}✅ 数据库已存在${NC}"
fi

# 执行数据库迁移
echo -e "${YELLOW}🔄 执行数据库迁移...${NC}"
cd api
source venv/bin/activate

# 检查是否需要迁移
python3 -c "
import sqlite3
conn = sqlite3.connect('edugenius.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(users)')
cols = [col[1] for col in cursor.fetchall()]
conn.close()

needs_migration = 'refresh_token' not in cols
print('NEEDS_REFRESH_TOKEN' if needs_migration else 'OK')
" > /tmp/migration_check.txt

MIGRATION_STATUS=$(cat /tmp/migration_check.txt | grep -E 'NEEDS_REFRESH_TOKEN|OK')

if echo "$MIGRATION_STATUS" | grep -q "NEEDS_REFRESH_TOKEN"; then
    echo -e "${YELLOW}   添加 refresh_token 列...${NC}"
    python3 migrations/add_refresh_token.py
fi

python3 -c "
import sqlite3
conn = sqlite3.connect('edugenius.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(questions)')
cols = [col[1] for col in cursor.fetchall()]
conn.close()

needs_migration = 'subsection_number' not in cols
print('NEEDS_SUBSECTION' if needs_migration else 'OK')
" > /tmp/migration_check.txt

MIGRATION_STATUS=$(cat /tmp/migration_check.txt | grep -E 'NEEDS_SUBSECTION|OK')

if echo "$MIGRATION_STATUS" | grep -q "NEEDS_SUBSECTION"; then
    echo -e "${YELLOW}   添加 subsection_number 列...${NC}"
    python3 migrations/add_subsection_to_questions.py
fi

deactivate
cd ..
echo -e "${GREEN}✅ 数据库迁移完成${NC}"
rm -f /tmp/migration_check.txt
echo ""

# 检查端口占用
check_port() {
    local port=$1
    if lsof -ti:$port > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  端口 $port 已被占用${NC}"
        read -p "是否停止占用端口的进程? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            lsof -ti:$port | xargs kill -9
            echo -e "${GREEN}✅ 已释放端口 $port${NC}"
        else
            return 1
        fi
    fi
    return 0
}

# 启动后端
echo ""
echo "================================"
echo "  启动服务"
echo "================================"
echo ""

if ! check_port 8000; then
    echo -e "${RED}❌ 无法启动后端（端口 8000 被占用）${NC}"
    echo "请手动停止占用端口的进程后重试"
    exit 1
fi

echo -e "${GREEN}🚀 启动后端服务...${NC}"
cd api
source venv/bin/activate
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
deactivate
cd ..

# 等待后端启动
sleep 3

# 检查后端是否启动成功
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ 后端启动成功 (PID: $BACKEND_PID)${NC}"
    echo -e "   API: http://localhost:8000"
    echo -e "   文档: http://localhost:8000/docs"
else
    echo -e "${RED}❌ 后端启动失败${NC}"
    echo "查看日志: tail -f backend.log"
    exit 1
fi

# 启动前端
if ! check_port 3000; then
    echo -e "${RED}❌ 无法启动前端（端口 3000 被占用）${NC}"
    echo "请手动停止占用端口的进程后重试"
    exit 1
fi

echo -e "${GREEN}🚀 启动前端服务...${NC}"
nohup npm run dev > /dev/null 2>&1 &
FRONTEND_PID=$!

# 等待前端启动
sleep 3

echo ""
echo "================================"
echo -e "${GREEN}  ✨ 所有服务启动成功！${NC}"
echo "================================"
echo ""
echo "服务地址:"
echo -e "  前端: ${GREEN}http://localhost:3000${NC}"
echo -e "  后端: ${GREEN}http://localhost:8000${NC}"
echo -e "  API 文档: ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo "日志查看:"
echo -e "  后端日志: ${YELLOW}tail -f backend.log${NC}"
echo ""
echo "停止服务:"
echo -e "  ${YELLOW}kill $BACKEND_PID $FRONTEND_PID${NC}"
echo -e "  或运行: ${YELLOW}./stop-dev.sh${NC}"
echo ""
echo "测试账号 (请先注册):"
echo -e "  邮箱: ${YELLOW}test@test.com${NC}"
echo -e "  密码: ${YELLOW}Test1234${NC}"
echo ""
echo "================================"
