#!/bin/bash
# 启动 EduGenius 后端服务器

cd "$(dirname "$0")/api" || exit 1

echo "🚀 启动 EduGenius 后端..."
echo "工作目录: $(pwd)"
echo ""

# 检查端口是否被占用
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  端口 8000 已被占用，正在清理..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 2
fi

# 启动后端
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
