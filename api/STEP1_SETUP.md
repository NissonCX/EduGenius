# EduGenius - 第一步：打通 API 命脉

## ✅ 已完成的工作

### 1. 依赖安装
- ✅ langchain
- ✅ DashScope SDK
- ✅ langchain-community

### 2. 配置管理
- ✅ 创建 `core/config.py` 统一配置管理
- ✅ 创建 `.env.example` 环境变量模板
- ✅ 支持从环境变量读取 API 密钥

### 3. 智能体升级
- ✅ Architect 智能体 → ChatDashScope
- ✅ Examiner 智能体 → ChatDashScope  
- ✅ Tutor 智能体 → ChatDashScope
- ✅ 支持根据学生等级自动选择模型

### 4. 测试脚本
- ✅ 创建 `test_ai.py` 验证 API 连接
- ✅ 支持基础对话、流式响应、智能体集成测试

---

## 🔧 需要手动完成的步骤

### 步骤 1: 获取 DashScope API 密钥

1. 访问阿里云 DashScope 控制台：https://dashscope.console.aliyun.com/apiKey
2. 登录/注册阿里云账号
3. 创建 API Key
4. 复制 API Key

### 步骤 2: 配置环境变量

```bash
# 在 api 目录下创建 .env 文件
cd api
cp .env.example .env

# 编辑 .env 文件，填入真实的 API Key
# DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

### 步骤 3: 运行测试脚本

```bash
cd api
python3 test_ai.py
```

**预期输出：**
```
🚀 EduGenius AI 连接测试
============================================================
✅ 配置检查通过
📊 使用模型: qwen-max
🔑 API Key: ********************xxxx

============================================================
📋 测试 1: 基础对话功能
============================================================
✅ 基础对话成功！
📝 回复: 机器学习是一门通过数据训练模型的科学...

============================================================
📋 测试 2: 流式响应功能
============================================================
🔄 正在测试流式输出...
   (逐字打印效果)
向量是...
✅ 流式响应成功！

============================================================
📋 测试 3: Tutor 智能体集成
============================================================
🎓 Tutor 智能体初始化成功
✅ Tutor 讲解成功！

🎉 所有测试通过！DashScope 集成成功！
```

---

## 📁 文件变更清单

### 新增文件
```
api/
├── core/
│   └── config.py           # 统一配置管理
├── .env.example            # 环境变量模板
└── test_ai.py              # AI 连接测试脚本
```

### 修改文件
```
api/app/agents/nodes/
├── architect.py            # → 使用 ChatDashScope
├── examiner.py             # → 使用 ChatDashScope
└── tutor.py                # → 使用 ChatDashScope
```

---

## 🎯 下一步预览

完成 API 配置后，下一步将：
1. 实现文档上传和解析
2. 实现 RAG 向量检索
3. 实现 SSE 流式对话接口
4. 前端对接真实数据

---

## ❓ 常见问题

### Q: API Key 在哪里配置？
A: 在 `api/.env` 文件中配置 `DASHSCOPE_API_KEY`

### Q: 如何选择不同的模型？
A: 在 `.env` 中修改 `DEFAULT_MODEL`，可选值：
- `qwen-max` - 最强模型（推荐）
- `qwen-plus` - 快速模型（L1-L2 学生）

### Q: 测试脚本失败怎么办？
A: 检查：
1. API Key 是否正确设置
2. 网络连接是否正常
3. Python 依赖是否完整安装

---

**完成配置后，请运行测试脚本验证！** 🚀
