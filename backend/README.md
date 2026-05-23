# Hubu Agent Backend

## 项目简介

Hubu Agent Backend 是一个基于 FastAPI 构建的智能对话系统后端，集成了 LangChain、LangGraph、RAG（检索增强生成）、长期记忆等先进技术。系统采用前后端分离架构，为前端提供 RESTful API 接口，支持流式和非流式响应，提供智能、专业、个性化的对话体验。

## 技术栈

### 核心框架
- **FastAPI 0.121.0**: 高性能 Web 框架
- **Uvicorn**: ASGI 服务器
- **Pydantic 2.10.6**: 数据验证和设置管理

### AI 框架
- **LangChain 1.2.15**: LLM 应用开发框架
- **LangGraph 1.1.10**: 多 Agent 协作框架
- **LangChain OpenAI 1.0.2**: OpenAI 模型集成
- **Dashscope 1.25.18**: 阿里云通义千问 SDK

### 数据库
- **MySQL**: 关系型数据库（通过 SQLModel 和 PyMySQL）
- **Redis**: 缓存和会话管理
- **Milvus**: 向量数据库，用于 RAG 检索

### 认证与安全
- **PyJWT**: JWT 令牌生成和验证
- **python-jose**: JWT 编码/解码
- **Passlib + Bcrypt**: 密码哈希

### 文档处理
- **Unstructured**: 多格式文档解析
- **PyPDF**: PDF 文档处理
- **docx2txt**: Word 文档处理
- **BeautifulSoup4**: HTML 解析

### 其他
- **Loguru**: 日志管理
- **Matplotlib**: 图表生成
- **Tiktoken**: Token 计数

## 目录结构

```
app/
├── api/                  # API 路由层
│   ├── dependencies.py   # 依赖注入
│   └── v1/              # API v1 版本
│       ├── auth.py      # 认证接口
│       ├── chat.py      # 聊天接口
│       ├── dialog.py    # 对话管理接口
│       ├── knowledge.py # 知识库接口
│       ├── memory.py    # 长期记忆接口
│       ├── report.py    # 报告生成接口
│       └── router.py    # 路由注册
├── auth/                 # 认证模块
│   ├── auth_jwt.py      # JWT 认证实现
│   ├── config.py        # 认证配置
│   └── exceptions.py    # 认证异常
├── core/                 # 核心业务逻辑
│   ├── agents/         # Agent 实现
│   │   ├── chat_agent.py      # 聊天 Agent
│   │   ├── memory_agent.py    # 记忆 Agent
│   │   └── summary_agent.py   # 摘要 Agent
│   └── graph/          # LangGraph 工作流
│       ├── graph.py            # Graph 主文件
│       ├── state.py            # 状态定义
│       └── nodes/              # Graph 节点
│           ├── chat_agent_node.py
│           ├── rag_node.py
│           ├── memory_node.py
│           ├── history_node.py
│           └── memory_extract_node.py
├── database/              # 数据库相关
│   ├── models/         # 数据模型定义
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── dialog.py
│   │   ├── history.py
│   │   ├── knowledge.py
│   │   ├── knowledge_file.py
│   │   └── report.py
│   ├── dao/            # 数据访问层
│   │   ├── user_dao.py
│   │   ├── dialog_dao.py
│   │   └── history_dao.py
│   ├── engine.py       # 数据库引擎
│   ├── init_db.py      # 数据库初始化
│   └── session.py      # 会话管理
├── schemas/              # Pydantic 数据模型
│   ├── auth.py
│   ├── chat.py
│   ├── dialog.py
│   ├── knowledge.py
│   └── memory.py
├── services/             # 业务服务层
│   ├── auth_service.py  # 认证服务
│   ├── llm_service.py   # LLM 服务
│   ├── memory_service.py # 记忆服务
│   ├── redis_client.py  # Redis 客户端
│   └── rag/            # RAG 服务
│       ├── handler.py        # RAG 核心处理器
│       ├── embedding.py      # 文本向量化
│       ├── vector_store.py   # 向量存储封装
│       ├── reranker.py       # 检索结果重排序
│       └── milvus_client.py  # Milvus 客户端
├── tools/                # 工具模块
│   ├── get_weather/       # 天气查询
│   ├── web_search/        # 网络搜索
│   ├── web_scraper/       # 网页抓取
│   ├── knowledge_search/  # 知识库搜索
│   ├── knowledge_list/    # 知识库列表
│   ├── code_runner/       # 代码执行
│   ├── report_generator/  # 报告生成
│   └── chart_generator/   # 图表生成
├── utils/                # 工具函数
│   ├── doc_parser.py    # 文档解析器
│   └── token_counter.py # Token 计数器
├── config.py            # 配置管理
└── main.py              # 应用入口
```

## 核心模块说明

### 1. Graph 工作流

系统使用 LangGraph 构建了多节点工作流，实现 RAG、记忆、历史管理等功能的协同工作：

```
START → RAG → Memory → History Manager → Chat Agent → Memory Extract → END
```

**各节点功能**：
- **RAG 节点**: 检索相关文档，为 Agent 提供上下文
- **Memory 节点**: 获取用户的长期记忆
- **History Manager 节点**: 管理和压缩对话历史
- **Chat Agent 节点**: 处理用户输入，生成回复
- **Memory Extract 节点**: 从对话中提取并存储新的长期记忆

### 2. RAG 服务

RAG（检索增强生成）服务提供完整的文档检索能力：
- 支持多种文档格式解析（PDF、Word、TXT、HTML 等）
- 使用 Milvus 向量数据库进行相似度检索
- 支持检索结果重排序，提高准确性
- 可配置检索参数（top_k、min_score 等）

### 3. 长期记忆

系统自动提取和存储用户信息，实现个性化对话：
- 从对话中提取关键信息
- 存储用户偏好、个人信息等
- 在后续对话中自动使用记忆信息

### 4. 工具系统

集成了 8 个实用工具，扩展 Agent 能力：
1. **get_weather**: 获取天气信息
2. **web_search**: 网络搜索
3. **web_scraper**: 网页内容抓取
4. **knowledge_search**: 知识库搜索
5. **knowledge_list**: 列出知识库
6. **code_runner**: 代码执行
7. **report_generator**: 报告生成
8. **chart_generator**: 图表生成

## 环境配置

### 必需环境
- Python 3.11 或 3.12
- MySQL 8.0+
- Redis 6.0+
- Milvus 2.4+

### 环境变量
创建 `.env` 文件，配置以下变量：

```env
# 应用配置
APP_NAME=Hubu Agent
APP_VERSION=1.0.0
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/hubu_agent

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530

# LLM 配置（OpenAI 兼容 API）
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

# JWT 配置
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# RAG 配置
RAG_TOP_K=5
RAG_MIN_SCORE=0.3
RAG_RERANKER_TOP_N=10

# Agent 配置
AGENT_MAX_ITERATIONS=10
```

## 安装与启动

### 使用 Poetry 安装依赖

```bash
# 安装 Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 安装项目依赖
poetry install
```

### 初始化数据库

```bash
# 运行数据库初始化脚本
python -c "from app.database.init_db import init_db; import asyncio; asyncio.run(init_db())"
```

### 启动服务

```bash
# 开发模式（自动重载）
python -m app.main

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 访问 API 文档

启动服务后，访问以下地址查看 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 接口

### 认证接口
- `POST /api/v1/auth/register`: 用户注册
- `POST /api/v1/auth/login`: 用户登录

### 聊天接口
- `POST /api/v1/chat/message`: 发送消息（非流式）
- `POST /api/v1/chat/stream-message`: 发送消息（流式）
- `POST /api/v1/chat/upload-file`: 上传并解析文件
- `GET /api/v1/chat/history/{dialog_id}`: 获取对话历史

### 对话管理接口
- `POST /api/v1/dialog/create`: 创建对话
- `GET /api/v1/dialog/list`: 获取对话列表
- `PUT /api/v1/dialog/{dialog_id}/name`: 更新对话名称
- `DELETE /api/v1/dialog/{dialog_id}`: 删除对话
- `GET /api/v1/dialog/{dialog_id}`: 获取对话详情
- `GET /api/v1/dialog/{dialog_id}/history`: 获取对话历史

### 知识库接口
- `POST /api/v1/knowledge/`: 创建知识库
- `GET /api/v1/knowledge/`: 获取知识库列表
- `GET /api/v1/knowledge/{knowledge_id}`: 获取知识库详情
- `DELETE /api/v1/knowledge/{knowledge_id}`: 删除知识库
- `POST /api/v1/knowledge/upload`: 上传文档到知识库
- `POST /api/v1/knowledge/query`: RAG查询

### 长期记忆接口
- `GET /api/v1/memory/`: 获取记忆列表
- `POST /api/v1/memory/`: 手动添加记忆
- `PUT /api/v1/memory/{memory_id}`: 更新记忆
- `DELETE /api/v1/memory/{memory_id}`: 删除记忆

### 报告接口
- `GET /api/v1/report/download/{report_id}`: 下载报告（支持Header/URL Token双认证）
- `GET /api/v1/report/list`: 获取报告列表
- `DELETE /api/v1/report/{report_id}`: 删除报告

## 开发指南

### 添加新工具

1. 在 `app/tools/` 下创建新工具目录
2. 实现 `action.py`，定义工具函数
3. 在 `app/tools/__init__.py` 中注册工具

### 扩展 RAG

修改 `app/services/rag/` 下的处理器：
- `handler.py`: 修改检索逻辑
- `reranker.py`: 调整重排序策略
- `embedding.py`: 切换嵌入模型

### 优化记忆

调整 `app/services/memory_service.py` 中的记忆提取逻辑

### 新增 API

1. 在 `app/api/v1/` 下创建新模块
2. 实现路由和处理函数
3. 在 `app/api/v1/router.py` 中注册路由

## 常见问题

### 1. 数据库连接失败
检查 `DATABASE_URL` 配置是否正确，确保 MySQL 服务已启动。

### 2. Milvus 连接失败
检查 `MILVUS_HOST` 和 `MILVUS_PORT` 配置，确保 Milvus 服务已启动。

### 3. LLM 调用失败
检查 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL` 配置是否正确。

### 4. Redis 连接失败
检查 `REDIS_URL` 配置，确保 Redis 服务已启动。

## 许可证

MIT License

## 联系方式

- 作者: 互补所短
- 邮箱: 1879334164@qq.com
