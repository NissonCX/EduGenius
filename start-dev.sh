#!/bin/bash
# 启动 EduGenius 后端和前端

echo "🚀 启动 EduGenius 开发环境"
echo "================================"

# 清理可能存在的进程
echo "🧹 清理旧进程..."
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 2

# 进入 api 目录并启动后端
echo "📡 启动后端服务器..."
cd "$(dirname "$0")/api" || exit 1
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID"
echo "   后端地址: http://localhost:8000"

# 等待后端启动
sleep 3

# 检查后端是否启动成功
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "   ✅ 后端启动成功！"
else
    echo "   ⚠️  后端启动中，请稍候..."
fi

# 启动前端
echo ""
echo "🎨 启动前端服务器..."
cd "$(dirname "$0")"
npm run dev &
FRONTEND_PID=$!
echo "   前端 PID: $FRONTEND_PID"
echo "   前端地址: http://localhost:3000"

echo ""
echo "================================"
echo "✅ EduGenius 开发环境已启动！"
echo ""
echo "📱 前端: http://localhost:3000"
echo "🔌 后端: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo "================================"

# 保存 PID 以便后续清理
echo $BACKEND_PID > /tmp/edugenius_backend.pid
echo $FRONTEND_PID > /tmp/edugenius_frontend.pid

# 等待用户中断
wait
