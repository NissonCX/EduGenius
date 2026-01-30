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

**这是个人学习项目，目前处于早期开发阶段：**

- ✅ 基础架构已搭建完成
- ✅ 核心对话功能可用
- 🚧 多项功能仍在开发中
- 🚧 存在已知 Bug 和限制
- 🚧 未经充分测试

### 🏗️ 核心特性（计划中）

- **AI 智能教学系统**：基于 LangGraph 的多智能体架构
- **自适应难度调节**：L1-L5 五级教学风格
- **文档上传与解析**：支持 PDF 教材的章节识别
- **小节级学习**：支持细粒度的知识点学习
- **实时对话**：SSE 流式传输的 AI 导师对话
- **能力评估**：六维能力评估系统

---

## 🏗️ 技术架构

### 前端技术栈

```
Next.js 16.1.6     # React 框架
React 19           # UI 库
TypeScript 5.9     # 类型系统
TailwindCSS 4      # 样式框架
Framer Motion      # 动画库
Recharts           # 数据可视化
React Markdown     # Markdown 渲染
KaTeX              # 数学公式
Mermaid            # 图表渲染
```

### 后端技术栈

```
FastAPI 0.115        # Web 框架
LangGraph 0.2        # AI 智能体框架
LangChain            # LLM 集成
SQLAlchemy 2.0       # ORM
ChromaDB             # 向量数据库
SQLite               # 关系数据库
Pydantic 2.10        # 数据验证
Uvicorn              # ASGI 服务器
```

### AI 能力

```
通义千问 (DashScope)  # 主要 LLM
Text Embeddings       # 向量嵌入
RAG 检索增强          # 知识库查询
PaddleOCR            # PDF 文字识别
```

---

## 🚀 快速开始

### ⚠️ 前置要求

- Node.js >= 18.0
- Python >= 3.10
- 通义千问 API Key（必需）

### 1. 克隆项目

```bash
git clone https://github.com/NissonCX/EduGenius.git
cd EduGenius
```

### 2. 后端设置

```bash
# 进入后端目录
cd api

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 DASHSCOPE_API_KEY（必需）

# 启动后端服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端将运行在 http://localhost:8000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 3. 前端设置

```bash
# 新开一个终端，进入项目根目录
cd EduGenius

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 http://localhost:3000

### 4. 开始使用

1. 访问 http://localhost:3000/register 注册账户
2. 完成 5 道能力测评题目
3. 系统推荐你的初始等级（L1-L5）
4. 上传 PDF 教材或进入学习页面

---

## 📊 开发进度

**当前版本：v0.5.0-alpha**

**整体完成度：约 60%**

### ✅ 已完成功能

| 模块 | 完成度 | 说明 |
|------|--------|------|
| 前端基础架构 | 90% | 主要页面已实现，部分待优化 |
| AI 对话系统 | 75% | 基础对话可用，需要更多测试 |
| 用户认证系统 | 80% | 注册登录正常，会话管理待完善 |
| 文档上传 | 70% | PDF 解析基本可用，OCR 识别待优化 |
| 章节识别 | 65% | 基于目录的章节划分已实现 |
| 小节支持 | 50% | 数据模型完成，UI 部分实现 |
| 教学风格系统 | 70% | L1-L5 提示词已优化，持久化完成 |

### 🚧 开发中功能

| 模块 | 完成度 | 说明 |
|------|--------|------|
| 学习进度追踪 | 20% | 数据模型存在，UI 待实现 |
| 错题本功能 | 10% | 页面已创建，功能未实现 |
| 章节测试 | 30% | 基础结构存在，题目生成待完善 |
| 章节解锁机制 | 0% | 未开始 |
| 端到端测试 | 0% | 未开始 |

### 📝 待开发功能

- [ ] 完整的学习进度追踪系统
- [ ] 错题本数据持久化和复习功能
- [ ] 能力雷达图实时更新
- [ ] 章节锁定/解锁机制
- [ ] 单元测试和集成测试
- [ ] 性能优化
- [ ] 移动端适配优化
- [ ] 暗色模式完善

---

## ⚠️ 已知问题

### 严重问题

- **PDF 章节识别不稳定**：部分教材的章节划分不准确
- **OCR 识别效率低**：扫描版 PDF 处理时间过长
- **教学风格切换不生效**：某些情况下切换风格后对话未立即更新

### 中等问题

- **错题本功能未完成**：页面存在但无法使用
- **进度条不准确**：学习进度显示可能与实际不符
- **能力雷达图不更新**：完成测试后图表未动态刷新

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
│   │   │   ├── graphs/      # 工作流图
│   │   │   ├── nodes/       # 智能体节点（导师、出题专家等）
│   │   │   └── state/       # 状态管理
│   │   ├── api/endpoints/   # API 端点
│   │   ├── core/            # 核心功能（安全、配置）
│   │   ├── db/              # 数据库连接
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   └── services/        # 业务逻辑
│   ├── main.py              # FastAPI 应用入口
│   └── requirements.txt     # Python 依赖
│
├── src/                      # 前端应用
│   ├── app/                 # Next.js App Router
│   │   ├── page.tsx         # 首页
│   │   ├── login/           # 登录页面
│   │   ├── register/        # 注册页面
│   │   ├── study/           # 学习页面
│   │   ├── dashboard/       # 仪表盘
│   │   ├── mistakes/        # 错题本（未完成）
│   │   └── quiz/            # 测试页面
│   ├── components/          # React 组件
│   │   ├── chat/           # 聊天相关组件
│   │   ├── layout/         # 布局组件
│   │   └── study/          # 学习相关组件
│   ├── lib/                # 工具函数
│   ├── styles/             # 全局样式
│   └── types/              # TypeScript 类型
│
├── CHANGELOG.md             # 更新日志
├── DEPLOYMENT_GUIDE.md      # 部署指南
└── README.md               # 本文件
```

---

## 🔧 环境变量配置

在 `api/.env` 文件中配置以下变量：

```bash
# 通义千问 API 密钥（必需）
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 数据库路径（可选，默认 ./edugenius.db）
DATABASE_URL=sqlite:///./edugenius.db

# ChromaDB 路径（可选，默认 ./chroma_db）
CHROMA_DB_PATH=./chroma_db

# CORS 设置（可选）
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

---

## 📖 API 文档

启动后端服务后，访问 http://localhost:8000/docs 查看完整的 API 文档。

### 核心端点

#### 用户相关
- `POST /api/users/register` - 用户注册
- `POST /api/users/login` - 用户登录
- `POST /api/users/assess-level` - 能力测评
- `GET /api/users/{user_id}` - 获取用户信息
- `PUT /api/users/{user_id}/teaching-style` - 更新教学风格

#### 文档相关
- `POST /api/documents/upload` - 上传教学文档
- `GET /api/documents` - 获取文档列表
- `GET /api/documents/{doc_id}/chapters` - 获取章节列表

#### 教学相关
- `POST /api/teaching/chat` - AI 对话（SSE 流式）
- `GET /api/teaching/history` - 获取对话历史

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

### v0.6.0 (进行中)
- [x] 小节支持系统
- [x] 教学风格优化
- [ ] 实时学习进度追踪
- [ ] 错题本功能实现
- [ ] PDF 章节识别优化

### v0.7.0 (计划中)
- [ ] 章节测试系统完善
- [ ] 能力雷达图动态更新
- [ ] 单元测试覆盖
- [ ] 性能优化

### v0.8.0 (计划中)
- [ ] 移动端适配优化
- [ ] 暗色模式完善
- [ ] PWA 支持

### v1.0.0 (未来)
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
A: 这是已知问题，目前的章节识别依赖 PDF 目录，对于目录不规范的教材识别效果较差。正在优化中。

### Q: 错题本功能什么时候能完成？
A: 错题本的基础架构已搭建，但功能实现还需要时间。预计在 v0.6 版本完成。

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
