# 🎓 EduGenius 智能上传系统 - 完整演示指南

## 🎯 功能概览

实现了**混合处理架构**，支持：
- ✅ **快速路径**：文本版 PDF（5-10秒处理）
- ✅ **OCR 路径**：扫描版 PDF（2-10分钟处理）
- ✅ **智能检测**：自动判断 PDF 类型
- ✅ **实时进度**：平滑进度条 + 分阶段动画
- ✅ **并发控制**：防止服务器过载
- ✅ **置信度警告**：低质量扫描件提示

---

## 🚀 使用演示

### 场景 1：上传文本版 PDF（快速路径）

```
1. 访问 http://localhost:3000/upload
2. 拖拽或点击上传教材 PDF
3. 观察处理流程：

   📋 检测PDF类型
      ↓
   ✅ 检测到文本层（85% 页面有文本）
      ↓
   ⚡ 快速路径处理
      ↓
   提取文本内容...  ████████████ 100%
      ↓
   向量化存储...  ████████████ 100%
      ↓
   ✅ 处理完成！（耗时：8秒）

4. 自动跳转到文档详情页
```

### 场景 2：上传扫描版 PDF（OCR 路径）

```
1. 访问 http://localhost:3000/upload
2. 上传扫描版教材
3. 观察处理流程：

   📋 检测PDF类型
      ↓
   ⚠️  检测到扫描版（5% 页面有文本）
      ↓
   💡 将使用 PaddleOCR 进行文字识别
   预计处理时间: 200-500 秒
      ↓
   🔬 OCR识别中
      第 1/100 页...  ████░░░░░░░░ 1%
      第 2/100 页...  ██████░░░░░░░ 2%
      第 3/100 页...  ████████░░░░░░ 3%
      ...
      第 99/100 页...  ██████████████ 99%
      第 100/100 页...  ██████████████ 100%
      ↓
   📊 识别完成（置信度: 87.5%）
      ↓
   🧠 向量化存储...  ████████████ 100%
      ↓
   ✅ 处理完成！（耗时：245秒）

4. 显示 OCR 标签（👁️ OCR识别）
5. 显示提示："此文档通过OCR识别，建议核对专业术语"
```

### 场景 3：服务器繁忙（并发控制）

```
1. 两个用户同时上传扫描版 PDF
2. 第三个用户上传时：

   ⏳ 服务器繁忙，您的文档已加入队列，请稍后刷新页面查看进度

3. 第三个用户刷新页面
4. 等待其他任务完成后开始处理
```

---

## 🎨 设计细节

### 背景动画效果

```tsx
{/* 动态渐变背景 */}
<div className="fixed inset-0">
  {/* 基础渐变 */}
  <div className="bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50" />

  {/* 蓝色光晕 */}
  <motion.div
    animate={{
      scale: [1, 1.2, 1],
      opacity: [0.3, 0.5, 0.3],
    }}
    transition={{ duration: 8, repeat: Infinity }}
    className="w-96 h-96 bg-blue-400/20 rounded-full blur-3xl"
  />

  {/* 紫色光晕 */}
  <motion.div
    animate={{
      scale: [1.2, 1, 1.2],
      opacity: [0.5, 0.3, 0.5],
    }}
    transition={{ duration: 10, repeat: Infinity }}
    className="bottom-0 right-1/4 w-96 h-96 bg-purple-400/20 rounded-full blur-3xl"
  />

  {/* 网格纹理 */}
  <div className="absolute inset-0 opacity-[0.03]"
    style={{
      backgroundImage: `
        linear-gradient(rgba(0,0,0,0.1) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,0,0,0.1) 1px, transparent 1px)
      `,
      backgroundSize: '50px 50px'
    }}
  />
</div>
```

### 平滑进度条算法

```typescript
// easeOutQuart 缓动函数 - 让进度像人类思考
function useSmoothProgress(targetProgress: number, duration: number = 600) {
  const [smoothProgress, setSmoothProgress] = useState(0)

  useEffect(() => {
    if (targetProgress === 0) {
      setSmoothProgress(0)
      return
    }

    const startValue = smoothProgress
    const difference = targetProgress - startValue
    const startTime = Date.now()

    const animate = () => {
      const now = Date.now()
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)

      // easeOutQuart 缓动
      const easeOutQuart = (t: number) => 1 - Math.pow(1 - t, 4)
      const currentValue = startValue + difference * easeOutQuart(progress)

      setSmoothProgress(currentValue)

      if (progress < 1) {
        requestAnimationFrame(animate)
      } else {
        setSmoothProgress(targetProgress)
      }
    }

    requestAnimationFrame(animate)
  }, [targetProgress, duration])

  return smoothProgress
}
```

**效果对比**：

| 原始进度 | 平滑进度 |
|---------|---------|
| 0% → 20% → 40% → 60% → 80% → 100% | 0% → 3% → 8% → 15% → 26% → 40% → 58% → 78% → 92% → 100% |
| (生硬跳变) | (流畅渐进) |

### Glassmorphism 卡片

```css
.glass-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}
```

---

## 📊 API 接口

### 1. 上传文档

**端点**: `POST /api/documents/upload`

**响应示例**：
```json
{
  "message": "✅ 文档已上传，正在OCR识别中...",
  "is_duplicate": false,
  "document_id": 123,
  "md5_hash": "abc123...",
  "processing_status": "pending"
}
```

### 2. 查询进度

**端点**: `GET /api/documents/{id}/status`

**响应示例**（OCR 处理中）：
```json
{
  "document_id": 123,
  "filename": "化学教材.pdf",
  "title": "化学教材",
  "status": "ocr_processing",
  "stage": "正在OCR识别",
  "stage_message": "正在使用AI识别第 45/100 页...",
  "progress_percentage": 45,
  "has_text_layer": false,
  "ocr_confidence": 0.0,
  "current_page": 45,
  "total_pages": 100,
  "total_chapters": 0,
  "is_scan": true,
  "warning": "此文档通过OCR识别，建议核对专业术语",
  "ocr_notice": "扫描件识别准确率约85-95%，重要内容请手动核对"
}
```

**响应示例**（完成）：
```json
{
  "document_id": 123,
  "filename": "化学教材.pdf",
  "status": "completed",
  "stage": "处理完成",
  "stage_message": "文档已成功处理并可以使用",
  "progress_percentage": 100,
  "has_text_layer": false,
  "ocr_confidence": 0.875,
  "is_scan": true
}
```

---

## 🔧 测试步骤

### 前提条件

```bash
# 1. 安装 PaddleOCR（如果还没有）
pip install paddleocr

# 2. 启动后端
cd api
python main.py

# 3. 启动前端
cd ..
npm run dev
```

### 测试 1：文本版 PDF

1. 访问 http://localhost:3000/upload
2. 上传一个有文本层的 PDF
3. 观察 5-10 秒快速处理
4. 查看文档详情页

### 测试 2：扫描版 PDF

1. 访问 http://localhost:3000/upload
2. 上传一个扫描版 PDF
3. 观察实时 OCR 进度
4. 等待 2-10 分钟处理
5. 查看置信度警告

### 测试 3：并发控制

1. 打开 3 个浏览器标签
2. 同时上传 3 个扫描版 PDF
3. 观察第 3 个是否进入队列
4. 查看后端日志

---

## 📝 开发者信息

### 关键文件

**前端**：
- `/upload` - 上传页面
- `/components/upload/SmartUpload.tsx` - 上传组件
- `/design-system/MASTER.md` - 设计系统

**后端**：
- `/api/app/core/ocr_engine.py` - OCR 引擎
- `/api/app/services/hybrid_document_processor.py` - 混合处理器
- `/api/app/core/ocr_semaphore.py` - 并发控制

### 配置参数

**并发控制**：
```python
# api/app/core/ocr_semaphore.py
ocr_semaphore = OCRSemaphore(max_concurrent=2)  # 最多2个并发OCR任务
```

**置信度阈值**：
```python
# api/app/services/hybrid_document_processor.py
OCR_CONFIDENCE_THRESHOLD = 0.6  # 最低60%置信度
TEXT_RATIO_THRESHOLD = 0.1      # 10%文本占比阈值
```

---

## 🎬 下一步

### 立即可用
✅ 上传文本版 PDF - 快速处理
✅ 上传扫描版 PDF - OCR 识别
✅ 实时进度展示
✅ 置信度警告

### 待优化（建议）
- [ ] 实现 WebSocket 替代轮询
- [ ] 使用 Celery 替代 asyncio.create_task
- [ ] 添加 OCR 失败重试
- [ ] 优化文本后处理
- [ ] 添加文档详情页面
- [ ] 实现队列管理界面

---

## 💡 提示

**对于用户**：
- 文本版 PDF 推荐（快速、准确）
- 扫描版 PDF 也可以（稍慢、85-95% 准确率）
- 建议 OCR 后核对专业术语

**对于开发者**：
- 查看 design-system/MASTER.md 了解设计规范
- 修改 `max_concurrent` 调整并发限制
- 修改 `OCR_CONFIDENCE_THRESHOLD` 调整置信度要求

---

**提交信息**: `cd5f28a`
**分支**: `main → origin/main`

🎉 享受丝滑的文档上传体验！
