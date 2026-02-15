# EduGenius

<div align="center">

# 🚧 开发中的 AI 教育平台

**⚠️ 注意：本项目处于活跃开发阶段，核心功能尚未完成，不建议用于生产环境。**

[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-blue?style=flat-square&logo=langchain)](https://langchain-ai.github.io/langgraph/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![Status](https://img.shields.io/badge/Status-WIP-orange?style=flat-square)](https://github.com/NissonCX/EduGenius)

一个基于 AI 的智能教学系统，通过自适应学习路径和个性化辅导，为每位学习者提供定制化的教育体验。

[项目概览](#-项目概览) · [快速开始](#-快速开始) · [开发进度](#-开发进度) · [已知问题](#-已知问题)

</div>

---

## 📋 项目概览

### 🎯 项目目标

EduGenius 旨在构建一个基于多智能体架构的自适应学习平台，通过 AI 导师为学生提供个性化教学体验。

### ⚠️ 当前状态

**这是个人学习项目，目前处于中期开发阶段：**

- ✅ 基础架构已搭建完成
- ✅ 用户认证系统完整
- ✅ 核心对话功能可用
- ✅ 文档上传和章节识别完成
- ✅ 错题本功能基本实现
- ✅ 仪表板和进度追踪完成
- ✅ LaTeX 公式渲染正常
- ✅ 对话记忆功能完整
- 🚧 测验系统完善中
- 🚧 存在已知 Bug 和限制
- 🚧 未经充分测试

### 🏗️ 核心特性（已实现）

- **AI 智能教学系统**：基于 LangGraph 的多智能体架构
- **自适应难度调节**：L1-L5 五级教学风格
- **文档上传与解析**：支持 PDF 教材的章节识别
- **小节级学习**：支持细粒度的知识点学习
- **实时对话**：SSE 流式传输的 AI 导师对话
- **能力评估**：六维能力评估系统
- **错题本系统**：自动收集和复习错题
- **学习进度追踪**：实时更新学习进度
- **LaTeX 公式支持**：数学公式完美渲染

---

## 🏗️ 技术架构

### 前端技术栈

```
Next.js 16.1.6      # React 框架
React 19            # UI 库
TypeScript 5.9      # 类型系统
TailwindCSS 4       # 样式框架
Framer Motion       # 动画库
Recharts            # 数据可视化
React Markdown      # Markdown 渲染
KaTeX 0.16          # 数学公式
Radix UI            # UI 组件库
Lucide React        # 图标库
```

### 后端技术栈

```
FastAPI 0.115        # Web 框架
LangGraph 0.2        # AI 智能体框架
LangChain            # LLM 集成
SQLAlchemy 2.0       # ORM
ChromaDB 0.6         # 向量数据库
SQLite               # 关系数据库
Pydantic 2.10        # 数据验证
Uvicorn              # ASGI 服务器
PaddleOCR 2.7        # PDF 文字识别
```

### AI 能力

```
通义千问 (DashScope)  # 主要 LLM
OpenAI GPT           # 备用 LLM
Text Embeddings      # 向量嵌入
RAG 检索增强         # 知识库查询
PaddleOCR           # PDF 文字识别
```

---

## 🚀 快速开始

### ⚠️ 前置要求

**本地安装：**
- Node.js >= 18.0
- Python >= 3.10
- 通义千问 API Key（必需）

**Docker 部署：**
- Docker >= 20.10
- Docker Compose >= 2.0
- 通义千问 API Key（必需）

### 方式 1: Docker 部署（推荐）

**最简单的部署方式，无需安装 Node.js 和 Python**

```bash
# 1. 克隆项目
git clone https://github.com/NissonCX/EduGenius.git
cd EduGenius

# 2. 配置环境变量
cp .env.example .env
nano .env  # 填入 DASHSCOPE_API_KEY 和 JWT_SECRET_KEY

# 3. 启动所有服务（后端、前端、Redis）
docker compose up -d

# 4. 初始化数据库
docker compose exec backend python init_db.py
docker compose exec backend bash -c "cd migrations && python add_refresh_token.py && python add_subsection_to_questions.py"

# 5. 访问应用
# 前端: http://localhost:3000
# 后端: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

**详细的 Docker 部署说明请查看 [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)**

### 方式 2: 本地安装（一键启动）

**⚠️ 注意**: 首次使用需要先配置环境变量，请参考 [环境变量配置](#-环境变量配置) 章节。

```bash
git clone https://github.com/NissonCX/EduGenius.git
cd EduGenius

# 1. 配置后端环境变量（必须）
cp api/.env.example api/.env
nano api/.env  # 填入 DASHSCOPE_API_KEY 和 JWT_SECRET_KEY

# 2. 配置前端环境变量（可选，使用默认值即可）
cp .env.local.example .env.local

# 3. 一键启动
./start-dev.sh
```

启动脚本会自动完成：
- ✅ 检查系统环境（Node.js, Python 版本）
- ✅ 检查并安装前后端依赖（如缺失）
- ✅ 创建 Python 虚拟环境（如不存在）
- ✅ 检查环境变量配置
- ✅ 检查并初始化数据库（如不存在）
- ✅ 启动前后端服务

**首次安装请务必先配置环境变量！**

### 方式 3: 本地手动安装

**适合需要完全控制安装过程的用户**

**详细步骤请查看 [启动指南](SETUP_GUIDE.md)**

```bash
# 1. 克隆项目
git clone https://github.com/NissonCX/EduGenius.git
cd EduGenius

# 2. 安装前端依赖
npm install

# 3. 安装后端依赖
cd api
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. 配置环境变量（必须！）
cp .env.example .env
nano .env  # 编辑 .env 文件，填入 DASHSCOPE_API_KEY（必需）

# 5. 初始化数据库
python3 init_db.py

# 6. 执行数据库迁移（重要！）
cd migrations
python3 add_refresh_token.py
python3 add_subsection_to_questions.py

# 7. 启动后端服务
cd ..
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**新开终端启动前端:**
```bash
cd EduGenius
cp .env.local.example .env.local  # 配置前端环境变量
npm run dev
```

**详细的迁移说明请参考 [迁移指南](MIGRATION_GUIDE.md)**

### 部署方式对比

| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **Docker 部署** | • 环境隔离<br>• 一键启动<br>• 易于部署 | • 需要 Docker<br>• 占用资源稍多 | 生产环境、快速演示 |
| **本地安装** | • 灵活调试<br>• 资源占用少<br>• 热重载快 | • 环境配置复杂<br>• 依赖管理麻烦 | 开发环境、深度定制 |

### 访问应用

服务启动成功后，访问：

- 🌐 **前端**: http://localhost:3000
- 🔧 **后端 API**: http://localhost:8000
- 📚 **API 文档**: http://localhost:8000/docs
- ❤️ **健康检查**: http://localhost:8000/health

### 数据库迁移（重要！）

**首次安装必须执行数据库迁移！**

如果遇到数据库相关错误，请查看 [迁移指南](MIGRATION_GUIDE.md) 或执行：

```bash
cd api/migrations
python3 add_refresh_token.py           # 修复登录问题
python3 add_subsection_to_questions.py # 修复历史对话问题
```

**为什么需要迁移？**

数据库迁移用于添加新字段和修复数据结构：
- `add_refresh_token.py` - 添加刷新令牌功能，修复登录问题
- `add_subsection_to_questions.py` - 添加小节支持，修复历史对话问题

### 开始使用

1. 访问 http://localhost:3000/register 注册账户
2. 选择教学风格偏好
3. 上传 PDF 教材或进入学习页面
4. 开始与 AI 导师对话学习

---

## 📊 开发进度

**当前版本：v1.0.0-alpha**

**整体完成度：约 75%**

### ✅ 已完成功能

| 模块 | 完成度 | 说明 |
|------|--------|------|
| 前端基础架构 | 95% | 主要页面已实现，样式完善 |
| AI 对话系统 | 85% | 对话记忆、流式输出正常 |
| 用户认证系统 | 95% | 注册登录、会话管理完善 |
| 文档上传 | 85% | PDF 解析、OCR 识别完成 |
| 章节识别 | 80% | 基于目录的章节划分完善 |
| 小节支持 | 75% | 数据模型和 UI 已实现 |
| 教学风格系统 | 85% | L1-L5 提示词优化，持久化完成 |
| LaTeX 渲染 | 90% | 数学公式支持完善 |
| 错题本功能 | 70% | 基础功能实现，待优化 |
| 仪表板 | 80% | 进度展示、数据可视化完成 |
| 学习进度追踪 | 75% | 实时更新、历史记录正常 |
| 能力评估 | 70% | 六维评估、雷达图展示 |

### 🚧 开发中功能

| 模块 | 完成度 | 说明 |
|------|--------|------|
| 章节测试 | 50% | 基础结构完成，题目生成待完善 |
| 章节解锁机制 | 30% | 逻辑设计中 |
| 端到端测试 | 0% | 未开始 |

### 📝 待开发功能

- [ ] 完整的章节测试系统
- [ ] 章节锁定/解锁机制
- [ ] 单元测试和集成测试
- [ ] 性能优化
- [ ] 移动端适配优化
- [ ] 暗色模式完善
- [ ] 学习报告导出

---

## ⚠️ 已知问题

### 严重问题

- **章节测试功能未完成**：题目生成和评分逻辑需要完善
- **章节解锁机制缺失**：无法控制学习顺序

### 中等问题

- **错题本复习功能**：重做错题后状态更新不完善
- **能力雷达图更新**：某些情况下未实时刷新

### 轻微问题

- 部分 UI 动画不够流畅
- 移动端适配不完善
- 错误提示信息不够友好

---

## 📁 项目结构

```
EduGenius/
├── api/                      # 后端 API 服务
│   ├── app/
│   │   ├── agents/          # LangGraph 智能体
│   │   │   ├── nodes/       # 智能体节点
│   │   │   ├── graphs/      # 工作流图
│   │   │   └── state/       # 状态管理
│   │   ├── api/endpoints/   # API 端点
│   │   ├── core/            # 核心配置
│   │   ├── db/              # 数据库
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic 模式
│   │   ├── services/        # 业务逻辑
│   │   └── crud/            # 数据库操作
│   ├── main.py              # FastAPI 入口
│   └── requirements.txt     # Python 依赖
│
├── src/                      # 前端应用
│   ├── app/                 # Next.js App Router
│   │   ├── page.tsx         # 首页
│   │   ├── login/           # 登录
│   │   ├── register/        # 注册
│   │   ├── dashboard/       # 仪表板
│   │   ├── study/           # 学习页面
│   │   ├── quiz/            # 测试页面
│   │   ├── mistakes/        # 错题本
│   │   ├── upload/          # 上传页面
│   │   └── documents/       # 文档管理
│   ├── components/          # React 组件
│   │   ├── ui/             # 通用 UI 组件
│   │   ├── layout/         # 布局组件
│   │   ├── study/          # 学习组件
│   │   ├── quiz/           # 测试组件
│   │   └── progress/       # 进度组件
│   ├── lib/                # 工具函数
│   ├── styles/             # 全局样式
│   └── types/              # TypeScript 类型
│
├── CHANGELOG.md             # 更新日志
├── DEPLOYMENT_GUIDE.md      # 部署指南
├── DEBUGGING_GUIDE.md       # 调试指南
├── LEARNING_PROGRESS_DESIGN.md  # 学习进度设计
├── QUIZ_BUSINESS_PLAN.md    # 测验业务方案
└── README.md                # 本文件
```

---

## 🔧 环境变量配置

### 后端 (`api/.env`)

```bash
# 通义千问 API 密钥（必需）
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# JWT 密钥（必需）
JWT_SECRET_KEY=your_secret_key_here

# 数据库路径（可选）
DATABASE_URL=sqlite+aiosqlite:///./edugenius.db

# ChromaDB 路径（可选）
CHROMA_PERSIST_DIR=./chroma_db

# 文件上传限制（可选）
MAX_FILE_SIZE_MB=50
```

### 前端 (`.env.local`)

```bash
# API 地址
NEXT_PUBLIC_API_URL=http://localhost:8000

# 文件上传大小限制
NEXT_PUBLIC_MAX_FILE_SIZE=52428800

# Token 有效期
NEXT_PUBLIC_TOKEN_EXPIRE_MINUTES=120
```

---

## 📖 API 文档

启动后端服务后，访问 http://localhost:8000/docs 查看完整的 API 文档。

### 核心端点

#### 用户相关
- `POST /api/users/register` - 用户注册
- `POST /api/users/login` - 用户登录
- `POST /api/users/refresh` - 刷新 Token
- `GET /api/users/me` - 获取当前用户信息
- `PUT /api/users/me/teaching-style` - 更新教学风格

#### 文档相关
- `POST /api/documents/upload` - 上传教学文档
- `GET /api/documents` - 获取文档列表
- `GET /api/documents/{doc_id}/chapters` - 获取章节列表
- `DELETE /api/documents/{doc_id}` - 删除文档

#### 教学相关
- `POST /api/teaching/start` - 开始教学对话
- `GET /api/teaching/chat` - 获取聊天消息 (SSE)
- `DELETE /api/teaching/session` - 结束会话

#### 测验相关
- `GET /api/quiz/questions/{doc_id}/{chapter_number}` - 获取测验题目
- `POST /api/quiz/submit` - 提交答案
- `GET /api/quiz/results` - 获取结果

#### 错题本
- `GET /api/mistakes` - 获取错题列表
- `POST /api/mistakes/{id}/retry` - 重做错题
- `DELETE /api/mistakes/{id}` - 删除错题

---

## 🤝 贡献指南

这是一个个人学习项目，但目前仍欢迎贡献！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: 添加某个功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具链更新

---

## 📝 开发路线图

### v1.1.0 (进行中)
- [x] 错题本功能实现
- [x] 仪表板完善
- [x] 学习进度追踪
- [x] LaTeX 渲染修复
- [x] 对话记忆功能
- [ ] 章节测试系统完善

### v1.2.0 (计划中)
- [ ] 章节锁定/解锁机制
- [ ] 测验题目自动生成优化
- [ ] 单元测试覆盖
- [ ] 性能优化

### v1.3.0 (计划中)
- [ ] 移动端适配优化
- [ ] 暗色模式完善
- [ ] PWA 支持

### v2.0.0 (未来)
- [ ] 多语言支持
- [ ] 学习报告导出
- [ ] 协作学习功能
- [ ] 生产环境部署

---

## ❓ 常见问题

### Q: 如何获取通义千问 API Key？
A: 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/) 申请开通。

### Q: 数据库文件在哪里？
A: SQLite 数据库文件在 `api/edugenius.db`，ChromaDB 数据在 `api/chroma_db/`。

### Q: 为什么上传的 PDF 章节识别不准确？
A: 目前的章节识别依赖 PDF 目录，对于目录不规范的教材识别效果较差。建议使用有清晰目录结构的 PDF。

### Q: LaTeX 公式显示不正常怎么办？
A: 请查看 [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) 中的 LaTeX 渲染调试步骤。

### Q: 如何参与开发？
A: 欢迎 Fork 并提交 PR！在提交前请先查看 [已知问题](#-已知问题) 部分。

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🌟 致谢

感谢以下开源项目：

- [Next.js](https://nextjs.org/) - React 框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [LangChain](https://langchain.com/) - LLM 应用开发框架
- [TailwindCSS](https://tailwindcss.com/) - CSS 框架
- [通义千问](https://tongyi.aliyun.com/) - AI 模型服务

---

<div align="center">

**⚠️ 这是开发中的项目，功能和 API 可能随时变化**

**如果这个项目对你有帮助，请给它一个 ⭐️**

Made with ❤️ by [NissonCX](https://github.com/NissonCX)

</div>
