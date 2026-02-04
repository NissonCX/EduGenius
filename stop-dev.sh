#!/bin/bash

# EduGenius 开发环境停止脚本
# 使用方法: ./stop-dev.sh

echo "🛑 停止 EduGenius 开发服务..."

# 停止后端 (端口 8000)
BACKEND_PID=$(lsof -ti:8000)
if [ -n "$BACKEND_PID" ]; then
    echo "  停止后端 (PID: $BACKEND_PID)..."
    kill $BACKEND_PID
    echo "  ✅ 后端已停止"
else
    echo "  ℹ️  后端未运行"
fi

# 停止前端 (端口 3000)
FRONTEND_PID=$(lsof -ti:3000)
if [ -n "$FRONTEND_PID" ]; then
    echo "  停止前端 (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID
    echo "  ✅ 前端已停止"
else
    echo "  ℹ️  前端未运行"
fi

echo ""
echo "✨ 所有服务已停止"
