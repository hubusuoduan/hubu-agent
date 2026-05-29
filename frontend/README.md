# Hubu Agent Frontend

基于 Vue 3 + Element Plus 构建的智能对话系统前端，提供聊天、知识库管理、技能系统、系统配置等功能界面。

## 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| 框架 | Vue 3 + TypeScript | 组合式 API |
| 构建 | Vite 5 | 开发 & 打包 |
| UI | Element Plus | 组件库 |
| 路由 | Vue Router 4 | SPA 路由管理 |
| HTTP | Axios | API 请求 |
| 图表 | ECharts | 数据可视化 |
| 流程图 | Vue Flow | Agent 工作流可视化 |
| Markdown | markdown-it + highlight.js | 消息渲染 & 代码高亮 |

## 目录结构

```
src/
├── apis/                  # API 请求封装
│   ├── request.ts         # Axios 实例 & 拦截器
│   ├── auth.ts            # 认证接口
│   ├── chat.ts            # 聊天接口
│   ├── model.ts           # 模型管理接口
│   ├── knowledge.ts       # 知识库接口
│   ├── memory.ts          # 记忆接口
│   ├── skills.ts          # 技能接口
│   ├── user-agent.ts      # 用户 Agent 接口
│   ├── workspace.ts       # 工作区接口
│   ├── settings.ts        # 系统配置接口
│   ├── embedding-provider.ts # Embedding 供应商接口
│   ├── export.ts          # 导出接口
│   ├── usage-stats.ts     # Token 统计接口
│   └── logs.ts            # 日志接口
├── components/            # 公共组件
│   ├── ChatInput.vue      # 聊天输入框
│   ├── ChatMessage.vue    # 消息渲染
│   ├── DialogHistoryList.vue # 对话历史列表
│   ├── ThinkingSteps.vue  # 思考过程展示
│   ├── WorkflowGraph.vue  # 工作流图
│   ├── WorkflowNode.vue   # 工作流节点
│   ├── WorkflowSidebar.vue # 工作流侧边栏
│   └── ExportDialog.vue   # 导出对话框
├── composables/           # 组合式函数
│   ├── useChat.ts         # 聊天入口
│   ├── useMarkdown.ts     # Markdown 渲染
│   └── chat/              # 聊天逻辑拆分
│       ├── index.ts       # 聚合导出
│       ├── useChatStream.ts    # SSE 流式处理
│       ├── useChatDelete.ts    # 消息/对话删除
│       ├── useChatFiles.ts     # 文件上传
│       ├── useChatModels.ts    # 模型切换
│       └── useChatWorkflow.ts  # 工作流数据
├── pages/                 # 页面组件
│   ├── LoginPage.vue      # 登录
│   ├── RegisterPage.vue   # 注册
│   ├── ChatPage.vue       # 聊天主页面
│   ├── KnowledgePage.vue  # 知识库列表
│   ├── KnowledgeDetailPage.vue # 知识库详情
│   ├── MemoryPage.vue     # 长期记忆管理
│   ├── SkillsPage.vue     # 技能管理
│   ├── UserAgentPage.vue  # 用户自建 Agent
│   ├── ProviderPage.vue   # 模型/Embedding 供应商
│   ├── SettingsPage.vue   # 系统配置
│   ├── WorkspacePage.vue  # 工作区文件
│   ├── DashboardPage.vue  # 仪表盘（Token 统计）
│   ├── LogsPage.vue       # 日志查看（管理员）
│   └── ProfilePage.vue    # 个人信息
├── router/                # 路由配置
│   └── index.ts           # 路由定义 & 导航守卫
├── styles/                # 页面样式
├── types/                 # TypeScript 类型定义
├── utils/                 # 工具函数
│   ├── markdown.ts        # Markdown 配置
│   ├── toolFormat.ts      # 工具调用格式化
│   └── fileCard.ts        # 文件卡片工具
├── App.vue                # 根组件
└── main.ts                # 入口文件
```

## 页面说明

| 页面 | 路由 | 说明 |
|------|------|------|
| 登录 | `/login` | 用户登录 |
| 注册 | `/register` | 用户注册 |
| 聊天 | `/chat/:dialogId?` | 对话主界面，支持流式响应 & 工作流可视化 |
| 知识库 | `/knowledge` | 知识库列表 & 创建 |
| 知识库详情 | `/knowledge/:id` | 文档上传 & RAG 检索测试 |
| 长期记忆 | `/memory` | 查看/编辑/删除记忆 |
| 技能管理 | `/skills` | 查看/上传/删除技能 |
| 用户 Agent | `/user-agent` | 创建/管理自定义 Agent |
| 供应商 | `/provider` | 配置 LLM & Embedding 模型供应商 |
| 系统配置 | `/settings` | 动态参数配置（实时生效） |
| 工作区 | `/workspace` | 查看/下载 Agent 生成的文件 |
| 仪表盘 | `/dashboard` | Token 用量统计 & 图表 |
| 日志 | `/logs` | 系统日志查看（仅管理员） |
| 个人信息 | `/profile` | 修改密码等 |

## 安装与启动

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 开发模式

```bash
npm run dev
```

启动后访问 http://localhost:5173，API 请求自动代理到后端 `http://localhost:8000`。

### 3. 生产构建

```bash
npm run build
npm run preview
```

## 开发指南

### 新增页面

1. 在 `src/pages/` 下创建页面组件
2. 在 `src/router/index.ts` 中注册路由
3. 在 `src/styles/` 下添加页面样式

### 新增 API

1. 在 `src/apis/` 下创建或扩展模块
2. 使用 `request.ts` 中的 Axios 实例发起请求

### 路由守卫

- 未登录用户自动跳转 `/login`
- 已登录用户访问登录/注册页自动跳转首页
- 日志页面仅管理员可访问

## 许可证

MIT License
