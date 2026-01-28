# EduGenius

<div align="center">

**高端 AI 自适应教育平台**

[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-blue?style=flat-square&logo=langchain)](https://langchain-ai.github.io/langgraph/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)

一个基于 AI 的智能教学系统，通过自适应学习路径和个性化辅导，为每位学习者提供定制化的教育体验。

[功能特性](#-功能特性) · [快速开始](#-快速开始) · [技术架构](#-技术架构) · [开发进度](#-开发进度)

</div>

---

## ✨ 功能特性

### 🤖 AI 智能教学
- **多智能体系统**：基于 LangGraph 的架构，包含教学设计师、AI 导师、出题专家
- **自适应难度**：L1-L5 五级难度调节，根据学生能力动态调整
- **实时对话**：SSE 流式传输，提供流畅的打字机效果
- **RAG 检索**：基于 ChromaDB 的向量检索，提供精准的知识点讲解

### 👤 用户系统
- **三步注册流程**：基本信息 → 能力测评 → 等级推荐
- **JWT 认证**：安全的 Token 认证机制
- **密码加密**：bcrypt 密码哈希存储
- **会话持久化**：自动保存学习历史和进度

### 📊 学习追踪
- **实时进度条**：可视化展示学习进度
- **能力雷达图**：六维能力评估（理解、逻辑、术语、记忆、应用、稳定）
- **历史记录**：完整的对话历史和答题记录
- **错题本**：自动收集错题，支持复习

### 🎨 精美界面
- **沉浸式聊天**：极简设计风格，支持 Markdown、LaTeX、Mermaid 图表
- **响应式布局**：完美适配桌面端和移动端
- **流畅动画**：Framer Motion 驱动的交互动画
- **暗色模式**：保护眼睛的夜间学习模式

---

## 🏗️ 技术架构

### 前端技术栈
```
Next.js 16      # React 框架
React 19        # UI 库
TypeScript 5.9  # 类型系统
TailwindCSS 4   # 样式框架
Framer Motion   # 动画库
Recharts        # 数据可视化
React Markdown  # Markdown 渲染
KaTeX           # 数学公式
Mermaid         # 图表渲染
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
```

---

## 📁 项目结构

```
EduGenius/
├── api/                      # 后端 API 服务
│   ├── app/
│   │   ├── agents/          # LangGraph 智能体
│   │   │   ├── graphs/      # 工作流图
│   │   │   ├── nodes/       # 智能体节点
│   │   │   └── state/       # 状态管理
│   │   ├── api/endpoints/   # API 端点
│   │   ├── core/            # 核心功能（安全、配置）
│   │   ├── crud/            # 数据库操作
│   │   ├── db/              # 数据库连接
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic 模型
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
│   │   ├── mistakes/        # 错题本
│   │   └── learn/           # 学习演示
│   ├── components/          # React 组件
│   │   ├── chat/           # 聊天相关组件
│   │   ├── charts/         # 图表组件
│   │   ├── layout/         # 布局组件
│   │   ├── progress/       # 进度组件
│   │   └── visualization/  # 可视化组件
│   ├── lib/                # 工具函数
│   ├── styles/             # 全局样式
│   └── types/              # TypeScript 类型
│
├── design-system/           # 设计系统文档
├── PROGRESS_REPORT.md       # 开发进度报告
├── STEP*.md                # 各阶段开发文档
└── README.md               # 本文件
```

---

## 🚀 快速开始

### 前置要求
- Node.js >= 18.0
- Python >= 3.10
- 通义千问 API Key

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
# 编辑 .env 文件，填入你的 DASHSCOPE_API_KEY

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
4. 进入学习页面开始与 AI 导师对话

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

## 📊 开发进度

**当前版本：v0.5.0**

**整体完成度：85%**

### ✅ 已完成功能

| 模块 | 完成度 | 状态 |
|------|--------|------|
| 前端基础架构 | 100% | ✅ |
| AI 对话系统 | 100% | ✅ |
| 用户认证系统 | 100% | ✅ |
| 数据持久化 | 100% | ✅ |
| RAG 检索 | 100% | ✅ |
| UI 组件库 | 100% | ✅ |

### 🚧 开发中功能

| 模块 | 完成度 | 状态 |
|------|--------|------|
| 学习进度追踪 | 0% | ⏳ |
| 错题本功能 | 20% | ⏳ |
| 章节解锁机制 | 0% | ⏳ |
| 端到端测试 | 0% | ⏳ |

---

## 📖 API 文档

### 核心端点

#### 用户相关
- `POST /api/users/register` - 用户注册
- `POST /api/users/login` - 用户登录
- `POST /api/users/assess-level` - 能力测评
- `GET /api/users/{user_id}/history` - 获取历史记录
- `POST /api/users/{user_id}/update-progress` - 更新学习进度

#### 教学相关
- `POST /api/teaching/chat` - AI 对话（SSE 流式）
- `POST /api/documents/upload` - 上传教学文档

完整 API 文档请访问：http://localhost:8000/docs

---

## 🎯 核心功能演示

### 1. 自适应难度调节

```typescript
// 前端调用示例
const response = await fetch('http://localhost:8000/api/teaching/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "什么是向量？",
    chapter_id: "1",
    student_level: 3,  // L1-L5
    stream: true
  })
});
```

### 2. 能力测评

```typescript
// 提交测评答案
const assessment = await fetch('/api/users/assess-level', {
  method: 'POST',
  body: JSON.stringify({
    email: "user@example.com",
    answers: [5, 4, 3, 4, 5]  // 5 道题的得分
  })
});
// 返回推荐等级：L3 (进阶)
```

---

## 🤝 贡献指南

我们欢迎任何形式的贡献！

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
- [ ] 实时学习进度追踪
- [ ] 错题本数据持久化
- [ ] 能力雷达图动态更新
- [ ] 章节锁定/解锁机制

### v0.7.0 (计划中)
- [ ] 端到端测试
- [ ] 性能优化
- [ ] 移动端适配优化
- [ ] PWA 支持

### v1.0.0 (未来)
- [ ] 多语言支持
- [ ] 协作学习功能
- [ ] 学习报告导出
- [ ] 家长/教师端

---

## ❓ 常见问题

### Q: 如何获取通义千问 API Key？
A: 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/) 申请开通。

### Q: 数据库文件在哪里？
A: SQLite 数据库文件在 `api/edugenius.db`，ChromaDB 数据在 `api/chroma_db/`。

### Q: 如何修改 AI 教学风格？
A: 编辑 `api/app/agents/state/level_prompts.py` 中的提示词模板。

### Q: 前端如何连接到远程后端？
A: 修改 `src/components/chat/StudyChat.tsx` 中的 API 地址。

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🌟 致谢

- [Next.js](https://nextjs.org/) - React 框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [LangChain](https://langchain.com/) - LLM 应用开发框架
- [TailwindCSS](https://tailwindcss.com/) - CSS 框架
- [通义千问](https://tongyi.aliyun.com/) - AI 模型服务

---

<div align="center">

**如果这个项目对你有帮助，请给它一个 ⭐️**

Made with ❤️ by [NissonCX](https://github.com/NissonCX)

</div>
