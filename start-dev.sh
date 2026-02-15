#!/bin/bash
# 启动 EduGenius 后端和前端

set -e  # 遇到错误时退出

echo "🚀 启动 EduGenius 开发环境"
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 打印带颜色的信息
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo "ℹ️  $1"
}

# 检查系统环境
echo "🔍 检查系统环境..."

# 检查 Node.js
if command_exists node; then
    NODE_VERSION=$(node --version)
    print_success "Node.js 已安装: $NODE_VERSION"

    # 检查版本是否符合要求 (>= 18.0)
    NODE_MAJOR=$(node --version | cut -d'.' -f1 | sed 's/v//')
    if [ "$NODE_MAJOR" -lt 18 ]; then
        print_error "Node.js 版本过低，需要 18.0 或更高版本"
        echo "请访问 https://nodejs.org/ 下载最新版本"
        exit 1
    fi
else
    print_error "未找到 Node.js"
    echo "请访问 https://nodejs.org/ 安装 Node.js"
    exit 1
fi

# 检查 npm
if command_exists npm; then
    NPM_VERSION=$(npm --version)
    print_success "npm 已安装: $NPM_VERSION"
else
    print_error "未找到 npm"
    exit 1
fi

# 检查 Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python 已安装: $PYTHON_VERSION"

    # 检查版本是否符合要求 (>= 3.10)
    PYTHON_MAJOR=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1)
    PYTHON_MINOR=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f2)
    if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MINOR" -lt 10 ]; then
        print_error "Python 版本过低，需要 3.10 或更高版本"
        echo "请访问 https://www.python.org/downloads/ 下载最新版本"
        exit 1
    fi
else
    print_error "未找到 Python3"
    echo "请访问 https://www.python.org/downloads/ 安装 Python"
    exit 1
fi

echo ""

# 检查前端依赖
if [ ! -d "node_modules" ]; then
    print_warning "未检测到前端依赖"
    echo "正在安装前端依赖..."
    if ! npm install; then
        print_error "前端依赖安装失败"
        echo "请尝试手动运行: npm install"
        exit 1
    fi
    print_success "前端依赖安装完成"
else
    print_success "前端依赖已就绪"
fi

echo ""

# 检查后端环境和依赖
cd "$(dirname "$0")/api" || exit 1

# 检查虚拟环境
if [ ! -d "venv" ]; then
    print_warning "未检测到 Python 虚拟环境"
    echo "正在创建虚拟环境..."
    if ! python3 -m venv venv; then
        print_error "虚拟环境创建失败"
        echo "请尝试手动创建: cd api && python3 -m venv venv"
        exit 1
    fi
    print_success "虚拟环境创建完成"
fi

# 检查后端依赖
print_info "检查后端依赖..."
if ! source venv/bin/activate && python -c "import fastapi" 2>/dev/null; then
    print_warning "后端依赖未完全安装"
    echo "正在安装后端依赖..."
    source venv/bin/activate
    if ! pip install -r requirements.txt; then
        print_error "后端依赖安装失败"
        echo "请尝试手动安装: cd api && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
    print_success "后端依赖安装完成"
else
    source venv/bin/activate
    print_success "后端依赖已就绪"
fi

echo ""

# 检查环境变量配置
print_info "检查环境变量配置..."

if [ ! -f ".env" ]; then
    print_error "未找到 .env 文件"
    echo ""
    echo "请先配置环境变量："
    echo "  cd api"
    echo "  cp .env.example .env"
    echo "  nano .env  # 或使用你喜欢的编辑器"
    echo ""
    echo "必须配置的变量："
    echo "  - DASHSCOPE_API_KEY (通义千问 API 密钥)"
    echo "  - JWT_SECRET_KEY (JWT 密钥)"
    echo ""
    echo "获取 API Key: https://bailian.console.aliyun.com/"
    exit 1
fi

# 检查必需的环境变量
source .env 2>/dev/null || true

if [ -z "$DASHSCOPE_API_KEY" ] || [ "$DASHSCOPE_API_KEY" = "your-dashscope-api-key-here" ]; then
    print_error "DASHSCOPE_API_KEY 未配置或使用默认值"
    echo "请编辑 api/.env 文件，设置有效的 API Key"
    echo "获取地址: https://bailian.console.aliyun.com/"
    exit 1
fi

if [ -z "$JWT_SECRET_KEY" ] || [ "$JWT_SECRET_KEY" = "your-super-secret-jwt-key-change-in-production-min-32-chars!" ]; then
    print_warning "JWT_SECRET_KEY 使用默认值（不安全）"
    echo "建议在生产环境使用强随机密钥"
    echo "生成方法: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
fi

print_success "环境变量配置检查通过"

echo ""

# 检查数据库
print_info "检查数据库..."

if [ ! -f "edugenius.db" ]; then
    print_warning "未找到数据库文件"
    echo "正在初始化数据库..."
    if ! python3 init_db.py; then
        print_error "数据库初始化失败"
        echo "请尝试手动运行: cd api && python3 init_db.py"
        exit 1
    fi
    print_success "数据库初始化完成"

    echo ""
    print_warning "请确保已执行数据库迁移："
    echo "  cd api/migrations"
    echo "  python3 add_refresh_token.py"
    echo "  python3 add_subsection_to_questions.py"
    echo ""
    echo "详细说明请参考: MIGRATION_GUIDE.md"
else
    print_success "数据库文件存在"
fi

echo ""

# 清理可能存在的进程
echo "🧹 清理旧进程..."
lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 2

# 启动后端
echo "📡 启动后端服务器..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID"
echo "   后端地址: http://localhost:8000"

# 等待后端启动
sleep 5

# 检查后端是否启动成功
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "后端启动成功！"
elif curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    print_success "后端启动成功！"
else
    print_warning "后端可能仍在启动中，请稍候..."
    print_info "如果后端无法访问，请查看日志："
    echo "  - 检查端口 8000 是否被占用"
    echo "  - 查看后端日志输出"
    echo "  - 访问 http://localhost:8000/docs 查看 API 文档"
fi

# 启动前端
echo ""
echo "🎨 启动前端服务器..."
cd "$(dirname "$0")" || exit 1

# 检查前端环境变量
if [ ! -f ".env.local" ]; then
    print_warning "未找到 .env.local"
    echo "正在创建默认配置..."
    cp .env.local.example .env.local
    print_success "已创建 .env.local（使用默认配置）"
fi

npm run dev &
FRONTEND_PID=$!
echo "   前端 PID: $FRONTEND_PID"
echo "   前端地址: http://localhost:3000"

echo ""
echo "================================"
print_success "EduGenius 开发环境已启动！"
echo ""
echo "📱 前端: http://localhost:3000"
echo "🔌 后端: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"
echo "❤️  健康检查: http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo "================================"

# 保存 PID 以便后续清理
echo $BACKEND_PID > /tmp/edugenius_backend.pid
echo $FRONTEND_PID > /tmp/edugenius_frontend.pid

# 等待用户中断
wait
