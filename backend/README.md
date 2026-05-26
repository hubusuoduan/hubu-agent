# Hubu Agent Backend

## 项目简介

Hubu Agent Backend 是一个基于 FastAPI 构建的智能对话系统后端，集成了 LangChain、LangGraph、RAG（检索增强生成）、长期记忆、Skills 技能系统等先进技术。系统采用前后端分离架构，为前端提供 RESTful API 接口，支持流式和非流式响应，提供智能、专业、个性化的对话体验。

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
- **python-docx**: Word 文档处理
- **docx2txt**: Word 文档文本提取
- **openpyxl**: Excel 文档处理
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
│       ├── export.py    # 导出接口
│       ├── knowledge.py # 知识库接口
│       ├── logs.py      # 日志查看接口
│       ├── memory.py    # 长期记忆接口
│       ├── model.py     # 模型切换接口
│       ├── settings.py  # 系统配置接口
│       ├── skills.py    # 技能管理接口
│       ├── usage_stats.py # Token 使用量统计接口
│       ├── workspace.py # 工作区文件接口
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
│           ├── chat_agent_node.py   # 聊天节点
│           ├── rag_node.py          # RAG 检索节点
│           ├── memory_node.py       # 记忆检索节点
│           ├── history_node.py      # 历史管理节点
│           ├── merge_node.py        # 上下文合并节点
│           └── memory_extract_node.py # 记忆提取节点
├── database/              # 数据库相关
│   ├── models/         # 数据模型定义
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── dialog.py
│   │   ├── history.py
│   │   ├── knowledge.py
│   │   ├── knowledge_file.py
│   │   └── usage_stats.py
│   ├── dao/            # 数据访问层
│   │   ├── user_dao.py
│   │   ├── dialog_dao.py
│   │   ├── history_dao.py
│   │   └── usage_stats_dao.py
│   ├── engine.py       # 数据库引擎
│   ├── init_db.py      # 数据库初始化
│   └── session.py      # 会话管理
├── schemas/              # Pydantic 数据模型
│   ├── auth.py
│   ├── chat.py
│   ├── dialog.py
│   ├── export.py
│   ├── knowledge.py
│   └── memory.py
├── services/             # 业务服务层
│   ├── auth_service.py  # 认证服务
│   ├── llm_service.py   # LLM 服务
│   ├── memory_service.py # 记忆服务
│   ├── export_service.py # 导出服务
│   ├── settings_service.py # 系统配置服务
│   ├── redis_client.py  # Redis 客户端
│   └── rag/            # RAG 服务
│       ├── handler.py        # RAG 核心处理器
│       ├── embedding.py      # 文本向量化
│       ├── vector_store.py   # 向量存储封装
│       ├── reranker.py       # 检索结果重排序
│       └── milvus_client.py  # Milvus 客户端
├── skills/               # Skills 技能系统
│   ├── docx/            # Word 文档生成技能
│   ├── pdf/             # PDF 文档处理技能
│   ├── pptx/            # PPT 演示文稿生成技能
│   ├── xlsx/            # Excel 表格生成技能
│   └── skill-creator/   # 技能创建器
├── tools/                # 工具模块
│   ├── get_weather/       # 天气查询
│   ├── web_search/        # 网络搜索（Tavily）
│   ├── web_scraper/       # 网页抓取
│   ├── knowledge_search/  # 知识库搜索
│   ├── knowledge_list/    # 知识库列表
│   ├── code_runner/       # 沙箱代码执行（进程内 exec，安全受限）
│   ├── code_exec/         # 完整代码执行（子进程，无模块限制）
│   ├── run_script/        # 执行 Skill 脚本
│   ├── file_manager/      # 文件管理（读写/移动/删除工作区文件）
│   ├── package_installer/ # 包安装器（pip/npm）
│   └── skill_loader/      # 技能加载器（加载/列出/读取技能资源）
├── utils/                # 工具函数
│   ├── doc_parser.py    # 文档解析器
│   ├── token_counter.py # Token 计数器
│   └── format.py        # 格式化工具（文件大小等）
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
- **Chat Agent 节点**: 处理用户输入，调用工具生成回复
- **Memory Extract 节点**: 从对话中提取并存储新的长期记忆

### 2. RAG 服务

RAG（检索增强生成）服务提供完整的文档检索能力：
- 支持多种文档格式解析（PDF、Word、TXT、HTML 等）
- 使用 Milvus 向量数据库进行相似度检索
- 支持 BM25 + 语义混合检索
- 支持检索结果重排序，提高准确性
- 可配置检索参数（top_k、min_score、hybrid_weights 等）

### 3. 长期记忆

系统自动提取和存储用户信息，实现个性化对话：
- 从对话中提取关键信息
- 存储用户偏好、个人信息等
- 在后续对话中自动使用记忆信息

### 4. 工具系统

集成了多个实用工具，扩展 Agent 能力：

| 工具 | 说明 |
|------|------|
| **get_weather** | 获取天气信息（高德地图 API） |
| **web_search** | 网络搜索（Tavily API） |
| **web_scraper** | 网页内容抓取 |
| **knowledge_search** | 知识库搜索 |
| **knowledge_list** | 列出知识库 |
| **code_runner** | 沙箱代码执行（进程内 exec，安全受限） |
| **code_exec** | 完整代码执行（子进程，无模块限制） |
| **run_script** | 执行 Skill 目录下的脚本（如 unpack.py、validate.py） |
| **file_manager** | 文件管理（读写/移动/删除/创建目录等） |
| **package_installer** | 包安装器（pip install / npm install） |
| **skill_loader** | 技能加载器（加载/列出/读取技能资源） |

### 5. Skills 技能系统

系统内置了多种文档生成技能，Agent 可通过 skill_loader 工具动态加载：
- **docx**: Word 文档生成
- **pdf**: PDF 文档处理
- **pptx**: PPT 演示文稿生成
- **xlsx**: Excel 表格生成
- **skill-creator**: 自动创建新技能

## 环境配置

### 必需环境
- Python 3.11 或 3.12
- MySQL 8.0+
- Redis 6.0+
- Milvus 2.4+

### 环境变量

复制 `.env.example` 为 `.env` 并填入实际值，详见 `.env.example` 文件。

主要配置项：

| 配置组 | 关键变量 | 说明 |
|--------|----------|------|
| 应用配置 | `APP_NAME`, `HOST`, `PORT`, `DEBUG` | 应用基础设置 |
| 数据库 | `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL 连接 |
| Redis | `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD` | Redis 连接 |
| LLM | `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_PROVIDERS` | 模型配置 |
| Embedding | `EMBEDDING_API_KEY`, `EMBEDDING_MODEL` | 向量化配置 |
| Milvus | `MILVUS_HOST`, `MILVUS_PORT`, `MILVUS_PASSWORD` | 向量数据库 |
| RAG | `RAG_TOP_K`, `RAG_MIN_SCORE`, `RAG_HYBRID_WEIGHTS` | 检索参数 |
| 记忆 | `MEMORY_TOP_K`, `MEMORY_MIN_SCORE` | 记忆检索 |
| Agent | `AGENT_MAX_ITERATIONS` | 最大工具调用轮数 |
| 工具 | `TAVILY_API_KEY`, `WEATHER_API_KEY` | 外部 API Key |
| 沙箱执行 | `SANDBOX_TIMEOUT`, `SANDBOX_MAX_TIMEOUT`, `SANDBOX_MAX_OUTPUT` | code_runner 配置 |
| 代码执行 | `CODE_EXEC_TIMEOUT`, `CODE_EXEC_MAX_TIMEOUT`, `CODE_EXEC_MAX_OUTPUT` | code_exec 配置 |
| 文件管理 | `FILE_WORKSPACE`, `FILE_MAX_SIZE`, `FILE_DENY_EXTENSIONS` | 工作区文件 |
| 包安装 | `PKG_ALLOW_PIP`, `PKG_ALLOW_NPM`, `PKG_PIP_TIMEOUT` | pip/npm 控制 |

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
- `POST /api/v1/chat/stream-message`: 发送消息（流式）
- `POST /api/v1/chat/upload-file`: 上传并解析文件

### 模型接口
- `GET /api/v1/model/current`: 获取当前使用的模型
- `GET /api/v1/model/list`: 获取所有可用模型列表
- `POST /api/v1/model/switch`: 切换当前对话模型

### 导出接口
- `POST /api/v1/export/{dialog_id}/export`: 导出对话记录

### 对话管理接口
- `POST /api/v1/dialog/create`: 创建对话
- `GET /api/v1/dialog/list`: 获取对话列表
- `GET /api/v1/dialog/{dialog_id}`: 获取对话详情
- `PUT /api/v1/dialog/{dialog_id}/name`: 更新对话名称
- `PUT /api/v1/dialog/{dialog_id}/pin`: 更新对话置顶状态
- `PUT /api/v1/dialog/{dialog_id}/star`: 更新对话收藏状态
- `DELETE /api/v1/dialog/{dialog_id}`: 删除对话
- `DELETE /api/v1/dialog/{dialog_id}/messages`: 批量删除对话消息
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

### 工作区文件接口
- `GET /api/v1/workspace/list`: 列出工作区文件（分页）
- `GET /api/v1/workspace/download/{file_path:path}`: 下载工作区文件（支持 Header/URL Token 双认证）
- `GET /api/v1/workspace/info/{file_path:path}`: 获取工作区文件信息
- `DELETE /api/v1/workspace/delete/{file_path:path}`: 删除工作区文件或目录

### 技能管理接口
- `GET /api/v1/skills/list`: 获取技能列表（分页 + 关键词搜索）
- `POST /api/v1/skills/add`: 添加技能
- `POST /api/v1/skills/upload`: 上传技能包（ZIP）
- `DELETE /api/v1/skills/{skill_name}`: 删除技能

### 系统配置接口
- `GET /api/v1/settings`: 获取所有可配置项（按分组）
- `GET /api/v1/settings/flat`: 获取所有可配置项（平铺列表）
- `GET /api/v1/settings/{key}`: 获取单个配置项
- `PUT /api/v1/settings/{key}`: 更新单个配置项
- `PUT /api/v1/settings`: 批量更新配置项
- `DELETE /api/v1/settings/{key}`: 重置单个配置项
- `POST /api/v1/settings/reset`: 重置所有配置项

### Token 使用量统计接口
- `POST /api/v1/usage_stats/usage`: 获取 Token 使用量（按日期+模型聚合）
- `POST /api/v1/usage_stats/usage_count`: 获取调用次数（按日期+模型聚合）
- `GET /api/v1/usage_stats/models_list`: 获取用户使用过的模型列表

### 日志查看接口
- `GET /api/v1/logs/list`: 列出日志文件（分页）
- `GET /api/v1/logs/read/{file_path:path}`: 读取日志文件内容（支持 tail 参数）
- `DELETE /api/v1/logs/delete/{file_path:path}`: 删除日志文件

## 开发指南

### 添加新工具

1. 在 `app/tools/` 下创建新工具目录
2. 实现 `action.py`，定义工具函数
3. 在 `app/tools/__init__.py` 中注册工具

### 添加新技能（Skill）

1. 在 `app/skills/` 下创建新技能目录
2. 编写 `SKILL.md` 描述技能用途和使用方法
3. 在 `scripts/` 目录下放置技能脚本
4. Agent 通过 `skill_loader` 工具自动加载

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
检查 `DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD` 配置是否正确，确保 MySQL 服务已启动。

### 2. Milvus 连接失败
检查 `MILVUS_HOST` 和 `MILVUS_PORT` 配置，确保 Milvus 服务已启动。

### 3. LLM 调用失败
检查 `LLM_API_KEY` 和 `LLM_BASE_URL` 配置是否正确，或确认 `LLM_PROVIDERS` 中 JSON 格式无误。

### 4. Redis 连接失败
检查 `REDIS_HOST` 和 `REDIS_PORT` 配置，确保 Redis 服务已启动。

### 5. 工作区文件无法下载
检查 `FILE_WORKSPACE` 配置的目录是否存在，以及文件路径是否合法。

## 许可证

MIT License

## 联系方式

- 作者: 互补所短
- 邮箱: 1879334164@qq.com
