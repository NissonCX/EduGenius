#!/bin/bash

echo "🔍 EduGenius 快速诊断"
echo "===================="
echo ""

# 1. 检查后端
echo "1️⃣ 检查后端..."
if curl -s http://localhost:8000/api/documents/health > /dev/null 2>&1; then
    echo "✅ 后端正在运行"
    curl -s http://localhost:8000/api/documents/health | jq .
else
    echo "❌ 后端未运行或无法访问"
    echo "   请运行: cd api && uvicorn main:app --reload"
    exit 1
fi
echo ""

# 2. 检查前端
echo "2️⃣ 检查前端..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端正在运行"
else
    echo "❌ 前端未运行"
    echo "   请运行: npm run dev"
fi
echo ""

# 3. 检查环境变量
echo "3️⃣ 检查环境变量..."
if [ -f ".env.local" ]; then
    echo "✅ .env.local 存在"
    echo "   内容:"
    cat .env.local | grep -v "^#" | grep -v "^$"
else
    echo "⚠️  .env.local 不存在"
    echo "   请创建: cp .env.local.example .env.local"
fi
echo ""

# 4. 检查后端环境变量
echo "4️⃣ 检查后端环境变量..."
if [ -f "api/.env" ]; then
    echo "✅ api/.env 存在"
    echo "   JWT_SECRET_KEY: $(grep JWT_SECRET_KEY api/.env | cut -d'=' -f2 | cut -c1-20)..."
    echo "   DASHSCOPE_API_KEY: $(grep DASHSCOPE_API_KEY api/.env | cut -d'=' -f2 | cut -c1-20)..."
else
    echo "⚠️  api/.env 不存在"
    echo "   请创建: cp api/.env.example api/.env"
fi
echo ""

# 5. 测试用户注册/登录
echo "5️⃣ 测试用户功能..."
echo "   尝试注册测试用户..."
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "Test1234",
    "preferred_teaching_style": 3
  }' 2>&1)

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    echo "✅ 用户注册成功"
elif echo "$REGISTER_RESPONSE" | grep -q "已被使用"; then
    echo "ℹ️  用户已存在，尝试登录..."
    LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/users/login \
      -H "Content-Type: application/json" \
      -d '{
        "email": "test@example.com",
        "password": "Test1234"
      }')
    
    if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
        echo "✅ 用户登录成功"
        TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
        echo "   Token: ${TOKEN:0:30}..."
    else
        echo "❌ 登录失败"
        echo "$LOGIN_RESPONSE" | jq .
    fi
else
    echo "❌ 注册失败"
    echo "$REGISTER_RESPONSE"
fi
echo ""

echo "===================="
echo "诊断完成！"
echo ""
echo "📋 下一步:"
echo "1. 确保后端和前端都在运行"
echo "2. 在浏览器中访问 http://localhost:3000"
echo "3. 使用 test@example.com / Test1234 登录"
echo "4. 尝试上传文件"
echo "5. 打开浏览器控制台查看详细日志"
