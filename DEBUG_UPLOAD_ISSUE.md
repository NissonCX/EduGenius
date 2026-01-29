# 🔍 文档上传问题调试指南

## 当前状态
**错误**: 上传失败，错误信息为空对象 `{}`  
**位置**: `src/app/documents/upload/page.tsx:149`

---

## 调试步骤

### 1. 检查后端是否运行

```bash
# 检查后端进程
ps aux | grep uvicorn

# 检查端口占用
lsof -i :8000

# 测试健康检查
curl http://localhost:8000/api/documents/health
```

**预期响应**:
```json
{
  "status": "healthy",
  "service": "EduGenius API"
}
```

---

### 2. 检查前端配置

```bash
# 检查环境变量
cat .env.local

# 应该包含
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

### 3. 检查浏览器控制台

打开浏览器开发者工具（F12），查看：

#### Console 标签
查找以下日志：
```
Upload headers: {...}
Is authenticated: true/false
User: {...}
```

#### Network 标签
1. 找到 `/api/documents/upload` 请求
2. 查看 Request Headers:
   - 是否有 `Authorization: Bearer xxx`
   - 是否有 `Content-Type: multipart/form-data`
3. 查看 Response:
   - Status Code (200, 401, 500?)
   - Response Body

---

### 4. 使用测试脚本

```bash
# 给脚本执行权限
chmod +x test_upload.sh

# 运行测试
./test_upload.sh
```

这个脚本会测试：
1. 后端健康检查
2. 用户登录
3. 文档列表
4. 文档上传

---

### 5. 检查后端日志

```bash
# 查看后端日志
tail -f /tmp/edugenius_backend.log

# 或者查看 uvicorn 输出
# 在运行 uvicorn 的终端查看
```

查找：
- 认证错误
- 文件处理错误
- 数据库错误

---

## 常见问题和解决方案

### 问题 1: 401 Unauthorized

**原因**: Token 无效或未发送

**检查**:
```javascript
// 在浏览器控制台运行
localStorage.getItem('token')
```

**解决**:
1. 重新登录
2. 检查 token 是否过期
3. 检查 `getAuthHeaders` 函数

---

### 问题 2: 403 Forbidden

**原因**: 权限不足

**检查**:
- 用户是否有上传权限
- 文档是否属于当前用户

---

### 问题 3: 500 Internal Server Error

**原因**: 后端处理错误

**检查后端日志**:
```bash
tail -f /tmp/edugenius_backend_error.log
```

**常见原因**:
- 数据库连接失败
- 文件处理失败
- API 密钥未配置

---

### 问题 4: CORS 错误

**错误信息**: `Access to fetch at ... has been blocked by CORS policy`

**解决**:
1. 检查 `api/main.py` 中的 CORS 配置
2. 确保 `ALLOWED_ORIGINS` 包含前端地址

```python
# api/main.py
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 问题 5: 网络错误

**错误信息**: `Failed to fetch` 或 `Network error`

**检查**:
1. 后端是否运行
2. 端口是否正确
3. 防火墙是否阻止

---

## 手动测试上传

### 使用 curl

```bash
# 1. 登录获取 token
TOKEN=$(curl -s -X POST http://localhost:8000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. 创建测试文件
echo "测试内容" > test.txt

# 3. 上传文件
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.txt" \
  -F "title=测试文档" \
  -v

# 4. 清理
rm test.txt
```

---

## 检查清单

- [ ] 后端正在运行 (port 8000)
- [ ] 前端正在运行 (port 3000)
- [ ] 环境变量配置正确
- [ ] 用户已登录
- [ ] Token 存在且有效
- [ ] CORS 配置正确
- [ ] 数据库已初始化
- [ ] API 密钥已配置

---

## 快速修复

### 重启所有服务

```bash
# 1. 停止所有服务
# Ctrl+C 停止前端和后端

# 2. 清理缓存
rm -rf .next
rm -rf api/__pycache__
rm -rf api/app/**/__pycache__

# 3. 重启后端
cd api
source venv/bin/activate
uvicorn main:app --reload

# 4. 重启前端（新终端）
npm run dev

# 5. 清除浏览器缓存
# 在浏览器中按 Ctrl+Shift+R 强制刷新
```

---

## 获取详细错误信息

在 `src/app/documents/upload/page.tsx` 中，我已经添加了详细的错误日志。

上传时查看浏览器控制台，应该看到：
```
Upload headers: { Authorization: "Bearer xxx..." }
Is authenticated: true
User: { id: 1, email: "...", ... }
Upload failed with status: 401 Unauthorized
Error response: { detail: "无法验证凭据" }
```

根据这些信息可以定位问题。

---

## 联系支持

如果以上步骤都无法解决问题，请提供：
1. 浏览器控制台完整日志
2. 后端日志 (`/tmp/edugenius_backend.log`)
3. Network 标签中的请求详情
4. 环境信息（操作系统、浏览器版本等）

---

**文档版本**: v1.0.0  
**更新时间**: 2026-01-29
