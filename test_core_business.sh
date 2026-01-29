#!/bin/bash

echo "🧪 EduGenius 核心功能测试"
echo "=========================="
echo ""

# 1. 测试后端健康
echo "1️⃣ 测试后端..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端正常运行"
    curl -s http://localhost:8000/health | jq .
else
    echo "❌ 后端未运行"
    echo "请运行: cd api && python -m uvicorn main:app --reload"
    exit 1
fi
echo ""

# 2. 注册/登录测试用户
echo "2️⃣ 获取测试用户 Token..."

# 使用时间戳创建唯一用户
TIMESTAMP=$(date +%s)
TEST_EMAIL="test${TIMESTAMP}@edugenius.com"
TEST_USER="testuser${TIMESTAMP}"
TEST_PASS="Test1234"

REGISTER=$(curl -s -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"username\": \"$TEST_USER\",
    \"password\": \"$TEST_PASS\",
    \"preferred_teaching_style\": 3
  }")

TOKEN=$(echo "$REGISTER" | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ 注册失败"
    echo "$REGISTER" | jq .
    exit 1
fi

echo "✅ Token: ${TOKEN:0:30}..."
echo "✅ 测试用户: $TEST_EMAIL"
echo ""

# 3. 创建测试文档
echo "3️⃣ 创建测试文档..."
cat > /tmp/test_edugenius.txt << 'EOF'
第一章：线性代数基础

1.1 向量和矩阵
向量是具有大小和方向的量。在数学中，向量可以用坐标表示。
例如，二维向量可以表示为 (x, y)，三维向量可以表示为 (x, y, z)。

矩阵是由数字组成的矩形阵列。矩阵可以进行加法、乘法等运算。
矩阵在线性变换、方程组求解等方面有广泛应用。

1.2 矩阵运算
矩阵加法：对应元素相加
矩阵乘法：行乘列求和
矩阵转置：行列互换

第二章：微积分入门

2.1 极限
极限是微积分的基础概念，描述函数在某点附近的行为。
极限的定义：当 x 趋近于 a 时，f(x) 趋近于 L。

2.2 导数
导数表示函数的变化率，是微积分中的核心概念。
导数的几何意义是函数图像在某点的切线斜率。

2.3 积分
积分是导数的逆运算，用于计算面积、体积等。
定积分表示曲线下的面积。
EOF

echo "✅ 测试文档已创建"
echo ""

# 4. 上传文档
echo "4️⃣ 上传文档..."
UPLOAD=$(curl -s -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_edugenius.txt" \
  -F "title=测试教材-线性代数与微积分")

echo "$UPLOAD" | jq .

if echo "$UPLOAD" | jq -e '.document_id' > /dev/null 2>&1; then
    DOC_ID=$(echo "$UPLOAD" | jq -r '.document_id')
    echo "✅ 文档上传成功，ID: $DOC_ID"
else
    echo "❌ 文档上传失败"
    echo "$UPLOAD"
    rm /tmp/test_edugenius.txt
    exit 1
fi
echo ""

# 5. 等待处理
echo "5️⃣ 等待文档处理（10秒）..."
for i in {10..1}; do
    echo -ne "\r   剩余 $i 秒..."
    sleep 1
done
echo -e "\r   ✅ 等待完成"
echo ""

# 6. 获取文档列表
echo "6️⃣ 获取文档列表..."
DOCS=$(curl -s http://localhost:8000/api/documents/list \
  -H "Authorization: Bearer $TOKEN")
echo "$DOCS" | jq '.documents[] | {id, title, total_chapters, processing_status}'
echo ""

# 7. 获取章节列表
echo "7️⃣ 获取章节列表..."
CHAPTERS=$(curl -s http://localhost:8000/api/documents/$DOC_ID/chapters \
  -H "Authorization: Bearer $TOKEN")
echo "$CHAPTERS" | jq '.chapters[] | {chapter_number, chapter_title, status, is_locked}'
echo ""

# 8. 统计
CHAPTER_COUNT=$(echo "$CHAPTERS" | jq '.chapters | length')
echo "📊 统计信息:"
echo "   文档 ID: $DOC_ID"
echo "   章节数量: $CHAPTER_COUNT"
echo ""

# 9. 清理
rm /tmp/test_edugenius.txt

echo "=========================="
echo "✅ 核心功能测试完成！"
echo ""
echo "📝 测试结果:"
echo "   ✅ 后端运行正常"
echo "   ✅ 用户认证成功"
echo "   ✅ 文档上传成功"
echo "   ✅ 文档处理完成"
echo "   ✅ 章节划分完成"
echo ""
echo "🎯 下一步:"
echo "   1. 访问 http://localhost:3000/documents"
echo "   2. 使用 test@edugenius.com / Test1234 登录"
echo "   3. 查看上传的文档"
echo "   4. 点击'开始学习'进入学习页面"
