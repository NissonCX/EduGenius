#!/bin/bash

# 测试脚本：验证文档上传功能

echo "=== EduGenius 文档上传测试 ==="
echo ""

# 1. 测试后端健康检查
echo "1. 测试后端健康检查..."
curl -s http://localhost:8000/api/documents/health | jq .
echo ""

# 2. 测试用户登录（获取 token）
echo "2. 测试用户登录..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234"
  }')

echo "$LOGIN_RESPONSE" | jq .

# 提取 token
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ 登录失败，无法获取 token"
  echo "请先注册用户或检查登录凭据"
  exit 1
fi

echo "✅ Token: ${TOKEN:0:20}..."
echo ""

# 3. 测试文档列表
echo "3. 测试文档列表..."
curl -s http://localhost:8000/api/documents/list \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

# 4. 测试文档上传（需要实际文件）
echo "4. 测试文档上传..."
echo "创建测试文件..."
echo "这是一个测试文档。" > /tmp/test_upload.txt

UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_upload.txt" \
  -F "title=测试文档")

echo "$UPLOAD_RESPONSE" | jq .

# 清理
rm /tmp/test_upload.txt

echo ""
echo "=== 测试完成 ==="
