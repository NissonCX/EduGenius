# 更新日志

## [2026-02-04] - v1.2.0 启动指南和数据库迁移

### 新增 (Added)
- **SETUP_GUIDE.md** - 详细的启动配置指南
  - 完整的系统要求和依赖说明
  - 分步安装和配置指导
  - 数据库配置说明
  - API 密钥配置指南
  - 常见问题解决方案
  - 生产部署检查清单

- **MIGRATION_GUIDE.md** - 数据库迁移执行指南
  - 迁移脚本说明
  - 手动 SQL 迁移方法
  - 完全重置数据库指南
  - 常见错误排查

- **start-dev.sh** - 一键启动脚本
  - 自动检查系统环境
  - 自动安装依赖
  - 自动初始化数据库
  - 自动执行迁移
  - 自动启动服务

- **stop-dev.sh** - 一键停止脚本

### 修复 (Fixed)
- **登录/注册功能** - 添加缺失的 `refresh_token` 列
  - 修复用户注册返回数据不完整问题
  - 添加 refresh_token 到 LoginResponse

- **历史对话功能** - 添加缺失的 `subsection_number` 列
  - 修复 questions 表结构不匹配问题
  - 添加数据库迁移脚本

- **前端构建错误** - 修复导入错误
  - 删除 PWAInstaller.tsx 中多余的标签
  - 修复 dashboard/page.tsx 导入问题
  - 实现 fetchCompetencyData 和 fetchKnowledgeGraph 本地函数

### 更新 (Changed)
- **README.md** - 更新快速开始部分
  - 添加一键启动说明
  - 添加数据库迁移提醒
  - 添加启动指南文档链接

### 文档 (Documentation)
- 所有新增文档包含详细的错误排查
- 提供多种启动方式供选择
- 包含完整的命令示例

---

## [2026-02-03] - v1.1.0 文档更新和项目整理

### 变更 (Changed)
- 更新 README.md，反映最新的项目状态和功能
- 更新 DEPLOYMENT_GUIDE.md，添加 Docker 和生产部署说明
- 更新 LEARNING_PROGRESS_DESIGN.md，标记已实现功能
- 更新 QUIZ_BUSINESS_PLAN.md，反映当前测试功能状态
- 更新 DEBUGGING_GUIDE.md，确认问题已修复

### 移除 (Removed)
- 删除多余的进度和总结文档（9个文件）
- 清理临时工作文档

### 文档 (Documentation)
- 所有文档更新到 v1.1.0 版本
- 统一文档格式和版本信息

---

## [2026-02-01] - 功能完善和错误修复

## [2026-01-30] - PaddleOCR 集成与功能测试

### 新增 (Added)
- PaddleOCR 2.7.0 OCR 引擎集成
- 完整的功能测试脚本 (`test_functionality.py`)
- 端到端上传测试脚本 (`test_upload_flow.py`)
- 服务器启动脚本 (`start_server.sh`)
- 功能测试报告 (`FUNCTIONALITY_TEST_REPORT.md`)
- 明日工作恢复指南 (`TOMORROW_ACTION_PLAN.md`)

### 修复 (Fixed)
- **PaddleOCR 导入错误**: 降级到 2.7.0 版本，解决 langchain.docstore 依赖冲突
- **NumPy 兼容性问题**: 降级到 1.26.4，解决 imgaug 不兼容 NumPy 2.x 的问题
- **章节提取缺失**: 在快速路径添加 TextbookParser 和 EnhancedChapterDivider 调用
- **上传进度显示**: 修复前端轮询缺少认证 token 的问题

### 更新 (Changed)
- `requirements.txt`: 更新 OCR 依赖版本
- `app/core/ocr_engine.py`: 添加 logger 导入和环境变量配置
- `app/services/hybrid_document_processor.py`: 完善章节提取逻辑
- `src/components/upload/SmartUpload.tsx`: 优化上传进度显示
- `src/app/documents/page.tsx`: 改进文档列表刷新机制

### 技术细节 (Technical)
- **OCR 引擎**: PaddleOCR 2.7.0 + PaddlePaddle 2.6.2
- **识别准确率**: 98.9%
- **处理性能**: 单页 2-3 秒
- **API 响应**: <100ms

### 测试 (Testing)
- ✅ 后端健康检查通过
- ✅ 用户认证系统通过
- ✅ 文档列表查询通过
- ✅ OCR 引擎测试通过
- ✅ 文档上传流程通过
- ✅ MD5 去重功能通过

### 文档 (Documentation)
- 更新 `DAILY_PROGRESS.md`
- 创建 `FUNCTIONALITY_TEST_REPORT.md`
- 更新 `TOMORROW_ACTION_PLAN.md`

---

## [2026-01-29] - 文档上传与章节提取

### 新增 (Added)
- 智能文档上传页面
- 混合文档处理器（快速路径 + OCR 路径）
- PDF 文本层检测
- 章节自动划分功能

### 修复 (Fixed)
- 临时文件处理问题
- SQLAlchemy 会话管理
- 前端 Toast 错误

---

## [2026-01-28] - 项目初始化

### 新增 (Added)
- FastAPI 后端框架
- Next.js 前端框架
- 用户认证系统
- 多智能体教学系统
- ChromaDB 向量存储
