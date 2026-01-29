# 🐛 EduGenius Bug 修复优先级清单

## 📊 总览
- **发现总问题数**: 26 个
- **前端问题**: 17 个
- **后端问题**: 9 个
- **代码质量评分**: 72.5/100
- **生产就绪度**: 65%

---

## 🔴 P0 - 立即修复（安全关键）

### 1. JWT Secret 安全漏洞
**文件**: `api/app/core/config.py:18`
```python
# ❌ 当前代码
SECRET_KEY: str = settings.DASHSCOPE_API_KEY

# ✅ 修复方案
SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-random-key-change-in-production")
```
**影响**: Token 可被轻易破解，用户账户可被盗用
**预计时间**: 10 分钟

### 2. 密码复杂度缺失
**文件**: `api/app/api/endpoints/users.py:38-45`
```python
# ✅ 添加验证
import re

def validate_password(password: str) -> bool:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="密码长度至少8位")
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="密码必须包含大写字母")
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=400, detail="密码必须包含小写字母")
    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="密码必须包含数字")
    return True

# 在注册端点调用
validate_password(user_data.password)
```
**预计时间**: 15 分钟

### 3. Token 有效期过长
**文件**: `api/app/core/security.py:25`
```python
# ❌ 当前：7天
expires_delta = timedelta(days=7)

# ✅ 修复：2小时 + refresh token
expires_delta = timedelta(hours=2)
```
**影响**: Token 泄露后风险期过长
**预计时间**: 30 分钟（需实现 refresh token 机制）

### 4. 硬编码 API 地址
**文件**: `src/app/mistakes/page.tsx:71`, `src/components/quiz/Quiz.tsx:123`
```typescript
// ❌ 当前
const response = await fetch('http://localhost:8000/api/mistakes')

// ✅ 修复
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const response = await fetch(`${API_BASE}/api/mistakes`)
```
**影响**: 无法部署到生产环境
**预计时间**: 20 分钟

### 5. XSS 漏洞
**文件**: `src/components/chat/ChatMessage.tsx:48`
```typescript
// ✅ 安装 DOMPurify
// npm install dompurify
// npm install @types/dompurify

import DOMPurify from 'dompurify'

// 在渲染用户输入前清理
const sanitizedContent = DOMPurify.sanitize(message.content)
<ReactMarkdown>{sanitizedContent}</ReactMarkdown>
```
**影响**: 脚本注入攻击风险
**预计时间**: 15 分钟

---

## 🟠 P1 - 高优先级（功能稳定性）

### 6. 移除硬编码 API 地址（补充）
**需要创建配置文件**
```typescript
// src/lib/config.ts
export const config = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  maxFileSize: 50 * 1024 * 1024, // 50MB
  tokenExpireMinutes: 120
}

// 创建 .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```
**预计时间**: 10 分钟

### 7. 统一错误处理
**文件**: `src/lib/errors.ts`
```typescript
// ✅ 扩展现有的 safeFetch
export async function safeFetch(
  url: string,
  options?: RequestInit
): Promise<Response> {
  try {
    const response = await fetch(url, options)
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || error.message || '请求失败')
    }
    return response
  } catch (error) {
    console.error('API Error:', error)
    throw error
  }
}
```
**预计时间**: 30 分钟

### 8. 文件上传大小限制
**文件**: `api/app/api/endpoints/documents.py:39`
```python
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    ...
):
    # ✅ 添加大小检查
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大，最大支持 {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    # 重置文件指针
    await file.seek(0)
```
**预计时间**: 10 分钟

### 9. 内存泄漏 - 定时器清理
**文件**: `src/components/quiz/Quiz.tsx:45-50`
```typescript
useEffect(() => {
  const timer = setInterval(() => {
    setTimeSpent(prev => prev + 1)
  }, 1000)

  // ✅ 添加清理函数
  return () => clearInterval(timer)
}, [])
```
**预计时间**: 5 分钟

### 10. 实现结构化日志
**文件**: `api/app/core/logging.py` (新建)
```python
import logging
import sys
from datetime import datetime

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/tmp/edugenius_backend.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

# 在所有服务中使用
logger = setup_logging()
logger.info("文档上传成功")
```
**预计时间**: 1 小时

---

## 🟡 P2 - 中优先级（代码质量）

### 11. N+1 查询问题
**文件**: `api/app/api/endpoints/documents.py:243-249`
```python
# ❌ 当前：每个章节单独查询
for progress in all_progress:
    prev_progress = await db.execute(...)

# ✅ 修复：一次查询获取所有数据
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(Progress)
    .options(selectinload(Progress.document))
    .where(...)
)
```
**预计时间**: 30 分钟

### 12. API 参数验证
**文件**: 多处
```python
# ✅ 使用 Pydantic 验证
from pydantic import validator, Field

class ChapterQuery(BaseModel):
    chapter_number: int = Field(..., ge=1, le=100)
    document_id: int = Field(..., gt=0)

    @validator('chapter_number')
    def validate_chapter(cls, v):
        if v > 50:
            raise ValueError('章节数量不能超过50')
        return v
```
**预计时间**: 45 分钟

### 13. React.memo 优化
**文件**: `src/components/mistakes/MistakeCard.tsx`
```typescript
// ✅ 包裹组件
export const MistakeCard = React.memo(({ mistake, onMarkMastered }: MistakeCardProps) => {
  // ...
}, (prevProps, nextProps) => {
  return prevProps.mistake.id === nextProps.mistake.id
})
```
**预计时间**: 15 分钟

### 14. TypeScript 类型统一
**文件**: `src/app/quiz/page.tsx:96`
```typescript
// ❌ 当前：类型不匹配
user_id={user?.id ?? undefined}

// ✅ 修复：统一类型定义
interface QuizProps {
  userId: number | null
  token: string | null
}

// 使用时
<Quiz userId={user?.id ?? null} token={token ?? null} />
```
**预计时间**: 20 分钟

### 15. 清理未使用代码
**文件**: 多处
```typescript
// 移除未使用的导入
- import { Drag } from 'framer-motion'  // KnowledgeConstellation.tsx:13

// 移除 TODO 注释或实现功能
- // TODO: 添加筛选功能  // mistakes/page.tsx:8
```
**预计时间**: 15 分钟

---

## 🟢 P3 - 低优先级（优化改进）

### 16. 移除 console.error
```typescript
// ❌ 生产环境不应有
console.error('Failed to load:', error)

// ✅ 使用日志系统
logger.error('Failed to load', { error })
```

### 17. localStorage 异常处理
```typescript
export function saveToLocalStorage(key: string, value: any) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (error) {
    console.warn('localStorage full or disabled')
    // 降级到内存存储
    memoryStorage.set(key, value)
  }
}
```

### 18. 添加 React key
```typescript
// ❌ 缺少 key
{filters.map(filter => <Button>{filter}</Button>)}

// ✅ 添加唯一 key
{filters.map(filter => <Button key={filter.id}>{filter.name}</Button>)}
```

### 19. 会话存储迁移到 Redis
```python
# ❌ 当前：内存存储
active_sessions: Dict[str, Any] = {}

# ✅ 修复：Redis
import redis
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
redis_client.setex(session_token, 3600, user_data)
```

### 20. 请求速率限制
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/upload")
@limiter.limit("5/minute")  # 每分钟最多5次
async def upload_document(...):
    ...
```

---

## 📋 修复检查清单

### 第一批：安全加固（1-2小时）
- [ ] 更换 JWT Secret
- [ ] 添加密码复杂度验证
- [ ] 缩短 Token 有效期
- [ ] 修复 XSS 漏洞
- [ ] 实现环境变量配置

### 第二批：稳定性提升（2-3小时）
- [ ] 移除硬编码地址
- [ ] 统一错误处理
- [ ] 文件大小限制
- [ ] 修复内存泄漏
- [ ] 实现日志系统

### 第三批：性能优化（2-3小时）
- [ ] 解决 N+1 查询
- [ ] API 参数验证
- [ ] React.memo 优化
- [ ] 类型定义统一
- [ ] 清理冗余代码

### 第四批：完善改进（1-2小时）
- [ ] 移除 console.error
- [ ] localStorage 异常处理
- [ ] 添加 React key
- [ ] Redis 会话存储
- [ ] 速率限制

---

## 🎯 快速启动方案

如果需要**立即部署到测试环境**，只需完成：
1. JWT Secret 更换（10分钟）
2. 环境变量配置（10分钟）
3. 移除硬编码地址（20分钟）
4. XSS 修复（15分钟）

**总计**: ~1 小时

如果需要**生产环境部署**，建议完成：
- P0 + P1 问题（5-8小时）
- 基础日志和监控（1小时）
- 安全配置（1小时）

**总计**: ~1-2 天

---

**文档版本**: v1.0.0
**创建时间**: 2026-01-29
**预计总修复时间**: 8-12 小时（全部完成）
