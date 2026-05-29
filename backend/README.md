# Hubu Agent Backend

基于 FastAPI + LangGraph 构建的多 Agent 智能对话系统后端，支持 RAG 检索增强、长期记忆、技能系统、用户自建 Agent 等功能。

## 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | 高性能异步 API |
| AI 框架 | LangChain + LangGraph | LLM 应用开发 & 多 Agent 工作流 |
| 数据库 | MySQL (SQLModel) | 关系数据存储 |
| 缓存 | Redis | 会话管理 & 配置缓存 |
| 向量库 | Milvus | RAG 语义检索 |
| 认证 | PyJWT + Passlib | JWT 令牌 & 密码哈希 |

## 系统架构

### 多 Agent 协作工作流

```
START → [RAG, Memory, History] 并行 → Merge → Supervisor（路由）
                                                    │
                                      ┌─────────────┼─────────────┬──────────┐──────────┐
                                      ▼             ▼             ▼          ▼          ▼
                                   Chat        Researcher     Coder     Skill    用户Agent...
                                      │             │             │          │          │
                                      └─────────────┴─────────────┴──────────┘──────────┘
                                                    │
                                                    ▼
                                                Reviewer
                                               ╱        ╲
                                          通过 ✅      不够 🔁
                                           │              │
                                           ▼              └→ 回到 Supervisor
                                          END
```

**工作流程**：

1. **并行预处理**：RAG 检索、长期记忆、历史管理同时执行
2. **综合合并**：将检索结果、记忆、历史合并为统一上下文
3. **意图路由**：Supervisor 判断用户意图，路由到对应 Agent
4. **Agent 执行**：各 Agent 基于 ReAct 模式调用工具完成任务
5. **审查校验**：Reviewer 检查结果质量，不通过则重新路由
6. **记忆提取**：审查通过后，异步后台提取并存储长期记忆

### Agent 体系

| Agent | 类型 | 职责 |
|-------|------|------|
| Supervisor | LLM Agent | 意图识别 & 任务路由 |
| Chat | ReAct Agent | 日常对话 & 通用工具调用 |
| Researcher | ReAct Agent | 信息检索 & 网络搜索 |
| Coder | ReAct Agent | 代码编写 & 执行 |
| Skill | ReAct Agent | 技能脚本执行 |
| Reviewer | LLM Agent | 结果质量审查 |
| MemoryExtract | LLM Agent | 长期记忆提取（异步） |
| Summary | LLM Agent | 对话历史摘要 |
| 用户自建 Agent | ReAct Agent | 用户自定义 Agent |

## 目录结构

```
app/
├── api/v1/                # API 路由
│   ├── auth.py            # 认证（注册/登录）
│   ├── chat.py            # 聊天（流式/非流式）
│   ├── dialog.py          # 对话管理
│   ├── knowledge.py       # 知识库
│   ├── memory.py          # 长期记忆
│   ├── export.py          # 对话导出
│   ├── provider.py        # 模型供应商管理
│   ├── embedding_provider.py  # Embedding 供应商管理
│   ├── model.py           # 模型切换
│   ├── skills.py          # 技能管理
│   ├── user_agent.py      # 用户自建 Agent
│   ├── workspace.py       # 工作区文件
│   ├── settings.py        # 系统配置
│   ├── usage_stats.py     # Token 用量统计
│   └── logs.py            # 日志查看
├── auth/                  # JWT 认证模块
├── core/
│   ├── agents/            # Agent 实现
│   │   ├── bases/         # 基类（BaseLLMAgent / BaseReactAgent）
│   │   ├── llm/           # LLM 型 Agent（Supervisor/Reviewer/Summary/MemoryExtract）
│   │   ├── react/         # ReAct 型 Agent（Chat/Coder/Researcher/Writer）
│   │   └── custom/        # 用户自建 Agent（加载/工厂）
│   └── graph/             # LangGraph 工作流
│       ├── graph.py       # Graph 拓扑定义
│       ├── state.py       # 全局状态
│       └── nodes/         # 各节点实现
├── database/              # 数据层
│   ├── models/            # SQLModel 模型
│   ├── dao/               # 数据访问层
│   ├── engine.py          # 数据库引擎
│   └── session.py         # 会话管理
├── schemas/               # Pydantic 请求/响应模型
├── services/              # 业务服务
│   ├── auth_service.py    # 认证服务
│   ├── llm_service.py     # LLM 调用服务
│   ├── memory_service.py  # 记忆服务
│   ├── export_service.py  # 导出服务
│   ├── settings_service.py # 动态配置服务
│   ├── redis_client.py    # Redis 客户端
│   └── rag/               # RAG 服务
│       ├── handler.py     # 检索处理器
│       ├── embedding.py   # 文本向量化
│       ├── vector_store.py # 向量存储
│       ├── reranker.py    # 重排序
│       └── milvus_client.py # Milvus 客户端
├── prompts/               # Agent Prompt 模板
├── skills/                # 系统内置技能
│   ├── docx/              # Word 文档生成
│   ├── pdf/               # PDF 处理
│   ├── pptx/              # PPT 生成
│   ├── xlsx/              # Excel 生成
│   └── skill-creator/     # 技能创建器
├── tools/                 # 工具模块
│   ├── web_search.py      # 网络搜索（Tavily）
│   ├── web_scraper.py     # 网页抓取
│   ├── get_weather.py     # 天气查询（高德 API）
│   ├── knowledge_search.py # 知识库检索
│   ├── knowledge_list.py  # 知识库列表
│   ├── exec_python.py     # Python 代码执行
│   ├── exec_js.py         # JavaScript 代码执行
│   ├── file_manager.py    # 文件管理
│   ├── package_installer.py # 包安装器
│   └── skill_loader.py    # 技能加载器
├── middleware/             # 中间件（用户上下文）
├── callbacks/             # LLM 回调（Token 统计）
├── utils/                 # 工具函数
├── config.py              # 配置管理
└── main.py                # 应用入口
```

## 环境配置

### 必需环境

- Python 3.11 或 3.12
- MySQL 8.0+
- Redis 6.0+
- Milvus 2.4+

### 环境变量

复制 `.env.example` 为 `.env` 并填入实际值：

```bash
cp .env.example .env
```

**静态配置**（`.env` 文件，需重启生效）：

| 配置组 | 变量 | 说明 |
|--------|------|------|
| 应用 | `APP_NAME`, `HOST`, `PORT`, `DEBUG` | 基础设置 |
| 数据库 | `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL 连接 |
| Redis | `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD` | Redis 连接 |
| Milvus | `MILVUS_HOST`, `MILVUS_PORT`, `MILVUS_PASSWORD`, `EMBEDDING_DIMENSION` | 向量数据库 |
| 工具 | `TAVILY_API_KEY`, `WEATHER_API_KEY` | 外部 API Key |
| 代码执行 | `CODE_EXEC_MAX_OUTPUT` | 输出限制 |
| 文件管理 | `FILE_MAX_SIZE` | 文件大小限制 |
| 包安装 | `PKG_ALLOW_PIP`, `PKG_ALLOW_NPM`, `PKG_PIP_TIMEOUT` | pip/npm 控制 |
| 日志 | `LOG_LEVEL`, `LOG_FILE_LEVEL` | 日志级别 |

**动态配置**（通过前端「系统设置」或 `/api/v1/settings` 接口管理，实时生效）：

| 配置组 | 变量 | 说明 |
|--------|------|------|
| 对话历史 | `MAX_HISTORY_ROUNDS`, `ENABLE_HISTORY_SUMMARY`, `SUMMARY_THRESHOLD` | 历史管理 |
| 上下文控制 | `MAX_CONTEXT_TOKENS`, `RESERVE_FOR_RESPONSE`, `ENABLE_TOKEN_CONTROL` | Token 控制 |
| RAG 检索 | `RAG_TOP_K`, `RAG_MIN_SCORE`, `RAG_RERANKER_TOP_N`, `RAG_HYBRID_WEIGHTS`, `MILVUS_NPROBE` | 检索参数 |
| 长期记忆 | `MEMORY_TOP_K`, `MEMORY_MIN_SCORE` | 记忆检索 |
| Agent | `AGENT_MAX_ITERATIONS`, `REVIEWER_MAX_RETRIES` | 运行控制 |
| 代码执行 | `CODE_EXEC_TIMEOUT`, `CODE_EXEC_MAX_TIMEOUT` | 超时控制 |
| LLM | `LLM_STREAM_CHUNK_TIMEOUT` | 流式超时 |

**数据库管理**（通过前端设置页面或对应 API 管理）：

| 配置 | API | 说明 |
|------|-----|------|
| 模型供应商 | `/api/v1/provider` | LLM 模型配置（API Key、Base URL、模型名） |
| Embedding 供应商 | `/api/v1/embedding-provider` | Embedding 模型配置 |

## 安装与启动

### 1. 安装依赖

```bash
cd backend
poetry install
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env，填入 MySQL、Redis、Milvus 等连接信息
```

### 3. 启动服务

```bash
# 开发模式（自动重载）
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## API 接口

### 认证
- `POST /api/v1/auth/register` — 用户注册
- `POST /api/v1/auth/login` — 用户登录

### 聊天
- `POST /api/v1/chat/stream-message` — 发送消息（SSE 流式）

### 对话管理
- `POST /api/v1/dialog/create` — 创建对话
- `GET /api/v1/dialog/list` — 对话列表
- `GET /api/v1/dialog/{id}` — 对话详情
- `PUT /api/v1/dialog/{id}/name` — 重命名
- `DELETE /api/v1/dialog/{id}` — 删除对话

### 知识库
- `POST /api/v1/knowledge/` — 创建知识库
- `GET /api/v1/knowledge/` — 知识库列表
- `POST /api/v1/knowledge/upload` — 上传文档
- `POST /api/v1/knowledge/query` — RAG 查询
- `DELETE /api/v1/knowledge/{id}` — 删除知识库

### 长期记忆
- `GET /api/v1/memory/` — 记忆列表
- `POST /api/v1/memory/` — 添加记忆
- `PUT /api/v1/memory/{id}` — 更新记忆
- `DELETE /api/v1/memory/{id}` — 删除记忆

### 模型管理
- `GET /api/v1/model/current` — 当前模型
- `GET /api/v1/model/list` — 可用模型列表
- `POST /api/v1/model/switch` — 切换模型
- `GET /api/v1/provider/` — 模型供应商列表
- `POST /api/v1/provider/` — 添加供应商
- `PUT /api/v1/provider/{id}` — 更新供应商
- `DELETE /api/v1/provider/{id}` — 删除供应商

### Embedding 供应商
- `GET /api/v1/embedding-provider/` — 供应商列表
- `POST /api/v1/embedding-provider/` — 添加供应商
- `PUT /api/v1/embedding-provider/{id}` — 更新供应商
- `DELETE /api/v1/embedding-provider/{id}` — 删除供应商

### 技能管理
- `GET /api/v1/skills/list` — 技能列表
- `POST /api/v1/skills/add` — 添加技能
- `POST /api/v1/skills/upload` — 上传技能包（ZIP）
- `DELETE /api/v1/skills/{name}` — 删除技能

### 用户自建 Agent
- `GET /api/v1/user-agent/list` — Agent 列表
- `POST /api/v1/user-agent/create` — 创建 Agent
- `PUT /api/v1/user-agent/{id}` — 更新 Agent
- `DELETE /api/v1/user-agent/{id}` — 删除 Agent

### 工作区文件
- `GET /api/v1/workspace/list` — 文件列表
- `GET /api/v1/workspace/download/{path}` — 下载文件
- `DELETE /api/v1/workspace/delete/{path}` — 删除文件

### 系统配置
- `GET /api/v1/settings` — 获取配置（分组）
- `PUT /api/v1/settings/{key}` — 更新单项
- `PUT /api/v1/settings` — 批量更新
- `DELETE /api/v1/settings/{key}` — 重置单项
- `POST /api/v1/settings/reset` — 重置全部

### 其他
- `POST /api/v1/export/{dialog_id}/export` — 导出对话
- `POST /api/v1/usage_stats/usage` — Token 用量统计
- `GET /api/v1/usage_stats/models_list` — 使用过的模型列表
- `GET /api/v1/logs/list` — 日志文件列表
- `GET /api/v1/logs/read/{path}` — 读取日志

## 开发指南

### 添加新工具

1. 在 `app/tools/` 下创建工具文件（如 `my_tool.py`）
2. 实现工具函数，使用 `@tool` 装饰器
3. 在 `app/tools/__init__.py` 中注册

### 添加新技能

1. 在 `app/skills/` 下创建技能目录
2. 编写 `SKILL.md` 描述技能用途
3. 在 `scripts/` 下放置脚本
4. Agent 通过 `skill_loader` 自动加载

### 添加用户自建 Agent

通过 `/api/v1/user-agent/create` 接口创建，系统自动注入 Graph 工作流。

### 新增 API

1. 在 `app/api/v1/` 下创建模块
2. 实现路由和处理函数
3. 在 `app/api/v1/router.py` 中注册

## 许可证

MIT License
