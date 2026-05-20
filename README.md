# Hubu Agent - 智能问答系统

## 项目简介
Hubu Agent 是一个基于 LangGraph 的智能问答系统，集成了 RAG（检索增强生成）、知识库管理、用户认证等功能，支持多轮对话和工具调用。

## 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **Agent 框架**: LangGraph + LangChain
- **大语言模型**: Qwen3-VL (DashScope)
- **向量数据库**: Milvus
- **关系数据库**: MySQL + SQLModel
- **缓存**: Redis
- **认证**: JWT + PyJWT
- **文档解析**: unstructured, pypdf, docx2txt
- **依赖管理**: Poetry

### 前端
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI 组件**: Element Plus
- **HTTP 客户端**: Axios
- **Markdown 渲染**: markdown-it + highlight.js

## 核心功能

- ✅ **智能对话**: 基于 LangGraph 的多轮对话系统
- ✅ **RAG 知识库**: 支持文档上传、解析、向量化存储和检索
- ✅ **用户认证**: JWT Token 认证，支持注册/登录
- ✅ **对话历史**: MySQL 持久化存储，Redis 缓存加速
- ✅ **工具调用**: 支持天气查询、网络搜索等外部工具
- ✅ **流式输出**: Server-Sent Events (SSE) 实时响应

## 目录结构

```
hubu-agent/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API 路由 (v1/auth, v1/chat, v1/knowledge)
│   │   ├── auth/              # JWT 认证模块
│   │   ├── core/              # 核心逻辑
│   │   │   ├── agents/        # Agent 定义
│   │   │   ── graph/         # LangGraph 工作流
│   │   ├── database/          # 数据库层
│   │   │   ├── dao/           # 数据访问对象
│   │   │   ── models/        # 数据模型
│   │   ├── schemas/           # Pydantic 数据校验
│   │   ├── services/          # 业务逻辑
│   │   │   ├── rag/           # RAG 相关服务
│   │   │   └── llm_service.py # LLM 调用服务
│   │   ├── tools/             # 工具定义 (天气、搜索)
│   │   ├── config.py          # 配置管理
│   │   └── main.py            # 应用入口
│   ├── test/                  # 测试脚本
│   ├── .env                   # 环境变量配置
│   ├── pyproject.toml         # Poetry 依赖配置
│   └── README.md
── frontend/                  # 前端应用
│   ├── src/
│   │   ├── apis/              # API 调用封装
│   │   ├── pages/             # 页面组件
│   │   │   ├── LoginPage.vue
│   │   │   ├── ChatPage.vue
│   │   │   └── KnowledgePage.vue
│   │   ├── router/            # 路由配置
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
├── docs/                      # 项目文档
├── .gitignore
├── pyproject.toml
├── start_backend.bat          # Windows 后端启动脚本
└── start_frontend.bat         # Windows 前端启动脚本
```

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- Redis 6.0+
- Milvus 2.4+

### 后端启动

```bash
cd backend

# 安装依赖
poetry install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写数据库连接、API Key 等配置

# 启动服务
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

或者直接双击运行：
```bash
start_backend.bat
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

或者直接双击运行：
```bash
start_frontend.bat
```

### 访问地址
- 前端界面: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 配置说明

### 后端环境变量 (.env)

```env
# 数据库配置
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/hubu_agent

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_USER=
MILVUS_PASSWORD=

# DashScope API Key
DASHSCOPE_API_KEY=your-api-key-here

# JWT 配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 开发规范

### 代码提交
```bash
git add .
git commit -m "feat: 功能描述"  # feat/fix/docs/style/refactor/test/chore
git push
```

### API 路由规范
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/chat/completions` - 对话接口
- `POST /api/v1/knowledge/` - 知识库管理

## 项目文档

详细文档请查看 [docs/](docs/) 目录：
- [快速入门](docs/GETTING_STARTED.md)
- [项目结构说明](docs/PROJECT_STRUCTURE.md)
- [功能特性文档](docs/features/)

## 常见问题

### 1. 数据库连接失败
确保 MySQL 服务已启动，并检查 `.env` 中的数据库配置。

### 2. Milvus 连接失败
确保 Milvus 服务已启动，并检查认证配置。

### 3. LLM 调用失败
检查 `DASHSCOPE_API_KEY` 是否配置正确。

## 技术文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [Vue 3 官方文档](https://cn.vuejs.org/)
- [Milvus 文档](https://milvus.io/docs)

## License

MIT

## 作者

互补所短 <1879334164@qq.com>
