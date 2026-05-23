# Hubu Agent Frontend

## 简介
Hubu Agent 智能对话助手前端，基于 Vue 3 + TypeScript + Element Plus 构建，支持流式对话、知识库管理、记忆管理等功能。

## 技术栈
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI 组件**: Element Plus
- **HTTP 客户端**: Axios
- **Markdown 渲染**: markdown-it + highlight.js

## 目录结构
```
src/
├── apis/                # API调用封装
│   ├── request.ts       # Axios封装（拦截器/Token注入/刷新）
│   ├── auth.ts          # 认证API（注册/登录）
│   ├── chat.ts          # 聊天API（SSE流式/思考过程事件/节点追踪）
│   ├── knowledge.ts     # 知识库API
│   ├── memory.ts        # 记忆管理API
│   └── report.ts        # 报告API
├── components/          # 可复用组件
│   ├── ChatInput.vue    # 聊天输入框（文件上传/发送/停止生成）
│   ├── ChatMessage.vue  # 消息气泡（Markdown渲染/思考过程/图片预览）
│   ├── WorkflowGraph.vue # 工作流可视化图
│   ├── WorkflowNode.vue  # 工作流节点组件
│   └── WorkflowSidebar.vue # 工作流侧边栏（节点详情）
├── composables/         # 组合式函数
│   ├── useChat.ts       # 聊天核心逻辑（对话管理/流式消息/工作流追踪）
│   └── useMarkdown.ts   # Markdown渲染（代码高亮/图片预览/报告卡片）
├── types/               # TypeScript类型定义
│   └── chat.ts          # 消息/思考步骤/Token用量类型
├── pages/               # 页面组件
│   ├── ChatPage.vue     # 聊天主页（流式输出/文件上传/思考过程/工作流面板）
│   ├── KnowledgePage.vue # 知识库管理
│   ├── MemoryPage.vue   # 记忆管理（查看/添加/编辑/删除）
│   ├── LoginPage.vue    # 登录
│   └── RegisterPage.vue # 注册
├── router/index.ts      # 路由配置
├── App.vue              # 根组件
└── main.ts              # 入口文件
```

## 启动方式
```bash
npm install
npm run dev
```

访问 http://localhost:5173 查看应用

## 功能页面

### 聊天页面 (ChatPage)
- SSE 流式对话输出
- 文件上传解析
- 思考过程展示（LLM思考/工具调用参数和结果）
- 工作流可视化面板（实时节点追踪/耗时统计/节点详情）
- 对话列表侧边栏（新建/切换/删除/重命名）
- 图片点击全屏预览
- 报告/图表卡片式渲染

### 知识库页面 (KnowledgePage)
- 创建/删除知识库
- 上传文档到知识库

### 记忆页面 (MemoryPage)
- 查看长期记忆列表
- 手动添加/编辑/删除记忆
- 记忆来源追溯
