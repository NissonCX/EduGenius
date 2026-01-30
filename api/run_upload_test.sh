#!/bin/bash
cd /Users/nissoncx/code/EduGenius/api

TOKEN=$(curl -s -X POST 'http://localhost:8000/api/users/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'username=testuser2' \
  --data-urlencode 'password=Test12345' | jq -r '.access_token')

echo "Token: ${TOKEN:0:20}..."
echo ""

# 选择第一个PDF文件
PDF_FILE=$(ls uploads/*.pdf | head -1)
FILE_NAME=$(basename "$PDF_FILE")

echo "上传文件: $FILE_NAME"
echo ""

# 上传文档
RESULT=$(curl -s -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$PDF_FILE" \
  -F "title=${FILE_NAME%.pdf}")

echo "上传结果: $RESULT" | jq .
DOC_ID=$(echo $RESULT | jq -r '.document_id')
echo ""

if [ "$DOC_ID" != "null" ]; then
    echo "文档ID: $DOC_ID"
    echo ""
    echo "开始轮询处理状态..."
    
    for i in {1..60}; do
        STATUS=$(curl -s "http://localhost:8000/api/documents/$DOC_ID/status" \
          -H "Authorization: Bearer $TOKEN")
        
        PERCENT=$(echo $STATUS | jq -r '.progress_percentage')
        STATE=$(echo $STATUS | jq -r '.status')
        STAGE=$(echo $STATUS | jq -r '.stage')
        MSG=$(echo $STATUS | jq -r '.stage_message')
        
        echo "[$PERCENT%] $STAGE - $MSG"
        
        if [ "$STATE" = "completed" ]; then
            echo ""
            echo "✅ 处理完成!"
            echo $STATUS | jq .
            break
        fi
        
        if [ "$STATE" = "failed" ]; then
            echo ""
            echo "❌ 处理失败"
            echo $STATUS | jq .
            break
        fi
        
        sleep 3
    done
fi
