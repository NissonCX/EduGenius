#!/bin/bash
# EduGenius 首次安装脚本
# 此脚本将自动检查环境、安装依赖、初始化数据库

set -e  # 遇到错误时退出

echo "🚀 EduGenius 首次安装向导"
echo "================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查版本是否符合要求
check_version() {
    local version=$1
    local min_version=$2
    local major=$(echo "$version" | cut -d'.' -f1 | sed 's/[^0-9]//g')
    local minor=$(echo "$version" | cut -d'.' -f2 | sed 's/[^0-9]//g')
    local min_major=$(echo "$min_version" | cut -d'.' -f1)
    local min_minor=$(echo "$min_version" | cut -d'.' -f2)

    if [ "$major" -gt "$min_major" ]; then
        return 0
    elif [ "$major" -eq "$min_major" ] && [ "$minor" -ge "$min_minor" ]; then
        return 0
    else
        return 1
    fi
}

# ==================== 步骤 1: 检查系统环境 ====================
print_header "步骤 1/6: 检查系统环境"

check_passed=true

# 检查 Node.js
if command_exists node; then
    NODE_VERSION=$(node --version)
    print_success "Node.js 已安装: $NODE_VERSION"

    NODE_MAJOR=$(node --version | cut -d'.' -f1 | sed 's/v//')
    if [ "$NODE_MAJOR" -lt 18 ]; then
        print_error "Node.js 版本过低，需要 18.0 或更高版本"
        print_info "请访问 https://nodejs.org/ 下载最新 LTS 版本"
        check_passed=false
    fi
else
    print_error "未找到 Node.js"
    print_info "请访问 https://nodejs.org/ 安装 Node.js"
    check_passed=false
fi

# 检查 npm
if command_exists npm; then
    NPM_VERSION=$(npm --version)
    print_success "npm 已安装: $NPM_VERSION"
else
    print_error "未找到 npm"
    check_passed=false
fi

# 检查 Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python 已安装: $PYTHON_VERSION"

    PYTHON_MAJOR=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1)
    PYTHON_MINOR=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f2)
    if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MINOR" -lt 10 ]; then
        print_error "Python 版本过低，需要 3.10 或更高版本"
        print_info "请访问 https://www.python.org/downloads/ 下载最新版本"
        check_passed=false
    fi
else
    print_error "未找到 Python3"
    print_info "请访问 https://www.python.org/downloads/ 安装 Python"
    check_passed=false
fi

# 检查 Git
if command_exists git; then
    GIT_VERSION=$(git --version)
    print_success "Git 已安装: $GIT_VERSION"
else
    print_warning "未找到 Git（可选，用于版本管理）"
fi

if [ "$check_passed" = false ]; then
    print_error "环境检查失败，请安装缺失的依赖后重试"
    exit 1
fi

print_success "环境检查通过！"

# ==================== 步骤 2: 安装前端依赖 ====================
print_header "步骤 2/6: 安装前端依赖"

if [ -d "node_modules" ]; then
    print_warning "检测到已存在的 node_modules 目录"
    read -p "是否重新安装前端依赖？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "正在安装前端依赖..."
        if npm install; then
            print_success "前端依赖安装完成！"
        else
            print_error "前端依赖安装失败"
            print_info "请尝试手动运行: npm install"
            exit 1
        fi
    else
        print_info "跳过前端依赖安装"
    fi
else
    print_info "正在安装前端依赖..."
    if npm install; then
        print_success "前端依赖安装完成！"
    else
        print_error "前端依赖安装失败"
        print_info "请尝试手动运行: npm install"
        exit 1
    fi
fi

# ==================== 步骤 3: 设置 Python 虚拟环境 ====================
print_header "步骤 3/6: 设置 Python 后端环境"

cd api

# 检查虚拟环境
if [ -d "venv" ]; then
    print_warning "检测到已存在的虚拟环境"
    read -p "是否重新创建虚拟环境？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "删除旧的虚拟环境..."
        rm -rf venv
        print_info "创建新的虚拟环境..."
        python3 -m venv venv
        print_success "虚拟环境创建完成！"
    else
        print_info "使用现有虚拟环境"
    fi
else
    print_info "创建 Python 虚拟环境..."
    if python3 -m venv venv; then
        print_success "虚拟环境创建完成！"
    else
        print_error "虚拟环境创建失败"
        exit 1
    fi
fi

# 激活虚拟环境
print_info "激活虚拟环境..."
source venv/bin/activate

# 升级 pip
print_info "升级 pip 到最新版本..."
pip install --upgrade pip --quiet
print_success "pip 已升级"

# 安装后端依赖
print_info "正在安装后端依赖..."
if pip install -r requirements.txt; then
    print_success "后端依赖安装完成！"
else
    print_error "后端依赖安装失败"
    print_info "请尝试手动安装: cd api && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

cd ..

# ==================== 步骤 4: 配置环境变量 ====================
print_header "步骤 4/6: 配置环境变量"

# 配置后端环境变量
print_info "配置后端环境变量..."
cd api

if [ -f ".env" ]; then
    print_warning "检测到已存在的 .env 文件"
    read -p "是否重新配置？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env .env.backup
        print_warning "已备份现有 .env 到 .env.backup"
        rm .env
    else
        print_info "使用现有 .env 配置"
    fi
fi

if [ ! -f ".env" ]; then
    cp .env.example .env
    print_success "已创建 .env 文件（从 .env.example 复制）"

    print_warning "⚠️  你需要编辑 api/.env 文件并配置以下必需的变量："
    echo ""
    echo -e "${RED}必需配置：${NC}"
    echo "  1. DASHSCOPE_API_KEY=your_actual_api_key_here"
    echo "     获取地址: https://bailian.console.aliyun.com/"
    echo ""
    echo "  2. JWT_SECRET_KEY=your_super_secret_key"
    echo "     生成方法: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    echo ""
    echo -e "${YELLOW}推荐配置：${NC}"
    echo "  - REDIS_HOST=localhost"
    echo "  - REDIS_PORT=6379"
    echo "  - REDIS_ENABLED=true"
    echo ""

    read -p "是否现在编辑 .env 文件？(Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        # 尝试检测可用的编辑器
        if command_exists nano; then
            nano .env
        elif command_exists vim; then
            vim .env
        elif command_exists vi; then
            vi .env
        else
            print_warning "未找到编辑器，请手动编辑 api/.env 文件"
        fi
    fi

    # 验证配置
    source .env 2>/dev/null || true

    if [ -z "$DASHSCOPE_API_KEY" ] || [ "$DASHSCOPE_API_KEY" = "your-dashscope-api-key-here" ]; then
        print_error "DASHSCOPE_API_KEY 未配置或使用默认值"
        print_info "请编辑 api/.env 文件，设置有效的 API Key"
        print_info "获取地址: https://bailian.console.aliyun.com/"
        echo ""
        read -p "是否继续安装？(稍后配置): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "后端环境变量配置完成！"
    fi
else
    # 验证现有配置
    source .env 2>/dev/null || true
    if [ -n "$DASHSCOPE_API_KEY" ] && [ "$DASHSCOPE_API_KEY" != "your-dashscope-api-key-here" ]; then
        print_success "后端环境变量配置正常！"
    else
        print_warning "请确保已正确配置 api/.env 中的 DASHSCOPE_API_KEY"
    fi
fi

cd ..

# 配置前端环境变量
print_info "配置前端环境变量..."

if [ ! -f ".env.local" ]; then
    cp .env.local.example .env.local
    print_success "已创建 .env.local 文件（使用默认配置）"

    print_info "前端环境变量："
    echo "  - NEXT_PUBLIC_API_URL=http://localhost:8000"
    echo "  - NEXT_PUBLIC_MAX_FILE_SIZE=52428800"
    echo "  - NEXT_PUBLIC_TOKEN_EXPIRE_MINUTES=120"
    echo ""
    echo "通常使用默认配置即可，无需修改"
else
    print_success "前端环境变量已存在！"
fi

# ==================== 步骤 5: 初始化数据库 ====================
print_header "步骤 5/6: 初始化数据库"

cd api

if [ -f "edugenius.db" ]; then
    print_warning "检测到已存在的数据库文件"
    read -p "是否重新初始化数据库？这将清除所有数据！(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp edugenius.db edugenius.db.backup
        print_warning "已备份数据库到 edugenius.db.backup"
        rm edugenius.db
        print_info "正在初始化数据库..."
        if python3 init_db.py; then
            print_success "数据库初始化完成！"
        else
            print_error "数据库初始化失败"
            exit 1
        fi
    else
        print_info "跳过数据库初始化"
    fi
else
    print_info "正在初始化数据库..."
    if python3 init_db.py; then
        print_success "数据库初始化完成！"
    else
        print_error "数据库初始化失败"
        exit 1
    fi
fi

# 执行数据库迁移
print_info "执行数据库迁移..."
cd migrations

MIGRATION_PASSED=true

# 检查并执行迁移
for migration in add_refresh_token.py add_subsection_to_questions.py; do
    if [ -f "$migration" ]; then
        print_info "执行迁移: $migration"
        if python3 "$migration"; then
            print_success "迁移完成: $migration"
        else
            print_error "迁移失败: $migration"
            MIGRATION_PASSED=false
        fi
    else
        print_warning "迁移文件不存在: $migration"
    fi
done

cd ../..

if [ "$MIGRATION_PASSED" = false ]; then
    print_error "部分迁移失败，请查看错误信息"
    print_info "详细说明请参考: MIGRATION_GUIDE.md"
    exit 1
fi

print_success "数据库迁移完成！"

# ==================== 步骤 6: 安装完成 ====================
print_header "步骤 6/6: 安装完成"

echo ""
print_success "🎉 EduGenius 安装完成！"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "下一步操作："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. 确保 api/.env 中的环境变量已正确配置"
echo "   特别是 DASHSCOPE_API_KEY"
echo ""
echo "2. 启动服务："
echo "   ./start-dev.sh"
echo ""
echo "3. 访问应用："
echo "   前端: http://localhost:3000"
echo "   后端: http://localhost:8000"
echo "   API 文档: http://localhost:8000/docs"
echo ""
echo "4. 注册账户并开始使用"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "如有问题，请查看："
echo "  - SETUP_GUIDE.md（安装指南）"
echo "  - MIGRATION_GUIDE.md（迁移指南）"
echo "  - README.md（项目文档）"
echo ""

# 可选：立即启动
read -p "是否现在启动服务？(Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    print_info "正在启动服务..."
    ./start-dev.sh
else
    print_info "稍后可以使用 ./start-dev.sh 启动服务"
fi
