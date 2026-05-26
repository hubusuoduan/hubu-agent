# Hubu Agent - 智能对话助手

## 项目简介

Hubu Agent 是一个基于 LangGraph 的智能对话助手，集成了 RAG 检索增强生成、长期记忆、知识库管理、多工具调用等能力，支持多轮对话和流式输出。

## 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **Agent 框架**: LangGraph + LangChain
- **大语言模型**: OpenAI 兼容 API（默认 Qwen/DashScope）
- **向量数据库**: Milvus 2.4+
- **关系数据库**: MySQL 8.0+ (SQLModel + aiomysql)
- **缓存**: Redis 6.0+
- **认证**: JWT (PyJWT)
- **文档解析**: pypdf, docx2txt, python-pptx, pandas, BeautifulSoup4, striprtf
- **依赖管理**: Poetry

### 前端
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI 组件**: Element Plus
- **HTTP 客户端**: Axios
- **Markdown 渲染**: markdown-it + highlight.js

## 核心功能

### 🤖 智能对话
- 基于 LangGraph 工作流的多轮对话系统
- 工作流：RAG 检索 → 长期记忆 → 历史管理 → ChatAgent → 记忆提取
- 支持流式输出（SSE）和非流式输出
- 支持文件上传并在对话中解析文件内容

### 🧠 长期记忆
- 基于 Milvus 向量数据库的长期记忆存储
- 自动从对话中提取记忆（偏好/事实/洞察）
- 记忆去重（基于向量相似度）
- 支持手动添加、编辑、删除记忆
- 记忆来源追溯

### 📚 RAG 知识库
- 支持创建、删除知识库
- 文档上传自动解析、分块、向量化索引
- 支持 13 种文档格式：txt, md, pdf, docx, html, csv, json, xlsx, pptx, rtf, xml 等
- 向量检索 + Reranker 重排序
- RAG 查询 API

### 🔧 工具调用（8 个内置工具）
| 工具 | 功能 |
|------|------|
| get_weather | 天气查询 |
| web_search | 网络搜索 |
| web_scraper | 网页抓取 |
| knowledge_search | 知识库搜索 |
| knowledge_list | 知识库列表 |
| code_runner | 代码执行 |
| report_generator | 报告生成（Markdown/HTML/TXT） |
| chart_generator | 图表生成（PNG/SVG/HTML） |

### 🔐 用户认证
- JWT Token 认证
- 用户注册/登录
- 所有 API 接口鉴权保护

### 🔍 工作流可视化
- 实时展示 LangGraph 工作流节点执行路径
- 节点状态追踪（运行中/完成/失败）
- 节点耗时统计
- 节点详情侧边栏（输入/输出数据查看）

### 💬 对话管理
- 对话创建/列表/详情/改名/删除
- 对话历史持久化存储（MySQL）
- 历史消息加载（最近 10 条作为上下文）

### 📊 报告管理
- 报告文件下载（支持 Header/URL Token 双认证）
- 报告列表/删除
- 支持多种格式：Markdown, HTML, TXT, PNG, SVG 等

## 目录结构

```
hubu-agent/
├── backend/                        # 后端服务
│   ├── app/
│   │   ├── api/v1/                 # API 路由
│   │   │   ├── auth.py             # 认证接口（注册/登录）
│   │   │   ├── chat.py             # 聊天接口（流式/非流式/文件上传）
│   │   │   ├── dialog.py           # 对话管理接口
│   │   │   ├── knowledge.py        # 知识库接口（CRUD/上传/查询）
│   │   │   ├── memory.py           # 记忆管理接口（CRUD）
│   │   │   ├── report.py           # 报告接口（下载/列表/删除）
│   │   │   └── router.py           # 路由注册
│   │   ├── auth/                   # JWT 认证模块
│   │   ├── core/
│   │   │   ├── agents/             # Agent 定义
│   │   │   │   ├── chat_agent.py   # 聊天 Agent（create_react_agent）
│   │   │   │   ├── memory_agent.py # 记忆 Agent
│   │   │   │   └── summary_agent.py # 摘要 Agent
│   │   │   └── graph/              # LangGraph 工作流
│   │   │       ├── graph.py        # 工作流定义
│   │   │       ├── state.py        # ChatState 状态定义
│   │   │       └── nodes/          # 工作流节点
│   │   │           ├── rag_node.py           # RAG 检索节点
│   │   │           ├── memory_node.py        # 长期记忆检索节点
│   │   │           ├── history_node.py       # 历史管理节点
│   │   │           ├── chat_agent_node.py    # 聊天 Agent 节点
│   │   │           └── memory_extract_node.py # 记忆提取节点
│   │   ├── database/
│   │   │   ├── models/             # 数据模型（User/Dialog/History/Knowledge/KnowledgeFile/Report）
│   │   │   ├── dao/                # 数据访问层
│   │   │   ├── engine.py           # 数据库引擎
│   │   │   ├── init_db.py          # 数据库初始化
│   │   │   └── session.py          # 会话管理
│   │   ├── schemas/                # Pydantic 请求/响应模型
│   │   ├── services/
│   │   │   ├── auth_service.py     # 认证服务
│   │   │   ├── llm_service.py      # LLM 服务封装
│   │   │   ├── memory_service.py   # 长期记忆服务（Milvus）
│   │   │   ├── redis_client.py     # Redis 客户端
│   │   │   └── rag/                # RAG 检索增强生成
│   │   │       ├── handler.py      # RAG 核心处理器
│   │   │       ├── embedding.py    # 文本向量化
│   │   │       ├── vector_store.py # 向量存储封装
│   │   │       ├── reranker.py     # 重排序
│   │   │       └── milvus_client.py # Milvus 客户端
│   │   ├── tools/                  # Agent 工具（8 个）
│   │   │   ├── __init__.py         # 工具注册中心
│   │   │   ├── get_weather/        # 天气查询
│   │   │   ├── web_search/         # 网络搜索
│   │   │   ├── web_scraper/        # 网页抓取
│   │   │   ├── knowledge_search/   # 知识库搜索
│   │   │   ├── knowledge_list/     # 知识库列表
│   │   │   ├── code_runner/        # 代码执行
│   │   │   ├── report_generator/   # 报告生成
│   │   │   └── chart_generator/    # 图表生成
│   │   └── utils/
│   │       ├── doc_parser.py       # 文档解析器（13 种格式）
│   │       └── token_counter.py    # Token 计数器
│   ├── pyproject.toml              # 依赖配置
│   └── .env.example                # 环境变量示例
├── frontend/
│   └── src/
│       ├── apis/                   # API 调用封装
│       │   ├── request.ts          # Axios 封装（拦截器/Token注入/刷新）
│       │   ├── auth.ts             # 认证 API
│       │   ├── chat.ts             # 聊天 API（SSE流式/思考过程事件/节点追踪）
│       │   ├── knowledge.ts        # 知识库 API
│       │   ├── memory.ts           # 记忆 API
│       │   └── report.ts           # 报告 API
│       ├── components/             # 可复用组件
│       │   ├── ChatInput.vue       # 聊天输入框（文件上传/发送/停止）
│       │   ├── ChatMessage.vue     # 消息气泡（Markdown/思考过程/图片预览）
│       │   ├── WorkflowGraph.vue   # 工作流可视化图
│       │   ├── WorkflowNode.vue    # 工作流节点组件
│       │   └── WorkflowSidebar.vue # 工作流侧边栏
│       ├── composables/            # 组合式函数
│       │   ├── useChat.ts          # 聊天核心逻辑（对话/流式/工作流追踪）
│       │   └── useMarkdown.ts      # Markdown渲染（高亮/图片预览/报告卡片）
│       ├── types/                  # TypeScript 类型定义
│       │   └── chat.ts             # 消息/思考步骤/Token用量类型
│       ├── pages/                  # 页面组件
│       │   ├── ChatPage.vue        # 聊天主页（流式/文件上传/思考过程/工作流面板）
│       │   ├── KnowledgePage.vue   # 知识库管理
│       │   ├── MemoryPage.vue      # 记忆管理（查看/添加/编辑/删除）
│       │   ├── LoginPage.vue       # 登录
│       │   └── RegisterPage.vue    # 注册
│       └── router/index.ts         # 路由配置
├── docs/                           # 项目文档
├── .gitignore
├── start_backend.bat               # Windows 后端启动脚本
└── start_frontend.bat              # Windows 前端启动脚本
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

# LLM 配置（OpenAI 兼容 API）
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

# Embedding 配置
EMBEDDING_MODEL=text-embedding-v3
EMBEDDING_DIMENSION=1024

# RAG 配置
RAG_TOP_K=5
RAG_MIN_SCORE=0.3
RAG_RERANKER_TOP_N=10

# JWT 配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## API 接口一览

### 认证
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录

### 聊天
- `POST /api/v1/chat/stream-message` - 发送消息（SSE 流式）
- `POST /api/v1/chat/upload-file` - 上传并解析文件
- `GET /api/v1/chat/history/{dialog_id}` - 获取聊天历史

### 对话管理
- `POST /api/v1/dialog/create` - 创建对话
- `GET /api/v1/dialog/list` - 对话列表
- `GET /api/v1/dialog/{dialog_id}` - 对话详情
- `PUT /api/v1/dialog/{dialog_id}/name` - 修改对话名称
- `DELETE /api/v1/dialog/{dialog_id}` - 删除对话
- `GET /api/v1/dialog/{dialog_id}/history` - 对话历史

### 知识库
- `POST /api/v1/knowledge/` - 创建知识库
- `GET /api/v1/knowledge/` - 知识库列表
- `GET /api/v1/knowledge/{id}` - 知识库详情
- `DELETE /api/v1/knowledge/{id}` - 删除知识库
- `POST /api/v1/knowledge/upload` - 上传文件到知识库
- `POST /api/v1/knowledge/query` - RAG 查询

### 记忆管理
- `GET /api/v1/memory/` - 获取记忆列表
- `POST /api/v1/memory/` - 手动添加记忆
- `PUT /api/v1/memory/{memory_id}` - 更新记忆
- `DELETE /api/v1/memory/{memory_id}` - 删除记忆

### 报告
- `GET /api/v1/report/download/{report_id}` - 下载报告
- `GET /api/v1/report/list` - 报告列表
- `DELETE /api/v1/report/{report_id}` - 删除报告

## 开发规范

### 添加新工具
1. 在 `backend/app/tools/` 下创建新目录，编写 `action.py`
2. 在 `tools/__init__.py` 的 `AgentTools` 列表中注册

### 添加新 API
1. 在 `backend/app/api/v1/` 下创建新模块
2. 在 `router.py` 中 `include_router` 注册

### 添加新数据模型
1. 在 `backend/app/database/models/` 下定义 SQLModel 模型
2. 在 `init_db.py` 中注册

### 代码提交
```bash
git add .
git commit -m "feat: 功能描述"  # feat/fix/docs/style/refactor/test/chore
git push
```

## 常见问题

### 1. 数据库连接失败
确保 MySQL 服务已启动，并检查 `.env` 中的 `DATABASE_URL` 配置。

### 2. Milvus 连接失败
确保 Milvus 服务已启动，并检查 `MILVUS_HOST` 和 `MILVUS_PORT` 配置。

### 3. LLM 调用失败
检查 `LLM_API_KEY` 和 `LLM_BASE_URL` 是否配置正确。

### 4. Redis 连接失败
确保 Redis 服务已启动，检查 `REDIS_HOST` 和 `REDIS_PORT` 配置。

## 技术文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [LangChain 文档](https://python.langchain.com/)
- [Vue 3 官方文档](https://cn.vuejs.org/)
- [Milvus 文档](https://milvus.io/docs)
- [Element Plus 文档](https://element-plus.org/)

## License

MIT

## 作者

互补所短 <1879334164@qq.com>

