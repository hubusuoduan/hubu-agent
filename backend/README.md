# Hubu Agent Backend

## 简介
简化的智能对话系统后端，基于 FastAPI 构建。

## 目录结构
```
app/
├── api/              # API路由层
│   └── v1/          # API版本1
├── core/            # 核心业务逻辑
│   ├── agents/     # Agent实现
│   └── models/     # 模型配置
├── database/        # 数据库相关
│   ├── models/     # 数据模型定义
│   └── session.py  # 数据库会话
├── schemas/         # Pydantic数据模型
├── services/        # 业务服务层
├── config.py        # 配置管理
└── main.py          # 应用入口
```

## 启动方式
```bash
python -m app.main
```

访问 http://localhost:8000/docs 查看API文档
